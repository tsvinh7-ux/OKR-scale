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
        before = self.teamwork.recognition_count
        kudos = self._kudos(self.seller, self.seller2 | self.tech)
        self.assertEqual(kudos.sender_id, self.seller)
        self.assertIn(self.seller2.partner_id, kudos.message_partner_ids)
        message = kudos.message_ids.filtered(lambda m: m.message_type == 'comment')[:1]
        self.assertTrue(message)
        self.assertEqual(message.partner_ids, (self.seller2 | self.tech).partner_id)
        self.teamwork.invalidate_recordset(['recognition_count'])
        self.assertEqual(self.teamwork.recognition_count, before + 1)

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
    def _allow_anonymous(self, allowed=True):
        self.env['ir.config_parameter'].sudo().set_param('okr_scale_cfr.allow_anonymous_feedback', allowed)

    def test_anonymous_feedback_disabled_by_default(self):
        """OKR is transparent: anonymity is off unless an administrator enables it."""
        settings = self.env['res.config.settings'].create({})
        self.assertFalse(settings.okr_allow_anonymous_feedback)
        Feedback = self.env['okr.scale.feedback']
        self.assertFalse(Feedback.with_user(self.seller).new({}).anonymous_allowed)
        with self.assertRaises(ValidationError):
            Feedback.with_user(self.seller).create({
                'recipient_id': self.seller2.id, 'content': '<p>Hidden</p>', 'anonymous': True})
        feedback = Feedback.with_user(self.seller).create({
            'recipient_id': self.seller2.id, 'content': '<p>Signed</p>'})
        with self.assertRaises(ValidationError):
            feedback.write({'anonymous': True})
        feedback.action_give()
        self.assertEqual(feedback.with_user(self.seller2).author_display, self.seller.name)
        # Enabled through the settings, then disabled again: a draft cannot be sent anonymously anymore
        settings.okr_allow_anonymous_feedback = True
        settings.execute()
        self.assertTrue(Feedback.with_user(self.seller).new({}).anonymous_allowed)
        # The form of a new feedback shows the checkbox (computed in the first onchange)
        values = Feedback.with_user(self.seller).onchange({}, [], {'anonymous_allowed': {}, 'company_id': {}})
        self.assertTrue(values['value']['anonymous_allowed'])
        draft = Feedback.with_user(self.seller).create({
            'recipient_id': self.seller2.id, 'content': '<p>Hidden</p>', 'anonymous': True})
        self._allow_anonymous(False)
        with self.assertRaises(UserError):
            draft.action_give()
        draft.write({'anonymous': False})
        draft.action_give()
        self.assertEqual(draft.state, 'given')

    def test_anonymous_feedback_hides_author(self):
        self._allow_anonymous()
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
        self._allow_anonymous()
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
            Conversation.with_user(self.seller).create({
                'employee_user_id': self.seller2.id, 'objective_ids': [(6, 0, self.sales_obj.ids)]})
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
                {'employee_user_id': self.sales_manager.id, 'objective_ids': [(6, 0, self.sales_obj.ids)]})

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    def _age_existing_recognitions(self):
        """Move recognitions already in the database (e.g. demo data) out of the periods measured."""
        self.env['okr.scale.recognition'].flush_model()
        self.env.cr.execute("UPDATE okr_scale_recognition SET date = date - interval '800 days', "
                            "create_date = create_date - interval '800 days'")
        self.env.invalidate_all()

    def test_dashboard_extra_data(self):
        self._age_existing_recognitions()
        self._kudos(self.seller, self.seller2)
        self._kudos(self.tech, self.seller2 | self.seller)
        data = self.env['okr.scale.dashboard'].with_user(self.seller).get_dashboard_data(self.cycle.id)
        kpi = next(k for k in data['kpis'] if k['key'] == 'recognitions')
        self.assertEqual(kpi['value'], 2)
        section = next(s for s in data['extra_sections'] if s['key'] == 'top_recognized')
        self.assertEqual(section['rows'][0], [self.seller2.name, 2])

    def test_rankings_most_recognized(self):
        self._age_existing_recognitions()
        innovation = self.env.ref('okr_scale_cfr.core_value_innovation')
        self._kudos(self.seller, self.seller2)
        self._kudos(self.tech, self.seller2 | self.seller, core_value_ids=[(6, 0, innovation.ids)])
        self._kudos(self.seller, self.tech, visibility='private')
        self._kudos(self.tech, self.seller2, core_value_ids=[(6, 0, innovation.ids)])
        boards = self.env['okr.scale.dashboard'].with_user(self.tech)._get_extra_rankings(self.cycle, None)
        board = next(b for b in boards if b['key'] == 'most_recognized')
        self.assertEqual(board['icon'], 'fa-heart')
        rows = board['rows']
        self.assertEqual(rows[0]['user_id'], self.seller2.id)
        self.assertEqual(rows[0]['value'], 3)
        self.assertEqual(rows[0]['subtitle'], innovation.display_name)
        self.assertEqual(rows[1]['user_id'], self.seller.id)
        self.assertNotIn(self.tech.id, [row['user_id'] for row in rows], 'Private kudos are never ranked')
        # Recognitions of another company are not counted
        other = self.env['res.company'].create({'name': 'Other Co'})
        self.Recognition.sudo().create({
            'sender_id': self.seller.id, 'receiver_ids': [(6, 0, self.tech.ids)], 'message': '<p>x</p>',
            'company_id': other.id})
        boards = self.env['okr.scale.dashboard'].with_user(self.tech)._get_extra_rankings(self.cycle, None)
        board = next(b for b in boards if b['key'] == 'most_recognized')
        self.assertNotIn(self.tech.id, [row['user_id'] for row in board['rows']])

    def test_my_workspace_tile_and_wall_banner(self):
        self._age_existing_recognitions()
        self._kudos(self.seller, self.seller2)
        self._kudos(self.tech, self.seller2, visibility='private')
        tiles = self.env['okr.scale.dashboard'].with_user(self.seller2)._get_my_extra()
        tile = next(t for t in tiles if t['key'] == 'kudos_received')
        self.assertEqual(tile['value'], 2)
        self.assertTrue(self.env.ref(tile['action']))
        values = self.Recognition.with_user(self.seller)._okr_wall_banner_values()
        self.assertEqual(values['month_count'], 1, 'Private kudos of others are not counted')
        self.assertEqual(values['given_count'], 1)
        self.assertEqual(values['top_value'], self.teamwork.display_name)
        html = self.env['ir.qweb'].with_user(self.seller)._render('okr_scale_cfr.okr_wall_banner', values)
        self.assertIn('okr_scale_cfr.okr_recognition_action_new', html)


