from odoo import _, api, fields, models
from odoo.exceptions import UserError


class OkrRewardRedeem(models.TransientModel):
    _name = 'okr.scale.reward.redeem'
    _description = 'Redeem a Reward'

    item_id = fields.Many2one('okr.scale.reward.item', 'Reward', required=True)
    image_128 = fields.Image(related='item_id.image_128')
    points_cost = fields.Integer(related='item_id.points_cost')
    limited_stock = fields.Boolean(related='item_id.limited_stock')
    stock_qty = fields.Integer(related='item_id.stock_qty')
    quantity = fields.Integer(required=True, default=1)
    note = fields.Text(help='Delivery details, size, colour...')
    total_points = fields.Integer(compute='_compute_points')
    balance = fields.Integer('Current Balance', compute='_compute_points')
    balance_after = fields.Integer('Balance After', compute='_compute_points')

    @api.depends('item_id', 'quantity')
    def _compute_points(self):
        balance = self.env.user.okr_point_balance
        for wizard in self:
            wizard.total_points = wizard.item_id.points_cost * wizard.quantity
            wizard.balance = balance
            wizard.balance_after = balance - wizard.total_points

    def action_confirm(self):
        self.ensure_one()
        if self.quantity <= 0:
            raise UserError(_('The quantity must be positive.'))
        redemption = self.env['okr.scale.redemption'].create({
            'item_id': self.item_id.id,
            'quantity': self.quantity,
            'note': self.note,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'okr.scale.redemption',
            'res_id': redemption.id,
            'view_mode': 'form',
            'target': 'current',
        }
