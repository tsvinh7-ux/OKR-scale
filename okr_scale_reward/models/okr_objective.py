from odoo import _, fields, models

SUCCESS_SCORE = 0.7


class OkrObjective(models.Model):
    _inherit = 'okr.scale.objective'

    okr_reward_granted = fields.Boolean('Success Points Granted', readonly=True, copy=False)

    def write(self, vals):
        res = super().write(vals)
        if {'state', 'final_score'} & set(vals):
            self._okr_reward_objective()
        return res

    def _okr_reward_objective(self):
        """Grant the owner points once when the objective is closed with a final score >= 0.7."""
        Transaction = self.env['okr.scale.point.transaction']
        points = Transaction._get_reward_param('objective_achieved_points')
        if not points:
            return
        for objective in self.sudo():
            if objective.okr_reward_granted or objective.state != 'done' \
                    or objective.final_score < SUCCESS_SCORE or not objective.owner_id:
                continue
            objective.write({'okr_reward_granted': True})
            Transaction._grant(objective.owner_id, points, 'objective_achieved',
                               _('Objective achieved: %s (score %.2f)', objective.name, objective.final_score),
                               source=objective)
