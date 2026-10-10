from datetime import timedelta

from odoo import _, fields, models


class OkrCheckin(models.Model):
    _inherit = 'okr.scale.checkin'

    okr_points_granted = fields.Boolean('Points Granted', readonly=True, copy=False)
    okr_reward_date = fields.Date('Points Granted On', readonly=True, copy=False)

    def action_submit(self):
        drafts = self.filtered(lambda c: c.state == 'draft')
        res = super().action_submit()
        submitted = drafts.filtered(lambda c: c.state == 'submitted')
        submitted._okr_reward_checkin()
        # Key results measured from aligned objectives may be achieved by this check-in too.
        krs = submitted.key_result_id
        parents = krs.objective_id.parent_key_result_id
        while parents - krs:
            krs |= parents
            parents = parents.objective_id.parent_key_result_id
        krs._okr_reward_achieved()
        return res

    def _okr_reward_checkin(self):
        """Reward on-time check-ins, at most once per key result and check-in period.

        The period is measured on the submission date (not on the editable check-in
        date), so submitting many check-ins does not farm points.
        """
        Transaction = self.env['okr.scale.point.transaction']
        points = Transaction._get_reward_param('checkin_points')
        if not points:
            return
        today = fields.Date.context_today(self)
        for checkin in self.sudo():
            kr = checkin.key_result_id
            period = kr.cycle_id.get_checkin_days()
            previous = self.sudo().search_count([
                ('key_result_id', '=', kr.id),
                ('okr_points_granted', '=', True),
                ('okr_reward_date', '>', today - timedelta(days=period)),
            ], limit=1)
            if previous or checkin.user_id.share:
                continue
            checkin.write({'okr_points_granted': True, 'okr_reward_date': today})
            Transaction._grant(checkin.user_id, points, 'checkin',
                               _('Check-in on "%s"', kr.name), source=checkin)
