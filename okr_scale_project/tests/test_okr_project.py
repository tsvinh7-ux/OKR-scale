from odoo.tests import Form, new_test_user, tagged

from odoo.addons.okr_scale.tests.common import OkrCommon


@tagged('post_install', '-at_install')
class TestOkrProject(OkrCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project_user = new_test_user(cls.env, 'okr_project_user',
                                         groups='base.group_user,project.group_project_user')
        cls.project = cls.env['project.project'].create({
            'name': 'CRM roll-out', 'privacy_visibility': 'employees'})
        cls.kr_tasks = cls.env['okr.scale.key.result'].create({
            'objective_id': cls.sales_obj.id, 'name': 'Deliver the CRM', 'progress_method': 'tasks'})
        Task = cls.env['project.task']
        cls.task1, cls.task2, cls.task3, cls.task4 = Task.create([{
            'name': f'Task {i}', 'project_id': cls.project.id, 'allocated_hours': hours,
            'okr_key_result_id': cls.kr_tasks.id,
        } for i, hours in enumerate((10, 20, 30, 40), 1)])

    def test_progress_from_task_count(self):
        self.assertEqual(self.kr_tasks.progress, 0)
        self.task1.state = '1_done'
        self.assertEqual(self.kr_tasks.progress, 25)
        self.assertEqual((self.kr_tasks.task_done_count, self.kr_tasks.task_count), (1, 4))
        self.task2.state = '1_done'
        self.assertEqual(self.kr_tasks.progress, 50)
        self.assertEqual(self.sales_obj.progress, (0 + 50) / 2, 'Objective rolls up the task based progress')
        self.task2.state = '01_in_progress'
        self.assertEqual(self.kr_tasks.progress, 25, 'Progress follows reopened tasks')

    def test_progress_from_allocated_hours(self):
        self.kr_tasks.progress_method = 'task_hours'
        self.task4.state = '1_done'
        self.assertEqual(self.kr_tasks.progress, 40)
        self.task4.allocated_hours = 60
        self.assertEqual(self.kr_tasks.progress, 50)
        (self.task1 | self.task2 | self.task3 | self.task4).allocated_hours = 0
        self.assertEqual(self.kr_tasks.progress, 25, 'Falls back on the task count without hours')

    def test_cancelled_and_archived_tasks_excluded(self):
        self.task1.state = '1_done'
        self.task2.state = '1_canceled'
        self.assertAlmostEqual(self.kr_tasks.progress, 100 / 3)
        self.task3.active = False
        self.assertEqual(self.kr_tasks.progress, 50)
        self.assertEqual(self.kr_tasks.task_count, 2)

    def test_project_link(self):
        project = self.env['project.project'].create({'name': 'Website'})
        tasks = self.env['project.task'].create([{'name': f'Page {i}', 'project_id': project.id} for i in range(4)])
        kr = self.env['okr.scale.key.result'].create({
            'objective_id': self.sales_obj.id, 'name': 'Launch the website', 'progress_method': 'tasks',
            'project_ids': [(4, project.id)]})
        self.assertEqual(project.okr_key_result_ids, kr)
        self.assertEqual(project.okr_key_result_count, 1)
        self.assertEqual(kr.task_count, 4)
        tasks[0].state = '1_done'
        self.assertEqual(kr.progress, 25)
        self.env['project.task'].create({'name': 'Late page', 'project_id': project.id})
        self.assertEqual(kr.progress, 20, 'New tasks of a linked project are counted')
        # A task both linked and in the project is counted once.
        tasks[1].okr_key_result_id = kr
        self.assertEqual(kr.task_count, 5)
        action = kr.action_view_tasks()
        self.assertEqual(self.env['project.task'].search(action['domain']), project.tasks)
        self.assertEqual(self.env['okr.scale.key.result'].search(project.action_view_okr_key_results()['domain']),
                         kr)

    def test_other_methods_unchanged(self):
        self.kr_tasks.write({'progress_method': 'manual', 'start_value': 0, 'target_value': 10, 'current_value': 3})
        self.assertEqual(self.kr_tasks.progress, 30)

    def test_done_note_on_key_result(self):
        self.task1.with_user(self.project_user).state = '1_done'
        self.assertIn('Task 1', self.kr_tasks.message_ids[0].body)

    def test_project_user_without_okr_access(self):
        private_obj = self.env['okr.scale.objective'].create({
            'name': 'Secret plan', 'cycle_id': self.cycle.id, 'level': 'individual',
            'employee_id': self.emp_tech.id, 'visibility': 'private',
            'key_result_ids': [(0, 0, {'name': 'Secret KR', 'progress_method': 'tasks'})],
        })
        private_kr = private_obj.key_result_ids
        self.task1.okr_key_result_id = private_kr
        KeyResult = self.env['okr.scale.key.result'].with_user(self.project_user)
        self.assertFalse(KeyResult.search([('id', '=', private_kr.id)]), 'Test needs a hidden key result')

        task = self.task1.with_user(self.project_user)
        with Form(task) as form:
            self.assertEqual(form.okr_key_result_id.id, private_kr.id)
            form.state = '1_done'
        self.assertEqual(task.read(['okr_key_result_id'])[0]['okr_key_result_id'][0], private_kr.id)
        self.assertEqual(private_kr.progress, 100, 'Progress is updated even without access to the key result')
        self.project.okr_key_result_ids = self.kr_tasks | private_kr
        self.assertEqual(self.project.okr_key_result_count, 2)
        self.env.invalidate_all()
        self.assertEqual(self.project.with_user(self.project_user).okr_key_result_count, 1,
                         'Only the visible key results are counted')

    def test_key_result_form_for_okr_user(self):
        self.task1.state = '1_done'
        with Form(self.kr_tasks.with_user(self.sales_manager)) as form:
            self.assertEqual(form.task_done_count, 1)

    def test_dashboard_kpi(self):
        self.task1.state = '1_done'
        data = self.env['okr.scale.dashboard'].with_user(self.sales_manager).get_dashboard_data(self.cycle.id)
        kpi = next(k for k in data['kpis'] if k['key'] == 'tasks_done')
        self.assertEqual(kpi['value'], 25)
