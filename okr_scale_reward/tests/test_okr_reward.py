from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from odoo.addons.okr_scale.tests.common import OkrCommon


@tagged('post_install', '-at_install')
class TestOkrReward(OkrCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Transaction = cls.env['okr.scale.point.transaction']
        cls.Recognition = cls.env['okr.scale.recognition']
        params = cls.env['ir.config_parameter'].sudo()
        for key, value in [('monthly_allowance', 100), ('max_points_per_recognition', 50), ('checkin_points', 5),
                           ('kr_achieved_points', 50), ('objective_achieved_points', 100)]:
            params.set_param('okr_scale_reward.%s' % key, value)
        cls.hoodie = cls.env['okr.scale.reward.item'].create({
            'name': 'Hoodie', 'points_cost': 30, 'limited_stock': True, 'stock_qty': 2})

    def _balance(self, user):
        # The wallet is a non stored computed field: read it fresh.
        self.env.invalidate_all()
        return user.with_user(user).okr_point_balance

    def _budget(self, user):
        self.env.invalidate_all()
        return user.with_user(user).okr_give_budget_left

    def _kudos(self, sender, receivers, points):
        return self.Recognition.with_user(sender).create({
            'receiver_ids': [(6, 0, receivers.ids)],
            'message': '<p>Well done</p>',
            'points': points,
        })

    def _grant(self, user, points):
        return self.Transaction._grant(user, points, 'manual', 'Test grant')

    # ------------------------------------------------------------------
    # Recognition points and monthly budget
    # ------------------------------------------------------------------
    def test_recognition_points_and_budget(self):
        kudos = self._kudos(self.seller, self.seller2 | self.tech, 30)
        self.assertEqual(kudos.points_total, 60)
        self.assertEqual(self._balance(self.seller2), 30)
        self.assertEqual(self._balance(self.tech), 30)
        self.assertEqual(self._balance(self.seller), 0, 'Giving points does not cost the giver')
        self.assertEqual(self._budget(self.seller), 40)
        transactions = self.Transaction.search([('res_model', '=', kudos._name), ('res_id', '=', kudos.id)])
        self.assertEqual(len(transactions), 2)
        self.assertEqual(set(transactions.mapped('transaction_type')), {'recognition'})
        # 2 x 30 = 60 > 40 left this month
        with self.assertRaises(ValidationError):
            self._kudos(self.seller, self.seller2 | self.tech, 30)
        with self.assertRaises(ValidationError):
            self._kudos(self.seller, self.seller2, 51)
        with self.assertRaises(ValidationError):
            self._kudos(self.seller, self.seller2, -5)
        self._kudos(self.seller, self.seller2, 40)
        self.assertEqual(self._budget(self.seller), 0)
        self.assertEqual(self._balance(self.seller2), 70)
        # Kudos without points are always possible and create no transaction
        count = self.Transaction.search_count([])
        self._kudos(self.seller, self.seller2, 0)
        self.assertEqual(self.Transaction.search_count([]), count)
        # Points cannot be changed afterwards and the kudos cannot be deleted by its sender
        with self.assertRaises(UserError):
            kudos.with_user(self.seller).write({'points': 50})
        with self.assertRaises(UserError):
            kudos.with_user(self.seller).unlink()

    # ------------------------------------------------------------------
    # Ledger
    # ------------------------------------------------------------------
    def test_ledger_immutable(self):
        transaction = self._grant(self.seller, 10)
        with self.assertRaises(UserError):
            transaction.with_user(self.admin).write({'points': 1000})
        with self.assertRaises(UserError):
            transaction.with_user(self.admin).sudo().write({'points': 1000})
        with self.assertRaises(UserError):
            transaction.with_user(self.admin).unlink()
        with self.assertRaises(UserError):
            transaction.with_user(self.seller).sudo().unlink()
        with self.assertRaises(AccessError):
            self.Transaction.with_user(self.seller).create({
                'user_id': self.seller.id, 'points': 1000, 'transaction_type': 'manual', 'description': 'Free'})
        self.assertEqual(self._balance(self.seller), 10)

    def test_ledger_and_wallet_privacy(self):
        mine = self._grant(self.seller, 10)
        other = self._grant(self.tech, 20)
        visible = self.Transaction.with_user(self.seller).search([])
        self.assertIn(mine, visible)
        self.assertNotIn(other, visible)
        with self.assertRaises(AccessError):
            other.with_user(self.seller).read(['points'])
        self.assertEqual(self.tech.with_user(self.seller).okr_point_balance, 0, 'Wallets are private')
        self.assertEqual(self.tech.with_user(self.admin).okr_point_balance, 20)
        self.assertEqual(len(self.Transaction.with_user(self.admin).search([('id', 'in', (mine | other).ids)])), 2)

    def test_manual_grant_wizard(self):
        wizard = self.env['okr.scale.point.grant'].with_user(self.admin).create({
            'user_ids': [(6, 0, (self.seller | self.tech).ids)], 'points': 15, 'reason': 'Hackathon'})
        wizard.action_grant()
        self.assertEqual(self._balance(self.seller), 15)
        self.assertEqual(self._balance(self.tech), 15)
        with self.assertRaises(AccessError):
            self.env['okr.scale.point.grant'].with_user(self.seller).create({
                'user_ids': [(6, 0, self.seller.ids)], 'points': 1000, 'reason': 'Me'})

    # ------------------------------------------------------------------
    # OKR hooks
    # ------------------------------------------------------------------
    def _checkin(self, user, kr, value):
        checkin = self.env['okr.scale.checkin'].with_user(user).create({
            'key_result_id': kr.id, 'new_value': value, 'confidence': '7'})
        checkin.action_submit()
        return checkin

    def test_checkin_points_not_farmable(self):
        first = self._checkin(self.sales_manager, self.kr_customers, 5)
        self.assertTrue(first.okr_points_granted)
        self.assertEqual(self._balance(self.sales_manager), 5)
        second = self._checkin(self.sales_manager, self.kr_customers, 6)
        self.assertEqual(second.state, 'submitted')
        self.assertFalse(second.okr_points_granted, 'Only one rewarded check-in per key result and period')
        self.assertEqual(self._balance(self.sales_manager), 5)
        # Changing the editable check-in date does not help either
        third = self.env['okr.scale.checkin'].with_user(self.sales_manager).create({
            'key_result_id': self.kr_customers.id, 'new_value': 7, 'confidence': '7',
            'date': first.date.replace(year=first.date.year + 1)})
        third.action_submit()
        self.assertFalse(third.okr_points_granted)
        # Next period: a new reward
        first.sudo().okr_reward_date = first.okr_reward_date.replace(year=first.okr_reward_date.year - 1)
        fourth = self._checkin(self.sales_manager, self.kr_customers, 8)
        self.assertTrue(fourth.okr_points_granted)
        self.assertEqual(self._balance(self.sales_manager), 10)

    def test_kr_achieved_points_once(self):
        self._checkin(self.sales_manager, self.kr_customers, 20)
        self.assertTrue(self.kr_customers.achieved)
        self.assertTrue(self.kr_customers.okr_reward_granted)
        achieved = self.Transaction.search([('transaction_type', '=', 'kr_achieved')])
        self.assertEqual(set(achieved.mapped('points')), {50})
        self.assertEqual(achieved.filtered(lambda t: t.res_id == self.kr_customers.id).user_id, self.sales_manager)
        # The company KR measured from the aligned sales objective is achieved too
        self.assertTrue(self.kr_sales.achieved)
        self.assertEqual(achieved.filtered(lambda t: t.res_id == self.kr_sales.id).user_id, self.ceo)
        # Falling back and reaching the target again does not grant twice
        self.kr_customers.current_value = 10
        self.kr_customers.current_value = 20
        self._checkin(self.sales_manager, self.kr_customers, 20)
        self.assertEqual(self.Transaction.search_count([('transaction_type', '=', 'kr_achieved'),
                                                        ('res_id', '=', self.kr_customers.id)]), 1)

    def test_kr_added_after_start_not_rewarded(self):
        self.sales_obj.sudo().approval_date = '2000-01-01 00:00:00'
        kr = self.env['okr.scale.key.result'].create({
            'objective_id': self.sales_obj.id, 'name': 'Easy one', 'metric_type': 'boolean',
            'start_value': 0, 'target_value': 1})
        kr.current_value = 1
        self.assertTrue(kr.achieved)
        self.assertFalse(kr.okr_reward_granted)

    def test_objective_done_points_once(self):
        self.kr_customers.current_value = 16
        self.sales_obj.with_user(self.ceo).action_done()
        self.assertEqual(self.sales_obj.state, 'done')
        self.assertEqual(self.sales_obj.final_score, 0.8)
        reward = self.Transaction.search([('transaction_type', '=', 'objective_achieved')])
        self.assertEqual(reward.user_id, self.sales_manager)
        self.assertEqual(reward.points, 100)
        self.sales_obj.with_user(self.ceo).action_draft()
        self.sales_obj.write({'state': 'running'})
        self.sales_obj.with_user(self.ceo).action_done()
        self.assertEqual(self.Transaction.search_count([('transaction_type', '=', 'objective_achieved')]), 1)
        # A low score is no success
        self.kr_revenue.current_value = 1
        self.company_obj.action_done()
        self.assertLess(self.company_obj.final_score, 0.7)
        self.assertFalse(self.company_obj.okr_reward_granted)

    # ------------------------------------------------------------------
    # Store
    # ------------------------------------------------------------------
    def _redeem(self, user, item, quantity=1):
        wizard = self.env['okr.scale.reward.redeem'].with_user(user).create({'item_id': item.id, 'quantity': quantity})
        action = wizard.action_confirm()
        return self.env['okr.scale.redemption'].browse(action['res_id'])

    def test_redemption_insufficient_balance(self):
        self._grant(self.seller, 20)
        wizard = self.env['okr.scale.reward.redeem'].with_user(self.seller).create({'item_id': self.hoodie.id})
        self.assertEqual(wizard.balance, 20)
        self.assertEqual(wizard.balance_after, -10)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        self.assertEqual(self.hoodie.stock_qty, 2)
        self.assertEqual(self._balance(self.seller), 20)

    def test_redemption_stock_and_refund(self):
        self._grant(self.seller, 100)
        redemption = self._redeem(self.seller, self.hoodie)
        self.assertTrue(redemption.name.startswith('RDM/'))
        self.assertEqual(redemption.state, 'requested')
        self.assertEqual(redemption.points, 30)
        self.assertEqual(self.hoodie.stock_qty, 1)
        self.assertEqual(self._balance(self.seller), 70)
        self.assertIn(self.admin, redemption.activity_ids.user_id)
        # Only admins process redemptions
        with self.assertRaises(AccessError):
            redemption.with_user(self.seller).action_approve()
        with self.assertRaises(UserError):
            self._redeem(self.seller, self.hoodie, quantity=2)
        redemption.with_user(self.admin).action_reject()
        self.assertEqual(redemption.state, 'rejected')
        self.assertEqual(self.hoodie.stock_qty, 2)
        self.assertEqual(self._balance(self.seller), 100)
        refund = self.Transaction.search([('transaction_type', '=', 'refund'), ('res_id', '=', redemption.id)])
        self.assertEqual(refund.points, 30)
        # Happy path, then the user cancels a second request
        second = self._redeem(self.seller, self.hoodie, quantity=2)
        self.assertEqual(self.hoodie.stock_qty, 0)
        self.assertFalse(self.hoodie.with_user(self.seller2).can_redeem)
        second.with_user(self.admin).action_approve()
        second.with_user(self.admin).action_deliver()
        self.assertEqual(second.state, 'delivered')
        with self.assertRaises(UserError):
            second.with_user(self.seller).action_cancel()
        self.hoodie.stock_qty = 1
        third = self._redeem(self.seller, self.hoodie)
        third.with_user(self.seller).action_cancel()
        self.assertEqual(third.state, 'cancelled')
        self.assertEqual(self.hoodie.stock_qty, 1)
        self.assertEqual(self._balance(self.seller), 40)

    def test_redemption_privacy(self):
        self._grant(self.seller, 100)
        redemption = self._redeem(self.seller, self.hoodie)
        self.assertFalse(self.env['okr.scale.redemption'].with_user(self.tech).search([]))
        with self.assertRaises(AccessError):
            redemption.with_user(self.tech).read(['points'])
        with self.assertRaises(AccessError):
            redemption.with_user(self.tech).action_cancel()
        with self.assertRaises(AccessError):
            redemption.with_user(self.seller).write({'points': 1})
        # A user cannot redeem on someone else's wallet nor forge the price
        self._grant(self.tech, 100)
        forged = self.env['okr.scale.redemption'].with_user(self.seller).create({
            'item_id': self.hoodie.id, 'user_id': self.tech.id, 'points': 1, 'state': 'delivered'})
        self.assertEqual(forged.user_id, self.seller)
        self.assertEqual(forged.points, 30)
        self.assertEqual(forged.state, 'requested')
        self.assertEqual(self._balance(self.tech), 100)

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    def test_dashboard_extra_data(self):
        self._kudos(self.seller, self.seller2, 20)
        self._kudos(self.tech, self.seller2 | self.seller, 10)
        data = self.env['okr.scale.dashboard'].with_user(self.seller).get_dashboard_data(self.cycle.id)
        kpi = next(k for k in data['kpis'] if k['key'] == 'points_granted')
        self.assertEqual(kpi['value'], 40)
        section = next(s for s in data['extra_sections'] if s['key'] == 'leaderboard')
        self.assertEqual(section['rows'][0], [1, self.seller2.name, 30])
        self.assertEqual(section['rows'][1], [2, self.seller.name, 10])
        self.assertTrue(any(k['key'] == 'recognitions' for k in data['kpis']))

    def test_store_availability_status(self):
        self._grant(self.seller, 40)
        hoodie = self.hoodie.with_user(self.seller)
        self.assertEqual(hoodie.stock_status, 'low')
        self.assertEqual(hoodie.available_qty, 2)
        self.assertTrue(hoodie.affordable)
        self.assertTrue(hoodie.can_redeem)
        mug = self.env['okr.scale.reward.item'].create({'name': 'Mug', 'points_cost': 50})
        mug = mug.with_user(self.seller)
        self.assertEqual(mug.stock_status, 'unlimited')
        self.assertFalse(mug.affordable)
        self.assertEqual(mug.points_missing, 10)
        self.assertFalse(mug.can_redeem)
        self.hoodie.stock_qty = 0
        hoodie.invalidate_recordset()
        self.assertEqual(hoodie.stock_status, 'out')
        self.assertFalse(hoodie.can_redeem)
        values = self.env['okr.scale.reward.item'].with_user(self.seller)._okr_store_banner_values()
        self.assertEqual(values['balance'], 40)
        self.assertEqual(values['affordable'], 1)
        html = self.env['ir.qweb'].with_user(self.seller)._render('okr_scale_reward.okr_store_banner', values)
        self.assertIn('okr_scale_reward.okr_redemption_action_my', html)

    def test_rankings_and_workspace(self):
        self._kudos(self.seller, self.seller2, 20)
        self._kudos(self.tech, self.seller2 | self.seller, 10)
        Dashboard = self.env['okr.scale.dashboard'].with_user(self.tech)
        board = next(b for b in Dashboard._get_extra_rankings(self.cycle, None) if b['key'] == 'top_points')
        self.assertEqual(board['icon'], 'fa-star')
        self.assertEqual([(r['user_id'], r['value']) for r in board['rows']],
                         [(self.seller2.id, 30), (self.seller.id, 10)])
        self.assertEqual(board['rows'][0]['subtitle'], self.dep_sales.name)
        self.assertTrue(any(b['key'] == 'most_recognized' for b in Dashboard._get_extra_rankings(self.cycle, None)))
        tiles = {t['key']: t for t in self.env['okr.scale.dashboard'].with_user(self.seller2)._get_my_extra()}
        self.assertEqual(tiles['my_points']['value'], 30)
        self.assertEqual(tiles['give_budget_left']['value'], 100)
        self.assertIn('kudos_received', tiles)
        for tile in tiles.values():
            self.assertTrue(self.env.ref(tile['action']))

    def test_settings_in_okr_app(self):
        arch = self.env['res.config.settings'].get_views([(False, 'form')])['views']['form']['arch']
        self.assertEqual(arch.count('name="okr_scale"'), 1, 'One OKR settings app shared by the add-ons')
        self.assertIn('okr_reward_monthly_allowance', arch)
        self.assertIn('okr_allow_anonymous_feedback', arch)
