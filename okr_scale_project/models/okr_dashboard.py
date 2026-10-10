from odoo import _, api, models


class OkrDashboard(models.AbstractModel):
    _inherit = 'okr.scale.dashboard'

    @api.model
    def _get_extra_kpis(self, objectives, cycle):
        kpis = super()._get_extra_kpis(objectives, cycle)
        # The key results are already filtered by the user's rights, their tasks may not be.
        tasks = objectives.key_result_ids.sudo()._get_okr_tasks()
        done = tasks.filtered(lambda t: t.state == '1_done')
        kpis.append({
            'key': 'tasks_done',
            'label': _('Linked tasks done'),
            'value': round(len(done) * 100.0 / len(tasks), 1) if tasks else 0.0,
            'suffix': '%',
        })
        return kpis
