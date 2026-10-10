from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class OkrKeyResult(models.Model):
    _inherit = 'okr.scale.key.result'

    portal_collaborator_partner_ids = fields.Many2many(
        'res.partner', string='Portal Collaborators', compute='_compute_portal_collaborator_partner_ids',
        help='Contacts the objective is shared with: their portal users may own this key result.')
    portal_reminder_date = fields.Date(
        'Last Portal Reminder', readonly=True, copy=False,
        help='Date of the last check-in reminder e-mailed to the portal owner.')

    @api.depends('objective_id.collaborator_ids.partner_id')
    def _compute_portal_collaborator_partner_ids(self):
        for kr in self:
            kr.portal_collaborator_partner_ids = kr.objective_id.sudo().collaborator_ids.partner_id

    @api.constrains('owner_id', 'objective_id')
    def _check_portal_owner(self):
        for kr in self.sudo():
            owner = kr.owner_id
            if not owner.share:
                continue
            if not owner._is_portal() or not kr.objective_id.portal_shared:
                raise ValidationError(_(
                    'Key result "%(kr)s": %(user)s is not an employee. Only portal users can own key results '
                    'of objectives shared on the portal.', kr=kr.name, user=owner.name))

    def _sync_portal_owner_collaborators(self):
        """Portal owners become edit collaborators of the objective (they must check in)."""
        for kr in self.sudo():
            if kr.owner_id.share and kr.owner_id._is_portal():
                kr.objective_id._add_collaborators(kr.owner_id.partner_id, 'edit', upgrade_only=True)

    @api.model_create_multi
    def create(self, vals_list):
        krs = super().create(vals_list)
        krs._sync_portal_owner_collaborators()
        return krs

    def write(self, vals):
        res = super().write(vals)
        if 'owner_id' in vals or 'objective_id' in vals:
            self._sync_portal_owner_collaborators()
        return res

    # ------------------------------------------------------------------
    # Portal check-in
    # ------------------------------------------------------------------
    def _portal_can_checkin(self, user=None):
        """True when ``user`` (portal) may check in on this key result from the portal:
        edit collaborator of a running objective shared on the portal."""
        self.ensure_one()
        user = user or self.env.user
        kr = self.sudo()
        objective = kr.objective_id
        if not user._is_portal() or not objective.portal_shared or objective.state != 'running':
            return False
        if objective._portal_access_mode(user) != 'edit':
            return False
        # Defense in depth: the portal record rules must grant access as well.
        return bool(kr.with_user(user).search_count([('id', '=', kr.id)]))

    def _portal_submit_checkin(self, values):
        """Create and submit a check-in on behalf of the current portal user.

        Access is checked by :meth:`_portal_can_checkin`; portal users have no
        create right on check-ins, so the record is created with sudo.
        """
        self.ensure_one()
        user = self.env.user
        if not self._portal_can_checkin(user):
            raise ValidationError(_('You are not allowed to check in on this key result.'))
        kr = self.sudo()
        vals = {
            'key_result_id': kr.id,
            'user_id': user.id,
            'confidence': values['confidence'],
            'achievements': values.get('achievements') or False,
            'blockers': values.get('blockers') or False,
            'next_steps': values.get('next_steps') or False,
        }
        if kr.progress_method == 'manual':
            vals['new_value'] = values['new_value']
        else:
            vals['new_value'] = kr.current_value
        checkin = self.env['okr.scale.checkin'].sudo().create(vals)
        checkin.action_submit()
        kr.objective_id.message_post(
            body=_('%(user)s checked in on "%(kr)s" from the customer portal: progress %(progress).0f%%.',
                   user=user.name, kr=kr.name, progress=checkin.progress_after),
            subtype_xmlid='mail.mt_note')
        return checkin

    # ------------------------------------------------------------------
    # Reminders
    # ------------------------------------------------------------------
    def _notify_checkin_due(self, activity_type, today):
        res = super()._notify_checkin_due(activity_type, today)
        if self.owner_id.share:
            self._notify_portal_checkin_due(today)
        return res

    def _notify_portal_checkin_due(self, today):
        """E-mail portal owners, at most once per check-in period."""
        self.ensure_one()
        objective = self.objective_id
        if not objective.portal_shared or not self.owner_id.email \
                or objective._portal_access_mode(self.owner_id) != 'edit':
            return
        if self.portal_reminder_date and (today - self.portal_reminder_date).days < self.cycle_id.get_checkin_days():
            return
        template = self.env.ref('okr_scale_portal.mail_template_okr_portal_checkin_reminder', raise_if_not_found=False)
        if not template:
            return
        template.send_mail(self.id, email_layout_xmlid='mail.mail_notification_light')
        self.sudo().portal_reminder_date = today
