from datetime import date, timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import OkrCommon


@tagged('post_install', '-at_install')
class TestOkrWeekly(OkrCommon):

    def setUp(self):
        super().setUp()
        self.kr_customers.owner_id = self.seller

    def test_friday_window(self):
        """Weekly cycles: due from the check-in day until a check-in is made in that week."""
        self.cycle.checkin_weekday = '4'  # Friday
        kr = self.kr_customers
        friday = date(2026, 10, 9)
        self.assertTrue(kr._is_checkin_due(friday))
        self.assertFalse(kr._is_checkin_due(friday - timedelta(days=1)) and kr.last_checkin_date,
                         'Before Friday nothing new is asked')
        self.env['okr.scale.checkin'].with_user(self.seller).create({
            'key_result_id': kr.id, 'new_value': 3, 'confidence': '8', 'date': friday - timedelta(days=2),
        }).action_submit()
        self.assertFalse(kr._is_checkin_due(friday), 'A check-in from Wednesday counts for the week')
        self.assertFalse(kr._is_checkin_due(friday + timedelta(days=3)), 'Still fine on Monday')
        self.assertTrue(kr._is_checkin_due(friday + timedelta(days=7)), 'Due again next Friday')

    def test_submit_my_week(self):
        Weekly = self.env['okr.scale.weekly'].with_user(self.seller)
        data = Weekly.get_my_week()
        self.assertEqual([kr['id'] for kr in data['key_results']], self.kr_customers.ids)
        with self.assertRaises(UserError):
            Weekly.submit_my_week({'summary': 'ok', 'lines': []})
        weekly_id = Weekly.submit_my_week({
            'summary': 'Signed 2 clinics', 'next_plan': 'Call 10 leads', 'help_needed': 'Need a demo slot',
            'mood': 'great',
            'lines': [{'key_result_id': self.kr_customers.id, 'new_value': 6, 'confidence': 8,
                       'note': '2 new clinics', 'blockers': ''}],
        })
        weekly = self.env['okr.scale.weekly'].browse(weekly_id)
        self.assertEqual(weekly.checkin_count, 1)
        self.assertEqual(self.kr_customers.current_value, 6)
        self.assertTrue(weekly.has_blockers, 'Help needed counts as a blocker')
        self.assertTrue(Weekly.get_my_week()['key_results'][0]['done'])
        # Submitting again does not duplicate check-ins
        Weekly.submit_my_week({'next_plan': 'Updated plan', 'lines': [
            {'key_result_id': self.kr_customers.id, 'new_value': 9, 'confidence': 8}]})
        self.assertEqual(weekly.checkin_count, 1)
        self.assertEqual(weekly.next_plan, 'Updated plan')

    def test_team_board_follows_hierarchy(self):
        self.env['okr.scale.weekly'].with_user(self.seller).submit_my_week({
            'next_plan': 'Plan', 'lines': [{'key_result_id': self.kr_customers.id, 'new_value': 2,
                                            'confidence': 3, 'blockers': 'No leads'}]})
        board = self.env['okr.scale.weekly'].with_user(self.sales_manager).get_team_week()
        names = {row['name']: row for row in board['rows']}
        self.assertIn('Seller', names)
        self.assertNotIn('Tech', names, 'Only the managed people')
        self.assertTrue(names['Seller']['submitted'])
        self.assertEqual(names['Seller']['blockers'], ['No leads'])
        self.assertEqual(board['stats']['blocked'], 1)
        self.assertFalse(self.env['okr.scale.weekly'].with_user(self.tech).get_team_week()['rows'])
        # The manager reads the weekly check-in of the team member, a colleague does not
        weekly = self.env['okr.scale.weekly'].search([('user_id', '=', self.seller.id)])
        self.assertTrue(weekly.with_user(self.sales_manager).next_plan)
        self.assertFalse(self.env['okr.scale.weekly'].with_user(self.seller2).search([('id', '=', weekly.id)]))

    def test_notifications(self):
        with patch.object(type(self.env['res.users']), '_okr_send') as send:
            self.env['okr.scale.weekly'].with_user(self.sales_manager).remind_user(self.seller.id)
            self.assertEqual(send.call_count, 1)
        # Real rendering: inbox notification and e-mail
        self.seller.notification_type = 'inbox'
        mails_before = self.env['mail.mail'].sudo().search_count([])
        self.seller._okr_notify_checkin_due(self.kr_customers)
        self.assertGreater(self.env['mail.mail'].sudo().search_count([]), mails_before)
        digest = self.env['okr.scale.dashboard'].with_user(self.seller)._get_weekly_digest()
        self.assertEqual(digest['key_results'][0]['name'], self.kr_customers.name)
        self.env['res.users']._cron_okr_weekly_digest()

    def test_reminder_only_on_checkin_day(self):
        self.cycle.checkin_weekday = str((fields.Date.today().weekday() + 1) % 7)
        self.env['okr.scale.key.result']._cron_checkin_reminder()
        activity_type = self.env.ref('okr_scale.mail_activity_okr_checkin')
        self.assertFalse(self.kr_customers.activity_ids.filtered(lambda a: a.activity_type_id == activity_type))


@tagged('post_install', '-at_install')
class TestOkrSupportAndInsights(OkrCommon):

    def test_supporters_see_and_comment(self):
        objective = self.env['okr.scale.objective'].create({
            'name': 'Private sales push', 'cycle_id': self.cycle.id, 'level': 'individual',
            'employee_id': self.emp_seller.id, 'visibility': 'private',
            'contributor_department_ids': [(6, 0, self.dep_tech.ids)],
            'key_result_ids': [(0, 0, {'name': 'Demo app', 'metric_type': 'boolean', 'target_value': 1})],
            'state': 'running',
        })
        self.assertTrue(objective.with_user(self.tech).read(['name']), 'Supporting department sees it')
        objective.with_user(self.tech).message_post(body='I can help with the demo')
        self.assertFalse(self.env['okr.scale.objective'].with_user(self.seller2).search([('id', '=', objective.id)]))
        objective.contributor_user_ids = self.seller2
        self.assertTrue(self.env['okr.scale.objective'].with_user(self.seller2).search([('id', '=', objective.id)]))
        self.assertIn(self.seller2.partner_id, objective.message_partner_ids)
        data = self.env['okr.scale.dashboard'].with_user(self.seller2).get_my_okr_data()
        self.assertIn(objective.id, [o['id'] for o in data['supporting']])

    def test_progress_history(self):
        self.kr_customers.owner_id = self.seller
        checkin = self.env['okr.scale.checkin'].with_user(self.seller).create({
            'key_result_id': self.kr_customers.id, 'new_value': 10, 'confidence': '8'})
        checkin.action_submit()
        history = self.kr_customers.progress_history
        self.assertEqual(history['points'][0][1], 0)
        self.assertEqual(history['points'][-1][1], 50)
        self.assertEqual(self.sales_obj.progress_history['points'][-1][1], 50)

    def test_issues(self):
        self.kr_customers.write({'owner_id': self.seller, 'confidence': '2'})
        data = self.env['okr.scale.dashboard'].with_user(self.admin).get_dashboard_data(self.cycle.id)
        issues = {i['key']: i for i in data['issues']}
        self.assertIn(self.kr_customers.id, issues['low_confidence']['ids'])
        self.assertIn(self.kr_customers.id, issues['checkin_due']['ids'])
        self.assertEqual(issues['off_track']['model'], 'okr.scale.key.result')
