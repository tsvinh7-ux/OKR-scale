from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class OkrRedemption(models.Model):
    _name = 'okr.scale.redemption'
    _description = 'OKR Reward Redemption'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _mail_post_access = 'read'

    name = fields.Char('Reference', required=True, readonly=True, copy=False, default=lambda self: _('New'))
    user_id = fields.Many2one('res.users', 'Employee', required=True, readonly=True, index=True,
                              default=lambda self: self.env.user, ondelete='cascade')
    item_id = fields.Many2one('okr.scale.reward.item', 'Reward', required=True, readonly=True, index=True,
                              ondelete='restrict')
    image_128 = fields.Image(related='item_id.image_128')
    quantity = fields.Integer(required=True, default=1, readonly=True)
    points = fields.Integer('Total Points', readonly=True)
    state = fields.Selection([
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('delivered', 'Delivered'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], default='requested', required=True, readonly=True, tracking=True, index=True)
    note = fields.Text(help='Delivery details, size, colour...')
    approver_id = fields.Many2one('res.users', 'Approved By', readonly=True)
    request_date = fields.Datetime(default=fields.Datetime.now, readonly=True)
    approve_date = fields.Datetime('Approval Date', readonly=True)
    deliver_date = fields.Datetime('Delivery Date', readonly=True)
    reason = fields.Text('Rejection Reason', tracking=True)
    company_id = fields.Many2one('res.company', required=True, index=True, readonly=True,
                                 default=lambda self: self.env.company)

    @api.constrains('quantity')
    def _check_quantity(self):
        if any(redemption.quantity <= 0 for redemption in self):
            raise ValidationError(_('The quantity must be positive.'))

    def _okr_is_reward_manager(self):
        return self.env.su or self.env.user.has_group('okr_scale.group_okr_admin')

    @api.model_create_multi
    def create(self, vals_list):
        is_manager = self._okr_is_reward_manager()
        Item = self.env['okr.scale.reward.item']
        for vals in vals_list:
            if not is_manager:
                vals['user_id'] = self.env.uid
            item = Item.browse(vals.get('item_id'))
            if not item.exists() or not item.active:
                raise UserError(_('This reward is not available anymore.'))
            quantity = vals.get('quantity') or 1
            vals.update({
                'state': 'requested',
                'quantity': quantity,
                'points': item.points_cost * quantity,
                'company_id': (item.company_id or self.env.company).id,
                'name': self.env['ir.sequence'].sudo().next_by_code('okr.scale.redemption') or _('New'),
            })
            vals.pop('approver_id', None)
        redemptions = super().create(vals_list)
        for redemption in redemptions:
            redemption._reserve()
            redemption._notify_reward_managers()
        return redemptions

    def _reserve(self):
        """Spend the points and reserve the stock as soon as the gift is requested."""
        self.ensure_one()
        cr = self.env.cr
        # Serialize concurrent redemptions of the same user and of the same reward.
        cr.execute('SELECT id FROM res_users WHERE id = %s FOR UPDATE', [self.user_id.id])
        item = self.item_id.sudo()
        cr.execute('SELECT id FROM okr_scale_reward_item WHERE id = %s FOR UPDATE', [item.id])
        item.invalidate_recordset(['stock_qty'])
        Transaction = self.env['okr.scale.point.transaction']
        balance = Transaction._get_balances(self.user_id).get(self.user_id.id, 0)
        if balance < self.points:
            raise UserError(_('Not enough points: "%(item)s" costs %(cost)s points and your balance is %(balance)s.',
                              item=item.name, cost=self.points, balance=balance))
        item._okr_reserve_stock(self.quantity, redemption=self)
        Transaction._grant(self.user_id, -self.points, 'redemption',
                           _('Redemption %(ref)s: %(qty)s x %(item)s', ref=self.name, qty=self.quantity, item=item.name),
                           source=self)

    def _release(self, reason):
        """Give the points back and restore the stock of a rejected or cancelled redemption."""
        self.ensure_one()
        self.item_id.sudo()._okr_release_stock(self.quantity, redemption=self)
        self.env['okr.scale.point.transaction']._grant(
            self.user_id, self.points, 'refund', _('Refund %(ref)s: %(reason)s', ref=self.name, reason=reason),
            source=self)

    def _notify_reward_managers(self):
        managers = self.env.ref('okr_scale.group_okr_admin').sudo().users.filtered(
            lambda u: not u.share and u.active and u._is_internal())
        for manager in managers[:5]:
            self.sudo().activity_schedule(
                'mail.mail_activity_data_todo', user_id=manager.id,
                summary=_('Reward requested: %(item)s for %(user)s', item=self.item_id.name, user=self.user_id.name))

    def _check_reward_manager(self):
        if not self._okr_is_reward_manager():
            raise AccessError(_('Only OKR administrators can process reward redemptions.'))

    def action_approve(self):
        self._check_reward_manager()
        for redemption in self.filtered(lambda r: r.state == 'requested'):
            redemption.write({'state': 'approved', 'approver_id': self.env.uid,
                              'approve_date': fields.Datetime.now()})
            redemption.activity_feedback(['mail.mail_activity_data_todo'])
            redemption.message_post(body=_('Your reward request has been approved.'),
                                    partner_ids=redemption.user_id.partner_id.ids,
                                    subtype_xmlid='mail.mt_comment')

    def action_deliver(self):
        self._check_reward_manager()
        self.filtered(lambda r: r.state == 'approved')._okr_mark_delivered()

    def _okr_mark_delivered(self):
        for redemption in self:
            redemption.write({'state': 'delivered', 'deliver_date': fields.Datetime.now()})
            redemption.message_post(body=_('Your reward has been delivered. Enjoy!'),
                                    partner_ids=redemption.user_id.partner_id.ids,
                                    subtype_xmlid='mail.mt_comment')

    def action_reject(self):
        self._check_reward_manager()
        for redemption in self.filtered(lambda r: r.state in ('requested', 'approved')):
            redemption.write({'state': 'rejected'})
            redemption._release(redemption.reason or _('rejected'))
            redemption.activity_unlink(['mail.mail_activity_data_todo'])
            redemption.message_post(body=_('Your reward request has been rejected and your points refunded.'),
                                    partner_ids=redemption.user_id.partner_id.ids,
                                    subtype_xmlid='mail.mt_comment')

    def action_cancel(self):
        """The employee cancels an unprocessed request; managers may also cancel approved ones."""
        is_manager = self._okr_is_reward_manager()
        for redemption in self:
            allowed_states = ('requested', 'approved') if is_manager else ('requested',)
            if redemption.state not in allowed_states:
                raise UserError(_('Redemption %s cannot be cancelled anymore.', redemption.name))
            if not is_manager and redemption.user_id != self.env.user:
                raise AccessError(_('You can only cancel your own requests.'))
            redemption.sudo().write({'state': 'cancelled'})
            redemption.sudo()._release(_('cancelled'))
            redemption.sudo().activity_unlink(['mail.mail_activity_data_todo'])
