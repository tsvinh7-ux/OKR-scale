from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    okr_allow_anonymous_feedback = fields.Boolean(
        'Allow anonymous feedback', config_parameter='okr_scale_cfr.allow_anonymous_feedback',
        help='OKR is built on transparency: by default every feedback shows its author. '
             'Enable this option to let people hide their name from the recipient.')
