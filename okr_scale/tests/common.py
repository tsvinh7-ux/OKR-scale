from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase, new_test_user


class OkrCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True, mail_create_nolog=True))
        today = fields.Date.today()
        cls.cycle = cls.env['okr.scale.cycle'].create({
            'name': 'Test Quarter',
            'date_start': today - timedelta(days=45),
            'date_end': today + timedelta(days=45),
            'state': 'open',
            'require_approval': True,
        })
        cls.admin = new_test_user(cls.env, 'okr_admin', groups='base.group_user,okr_scale.group_okr_admin')
        cls.ceo = new_test_user(cls.env, 'okr_ceo', groups='base.group_user,okr_scale.group_okr_manager')
        cls.sales_manager = new_test_user(cls.env, 'okr_sales_mgr', groups='base.group_user,okr_scale.group_okr_manager')
        cls.seller = new_test_user(cls.env, 'okr_seller', groups='base.group_user')
        cls.seller2 = new_test_user(cls.env, 'okr_seller2', groups='base.group_user')
        cls.tech = new_test_user(cls.env, 'okr_tech', groups='base.group_user')

        Employee = cls.env['hr.employee']
        cls.emp_ceo = Employee.create({'name': 'CEO', 'user_id': cls.ceo.id})
        cls.dep_root = cls.env['hr.department'].create({'name': 'Company', 'manager_id': cls.emp_ceo.id})
        cls.emp_sales_mgr = Employee.create({'name': 'Sales Manager', 'user_id': cls.sales_manager.id,
                                             'parent_id': cls.emp_ceo.id})
        cls.dep_sales = cls.env['hr.department'].create({
            'name': 'Sales', 'parent_id': cls.dep_root.id, 'manager_id': cls.emp_sales_mgr.id})
        cls.dep_tech = cls.env['hr.department'].create({'name': 'Tech', 'parent_id': cls.dep_root.id})
        cls.emp_seller = Employee.create({'name': 'Seller', 'user_id': cls.seller.id,
                                          'department_id': cls.dep_sales.id, 'parent_id': cls.emp_sales_mgr.id})
        cls.emp_seller2 = Employee.create({'name': 'Seller 2', 'user_id': cls.seller2.id,
                                           'department_id': cls.dep_sales.id, 'parent_id': cls.emp_sales_mgr.id})
        cls.emp_tech = Employee.create({'name': 'Tech', 'user_id': cls.tech.id, 'department_id': cls.dep_tech.id})
        cls.emp_sales_mgr.department_id = cls.dep_sales

        Objective = cls.env['okr.scale.objective']
        cls.company_obj = Objective.create({
            'name': 'Grow revenue',
            'cycle_id': cls.cycle.id,
            'level': 'company',
            'owner_id': cls.ceo.id,
            'key_result_ids': [
                (0, 0, {'name': 'Revenue 10B', 'start_value': 0, 'target_value': 10, 'weight': 1}),
                (0, 0, {'name': 'Sales objectives', 'progress_method': 'objectives', 'weight': 1}),
            ],
        })
        cls.kr_revenue, cls.kr_sales = cls.company_obj.key_result_ids
        cls.sales_obj = Objective.create({
            'name': 'Win the market',
            'cycle_id': cls.cycle.id,
            'level': 'department',
            'department_id': cls.dep_sales.id,
            'parent_key_result_id': cls.kr_sales.id,
            'key_result_ids': [(0, 0, {'name': '20 new customers', 'start_value': 0, 'target_value': 20})],
        })
        cls.kr_customers = cls.sales_obj.key_result_ids
        (cls.company_obj | cls.sales_obj).write({'state': 'running'})
