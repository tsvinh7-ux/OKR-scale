from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    okr_manager_auto = fields.Boolean(
        'OKR Manager (from HR)', copy=False,
        help='Set when the OKR Manager group was granted automatically because the user manages '
             'a department or employees in the Employees app.')

    @api.model
    def _okr_sync_manager_group(self):
        """Mirror the Employees app hierarchy on the OKR Manager group.

        Department managers and employees having subordinates get the group;
        it is removed again when they stop managing, but only if it had been
        granted automatically.
        """
        group = self.env.ref('okr_scale.group_okr_manager', raise_if_not_found=False)
        if not group:
            return
        sudo_self = self.sudo()
        managers = self.env['hr.department'].sudo().search([]).manager_id.user_id \
            | self.env['hr.employee'].sudo().search([('parent_id', '!=', False)]).parent_id.user_id
        managers = managers.filtered(lambda u: not u.share)
        to_add = managers.filtered(lambda u: group not in u.groups_id)
        if to_add:
            to_add.write({'groups_id': [(4, group.id)], 'okr_manager_auto': True})
        admin_group = self.env.ref('okr_scale.group_okr_admin')
        to_remove = sudo_self.search([('okr_manager_auto', '=', True)]) - managers
        to_remove = to_remove.filtered(lambda u: admin_group not in u.groups_id)
        if to_remove:
            to_remove.write({'groups_id': [(3, group.id)], 'okr_manager_auto': False})
