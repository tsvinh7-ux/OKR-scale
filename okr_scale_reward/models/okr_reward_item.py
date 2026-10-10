from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class OkrRewardCategory(models.Model):
    _name = 'okr.scale.reward.category'
    _description = 'OKR Reward Category'
    _order = 'sequence, name'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    item_ids = fields.One2many('okr.scale.reward.item', 'category_id', 'Rewards')


class OkrRewardItem(models.Model):
    _name = 'okr.scale.reward.item'
    _description = 'OKR Reward'
    _inherit = ['image.mixin']
    _order = 'sequence, points_cost, id'

    name = fields.Char(required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    category_id = fields.Many2one('okr.scale.reward.category', 'Category', index=True)
    points_cost = fields.Integer('Cost (points)', required=True, default=100)
    limited_stock = fields.Boolean(help='Track the number of gifts still available.')
    stock_qty = fields.Integer('Available Quantity', default=0)
    product_id = fields.Many2one('product.product', 'Product', check_company=True,
                                 help='Optional product used to purchase or track this gift.')
    company_id = fields.Many2one('res.company', index=True, default=lambda self: self.env.company,
                                 help='Leave empty to offer this reward in every company.')
    redemption_ids = fields.One2many('okr.scale.redemption', 'item_id', 'Redemptions')
    redemption_count = fields.Integer(compute='_compute_redemption_count')
    # Wallet of the current user, displayed on the store cards.
    user_balance = fields.Integer('My Points', compute='_compute_user_balance')
    can_redeem = fields.Boolean(compute='_compute_user_balance')

    _sql_constraints = [
        ('points_cost_positive', 'CHECK (points_cost > 0)', 'The cost of a reward must be positive.'),
        ('stock_qty_positive', 'CHECK (stock_qty >= 0)', 'The available quantity cannot be negative.'),
    ]

    def _compute_redemption_count(self):
        data = self.env['okr.scale.redemption']._read_group(
            [('item_id', 'in', self.ids), ('state', 'not in', ('rejected', 'cancelled'))], ['item_id'], ['__count'])
        counts = {item.id: count for item, count in data}
        for item in self:
            item.redemption_count = counts.get(item.id, 0)

    @api.depends_context('uid')
    @api.depends('points_cost', 'limited_stock', 'stock_qty')
    def _compute_user_balance(self):
        balance = self.env.user.okr_point_balance
        for item in self:
            item.user_balance = balance
            item.can_redeem = balance >= item.points_cost and (not item.limited_stock or item.stock_qty > 0)

    @api.constrains('limited_stock', 'stock_qty')
    def _check_stock(self):
        if any(item.stock_qty < 0 for item in self):
            raise ValidationError(_('The available quantity cannot be negative.'))

    def action_redeem(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Redeem %s', self.name),
            'res_model': 'okr.scale.reward.redeem',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_item_id': self.id},
        }

    def action_view_redemptions(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('okr_scale_reward.okr_redemption_action_all')
        action['domain'] = [('item_id', '=', self.id)]
        action['context'] = {}
        return action
