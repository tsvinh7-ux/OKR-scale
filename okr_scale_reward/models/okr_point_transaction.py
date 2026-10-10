from datetime import datetime, time

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError

TRANSACTION_TYPES = [
    ('recognition', 'Recognition'),
    ('checkin', 'Check-in'),
    ('kr_achieved', 'Key Result Achieved'),
    ('objective_achieved', 'Objective Achieved'),
    ('manual', 'Manual'),
    ('redemption', 'Redemption'),
    ('refund', 'Refund'),
]
# Transactions that are not earnings (spent or given back points).
SPENDING_TYPES = ('redemption', 'refund')

SOURCE_MODELS = [
    ('okr.scale.recognition', 'Recognition'),
    ('okr.scale.checkin', 'Check-in'),
    ('okr.scale.key.result', 'Key Result'),
    ('okr.scale.objective', 'Objective'),
    ('okr.scale.redemption', 'Redemption'),
]


def month_start(record):
    """First moment of the current month, as a naive UTC datetime."""
    today = fields.Date.context_today(record)
    return datetime.combine(today.replace(day=1), time.min)


class OkrPointTransaction(models.Model):
    """Immutable ledger of reward points: a correction is a new transaction."""
    _name = 'okr.scale.point.transaction'
    _description = 'OKR Point Transaction'
    _order = 'date desc, id desc'
    _rec_name = 'description'

    user_id = fields.Many2one('res.users', 'User', required=True, index=True, ondelete='cascade', readonly=True)
    points = fields.Integer(required=True, readonly=True)
    transaction_type = fields.Selection(TRANSACTION_TYPES, 'Type', required=True, index=True, readonly=True)
    description = fields.Char(required=True, readonly=True)
    date = fields.Datetime(required=True, default=fields.Datetime.now, index=True, readonly=True)
    res_model = fields.Char('Source Model', readonly=True)
    res_id = fields.Many2oneReference('Source ID', model_field='res_model', readonly=True)
    source_ref = fields.Reference(SOURCE_MODELS, 'Source', compute='_compute_source_ref')
    company_id = fields.Many2one('res.company', required=True, index=True, readonly=True,
                                 default=lambda self: self.env.company)
    created_by_id = fields.Many2one('res.users', 'Created By', readonly=True, default=lambda self: self.env.user)

    @api.depends('res_model', 'res_id')
    def _compute_source_ref(self):
        sources = dict(SOURCE_MODELS)
        for transaction in self:
            ref = False
            if transaction.res_model in sources and transaction.res_id:
                if self.env[transaction.res_model].browse(transaction.res_id).exists():
                    ref = '%s,%s' % (transaction.res_model, transaction.res_id)
            transaction.source_ref = ref

    def write(self, vals):
        if self.env.uid != SUPERUSER_ID:
            raise UserError(_('Point transactions cannot be modified. Record a correction transaction instead.'))
        return super().write(vals)

    def unlink(self):
        if self.env.uid != SUPERUSER_ID:
            raise UserError(_('Point transactions cannot be deleted. Record a correction transaction instead.'))
        return super().unlink()

    # ------------------------------------------------------------------
    # Helpers used by the other models
    # ------------------------------------------------------------------
    @api.model
    def _get_reward_param(self, key):
        """Integer setting of the reward program. A missing (or zero) value disables the reward."""
        value = self.env['ir.config_parameter'].sudo().get_param('okr_scale_reward.%s' % key)
        try:
            return max(int(value or 0), 0)
        except ValueError:
            return 0

    @api.model
    def _grant(self, users, points, transaction_type, description, source=None, company=None):
        """Create one transaction per (internal) user. Points are never granted to portal users."""
        users = users.filtered(lambda u: not u.share)
        if not points or not users:
            return self.browse()
        if not company:
            company = source.company_id if source and 'company_id' in source._fields else False
            company = company or self.env.company
        return self.sudo().create([{
            'user_id': user.id,
            'points': points,
            'transaction_type': transaction_type,
            'description': description,
            'res_model': source._name if source else False,
            'res_id': source.id if source else False,
            'company_id': company.id,
        } for user in users])

    @api.model
    def _get_balances(self, users):
        data = self.sudo()._read_group([('user_id', 'in', users.ids)], ['user_id'], ['points:sum'])
        return {user.id: total for user, total in data}
