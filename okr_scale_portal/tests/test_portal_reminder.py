from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .common import OkrPortalCommonMixin


@tagged('post_install', '-at_install')
class TestOkrPortalReminder(OkrPortalCommonMixin, TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_okr_portal_data()

    def _reminders(self, kr):
        return self.env['mail.mail'].search([('model', '=', kr._name), ('res_id', '=', kr.id)])

    def test_portal_owner_reminded_once_per_period(self):
        self.assertTrue(self.kr_portal.checkin_due)
        KeyResult = self.env['okr.scale.key.result']
        KeyResult._cron_checkin_reminder()
        mails = self._reminders(self.kr_portal)
        self.assertEqual(len(mails), 1)
        self.assertEqual(mails.recipient_ids, self.portal_a1.partner_id)
        self.assertIn(f'/my/okr/{self.obj_shared_a.id}', mails.body_html)
        self.assertFalse(self.kr_portal.activity_ids, 'Portal owners get an e-mail, not an activity')
        self.assertTrue(self.kr_internal.activity_ids, 'Internal owners still get an activity')
        self.assertTrue(self.kr_portal.portal_reminder_date)

        KeyResult._cron_checkin_reminder()
        self.assertEqual(len(self._reminders(self.kr_portal)), 1, 'No daily spam')

    def test_no_reminder_when_view_only(self):
        self.obj_shared_a.portal_access = 'read'
        self.env['okr.scale.key.result']._cron_checkin_reminder()
        self.assertFalse(self._reminders(self.kr_portal))
