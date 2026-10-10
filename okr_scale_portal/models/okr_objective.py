from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# Objectives in these states are shown on the customer portal.
PORTAL_STATES = ('running', 'done')


class OkrObjective(models.Model):
    _name = 'okr.scale.objective'
    _inherit = ['okr.scale.objective', 'portal.mixin']

    partner_id = fields.Many2one(
        'res.partner', 'Customer', index=True, tracking=True,
        domain="['|', ('is_company', '=', True), ('parent_id', '=', False)]",
        help='B2B customer (commercial entity) this objective is shared with. '
             'All portal users of this customer can see the objective once it is shared.')
    portal_shared = fields.Boolean(
        'Share on customer portal', tracking=True, copy=False,
        help='Running and closed objectives are visible on the portal of the customer.')
    portal_access = fields.Selection([
        ('read', 'View only'),
        ('contribute', 'View and check-in'),
    ], 'Portal Access', default='read', required=True, tracking=True,
        help='View only: the customer follows the progress and discusses.\n'
             'View and check-in: portal users owning a key result can also check in on it.')
    # Internal assessments are never exposed to portal users, even through RPC.
    self_assessment = fields.Text(groups='base.group_user')
    lessons_learned = fields.Text(groups='base.group_user')

    def _compute_access_url(self):
        super()._compute_access_url()
        for objective in self:
            objective.access_url = f'/my/okr/{objective.id}'

    @api.constrains('portal_shared', 'partner_id')
    def _check_portal_partner(self):
        for objective in self:
            if objective.portal_shared and not objective.partner_id:
                raise ValidationError(_('Select a customer before sharing "%s" on the portal.', objective.name))
            customer = objective.partner_id.commercial_partner_id
            portal_owners = objective.sudo().key_result_ids.owner_id.filtered('share')
            if portal_owners.filtered(lambda u: u.commercial_partner_id != customer):
                raise ValidationError(_(
                    'Some key results of "%s" are owned by portal users of another customer: '
                    'reassign them before changing the customer.', objective.name))

    def write(self, vals):
        res = super().write(vals)
        if vals.get('portal_shared') is False or 'partner_id' in vals:
            # Links sent earlier (access token) must not survive a change of audience.
            self.sudo().filtered('access_token').write({'access_token': False})
        return res

    @api.model
    def _get_mail_message_access(self, res_ids, operation, model_name=None):
        """Portal users may comment on the objectives they can read (portal chatter)."""
        if operation == 'create' and not model_name and self.env.user.share:
            return 'read'
        return super()._get_mail_message_access(res_ids, operation, model_name=model_name)

    def _is_portal_visible(self):
        self.ensure_one()
        return self.portal_shared and self.state in PORTAL_STATES

    def action_preview_portal(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.access_url,
            'target': 'new',
        }
