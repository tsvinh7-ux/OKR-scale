from odoo.exceptions import AccessError, UserError, ValidationError
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
    def test_portal_sees_only_objectives_shared_with_them(self):
        self.assertEqual(self._visible(self.portal_a1), self.obj_shared_a, 'Edit collaborator (KR owner)')
        self.assertEqual(self._visible(self.portal_a2), self.obj_shared_a, 'Read collaborator')
        self.assertEqual(self._visible(self.portal_b), self.obj_shared_b)

        for objective in (self.obj_unshared_a, self.obj_shared_b, self.obj_draft_a):
            with self.assertRaises(AccessError):
                objective.with_user(self.portal_a1).read(['name'])

    def test_no_company_wide_leak(self):
        """Another contact of the same customer sees nothing until invited."""
        self.assertEqual(self.obj_shared_a.partner_id, self.customer_a)
        self.assertFalse(self._visible(self.portal_a3))
        self.assertFalse(self._visible(self.portal_a3, 'okr.scale.key.result'))
        self.assertFalse(self._visible(self.portal_a3, 'okr.scale.cycle'))
        with self.assertRaises(AccessError):
            self.obj_shared_a.with_user(self.portal_a3).read(['name'])
        self.obj_shared_a._add_collaborators(self.portal_a3.partner_id)
        self.assertEqual(self._visible(self.portal_a3), self.obj_shared_a)

    def test_portal_key_results_checkins_cycles(self):
        self.assertEqual(self._visible(self.portal_a2, 'okr.scale.key.result'), self.obj_shared_a.key_result_ids)
        self.assertEqual(self._visible(self.portal_b, 'okr.scale.key.result'), self.obj_shared_b.key_result_ids)
        self.assertEqual(self._visible(self.portal_a2, 'okr.scale.cycle'), self.cycle)
        self.assertEqual(self.obj_shared_a.with_user(self.portal_a2).cycle_id.name, 'Portal Quarter')

        checkin_a = self.env['okr.scale.checkin'].create({'key_result_id': self.kr_internal.id, 'new_value': 2})
        checkin_a.action_submit()
        checkin_secret = self.env['okr.scale.checkin'].create({
            'key_result_id': self.obj_unshared_a.key_result_ids.id, 'new_value': 1})
        checkin_secret.action_submit()
        draft = self.env['okr.scale.checkin'].create({'key_result_id': self.kr_internal.id, 'new_value': 3})
        self.assertEqual(self._visible(self.portal_a2, 'okr.scale.checkin'), checkin_a, 'Drafts stay hidden')
        self.assertNotIn(draft, self._visible(self.portal_a1, 'okr.scale.checkin'))
        self.assertFalse(self._visible(self.portal_b, 'okr.scale.checkin'))

    def test_collaborator_visibility(self):
        Collaborator = self.env['okr.scale.objective.collaborator']
        self.assertEqual(Collaborator.with_user(self.portal_a2).search([]).objective_id, self.obj_shared_a,
                         'Portal users only see their own collaborations of shared objectives')
        self.assertFalse(Collaborator.with_user(self.portal_a3).search([]))

    def test_unshare_and_remove_collaborator(self):
        self.obj_shared_a.collaborator_ids.filtered(lambda c: c.partner_id == self.portal_a2.partner_id).unlink()
        self.assertFalse(self._visible(self.portal_a2))
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
        with self.assertRaises(AccessError):
            self.env['okr.scale.objective.collaborator'].with_user(self.portal_a3).create({
                'objective_id': self.obj_shared_a.id, 'partner_id': self.portal_a3.partner_id.id})
        with self.assertRaises(AccessError):
            self.obj_shared_a.collaborator_ids.with_user(self.portal_a2).write({'access_mode': 'edit'})

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

    def test_internal_collaborator_management(self):
        """Only the owner and managers of an objective manage its collaborators."""
        self.assertTrue(self.obj_shared_a.with_user(self.okr_admin).can_share)
        self.assertFalse(self.obj_shared_a.with_user(self.employee_user).can_share)
        with self.assertRaises(AccessError):
            self.env['okr.scale.objective.collaborator'].with_user(self.employee_user).create({
                'objective_id': self.obj_shared_a.id, 'partner_id': self.portal_a3.partner_id.id})
        with self.assertRaises(AccessError):
            self.obj_shared_a.with_user(self.employee_user).action_open_share_wizard()
        self.env['okr.scale.objective.collaborator'].with_user(self.okr_admin).create({
            'objective_id': self.obj_shared_a.id, 'partner_id': self.portal_a3.partner_id.id})
        self.assertEqual(self.obj_shared_a.collaborator_count, 3)
        with self.assertRaises(ValidationError):
            self.obj_shared_a._add_collaborators(self.employee_user.partner_id)

    def test_portal_chatter(self):
        message = self.obj_shared_a.with_user(self.portal_a2).message_post(
            body='Question from the customer', message_type='comment', subtype_xmlid='mail.mt_comment')
        self.assertEqual(message.author_id, self.portal_a2.partner_id)
        with self.assertRaises(AccessError):
            self.obj_unshared_a.with_user(self.portal_a2).message_post(
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
    def _collaborator(self, objective, user):
        return objective.collaborator_ids.filtered(lambda c: c.partner_id == user.partner_id)

    def test_portal_owner_auto_edit_collaborator(self):
        self.assertEqual(self._collaborator(self.obj_shared_a, self.portal_a1).access_mode, 'edit',
                         'Portal key result owners are added as edit collaborators')
        self.assertIn(self.portal_a1.partner_id, self.kr_portal.portal_collaborator_partner_ids)
        # A read collaborator is upgraded when they become owner
        self.kr_internal.owner_id = self.portal_a2
        self.assertEqual(self._collaborator(self.obj_shared_a, self.portal_a2).access_mode, 'edit')
        # Any portal user (even of another customer) can be invited as owner
        self.kr_internal.owner_id = self.portal_b
        self.assertEqual(self._collaborator(self.obj_shared_a, self.portal_b).access_mode, 'edit')
        self.assertIn(self.obj_shared_a, self._visible(self.portal_b))

    def test_portal_owner_constraints(self):
        with self.assertRaises(ValidationError):
            self.obj_unshared_a.key_result_ids.owner_id = self.portal_a1
        with self.assertRaises(UserError):
            self._collaborator(self.obj_shared_a, self.portal_a1).access_mode = 'read'
        with self.assertRaises(UserError):
            self._collaborator(self.obj_shared_a, self.portal_a1).unlink()
        self.kr_portal.owner_id = self.okr_admin
        self._collaborator(self.obj_shared_a, self.portal_a1).access_mode = 'read'
        self.assertEqual(self._collaborator(self.obj_shared_a, self.portal_a1).access_mode, 'read')

    # ------------------------------------------------------------------
    # Check-in rights
    # ------------------------------------------------------------------
    def test_portal_can_checkin(self):
        self.assertTrue(self.kr_portal._portal_can_checkin(self.portal_a1))
        self.assertTrue(self.kr_internal._portal_can_checkin(self.portal_a1),
                        'Edit collaborators check in on every key result')
        self.assertFalse(self.kr_portal._portal_can_checkin(self.portal_a2), 'Read collaborators only view')
        self.assertFalse(self.kr_portal._portal_can_checkin(self.portal_a3))
        self.assertFalse(self.kr_portal._portal_can_checkin(self.employee_user), 'Employees use the backend')
        self._collaborator(self.obj_shared_a, self.portal_a2).access_mode = 'edit'
        self.assertTrue(self.kr_internal._portal_can_checkin(self.portal_a2))
        self.assertFalse(self.obj_unshared_a.key_result_ids._portal_can_checkin(self.portal_a2),
                         'Not shared on the portal')
        self.obj_shared_a.action_done()
        self.assertFalse(self.kr_portal._portal_can_checkin(self.portal_a1), 'Closed objective')

    def test_portal_submit_checkin(self):
        kr = self.kr_internal.with_user(self.portal_a1)
        checkin = kr._portal_submit_checkin({'new_value': 4.0, 'confidence': '8', 'achievements': 'Done 4'})
        self.assertEqual(checkin.user_id, self.portal_a1)
        self.assertEqual(checkin.state, 'submitted')
        self.assertEqual(self.kr_internal.current_value, 4.0)
        self.assertEqual(self.kr_internal.confidence, '8')
        self.assertEqual(self.kr_internal.progress, 40.0)
        with self.assertRaises(ValidationError):
            self.kr_portal.with_user(self.portal_a2)._portal_submit_checkin({'new_value': 90.0, 'confidence': '9'})
