from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from odoo.addons.okr_scale.tests.common import OkrCommon


@tagged('post_install', '-at_install')
class TestOkrCfr(OkrCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Recognition = cls.env['okr.scale.recognition']
        cls.teamwork = cls.env.ref('okr_scale_cfr.core_value_teamwork')

    def _kudos(self, sender, receivers, **vals):
        return self.Recognition.with_user(sender).create(dict({
            'receiver_ids': [(6, 0, receivers.ids)],
            'message': '<p>Thanks for the help!</p>',
            'core_value_ids': [(6, 0, self.teamwork.ids)],
        }, **vals))

    # ------------------------------------------------------------------
    # Recognition
    # ------------------------------------------------------------------
    def test_recognition_notifies_receivers(self):
        kudos = self._kudos(self.seller, self.seller2 | self.tech)
        self.assertEqual(kudos.sender_id, self.seller)
        self.assertIn(self.seller2.partner_id, kudos.message_partner_ids)
        message = kudos.message_ids.filtered(lambda m: m.message_type == 'comment')[:1]
        self.assertTrue(message)
        self.assertEqual(message.partner_ids, (self.seller2 | self.tech).partner_id)
        self.assertEqual(self.teamwork.recognition_count, 1)

    def test_recognition_sender_cannot_be_forged(self):
        kudos = self._kudos(self.seller, self.tech, sender_id=self.seller2.id)
        self.assertEqual(kudos.sender_id, self.seller)

    def test_self_recognition_blocked(self):
        with self.assertRaises(ValidationError):
            self._kudos(self.seller, self.seller | self.tech)

    def test_private_recognition_visibility(self):
        kudos = self._kudos(self.seller, self.seller2, visibility='private')
        public = self._kudos(self.seller, self.seller2)
        visible_for_tech = self.Recognition.with_user(self.tech).search([])
        self.assertNotIn(kudos, visible_for_tech)
        self.assertIn(public, visible_for_tech)
        with self.assertRaises(AccessError):
            kudos.with_user(self.tech).message
        kudos.with_user(self.seller2).message
        kudos.with_user(self.admin).message
        # Only the sender edits a recognition, everybody who sees it can like it
        with self.assertRaises(AccessError):
            public.with_user(self.tech).write({'message': '<p>Hacked</p>'})
        with self.assertRaises(AccessError):
            kudos.with_user(self.tech).action_toggle_like()
        public.with_user(self.tech).action_toggle_like()
        self.assertEqual(public.like_count, 1)
        self.assertTrue(public.with_user(self.tech).liked_by_me)
        public.with_user(self.tech).action_toggle_like()
        self.assertEqual(public.like_count, 0)

    def test_give_kudos_from_objective(self):
        action = self.sales_obj.with_user(self.seller).action_give_kudos()
        self.assertEqual(action['context']['default_objective_id'], self.sales_obj.id)
        self.assertEqual(action['context']['default_receiver_ids'], [(6, 0, self.sales_manager.ids)])

    # ------------------------------------------------------------------
    # Feedback
    # ------------------------------------------------------------------
    def test_anonymous_feedback_hides_author(self):
        Feedback = self.env['okr.scale.feedback']
        feedback = Feedback.with_user(self.seller).create({
            'recipient_id': self.seller2.id,
            'feedback_type': 'constructive',
            'content': '<p>Please share your pipeline earlier.</p>',
            'anonymous': True,
        })
        feedback.with_user(self.seller).action_give()
        self.assertEqual(feedback.state, 'given')
        as_recipient = feedback.with_user(self.seller2)
        self.assertTrue(as_recipient.author_display)
        self.assertNotEqual(as_recipient.author_display, self.seller.name)
        self.assertFalse(as_recipient.is_author)
        with self.assertRaises(AccessError):
            as_recipient.read(['author_id'])
        with self.assertRaises(AccessError):
            Feedback.with_user(self.seller2).search([('author_id', '=', self.seller.id)])
        self.assertNotIn('create_uid', Feedback._fields)
        # Nothing in the chatter points to the author
        author_partner = self.seller.partner_id
        messages = self.env['mail.message'].search([('model', '=', Feedback._name), ('res_id', '=', feedback.id)])
        self.assertTrue(messages)
        self.assertNotIn(author_partner, messages.author_id)
        self.assertNotIn(self.seller, messages.create_uid)
        self.assertNotIn(author_partner, feedback.message_partner_ids)
        # The author still finds the feedback and sees their own name, admins see everything
        self.assertEqual(feedback.with_user(self.seller).author_display, self.seller.name)
        self.assertIn(feedback, Feedback.with_user(self.seller).search([('is_author', '=', True)]))
        self.assertNotIn(feedback, Feedback.with_user(self.seller2).search([('is_author', '=', True)]))
        self.assertEqual(feedback.with_user(self.admin).author_id, self.seller)
        # Third parties cannot read it, the given feedback is frozen
        with self.assertRaises(AccessError):
            feedback.with_user(self.tech).content
        with self.assertRaises(AccessError):
            feedback.with_user(self.seller).write({'content': '<p>Changed</p>'})

    def test_feedback_request_flow(self):
        wizard = self.env['okr.scale.feedback.request'].with_user(self.seller).create({
            'giver_ids': [(6, 0, (self.seller2 | self.tech | self.seller).ids)],
            'message': 'How was my demo?',
            'objective_id': self.sales_obj.id,
        })
        wizard.action_request()
        Feedback = self.env['okr.scale.feedback']
        requests = Feedback.with_user(self.seller).search([('requested_by_id', '=', self.seller.id)])
        self.assertEqual(len(requests), 2, 'The requester is never asked for feedback about themself')
        self.assertTrue(all(r.state == 'requested' and r.recipient_id == self.seller for r in requests))
        to_answer = Feedback.with_user(self.tech).search([('is_author', '=', True), ('state', '=', 'requested')])
        self.assertEqual(len(to_answer), 1)
        self.assertEqual(to_answer.activity_ids.user_id, self.tech)
        with self.assertRaises(UserError):
            to_answer.with_user(self.tech).action_give()
        to_answer.with_user(self.tech).write({'content': '<p>Great demo</p>', 'feedback_type': 'praise'})
        # The requester cannot write the feedback in place of the giver
        with self.assertRaises(AccessError):
            to_answer.with_user(self.seller).write({'content': '<p>I am the best</p>'})
        with self.assertRaises(AccessError):
            to_answer.with_user(self.seller).action_give()
        to_answer.with_user(self.tech).action_give()
        self.assertEqual(to_answer.state, 'given')
        self.assertFalse(to_answer.activity_ids)
        self.assertEqual(to_answer.with_user(self.seller).author_display, self.tech.name)
        message = to_answer.message_ids[:1]
        self.assertIn(self.seller.partner_id, message.partner_ids)
        # An anonymous answer removes the giver from the followers added by the request activity
        anonymous = (requests - to_answer).with_user(self.seller2)
        self.assertIn(self.seller2.partner_id, anonymous.sudo().message_partner_ids)
        anonymous.write({'content': '<p>Speak slower</p>', 'anonymous': True})
        anonymous.action_give()
        self.assertNotIn(self.seller2.partner_id, anonymous.sudo().message_partner_ids)
        self.assertNotEqual(anonymous.with_user(self.seller).author_display, self.seller2.name)

    # ------------------------------------------------------------------
    # Conversations
    # ------------------------------------------------------------------
    def test_conversation_calendar_event(self):
        Conversation = self.env['okr.scale.conversation']
        with self.assertRaises(AccessError):
            Conversation.with_user(self.seller).create({'employee_user_id': self.seller2.id})
        conversation = Conversation.with_user(self.sales_manager).create({
            'employee_user_id': self.seller.id,
            'objective_ids': [(6, 0, self.sales_obj.ids)],
            'duration': 1.0,
        })
        self.assertEqual(conversation.agenda.count('<h3>'), 4, 'Default agenda with 4 questions')
        self.assertIn(self.seller.name, conversation.name)
        conversation.with_user(self.sales_manager).action_schedule_meeting()
        event = conversation.calendar_event_id
        self.assertTrue(event)
        self.assertEqual(event.partner_ids, (self.sales_manager | self.seller).partner_id)
        self.assertEqual(event.start, conversation.date)
        self.assertEqual(event.duration, 1.0)
        self.assertEqual(event.res_id, conversation.id)
        # Scheduling twice keeps the same meeting, moving the conversation moves the meeting
        conversation.with_user(self.sales_manager).action_schedule_meeting()
        self.assertEqual(conversation.calendar_event_id, event)
        conversation.with_user(self.seller).write({'notes': '<p>All good</p>', 'duration': 2.0})
        self.assertEqual(event.duration, 2.0)
        conversation.with_user(self.seller).action_done()
        self.assertEqual(conversation.state, 'done')
        with self.assertRaises(AccessError):
            conversation.with_user(self.tech).notes

    def test_conversation_needs_two_people(self):
        with self.assertRaises(ValidationError):
            self.env['okr.scale.conversation'].with_user(self.sales_manager).create(
                {'employee_user_id': self.sales_manager.id})

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    def test_dashboard_extra_data(self):
        self._kudos(self.seller, self.seller2)
        self._kudos(self.tech, self.seller2 | self.seller)
        data = self.env['okr.scale.dashboard'].with_user(self.seller).get_dashboard_data(self.cycle.id)
        kpi = next(k for k in data['kpis'] if k['key'] == 'recognitions')
        self.assertEqual(kpi['value'], 2)
        section = next(s for s in data['extra_sections'] if s['key'] == 'top_recognized')
        self.assertEqual(section['rows'][0], [self.seller2.name, 2])
