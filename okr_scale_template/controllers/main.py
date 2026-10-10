from odoo import http
from odoo.http import request


class OkrTemplateController(http.Controller):

    @http.route('/okr_scale_template/gallery_banner', type='json', auth='user')
    def gallery_banner(self, **kwargs):
        """Hero displayed above the template gallery (kanban ``banner_route``)."""
        env = request.env
        values = {
            'template_count': env['okr.scale.template'].search_count([]),
            'category_count': env['okr.scale.template.category'].search_count([]),
            'usage_count': sum(env['okr.scale.template'].search([]).mapped('usage_count')),
        }
        return {'html': env['ir.qweb']._render('okr_scale_template.okr_tpl_gallery_banner', values)}
