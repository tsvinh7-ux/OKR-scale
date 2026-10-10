from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from odoo.addons.okr_scale.tests.common import OkrCommon


@tagged('post_install', '-at_install')
class TestOkrRewardStock(OkrCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Transaction = cls.env['okr.scale.point.transaction']
        cls.warehouse = cls.env['stock.warehouse'].search([('company_id', '=', cls.env.company.id)], limit=1)
        cls.mug = cls.env['okr.scale.reward.item'].create({
            'name': 'DMAG Mug', 'points_cost': 20, 'track_inventory': True, 'limited_stock': True, 'stock_qty': 7})
        cls.product = cls.mug.product_id
        cls.Transaction._grant(cls.seller, 200, 'manual', 'Test grant')

    def _set_stock(self, qty):
        self.env['stock.quant']._update_available_quantity(self.product, self.warehouse.lot_stock_id, qty)
        self.mug.invalidate_recordset()

    def _redeem(self, user, quantity=1):
        wizard = self.env['okr.scale.reward.redeem'].with_user(user).create(
            {'item_id': self.mug.id, 'quantity': quantity})
        return self.env['okr.scale.redemption'].browse(wizard.action_confirm()['res_id'])

    def _allow_preorder(self, allowed):
        settings = self.env['res.config.settings'].create({'okr_reward_allow_preorder': allowed})
        settings.execute()

    def test_product_created_and_manual_counter_disabled(self):
        self.assertTrue(self.product)
        self.assertEqual(self.product.type, 'product')
        self.assertEqual(self.product.name, 'DMAG Mug')
        self.assertFalse(self.product.sale_ok)
        self.assertFalse(self.mug.limited_stock, 'The inventory replaces the manual counter')
        # Tracking an existing reward creates its product too
        hoodie = self.env['okr.scale.reward.item'].create({'name': 'Hoodie', 'points_cost': 50})
        self.assertFalse(hoodie.product_id)
        hoodie.track_inventory = True
        self.assertEqual(hoodie.product_id.type, 'product')

    def test_preorder_setting_default_true(self):
        self.assertTrue(self.env['res.config.settings'].create({}).okr_reward_allow_preorder)
        self._allow_preorder(False)
        self.assertFalse(self.env['res.config.settings'].create({}).okr_reward_allow_preorder)
        self._allow_preorder(True)
        self.assertTrue(self.mug._okr_allows_preorder())

    def test_redemption_delivered_from_stock(self):
        self._set_stock(5)
        mug = self.mug.with_user(self.seller)
        self.assertEqual(mug.inventory_free_qty, 5)
        self.assertEqual(mug.available_qty, 5)
        self.assertEqual(mug.stock_status, 'available')
        redemption = self._redeem(self.seller, 2)
        self.assertEqual(redemption.state, 'requested')
        self.assertFalse(redemption.picking_id)
        self.mug.invalidate_recordset()
        self.assertEqual(self.mug.available_qty, 3, 'Pending requests are deducted from the available quantity')
        # Approval creates and reserves the delivery
        redemption.with_user(self.admin).action_approve()
        picking = redemption.picking_id
        self.assertTrue(picking)
        self.assertEqual(picking.picking_type_id, self.warehouse.out_type_id)
        self.assertEqual(picking.partner_id, self.emp_seller.work_contact_id)
        self.assertEqual(picking.origin, redemption.name)
        self.assertEqual(picking.state, 'assigned')
        self.assertEqual(picking.move_ids.product_uom_qty, 2)
        self.mug.invalidate_recordset()
        self.assertEqual(self.mug.inventory_free_qty, 3)
        self.assertEqual(self.mug.available_qty, 3)
        # Delivering validates the delivery order
        redemption.with_user(self.admin).action_deliver()
        self.assertEqual(picking.state, 'done')
        self.assertEqual(redemption.state, 'delivered')
        self.mug.invalidate_recordset()
        self.assertEqual(self.mug.inventory_qty, 3)
        self.assertEqual(self.Transaction._get_balances(self.seller)[self.seller.id], 160)

    def test_picking_done_delivers_redemption(self):
        self._set_stock(1)
        redemption = self._redeem(self.seller)
        redemption.with_user(self.admin).action_approve()
        picking = redemption.picking_id
        picking.move_ids.quantity = 1
        picking.move_ids.picked = True
        picking.button_validate()
        self.assertEqual(redemption.state, 'delivered')
        self.assertTrue(redemption.deliver_date)
        # Delivering again is harmless
        redemption.with_user(self.admin).action_deliver()
        self.assertEqual(redemption.state, 'delivered')

    def test_no_stock_blocked_without_preorder(self):
        self._allow_preorder(False)
        self.assertEqual(self.mug.with_user(self.seller).stock_status, 'out')
        self.assertFalse(self.mug.with_user(self.seller).can_redeem)
        with self.assertRaises(UserError):
            self._redeem(self.seller)
        self._set_stock(1)
        self._redeem(self.seller)
        # The last unit is requested by the seller: nobody else can take it
        self.Transaction._grant(self.tech, 100, 'manual', 'Test grant')
        with self.assertRaises(UserError):
            self._redeem(self.tech)
        self.assertEqual(self.Transaction._get_balances(self.tech)[self.tech.id], 100)

    def test_preorder_waits_for_stock(self):
        self._allow_preorder(True)
        mug = self.mug.with_user(self.seller)
        self.assertEqual(mug.stock_status, 'preorder')
        self.assertTrue(mug.can_redeem)
        redemption = self._redeem(self.seller)
        redemption.with_user(self.admin).action_approve()
        picking = redemption.picking_id
        self.assertEqual(picking.state, 'confirmed', 'The delivery waits for the gift')
        with self.assertRaises(UserError):
            redemption.with_user(self.admin).action_deliver()
        self.assertEqual(redemption.state, 'approved')
        self._set_stock(3)
        redemption.with_user(self.admin).action_deliver()
        self.assertEqual(picking.state, 'done')
        self.assertEqual(redemption.state, 'delivered')

    def test_reject_and_cancel_cancel_delivery(self):
        self._set_stock(5)
        first = self._redeem(self.seller)
        first.with_user(self.admin).action_approve()
        first.with_user(self.admin).action_reject()
        self.assertEqual(first.state, 'rejected')
        self.assertEqual(first.picking_id.state, 'cancel')
        second = self._redeem(self.seller)
        second.with_user(self.admin).action_approve()
        with self.assertRaises(UserError):
            second.with_user(self.seller).action_cancel()
        second.with_user(self.admin).action_cancel()
        self.assertEqual(second.picking_id.state, 'cancel')
        self.mug.invalidate_recordset()
        self.assertEqual(self.mug.inventory_free_qty, 5)
        self.assertEqual(self.Transaction._get_balances(self.seller)[self.seller.id], 200)
        # A cancelled delivery can be recreated for an approved redemption
        third = self._redeem(self.seller)
        third.with_user(self.admin).action_approve()
        third.picking_id.action_cancel()
        old = third.picking_id
        third.with_user(self.admin).action_create_delivery()
        self.assertNotEqual(third.picking_id, old)
        self.assertEqual(third.picking_id.state, 'assigned')
        with self.assertRaises(AccessError):
            third.with_user(self.seller).action_create_delivery()
