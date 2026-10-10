from collections import defaultdict

from odoo import _, api, fields, models

# Weight of the progress in the people score, the rest is the check-in discipline.
PROGRESS_WEIGHT = 0.7


class OkrDashboardRanking(models.AbstractModel):
    _inherit = 'okr.scale.dashboard'

    @api.model
    def _ranking_scope(self, cycle, department_id):
        """Objectives used by rankings, read with sudo so that every viewer sees the
        same scores. Only figures and public names leave this method."""
        domain = [('state', 'in', ('running', 'done')), ('company_id', 'in', self.env.companies.ids)]
        if cycle:
            domain.append(('cycle_id', '=', cycle.id))
        if department_id:
            domain.append(('department_id', 'child_of', department_id))
        return self.env['okr.scale.objective'].sudo().search(domain)

    @api.model
    def _checkin_discipline(self, krs, today):
        """Share of the expected check-ins actually submitted, per key result."""
        submitted = defaultdict(int)
        for checkin in krs.checkin_ids.filtered(lambda c: c.state != 'draft'):
            submitted[checkin.key_result_id.id] += 1
        rates = {}
        for kr in krs:
            cycle = kr.cycle_id
            start = kr.objective_id.approval_date.date() if kr.objective_id.approval_date else cycle.date_start
            start = max(start, cycle.date_start)
            end = min(today, cycle.date_end)
            elapsed = (end - start).days
            expected = max(1, elapsed // cycle.get_checkin_days()) if elapsed >= 0 else 0
            rates[kr.id] = min(1.0, submitted[kr.id] / expected) if expected else 1.0
        return rates

    @api.model
    def _objective_row(self, objective, rank):
        return {
            'rank': rank,
            'id': objective.id,
            'name': objective.name,
            'level': objective.level,
            'owner': objective.owner_id.name,
            'user_id': objective.owner_id.id,
            'department': objective.department_id.name or '',
            'progress': round(objective.progress, 1),
            'confidence': round(objective.confidence, 1),
            'status': objective.status,
        }

    @api.model
    def get_ranking_data(self, cycle_id=False, department_id=False):
        Cycle = self.env['okr.scale.cycle']
        cycle = Cycle.browse(cycle_id) if cycle_id else Cycle.get_current_cycle()
        objectives = self._ranking_scope(cycle, department_id)
        krs = objectives.key_result_ids
        today = fields.Date.context_today(self)
        discipline = self._checkin_discipline(krs, today)

        # People: key results they own
        by_user = defaultdict(lambda: self.env['okr.scale.key.result'].sudo())
        for kr in krs.filtered(lambda k: k.owner_id and not k.owner_id.share):
            by_user[kr.owner_id] |= kr
        people = []
        for user, user_krs in by_user.items():
            progress = sum(user_krs.mapped('progress')) / len(user_krs)
            rate = sum(discipline[kr.id] for kr in user_krs) / len(user_krs) * 100
            people.append({
                'user_id': user.id,
                'name': user.name,
                'department': user.employee_id.department_id.name or '',
                'key_results': len(user_krs),
                'achieved': len(user_krs.filtered('achieved')),
                'progress': round(progress, 1),
                'checkin_rate': round(rate, 1),
                'score': round(PROGRESS_WEIGHT * progress + (1 - PROGRESS_WEIGHT) * rate, 1),
            })
        people.sort(key=lambda p: (-p['score'], -p['progress'], p['name']))
        for rank, person in enumerate(people, 1):
            person['rank'] = rank
        me = next((p for p in people if p['user_id'] == self.env.uid), False)

        # Departments
        by_department = defaultdict(lambda: self.env['okr.scale.objective'].sudo())
        for objective in objectives.filtered('department_id'):
            by_department[objective.department_id] |= objective
        departments = []
        for department, objs in by_department.items():
            dep_krs = objs.key_result_ids
            rate = sum(discipline[kr.id] for kr in dep_krs) / len(dep_krs) * 100 if dep_krs else 0.0
            progress = sum(objs.mapped('progress')) / len(objs)
            departments.append({
                'id': department.id,
                'name': department.name,
                'manager': department.manager_id.name or '',
                'objectives': len(objs),
                'progress': round(progress, 1),
                'checkin_rate': round(rate, 1),
                'score': round(PROGRESS_WEIGHT * progress + (1 - PROGRESS_WEIGHT) * rate, 1),
            })
        departments.sort(key=lambda d: (-d['score'], d['name']))
        for rank, department in enumerate(departments, 1):
            department['rank'] = rank

        # Best objectives per level and best key results: public ones only, names are shown.
        public = objectives.filtered(lambda o: o.visibility == 'public')
        level_labels = dict(self.env['okr.scale.objective']._fields['level']._description_selection(self.env))
        best_objectives = []
        for level in ('company', 'department', 'individual'):
            ranked = public.filtered(lambda o, lv=level: o.level == lv).sorted(
                lambda o: (-o.progress, -o.confidence, o.id))[:5]
            best_objectives.append({
                'level': level,
                'label': level_labels[level],
                'rows': [self._objective_row(o, rank) for rank, o in enumerate(ranked, 1)],
            })
        best_krs = public.key_result_ids.sorted(
            lambda kr: (-kr.progress, -int(kr.confidence or 0), kr.id))[:10]

        return {
            'cycle': {'id': cycle.id, 'name': cycle.display_name} if cycle else False,
            'cycles': [{'id': c.id, 'name': c.display_name} for c in Cycle.search([('state', '!=', 'draft')])],
            'departments': [{'id': d.id, 'name': d.display_name} for d in self.env['hr.department'].search([])],
            'department_id': department_id,
            'score_help': _('Score = %(p)s%% average progress of owned key results + %(c)s%% check-in discipline',
                            p=int(PROGRESS_WEIGHT * 100), c=int((1 - PROGRESS_WEIGHT) * 100)),
            'people': people[:20],
            'me': me,
            'departments_rank': departments,
            'objectives': best_objectives,
            'key_results': [{
                'rank': rank,
                'id': kr.id,
                'name': kr.name,
                'objective': kr.objective_id.name,
                'owner': kr.owner_id.name or '',
                'user_id': kr.owner_id.id,
                'progress': round(kr.progress, 1),
                'confidence': kr.confidence or '',
                'status': kr.status,
            } for rank, kr in enumerate(best_krs, 1)],
            'extra_boards': self._get_extra_rankings(cycle, objectives),
        }

    # ------------------------------------------------------------------
    # Personal workspace
    # ------------------------------------------------------------------
    @api.model
    def get_my_okr_data(self):
        user = self.env.user
        Objective = self.env['okr.scale.objective']
        cycle = self.env['okr.scale.cycle'].get_current_cycle()
        domain = [('state', 'not in', ('cancelled',)),
                  '|', '|', ('owner_id', '=', user.id), ('employee_id.user_id', '=', user.id),
                  ('key_result_ids.owner_id', '=', user.id)]
        if cycle:
            domain.append(('cycle_id', '=', cycle.id))
        objectives = Objective.search(domain)
        status_labels = dict(Objective._fields['status']._description_selection(self.env))
        state_labels = dict(Objective._fields['state']._description_selection(self.env))
        level_labels = dict(Objective._fields['level']._description_selection(self.env))
        my_krs = self.env['okr.scale.key.result'].search([('owner_id', '=', user.id), ('objective_state', '=', 'running')])
        due = my_krs.filtered('checkin_due')
        is_manager = user.has_group('okr_scale.group_okr_manager')
        team_domain = Objective._my_team_domain()
        ranking = self.get_ranking_data(cycle.id if cycle else False)
        return {
            'user': {'id': user.id, 'name': user.name},
            'cycle': {'id': cycle.id, 'name': cycle.display_name,
                      'date_end': fields.Date.to_string(cycle.date_end),
                      'days_left': max(0, (cycle.date_end - fields.Date.context_today(self)).days),
                      'elapsed': round(objectives[:1].expected_progress, 1) if objectives else 0.0}
            if cycle else False,
            'objectives': [{
                'id': o.id,
                'name': o.name,
                'level': o.level,
                'level_label': level_labels.get(o.level),
                'state': o.state,
                'state_label': state_labels.get(o.state),
                'progress': round(o.progress, 1),
                'status': o.status,
                'status_label': status_labels.get(o.status, ''),
                'key_results': [{
                    'id': kr.id,
                    'name': kr.name,
                    'mine': kr.owner_id == user,
                    'progress': round(kr.progress, 1),
                    'current': kr.current_value,
                    'target': kr.target_value,
                    'unit': kr.unit or '',
                    'manual': kr.progress_method == 'manual',
                    'confidence': kr.confidence or '',
                    'status': kr.status,
                    'due': kr.checkin_due,
                    'running': kr.objective_state == 'running',
                } for kr in o.key_result_ids],
            } for o in objectives],
            'stats': {
                'objectives': len(objectives),
                'key_results': len(my_krs),
                'progress': round(sum(my_krs.mapped('progress')) / len(my_krs), 1) if my_krs else 0.0,
                'due': len(due),
                'rank': ranking['me']['rank'] if ranking['me'] else False,
                'score': ranking['me']['score'] if ranking['me'] else False,
                'ranked': len(ranking['people']),
            },
            'manager': {
                'to_approve': Objective.search_count(team_domain + [('state', '=', 'to_approve')]),
                'to_review': self.env['okr.scale.checkin'].search_count([
                    ('state', '=', 'submitted'), ('objective_id', 'in', Objective.search(team_domain).ids)]),
                'team_risky': Objective.search_count(team_domain + [
                    ('state', '=', 'running'), ('status', 'in', ('at_risk', 'off_track'))]),
            } if is_manager else False,
            'supporting': [{
                'id': o.id,
                'name': o.name,
                'owner': o.owner_id.name,
                'owner_id': o.owner_id.id,
                'progress': round(o.progress, 1),
                'status': o.status,
                'status_label': status_labels.get(o.status, ''),
            } for o in self._supporting_objectives(cycle) - objectives],
            'extra': self._get_my_extra(),
        }

    @api.model
    def _supporting_objectives(self, cycle):
        domain = [('state', '=', 'running'),
                  '|', '|', ('contributor_user_ids', 'in', [self.env.uid]),
                  ('key_result_ids.contributor_ids', 'in', [self.env.uid]),
                  ('contributor_department_ids', 'in', self.env.user.sudo().employee_ids.department_id.ids)]
        if cycle:
            domain.append(('cycle_id', '=', cycle.id))
        return self.env['okr.scale.objective'].search(domain)

    @api.model
    def _get_my_extra(self):
        """Extra tiles of the personal workspace: ``[{'key', 'label', 'value', 'icon', 'action'}]``."""
        return []
