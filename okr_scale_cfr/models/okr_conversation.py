from datetime import timedelta

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

CADENCE_DAYS = {'weekly': 7, 'biweekly': 14, 'monthly': 30}


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
    cadence = fields.Selection([
        ('none', 'One-off'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Every 2 weeks'),
        ('monthly', 'Monthly'),
    ], default='biweekly', required=True,
        help='When the conversation is done, the next one is planned automatically.')
    previous_id = fields.Many2one('okr.scale.conversation', 'Previous 1:1', readonly=True, copy=False,
                                  ondelete='set null')
    checkin_id = fields.Many2one('okr.scale.checkin', 'From Check-in', readonly=True, copy=False,
                                 ondelete='set null', help='Check-in that triggered this conversation.')
    since_date = fields.Date(compute='_compute_since_date',
                             help='Check-ins submitted since this date are reviewed in this conversation.')
    key_result_ids = fields.Many2many('okr.scale.key.result', compute='_compute_okr_snapshot',
                                      string='Key Results of the Employee')
    checkin_ids = fields.Many2many('okr.scale.checkin', compute='_compute_okr_snapshot',
                                   string='Check-ins since last 1:1')
    checkin_count = fields.Integer(compute='_compute_okr_snapshot')

    @api.model
    def _default_agenda(self):
        questions = [
            (_('Progress on OKRs'), _('Where do you stand on your key results since our last talk?')),
            (_('Blockers'), _('What is slowing you down or keeping you from reaching your targets?')),
            (_('Support needed'), _('What can I or the team do to help you?')),
            (_('Career and development'), _('What would you like to learn or grow into next?')),
        ]
        return Markup('').join(Markup('<h3>%s</h3><p>%s</p>') % question for question in questions)

    @api.depends('previous_id.date', 'date', 'cadence')
    def _compute_since_date(self):
        for conversation in self:
            if conversation.previous_id:
                conversation.since_date = conversation.previous_id.date.date()
            else:
                days = CADENCE_DAYS.get(conversation.cadence, 14)
                conversation.since_date = (conversation.date or fields.Datetime.now()).date() - timedelta(days=days)

    @api.depends('employee_user_id', 'since_date', 'date', 'objective_ids')
    def _compute_okr_snapshot(self):
        """Running key results of the employee and their recent check-ins, read with the
        access rights of the viewer (managers see their team through the HR hierarchy)."""
        KeyResult = self.env['okr.scale.key.result']
        Checkin = self.env['okr.scale.checkin']
        for conversation in self:
            user = conversation.employee_user_id
            if not user:
                conversation.key_result_ids = conversation.checkin_ids = False
                conversation.checkin_count = 0
                continue
            krs = KeyResult.search([
                '|', ('owner_id', '=', user.id), ('objective_id', 'in', conversation.objective_ids.ids),
                ('objective_state', '=', 'running')])
            end = max(conversation.date or fields.Datetime.now(), fields.Datetime.now()).date()
            checkins = Checkin.search([
                ('state', '!=', 'draft'), ('date', '>=', conversation.since_date), ('date', '<=', end),
                '|', ('user_id', '=', user.id), ('key_result_id', 'in', krs.ids)])
            conversation.key_result_ids = krs
            conversation.checkin_ids = checkins
            conversation.checkin_count = len(checkins)

    @api.onchange('employee_user_id')
    def _onchange_employee_user_id(self):
        if self.employee_user_id and not self.objective_ids:
            self.objective_ids = self.env['okr.scale.objective'].search([
                ('state', '=', 'running'),
                '|', ('owner_id', '=', self.employee_user_id.id),
                ('key_result_ids.owner_id', '=', self.employee_user_id.id)])

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
        for conversation in self.filtered(lambda c: c.cadence != 'none'):
            conversation._plan_next()

    def _plan_next(self):
        """Plan the next conversation of a recurring 1:1, once."""
        self.ensure_one()
        if self.search_count([('previous_id', '=', self.id)]):
            return self.browse()
        next_conversation = self.copy({
            'date': self.date + timedelta(days=CADENCE_DAYS[self.cadence]),
            'previous_id': self.id,
            'state': 'planned',
            'notes': False,
            'name': self.name,
        })
        self.message_post(body=Markup(_('Next 1:1 planned: %s')) % next_conversation._get_html_link())
        return next_conversation

    @api.model
    def _prepare_from_checkin(self, checkin):
        return {
            'default_manager_id': self.env.uid,
            'default_employee_user_id': checkin.user_id.id,
            'default_objective_ids': [(6, 0, checkin.objective_id.ids)],
            'default_checkin_id': checkin.id,
            'default_cadence': 'none',
            'default_name': _('1:1 about %s', checkin.key_result_id.name),
        }

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_plan(self):
        self.write({'state': 'planned'})
