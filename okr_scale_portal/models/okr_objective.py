from odoo import _, api, fields, models
from odoo.exceptions import AccessError

# Objectives in these states are shown on the customer portal.
PORTAL_STATES = ('running', 'done')


class OkrObjective(models.Model):
    _name = 'okr.scale.objective'
    _inherit = ['okr.scale.objective', 'portal.mixin']

    partner_id = fields.Many2one(
        'res.partner', 'Customer', index=True, tracking=True,
        domain="['|', ('is_company', '=', True), ('parent_id', '=', False)]",
        help='B2B customer this objective is about. Informative (grouping, reporting): '
             'only the collaborators invited with the Share button see the objective on the portal.')
    portal_shared = fields.Boolean(
        'Shared on portal', tracking=True, copy=False,
        help='Running and closed objectives are visible on the portal of their collaborators.')
    collaborator_ids = fields.One2many(
        'okr.scale.objective.collaborator', 'objective_id', 'Collaborators', copy=False,
        help='Portal contacts the objective is shared with, with their access mode.')
    collaborator_count = fields.Integer(compute='_compute_collaborator_count')
    can_share = fields.Boolean(compute='_compute_can_share',
                               help='The current user may share this objective with customers.')
    # Internal assessments are never exposed to portal users, even through RPC.
    self_assessment = fields.Text(groups='base.group_user')
    lessons_learned = fields.Text(groups='base.group_user')

    @api.depends('collaborator_ids')
    def _compute_collaborator_count(self):
        for objective in self:
            objective.collaborator_count = len(objective.collaborator_ids)

    @api.depends_context('uid')
    @api.depends('owner_id')
    def _compute_can_share(self):
        is_manager = self.env.user.has_group('okr_scale.group_okr_manager')
        for objective in self:
            objective.can_share = bool(objective.id) and (
                objective._okr_is_admin() or objective.owner_id == self.env.user
                or (is_manager and objective._okr_is_manager_of()))

    def _compute_access_url(self):
        super()._compute_access_url()
        for objective in self:
            objective.access_url = f'/my/okr/{objective.id}'

    def write(self, vals):
        res = super().write(vals)
        if vals.get('portal_shared') is False:
            # Links sent earlier (access token) must not survive a change of audience.
            self.sudo().filtered('access_token').write({'access_token': False})
        return res

    @api.model
    def _get_mail_message_access(self, res_ids, operation, model_name=None):
        """Portal users may comment on the objectives they can read (portal chatter)."""
        if operation == 'create' and not model_name and self.env.user.share:
            return 'read'
        return super()._get_mail_message_access(res_ids, operation, model_name=model_name)

    # ------------------------------------------------------------------
    # Collaborators
    # ------------------------------------------------------------------
    def _is_portal_visible(self):
        self.ensure_one()
        return self.portal_shared and self.state in PORTAL_STATES

    def _check_can_share(self):
        for objective in self:
            if not objective.can_share:
                raise AccessError(_('Only the owner and the managers of "%s" can share it with customers.',
                                    objective.name))

    def _get_collaborator(self, partner):
        """Collaborator record (sudo) of ``partner`` on this objective, or an empty recordset."""
        self.ensure_one()
        return self.sudo().collaborator_ids.filtered(lambda c: c.partner_id == partner)[:1]

    def _portal_access_mode(self, user=None):
        """Access mode ('read' / 'edit') of a portal user on this objective, False if none."""
        self.ensure_one()
        user = user or self.env.user
        return self._get_collaborator(user.partner_id).access_mode or False

    def _add_collaborators(self, partners, access_mode='read', upgrade_only=False):
        """Create or update the collaborators of ``partners``.

        :param upgrade_only: only raise existing collaborators to ``access_mode``
            (used when a portal user becomes key result owner), never downgrade.
        """
        self.ensure_one()
        Collaborator = self.env['okr.scale.objective.collaborator'].sudo()
        for partner in partners:
            collaborator = self._get_collaborator(partner)
            if not collaborator:
                Collaborator.create({'objective_id': self.id, 'partner_id': partner.id, 'access_mode': access_mode})
            elif collaborator.access_mode != access_mode and not (upgrade_only and collaborator.access_mode == 'edit'):
                collaborator.access_mode = access_mode
        return True

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def action_open_share_wizard(self):
        self.ensure_one()
        self._check_can_share()
        return {
            'name': _('Share with customers'),
            'type': 'ir.actions.act_window',
            'res_model': 'okr.scale.share.wizard',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {'default_objective_id': self.id, 'dialog_size': 'medium'},
        }

    def action_view_collaborators(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('okr_scale_portal.okr_collaborator_action')
        action['domain'] = [('objective_id', '=', self.id)]
        action['context'] = {'default_objective_id': self.id}
        return action

    def action_preview_portal(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.access_url,
            'target': 'new',
        }
