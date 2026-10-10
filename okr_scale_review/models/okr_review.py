from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

from .okr_common import score_band


class OkrReview(models.Model):
    _name = 'okr.scale.review'
    _description = 'OKR Cycle Review'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(compute='_compute_name', store=True, readonly=False, precompute=True, required=True,
                       tracking=True)
    cycle_id = fields.Many2one('okr.scale.cycle', 'Cycle', required=True, index=True, ondelete='cascade',
                               tracking=True,
                               default=lambda self: self.env['okr.scale.cycle'].get_current_cycle())
    company_id = fields.Many2one(related='cycle_id.company_id', store=True, index=True)
    review_type = fields.Selection([
        ('mid', 'Mid-cycle review'),
        ('final', 'End-of-cycle retrospective'),
    ], 'Type', required=True, default='mid', tracking=True)
    department_id = fields.Many2one(
        'hr.department', 'Department', index=True, tracking=True,
        help='Leave empty for a company-wide review. A department review covers its sub-departments too.')
    date = fields.Date(required=True, default=fields.Date.context_today, tracking=True)
    facilitator_id = fields.Many2one('res.users', 'Facilitator', default=lambda self: self.env.user,
                                     domain=[('share', '=', False)], tracking=True)
    participant_ids = fields.Many2many('res.users', 'okr_scale_review_participant_rel', 'review_id', 'user_id',
                                       'Participants', domain=[('share', '=', False)])
    state = fields.Selection([('draft', 'In Progress'), ('done', 'Done')], default='draft', required=True,
                             tracking=True, copy=False)
    went_well = fields.Html('What Went Well')
    to_improve = fields.Html('What To Improve')
    lessons = fields.Html('Lessons Learned')
    decisions = fields.Html('Decisions & Next Actions')

    # Snapshot of the figures, refreshed while in progress and frozen once done
    snapshot_date = fields.Datetime('Figures Updated On', readonly=True, copy=False)
    snapshot_objective_count = fields.Integer('Objectives', readonly=True, copy=False)
    snapshot_kr_count = fields.Integer('Key Results', readonly=True, copy=False)
    snapshot_kr_achieved = fields.Integer('Key Results Achieved', readonly=True, copy=False)
    snapshot_avg_progress = fields.Float('Average Progress', readonly=True, copy=False)
    snapshot_avg_score = fields.Float('Average Score', readonly=True, copy=False, digits=(3, 2),
                                      help='0.0 - 1.0. Final score of graded objectives; during the cycle, '
                                           'projected score of running ones (progress / time elapsed).')
    snapshot_on_track = fields.Integer('On Track', readonly=True, copy=False)
    snapshot_at_risk = fields.Integer('At Risk', readonly=True, copy=False)
    snapshot_off_track = fields.Integer('Off Track', readonly=True, copy=False)
    snapshot_achieved = fields.Integer('Achieved', readonly=True, copy=False)
    snapshot_band_red = fields.Integer('Score < 0.4', readonly=True, copy=False)
    snapshot_band_yellow = fields.Integer('Score 0.4 - 0.69', readonly=True, copy=False)
    snapshot_band_green = fields.Integer('Score >= 0.7', readonly=True, copy=False)
    snapshot_band = fields.Selection([('red', 'Red'), ('yellow', 'Yellow'), ('green', 'Green')],
                                     compute='_compute_snapshot_band', string='Score Band')
    objective_ids = fields.Many2many('okr.scale.objective', compute='_compute_objective_ids',
                                     string='Objectives Reviewed')

    @api.depends('review_type', 'cycle_id', 'department_id')
    def _compute_name(self):
        type_labels = dict(self._fields['review_type']._description_selection(self.env))
        for review in self:
            parts = [type_labels.get(review.review_type, ''), review.cycle_id.name or '',
                     review.department_id.name or _('Company-wide')]
            review.name = ' · '.join(p for p in parts if p)

    @api.depends('snapshot_avg_score', 'snapshot_objective_count')
    def _compute_snapshot_band(self):
        for review in self:
            review.snapshot_band = score_band(review.snapshot_avg_score) if review.snapshot_objective_count else False

    def _compute_objective_ids(self):
        Board = self.env['okr.scale.review.board']
        for review in self:
            if review.cycle_id:
                review.objective_ids = self.env['okr.scale.objective'].search(
                    Board._scope_domain(review.cycle_id, review.department_id.id))
            else:
                review.objective_ids = False

    # ------------------------------------------------------------------
    # Permissions
    # ------------------------------------------------------------------
    @api.model
    def _okr_can_create_review(self, department_id=False):
        """Admins review anything; managers review the departments they manage."""
        user = self.env.user
        if self.env.su or user.has_group('okr_scale.group_okr_admin'):
            return True
        if not user.has_group('okr_scale.group_okr_manager'):
            return False
        if department_id:
            department = self.env['hr.department'].sudo().browse(department_id)
            return user in department.okr_manager_user_ids
        return bool(self._okr_managed_departments())

    @api.model
    def _okr_managed_departments(self):
        """Top-most departments managed by the current user."""
        departments = self.env['hr.department'].sudo().search(
            [('okr_manager_user_ids', 'in', [self.env.uid])])
        return departments.filtered(lambda d: self.env.user not in d.parent_id.okr_manager_user_ids)

    def _check_okr_review_rights(self):
        """Record rules already restrict writes; give a clear message for the common mistakes."""
        if self.env.su or self.env.user.has_group('okr_scale.group_okr_admin'):
            return
        for review in self:
            if not review.department_id:
                raise AccessError(_('Only OKR administrators can manage company-wide reviews.'))
            if self.env.user not in review.sudo().department_id.okr_manager_user_ids:
                raise AccessError(_('Only the managers of department %s can manage its reviews.',
                                    review.sudo().department_id.display_name))

    # ------------------------------------------------------------------
    # Snapshot
    # ------------------------------------------------------------------
    def _snapshot_values(self):
        """Figures of the review scope, computed with sudo so every reader sees the same numbers."""
        self.ensure_one()
        Board = self.env['okr.scale.review.board']
        cycle = self.cycle_id.sudo()
        objectives = self.env['okr.scale.objective'].sudo().search(
            Board._scope_domain(cycle, self.department_id.id) + [('company_id', '=', cycle.company_id.id)])
        phase, elapsed = Board._cycle_phase(cycle)
        figures = Board._figures(objectives, phase, elapsed)
        krs = objectives.key_result_ids
        return {
            'snapshot_date': fields.Datetime.now(),
            'snapshot_objective_count': figures['count'],
            'snapshot_kr_count': len(krs),
            'snapshot_kr_achieved': len(krs.filtered('achieved')),
            'snapshot_avg_progress': figures['progress'],
            'snapshot_avg_score': figures['score'],
            'snapshot_on_track': figures['status']['on_track'],
            'snapshot_at_risk': figures['status']['at_risk'],
            'snapshot_off_track': figures['status']['off_track'],
            'snapshot_achieved': figures['status']['achieved'],
            'snapshot_band_red': figures['bands']['red'],
            'snapshot_band_yellow': figures['bands']['yellow'],
            'snapshot_band_green': figures['bands']['green'],
        }

    def _refresh_snapshot(self):
        for review in self:
            # super() write: a snapshot is not a change of the review itself
            super(OkrReview, review).write(review._snapshot_values())

    @api.model_create_multi
    def create(self, vals_list):
        reviews = super().create(vals_list)
        reviews._check_okr_review_rights()
        reviews._refresh_snapshot()
        return reviews

    def write(self, vals):
        if 'state' not in vals and any(r.state == 'done' for r in self) \
                and set(vals) & {'cycle_id', 'department_id', 'review_type'}:
            raise UserError(_('Reset the review to "In Progress" before changing its scope.'))
        res = super().write(vals)
        if {'department_id', 'cycle_id'} & set(vals):
            self._check_okr_review_rights()
            self.filtered(lambda r: r.state == 'draft')._refresh_snapshot()
        return res

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def action_refresh_snapshot(self):
        self.filtered(lambda r: r.state == 'draft')._refresh_snapshot()

    def action_done(self):
        for review in self.filtered(lambda r: r.state == 'draft'):
            review._refresh_snapshot()
            review.state = 'done'
            review.message_post(body=_('Review closed. Average score %(score).2f over %(count)s objectives.',
                                       score=review.snapshot_avg_score, count=review.snapshot_objective_count))

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_open_board(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'okr_scale_review.cycle_review',
            'name': _('Cycle Review'),
            'params': {'cycle_id': self.cycle_id.id, 'department_id': self.department_id.id or False},
        }

    def action_view_objectives(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('okr_scale.okr_objective_action')
        action['domain'] = [('id', 'in', self.objective_ids.ids)]
        action['context'] = {}
        return action

    @api.model
    def _bullets(self, rows, fmt):
        if not rows:
            return False
        items = Markup('').join(Markup('<li>%s</li>') % fmt(row) for row in rows)
        return Markup('<ul>%s</ul>') % items

    @api.model
    def action_start_review(self, cycle_id, department_id=False, review_type=False):
        """Create a review meeting prefilled from the cycle review data and open it."""
        if not department_id and not self.env.user.has_group('okr_scale.group_okr_admin'):
            departments = self._okr_managed_departments()
            department_id = departments[:1].id
        if not self._okr_can_create_review(department_id):
            raise AccessError(_('Only OKR administrators and department managers can start a review meeting.'))
        data = self.env['okr.scale.review.board'].get_cycle_review_data(cycle_id, department_id)
        if not data.get('cycle'):
            raise UserError(_('Choose a cycle first.'))

        def objective_line(row):
            return Markup('<b>%s</b> (%s) · %s %.2f') % (row['name'], row['owner'], _('score'), row['score'])

        def quote_line(row):
            return Markup('<i>%s</i> · %s') % (row['text'], row['owner'])

        review = self.create({
            'cycle_id': data['cycle']['id'],
            'department_id': department_id or False,
            'review_type': review_type or data['suggested_review_type'],
            'participant_ids': [(4, self.env.uid)],
            'went_well': self._bullets([r for r in data['highlights'] if r['score'] >= 0.7], objective_line),
            'to_improve': self._bullets(data['lowlights'], objective_line),
            'lessons': self._bullets([q for q in data['quotes'] if q['kind'] == 'lessons_learned'], quote_line),
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': review.id,
            'views': [[False, 'form']],
            'target': 'current',
        }

