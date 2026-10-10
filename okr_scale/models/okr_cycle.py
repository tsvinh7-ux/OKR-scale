from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

CHECKIN_DAYS = {'weekly': 7, 'biweekly': 14, 'monthly': 30}


class OkrCycle(models.Model):
    _name = 'okr.scale.cycle'
    _description = 'OKR Cycle'
    _inherit = ['mail.thread']
    _order = 'date_start desc, id desc'

    name = fields.Char(required=True, tracking=True)
    cycle_type = fields.Selection([
        ('year', 'Year'),
        ('quarter', 'Quarter'),
        ('custom', 'Custom'),
    ], string='Type', required=True, default='quarter')
    date_start = fields.Date('Start Date', required=True, tracking=True)
    date_end = fields.Date('End Date', required=True, tracking=True)
    parent_id = fields.Many2one('okr.scale.cycle', 'Parent Cycle', index=True, ondelete='restrict',
                                domain="[('cycle_type', '=', 'year')]")
    child_ids = fields.One2many('okr.scale.cycle', 'parent_id', 'Sub Cycles')
    state = fields.Selection([
        ('draft', 'Planning'),
        ('open', 'Running'),
        ('closed', 'Closed'),
    ], default='draft', required=True, tracking=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    checkin_frequency = fields.Selection([
        ('weekly', 'Weekly'),
        ('biweekly', 'Every 2 weeks'),
        ('monthly', 'Monthly'),
    ], default='weekly', required=True,
        help='Key result owners are reminded when no check-in was submitted during this period.')
    require_approval = fields.Boolean(
        default=True, help='Objectives must be approved by a manager before they start running.')
    objective_ids = fields.One2many('okr.scale.objective', 'cycle_id', 'Objectives')
    objective_count = fields.Integer(compute='_compute_objective_stats')
    progress = fields.Float(compute='_compute_objective_stats', string='Average Progress')
    active = fields.Boolean(default=True)

    @api.constrains('date_start', 'date_end', 'parent_id')
    def _check_dates(self):
        for cycle in self:
            if cycle.date_end < cycle.date_start:
                raise ValidationError(_('The end date of cycle %s must be after its start date.', cycle.name))
            parent = cycle.parent_id
            if parent and (cycle.date_start < parent.date_start or cycle.date_end > parent.date_end):
                raise ValidationError(_('Cycle %s must be inside its parent cycle %s.', cycle.name, parent.name))

    @api.depends('objective_ids.progress')
    def _compute_objective_stats(self):
        data = self.env['okr.scale.objective']._read_group(
            [('cycle_id', 'in', self.ids), ('state', 'not in', ('draft', 'cancelled'))],
            ['cycle_id'], ['__count', 'progress:avg'])
        stats = {cycle.id: (count, avg) for cycle, count, avg in data}
        for cycle in self:
            cycle.objective_count, cycle.progress = stats.get(cycle.id, (0, 0.0))

    def get_checkin_days(self):
        self.ensure_one()
        return CHECKIN_DAYS[self.checkin_frequency]

    def action_open(self):
        self.write({'state': 'open'})

    def action_close(self):
        """Close the cycle and grade every running objective with its current progress."""
        for cycle in self:
            running = cycle.objective_ids.filtered(lambda o: o.state == 'running')
            running.action_done()
        self.write({'state': 'closed'})

    def action_reopen(self):
        self.write({'state': 'open'})

    def action_view_objectives(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('okr_scale.okr_objective_action')
        action['domain'] = [('cycle_id', '=', self.id)]
        action['context'] = {'default_cycle_id': self.id}
        return action

    @api.model
    def get_current_cycle(self):
        """Most relevant running cycle: the shortest open one containing today."""
        today = fields.Date.context_today(self)
        cycles = self.search([('state', '=', 'open'), ('date_start', '<=', today), ('date_end', '>=', today)])
        if not cycles:
            cycles = self.search([('state', '=', 'open')], limit=1)
        return cycles.sorted(lambda c: (c.date_end - c.date_start).days)[:1]
