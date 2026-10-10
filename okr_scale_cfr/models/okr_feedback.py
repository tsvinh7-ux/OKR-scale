from markupsafe import Markup

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import is_html_empty


class OkrFeedback(models.Model):
    _name = 'okr.scale.feedback'
    _description = 'OKR Feedback'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'
    _rec_name = 'recipient_id'
    # No create_uid / write_uid columns: they would reveal the author of anonymous feedback.
    _log_access = False

    # The real author is only readable by OKR administrators. Everybody else
    # reads ``author_display``, which hides the author of anonymous feedback.
    author_id = fields.Many2one('res.users', 'Author', required=True, index=True, ondelete='cascade',
                                default=lambda self: self.env.user, groups='okr_scale.group_okr_admin')
    author_display = fields.Char('From', compute='_compute_author_display')
    is_author = fields.Boolean(compute='_compute_author_display', search='_search_is_author')
    recipient_id = fields.Many2one('res.users', 'About', required=True, index=True, ondelete='cascade',
                                   domain=[('share', '=', False)],
                                   help='Person who receives the feedback.')
    requested_by_id = fields.Many2one('res.users', 'Requested By', readonly=True, index=True, ondelete='set null')
    request_message = fields.Text('Request', readonly=True)
    objective_id = fields.Many2one('okr.scale.objective', 'Objective', ondelete='set null')
    key_result_id = fields.Many2one('okr.scale.key.result', 'Key Result', ondelete='set null',
                                    domain="[('objective_id', '=?', objective_id)]")
    feedback_type = fields.Selection([
        ('praise', 'Praise'),
        ('constructive', 'Constructive'),
        ('suggestion', 'Suggestion'),
    ], 'Type', required=True, default='praise')
    content = fields.Html('Feedback')
    anonymous = fields.Boolean(help='The recipient will not see who wrote this feedback.')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('given', 'Given'),
    ], default='draft', required=True, index=True)
    date = fields.Datetime(required=True, readonly=True, default=fields.Datetime.now, index=True)
    given_date = fields.Datetime(readonly=True)
    company_id = fields.Many2one('res.company', required=True, index=True, default=lambda self: self.env.company)

    @api.depends_context('uid')
    @api.depends('anonymous', 'author_id')
    def _compute_author_display(self):
        is_admin = self._okr_is_admin()
        for feedback in self:
            author = feedback.sudo().author_id
            feedback.is_author = author == self.env.user
            if feedback.anonymous and not is_admin and not feedback.is_author:
                feedback.author_display = _('Anonymous')
            else:
                feedback.author_display = author.name

    def _search_is_author(self, operator, value):
        if operator not in ('=', '!=') or not isinstance(value, bool):
            raise NotImplementedError(_('Operation not supported'))
        mine = self.sudo().with_context(active_test=False)._search([('author_id', '=', self.env.uid)])
        return [('id', 'in' if (operator == '=') == value else 'not in', mine)]

    @api.constrains('author_id', 'recipient_id')
    def _check_recipient(self):
        for feedback in self.sudo():
            if feedback.author_id == feedback.recipient_id:
                raise ValidationError(_('You cannot give feedback to yourself.'))

    @api.onchange('key_result_id')
    def _onchange_key_result_id(self):
        if self.key_result_id:
            self.objective_id = self.key_result_id.objective_id

    def _okr_is_admin(self):
        return self.env.su or self.env.user.has_group('okr_scale.group_okr_admin')

    @api.model_create_multi
    def create(self, vals_list):
        if not self._okr_is_admin():
            # Feedback requests are created by the request wizard; users only write their own feedback.
            for vals in vals_list:
                vals.update(author_id=self.env.uid, state='draft', requested_by_id=False)
        return super(OkrFeedback, self.with_context(mail_create_nolog=True, mail_create_nosubscribe=True,
                                                    mail_notrack=True)).create(vals_list)

    def action_give(self):
        for feedback in self:
            if feedback.state == 'given':
                continue
            if not feedback.is_author and not self._okr_is_admin():
                raise AccessError(_('Only the author can give this feedback.'))
            if is_html_empty(feedback.content):
                raise UserError(_('Write your feedback before sending it.'))
            feedback.write({'state': 'given', 'given_date': fields.Datetime.now()})
            feedback._notify_given()
        return True

    def _notify_given(self):
        """Notify the recipient (and requester) without leaving any trace of an anonymous author."""
        self.ensure_one()
        if self.anonymous:
            poster = self.with_user(SUPERUSER_ID)
            author = self.env.ref('base.partner_root')
        else:
            poster = self.sudo()
            author = self.sudo().author_id.partner_id
        poster.activity_unlink(['okr_scale_cfr.mail_activity_okr_feedback'])
        if self.anonymous:
            # The request activity subscribed the giver: do not list them among the followers.
            poster.message_unsubscribe(partner_ids=self.sudo().author_id.partner_id.ids)
        partners = (self.recipient_id | self.requested_by_id).partner_id
        poster.message_post(
            body=Markup('<p>%s</p>%s') % (
                _('New feedback from %(author)s about %(recipient)s.',
                  author=self.author_display, recipient=self.recipient_id.name),
                self.content),
            author_id=author.id,
            partner_ids=partners.ids,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )

    def action_give_and_close(self):
        self.action_give()
        return {'type': 'ir.actions.act_window_close'}
