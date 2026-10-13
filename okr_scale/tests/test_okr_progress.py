from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import OkrCommon


@tagged('post_install', '-at_install')
class TestOkrProgress(OkrCommon):

    def test_alignment(self):
        self.assertEqual(self.sales_obj.parent_id, self.company_obj)
        self.assertEqual(self.sales_obj.owner_id, self.sales_manager, 'Department manager owns department objectives')
        self.assertIn(self.sales_manager, self.emp_seller.okr_manager_user_ids)
        self.assertIn(self.ceo, self.emp_seller.okr_manager_user_ids)
        self.assertIn(self.ceo, self.dep_sales.okr_manager_user_ids)

    def test_progress_rollup(self):
        self.kr_customers.current_value = 10
        self.assertEqual(self.sales_obj.progress, 50)
        self.assertEqual(self.kr_sales.progress, 50, 'KR measured from aligned objectives')
        self.kr_revenue.current_value = 5
        self.assertEqual(self.company_obj.progress, 50)
        self.kr_revenue.weight = 3
        self.assertEqual(self.company_obj.progress, 50)
        self.kr_customers.current_value = 20
        self.assertEqual(self.company_obj.progress, (50 * 3 + 100) / 4)

    def test_decreasing_target(self):
        kr = self.env['okr.scale.key.result'].create({
            'objective_id': self.sales_obj.id, 'name': 'Reduce churn', 'start_value': 10, 'target_value': 2,
            'current_value': 6})
        self.assertEqual(kr.progress, 50)
        kr.current_value = 1
        self.assertEqual(kr.progress, 100)
        self.assertEqual(kr.status, 'achieved')

    def test_checkin(self):
        checkin = self.env['okr.scale.checkin'].with_user(self.sales_manager).create({
            'key_result_id': self.kr_customers.id, 'new_value': 15, 'confidence': '3',
            'blockers': 'Not enough leads'})
        checkin.action_submit()
        self.assertEqual(checkin.state, 'submitted')
        self.assertEqual(checkin.progress_before, 0)
        self.assertEqual(checkin.progress_after, 75)
        self.assertEqual(self.kr_customers.current_value, 15)
        self.assertEqual(self.kr_customers.confidence, '3')
        self.assertEqual(self.kr_customers.status, 'off_track', 'Low confidence flags the KR')
        self.assertTrue(self.kr_customers.last_checkin_date)
        self.assertFalse(self.kr_customers.checkin_due)

    def test_checkin_reminder(self):
        self.cycle.write({'checkin_weekday': str(fields.Date.today().weekday()), 'checkin_hour': 0.0})
        self.kr_customers.owner_id = self.seller
        self.assertTrue(self.kr_customers.checkin_due)
        self.env['okr.scale.key.result']._cron_checkin_reminder()
        activity_type = self.env.ref('okr_scale.mail_activity_okr_checkin')
        activities = self.kr_customers.activity_ids.filtered(lambda a: a.activity_type_id == activity_type)
        self.assertEqual(activities.user_id, self.seller)
        self.env['okr.scale.key.result']._cron_checkin_reminder()
        self.assertEqual(len(self.kr_customers.activity_ids), 1, 'No duplicate reminder')
        checkin = self.env['okr.scale.checkin'].with_user(self.seller).create({
            'key_result_id': self.kr_customers.id, 'new_value': 2, 'confidence': '8'})
        checkin.action_submit()
        self.assertFalse(self.kr_customers.activity_ids, 'Check-in closes the reminder')

    def test_approval_workflow(self):
        objective = self.env['okr.scale.objective'].with_user(self.seller).create({
            'name': 'Learn the product', 'cycle_id': self.cycle.id, 'level': 'individual'})
        self.assertEqual(objective.employee_id, self.emp_seller)
        self.assertEqual(objective.owner_id, self.seller)
        self.assertEqual(objective.department_id, self.dep_sales)
        with self.assertRaises(UserError):
            objective.action_submit()
        objective.write({'key_result_ids': [(0, 0, {'name': 'Pass the certification', 'metric_type': 'boolean',
                                                     'target_value': 1})]})
        objective.action_submit()
        self.assertEqual(objective.state, 'to_approve')
        objective.with_user(self.sales_manager).action_approve()
        self.assertEqual(objective.state, 'running')
        self.assertEqual(objective.approved_by_id, self.sales_manager)

    def test_close_cycle_grades(self):
        self.kr_customers.current_value = 14
        self.cycle.action_close()
        self.assertEqual(self.sales_obj.state, 'done')
        self.assertEqual(self.sales_obj.final_score, 0.7)

    def test_manual_zero_grade_kept(self):
        self.kr_customers.current_value = 14
        self.sales_obj.final_score = 0.0
        self.assertTrue(self.sales_obj.graded)
        self.cycle.action_close()
        self.assertEqual(self.sales_obj.final_score, 0.0, 'A deliberate 0.0 grade is kept')
        self.assertFalse(self.company_obj.graded)
        self.assertEqual(self.company_obj.state, 'done')
