from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    okr_redemption_ids = fields.One2many('okr.scale.redemption', 'picking_id', 'Reward Redemptions')

    def _action_done(self):
        res = super()._action_done()
        # A delivery validated in Inventory delivers the reward too.
        redemptions = self.filtered(lambda p: p.state == 'done').sudo().okr_redemption_ids
        redemptions.filtered(lambda r: r.state == 'approved')._okr_mark_delivered()
        return res
