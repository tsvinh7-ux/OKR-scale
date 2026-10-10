from odoo import _, fields, models


class OkrKeyResult(models.Model):
    _inherit = 'okr.scale.key.result'

    okr_reward_granted = fields.Boolean('Achievement Points Granted', readonly=True, copy=False)

    def write(self, vals):
        res = super().write(vals)
        if set(vals) - {'okr_reward_granted'}:
            self._okr_reward_achieved()
        return res

    def _okr_reward_achieved(self):
        """Grant the owner points once, the first time the key result is achieved.

        Only key results that were part of the objective when it started count,
        so adding an easy key result to a running objective does not farm points.
        """
        Transaction = self.env['okr.scale.point.transaction']
        points = Transaction._get_reward_param('kr_achieved_points')
        if not points:
            return
        for kr in self.sudo():
            objective = kr.objective_id
            if kr.okr_reward_granted or not kr.achieved or not kr.owner_id \
                    or kr.objective_state not in ('running', 'done'):
                continue
            if objective.approval_date and kr.create_date and kr.create_date > objective.approval_date:
                continue
            kr.write({'okr_reward_granted': True})
            Transaction._grant(kr.owner_id, points, 'kr_achieved',
                               _('Key result achieved: %s', kr.name), source=kr)
