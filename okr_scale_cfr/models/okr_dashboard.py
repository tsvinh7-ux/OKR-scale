from datetime import datetime, time

from odoo import _, api, models


class OkrDashboard(models.AbstractModel):
    _inherit = 'okr.scale.dashboard'

    @api.model
    def _cfr_period_domain(self, cycle, date_field='date'):
        if not cycle:
            return []
        return [(date_field, '>=', datetime.combine(cycle.date_start, time.min)),
                (date_field, '<=', datetime.combine(cycle.date_end, time.max))]

    @api.model
    def _get_extra_kpis(self, objectives, cycle):
        kpis = super()._get_extra_kpis(objectives, cycle)
        count = self.env['okr.scale.recognition'].search_count(self._cfr_period_domain(cycle)) if cycle else 0
        kpis.append({'key': 'recognitions', 'label': _('Recognitions (this cycle)'), 'value': count, 'suffix': ''})
        return kpis

    @api.model
    def _get_extra_sections(self, objectives, cycle):
        sections = super()._get_extra_sections(objectives, cycle)
        rows = []
        if cycle:
            data = self.env['okr.scale.recognition']._read_group(
                self._cfr_period_domain(cycle), ['receiver_ids'], ['__count'], order='__count desc', limit=10)
            rows = [[user.name, count] for user, count in data if user]
        sections.append({
            'key': 'top_recognized',
            'title': _('Top recognized people'),
            'columns': [_('Name'), _('Recognitions')],
            'rows': rows,
        })
        return sections
