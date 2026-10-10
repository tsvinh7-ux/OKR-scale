from odoo import _, api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    okr_manager_auto = fields.Boolean(
        'OKR Manager (from HR)', copy=False,
        help='Set when the OKR Manager group was granted automatically because the user manages '
             'a department or employees in the Employees app.')
    okr_checkin_notified_date = fields.Date(copy=False)

    @api.model
    def _okr_sync_manager_group(self):
        """Mirror the Employees app hierarchy on the OKR Manager group.

        Department managers and employees having subordinates get the group;
        it is removed again when they stop managing, but only if it had been
        granted automatically.
        """
        group = self.env.ref('okr_scale.group_okr_manager', raise_if_not_found=False)
        if not group:
            return
        sudo_self = self.sudo()
        managers = self.env['hr.department'].sudo().search([]).manager_id.user_id \
            | self.env['hr.employee'].sudo().search([('parent_id', '!=', False)]).parent_id.user_id
        managers = managers.filtered(lambda u: not u.share)
        to_add = managers.filtered(lambda u: group not in u.groups_id)
        if to_add:
            to_add.write({'groups_id': [(4, group.id)], 'okr_manager_auto': True})
        admin_group = self.env.ref('okr_scale.group_okr_admin')
        to_remove = sudo_self.search([('okr_manager_auto', '=', True)]) - managers
        to_remove = to_remove.filtered(lambda u: admin_group not in u.groups_id)
        if to_remove:
            to_remove.write({'groups_id': [(3, group.id)], 'okr_manager_auto': False})

    # ------------------------------------------------------------------
    # Notifications: in Odoo (inbox) and by e-mail
    # ------------------------------------------------------------------
    def _okr_send(self, subject, template, values):
        """Deliver an OKR message to the user both in Odoo and by e-mail.

        Users notified by e-mail in their preferences already get the mail from
        ``message_notify``; the others get it in their inbox plus a direct e-mail.
        """
        self.ensure_one()
        values = dict(values, user=self, base_url=self.get_base_url())
        body = self.env['ir.qweb']._render(template, values, minimal_qcontext=True, raise_if_not_found=False)
        if not body:
            return
        partner = self.partner_id
        odoobot = self.env.ref('base.partner_root')
        self.env['mail.thread'].sudo().message_notify(
            partner_ids=partner.ids, subject=subject, body=body, author_id=odoobot.id,
            email_layout_xmlid='mail.mail_notification_light')
        if self.notification_type == 'inbox' and partner.email:
            self.env['mail.mail'].sudo().create({
                'subject': subject,
                'body_html': body,
                'email_to': partner.email_formatted,
                'email_from': self.company_id.email_formatted or odoobot.email_formatted,
                'auto_delete': True,
            })

    def _okr_notify_checkin_due(self, key_results, author=None):
        self.ensure_one()
        if self.share or not key_results:
            return
        self.with_context(lang=self.lang)._okr_send(
            _('OKR: time for your weekly check-in'), 'okr_scale.mail_checkin_due', {
                'key_results': key_results.sudo(),
                'author': author,
                'url': '/web#action=okr_scale.okr_weekly_action',
            })

    @api.model
    def _cron_okr_weekly_digest(self):
        """Monday digest: own key results to watch, and for managers the state of the team."""
        Dashboard = self.env['okr.scale.dashboard']
        KeyResult = self.env['okr.scale.key.result'].sudo()
        owners = KeyResult.search([('objective_state', '=', 'running')]).owner_id
        managers = self.env['hr.employee'].sudo().search([]).okr_manager_user_ids
        for user in (owners | managers).filtered(lambda u: not u.share and u.active):
            digest = Dashboard.with_user(user).with_context(lang=user.lang)._get_weekly_digest()
            if digest['key_results'] or digest['team']:
                user.with_context(lang=user.lang)._okr_send(
                    _('OKR: your weekly digest'), 'okr_scale.mail_weekly_digest', {'digest': digest})
