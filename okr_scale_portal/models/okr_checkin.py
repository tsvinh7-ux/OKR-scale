from odoo import fields, models


class OkrCheckin(models.Model):
    _inherit = 'okr.scale.checkin'

    # Feedback of the manager stays internal, even through RPC.
    manager_feedback = fields.Text(groups='base.group_user')
