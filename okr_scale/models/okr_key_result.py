from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError

from .okr_common import CONFIDENCE, STATUSES, compute_status, time_progress

# Fields that define the commitment of a key result: frozen for owners once running.
COMMITMENT_FIELDS = {'start_value', 'target_value', 'weight', 'metric_type', 'progress_method'}


class OkrKeyResult(models.Model):
    _name = 'okr.scale.key.result'
    _description = 'OKR Key Result'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'objective_id, sequence, id'
    _mail_post_access = 'read'

    name = fields.Char('Key Result', required=True, tracking=True)
    description = fields.Text()
    sequence = fields.Integer(default=10)
    objective_id = fields.Many2one('okr.scale.objective', 'Objective', required=True, index=True,
                                   ondelete='cascade')
    cycle_id = fields.Many2one(related='objective_id.cycle_id', store=True, index=True)
    company_id = fields.Many2one(related='objective_id.company_id', store=True, index=True)
    level = fields.Selection(related='objective_id.level', store=True)
    department_id = fields.Many2one(related='objective_id.department_id', store=True)
    objective_state = fields.Selection(related='objective_id.state', string='Objective Status', store=True)
    owner_id = fields.Many2one(
        'res.users', 'Owner', index=True, tracking=True,
        compute='_compute_owner_id', store=True, readonly=False, precompute=True,
        help='Person responsible for checking in on this key result.')
    deadline = fields.Date()
    contributor_ids = fields.Many2many(
        'res.users', 'okr_scale_key_result_contrib_rel', 'key_result_id', 'user_id', string='Supporting People',
        domain=[('share', '=', False)], tracking=True,
        help='People helping the owner on this key result. The owner stays accountable and checks in.')

    metric_type = fields.Selection([
        ('number', 'Number'),
        ('percent', 'Percentage'),
        ('currency', 'Amount'),
        ('boolean', 'Done / Not done'),
    ], default='number', required=True)
    unit = fields.Char(help='Unit displayed next to values, e.g. customers, leads, hours.')
    currency_id = fields.Many2one(related='company_id.currency_id')
    start_value = fields.Float('Start', tracking=True)
    target_value = fields.Float('Target', default=100.0, tracking=True)
    current_value = fields.Float('Current', tracking=True)
    weight = fields.Float(default=1.0, tracking=True,
                          help='Relative importance of this key result inside its objective.')
    progress_method = fields.Selection([
        ('manual', 'Manual (check-ins)'),
        ('objectives', 'From aligned objectives'),
    ], 'Measured By', default='manual', required=True, tracking=True)

    progress = fields.Float(compute='_compute_progress', store=True, recursive=True, group_operator='avg')
    confidence = fields.Selection(CONFIDENCE, tracking=True,
                                  help='How confident the owner is to reach the target (1-10), '
                                       'reported at each check-in.')
    status = fields.Selection(STATUSES, compute='_compute_status', store=True, index=True)
    achieved = fields.Boolean(compute='_compute_status', store=True)

    aligned_objective_ids = fields.One2many('okr.scale.objective', 'parent_key_result_id', 'Aligned Objectives')
    aligned_objective_count = fields.Integer(compute='_compute_counts')
    checkin_ids = fields.One2many('okr.scale.checkin', 'key_result_id', 'Check-ins')
    checkin_count = fields.Integer(compute='_compute_counts')
    last_checkin_date = fields.Date(compute='_compute_last_checkin', store=True)
    checkin_due = fields.Boolean(compute='_compute_checkin_due', search='_search_checkin_due')
    progress_history = fields.Json(compute='_compute_progress_history',
                                   help='Actual progress at each check-in against the expected pace.')

    @api.constrains('weight')
    def _check_weight(self):
        if any(kr.weight < 0 for kr in self):
            raise ValidationError(_('The weight of a key result cannot be negative.'))

    @api.constrains('target_value', 'start_value', 'metric_type')
    def _check_values(self):
        for kr in self:
            if kr.metric_type != 'boolean' and kr.progress_method == 'manual' and kr.target_value == kr.start_value:
                raise ValidationError(_('The target of "%s" must differ from its start value.', kr.name))

    @api.onchange('metric_type')
    def _onchange_metric_type(self):
        if self.metric_type == 'boolean':
            self.start_value, self.target_value = 0.0, 1.0
        elif self.metric_type == 'percent':
            self.start_value, self.target_value = 0.0, 100.0

    @api.depends('objective_id')
    def _compute_owner_id(self):
        for kr in self:
            if not kr.owner_id:
                kr.owner_id = kr.objective_id.owner_id

    def _progress_from_values(self):
        self.ensure_one()
        if self.metric_type == 'boolean':
            return 100.0 if self.current_value >= 1 else 0.0
        span = self.target_value - self.start_value
        if not span:
            return 100.0 if self.current_value == self.target_value else 0.0
        # Works for decreasing targets too: the span is then negative.
        return max(0.0, min(100.0, (self.current_value - self.start_value) * 100.0 / span))

    def _compute_progress_by_method(self):
        """Hook for other modules: return the progress for a non manual method."""
        self.ensure_one()
        if self.progress_method == 'objectives':
            objectives = self.aligned_objective_ids.filtered(lambda o: o.state != 'cancelled')
            return sum(objectives.mapped('progress')) / len(objectives) if objectives else 0.0
        return self._progress_from_values()

    @api.depends('progress_method', 'metric_type', 'start_value', 'target_value', 'current_value',
                 'aligned_objective_ids.progress', 'aligned_objective_ids.state')
    def _compute_progress(self):
        for kr in self:
            if kr.progress_method == 'manual':
                kr.progress = kr._progress_from_values()
            else:
                kr.progress = kr._compute_progress_by_method()

    @api.depends('progress', 'confidence', 'cycle_id.date_start', 'cycle_id.date_end', 'deadline')
    def _compute_status(self):
        today = fields.Date.context_today(self)
        for kr in self:
            expected = time_progress(kr.cycle_id.date_start, kr.deadline or kr.cycle_id.date_end, today)
            kr.status = compute_status(kr.progress, expected, kr.confidence)
            kr.achieved = kr.progress >= 100

    def _history_points(self):
        """[(date, progress)] from the submitted check-ins, oldest first."""
        self.ensure_one()
        checkins = self.checkin_ids.filtered(lambda c: c.state != 'draft').sorted(lambda c: (c.date, c.id))
        start = self.cycle_id.date_start
        points = [(start, checkins[:1].progress_before if checkins else 0.0)]
        for checkin in checkins:
            points.append((max(checkin.date, start), checkin.progress_after))
        # several check-ins the same day: keep the last one
        return [point for i, point in enumerate(points) if i + 1 == len(points) or points[i + 1][0] != point[0]]

    @api.depends('checkin_ids.progress_after', 'checkin_ids.state', 'progress', 'cycle_id.date_start',
                 'cycle_id.date_end', 'deadline')
    def _compute_progress_history(self):
        today = fields.Date.context_today(self)
        for kr in self:
            if not kr.cycle_id:
                kr.progress_history = False
                continue
            points = kr._history_points()
            if points[-1][0] <= today and round(points[-1][1], 1) != round(kr.progress, 1):
                points.append((min(today, kr.cycle_id.date_end), kr.progress))
            kr.progress_history = {
                'start': fields.Date.to_string(kr.cycle_id.date_start),
                'end': fields.Date.to_string(kr.deadline or kr.cycle_id.date_end),
                'today': fields.Date.to_string(today),
                'points': [[fields.Date.to_string(d), round(v, 1)] for d, v in points],
            }

    def _compute_counts(self):
        for kr in self:
            kr.aligned_objective_count = len(kr.aligned_objective_ids)
            kr.checkin_count = len(kr.checkin_ids)

    @api.depends('checkin_ids.state', 'checkin_ids.date')
    def _compute_last_checkin(self):
        for kr in self:
            dates = kr.checkin_ids.filtered(lambda c: c.state != 'draft').mapped('date')
            kr.last_checkin_date = max(dates) if dates else False

    def _is_checkin_due(self, today=None):
        self.ensure_one()
        if self.objective_state != 'running' or self.cycle_id.state != 'open':
            return False
        today = today or fields.Date.context_today(self)
        if today < self.cycle_id.date_start:
            return False
        cycle = self.cycle_id
        started = self.objective_id.approval_date.date() if self.objective_id.approval_date else cycle.date_start
        if cycle.checkin_frequency == 'weekly':
            window_start = cycle.get_checkin_window_start(today)
            checkin_day = window_start + timedelta(days=int(cycle.checkin_weekday))
            if today < checkin_day or started > checkin_day:
                return False
            return not self.last_checkin_date or self.last_checkin_date < window_start
        reference = self.last_checkin_date or started
        return (today - reference).days >= cycle.get_checkin_days()

    def _compute_checkin_due(self):
        today = fields.Date.context_today(self)
        for kr in self:
            kr.checkin_due = kr._is_checkin_due(today)

    def _search_checkin_due(self, operator, value):
        if operator not in ('=', '!=') or not isinstance(value, bool):
            raise NotImplementedError(_('Operation not supported'))
        candidates = self.search([('objective_state', '=', 'running'), ('cycle_id.state', '=', 'open')])
        due = candidates.filtered(lambda kr: kr._is_checkin_due())
        positive = (operator == '=') == value
        return [('id', 'in' if positive else 'not in', due.ids)]

    def write(self, vals):
        if COMMITMENT_FIELDS & set(vals) and not self.env.su:
            for kr in self:
                objective = kr.objective_id
                if objective.state in ('running', 'done') and not objective._okr_is_admin() \
                        and not objective._okr_is_manager_of():
                    raise AccessError(_(
                        'The objective "%s" is running: only its managers can change the target, '
                        'weight or measure of its key results.', objective.name))
        return super().write(vals)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def action_checkin(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Check-in: %s', self.name),
            'res_model': 'okr.scale.checkin',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_key_result_id': self.id},
        }

    def action_view_checkins(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('okr_scale.okr_checkin_action')
        action['domain'] = [('key_result_id', '=', self.id)]
        action['context'] = {'default_key_result_id': self.id}
        return action

    def action_view_aligned_objectives(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('okr_scale.okr_objective_action')
        action['domain'] = [('parent_key_result_id', '=', self.id)]
        action['context'] = {
            'default_parent_key_result_id': self.id,
            'default_cycle_id': self.cycle_id.id,
        }
        return action

    @api.model
    def _cron_checkin_reminder(self):
        """Hourly: on the check-in day of each cycle, from the check-in time, remind the
        owners of key results not checked in yet this period."""
        activity_type = self.env.ref('okr_scale.mail_activity_okr_checkin')
        now = fields.Datetime.context_timestamp(
            self.with_context(tz=self.env.user.tz or 'Asia/Ho_Chi_Minh'), fields.Datetime.now())
        today = now.date()
        notified = self.browse()
        for kr in self.search([('checkin_due', '=', True), ('owner_id', '!=', False)]):
            cycle = kr.cycle_id
            if cycle.checkin_frequency == 'weekly' and (
                    now.weekday() != int(cycle.checkin_weekday) or now.hour + now.minute / 60 < cycle.checkin_hour):
                continue
            kr._notify_checkin_due(activity_type, today)
            notified |= kr
        # One summary message per person and per day, in Odoo (inbox) and by e-mail
        users = notified.owner_id.filtered(lambda u: not u.share and u.okr_checkin_notified_date != today)
        for user in users:
            user._okr_notify_checkin_due(notified.filtered(lambda kr: kr.owner_id == user))
        users.sudo().write({'okr_checkin_notified_date': today})

    def _notify_checkin_due(self, activity_type, today):
        """Internal owners get an activity. Extended by the portal module for portal owners."""
        self.ensure_one()
        if self.owner_id.share:
            return
        if self.activity_ids.filtered(lambda a: a.activity_type_id == activity_type and a.user_id == self.owner_id):
            return
        self.activity_schedule(
            activity_type_id=activity_type.id, user_id=self.owner_id.id, date_deadline=today,
            summary=_('Weekly check-in: %s', self.name))
