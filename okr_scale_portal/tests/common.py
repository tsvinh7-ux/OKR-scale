from datetime import timedelta

from odoo import fields
from odoo.tests.common import new_test_user

PASSWORD = 'Okr-Portal-2026!'


class OkrPortalCommonMixin:
    """Customers A and B with portal users, objectives shared or not."""

    @classmethod
    def _setup_okr_portal_data(cls):
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True, mail_create_nolog=True))
        today = fields.Date.today()
        cls.cycle = cls.env['okr.scale.cycle'].create({
            'name': 'Portal Quarter',
            'date_start': today - timedelta(days=45),
            'date_end': today + timedelta(days=45),
            'state': 'open',
        })
        cls.okr_admin = new_test_user(cls.env, 'okrp_admin', groups='base.group_user,okr_scale.group_okr_admin',
                                      password=PASSWORD)
        cls.employee_user = new_test_user(cls.env, 'okrp_employee', groups='base.group_user', password=PASSWORD)

        Partner = cls.env['res.partner']
        cls.customer_a = Partner.create({'name': 'Customer A', 'is_company': True})
        cls.customer_b = Partner.create({'name': 'Customer B', 'is_company': True})
        cls.portal_a1 = cls._create_portal_user('okrp_portal_a1', cls.customer_a)
        cls.portal_a2 = cls._create_portal_user('okrp_portal_a2', cls.customer_a)
        cls.portal_b = cls._create_portal_user('okrp_portal_b', cls.customer_b)

        Objective = cls.env['okr.scale.objective']
        common = {'cycle_id': cls.cycle.id, 'level': 'company', 'owner_id': cls.okr_admin.id}
        cls.obj_shared_a = Objective.create(dict(
            common, name='Shared with A', partner_id=cls.customer_a.id, portal_shared=True,
            portal_access='contribute', key_result_ids=[
                (0, 0, {'name': 'Delivered orders', 'start_value': 0, 'target_value': 100,
                        'owner_id': cls.portal_a1.id, 'unit': 'orders'}),
                (0, 0, {'name': 'Internal KR', 'start_value': 0, 'target_value': 10}),
            ]))
        cls.kr_portal, cls.kr_internal = cls.obj_shared_a.key_result_ids
        cls.obj_unshared_a = Objective.create(dict(
            common, name='Not shared with A', partner_id=cls.customer_a.id,
            key_result_ids=[(0, 0, {'name': 'Secret KR', 'start_value': 0, 'target_value': 5})]))
        cls.obj_shared_b = Objective.create(dict(
            common, name='Shared with B', partner_id=cls.customer_b.id, portal_shared=True,
            key_result_ids=[(0, 0, {'name': 'B KR', 'start_value': 0, 'target_value': 5})]))
        cls.obj_draft_a = Objective.create(dict(
            common, name='Draft shared with A', partner_id=cls.customer_a.id, portal_shared=True,
            key_result_ids=[(0, 0, {'name': 'Draft KR', 'start_value': 0, 'target_value': 5})]))
        (cls.obj_shared_a | cls.obj_unshared_a | cls.obj_shared_b).write({'state': 'running'})

    @classmethod
    def _create_portal_user(cls, login, company):
        user = new_test_user(cls.env, login, groups='base.group_portal', password=PASSWORD,
                             email=f'{login}@example.com')
        user.partner_id.parent_id = company
        return user
