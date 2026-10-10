from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

from .okr_common import CONFIDENCE


class OkrCheckin(models.Model):
    _name = 'okr.scale.checkin'
    _description = 'OKR Check-in'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'
    _rec_name = 'key_result_id'

    key_result_id = fields.Many2one('okr.scale.key.result', 'Key Result', required=True, index=True,
                                    ondelete='cascade')
    objective_id = fields.Many2one(related='key_result_id.objective_id', store=True, index=True)
    cycle_id = fields.Many2one(related='key_result_id.cycle_id', store=True)
    company_id = fields.Many2one(related='key_result_id.company_id', store=True)
    department_id = fields.Many2one(related='key_result_id.department_id', store=True)
    progress_method = fields.Selection(related='key_result_id.progress_method')
    metric_type = fields.Selection(related='key_result_id.metric_type')
    unit = fields.Char(related='key_result_id.unit')
    target_value = fields.Float(related='key_result_id.target_value')
    user_id = fields.Many2one('res.users', 'Author', required=True, default=lambda self: self.env.user,
                              readonly=True, index=True)
    date = fields.Date(required=True, default=fields.Date.context_today, index=True)

    value_before = fields.Float('Previous Value', readonly=True)
    new_value = fields.Float('New Value')
    progress_before = fields.Float(readonly=True)
    progress_after = fields.Float('Progress', readonly=True)
    confidence = fields.Selection(CONFIDENCE, required=True, default='7',
                                  help='1 = no chance to reach the target, 10 = certain.')
    mood = fields.Selection([
        ('great', 'Great'),
        ('good', 'Good'),
        ('neutral', 'Neutral'),
        ('struggling', 'Struggling'),
    ], default='good')
    achievements = fields.Text('What did you achieve?')
    blockers = fields.Text('What is blocking you?')
    next_steps = fields.Text('Plan for the next period')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('reviewed', 'Reviewed'),
    ], default='draft', required=True, tracking=True, index=True)
    manager_feedback = fields.Text()
    weekly_id = fields.Many2one('okr.scale.weekly', 'Weekly Check-in', index=True, ondelete='set null')
    reviewer_id = fields.Many2one('res.users', readonly=True)
    review_date = fields.Datetime(readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        kr = self.env['okr.scale.key.result'].browse(res.get('key_result_id'))
        if kr.exists():
            res.setdefault('new_value', kr.current_value)
            res.setdefault('confidence', kr.confidence or '7')
        return res

    @api.onchange('key_result_id')
    def _onchange_key_result_id(self):
        if self.key_result_id:
            self.new_value = self.key_result_id.current_value
            self.confidence = self.key_result_id.confidence or '7'

    def _check_can_update_key_result(self):
        """The author must be allowed to report on the key result."""
        self.ensure_one()
        if self.env.su:
            return
        kr = self.key_result_id
        user = self.env.user
        objective = kr.objective_id
        if user in (kr.owner_id | objective.owner_id | objective.sudo().employee_id.user_id) \
                or objective._okr_is_admin() or objective._okr_is_manager_of():
            return
        raise AccessError(_('Only the owners and managers of "%s" can check in on it.', kr.name))

    def action_submit(self):
        for checkin in self:
            if checkin.state != 'draft':
                continue
            checkin._check_can_update_key_result()
            kr = checkin.key_result_id.sudo()
            if kr.objective_state != 'running':
                raise UserError(_('You can only check in on key results of running objectives.'))
            vals = {
                'value_before': kr.current_value,
                'progress_before': kr.progress,
                'state': 'submitted',
            }
            kr_vals = {'confidence': checkin.confidence}
            if kr.progress_method == 'manual':
                kr_vals['current_value'] = checkin.new_value
            kr.write(kr_vals)
            vals['progress_after'] = kr.progress
            checkin.write(vals)
            checkin._post_on_key_result()
            kr.activity_feedback(['okr_scale.mail_activity_okr_checkin'],
                                 user_id=checkin.user_id.id,
                                 feedback=_('Check-in submitted'))
        return True

    def _post_on_key_result(self):
        self.ensure_one()
        body = _('%(user)s checked in: progress %(before).0f%% → %(after).0f%%, confidence %(conf)s/10.',
                 user=self.user_id.name, before=self.progress_before, after=self.progress_after,
                 conf=self.confidence)
        self.key_result_id.sudo().message_post(body=body, subtype_xmlid='mail.mt_note')

    def action_review(self):
        for checkin in self:
            objective = checkin.objective_id
            if not (objective._okr_is_admin() or objective._okr_is_manager_of()):
                raise AccessError(_('Only managers can review check-ins.'))
            checkin.write({
                'state': 'reviewed',
                'reviewer_id': self.env.user.id,
                'review_date': fields.Datetime.now(),
            })
            if checkin.manager_feedback:
                checkin.message_post(body=checkin.manager_feedback, partner_ids=checkin.user_id.partner_id.ids,
                                     subtype_xmlid='mail.mt_comment')

    def action_submit_and_close(self):
        self.action_submit()
        return {'type': 'ir.actions.act_window_close'}
