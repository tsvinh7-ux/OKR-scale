from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

# At most this quantity left: the store shows "Only a few left".
LOW_STOCK = 3


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
    # Availability, displayed on the store cards (extended by okr_scale_reward_stock).
    available_qty = fields.Integer('Available', compute='_compute_stock_status')
    stock_status = fields.Selection([
        ('unlimited', 'Available'),
        ('available', 'In stock'),
        ('low', 'Only a few left'),
        ('out', 'Out of stock'),
        ('preorder', 'Pre-order'),
    ], compute='_compute_stock_status')
    # Wallet of the current user, displayed on the store cards.
    user_balance = fields.Integer('My Points', compute='_compute_user_balance')
    can_redeem = fields.Boolean(compute='_compute_user_balance')
    affordable = fields.Boolean(compute='_compute_user_balance')
    points_missing = fields.Integer('Points Missing', compute='_compute_user_balance')

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

    # ------------------------------------------------------------------
    # Stock hooks: the manual counter here, the inventory in okr_scale_reward_stock
    # ------------------------------------------------------------------
    def _okr_stock_limit(self):
        """Quantity that can still be redeemed, or ``None`` when the reward is unlimited."""
        self.ensure_one()
        return self.stock_qty if self.limited_stock else None

    def _okr_allows_preorder(self):
        """Whether the reward may be redeemed beyond the available quantity."""
        return False

    def _okr_reserve_stock(self, quantity, redemption=None):
        """Check and reserve ``quantity`` units when a redemption is requested."""
        self.ensure_one()
        limit = self._okr_stock_limit()
        if limit is not None and limit < quantity and not self._okr_allows_preorder():
            raise UserError(_('Only %(qty)s "%(item)s" left in stock.', qty=max(limit, 0), item=self.name))
        if self.limited_stock:
            self.stock_qty -= quantity

    def _okr_release_stock(self, quantity, redemption=None):
        """Give back the units of a rejected or cancelled redemption."""
        self.ensure_one()
        if self.limited_stock:
            self.stock_qty += quantity

    @api.depends('limited_stock', 'stock_qty')
    def _compute_stock_status(self):
        for item in self:
            limit = item._okr_stock_limit()
            item.available_qty = max(limit or 0, 0)
            if limit is None:
                item.stock_status = 'unlimited'
            elif limit <= 0:
                item.stock_status = 'preorder' if item._okr_allows_preorder() else 'out'
            else:
                item.stock_status = 'low' if limit <= LOW_STOCK else 'available'

    @api.depends_context('uid')
    @api.depends('points_cost', 'limited_stock', 'stock_qty')
    def _compute_user_balance(self):
        balance = self.env.user.okr_point_balance
        for item in self:
            item.user_balance = balance
            item.affordable = balance >= item.points_cost
            item.points_missing = max(item.points_cost - balance, 0)
            item.can_redeem = item.affordable and item.stock_status != 'out'

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
            'context': {'default_item_id': self.id, 'dialog_size': 'medium'},
        }

    def action_view_redemptions(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('okr_scale_reward.okr_redemption_action_all')
        action['domain'] = [('item_id', '=', self.id)]
        action['context'] = {}
        return action

    @api.model
    def _okr_store_banner_values(self):
        user = self.env.user
        pending = self.env['okr.scale.redemption'].search_count(
            [('user_id', '=', user.id), ('state', 'in', ('requested', 'approved'))])
        affordable = self.search_count([('points_cost', '<=', user.okr_point_balance)])
        return {
            'balance': user.okr_point_balance,
            'budget_left': user.okr_give_budget_left,
            'pending': pending,
            'affordable': affordable,
        }
