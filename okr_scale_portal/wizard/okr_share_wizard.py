from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import email_normalize


class OkrShareWizard(models.TransientModel):
    """Share an objective with portal contacts, like the project sharing wizard.

    Unlike ``portal.share``, no access token link is ever sent: collaborators
    must log in, so the wizard grants portal access to the contacts that
    have no user yet and e-mails them a sign up link.
    """
    _name = 'okr.scale.share.wizard'
    _description = 'Share an objective on the customer portal'

    objective_id = fields.Many2one('okr.scale.objective', 'Objective', required=True, readonly=True,
                                   ondelete='cascade')
    objective_state = fields.Selection(related='objective_id.state')
    partner_ids = fields.Many2many(
        'res.partner', string='Invite', required=True,
        help='Customer contacts to invite. Contacts without a portal account get one, '
             'with a link to choose their password.')
    access_mode = fields.Selection([
        ('read', 'Read-only'),
        ('edit', 'Edit'),
    ], 'Access', default='read', required=True,
        help='Read-only: follows the progress and discusses in the chatter.\n'
             'Edit: can also check in on every key result of the objective and attach files.')
    note = fields.Text(help='Personal message added to the invitation e-mail.')
    new_user_partner_ids = fields.Many2many(
        'res.partner', compute='_compute_new_user_partner_ids',
        string='New portal accounts')

    @api.depends('partner_ids')
    def _compute_new_user_partner_ids(self):
        for wizard in self:
            wizard.new_user_partner_ids = wizard.partner_ids.filtered(lambda p: not p.sudo().user_ids)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if not res.get('objective_id') and self.env.context.get('active_model') == 'okr.scale.objective':
            res['objective_id'] = self.env.context.get('active_id')
        return res

    # ------------------------------------------------------------------
    # Portal users
    # ------------------------------------------------------------------
    def _check_partners(self):
        """Raise when a contact cannot be invited."""
        Users = self.env['res.users'].sudo().with_context(active_test=False)
        for partner in self.partner_ids:
            users = partner.sudo().with_context(active_test=False).user_ids
            if users.filtered(lambda u: not u.share):
                raise UserError(_('%s is an employee: employees do not need to be invited, they see objectives '
                                  'according to the OKR visibility.', partner.display_name))
            if users:
                continue
            email = email_normalize(partner.email)
            if not email:
                raise UserError(_('%s has no valid e-mail address: it is required to create the portal account.',
                                  partner.display_name))
            if Users.search_count([('login', '=ilike', email)]):
                raise UserError(_('A user with the login %(email)s already exists: %(partner)s cannot get '
                                  'a portal account with the same e-mail.', email=email, partner=partner.display_name))

    def _grant_portal_access(self, partners):
        """Give a (portal) user to the contacts that have none, reactivate archived ones.

        Same logic as the standard portal access wizard (``portal.wizard.user``).
        Return the contacts whose account was just created.
        """
        group_portal = self.env.ref('base.group_portal')
        group_public = self.env.ref('base.group_public')
        company = self.objective_id.company_id
        created = self.env['res.partner']
        for partner in partners.sudo():
            user = partner.with_context(active_test=False).user_ids[:1]
            if not user:
                email = email_normalize(partner.email)
                user = self.env['res.users'].sudo().with_company(company).with_context(
                    no_reset_password=True)._create_user_from_template({
                        'email': email,
                        'login': email,
                        'partner_id': partner.id,
                        'company_id': company.id,
                        'company_ids': [(6, 0, company.ids)],
                    })
                created |= partner
            if not user.active or not user._is_portal():
                user.write({'active': True, 'groups_id': [(4, group_portal.id), (3, group_public.id)]})
                created |= partner
            if partner in created:
                partner.signup_prepare()
        return created

    # ------------------------------------------------------------------
    # Invitation
    # ------------------------------------------------------------------
    def _get_invitation_url(self, partner, signup):
        objective = self.objective_id
        if signup:
            return partner.sudo().with_context(signup_valid=True)._get_signup_url_for_action(
                url=objective.access_url)[partner.id]
        return objective.get_base_url() + objective.access_url

    def _send_invitation(self, partner, signup):
        """Post the invitation (internal note, e-mailed to ``partner``) in their language."""
        self = self.with_context(lang=partner.lang or self.env.lang)
        objective = self.objective_id
        objective.message_post_with_source(
            'okr_scale_portal.okr_share_invitation',
            render_values={
                'partner': partner,
                'objective': objective,
                'note': self.note,
                'access_mode': self.access_mode,
                'share_link': self._get_invitation_url(partner, signup),
                'signup': signup,
            },
            subject=_('Invitation to follow the objective "%s"', objective.name),
            subtype_xmlid='mail.mt_note',
            email_layout_xmlid='mail.mail_notification_light',
            partner_ids=partner.ids,
        )

    def action_send(self):
        self.ensure_one()
        objective = self.objective_id
        objective._check_can_share()
        self._check_partners()
        created = self._grant_portal_access(self.partner_ids)
        objective_sudo = objective.sudo()
        if not objective_sudo.portal_shared:
            objective_sudo.portal_shared = True
        objective_sudo._add_collaborators(self.partner_ids, self.access_mode)
        for partner in self.partner_ids:
            self._send_invitation(partner, signup=partner in created)
        objective_sudo.message_subscribe(partner_ids=self.partner_ids.ids)
        return {'type': 'ir.actions.act_window_close'}
