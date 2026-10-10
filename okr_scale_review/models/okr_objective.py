from odoo import fields, models


class OkrObjective(models.Model):
    _inherit = 'okr.scale.objective'

    carried_from_id = fields.Many2one(
        'okr.scale.objective', 'Carried Over From', index=True, ondelete='set null', readonly=True, copy=False,
        help='Objective of a previous cycle this objective continues.')
    carried_to_ids = fields.One2many('okr.scale.objective', 'carried_from_id', 'Carried Over To')

    def _okr_can_carry_over(self):
        """Mirror of the core level rights: may the current user create this objective in another cycle?"""
        self.ensure_one()
        if self._okr_is_admin():
            return True
        user = self.env.user
        objective = self.sudo()
        if objective.level == 'company':
            return False
        if objective.level == 'department':
            return user in objective.department_id.okr_manager_user_ids
        return objective.employee_id.user_id == user or self._okr_is_manager_of()


class OkrKeyResult(models.Model):
    _inherit = 'okr.scale.key.result'

    carried_from_id = fields.Many2one(
        'okr.scale.key.result', 'Carried Over From', index=True, ondelete='set null', readonly=True, copy=False,
        help='Unfinished key result of a previous cycle this key result continues.')
    carried_to_ids = fields.One2many('okr.scale.key.result', 'carried_from_id', 'Carried Over To')
