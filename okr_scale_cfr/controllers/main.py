from odoo import http
from odoo.http import request


class OkrCfrController(http.Controller):

    @http.route('/okr_scale_cfr/wall_banner', type='json', auth='user')
    def wall_banner(self, context=None):
        """Header of the recognition wall (kanban ``banner_route``)."""
        env = request.env(context=dict(request.env.context, **(context or {})))
        values = env['okr.scale.recognition']._okr_wall_banner_values()
        return {'html': env['ir.qweb']._render('okr_scale_cfr.okr_wall_banner', values)}
