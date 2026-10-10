from odoo.exceptions import AccessError, UserError
from odoo.tests import Form, tagged

from odoo.addons.okr_scale.tests.common import OkrCommon


@tagged('post_install', '-at_install')
class TestOkrTemplate(OkrCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category = cls.env['okr.scale.template.category'].create({'name': 'Test category', 'icon': 'fa-heart'})
        cls.template = cls.env['okr.scale.template'].create({
            'name': 'Delight our patients',
            'category_id': cls.category.id,
            'level': 'company',
            'okr_type': 'aspirational',
            'line_ids': [
                (0, 0, {'sequence': 1, 'name': 'NPS', 'metric_type': 'number', 'unit': 'pts',
                        'start_value': 40, 'target_value': 60, 'weight': 2}),
                (0, 0, {'sequence': 2, 'name': 'No-show rate', 'metric_type': 'percent', 'unit': '%',
                        'start_value': 18, 'target_value': 8}),
                (0, 0, {'sequence': 3, 'name': 'Recall program live', 'metric_type': 'boolean',
                        'start_value': 0, 'target_value': 1}),
            ],
        })

    def _wizard(self, user, **values):
        Wizard = self.env['okr.scale.template.apply'].with_user(user).with_context(
            default_template_id=self.template.id)
        form = Form(Wizard)
        form.cycle_id = self.cycle
        for name, value in values.items():
            setattr(form, name, value)
        return form

    def test_data_loaded(self):
        templates = self.env['okr.scale.template'].search([])
        self.assertGreaterEqual(len(templates.filtered(lambda t: t.get_external_id()[t.id].startswith(
            'okr_scale_template.'))), 20)
        self.assertEqual(self.env['okr.scale.template.category'].search_count(
            [('id', 'in', [self.env.ref('okr_scale_template.okr_tpl_cat_%s' % xid).id for xid in (
                'sales', 'care', 'clinical', 'marketing', 'operations', 'hr', 'finance', 'tech')])]), 8)
        for template in templates.filtered(lambda t: t.get_external_id()[t.id].startswith('okr_scale_template.')):
            self.assertTrue(3 <= template.line_count <= 4, template.name)
            self.assertTrue(template.category_id, template.name)

    def test_apply_individual_as_user(self):
        form = self._wizard(self.seller)
        # A plain user cannot set company objectives: the wizard proposes an individual one.
        self.assertEqual(form.level, 'individual')
        self.assertEqual(form.employee_id, self.emp_seller)
        self.assertEqual(form.name, 'Delight our patients')
        self.assertEqual(len(form.line_ids), 3)
        form.name = 'Delight my patients'
        with form.line_ids.edit(0) as line:
            line.target_value = 75
        with form.line_ids.edit(2) as line:
            line.include = False
        wizard = form.save()
        action = wizard.action_apply()
        objective = self.env['okr.scale.objective'].browse(action['res_id'])
        self.assertEqual(objective.create_uid, self.seller)
        self.assertEqual(objective.state, 'draft')
        self.assertEqual(objective.level, 'individual')
        self.assertEqual(objective.employee_id, self.emp_seller)
        self.assertEqual(objective.owner_id, self.seller)
        self.assertEqual(objective.okr_type, 'aspirational')
        self.assertEqual(objective.name, 'Delight my patients')
        self.assertEqual(objective.key_result_ids.mapped('name'), ['NPS', 'No-show rate'])
        nps, no_show = objective.key_result_ids
        self.assertEqual((nps.start_value, nps.target_value, nps.weight, nps.unit), (40, 75, 2, 'pts'))
        self.assertEqual((no_show.start_value, no_show.target_value, no_show.current_value), (18, 8, 18))
        self.assertEqual(no_show.progress, 0.0)
        self.assertEqual(self.template.usage_count, 1)

    def test_apply_respects_level_rights(self):
        form = self._wizard(self.seller)
        form.level = 'company'
        wizard = form.save()
        with self.assertRaises(AccessError):
            wizard.action_apply()
        form = self._wizard(self.seller)
        form.level = 'department'
        form.department_id = self.dep_sales
        wizard = form.save()
        with self.assertRaises(AccessError):
            wizard.action_apply()
        # Someone else's individual objective is refused too
        form = self._wizard(self.tech)
        form.employee_id = self.emp_seller
        wizard = form.save()
        with self.assertRaises(AccessError):
            wizard.action_apply()
        self.assertEqual(self.template.usage_count, 0)

    def test_apply_department_and_alignment(self):
        form = self._wizard(self.sales_manager)
        self.assertEqual(form.level, 'department')
        self.assertEqual(form.department_id, self.dep_sales)
        form.parent_key_result_id = self.kr_sales
        action = form.save().action_apply()
        objective = self.env['okr.scale.objective'].browse(action['res_id'])
        self.assertEqual(objective.department_id, self.dep_sales)
        self.assertEqual(objective.parent_id, self.company_obj)
        self.assertEqual(len(objective.key_result_ids), 3)
        # Company level kept for OKR administrators
        form = self._wizard(self.admin)
        self.assertEqual(form.level, 'company')

    def test_fill_existing_draft_objective(self):
        objective = self.env['okr.scale.objective'].with_user(self.seller).create({
            'name': 'My own words', 'cycle_id': self.cycle.id, 'level': 'individual',
            'employee_id': self.emp_seller.id})
        action = objective.action_start_from_template()
        self.assertEqual(action['context']['okr_tpl_objective_id'], objective.id)
        use = self.template.with_user(self.seller).with_context(action['context']).action_use_template()
        self.assertEqual(use['context']['default_objective_id'], objective.id)
        wizard = Form(self.env['okr.scale.template.apply'].with_user(self.seller).with_context(use['context'])).save()
        wizard.action_apply()
        self.assertEqual(objective.name, 'My own words')
        self.assertEqual(len(objective.key_result_ids), 3)
        objective.sudo().state = 'running'
        with self.assertRaises(UserError):
            Form(self.env['okr.scale.template.apply'].with_user(self.seller).with_context(
                use['context'])).save().action_apply()

    def test_save_as_template(self):
        with self.assertRaises(AccessError):
            self.sales_obj.with_user(self.seller).action_save_as_template()
        action = self.company_obj.with_user(self.ceo).action_save_as_template()
        template = self.env['okr.scale.template'].browse(action['res_id'])
        self.assertEqual(template.name, 'Grow revenue')
        self.assertEqual(template.level, 'company')
        self.assertEqual(template.source_objective_id, self.company_obj)
        self.assertEqual(template.line_ids.mapped('name'), ['Revenue 10B', 'Sales objectives'])
        revenue, sales = template.line_ids
        self.assertEqual((revenue.start_value, revenue.target_value), (0, 10))
        # Measured from aligned objectives: proposed as a percentage
        self.assertEqual((sales.metric_type, sales.start_value, sales.target_value), ('percent', 0, 100))
        self.assertEqual(template.line_preview, 'Revenue 10B\nSales objectives')

    def test_template_rights_and_search(self):
        Template = self.env['okr.scale.template']
        with self.assertRaises(AccessError):
            Template.with_user(self.seller).create({'name': 'Nope'})
        self.assertTrue(Template.with_user(self.seller).search([('id', '=', self.template.id)]))
        Template.with_user(self.ceo).create({'name': 'Manager template'})
        self.template.keywords = 'nps, reviews'
        self.assertIn(self.template, Template.browse([r[0] for r in Template.name_search('reviews')]))
        values = Template.search_panel_select_range('category_id')['values']
        value = next(v for v in values if v['id'] == self.category.id)
        self.assertEqual(value['okr_tpl_icon'], 'fa-heart')
