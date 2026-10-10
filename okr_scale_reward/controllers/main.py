from odoo import http
from odoo.http import request


class OkrRewardController(http.Controller):

    @http.route('/okr_scale_reward/store_banner', type='json', auth='user')
    def store_banner(self, context=None):
        """Wallet header of the reward store (kanban ``banner_route``)."""
        env = request.env(context=dict(request.env.context, **(context or {})))
        values = env['okr.scale.reward.item']._okr_store_banner_values()
        return {'html': env['ir.qweb']._render('okr_scale_reward.okr_store_banner', values)}
