from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDemoData(TransactionCase):
    """The demo is created by the post-install hook: check that every screen has data."""

    def test_marker_and_organisation(self):
        self.assertTrue(self.env['ir.config_parameter'].sudo().get_param('okr_scale_demo.loaded'))
        self.assertEqual(self.env.company.name, 'DMAG')
        users = self.env['res.users'].search([('login', '=like', '%@dmag.vn')])
        self.assertGreaterEqual(len(users), 20)
        self.assertTrue(all(user.employee_id for user in users))
        departments = self.env['hr.department'].search([('parent_id.name', '=', 'Ban Giám đốc')])
        self.assertEqual(len(departments), 7)
        self.assertTrue(all(department.manager_id for department in departments))

    def test_cycles_and_objectives(self):
        Cycle = self.env['okr.scale.cycle']
        q3 = Cycle.search([('name', '=', 'Quý 3/2026')])
        q4 = Cycle.search([('name', '=', 'Quý 4/2026')])
        self.assertEqual(q3.state, 'closed')
        self.assertEqual(q4.state, 'open')
        Objective = self.env['okr.scale.objective']
        q4_objectives = Objective.search([('cycle_id', '=', q4.id)])
        self.assertGreaterEqual(len(q4_objectives), 30)
        self.assertEqual(len(q4_objectives.filtered(lambda o: o.level == 'company')), 3)
        self.assertTrue(q4_objectives.filtered(lambda o: o.state == 'to_approve'))
        self.assertTrue(q4_objectives.filtered(lambda o: o.state == 'draft'))
        self.assertTrue(q4_objectives.filtered(lambda o: o.visibility == 'private'))
        self.assertTrue(q4_objectives.key_result_ids.filtered(lambda k: k.progress_method == 'objectives'))
        self.assertTrue(q4_objectives.key_result_ids.filtered(lambda k: k.progress_method == 'tasks').task_count)
        graded = Objective.search([('cycle_id', '=', q3.id)])
        self.assertTrue(graded)
        self.assertTrue(all(o.state == 'done' and o.self_assessment for o in graded))
        self.assertTrue(self.env['okr.scale.review'].search([('cycle_id', '=', q3.id), ('review_type', '=', 'final')]))

    def test_history(self):
        q4 = self.env['okr.scale.cycle'].search([('name', '=', 'Quý 4/2026')])
        checkins = self.env['okr.scale.checkin'].search([('cycle_id', '=', q4.id)])
        self.assertGreaterEqual(len(checkins), 40)
        self.assertTrue(checkins.filtered('blockers'))
        self.assertGreaterEqual(self.env['okr.scale.checkin'].search_count([]), 300)
        self.assertGreaterEqual(self.env['okr.scale.weekly'].search_count([]), 30)

    def test_cfr_rewards_portal_templates(self):
        self.assertGreaterEqual(self.env['okr.scale.recognition'].search_count([]), 15)
        self.assertGreaterEqual(self.env['okr.scale.feedback'].search_count([('state', '=', 'given')]), 4)
        self.assertTrue(self.env['okr.scale.conversation'].search([('state', '=', 'done')]))
        self.assertTrue(self.env['okr.scale.conversation'].search([('state', '=', 'planned')]))
        items = self.env['okr.scale.reward.item'].search([])
        self.assertGreaterEqual(len(items), 5)
        self.assertTrue(all(item.image_128 for item in items))
        self.assertGreaterEqual(len(self.env['okr.scale.redemption'].search([]).mapped('state')), 3)
        collaborators = self.env['okr.scale.objective.collaborator'].search([])
        self.assertEqual(set(collaborators.mapped('access_mode')), {'read', 'edit'})
        self.assertTrue(collaborators.objective_id.key_result_ids.owner_id.filtered('share'))
        self.assertGreaterEqual(len(self.env['okr.scale.template'].search([('usage_count', '>', 0)])), 2)
        ranking = self.env['okr.scale.dashboard'].get_ranking_data()
        self.assertGreaterEqual(len(ranking['people']), 15)
