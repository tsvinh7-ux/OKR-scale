from odoo import _, api, fields, models

TASK_METHODS = ('tasks', 'task_hours')


class OkrKeyResult(models.Model):
    _inherit = 'okr.scale.key.result'

    progress_method = fields.Selection(selection_add=[
        ('tasks', 'Tasks completed'),
        ('task_hours', 'Tasks completed (weighted by allocated hours)'),
    ], ondelete={'tasks': 'set default', 'task_hours': 'set default'})
    project_ids = fields.Many2many(
        'project.project', 'okr_scale_key_result_project_rel', 'key_result_id', 'project_id', 'Projects',
        help='Every active task of these projects counts towards this key result.')
    task_ids = fields.One2many('project.task', 'okr_key_result_id', 'Tasks',
                               help='Tasks explicitly linked to this key result.')
    task_count = fields.Integer(compute='_compute_task_counts', compute_sudo=True)
    task_done_count = fields.Integer('Tasks Done', compute='_compute_task_counts', compute_sudo=True)

    def _get_okr_tasks(self):
        """Active, non cancelled tasks measuring these key results: the linked
        tasks and every task (sub-tasks included) of the linked projects."""
        return (self.task_ids | self.project_ids.tasks).filtered(lambda t: t.state != '1_canceled')

    @api.depends('task_ids', 'project_ids')
    def _compute_task_counts(self):
        for kr in self:
            tasks = kr._get_okr_tasks()
            kr.task_count = len(tasks)
            kr.task_done_count = len(tasks.filtered(lambda t: t.state == '1_done'))

    @api.depends('task_ids.state', 'task_ids.allocated_hours', 'task_ids.active',
                 'project_ids.tasks.state', 'project_ids.tasks.allocated_hours', 'project_ids.tasks.active')
    def _compute_progress(self):
        return super()._compute_progress()

    def _compute_progress_by_method(self):
        self.ensure_one()
        if self.progress_method not in TASK_METHODS:
            return super()._compute_progress_by_method()
        tasks = self._get_okr_tasks()
        done = tasks.filtered(lambda t: t.state == '1_done')
        total_hours = sum(tasks.mapped('allocated_hours'))
        if self.progress_method == 'task_hours' and total_hours:
            return sum(done.mapped('allocated_hours')) * 100.0 / total_hours
        # Count based, also the fallback when no hours are allocated.
        return len(done) * 100.0 / len(tasks) if tasks else 0.0

    def action_view_tasks(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('project.action_view_all_task')
        action.update({
            'name': _('Tasks: %s', self.name),
            'domain': ['|', ('okr_key_result_id', '=', self.id), ('project_id', 'in', self.project_ids.ids)],
            'context': {'default_okr_key_result_id': self.id},
        })
        return action
