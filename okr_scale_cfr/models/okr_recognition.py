from datetime import datetime, time

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class OkrRecognition(models.Model):
    _name = 'okr.scale.recognition'
    _description = 'OKR Recognition'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'
    # Receivers may answer on the chatter of a kudos they can read.
    _mail_post_access = 'read'

    sender_id = fields.Many2one('res.users', 'From', required=True, readonly=True, index=True,
                                default=lambda self: self.env.user, ondelete='cascade')
    receiver_ids = fields.Many2many(
        'res.users', 'okr_scale_recognition_receiver_rel', 'recognition_id', 'user_id', 'To',
        required=True, domain=[('share', '=', False)])
    message = fields.Html(required=True)
    core_value_ids = fields.Many2many('okr.scale.core.value', string='Core Values')
    objective_id = fields.Many2one('okr.scale.objective', 'Objective', index=True, ondelete='set null')
    key_result_id = fields.Many2one('okr.scale.key.result', 'Key Result', ondelete='set null',
                                    domain="[('objective_id', '=?', objective_id)]")
    date = fields.Datetime(required=True, default=fields.Datetime.now, index=True)
    visibility = fields.Selection([
        ('public', 'Everyone'),
        ('private', 'Sender and receivers'),
    ], default='public', required=True,
        help='Public recognitions are displayed on the wall of the whole company.')
    like_user_ids = fields.Many2many(
        'res.users', 'okr_scale_recognition_like_rel', 'recognition_id', 'user_id', 'Liked By', readonly=True)
    like_count = fields.Integer('Likes', compute='_compute_like_count', store=True)
    liked_by_me = fields.Boolean(compute='_compute_liked_by_me')
    company_id = fields.Many2one('res.company', required=True, index=True, default=lambda self: self.env.company)
    receiver_names = fields.Char('Receivers', compute='_compute_receiver_names')

    @api.depends('receiver_ids')
    def _compute_receiver_names(self):
        for recognition in self:
            names = recognition.receiver_ids.mapped('name')
            if len(names) > 3:
                names = names[:2] + [_('%s others', len(names) - 2)]
            recognition.receiver_names = ', '.join(names)

    @api.depends('sender_id', 'receiver_ids')
    def _compute_display_name(self):
        for recognition in self:
            recognition.display_name = _('Kudos from %(sender)s to %(receivers)s',
                                         sender=recognition.sender_id.name or '',
                                         receivers=', '.join(recognition.receiver_ids.mapped('name')))

    @api.depends('like_user_ids')
    def _compute_like_count(self):
        for recognition in self:
            recognition.like_count = len(recognition.like_user_ids)

    @api.depends_context('uid')
    @api.depends('like_user_ids')
    def _compute_liked_by_me(self):
        for recognition in self:
            recognition.liked_by_me = self.env.user in recognition.like_user_ids

    @api.constrains('sender_id', 'receiver_ids')
    def _check_receivers(self):
        for recognition in self:
            if recognition.sender_id in recognition.receiver_ids:
                raise ValidationError(_('You cannot recognize yourself.'))
            if any(recognition.receiver_ids.mapped('share')):
                raise ValidationError(_('Only internal users can receive a recognition.'))

    @api.onchange('key_result_id')
    def _onchange_key_result_id(self):
        if self.key_result_id:
            self.objective_id = self.key_result_id.objective_id

    def _okr_is_admin(self):
        return self.env.su or self.env.user.has_group('okr_scale.group_okr_admin')

    @api.model_create_multi
    def create(self, vals_list):
        if not self._okr_is_admin():
            # Nobody can send kudos on behalf of someone else.
            for vals in vals_list:
                vals['sender_id'] = self.env.uid
        recognitions = super(OkrRecognition, self.with_context(mail_create_nolog=True)).create(vals_list)
        for recognition in recognitions:
            recognition._notify_receivers()
        return recognitions

    def _notify_receivers(self):
        self.ensure_one()
        partners = self.receiver_ids.partner_id
        self.message_subscribe(partner_ids=partners.ids)
        self.message_post(
            body=Markup('<p>%s</p>%s') % (_('%s recognized you:', self.sender_id.name), self.message),
            partner_ids=partners.ids,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )

    def action_toggle_like(self):
        """Like or unlike: allowed for everybody who can read the recognition."""
        self.check_access_rights('read')
        self.check_access_rule('read')
        user = self.env.user
        for recognition in self:
            command = (3, user.id) if user in recognition.like_user_ids else (4, user.id)
            recognition.sudo().like_user_ids = [command]
        return True

    @api.model
    def _okr_wall_banner_values(self):
        """Figures of the wall header, read with the rights of the current user."""
        month_start = datetime.combine(fields.Date.context_today(self).replace(day=1), time.min)
        domain = [('date', '>=', month_start)]
        this_month = self.search(domain)
        values = self.env['okr.scale.core.value']
        top_value = False
        if this_month:
            counts = {}
            for value in this_month.core_value_ids:
                counts[value] = len(this_month.filtered(lambda r, v=value: v in r.core_value_ids))
            top_value = max(counts, key=counts.get) if counts else values
        return {
            'month_count': len(this_month),
            'received_count': len(this_month.filtered(lambda r: self.env.user in r.receiver_ids)),
            'given_count': len(this_month.filtered(lambda r: r.sender_id == self.env.user)),
            'top_value': top_value.display_name if top_value else False,
            'user': self.env.user,
        }
