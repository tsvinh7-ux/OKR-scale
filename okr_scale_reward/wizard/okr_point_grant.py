from odoo import _, fields, models
from odoo.exceptions import AccessError, UserError


class OkrPointGrant(models.TransientModel):
    _name = 'okr.scale.point.grant'
    _description = 'Grant Reward Points'

    user_ids = fields.Many2many('res.users', string='Users', required=True, domain=[('share', '=', False)])
    points = fields.Integer(required=True, help='Use a negative number to correct a previous grant.')
    reason = fields.Char(required=True)

    def action_grant(self):
        self.ensure_one()
        if not self.env.user.has_group('okr_scale.group_okr_admin'):
            raise AccessError(_('Only OKR administrators can grant points.'))
        if not self.points:
            raise UserError(_('Enter a number of points.'))
        self.env['okr.scale.point.transaction']._grant(self.user_ids, self.points, 'manual', self.reason)
        return {'type': 'ir.actions.act_window_close'}
