from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    okr_point_balance = fields.Integer('Reward Points', compute='_compute_okr_points',
                                       help='Points available to redeem in the reward store.')
    okr_points_given_this_month = fields.Integer('Points Given This Month', compute='_compute_okr_points')
    okr_give_budget_left = fields.Integer('Points Left to Give', compute='_compute_okr_points',
                                          help='Remaining monthly allowance to give points with recognitions.')

    @api.depends_context('uid')
    def _compute_okr_points(self):
        """The wallet is private: only the user and OKR administrators get the figures."""
        is_admin = self.env.su or self.env.user.has_group('okr_scale.group_okr_admin')
        allowed = self if is_admin else self & self.env.user
        balances = self.env['okr.scale.point.transaction']._get_balances(allowed)
        given = self.env['okr.scale.recognition']._okr_points_given(allowed)
        allowance = self.env['okr.scale.point.transaction']._get_reward_param('monthly_allowance')
        for user in self:
            if user in allowed:
                user.okr_point_balance = balances.get(user.id, 0)
                user.okr_points_given_this_month = given.get(user.id, 0)
                user.okr_give_budget_left = max(allowance - user.okr_points_given_this_month, 0)
            else:
                user.okr_point_balance = user.okr_points_given_this_month = user.okr_give_budget_left = 0
