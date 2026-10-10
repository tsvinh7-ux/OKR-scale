from datetime import timedelta

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class OkrConversation(models.Model):
    _name = 'okr.scale.conversation'
    _description = 'OKR Conversation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(required=True, tracking=True, compute='_compute_name', store=True, readonly=False,
                       precompute=True)
    manager_id = fields.Many2one('res.users', 'Manager', required=True, index=True, tracking=True,
                                 default=lambda self: self.env.user, domain=[('share', '=', False)])
    employee_user_id = fields.Many2one('res.users', 'Employee', required=True, index=True, tracking=True,
                                       domain=[('share', '=', False)])
    objective_ids = fields.Many2many('okr.scale.objective', string='Objectives',
                                     help='Objectives discussed during the conversation.')
    date = fields.Datetime(required=True, tracking=True,
                           default=lambda self: fields.Datetime.now().replace(minute=0, second=0) + timedelta(days=1))
    duration = fields.Float(default=0.5, help='Duration in hours.')
    agenda = fields.Html(default=lambda self: self._default_agenda())
    notes = fields.Html()
    action_items = fields.Html('Action Items')
    state = fields.Selection([
        ('planned', 'Planned'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], default='planned', required=True, tracking=True, index=True)
    calendar_event_id = fields.Many2one('calendar.event', 'Meeting', readonly=True, copy=False,
                                        ondelete='set null')
    company_id = fields.Many2one('res.company', required=True, index=True, default=lambda self: self.env.company)

    @api.model
    def _default_agenda(self):
        questions = [
            (_('Progress on OKRs'), _('Where do you stand on your key results since our last talk?')),
            (_('Blockers'), _('What is slowing you down or keeping you from reaching your targets?')),
            (_('Support needed'), _('What can I or the team do to help you?')),
            (_('Career and development'), _('What would you like to learn or grow into next?')),
        ]
        return Markup('').join(Markup('<h3>%s</h3><p>%s</p>') % question for question in questions)

    @api.depends('manager_id', 'employee_user_id')
    def _compute_name(self):
        for conversation in self:
            if not conversation.name and conversation.employee_user_id:
                conversation.name = _('1:1 %(manager)s / %(employee)s',
                                      manager=conversation.manager_id.name,
                                      employee=conversation.employee_user_id.name)

    @api.constrains('manager_id', 'employee_user_id')
    def _check_participants(self):
        for conversation in self:
            if conversation.manager_id == conversation.employee_user_id:
                raise ValidationError(_('A conversation needs two different participants.'))

    @api.constrains('duration')
    def _check_duration(self):
        if any(conversation.duration < 0 for conversation in self):
            raise ValidationError(_('The duration cannot be negative.'))

    def write(self, vals):
        res = super().write(vals)
        if {'date', 'duration', 'name'} & set(vals):
            for conversation in self.filtered('calendar_event_id'):
                conversation.calendar_event_id.sudo().write(conversation._prepare_event_times())
        return res

    def _prepare_event_times(self):
        self.ensure_one()
        return {
            'name': self.name,
            'start': self.date,
            'stop': self.date + timedelta(hours=self.duration or 0.5),
        }

    def action_schedule_meeting(self):
        """Create (once) the calendar meeting of the conversation with both participants."""
        self.ensure_one()
        if not self.calendar_event_id:
            event = self.env['calendar.event'].create(dict(
                self._prepare_event_times(),
                partner_ids=[(6, 0, (self.manager_id | self.employee_user_id).partner_id.ids)],
                user_id=self.manager_id.id,
                description=self.agenda,
                res_model_id=self.env['ir.model']._get_id(self._name),
                res_id=self.id,
            ))
            self.calendar_event_id = event
            self.message_post(body=_('Meeting scheduled in the calendar.'))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'calendar.event',
            'res_id': self.calendar_event_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_plan(self):
        self.write({'state': 'planned'})
