from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install')
class TestOkrReview(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True, mail_create_nolog=True))
        today = fields.Date.today()
        Cycle = cls.env['okr.scale.cycle']
        # Ended 10 days ago: end-of-cycle retrospective
        cls.past = Cycle.create({'name': 'Past Quarter', 'date_start': today - timedelta(days=100),
                                 'date_end': today - timedelta(days=10), 'state': 'open'})
        cls.next = Cycle.create({'name': 'Next Quarter', 'date_start': today - timedelta(days=9),
                                 'date_end': today + timedelta(days=80), 'state': 'open'})
        cls.admin = new_test_user(cls.env, 'rev_admin', groups='base.group_user,okr_scale.group_okr_admin')
        cls.ceo = new_test_user(cls.env, 'rev_ceo', groups='base.group_user')
        cls.sales_manager = new_test_user(cls.env, 'rev_sales_mgr', groups='base.group_user')
        cls.seller = new_test_user(cls.env, 'rev_seller', groups='base.group_user')
        cls.seller2 = new_test_user(cls.env, 'rev_seller2', groups='base.group_user')
        cls.tech = new_test_user(cls.env, 'rev_tech', groups='base.group_user')

        Employee = cls.env['hr.employee']
        Department = cls.env['hr.department']
        cls.emp_ceo = Employee.create({'name': 'CEO', 'user_id': cls.ceo.id})
        cls.dep_root = Department.create({'name': 'Company', 'manager_id': cls.emp_ceo.id})
        cls.emp_sales_mgr = Employee.create({'name': 'Sales Manager', 'user_id': cls.sales_manager.id,
                                             'parent_id': cls.emp_ceo.id})
        cls.dep_sales = Department.create({'name': 'Sales', 'parent_id': cls.dep_root.id,
                                           'manager_id': cls.emp_sales_mgr.id})
        cls.dep_tech = Department.create({'name': 'Tech', 'parent_id': cls.dep_root.id})
        cls.emp_seller = Employee.create({'name': 'Seller', 'user_id': cls.seller.id,
                                          'department_id': cls.dep_sales.id, 'parent_id': cls.emp_sales_mgr.id})
        cls.emp_seller2 = Employee.create({'name': 'Seller 2', 'user_id': cls.seller2.id,
                                           'department_id': cls.dep_sales.id, 'parent_id': cls.emp_sales_mgr.id})
        cls.emp_tech = Employee.create({'name': 'Tech', 'user_id': cls.tech.id, 'department_id': cls.dep_tech.id})
        cls.emp_sales_mgr.department_id = cls.dep_sales

        def objective(name, level, current, okr_type='committed', cycle=None, **vals):
            obj = cls.env['okr.scale.objective'].create(dict({
                'name': name, 'cycle_id': (cycle or cls.past).id, 'level': level, 'okr_type': okr_type,
                'key_result_ids': [(0, 0, {'name': 'KR ' + name, 'start_value': 0, 'target_value': 10,
                                           'current_value': current})],
            }, **vals))
            obj.state = 'running'
            return obj

        cls.company_obj = objective('Grow', 'company', 10, owner_id=cls.ceo.id)
        cls.sales_obj = objective('Win market', 'department', 5, 'aspirational', department_id=cls.dep_sales.id,
                                  self_assessment='Good start, pipeline still thin.',
                                  lessons_learned='Qualify leads earlier.')
        cls.seller_obj = objective('Learn product', 'individual', 2, employee_id=cls.emp_seller.id)
        cls.seller2_obj = objective('Stretch deals', 'individual', 8, 'aspirational', employee_id=cls.emp_seller2.id)
        # Graded objectives: final score = progress / 100; seller2 stays running
        (cls.company_obj | cls.sales_obj | cls.seller_obj).action_done()
        cls.Board = cls.env['okr.scale.review.board']

    def _level(self, data, key):
        return next(level for level in data['levels'] if level['key'] == key)

    def test_board_scores_per_level(self):
        data = self.Board.get_cycle_review_data(self.past.id)
        self.assertEqual(data['phase'], 'final')
        self.assertEqual(data['score_mode'], 'final')
        self.assertEqual(data['suggested_review_type'], 'final')
        company, department, individual = (self._level(data, k) for k in ('company', 'department', 'individual'))
        self.assertEqual((company['count'], company['score'], company['band']), (1, 1.0, 'green'))
        self.assertEqual((department['score'], department['band'], department['final_score']), (0.5, 'yellow', 0.5))
        # 0.2 (graded) and 0.8 (running, progress at the end of the cycle)
        self.assertEqual((individual['count'], individual['score'], individual['graded']), (2, 0.5, 1))
        self.assertEqual(individual['final_score'], 0.2)
        self.assertEqual(individual['bands'], {'red': 1, 'yellow': 0, 'green': 1})
        self.assertEqual(data['overall']['bands'], {'red': 1, 'yellow': 1, 'green': 2})
        self.assertEqual(data['overall']['score'], 0.62)
        types = {t['key']: t for t in data['types']}
        self.assertEqual((types['committed']['score'], types['committed']['reached']), (0.6, 1))
        self.assertEqual((types['aspirational']['score'], types['aspirational']['reached']), (0.65, 1))
        self.assertEqual([r['id'] for r in data['highlights']][:1], [self.company_obj.id])
        self.assertEqual(data['lowlights'][0]['id'], self.seller_obj.id)
        self.assertEqual(len(data['carry_over']['key_results']), 3)
        self.assertEqual(data['carry_over']['next_cycle']['id'], self.next.id)
        self.assertEqual({q['kind'] for q in data['quotes']}, {'self_assessment', 'lessons_learned'})
        sales_row = next(r for r in data['departments_table'] if r['id'] == self.dep_sales.id)
        self.assertEqual(sales_row['count'], 3)

        # Department filter (sub-departments included) and access rights of the reader
        data = self.Board.get_cycle_review_data(self.past.id, self.dep_sales.id)
        self.assertEqual(data['overall']['count'], 3)
        data = self.Board.with_user(self.tech).get_cycle_review_data(self.past.id)
        self.assertEqual(data['overall']['count'], 4, 'Public objectives are visible to everybody')
        self.seller_obj.sudo().visibility = 'private'
        data = self.Board.with_user(self.tech).get_cycle_review_data(self.past.id)
        self.assertEqual(data['overall']['count'], 3)
        self.assertFalse(data['can_review'])

    def test_board_projected_score_mid_cycle(self):
        today = fields.Date.today()
        mid = self.env['okr.scale.cycle'].create({
            'name': 'Mid', 'cycle_type': 'custom', 'date_start': today - timedelta(days=49),
            'date_end': today + timedelta(days=50), 'state': 'open'})
        obj = self.env['okr.scale.objective'].create({
            'name': 'Half way', 'cycle_id': mid.id, 'level': 'company', 'owner_id': self.ceo.id,
            'key_result_ids': [(0, 0, {'name': 'KR', 'start_value': 0, 'target_value': 10, 'current_value': 4})]})
        obj.state = 'running'
        data = self.Board.get_cycle_review_data(mid.id)
        self.assertEqual(data['phase'], 'mid')
        self.assertEqual(data['cycle']['elapsed'], 50.0)
        # 40 % progress at 50 % of the cycle: heading to 0.8
        self.assertEqual(self._level(data, 'company')['score'], 0.8)
        self.assertEqual(self._level(data, 'company')['band'], 'green')

    def test_carry_over(self):
        kr = self.sales_obj.key_result_ids
        wizard = self.env['okr.scale.carry.over'].with_user(self.admin).with_context(
            default_source_cycle_id=self.past.id, carry_kr_ids=kr.ids).create({})
        self.assertEqual(wizard.target_cycle_id, self.next, 'The next cycle by date is proposed')
        self.assertEqual(wizard.key_result_ids, kr)
        wizard.action_confirm()
        new_obj = self.env['okr.scale.objective'].search([('carried_from_id', '=', self.sales_obj.id)])
        self.assertEqual(len(new_obj), 1)
        self.assertEqual(new_obj.state, 'draft')
        self.assertEqual(new_obj.cycle_id, self.next)
        self.assertEqual((new_obj.level, new_obj.department_id, new_obj.okr_type),
                         ('department', self.dep_sales, 'aspirational'))
        new_kr = new_obj.key_result_ids
        self.assertEqual(len(new_kr), 1)
        self.assertEqual(new_kr.carried_from_id, kr)
        self.assertEqual((new_kr.start_value, new_kr.current_value, new_kr.target_value), (5.0, 5.0, 10.0))
        self.assertEqual(new_kr.progress, 0.0)
        self.assertIn(new_kr, kr.carried_to_ids)
        self.assertTrue(self.sales_obj.message_ids.filtered(lambda m: 'Next Quarter' in (m.body or '')))
        self.assertTrue(new_obj.message_ids.filtered(lambda m: 'Win market' in (m.body or '')))
        # Already carried: nothing to do anymore
        wizard2 = self.env['okr.scale.carry.over'].with_user(self.admin).create({
            'source_cycle_id': self.past.id, 'key_result_ids': [(6, 0, kr.ids)]})
        with self.assertRaises(UserError):
            wizard2.action_confirm()

    def test_carry_over_permissions(self):
        Wizard = self.env['okr.scale.carry.over'].with_user(self.seller)
        # Own individual key result: allowed
        own = Wizard.create({'source_cycle_id': self.past.id, 'target_cycle_id': self.next.id,
                             'key_result_ids': [(6, 0, self.seller_obj.key_result_ids.ids)]})
        own.action_confirm()
        new_obj = self.env['okr.scale.objective'].search([('carried_from_id', '=', self.seller_obj.id)])
        self.assertEqual((new_obj.employee_id, new_obj.state), (self.emp_seller, 'draft'))
        # Department key result: only its managers
        dept = Wizard.create({'source_cycle_id': self.past.id, 'target_cycle_id': self.next.id,
                              'key_result_ids': [(6, 0, self.sales_obj.key_result_ids.ids)]})
        with self.assertRaises(AccessError):
            dept.action_confirm()

    def test_review_permissions(self):
        Review = self.env['okr.scale.review']
        # Normal users cannot create reviews at all
        with self.assertRaises(AccessError):
            Review.with_user(self.seller).create({'cycle_id': self.past.id, 'department_id': self.dep_sales.id})
        # Managers: only for the departments they manage
        self.assertTrue(self.sales_manager.has_group('okr_scale.group_okr_manager'))
        with self.assertRaises(AccessError):
            Review.with_user(self.sales_manager).create({'cycle_id': self.past.id, 'department_id': self.dep_tech.id})
        with self.assertRaises(AccessError):
            Review.with_user(self.sales_manager).create({'cycle_id': self.past.id})
        sales_review = Review.with_user(self.sales_manager).create({
            'cycle_id': self.past.id, 'department_id': self.dep_sales.id, 'review_type': 'final'})
        self.assertEqual(sales_review.snapshot_objective_count, 3)
        self.assertEqual(sales_review.snapshot_band_green, 1)
        with self.assertRaises(AccessError):
            sales_review.with_user(self.sales_manager).write({'department_id': self.dep_tech.id})
        company_review = Review.with_user(self.admin).create({'cycle_id': self.past.id, 'review_type': 'final'})
        self.assertEqual(company_review.snapshot_objective_count, 4)
        self.assertEqual(company_review.snapshot_avg_score, 0.62)
        tech_review = Review.with_user(self.admin).create({'cycle_id': self.past.id, 'department_id': self.dep_tech.id})
        # Readers: company-wide and own department reviews
        visible = Review.with_user(self.seller).search([('cycle_id', '=', self.past.id)])
        self.assertEqual(visible, sales_review | company_review)
        with self.assertRaises(AccessError):
            sales_review.with_user(self.seller).write({'went_well': '<p>Hacked</p>'})
        self.assertNotIn(tech_review, visible)
        # Close: the snapshot is frozen
        sales_review.with_user(self.sales_manager).action_done()
        self.assertEqual(sales_review.state, 'done')

    def test_start_review_prefilled(self):
        action = self.env['okr.scale.review'].with_user(self.sales_manager).action_start_review(self.past.id)
        review = self.env['okr.scale.review'].browse(action['res_id'])
        self.assertEqual(review.department_id, self.dep_sales, 'Defaults to the department the manager manages')
        self.assertEqual(review.review_type, 'final')
        self.assertIn('Qualify leads earlier.', review.lessons)
        self.assertIn('Learn product', review.to_improve)
        with self.assertRaises(AccessError):
            self.env['okr.scale.review'].with_user(self.seller).action_start_review(self.past.id)

    def test_review_reminders_once(self):
        today = fields.Date.today()
        mid = self.env['okr.scale.cycle'].create({
            'name': 'Halfway', 'date_start': today - timedelta(days=49), 'date_end': today + timedelta(days=50),
            'state': 'open'})
        early = self.env['okr.scale.cycle'].create({
            'name': 'Early', 'date_start': today - timedelta(days=10), 'date_end': today + timedelta(days=80),
            'state': 'open'})
        obj = self.env['okr.scale.objective'].create({
            'name': 'Sales push', 'cycle_id': mid.id, 'level': 'department', 'department_id': self.dep_sales.id,
            'key_result_ids': [(0, 0, {'name': 'KR', 'start_value': 0, 'target_value': 10})]})
        obj.state = 'running'
        mid_type = self.env.ref('okr_scale_review.mail_activity_okr_mid_review')
        final_type = self.env.ref('okr_scale_review.mail_activity_okr_final_review')
        Cycle = self.env['okr.scale.cycle']
        Cycle._cron_review_reminders()
        activities = mid.activity_ids.filtered(lambda a: a.activity_type_id == mid_type)
        self.assertTrue(mid.mid_review_reminded)
        self.assertIn(self.admin, activities.user_id)
        self.assertIn(self.sales_manager, activities.user_id, 'Managers of the departments taking part')
        self.assertNotIn(self.seller, activities.user_id)
        self.assertFalse(early.mid_review_reminded)
        self.assertFalse(early.activity_ids)
        # The past cycle ended 10 days ago: final review reminder
        self.assertTrue(self.past.final_review_reminded)
        self.assertTrue(self.past.activity_ids.filtered(lambda a: a.activity_type_id == final_type))
        # Only once, even if the activities were done
        count = len(activities)
        activities.action_feedback(feedback='Done')
        Cycle._cron_review_reminders()
        self.assertFalse(mid.activity_ids.filtered(lambda a: a.activity_type_id == mid_type))
        self.assertEqual(len(mid.message_ids.filtered(lambda m: m.mail_activity_type_id == mid_type)), count)
