from markupsafe import Markup

from odoo import _, api, fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    okr_key_result_ids = fields.Many2many(
        'okr.scale.key.result', 'okr_scale_key_result_project_rel', 'project_id', 'key_result_id', 'Key Results')
    okr_key_result_count = fields.Integer('OKR', compute='_compute_okr_key_result_count')

    @api.depends('okr_key_result_ids')
    def _compute_okr_key_result_count(self):
        for project in self:
            project.okr_key_result_count = len(project.okr_key_result_ids)

    def action_view_okr_key_results(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('okr_scale.okr_key_result_action')
        action['domain'] = [('project_ids', 'in', self.id)]
        action['context'] = {'default_project_ids': [self.id]}
        return action


class ProjectTask(models.Model):
    _inherit = 'project.task'

    okr_key_result_id = fields.Many2one(
        'okr.scale.key.result', 'Key Result', index='btree_not_null', tracking=True,
        domain="[('objective_state', 'in', ('draft', 'to_approve', 'running'))]",
        help='Key result this task contributes to.')
    okr_objective_id = fields.Many2one(related='okr_key_result_id.objective_id', string='Objective', store=True)

    def write(self, vals):
        newly_done = self.env['project.task']
        if vals.get('state') == '1_done':
            newly_done = self.filtered(lambda t: t.okr_key_result_id and t.state != '1_done')
        res = super().write(vals)
        for task in newly_done:
            # The current user may not be allowed to read the key result.
            task.okr_key_result_id.sudo()._message_log(
                body=Markup(_('Task %s is done.')) % task._get_html_link())
        return res
