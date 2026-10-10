from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import OkrCommon


@tagged('post_install', '-at_install')
class TestOkrHrSync(OkrCommon):

    def test_manager_group_follows_hr(self):
        group = self.env.ref('okr_scale.group_okr_manager')
        boss = new_test_user(self.env, 'okr_new_boss', groups='base.group_user')
        self.assertNotIn(group, boss.groups_id)
        emp_boss = self.env['hr.employee'].create({'name': 'New boss', 'user_id': boss.id})
        self.assertNotIn(group, boss.groups_id, 'Not a manager yet')
        self.emp_tech.parent_id = emp_boss
        self.assertIn(group, boss.groups_id, 'Having a subordinate grants the OKR Manager group')
        self.assertTrue(boss.okr_manager_auto)
        self.emp_tech.parent_id = False
        self.assertNotIn(group, boss.groups_id, 'Removed again when no longer managing')
        self.dep_tech.manager_id = emp_boss
        self.assertIn(group, boss.groups_id, 'Department managers get it too')

    def test_manual_manager_group_kept(self):
        group = self.env.ref('okr_scale.group_okr_manager')
        self.env['res.users']._okr_sync_manager_group()
        self.assertIn(group, self.sales_manager.groups_id, 'Manually granted group is never removed')
        self.assertFalse(self.sales_manager.okr_manager_auto)

    def test_hierarchy_rights_without_manager_group(self):
        """Record access follows the Employees app, even without the OKR Manager group."""
        lead = new_test_user(self.env, 'okr_tech_lead', groups='base.group_user')
        emp_lead = self.env['hr.employee'].create({'name': 'Tech lead', 'user_id': lead.id})
        self.dep_tech.manager_id = emp_lead
        lead.write({'groups_id': [(3, self.env.ref('okr_scale.group_okr_manager').id)]})
        objective = self.env['okr.scale.objective'].with_user(lead).create({
            'name': 'Tech department goal', 'cycle_id': self.cycle.id, 'level': 'department',
            'department_id': self.dep_tech.id})
        personal = self.env['okr.scale.objective'].create({
            'name': 'Tech private goal', 'cycle_id': self.cycle.id, 'level': 'individual',
            'employee_id': self.emp_tech.id, 'visibility': 'private'})
        visible = self.env['okr.scale.objective'].with_user(lead).search([('id', 'in', (objective | personal).ids)])
        self.assertEqual(visible, objective | personal)
        personal.with_user(lead).write({'name': 'Reviewed by lead'})


@tagged('post_install', '-at_install')
class TestOkrRanking(OkrCommon):

    def test_rankings(self):
        self.kr_customers.owner_id = self.seller
        self.kr_revenue.owner_id = self.seller2
        self.kr_customers.current_value = 16
        self.kr_revenue.current_value = 2
        checkin = self.env['okr.scale.checkin'].with_user(self.seller).create({
            'key_result_id': self.kr_customers.id, 'new_value': 18, 'confidence': '8'})
        checkin.action_submit()
        data = self.env['okr.scale.dashboard'].with_user(self.tech).get_ranking_data(self.cycle.id)
        people = {p['user_id']: p for p in data['people']}
        self.assertEqual(data['people'][0]['user_id'], self.seller.id)
        self.assertGreater(people[self.seller.id]['score'], people[self.seller2.id]['score'])
        self.assertEqual(people[self.seller.id]['progress'], 90)
        self.assertFalse(data['me'], 'The viewer owns no key result')
        self.assertEqual(data['departments_rank'][0]['name'], 'Sales')
        levels = {level['level']: level for level in data['objectives']}
        self.assertEqual(levels['company']['rows'][0]['id'], self.company_obj.id)
        self.assertEqual(data['key_results'][0]['id'], self.kr_customers.id)

    def test_private_objectives_not_listed(self):
        self.sales_obj.visibility = 'private'
        data = self.env['okr.scale.dashboard'].with_user(self.tech).get_ranking_data(self.cycle.id)
        listed = [row['id'] for level in data['objectives'] for row in level['rows']]
        self.assertNotIn(self.sales_obj.id, listed)
        self.assertNotIn(self.kr_customers.id, [kr['id'] for kr in data['key_results']])

    def test_my_workspace(self):
        self.kr_customers.owner_id = self.seller
        data = self.env['okr.scale.dashboard'].with_user(self.seller).get_my_okr_data()
        self.assertEqual([o['id'] for o in data['objectives']], [self.sales_obj.id])
        self.assertEqual(data['stats']['key_results'], 1)
        self.assertEqual(data['stats']['due'], 1)
        self.assertFalse(data['manager'])
        manager_data = self.env['okr.scale.dashboard'].with_user(self.sales_manager).get_my_okr_data()
        self.assertIsInstance(manager_data['manager'], dict)
