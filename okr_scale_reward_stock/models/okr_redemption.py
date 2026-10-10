from odoo import _, fields, models
from odoo.exceptions import UserError


class OkrRedemption(models.Model):
    _inherit = 'okr.scale.redemption'

    picking_id = fields.Many2one('stock.picking', 'Delivery', readonly=True, copy=False, index='btree_not_null',
                                 ondelete='set null')
    picking_state = fields.Selection(related='picking_id.state', string='Delivery Status')
    track_inventory = fields.Boolean(related='item_id.track_inventory')

    # ------------------------------------------------------------------
    # Delivery order
    # ------------------------------------------------------------------
    def _okr_delivery_partner(self):
        self.ensure_one()
        employee = self.user_id.sudo().employee_ids.filtered(lambda e: e.company_id == self.company_id)[:1]
        return employee.work_contact_id or self.user_id.partner_id

    def _okr_prepare_picking_values(self, warehouse):
        self.ensure_one()
        picking_type = warehouse.out_type_id
        partner = self._okr_delivery_partner()
        location = picking_type.default_location_src_id or warehouse.lot_stock_id
        destination = picking_type.default_location_dest_id \
            or partner.property_stock_customer or self.env.ref('stock.stock_location_customers')
        product = self.item_id.product_id
        return {
            'picking_type_id': picking_type.id,
            'partner_id': partner.id,
            'origin': self.name,
            'location_id': location.id,
            'location_dest_id': destination.id,
            'company_id': self.company_id.id,
            'move_ids': [(0, 0, {
                'name': self.item_id.name,
                'product_id': product.id,
                'product_uom_qty': self.quantity,
                'product_uom': product.uom_id.id,
                'location_id': location.id,
                'location_dest_id': destination.id,
                'company_id': self.company_id.id,
            })],
        }

    def _okr_create_picking(self):
        """Create, confirm and reserve the delivery of approved redemptions of tracked gifts."""
        for redemption in self.sudo():
            if not redemption.track_inventory or not redemption.item_id.product_id \
                    or (redemption.picking_id and redemption.picking_id.state != 'cancel'):
                continue
            warehouse = redemption.item_id._okr_warehouse(redemption.company_id)
            if not warehouse:
                raise UserError(_('No warehouse found for company %s.', redemption.company_id.name))
            picking = self.env['stock.picking'].sudo().create(redemption._okr_prepare_picking_values(warehouse))
            picking.action_confirm()
            picking.action_assign()
            redemption.picking_id = picking
            redemption.message_post(body=_('Delivery %s created.', picking.name), subtype_xmlid='mail.mt_note')

    def _okr_validate_picking(self):
        """Validate the delivery: the gift must be fully reserved in the warehouse."""
        for redemption in self.sudo():
            picking = redemption.picking_id
            if not picking or picking.state in ('done', 'cancel'):
                continue
            picking.action_assign()
            moves = picking.move_ids.filtered(lambda m: m.state not in ('done', 'cancel'))
            if picking.state != 'assigned' or any(m.quantity < m.product_uom_qty for m in moves):
                raise UserError(_('"%(item)s" is not in stock yet: receive it in Inventory before delivering %(ref)s.',
                                  item=redemption.item_id.name, ref=redemption.name))
            moves.picked = True
            res = picking.with_context(skip_backorder=True, skip_sms=True).button_validate()
            if isinstance(res, dict) or picking.state != 'done':
                raise UserError(_('The delivery %s needs to be validated in Inventory.', picking.name))

    def _okr_cancel_picking(self):
        pickings = self.sudo().picking_id.filtered(lambda p: p.state not in ('done', 'cancel'))
        if pickings:
            pickings.action_cancel()

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def action_approve(self):
        to_approve = self.filtered(lambda r: r.state == 'requested')
        res = super().action_approve()
        to_approve.filtered(lambda r: r.state == 'approved')._okr_create_picking()
        return res

    def action_deliver(self):
        self._check_reward_manager()
        # Validating the delivery marks the redemption as delivered (see stock.picking).
        self.filtered(lambda r: r.state == 'approved')._okr_validate_picking()
        return super().action_deliver()

    def action_reject(self):
        res = super().action_reject()
        self.filtered(lambda r: r.state == 'rejected')._okr_cancel_picking()
        return res

    def action_cancel(self):
        res = super().action_cancel()
        self.filtered(lambda r: r.state == 'cancelled')._okr_cancel_picking()
        return res

    def action_create_delivery(self):
        self._check_reward_manager()
        self.filtered(lambda r: r.state == 'approved')._okr_create_picking()

    def action_view_picking(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'res_id': self.picking_id.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
        }
