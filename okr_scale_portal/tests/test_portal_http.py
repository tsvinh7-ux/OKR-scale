import re

from odoo.tests import HttpCase, tagged

from .common import PASSWORD, OkrPortalCommonMixin


@tagged('post_install', '-at_install')
class TestOkrPortalHttp(OkrPortalCommonMixin, HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_okr_portal_data()

    def _csrf_token(self, url):
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200)
        match = re.search(r'csrf_token: "(\w+)"', response.text)
        self.assertTrue(match, 'The portal layout exposes a CSRF token')
        return match.group(1)

    def _post_checkin(self, kr, **values):
        data = {'csrf_token': self._csrf_token('/my/okrs'), 'new_value': '55', 'confidence': '7',
                'achievements': 'Good week'}
        data.update(values)
        return self.url_open(f'/my/okr/kr/{kr.id}/checkin', data=data)

    def test_anonymous_redirected_to_login(self):
        response = self.url_open('/my/okrs', allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertIn('/web/login', response.headers['Location'])

    def test_portal_pages(self):
        self.authenticate(self.portal_a1.login, PASSWORD)
        response = self.url_open('/my/okrs')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Shared with A', response.text)
        self.assertNotIn('Not shared with A', response.text)
        self.assertNotIn('Shared with B', response.text)

        response = self.url_open('/my/okrs?filterby=done&sortby=progress')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Shared with A', response.text)
        response = self.url_open(f'/my/okrs?cycle={self.cycle.id}&sortby=name')
        self.assertIn('Shared with A', response.text)

        response = self.url_open(f'/my/okr/{self.obj_shared_a.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Delivered orders', response.text)
        self.assertIn(f'/my/okr/kr/{self.kr_portal.id}/checkin', response.text, 'Edit collaborators get the form')
        self.assertIn(f'/my/okr/kr/{self.kr_internal.id}/checkin', response.text, 'on every key result')
        self.assertIn('o_okr_access_edit', response.text)
        self.assertIn('o_portal_chatter', response.text)

        for objective in (self.obj_unshared_a, self.obj_shared_b, self.obj_draft_a):
            response = self.url_open(f'/my/okr/{objective.id}')
            self.assertEqual(response.status_code, 404, objective.name)

        counters = self.make_jsonrpc_request('/my/counters', {'counters': ['okr_count']})
        self.assertEqual(counters['okr_count'], 1)
        response = self.url_open('/my')
        self.assertEqual(response.status_code, 200)
        self.assertIn('/my/okrs', response.text)

    def test_portal_chatter(self):
        self.authenticate(self.portal_a1.login, PASSWORD)
        self.make_jsonrpc_request('/mail/chatter_post', {
            'res_model': 'okr.scale.objective', 'res_id': self.obj_shared_a.id, 'message': 'Hello DMAG'})
        result = self.make_jsonrpc_request('/mail/chatter_fetch', {
            'res_model': 'okr.scale.objective', 'res_id': self.obj_shared_a.id})
        self.assertEqual(result['message_count'], 1)
        self.assertIn('Hello DMAG', result['messages'][0]['body'])
        with self.assertRaises(Exception), self.assertLogs('odoo.http', level='WARNING'):
            self.make_jsonrpc_request('/mail/chatter_post', {
                'res_model': 'okr.scale.objective', 'res_id': self.obj_unshared_a.id, 'message': 'Hack'})
        self.assertFalse(self.obj_unshared_a.website_message_ids)

    def test_portal_read_collaborator(self):
        self.authenticate(self.portal_a2.login, PASSWORD)
        response = self.url_open(f'/my/okr/{self.obj_shared_a.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('o_okr_access_read', response.text)
        self.assertIn('o_okr_readonly', response.text, 'Attachments hidden for read-only collaborators')
        self.assertNotIn('/checkin"', response.text, 'No check-in form for read-only collaborators')
        response = self._post_checkin(self.kr_portal)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.kr_portal.current_value, 0)
        self.assertFalse(self.kr_portal.checkin_ids)

        # Upload of attachments is refused, the discussion stays open
        with self.assertLogs('odoo.http', level='WARNING'):
            response = self.url_open('/portal/attachment/add', data={
                'csrf_token': self._csrf_token('/my/okrs'), 'name': 'spec.txt', 'res_model': 'okr.scale.objective',
                'res_id': self.obj_shared_a.id}, files={'file': ('spec.txt', b'hello', 'text/plain')})
        self.assertNotEqual(response.status_code, 200)
        self.make_jsonrpc_request('/mail/chatter_post', {
            'res_model': 'okr.scale.objective', 'res_id': self.obj_shared_a.id, 'message': 'Read-only question'})
        self.assertIn('Read-only question', self.obj_shared_a.website_message_ids.body)

    def test_portal_edit_collaborator_attachment(self):
        self.authenticate(self.portal_a1.login, PASSWORD)
        response = self.url_open('/portal/attachment/add', data={
            'csrf_token': self._csrf_token('/my/okrs'), 'name': 'report.txt', 'res_model': 'okr.scale.objective',
            'res_id': self.obj_shared_a.id}, files={'file': ('report.txt', b'hello', 'text/plain')})
        self.assertEqual(response.status_code, 200)
        self.assertIn('report.txt', response.text)

    def test_portal_not_invited_contact(self):
        """Another contact of the same customer gets a 404 until invited."""
        self.authenticate(self.portal_a3.login, PASSWORD)
        response = self.url_open(f'/my/okr/{self.obj_shared_a.id}')
        self.assertEqual(response.status_code, 404)
        response = self.url_open('/my/okrs')
        self.assertNotIn('Shared with A', response.text)
        response = self._post_checkin(self.kr_portal)
        self.assertEqual(response.status_code, 404)

    def test_portal_checkin(self):
        self.authenticate(self.portal_a1.login, PASSWORD)
        response = self._post_checkin(self.kr_portal)
        self.assertEqual(response.status_code, 200)
        self.assertIn('checkin=done', response.url)
        self.kr_portal.invalidate_recordset()
        self.assertEqual(self.kr_portal.current_value, 55)
        self.assertEqual(self.kr_portal.confidence, '7')
        checkin = self.kr_portal.checkin_ids
        self.assertEqual(checkin.user_id, self.portal_a1)
        self.assertEqual(checkin.achievements, 'Good week')

        # Invalid input is refused without touching the key result
        for values, error in (({'new_value': 'abc'}, 'value'), ({'confidence': '11'}, 'confidence'),
                              ({'blockers': 'x' * 2001}, 'text')):
            response = self._post_checkin(self.kr_portal, **values)
            self.assertEqual(response.status_code, 200)
            self.assertIn(f'checkin_error={error}', response.url)
        self.kr_portal.invalidate_recordset()
        self.assertEqual(self.kr_portal.current_value, 55)
        self.assertEqual(len(self.kr_portal.checkin_ids), 1)

        # Edit collaborators check in on key results they do not own
        response = self._post_checkin(self.kr_internal, new_value='3')
        self.assertIn('checkin=done', response.url)
        self.kr_internal.invalidate_recordset()
        self.assertEqual(self.kr_internal.current_value, 3)
        self.assertEqual(self.kr_internal.checkin_ids.user_id, self.portal_a1)

        # Decimal comma accepted
        self._post_checkin(self.kr_portal, new_value='60,5')
        self.kr_portal.invalidate_recordset()
        self.assertEqual(self.kr_portal.current_value, 60.5)

    def test_portal_checkin_forbidden(self):
        self.authenticate(self.portal_a1.login, PASSWORD)
        self.kr_portal.owner_id = self.okr_admin
        self.obj_shared_a.collaborator_ids.filtered(
            lambda c: c.partner_id == self.portal_a1.partner_id).access_mode = 'read'
        response = self._post_checkin(self.kr_portal)
        self.assertEqual(response.status_code, 403)
        response = self._post_checkin(self.obj_shared_b.key_result_ids)
        self.assertEqual(response.status_code, 404)
        response = self._post_checkin(self.obj_unshared_a.key_result_ids)
        self.assertEqual(response.status_code, 404)
        self.assertFalse(self.kr_portal.checkin_ids)

    def test_internal_preview(self):
        self.authenticate(self.employee_user.login, PASSWORD)
        response = self.url_open(f'/my/okr/{self.obj_shared_a.id}')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(f'/my/okr/kr/{self.kr_portal.id}/checkin', response.text)
        self.assertNotIn('o_okr_readonly', response.text)
        response = self.url_open(f'/my/okr/{self.obj_unshared_a.id}')
        self.assertEqual(response.status_code, 404)
