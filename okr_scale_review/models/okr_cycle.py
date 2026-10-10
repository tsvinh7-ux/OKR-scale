from datetime import timedelta

from odoo import _, api, fields, models
from odoo.addons.okr_scale.models.okr_common import time_progress

# Final reminders are not sent for cycles that ended long before the module was installed.
FINAL_REMINDER_GRACE_DAYS = 14


class OkrCycle(models.Model):
    _name = 'okr.scale.cycle'
    _inherit = ['okr.scale.cycle', 'mail.activity.mixin']

    mid_review_reminded = fields.Boolean(
        'Mid-cycle Review Reminded', copy=False, readonly=True,
        help='Set once the mid-cycle review activities have been scheduled.')
    final_review_reminded = fields.Boolean(
        'Final Review Reminded', copy=False, readonly=True,
        help='Set once the end-of-cycle review activities have been scheduled.')
    review_ids = fields.One2many('okr.scale.review', 'cycle_id', 'Reviews')
    review_count = fields.Integer(compute='_compute_review_count')

    def _compute_review_count(self):
        data = self.env['okr.scale.review']._read_group(
            [('cycle_id', 'in', self.ids)], ['cycle_id'], ['__count'])
        counts = {cycle.id: count for cycle, count in data}
        for cycle in self:
            cycle.review_count = counts.get(cycle.id, 0)

    def _okr_next_cycle(self):
        """The cycle following this one: same type first, then any later cycle of the company."""
        self.ensure_one()
        later = self.search([
            ('id', '!=', self.id),
            ('date_start', '>', self.date_end),
            ('company_id', '=', self.company_id.id),
            ('state', '!=', 'closed'),
        ], order='date_start asc, id asc')
        return (later.filtered(lambda c: c.cycle_type == self.cycle_type) or later)[:1]

    def action_open_cycle_review(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'okr_scale_review.cycle_review',
            'name': _('Cycle Review'),
            'params': {'cycle_id': self.id},
            'context': {'active_id': self.id, 'active_model': self._name},
        }

    def action_view_reviews(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('okr_scale_review.okr_review_action')
        action['domain'] = [('cycle_id', '=', self.id)]
        action['context'] = {'default_cycle_id': self.id}
        return action

    # ------------------------------------------------------------------
    # Reminders
    # ------------------------------------------------------------------
    def _review_reminder_users(self):
        """OKR administrators and the managers of the departments taking part in the cycle."""
        self.ensure_one()
        admins = self.env.ref('okr_scale.group_okr_admin').sudo().users
        departments = self.env['okr.scale.objective'].sudo().search([
            ('cycle_id', '=', self.id), ('state', 'in', ('running', 'done')),
            ('department_id', '!=', False)]).department_id
        users = admins | departments.manager_id.user_id
        return users.filtered(lambda u: u.active and not u.share and self.company_id in u.company_ids)

    def _schedule_review_activity(self, review_type):
        self.ensure_one()
        xmlid = 'okr_scale_review.mail_activity_okr_mid_review' if review_type == 'mid' \
            else 'okr_scale_review.mail_activity_okr_final_review'
        activity_type = self.env.ref(xmlid)
        today = fields.Date.context_today(self)
        users = self._review_reminder_users()
        for user in users:
            already = self.activity_ids.filtered(
                lambda a, u=user: a.activity_type_id == activity_type and a.user_id == u)
            if already:
                continue
            # Texts in the language of each assignee (the cron has no language)
            summary, note = self.with_context(lang=user.lang)._review_reminder_texts(review_type)
            self.activity_schedule(
                activity_type_id=activity_type.id, user_id=user.id,
                date_deadline=today + timedelta(days=activity_type.delay_count or 7),
                summary=summary, note=note)
        return users

    def _review_reminder_texts(self, review_type):
        self.ensure_one()
        if review_type == 'mid':
            return (_('Mid-cycle review: %s', self.name),
                    _('Half of the cycle is over: look back at the scores, unblock what is off track '
                      'and adjust the plan with your team.'))
        return (_('Final review: %s', self.name),
                _('The cycle has ended: grade the objectives, share what went well and the lessons learned, '
                  'then carry unfinished key results over to the next cycle.'))

    @api.model
    def _cron_review_reminders(self):
        """Once per cycle: a mid-cycle review activity at 50 % of the cycle, a final review one at its end."""
        today = fields.Date.context_today(self)
        mid_cycles = self.search([('state', '=', 'open'), ('mid_review_reminded', '=', False),
                                  ('date_start', '<=', today), ('date_end', '>', today)])
        for cycle in mid_cycles:
            if time_progress(cycle.date_start, cycle.date_end, today) >= 50:
                cycle._schedule_review_activity('mid')
                cycle.mid_review_reminded = True
        final_cycles = self.search([
            ('state', 'in', ('open', 'closed')), ('final_review_reminded', '=', False),
            ('date_end', '>=', today - timedelta(days=FINAL_REMINDER_GRACE_DAYS)),
            '|', ('date_end', '<=', today), ('state', '=', 'closed')])
        for cycle in final_cycles:
            cycle._schedule_review_activity('final')
            cycle.write({'final_review_reminded': True, 'mid_review_reminded': True})
