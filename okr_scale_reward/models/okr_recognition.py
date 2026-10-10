from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .okr_point_transaction import month_start


class OkrRecognition(models.Model):
    _inherit = 'okr.scale.recognition'

    points = fields.Integer(default=0, help='Reward points given to each receiver. They are taken from your '
                                            'monthly giving allowance, not from your own wallet.')
    points_total = fields.Integer('Total Points', compute='_compute_points_total', store=True)
    sender_budget_left = fields.Integer('Points Left to Give', compute='_compute_sender_budget_left',
                                        help='What remains of your monthly giving allowance.')

    @api.depends('points', 'receiver_ids')
    def _compute_points_total(self):
        for recognition in self:
            recognition.points_total = recognition.points * len(recognition.receiver_ids)

    @api.depends_context('uid')
    def _compute_sender_budget_left(self):
        self.sender_budget_left = self.env.user.okr_give_budget_left

    @api.constrains('points')
    def _check_points(self):
        maximum = self.env['okr.scale.point.transaction']._get_reward_param('max_points_per_recognition')
        for recognition in self:
            if recognition.points < 0:
                raise ValidationError(_('The points of a recognition cannot be negative.'))
            if recognition.points > maximum:
                raise ValidationError(_('You can give at most %s points per person with a recognition.', maximum))

    @api.model
    def _okr_points_given(self, users):
        """Points given by ``users`` with recognitions sent this month: ``{user_id: points}``."""
        if not users:
            return {}
        data = self.sudo()._read_group(
            [('sender_id', 'in', users.ids), ('create_date', '>=', month_start(self))],
            ['sender_id'], ['points_total:sum'])
        return {user.id: total for user, total in data}

    @api.model_create_multi
    def create(self, vals_list):
        recognitions = super().create(vals_list)
        with_points = recognitions.filtered('points')
        if with_points:
            with_points._okr_check_budget()
            with_points._okr_grant_points()
        return recognitions

    def _okr_check_budget(self):
        allowance = self.env['okr.scale.point.transaction']._get_reward_param('monthly_allowance')
        given = self._okr_points_given(self.sender_id)
        for sender in self.sender_id:
            if given.get(sender.id, 0) > allowance:
                new = sum(self.filtered(lambda r: r.sender_id == sender).mapped('points_total'))
                raise ValidationError(_(
                    'Your monthly allowance is %(allowance)s points: you can still give %(left)s points '
                    'this month but this recognition needs %(needed)s.',
                    allowance=allowance, left=max(allowance - given[sender.id] + new, 0), needed=new))

    def _okr_grant_points(self):
        Transaction = self.env['okr.scale.point.transaction']
        for recognition in self:
            Transaction._grant(recognition.receiver_ids, recognition.points, 'recognition',
                               _('Recognition from %s', recognition.sender_id.name), source=recognition)

    def write(self, vals):
        if not self.env.su and {'points', 'receiver_ids'} & set(vals) \
                and any(recognition.points for recognition in self):
            raise UserError(_('The points and receivers of a recognition cannot be changed once sent.'))
        if 'points' in vals and not self.env.su:
            raise UserError(_('Points can only be given when the recognition is sent.'))
        return super().write(vals)

    def unlink(self):
        with_points = self.filtered('points')
        if with_points and not self._okr_is_admin():
            raise UserError(_('A recognition that gave points cannot be deleted. Ask an OKR administrator.'))
        Transaction = self.env['okr.scale.point.transaction']
        for recognition in with_points:
            Transaction._grant(recognition.receiver_ids, -recognition.points, 'manual',
                               _('Correction: recognition from %s deleted', recognition.sender_id.name),
                               company=recognition.company_id)
        return super().unlink()
