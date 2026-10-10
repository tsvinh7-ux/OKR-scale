from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import OkrCommon


@tagged('post_install', '-at_install')
class TestOkrAccess(OkrCommon):

    def _individual(self, employee, visibility='public'):
        return self.env['okr.scale.objective'].create({
            'name': 'Personal goal of %s' % employee.name,
            'cycle_id': self.cycle.id,
            'level': 'individual',
            'employee_id': employee.id,
            'visibility': visibility,
            'key_result_ids': [(0, 0, {'name': 'Do it', 'metric_type': 'boolean', 'target_value': 1})],
        })

    def test_level_creation_rights(self):
        Objective = self.env['okr.scale.objective']
        with self.assertRaises(AccessError):
            Objective.with_user(self.seller).create({
                'name': 'Hack company', 'cycle_id': self.cycle.id, 'level': 'company', 'owner_id': self.seller.id})
        with self.assertRaises(AccessError):
            Objective.with_user(self.seller).create({
                'name': 'Hack department', 'cycle_id': self.cycle.id, 'level': 'department',
                'department_id': self.dep_sales.id, 'owner_id': self.seller.id})
        with self.assertRaises(AccessError):
            Objective.with_user(self.tech).create({
                'name': 'Goal for someone else', 'cycle_id': self.cycle.id, 'level': 'individual',
                'employee_id': self.emp_seller.id})
        # Department manager may create department objectives and objectives for the team
        Objective.with_user(self.sales_manager).create({
            'name': 'Sales dept goal', 'cycle_id': self.cycle.id, 'level': 'department',
            'department_id': self.dep_sales.id})
        Objective.with_user(self.sales_manager).create({
            'name': 'Goal for seller', 'cycle_id': self.cycle.id, 'level': 'individual',
            'employee_id': self.emp_seller.id})
        with self.assertRaises(AccessError):
            Objective.with_user(self.sales_manager).create({
                'name': 'Tech goal', 'cycle_id': self.cycle.id, 'level': 'department',
                'department_id': self.dep_tech.id})
        # The admin manages company objectives
        Objective.with_user(self.admin).create({
            'name': 'Admin goal', 'cycle_id': self.cycle.id, 'level': 'company', 'owner_id': self.admin.id})

    def test_level_change_is_checked(self):
        objective = self._individual(self.emp_seller)
        with self.assertRaises(AccessError):
            objective.with_user(self.seller).write({'level': 'company'})

    def test_visibility(self):
        public = self._individual(self.emp_seller, 'public')
        department = self._individual(self.emp_seller, 'department')
        private = self._individual(self.emp_seller, 'private')
        objs = public | department | private

        def visible_for(user):
            return self.env['okr.scale.objective'].with_user(user).search([('id', 'in', objs.ids)])

        self.assertEqual(visible_for(self.seller), objs, 'Owner sees all own objectives')
        self.assertEqual(visible_for(self.seller2), public | department, 'Colleague sees public and department')
        self.assertEqual(visible_for(self.tech), public, 'Other department sees public only')
        self.assertEqual(visible_for(self.sales_manager), objs, 'Manager sees the whole team')
        self.assertEqual(visible_for(self.ceo), objs, 'Upper manager sees everything below')
        self.assertEqual(visible_for(self.admin), objs)
        team = self.env['okr.scale.objective'].with_user(self.sales_manager).search([
            ('id', 'in', objs.ids), ('is_my_team', '=', True)])
        self.assertEqual(team, objs, '"My Team" filter works for non HR users')
        krs = self.env['okr.scale.key.result'].with_user(self.tech).search([('objective_id', 'in', objs.ids)])
        self.assertEqual(krs, public.key_result_ids)

    def test_write_rights(self):
        objective = self._individual(self.emp_seller)
        objective.with_user(self.seller).write({'name': 'Renamed by owner'})
        objective.with_user(self.sales_manager).write({'name': 'Renamed by manager'})
        with self.assertRaises(AccessError):
            objective.with_user(self.seller2).write({'name': 'Renamed by colleague'})
        with self.assertRaises(AccessError):
            self.company_obj.with_user(self.seller).write({'name': 'Hacked'})

    def test_running_targets_frozen_for_owner(self):
        objective = self._individual(self.emp_seller)
        objective.state = 'running'
        kr = objective.key_result_ids
        with self.assertRaises(AccessError):
            kr.with_user(self.seller).write({'weight': 5})
        kr.with_user(self.sales_manager).write({'weight': 5})

    def test_checkin_rights(self):
        Checkin = self.env['okr.scale.checkin']
        with self.assertRaises(AccessError):
            Checkin.with_user(self.tech).create({'key_result_id': self.kr_customers.id, 'new_value': 3})
        self.kr_customers.owner_id = self.seller2
        checkin = Checkin.with_user(self.seller2).create({'key_result_id': self.kr_customers.id, 'new_value': 3})
        checkin.action_submit()
        self.assertEqual(self.kr_customers.current_value, 3)
        with self.assertRaises(AccessError):
            checkin.with_user(self.seller2).write({'new_value': 18})
        with self.assertRaises(AccessError):
            checkin.with_user(self.seller2).action_review()
        checkin.with_user(self.sales_manager).write({'manager_feedback': 'Good job'})
        checkin.with_user(self.sales_manager).action_review()
        self.assertEqual(checkin.state, 'reviewed')
