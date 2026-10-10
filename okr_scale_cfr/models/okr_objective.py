from odoo import _, fields, models


class OkrObjective(models.Model):
    _inherit = 'okr.scale.objective'

    recognition_ids = fields.One2many('okr.scale.recognition', 'objective_id', 'Recognitions')
    recognition_count = fields.Integer(compute='_compute_recognition_count')
    conversation_count = fields.Integer('1:1s', compute='_compute_conversation_count')

    def _compute_conversation_count(self):
        data = self.env['okr.scale.conversation']._read_group(
            [('objective_ids', 'in', self.ids)], ['objective_ids'], ['__count'])
        counts = {objective.id: count for objective, count in data}
        for objective in self:
            objective.conversation_count = counts.get(objective.id, 0)

    def action_view_conversations(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('okr_scale_cfr.okr_conversation_action')
        user = self.employee_id.user_id or self.owner_id
        action.update({
            'domain': [('objective_ids', 'in', self.id)],
            'context': {
                'default_objective_ids': [(6, 0, self.ids)],
                'default_employee_user_id': user.id if user != self.env.user else False,
            },
        })
        return action

    def _compute_recognition_count(self):
        data = self.env['okr.scale.recognition']._read_group(
            [('objective_id', 'in', self.ids)], ['objective_id'], ['__count'])
        counts = {objective.id: count for objective, count in data}
        for objective in self:
            objective.recognition_count = counts.get(objective.id, 0)

    def action_give_kudos(self):
        self.ensure_one()
        receivers = (self.owner_id | self.key_result_ids.owner_id) - self.env.user
        return {
            'type': 'ir.actions.act_window',
            'name': _('Give Kudos'),
            'res_model': 'okr.scale.recognition',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {
                'default_objective_id': self.id,
                'default_receiver_ids': [(6, 0, receivers.ids)],
            },
        }

    def action_view_recognitions(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('okr_scale_cfr.okr_recognition_action')
        action['domain'] = [('objective_id', '=', self.id)]
        action['context'] = {'default_objective_id': self.id}
        return action
