from collections import Counter, defaultdict
from datetime import datetime, time

from odoo import _, api, fields, models

RANKING_SIZE = 10


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

    @api.model
    def _get_extra_rankings(self, cycle, objectives):
        """"Most recognized" board: public kudos received during the cycle.

        Only public recognitions of the current companies are counted, so the board
        never reveals private kudos and is the same for every viewer.
        """
        boards = super()._get_extra_rankings(cycle, objectives)
        rows = []
        if cycle:
            recognitions = self.env['okr.scale.recognition'].sudo().search([
                ('visibility', '=', 'public'),
                ('company_id', 'in', self.env.companies.ids),
            ] + self._cfr_period_domain(cycle))
            counts = Counter()
            values = defaultdict(Counter)
            for recognition in recognitions:
                for receiver in recognition.receiver_ids:
                    if receiver.share or not receiver.active:
                        continue
                    counts[receiver] += 1
                    for value in recognition.core_value_ids:
                        values[receiver][value] += 1
            ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0].name or ''))[:RANKING_SIZE]
            for user, count in ranked:
                top_value = values[user].most_common(1)
                rows.append({
                    'user_id': user.id,
                    'name': user.name,
                    'subtitle': top_value[0][0].display_name if top_value else '',
                    'value': count,
                })
        boards.append({
            'key': 'most_recognized',
            'title': _('Most recognized'),
            'icon': 'fa-heart',
            'unit': _('kudos'),
            'rows': rows,
        })
        return boards

    @api.model
    def _get_my_extra(self):
        tiles = super()._get_my_extra()
        month_start = datetime.combine(fields.Date.context_today(self).replace(day=1), time.min)
        count = self.env['okr.scale.recognition'].search_count([
            ('receiver_ids', 'in', self.env.uid), ('date', '>=', month_start)])
        tiles.append({
            'key': 'kudos_received',
            'label': _('Kudos received (this month)'),
            'value': count,
            'icon': 'fa-heart',
            'action': 'okr_scale_cfr.okr_recognition_action_received',
        })
        return tiles
