from odoo import api, fields, models

PREORDER_PARAM = 'okr_scale_reward_stock.allow_preorder'


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    okr_reward_allow_preorder = fields.Boolean(
        'Allow redemption without stock (pre-order)',
        help='Employees may redeem a gift tracked in inventory even when it is not in stock yet: '
             'the delivery waits until the gift is received.')

    @api.model
    def get_values(self):
        res = super().get_values()
        res['okr_reward_allow_preorder'] = self.env['okr.scale.reward.item']._okr_preorder_allowed()
        return res

    def set_values(self):
        super().set_values()
        # Stored explicitly as 'True' / 'False': an absent parameter means "allowed" (the default).
        self.env['ir.config_parameter'].sudo().set_param(
            PREORDER_PARAM, 'True' if self.okr_reward_allow_preorder else 'False')
