from odoo import _, models

# A check-in at or below this confidence asks the manager for a 1:1.
LOW_CONFIDENCE = 4


class OkrCheckin(models.Model):
    _inherit = 'okr.scale.checkin'

    def action_discuss_in_one_on_one(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Plan a 1:1'),
            'res_model': 'okr.scale.conversation',
            'view_mode': 'form',
            'target': 'current',
            'context': self.env['okr.scale.conversation']._prepare_from_checkin(self),
        }

    def action_submit(self):
        submitted = self.filtered(lambda c: c.state == 'draft')
        res = super().action_submit()
        for checkin in submitted.filtered(lambda c: c.state != 'draft'):
            checkin._ask_manager_for_one_on_one()
        return res

    def _ask_manager_for_one_on_one(self):
        """Low confidence or blockers: remind the direct manager to talk with the owner."""
        self.ensure_one()
        if int(self.confidence) > LOW_CONFIDENCE and not self.blockers:
            return
        employee = self.user_id.sudo().employee_id
        manager = employee.parent_id.user_id or employee.department_id.manager_id.user_id
        if not manager or manager == self.user_id:
            return
        self.key_result_id.sudo().activity_schedule(
            'okr_scale_cfr.mail_activity_okr_one_on_one', user_id=manager.id,
            summary=_('1:1 with %(user)s: %(kr)s (confidence %(conf)s/10)',
                      user=self.user_id.name, kr=self.key_result_id.name, conf=self.confidence))


class OkrWeekly(models.Model):
    _inherit = 'okr.scale.weekly'

    def _one_on_one_action(self):
        return 'okr_scale_cfr.okr_conversation_action'
