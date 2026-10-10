from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .common import OkrPortalCommonMixin


@tagged('post_install', '-at_install')
class TestOkrShareWizard(OkrPortalCommonMixin, TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_okr_portal_data()
        cls.contact_new = cls.env['res.partner'].create({
            'name': 'Nguyen Van New', 'email': 'new.contact@example.com', 'parent_id': cls.customer_a.id})

    def _share(self, objective, partners, access_mode='read', user=None, note=False):
        user = user or self.okr_admin
        wizard = self.env['okr.scale.share.wizard'].with_user(user).with_context(
            active_model='okr.scale.objective', active_id=objective.id).create({
                'partner_ids': [(6, 0, partners.ids)], 'access_mode': access_mode, 'note': note})
        self.assertEqual(wizard.objective_id, objective)
        return wizard.action_send()

    def _invitations(self, objective, partner):
        return self.env['mail.message'].search([
            ('model', '=', objective._name), ('res_id', '=', objective.id),
            ('partner_ids', 'in', partner.ids), ('subject', '!=', False),
            ('subtype_id', '=', self.env.ref('mail.mt_note').id)])

    def test_share_creates_portal_user_collaborator_and_mail(self):
        objective = self.obj_unshared_a
        self._share(objective, self.contact_new, 'edit', note='Welcome on board')
        self.assertTrue(objective.portal_shared)
        user = self.contact_new.user_ids
        self.assertEqual(len(user), 1, 'A portal account is created')
        self.assertTrue(user._is_portal())
        self.assertEqual(user.login, 'new.contact@example.com')
        collaborator = objective.collaborator_ids.filtered(lambda c: c.partner_id == self.contact_new)
        self.assertEqual(collaborator.access_mode, 'edit')
        self.assertIn(self.contact_new, objective.message_partner_ids, 'Collaborators follow the objective')

        message = self._invitations(objective, self.contact_new)
        self.assertEqual(len(message), 1)
        self.assertIn('/web/signup', message.body, 'New users get a sign up link')
        self.assertIn('Welcome on board', message.body)
        self.assertTrue(message.notification_ids.filtered(
            lambda n: n.res_partner_id == self.contact_new and n.notification_type == 'email'),
            'The invitation is e-mailed')
        self.assertIn(objective, self.env['okr.scale.objective'].with_user(user).search([]))
        self.assertTrue(objective.key_result_ids._portal_can_checkin(user))

    def test_share_existing_portal_user_and_update_mode(self):
        objective = self.obj_shared_a
        self._share(objective, self.portal_a3.partner_id)
        message = self._invitations(objective, self.portal_a3.partner_id)
        self.assertEqual(len(message), 1)
        self.assertIn(f'/my/okr/{objective.id}', message.body)
        self.assertNotIn('/web/signup', message.body)
        self.assertEqual(len(self.portal_a3.partner_id.user_ids), 1, 'No new account')
        collaborator = objective.collaborator_ids.filtered(lambda c: c.partner_id == self.portal_a3.partner_id)
        self.assertEqual(collaborator.access_mode, 'read')
        self._share(objective, self.portal_a3.partner_id, 'edit')
        self.assertEqual(collaborator.access_mode, 'edit', 'Sharing again updates the access mode')
        self.assertEqual(len(objective.collaborator_ids), 3)

    def test_share_rights_and_checks(self):
        with self.assertRaises(AccessError):
            self._share(self.obj_shared_a, self.portal_a3.partner_id, user=self.employee_user)
        with self.assertRaises(UserError):
            self._share(self.obj_shared_a, self.employee_user.partner_id)
        no_email = self.env['res.partner'].create({'name': 'No Email'})
        with self.assertRaises(UserError):
            self._share(self.obj_shared_a, no_email)
        duplicate = self.env['res.partner'].create({'name': 'Duplicate', 'email': self.portal_b.login})
        with self.assertRaises(UserError):
            self._share(self.obj_shared_a, duplicate)
        # The owner of the objective (not a manager) may share it
        owned = self.env['okr.scale.objective'].create({
            'name': 'Owned', 'cycle_id': self.cycle.id, 'level': 'company', 'owner_id': self.employee_user.id})
        self._share(owned, self.portal_a3.partner_id, user=self.employee_user)
        self.assertEqual(owned.collaborator_ids.partner_id, self.portal_a3.partner_id)
