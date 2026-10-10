from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .res_config_settings import PREORDER_PARAM


class OkrRewardItem(models.Model):
    _inherit = 'okr.scale.reward.item'

    track_inventory = fields.Boolean(
        'Track in Inventory',
        help='Manage this gift as a storable product: the available quantity comes from the warehouse '
             'and approved redemptions create delivery orders. A product is created automatically if needed.')
    inventory_qty = fields.Float('On Hand', compute='_compute_inventory_qty', digits='Product Unit of Measure',
                                 help='Quantity on hand in the warehouse of the company.')
    inventory_free_qty = fields.Float('Free to Use', compute='_compute_inventory_qty',
                                      digits='Product Unit of Measure',
                                      help='Quantity on hand that is not reserved by deliveries yet.')

    @api.model
    def _okr_preorder_allowed(self):
        """Redeeming a tracked gift without stock is allowed unless disabled in the settings."""
        return self.env['ir.config_parameter'].sudo().get_param(PREORDER_PARAM, 'True') != 'False'

    def _okr_warehouse(self, company=None):
        company = company or self.company_id or self.env.company
        return self.env['stock.warehouse'].sudo().search([('company_id', '=', company.id)], limit=1)

    @api.depends('track_inventory', 'product_id')
    def _compute_inventory_qty(self):
        for item in self:
            item.inventory_qty = item.inventory_free_qty = 0.0
            warehouse = item._okr_warehouse()
            if item.track_inventory and item.product_id and warehouse:
                # Quantities are not sensitive: employees need them to know whether a gift is in stock.
                product = item.product_id.sudo().with_context(warehouse=warehouse.id)
                item.inventory_qty = product.qty_available
                item.inventory_free_qty = product.free_qty

    # ------------------------------------------------------------------
    # Product
    # ------------------------------------------------------------------
    def _okr_prepare_product_values(self):
        self.ensure_one()
        return {
            'name': self.name,
            'type': 'product',
            'sale_ok': False,
            'purchase_ok': True,
            'image_1920': self.image_1920,
            'company_id': self.company_id.id,
            'description': self.description,
        }

    def _okr_ensure_product(self):
        for item in self.filtered(lambda i: i.track_inventory and not i.product_id):
            item.product_id = self.env['product.product'].sudo().create(item._okr_prepare_product_values())

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('track_inventory'):
                vals['limited_stock'] = False
        items = super().create(vals_list)
        items._okr_ensure_product()
        return items

    def write(self, vals):
        if vals.get('track_inventory'):
            vals['limited_stock'] = False
        res = super().write(vals)
        if vals.get('track_inventory') or 'product_id' in vals:
            self._okr_ensure_product()
        return res

    @api.onchange('track_inventory')
    def _onchange_track_inventory(self):
        if self.track_inventory:
            self.limited_stock = False

    @api.constrains('track_inventory', 'product_id')
    def _check_inventory_product(self):
        for item in self:
            if item.track_inventory and item.product_id and item.product_id.type != 'product':
                raise ValidationError(_('The product of "%s" must be a storable product to be tracked in inventory.',
                                        item.name))

    # ------------------------------------------------------------------
    # Stock hooks of okr_scale_reward
    # ------------------------------------------------------------------
    def _okr_pending_qty(self, exclude=None):
        """Quantity requested but not approved yet (no delivery reserves it so far)."""
        self.ensure_one()
        domain = [('item_id', '=', self.id), ('state', '=', 'requested')]
        if exclude:
            domain.append(('id', 'not in', exclude.ids))
        data = self.env['okr.scale.redemption'].sudo()._read_group(domain, [], ['quantity:sum'])
        return data[0][0] or 0

    def _okr_stock_limit(self):
        self.ensure_one()
        if not self.track_inventory:
            return super()._okr_stock_limit()
        return int(self.inventory_free_qty) - self._okr_pending_qty()

    def _okr_allows_preorder(self):
        if self.track_inventory:
            return self._okr_preorder_allowed()
        return super()._okr_allows_preorder()

    def _okr_reserve_stock(self, quantity, redemption=None):
        self.ensure_one()
        if not self.track_inventory:
            return super()._okr_reserve_stock(quantity, redemption=redemption)
        if not self.product_id:
            raise UserError(_('The reward "%s" has no product to deliver.', self.name))
        self.invalidate_recordset(['inventory_qty', 'inventory_free_qty'])
        available = int(self.inventory_free_qty) - self._okr_pending_qty(exclude=redemption)
        if available < quantity and not self._okr_preorder_allowed():
            raise UserError(_('Only %(qty)s "%(item)s" left in stock.', qty=max(available, 0), item=self.name))
        return None

    def _okr_release_stock(self, quantity, redemption=None):
        if not self.track_inventory:
            return super()._okr_release_stock(quantity, redemption=redemption)
        # The delivery of the redemption is cancelled by the redemption itself.
        return None

    @api.depends('limited_stock', 'stock_qty', 'track_inventory', 'product_id')
    def _compute_stock_status(self):
        return super()._compute_stock_status()

    def action_view_product_stock(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'res_id': self.product_id.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
        }
