from odoo import _, api, models

from .okr_point_transaction import SPENDING_TYPES


class OkrDashboard(models.AbstractModel):
    _inherit = 'okr.scale.dashboard'

    @api.model
    def _reward_earning_domain(self, cycle):
        # Earned points are not sensitive: the leaderboard is shared with everybody,
        # restricted to the companies of the current user.
        return [
            ('points', '>', 0),
            ('transaction_type', 'not in', SPENDING_TYPES),
            ('company_id', 'in', self.env.companies.ids),
        ] + self._cfr_period_domain(cycle)

    @api.model
    def _get_extra_kpis(self, objectives, cycle):
        kpis = super()._get_extra_kpis(objectives, cycle)
        total = 0
        if cycle:
            data = self.env['okr.scale.point.transaction'].sudo()._read_group(
                self._reward_earning_domain(cycle), [], ['points:sum'])
            total = data[0][0] or 0
        kpis.append({'key': 'points_granted', 'label': _('Points granted (this cycle)'), 'value': total,
                     'suffix': ''})
        return kpis

    @api.model
    def _get_extra_sections(self, objectives, cycle):
        sections = super()._get_extra_sections(objectives, cycle)
        rows = []
        if cycle:
            data = self.env['okr.scale.point.transaction'].sudo()._read_group(
                self._reward_earning_domain(cycle), ['user_id'], ['points:sum'], order='points:sum desc', limit=10)
            rows = [[index, user.name, points] for index, (user, points) in enumerate(data, 1)]
        sections.append({
            'key': 'leaderboard',
            'title': _('Leaderboard'),
            'columns': ['#', _('Name'), _('Points')],
            'rows': rows,
        })
        return sections
