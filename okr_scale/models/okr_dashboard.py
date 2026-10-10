from datetime import timedelta

from odoo import _, api, fields, models

STATUS_ORDER = ['on_track', 'at_risk', 'off_track', 'achieved']


class OkrDashboard(models.AbstractModel):
    """Data provider of the overall OKR dashboard.

    Everything is read with the access rights of the current user, so each
    person sees the figures of the OKRs they are allowed to see. Other modules
    extend ``_get_extra_kpis`` and ``_get_extra_sections``.
    """
    _name = 'okr.scale.dashboard'
    _description = 'OKR Dashboard'

    @api.model
    def get_dashboard_data(self, cycle_id=False, department_id=False):
        Cycle = self.env['okr.scale.cycle']
        cycle = Cycle.browse(cycle_id) if cycle_id else Cycle.get_current_cycle()
        domain = [('state', 'in', ('running', 'done'))]
        if cycle:
            domain.append(('cycle_id', '=', cycle.id))
        if department_id:
            domain.append(('department_id', 'child_of', department_id))
        objectives = self.env['okr.scale.objective'].search(domain)
        krs = objectives.key_result_ids
        today = fields.Date.context_today(self)
        week_ago = today - timedelta(days=7)
        checkins = self.env['okr.scale.checkin'].search([
            ('objective_id', 'in', objectives.ids), ('state', '!=', 'draft')], order='date desc, id desc')
        recent_kr_ids = set(checkins.filtered(lambda c: c.date >= week_ago).key_result_id.ids)
        running_krs = krs.filtered(lambda kr: kr.objective_state == 'running')

        status_labels = dict(self.env['okr.scale.objective']._fields['status']._description_selection(self.env))
        level_labels = dict(self.env['okr.scale.objective']._fields['level']._description_selection(self.env))

        def avg(values):
            values = list(values)
            return round(sum(values) / len(values), 1) if values else 0.0

        by_department = {}
        for objective in objectives.filtered('department_id'):
            by_department.setdefault(objective.department_id, self.env['okr.scale.objective'])
            by_department[objective.department_id] |= objective

        return {
            'cycle': {'id': cycle.id, 'name': cycle.display_name} if cycle else False,
            'cycles': [{'id': c.id, 'name': c.display_name} for c in Cycle.search([('state', '!=', 'draft')])],
            'departments': [{'id': d.id, 'name': d.display_name}
                            for d in self.env['hr.department'].search([])],
            'department_id': department_id,
            'expected_progress': round(objectives[:1].expected_progress, 1) if objectives else 0.0,
            'kpis': [
                {'key': 'objectives', 'label': _('Objectives'), 'value': len(objectives)},
                {'key': 'key_results', 'label': _('Key Results'), 'value': len(krs)},
                {'key': 'progress', 'label': _('Average Progress'), 'value': avg(objectives.mapped('progress')),
                 'suffix': '%'},
                {'key': 'on_track', 'label': _('On Track'),
                 'value': avg([100.0 if o.status in ('on_track', 'achieved') else 0.0 for o in objectives]),
                 'suffix': '%'},
                {'key': 'checkin_rate', 'label': _('Checked-in this week'),
                 'value': round(len(recent_kr_ids & set(running_krs.ids)) * 100.0 / len(running_krs), 1)
                 if running_krs else 0.0, 'suffix': '%'},
            ] + self._get_extra_kpis(objectives, cycle),
            'status': [{
                'key': status,
                'label': status_labels[status],
                'count': len(objectives.filtered(lambda o, s=status: o.status == s)),
            } for status in STATUS_ORDER],
            'levels': [{
                'key': level,
                'label': level_labels[level],
                'count': len(objectives.filtered(lambda o, lv=level: o.level == lv)),
                'progress': avg(objectives.filtered(lambda o, lv=level: o.level == lv).mapped('progress')),
            } for level in ('company', 'department', 'individual')],
            'departments_progress': sorted([{
                'id': department.id,
                'name': department.display_name,
                'count': len(objs),
                'progress': avg(objs.mapped('progress')),
                'at_risk': len(objs.filtered(lambda o: o.status in ('at_risk', 'off_track'))),
            } for department, objs in by_department.items()], key=lambda d: -d['progress']),
            'company_objectives': [{
                'id': o.id,
                'name': o.name,
                'owner': o.owner_id.name,
                'progress': round(o.progress, 1),
                'status': o.status,
                'status_label': status_labels.get(o.status, ''),
            } for o in objectives.filtered(lambda o: o.level == 'company')],
            'risky_key_results': [{
                'id': kr.id,
                'name': kr.name,
                'objective': kr.objective_id.name,
                'owner': kr.owner_id.name or '',
                'progress': round(kr.progress, 1),
                'confidence': kr.confidence,
                'status': kr.status,
                'status_label': status_labels.get(kr.status, ''),
            } for kr in running_krs.filtered(lambda kr: kr.status in ('at_risk', 'off_track'))
                .sorted(lambda kr: kr.progress)[:10]],
            'recent_checkins': [{
                'id': c.id,
                'user': c.user_id.name,
                'user_id': c.user_id.id,
                'key_result': c.key_result_id.name,
                'date': fields.Date.to_string(c.date),
                'progress_before': round(c.progress_before, 1),
                'progress_after': round(c.progress_after, 1),
                'confidence': c.confidence,
            } for c in checkins[:10]],
            'extra_sections': self._get_extra_sections(objectives, cycle),
            'issues': self._get_issues(objectives, cycle),
        }

    @api.model
    def _get_issues(self, objectives, cycle):
        """Everything needing attention, most severe first. Each issue opens the records."""
        today = fields.Date.context_today(self)
        running = objectives.filtered(lambda o: o.state == 'running')
        krs = running.key_result_ids
        Checkin = self.env['okr.scale.checkin']
        blocked = Checkin.search([('objective_id', 'in', running.ids), ('state', '!=', 'draft'),
                                  ('date', '>=', today - timedelta(days=7)), ('blockers', '!=', False)])
        stale = krs.filtered(lambda kr: kr.progress_method == 'manual' and (
            not kr.last_checkin_date or (today - kr.last_checkin_date).days > 14))
        unaligned = running.filtered(lambda o: o.level != 'company' and not o.parent_id)
        team_domain = self.env['okr.scale.objective']._my_team_domain()
        to_approve = self.env['okr.scale.objective'].search(team_domain + [('state', '=', 'to_approve')]) \
            if self.env.user.has_group('okr_scale.group_okr_manager') else self.env['okr.scale.objective']
        issues = [
            ('off_track', _('Key results off track'), 'danger', 'fa-exclamation-circle', krs.filtered(lambda k: k.status == 'off_track')),
            ('checkin_due', _('Check-ins missing this week'), 'danger', 'fa-calendar-times-o', krs.filtered('checkin_due')),
            ('blockers', _('Blockers reported (7 days)'), 'danger', 'fa-hand-paper-o', blocked),
            ('at_risk', _('Key results at risk'), 'warning', 'fa-exclamation-triangle', krs.filtered(lambda k: k.status == 'at_risk')),
            ('low_confidence', _('Low confidence (≤ 4/10)'), 'warning', 'fa-heartbeat',
             krs.filtered(lambda k: k.confidence and int(k.confidence) <= 4)),
            ('stale', _('No update for 2 weeks'), 'warning', 'fa-hourglass-half', stale),
            ('to_approve', _('Objectives waiting for approval'), 'info', 'fa-check-square-o', to_approve),
            ('unaligned', _('Objectives not aligned'), 'info', 'fa-chain-broken', unaligned),
        ]
        return [{
            'key': key,
            'label': label,
            'severity': severity,
            'icon': icon,
            'count': len(records),
            'model': records._name,
            'ids': records.ids,
        } for key, label, severity, icon, records in issues]

    @api.model
    def _get_extra_kpis(self, objectives, cycle):
        """Return a list of ``{'key', 'label', 'value', 'suffix'}`` dicts."""
        return []

    @api.model
    def _get_extra_sections(self, objectives, cycle):
        """Return a list of ``{'key', 'title', 'columns': [...], 'rows': [[...]]}`` tables."""
        return []

    @api.model
    def _get_extra_rankings(self, cycle, objectives):
        """Return extra leaderboards shown on the Rankings page.

        Each board is ``{'key', 'title', 'icon' (fa class), 'unit', 'rows': [
        {'user_id', 'name', 'subtitle', 'value'}]}`` with rows sorted best first.
        """
        return []

    @api.model
    def _get_weekly_digest(self):
        """Content of the weekly digest of the current user (read with their rights)."""
        user = self.env.user
        status_labels = dict(self.env['okr.scale.key.result']._fields['status']._description_selection(self.env))
        krs = self.env['okr.scale.key.result'].search(
            [('owner_id', '=', user.id), ('objective_state', '=', 'running')], order='progress')
        team = False
        if user.has_group('okr_scale.group_okr_manager'):
            Weekly = self.env['okr.scale.weekly']
            last_week = Weekly._week_start() - timedelta(days=7)
            board = Weekly.get_team_week(fields.Date.to_string(last_week))
            if board['stats']['people']:
                team = {
                    'stats': board['stats'],
                    'missing': [r['name'] for r in board['rows'] if r['key_results'] and not r['submitted']],
                    'blocked': [r for r in board['rows'] if r['blockers'] or r['help_needed']],
                    'risky': [r for r in board['rows'] if r['risky']],
                }
        return {
            'key_results': [{
                'name': kr.name,
                'objective': kr.objective_id.name,
                'progress': round(kr.progress),
                'status': kr.status,
                'status_label': status_labels.get(kr.status, ''),
                'due': kr.checkin_due,
            } for kr in krs],
            'team': team,
        }
