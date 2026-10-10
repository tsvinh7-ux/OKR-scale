from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .common import OkrPortalCommonMixin


@tagged('post_install', '-at_install')
class TestOkrPortalAccess(OkrPortalCommonMixin, TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_okr_portal_data()

    def _visible(self, user, model='okr.scale.objective'):
        return self.env[model].with_user(user).search([])

    # ------------------------------------------------------------------
    # Record rules
    # ------------------------------------------------------------------
    def test_portal_sees_only_shared_objectives_of_own_customer(self):
        self.assertEqual(self._visible(self.portal_a1), self.obj_shared_a)
        self.assertEqual(self._visible(self.portal_a2), self.obj_shared_a,
                         'Every portal user of the customer sees its shared objectives')
        self.assertEqual(self._visible(self.portal_b), self.obj_shared_b)

        for objective in (self.obj_unshared_a, self.obj_shared_b, self.obj_draft_a):
            with self.assertRaises(AccessError):
                objective.with_user(self.portal_a1).read(['name'])

    def test_portal_key_results_checkins_cycles(self):
        self.assertEqual(self._visible(self.portal_a1, 'okr.scale.key.result'), self.obj_shared_a.key_result_ids)
        self.assertEqual(self._visible(self.portal_b, 'okr.scale.key.result'), self.obj_shared_b.key_result_ids)
        self.assertEqual(self._visible(self.portal_a1, 'okr.scale.cycle'), self.cycle)
        self.assertEqual(self.obj_shared_a.with_user(self.portal_a1).cycle_id.name, 'Portal Quarter')

        checkin_a = self.env['okr.scale.checkin'].create({'key_result_id': self.kr_internal.id, 'new_value': 2})
        checkin_a.action_submit()
        checkin_secret = self.env['okr.scale.checkin'].create({
            'key_result_id': self.obj_unshared_a.key_result_ids.id, 'new_value': 1})
        checkin_secret.action_submit()
        self.assertEqual(self._visible(self.portal_a1, 'okr.scale.checkin'), checkin_a)
        self.assertFalse(self._visible(self.portal_b, 'okr.scale.checkin'))

    def test_unshare_hides_objective(self):
        self.obj_shared_a.portal_shared = False
        self.assertFalse(self._visible(self.portal_a1))
        self.assertFalse(self._visible(self.portal_a1, 'okr.scale.key.result'))

    def test_portal_cannot_write_through_orm(self):
        objective = self.obj_shared_a.with_user(self.portal_a1)
        with self.assertRaises(AccessError):
            objective.write({'name': 'Hacked'})
        with self.assertRaises(AccessError):
            self.kr_portal.with_user(self.portal_a1).write({'current_value': 100})
        with self.assertRaises(AccessError):
            self.env['okr.scale.checkin'].with_user(self.portal_a1).create({
                'key_result_id': self.kr_portal.id, 'new_value': 50})
        with self.assertRaises(AccessError):
            objective.unlink()
        with self.assertRaises(AccessError):
            self.env['okr.scale.objective'].with_user(self.portal_a1).create({
                'name': 'New', 'cycle_id': self.cycle.id, 'level': 'company', 'owner_id': self.okr_admin.id})

    def test_internal_fields_hidden_from_portal(self):
        with self.assertRaises(AccessError):
            self.obj_shared_a.with_user(self.portal_a1).read(['self_assessment'])

    def test_internal_users_unaffected(self):
        visible = self._visible(self.employee_user)
        self.assertIn(self.obj_unshared_a, visible, 'Public objectives stay visible to employees')
        self.assertIn(self.obj_shared_b, visible)
        self.obj_unshared_a.visibility = 'private'
        self.assertNotIn(self.obj_unshared_a, self._visible(self.employee_user),
                         'The portal rules do not widen the internal visibility')
        self.assertIn(self.cycle, self._visible(self.employee_user, 'okr.scale.cycle'))

    def test_portal_chatter(self):
        message = self.obj_shared_a.with_user(self.portal_a1).message_post(
            body='Question from the customer', message_type='comment', subtype_xmlid='mail.mt_comment')
        self.assertEqual(message.author_id, self.portal_a1.partner_id)
        with self.assertRaises(AccessError):
            self.obj_unshared_a.with_user(self.portal_a1).message_post(
                body='Should fail', message_type='comment', subtype_xmlid='mail.mt_comment')

    def test_access_url_and_token_reset(self):
        self.assertEqual(self.obj_shared_a.access_url, f'/my/okr/{self.obj_shared_a.id}')
        self.obj_shared_a._portal_ensure_token()
        self.assertTrue(self.obj_shared_a.access_token)
        self.obj_shared_a.portal_shared = False
        self.assertFalse(self.obj_shared_a.access_token, 'Unsharing invalidates links sent earlier')

    # ------------------------------------------------------------------
    # Key result owners
    # ------------------------------------------------------------------
    def test_portal_owner_constraint(self):
        self.assertEqual(self.kr_portal.portal_partner_id, self.customer_a)
        self.assertFalse(self.obj_unshared_a.key_result_ids.portal_partner_id)
        with self.assertRaises(ValidationError):
            self.kr_internal.owner_id = self.portal_b
        with self.assertRaises(ValidationError):
            self.obj_unshared_a.key_result_ids.owner_id = self.portal_a1
        with self.assertRaises(ValidationError):
            self.obj_shared_a.partner_id = self.customer_b
        with self.assertRaises(ValidationError):
            self.obj_shared_b.write({'partner_id': False})
        self.kr_internal.owner_id = self.portal_a2
        self.assertEqual(self.kr_internal.owner_id, self.portal_a2)

    # ------------------------------------------------------------------
    # Check-in rights
    # ------------------------------------------------------------------
    def test_portal_can_checkin(self):
        self.assertTrue(self.kr_portal._portal_can_checkin(self.portal_a1))
        self.assertFalse(self.kr_portal._portal_can_checkin(self.portal_a2), 'Only the owner checks in')
        self.assertFalse(self.kr_internal._portal_can_checkin(self.portal_a1))
        self.assertFalse(self.kr_portal._portal_can_checkin(self.employee_user), 'Employees use the backend')
        self.obj_shared_a.portal_access = 'read'
        self.assertFalse(self.kr_portal._portal_can_checkin(self.portal_a1))
        self.obj_shared_a.portal_access = 'contribute'
        self.obj_shared_a.action_done()
        self.assertFalse(self.kr_portal._portal_can_checkin(self.portal_a1))

    def test_portal_submit_checkin(self):
        kr = self.kr_portal.with_user(self.portal_a1)
        checkin = kr._portal_submit_checkin({
            'new_value': 40.0, 'confidence': '8', 'achievements': 'Shipped 40 orders'})
        self.assertEqual(checkin.user_id, self.portal_a1)
        self.assertEqual(checkin.state, 'submitted')
        self.assertEqual(self.kr_portal.current_value, 40.0)
        self.assertEqual(self.kr_portal.confidence, '8')
        self.assertEqual(self.kr_portal.progress, 40.0)
        with self.assertRaises(ValidationError):
            self.kr_portal.with_user(self.portal_a2)._portal_submit_checkin({'new_value': 90.0, 'confidence': '9'})
