from odoo import _, api, fields, models
from odoo.exceptions import UserError


class OkrFeedbackRequest(models.TransientModel):
    _name = 'okr.scale.feedback.request'
    _description = 'Request OKR Feedback'

    giver_ids = fields.Many2many('res.users', string='Ask Feedback From', required=True,
                                 domain=[('share', '=', False)])
    recipient_id = fields.Many2one('res.users', 'About', required=True, default=lambda self: self.env.user,
                                   domain=[('share', '=', False)])
    objective_id = fields.Many2one('okr.scale.objective', 'Objective')
    key_result_id = fields.Many2one('okr.scale.key.result', 'Key Result',
                                    domain="[('objective_id', '=?', objective_id)]")
    feedback_type = fields.Selection(
        lambda self: self.env['okr.scale.feedback']._fields['feedback_type']._description_selection(self.env),
        'Type', required=True, default='constructive')
    message = fields.Text('Request', help='What would you like to get feedback on?')

    @api.onchange('key_result_id')
    def _onchange_key_result_id(self):
        if self.key_result_id:
            self.objective_id = self.key_result_id.objective_id

    def action_request(self):
        self.ensure_one()
        givers = self.giver_ids - self.recipient_id
        if not givers:
            raise UserError(_('Choose at least one person other than the person the feedback is about.'))
        # Access check on the linked OKRs with the requester's rights.
        self.objective_id.check_access_rule('read')
        self.key_result_id.check_access_rule('read')
        Feedback = self.env['okr.scale.feedback'].sudo()
        feedbacks = Feedback.create([{
            'author_id': giver.id,
            'recipient_id': self.recipient_id.id,
            'requested_by_id': self.env.uid,
            'request_message': self.message,
            'objective_id': self.objective_id.id,
            'key_result_id': self.key_result_id.id,
            'feedback_type': self.feedback_type,
            'company_id': self.env.company.id,
            'state': 'requested',
        } for giver in givers])
        for feedback, giver in zip(feedbacks, givers):
            feedback.activity_schedule(
                'okr_scale_cfr.mail_activity_okr_feedback', user_id=giver.id,
                summary=_('%(requester)s asks for your feedback about %(recipient)s',
                          requester=self.env.user.name, recipient=self.recipient_id.name),
                note=self.message or '')
        return {'type': 'ir.actions.act_window_close'}
