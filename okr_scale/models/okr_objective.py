from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from .okr_common import LEVELS, STATUSES, compute_status, time_progress

LEVEL_SEQUENCE = {'company': 1, 'department': 2, 'individual': 3}


class OkrObjective(models.Model):
    _name = 'okr.scale.objective'
    _description = 'OKR Objective'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _parent_store = True
    _order = 'cycle_id desc, level_sequence, sequence, id'
    _mail_post_access = 'read'

    name = fields.Char('Objective', required=True, tracking=True)
    description = fields.Html()
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    color = fields.Integer()
    cycle_id = fields.Many2one(
        'okr.scale.cycle', 'Cycle', required=True, index=True, tracking=True, ondelete='restrict',
        default=lambda self: self.env['okr.scale.cycle'].get_current_cycle())
    date_start = fields.Date(related='cycle_id.date_start')
    date_end = fields.Date(related='cycle_id.date_end')
    company_id = fields.Many2one('res.company', required=True, index=True,
                                 default=lambda self: self.env.company)
    level = fields.Selection(LEVELS, required=True, default='individual', tracking=True)
    level_sequence = fields.Integer(compute='_compute_level_sequence', store=True)
    employee_id = fields.Many2one(
        'hr.employee', 'Employee', index=True, tracking=True,
        default=lambda self: self.env.user.employee_id,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    department_id = fields.Many2one(
        'hr.department', 'Department', index=True, tracking=True,
        compute='_compute_department_id', store=True, readonly=False, precompute=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    owner_id = fields.Many2one(
        'res.users', 'Owner', required=True, index=True, tracking=True,
        compute='_compute_owner_id', store=True, readonly=False, precompute=True,
        domain=[('share', '=', False)])
    okr_type = fields.Selection([
        ('committed', 'Committed'),
        ('aspirational', 'Aspirational'),
    ], 'Type', default='committed', required=True,
        help='Committed: must be fully achieved (expected score 1.0).\n'
             'Aspirational: stretch goal, a score around 0.7 is a success.')
    visibility = fields.Selection([
        ('public', 'Everyone'),
        ('department', 'Department'),
        ('private', 'Owner and managers'),
    ], default='public', required=True, tracking=True,
        help='Who can see this objective. Managers in the hierarchy and OKR administrators always can.')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('to_approve', 'To Approve'),
        ('running', 'Running'),
        ('done', 'Closed'),
        ('cancelled', 'Cancelled'),
    ], default='draft', required=True, tracking=True, copy=False, index=True)
    tag_ids = fields.Many2many('okr.scale.tag', string='Tags')
    contributor_department_ids = fields.Many2many(
        'hr.department', 'okr_scale_objective_contrib_department_rel', 'objective_id', 'department_id',
        string='Supporting Departments', tracking=True,
        help='Departments helping the owner to reach this objective. Their members can follow it and comment.')
    contributor_user_ids = fields.Many2many(
        'res.users', 'okr_scale_objective_contrib_user_rel', 'objective_id', 'user_id',
        string='Supporting People', domain=[('share', '=', False)], tracking=True,
        help='People helping the owner. The owner stays accountable for the objective.')

    parent_id = fields.Many2one(
        'okr.scale.objective', 'Aligned To', index=True, ondelete='set null', tracking=True,
        compute='_compute_parent_id', store=True, readonly=False,
        help='Upper objective this objective contributes to.')
    parent_path = fields.Char(index=True, unaccent=False)
    child_ids = fields.One2many('okr.scale.objective', 'parent_id', 'Aligned Objectives')
    parent_key_result_id = fields.Many2one(
        'okr.scale.key.result', 'Aligned Key Result', index=True, ondelete='set null', tracking=True,
        help='Upper key result this objective contributes to. Key results measured '
             '"From aligned objectives" take their progress from these objectives.')
    key_result_ids = fields.One2many('okr.scale.key.result', 'objective_id', 'Key Results', copy=True)
    key_result_count = fields.Integer(compute='_compute_key_result_count')
    checkin_ids = fields.One2many('okr.scale.checkin', 'objective_id', 'Check-ins')

    progress = fields.Float(compute='_compute_progress', store=True, recursive=True,
                            group_operator='avg')
    expected_progress = fields.Float(compute='_compute_expected_progress',
                                     help='Share of the cycle already elapsed.')
    confidence = fields.Float(compute='_compute_progress', store=True, recursive=True, group_operator='avg',
                              help='Average confidence (1-10) of the key results.')
    status = fields.Selection(STATUSES, compute='_compute_status', store=True, index=True)
    last_checkin_date = fields.Date(compute='_compute_progress', store=True, recursive=True)
    progress_history = fields.Json(compute='_compute_progress_history',
                                   help='Weighted progress of the key results over the cycle.')

    quality_hint = fields.Char(compute='_compute_quality_hint',
                               help='Advice based on OKR good practices, never blocking.')
    is_my_team = fields.Boolean(compute='_compute_is_my_team', search='_search_is_my_team',
                                help='Objectives of the departments and employees managed by the current user.')

    final_score = fields.Float('Final Score', tracking=True, copy=False,
                               help='Grade given at the end of the cycle, from 0.0 to 1.0.')
    graded = fields.Boolean('Graded Manually', copy=False, readonly=True,
                            help='The final score was set by a person: closing the cycle keeps it, even 0.0.')
    self_assessment = fields.Text(copy=False)
    lessons_learned = fields.Text(copy=False)
    approved_by_id = fields.Many2one('res.users', readonly=True, copy=False)
    approval_date = fields.Datetime(readonly=True, copy=False)

    _sql_constraints = [
        ('final_score_range', 'CHECK (final_score >= 0 AND final_score <= 1)',
         'The final score must be between 0.0 and 1.0.'),
    ]

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends('level')
    def _compute_level_sequence(self):
        for objective in self:
            objective.level_sequence = LEVEL_SEQUENCE.get(objective.level, 9)

    @api.depends('employee_id', 'level')
    def _compute_department_id(self):
        for objective in self:
            if objective.level == 'individual' and objective.employee_id:
                objective.department_id = objective.employee_id.department_id
            elif objective.level == 'company':
                objective.department_id = False

    @api.depends('employee_id', 'department_id', 'level')
    def _compute_owner_id(self):
        for objective in self:
            if objective.level == 'individual' and objective.employee_id.user_id:
                objective.owner_id = objective.employee_id.user_id
            elif objective.level == 'department' and objective.department_id.manager_id.user_id and not objective.owner_id:
                objective.owner_id = objective.department_id.manager_id.user_id
            elif not objective.owner_id:
                objective.owner_id = self.env.user

    @api.depends('parent_key_result_id')
    def _compute_parent_id(self):
        for objective in self:
            if objective.parent_key_result_id:
                objective.parent_id = objective.parent_key_result_id.objective_id

    def _compute_key_result_count(self):
        for objective in self:
            objective.key_result_count = len(objective.key_result_ids)

    @api.depends('key_result_ids.progress', 'key_result_ids.weight', 'key_result_ids.confidence',
                 'key_result_ids.last_checkin_date')
    def _compute_progress(self):
        for objective in self:
            krs = objective.key_result_ids
            total_weight = sum(krs.mapped('weight'))
            if total_weight:
                objective.progress = sum(kr.progress * kr.weight for kr in krs) / total_weight
            else:
                objective.progress = 0.0
            confidences = [int(kr.confidence) for kr in krs if kr.confidence]
            objective.confidence = sum(confidences) / len(confidences) if confidences else 0.0
            dates = [d for d in krs.mapped('last_checkin_date') if d]
            objective.last_checkin_date = max(dates) if dates else False

    @api.depends('key_result_ids', 'owner_id', 'cycle_id', 'level', 'parent_id', 'parent_key_result_id')
    def _compute_quality_hint(self):
        """OKR good practices: 3-5 objectives per owner, 2-5 key results each, aligned upwards."""
        counts = {}
        if self.ids:
            data = self.sudo()._read_group(
                [('owner_id', 'in', self.owner_id.ids), ('cycle_id', 'in', self.cycle_id.ids),
                 ('state', 'not in', ('cancelled',)), ('level', 'in', self.mapped('level'))],
                ['owner_id', 'cycle_id', 'level'], ['__count'])
            counts = {(owner.id, cycle.id, level): count for owner, cycle, level, count in data}
        for objective in self:
            hints = []
            kr_count = len(objective.key_result_ids)
            if kr_count < 2:
                hints.append(_('Measure this objective with at least 2 key results.'))
            elif kr_count > 5:
                hints.append(_('More than 5 key results: keep the 3 to 5 that matter most.'))
            if counts.get((objective.owner_id.id, objective.cycle_id.id, objective.level), 0) > 5:
                hints.append(_('%s has more than 5 objectives in this cycle: focus on fewer.', objective.owner_id.name))
            if objective.level != 'company' and not objective.parent_id:
                hints.append(_('Align this objective to an upper key result so that everyone pulls in the same direction.'))
            objective.quality_hint = ' '.join(hints)

    def _my_team_domain(self):
        # Employees are private for non HR users: resolve the team with sudo.
        uid = self.env.uid
        employees = self.env['hr.employee'].sudo().with_context(active_test=False).search(
            [('okr_manager_user_ids', 'in', [uid])])
        departments = self.env['hr.department'].sudo().with_context(active_test=False).search(
            [('okr_manager_user_ids', 'in', [uid])])
        return ['|', ('employee_id', 'in', employees.ids), ('department_id', 'in', departments.ids)]

    def _compute_is_my_team(self):
        team = self.search(self._my_team_domain() + [('id', 'in', self.ids)])
        for objective in self:
            objective.is_my_team = objective in team

    def _search_is_my_team(self, operator, value):
        if operator not in ('=', '!=') or not isinstance(value, bool):
            raise NotImplementedError(_('Operation not supported'))
        domain = self._my_team_domain()
        return domain if (operator == '=') == value else ['!'] + domain

    @api.depends('key_result_ids.progress_history', 'key_result_ids.weight')
    def _compute_progress_history(self):
        today = fields.Date.context_today(self)
        for objective in self:
            krs = objective.key_result_ids
            total_weight = sum(krs.mapped('weight'))
            if not objective.cycle_id or not krs or not total_weight:
                objective.progress_history = False
                continue
            histories = {kr.id: kr._history_points() for kr in krs}
            dates = sorted({d for points in histories.values() for d, _v in points})

            def value_at(points, day):
                value = points[0][1]
                for point_day, point_value in points:
                    if point_day > day:
                        break
                    value = point_value
                return value

            points = [[fields.Date.to_string(day), round(sum(
                value_at(histories[kr.id], day) * kr.weight for kr in krs) / total_weight, 1)] for day in dates]
            if round(points[-1][1], 1) != round(objective.progress, 1):
                points.append([fields.Date.to_string(min(today, objective.cycle_id.date_end)), round(objective.progress, 1)])
            objective.progress_history = {
                'start': fields.Date.to_string(objective.cycle_id.date_start),
                'end': fields.Date.to_string(objective.cycle_id.date_end),
                'today': fields.Date.to_string(today),
                'points': points,
            }

    def _compute_expected_progress(self):
        today = fields.Date.context_today(self)
        for objective in self:
            objective.expected_progress = time_progress(objective.date_start, objective.date_end, today)

    @api.depends('progress', 'confidence', 'state', 'cycle_id.date_start', 'cycle_id.date_end')
    def _compute_status(self):
        today = fields.Date.context_today(self)
        for objective in self:
            expected = time_progress(objective.date_start, objective.date_end, today)
            objective.status = compute_status(objective.progress, expected, round(objective.confidence))

    # ------------------------------------------------------------------
    # Constraints and permissions
    # ------------------------------------------------------------------
    @api.constrains('parent_id')
    def _check_parent_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('An objective cannot be aligned to itself or to one of its children.'))

    @api.constrains('level', 'employee_id', 'department_id')
    def _check_level_fields(self):
        for objective in self:
            if objective.level == 'department' and not objective.department_id:
                raise ValidationError(_('A department objective needs a department.'))
            if objective.level == 'individual' and not objective.employee_id:
                raise ValidationError(_('An individual objective needs an employee.'))

    def _okr_is_admin(self):
        return self.env.su or self.env.user.has_group('okr_scale.group_okr_admin')

    def _okr_is_manager_of(self):
        """True when the current user manages this objective's department or employee."""
        self.ensure_one()
        user = self.env.user
        return user in self.sudo().department_id.okr_manager_user_ids \
            or user in self.sudo().employee_id.okr_manager_user_ids

    def _check_okr_level_rights(self):
        """Record rules cannot tell which level a user may create, so enforce it here."""
        if self._okr_is_admin():
            return
        user = self.env.user
        for objective in self:
            if objective.level == 'company':
                raise AccessError(_('Only OKR administrators can manage company objectives (%s).', objective.name))
            if objective.level == 'department' and user not in objective.sudo().department_id.okr_manager_user_ids:
                raise AccessError(_('Only the managers of department %s can manage its objectives.',
                                    objective.department_id.display_name))
            if objective.level == 'individual' and objective.sudo().employee_id.user_id != user \
                    and not objective._okr_is_manager_of():
                raise AccessError(_('You can only manage your own individual objectives or those of your team.'))

    @api.model_create_multi
    def create(self, vals_list):
        objectives = super().create(vals_list)
        objectives._check_okr_level_rights()
        objectives._subscribe_contributors()
        return objectives

    def write(self, vals):
        if 'final_score' in vals and not self.env.context.get('okr_auto_grade'):
            vals = dict(vals, graded=True)
        res = super().write(vals)
        if {'level', 'employee_id', 'department_id', 'owner_id'} & set(vals):
            self._check_okr_level_rights()
        if 'contributor_user_ids' in vals:
            self._subscribe_contributors()
        return res

    def _subscribe_contributors(self):
        for objective in self.filtered('contributor_user_ids'):
            objective.sudo().message_subscribe(partner_ids=objective.contributor_user_ids.partner_id.ids)

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def _get_approvers(self):
        """Users allowed to approve this objective."""
        self.ensure_one()
        objective = self.sudo()
        admins = self.env.ref('okr_scale.group_okr_admin').sudo().users
        if objective.level == 'individual':
            approvers = objective.employee_id.okr_manager_user_ids
        elif objective.level == 'department':
            approvers = objective.department_id.parent_id.okr_manager_user_ids
        else:
            approvers = self.env['res.users']
        return approvers or admins

    def _can_approve(self):
        self.ensure_one()
        return self._okr_is_admin() or self.env.user in self._get_approvers()

    def action_submit(self):
        for objective in self:
            if objective.state != 'draft':
                continue
            if not objective.key_result_ids:
                raise UserError(_('Add at least one key result to "%s" before submitting it.', objective.name))
            if not objective.cycle_id.require_approval:
                objective._start()
                continue
            objective.state = 'to_approve'
            approver_users = objective._get_approvers()
            for user in approver_users[:3]:
                objective.activity_schedule(
                    'okr_scale.mail_activity_okr_approval', user_id=user.id,
                    summary=_('Approve objective: %s', objective.name))

    def action_approve(self):
        for objective in self:
            if not objective._can_approve():
                raise AccessError(_('You are not allowed to approve "%s".', objective.name))
            objective._start()
            objective.activity_feedback(['okr_scale.mail_activity_okr_approval'])

    def _start(self):
        self.sudo().write({
            'state': 'running',
            'approved_by_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
        })

    def action_reject(self):
        for objective in self:
            if not objective._can_approve():
                raise AccessError(_('You are not allowed to reject "%s".', objective.name))
            objective.sudo().state = 'draft'
            objective.activity_unlink(['okr_scale.mail_activity_okr_approval'])
            objective.message_post(body=_('Objective sent back to draft by %s.', self.env.user.name))

    def action_done(self):
        for objective in self:
            if objective.state != 'running':
                continue
            objective.write({'state': 'done'})
            if not objective.graded:
                # Proposed grade from the progress; the owner can still adjust it.
                objective.with_context(okr_auto_grade=True).write(
                    {'final_score': round(min(objective.progress, 100.0) / 100.0, 2)})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_draft(self):
        self.write({'state': 'draft'})

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def action_view_key_results(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('okr_scale.okr_key_result_action')
        action['domain'] = [('objective_id', '=', self.id)]
        action['context'] = {'default_objective_id': self.id}
        return action

    def action_view_children(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('okr_scale.okr_objective_action')
        action['domain'] = [('parent_id', '=', self.id)]
        action['context'] = {'default_parent_id': self.id, 'default_cycle_id': self.cycle_id.id}
        return action

    @api.model
    def _cron_recompute_status(self):
        """The expected progress moves every day, so refresh the stored statuses."""
        objectives = self.search([('state', '=', 'running')])
        krs = objectives.key_result_ids
        self.env.add_to_compute(self.env['okr.scale.key.result']._fields['status'], krs)
        self.env.add_to_compute(self._fields['status'], objectives)
        objectives.flush_recordset()
        krs.flush_recordset()