@tagged('post_install', '-at_install')
class TestOkrOneOnOne(OkrCommon):

    def test_snapshot_and_recurrence(self):
        self.kr_customers.owner_id = self.seller
        checkin = self.env['okr.scale.checkin'].with_user(self.seller).create({
            'key_result_id': self.kr_customers.id, 'new_value': 4, 'confidence': '3', 'blockers': 'No leads'})
        checkin.action_submit()
        activity_type = self.env.ref('okr_scale_cfr.mail_activity_okr_one_on_one')
        activity = self.kr_customers.activity_ids.filtered(lambda a: a.activity_type_id == activity_type)
        self.assertEqual(activity.user_id, self.sales_manager, 'Low confidence asks the manager for a 1:1')

        action = checkin.with_user(self.sales_manager).action_discuss_in_one_on_one()
        Conversation = self.env['okr.scale.conversation'].with_user(self.sales_manager).with_context(action['context'])
        conversation = Conversation.create({'cadence': 'weekly'})
        self.assertEqual(conversation.employee_user_id, self.seller)
        self.assertEqual(conversation.checkin_id, checkin)
        self.assertIn(self.kr_customers, conversation.key_result_ids)
        self.assertIn(checkin, conversation.checkin_ids)
        self.assertIn(self.sales_obj, conversation.objective_ids)

        conversation.action_done()
        following = self.env['okr.scale.conversation'].search([('previous_id', '=', conversation.id)])
        self.assertEqual(len(following), 1, 'Recurring 1:1: next one planned')
        self.assertEqual(following.state, 'planned')
        self.assertEqual((following.date - conversation.date).days, 7)
        self.assertEqual(following.since_date, conversation.date.date())
        conversation.action_plan()
        conversation.action_done()
        self.assertEqual(self.env['okr.scale.conversation'].search_count([('previous_id', '=', conversation.id)]), 1)

    def test_employee_can_request_one_on_one(self):
        conversation = self.env['okr.scale.conversation'].with_user(self.seller).create({
            'manager_id': self.sales_manager.id, 'employee_user_id': self.seller.id, 'cadence': 'none',
            'objective_ids': [(6, 0, self.sales_obj.ids)]})
        self.assertTrue(conversation)
        self.assertEqual(self.sales_obj.with_user(self.sales_manager).conversation_count, 1)

    def test_one_on_one_needs_objectives(self):
        with self.assertRaises(ValidationError):
            self.env['okr.scale.conversation'].with_user(self.sales_manager).create(
                {'employee_user_id': self.seller.id, 'cadence': 'none'})

    def test_confident_checkin_no_activity(self):
        self.kr_customers.owner_id = self.seller
        checkin = self.env['okr.scale.checkin'].with_user(self.seller).create({
            'key_result_id': self.kr_customers.id, 'new_value': 4, 'confidence': '8'})
        checkin.action_submit()
        activity_type = self.env.ref('okr_scale_cfr.mail_activity_okr_one_on_one')
        self.assertFalse(self.kr_customers.activity_ids.filtered(lambda a: a.activity_type_id == activity_type))
