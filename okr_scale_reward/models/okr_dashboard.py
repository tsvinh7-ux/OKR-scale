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

    @api.model
    def _get_extra_rankings(self, cycle, objectives):
        """"Top points" board: points earned during the cycle (spending excluded)."""
        boards = super()._get_extra_rankings(cycle, objectives)
        rows = []
        if cycle:
            data = self.env['okr.scale.point.transaction'].sudo()._read_group(
                self._reward_earning_domain(cycle) + [('user_id.share', '=', False), ('user_id.active', '=', True)],
                ['user_id'], ['points:sum'], order='points:sum desc', limit=10)
            rows = [{
                'user_id': user.id,
                'name': user.name,
                'subtitle': user.employee_id.department_id.name or '',
                'value': points,
            } for user, points in data]
        boards.append({
            'key': 'top_points',
            'title': _('Top points'),
            'icon': 'fa-star',
            'unit': _('points'),
            'rows': rows,
        })
        return boards

    @api.model
    def _get_my_extra(self):
        tiles = super()._get_my_extra()
        user = self.env.user
        tiles += [{
            'key': 'my_points',
            'label': _('My points'),
            'value': user.okr_point_balance,
            'icon': 'fa-star',
            'action': 'okr_scale_reward.okr_point_transaction_action_my',
        }, {
            'key': 'give_budget_left',
            'label': _('Giving budget left'),
            'value': user.okr_give_budget_left,
            'icon': 'fa-heart',
            'action': 'okr_scale_cfr.okr_recognition_action',
        }]
        return tiles
