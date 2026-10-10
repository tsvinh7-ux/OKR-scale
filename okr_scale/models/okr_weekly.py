from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .okr_common import CONFIDENCE


class OkrWeekly(models.Model):
    """Weekly check-in of a person: how the week went and the plan for the next one.

    The key result check-ins submitted at the same time are attached to it, so a
    manager reads the whole week of a team member at once.
    """
    _name = 'okr.scale.weekly'
    _description = 'OKR Weekly Check-in'
    _inherit = ['mail.thread']
    _order = 'week_start desc, id desc'
    _rec_name = 'week_start'
    _mail_post_access = 'read'

    user_id = fields.Many2one('res.users', 'Employee', required=True, index=True, readonly=True,
                              default=lambda self: self.env.user)
    employee_id = fields.Many2one('hr.employee', 'Employee Profile', compute='_compute_employee_id', store=True,
                                  index=True)
    department_id = fields.Many2one('hr.department', compute='_compute_employee_id', store=True, index=True)
    week_start = fields.Date('Week', required=True, index=True, readonly=True,
                             help='Monday of the week of this check-in.')
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    summary = fields.Text('How did the week go?')
    next_plan = fields.Text('Plan for next week')
    help_needed = fields.Text('Help needed')
    mood = fields.Selection([
        ('great', 'Great'),
        ('good', 'Good'),
        ('neutral', 'Neutral'),
        ('struggling', 'Struggling'),
    ], default='good')
    confidence = fields.Float(compute='_compute_stats', store=True, group_operator='avg')
    checkin_ids = fields.One2many('okr.scale.checkin', 'weekly_id', 'Key Result Check-ins')
    checkin_count = fields.Integer(compute='_compute_stats', store=True)
    has_blockers = fields.Boolean(compute='_compute_stats', store=True)
    manager_comment = fields.Text()

    _sql_constraints = [
        ('user_week_uniq', 'unique (user_id, week_start)', 'Only one weekly check-in per person and week.'),
    ]

    @api.depends('user_id')
    def _compute_employee_id(self):
        for weekly in self:
            employee = weekly.user_id.sudo().employee_id
            weekly.employee_id = employee
            weekly.department_id = employee.department_id

    @api.depends('checkin_ids.confidence', 'checkin_ids.blockers', 'help_needed')
    def _compute_stats(self):
        for weekly in self:
            confidences = [int(c.confidence) for c in weekly.checkin_ids if c.confidence]
            weekly.confidence = sum(confidences) / len(confidences) if confidences else 0.0
            weekly.checkin_count = len(weekly.checkin_ids)
            weekly.has_blockers = bool(weekly.help_needed) or any(weekly.checkin_ids.mapped('blockers'))

    @api.model
    def _week_start(self, day=None):
        day = day or fields.Date.context_today(self)
        return day - timedelta(days=day.weekday())

    # ------------------------------------------------------------------
    # API of the weekly check-in screen
    # ------------------------------------------------------------------
    @api.model
    def get_my_week(self):
        """Key results to update this week and the current weekly check-in, if any."""
        user = self.env.user
        week = self._week_start()
        weekly = self.search([('user_id', '=', user.id), ('week_start', '=', week)], limit=1)
        krs = self.env['okr.scale.key.result'].search(
            [('owner_id', '=', user.id), ('objective_state', '=', 'running')], order='objective_id, sequence')
        done = {c.key_result_id.id: c for c in weekly.checkin_ids}
        cycle = krs[:1].cycle_id or self.env['okr.scale.cycle'].get_current_cycle()
        status_labels = dict(self.env['okr.scale.key.result']._fields['status']._description_selection(self.env))
        weekday_labels = dict(self.env['okr.scale.cycle']._fields['checkin_weekday']._description_selection(self.env))
        return {
            'week_start': fields.Date.to_string(week),
            'week_end': fields.Date.to_string(week + timedelta(days=6)),
            'checkin_day': weekday_labels.get(cycle.checkin_weekday) if cycle else False,
            'weekly': {
                'id': weekly.id,
                'summary': weekly.summary or '',
                'next_plan': weekly.next_plan or '',
                'help_needed': weekly.help_needed or '',
                'mood': weekly.mood or 'good',
                'manager_comment': weekly.manager_comment or '',
            } if weekly else False,
            'key_results': [{
                'id': kr.id,
                'name': kr.name,
                'objective': kr.objective_id.name,
                'manual': kr.progress_method == 'manual',
                'boolean': kr.metric_type == 'boolean',
                'unit': kr.unit or '',
                'start': kr.start_value,
                'target': kr.target_value,
                'current': round(kr.current_value, 2),
                'status_label': status_labels.get(kr.status, ''),
                'progress': round(kr.progress, 1),
                'confidence': kr.confidence or '7',
                'status': kr.status,
                'done': kr.id in done,
                'last_checkin_date': fields.Date.to_string(kr.last_checkin_date) if kr.last_checkin_date else False,
            } for kr in krs],
        }

    @api.model
    def submit_my_week(self, values):
        """Create the check-ins of the week in one go.

        ``values``: {'summary', 'next_plan', 'help_needed', 'mood',
        'lines': [{'key_result_id', 'new_value', 'confidence', 'note', 'blockers'}]}
        """
        user = self.env.user
        week = self._week_start()
        weekly = self.search([('user_id', '=', user.id), ('week_start', '=', week)], limit=1)
        vals = {k: values.get(k) or False for k in ('summary', 'next_plan', 'help_needed')}
        vals['mood'] = values.get('mood') if values.get('mood') in ('great', 'good', 'neutral', 'struggling') else 'good'
        if not values.get('next_plan'):
            raise UserError(_('Tell your team the plan for next week before submitting.'))
        if weekly:
            weekly.write(vals)
        else:
            weekly = self.create(dict(vals, user_id=user.id, week_start=week))
        Checkin = self.env['okr.scale.checkin']
        already = set(weekly.checkin_ids.key_result_id.ids)
        for line in values.get('lines', []):
            kr = self.env['okr.scale.key.result'].browse(int(line['key_result_id'])).exists()
            if not kr or kr.id in already:
                continue
            confidence = str(line.get('confidence') or '7')
            if confidence not in dict(CONFIDENCE):
                raise UserError(_('The confidence must be between 1 and 10.'))
            checkin = Checkin.create({
                'key_result_id': kr.id,
                'new_value': float(line.get('new_value') or 0.0) if kr.progress_method == 'manual' else kr.current_value,
                'confidence': confidence,
                'achievements': line.get('note') or values.get('summary') or False,
                'blockers': line.get('blockers') or False,
                'next_steps': values.get('next_plan') or False,
                'mood': vals['mood'],
                'weekly_id': weekly.id,
            })
            checkin.action_submit()
        weekly._notify_managers()
        return weekly.id

    def _notify_managers(self):
        """Tell the direct manager in Odoo that the weekly check-in is in."""
        for weekly in self:
            employee = weekly.employee_id.sudo()
            manager = employee.parent_id.user_id or employee.department_id.manager_id.user_id
            if manager and manager != weekly.user_id:
                weekly.sudo().message_subscribe(partner_ids=manager.partner_id.ids)

    # ------------------------------------------------------------------
    # Team board
    # ------------------------------------------------------------------
    @api.model
    def get_team_week(self, week_start=False, department_id=False):
        """Weekly check-in status of the people the current user manages (or of everyone
        for OKR administrators), read with the access rights of the user."""
        week = fields.Date.to_date(week_start) if week_start else self._week_start()
        Employee = self.env['hr.employee'].sudo()
        is_admin = self.env.user.has_group('okr_scale.group_okr_admin')
        domain = [('user_id', '!=', False), ('user_id.share', '=', False)]
        if not is_admin:
            domain.append(('okr_manager_user_ids', 'in', [self.env.uid]))
        if department_id:
            domain.append(('department_id', 'child_of', department_id))
        employees = Employee.search(domain, order='department_id, name')
        weeklies = self.search([('user_id', 'in', employees.user_id.ids), ('week_start', '=', week)])
        by_user = {w.user_id.id: w for w in weeklies}
        KeyResult = self.env['okr.scale.key.result']
        rows = []
        for employee in employees:
            user = employee.user_id
            krs = KeyResult.search([('owner_id', '=', user.id), ('objective_state', '=', 'running')])
            weekly = by_user.get(user.id)
            risky = krs.filtered(lambda kr: kr.status in ('at_risk', 'off_track'))
            rows.append({
                'user_id': user.id,
                'name': employee.name,
                'job': employee.job_title or '',
                'department': employee.department_id.name or '',
                'key_results': len(krs),
                'progress': round(sum(krs.mapped('progress')) / len(krs), 1) if krs else 0.0,
                'risky': len(risky),
                'risky_names': risky[:3].mapped('name'),
                'submitted': bool(weekly),
                'weekly_id': weekly.id if weekly else False,
                'confidence': round(weekly.confidence, 1) if weekly else 0,
                'mood': weekly.mood if weekly else False,
                'summary': weekly.summary or '' if weekly else '',
                'next_plan': weekly.next_plan or '' if weekly else '',
                'help_needed': weekly.help_needed or '' if weekly else '',
                'blockers': [c.blockers for c in weekly.checkin_ids if c.blockers] if weekly else [],
            })
        with_krs = [r for r in rows if r['key_results']]
        submitted = [r for r in with_krs if r['submitted']]
        return {
            'week_start': fields.Date.to_string(week),
            'week_end': fields.Date.to_string(week + timedelta(days=6)),
            'previous_week': fields.Date.to_string(week - timedelta(days=7)),
            'next_week': fields.Date.to_string(week + timedelta(days=7)),
            'is_current_week': week == self._week_start(),
            'departments': [{'id': d.id, 'name': d.display_name} for d in employees.department_id],
            'department_id': department_id,
            'stats': {
                'people': len(with_krs),
                'submitted': len(submitted),
                'missing': len(with_krs) - len(submitted),
                'rate': round(len(submitted) * 100.0 / len(with_krs), 1) if with_krs else 0.0,
                'blocked': len([r for r in submitted if r['blockers'] or r['help_needed']]),
                'risky': sum(r['risky'] for r in rows),
            },
            'rows': rows,
            'one_on_one_action': self._one_on_one_action(),
        }

    @api.model
    def _one_on_one_action(self):
        """xmlid of the 1:1 action when a CFR module provides it."""
        return False

    @api.model
    def remind_user(self, user_id):
        """Manager nudge from the team board: notification in Odoo and by e-mail."""
        user = self.env['res.users'].browse(user_id).exists()
        if not user:
            return False
        krs = self.env['okr.scale.key.result'].sudo().search(
            [('owner_id', '=', user.id), ('objective_state', '=', 'running')])
        user._okr_notify_checkin_due(krs, author=self.env.user)
        return True

