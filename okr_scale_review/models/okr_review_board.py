from collections import defaultdict

from odoo import _, api, fields, models
from odoo.addons.okr_scale.models.okr_common import time_progress

from .okr_common import BANDS, MIN_ELAPSED_FOR_PROJECTION, TYPE_TARGETS, average, score_band

LEVEL_KEYS = ('company', 'department', 'individual')
STATUS_KEYS = ('on_track', 'at_risk', 'off_track', 'achieved')
TOP_COUNT = 5
MAX_CARRY_OVER = 80
MAX_QUOTES = 12


class OkrReviewBoard(models.AbstractModel):
    """Data provider of the "Cycle Review" screen.

    Objectives, key results and check-ins are read with the access rights of
    the current user: each person reviews the OKRs they are allowed to see.
    """
    _name = 'okr.scale.review.board'
    _description = 'OKR Cycle Review Board'

    # ------------------------------------------------------------------
    # Scoring helpers (also used by okr.scale.review snapshots)
    # ------------------------------------------------------------------
    @api.model
    def _scope_domain(self, cycle, department_id=False):
        domain = [('state', 'in', ('running', 'done')), ('cycle_id', '=', cycle.id)]
        if department_id:
            domain.append(('department_id', 'child_of', department_id))
        return domain

    @api.model
    def _cycle_phase(self, cycle, today=None):
        """Return ``(phase, elapsed)``: phase is 'planning', 'mid' or 'final'."""
        today = today or fields.Date.context_today(self)
        elapsed = time_progress(cycle.date_start, cycle.date_end, today)
        if cycle.state == 'closed' or elapsed >= 100:
            return 'final', 100.0 if cycle.state == 'closed' else elapsed
        if elapsed <= 0:
            return 'planning', 0.0
        return 'mid', elapsed

    @api.model
    def _objective_score(self, objective, phase, elapsed):
        """Score on the 0.0 - 1.0 scale.

        * graded (closed) objectives: their final score;
        * running objectives at the end of the cycle: progress / 100;
        * running objectives during the cycle: projected score, i.e. the score
          they are heading to at the current pace (progress / time elapsed).
        """
        if objective.state == 'done':
            return round(objective.final_score, 2)
        progress = max(0.0, min(objective.progress, 100.0)) / 100.0
        if phase == 'mid':
            return round(min(1.0, progress * 100.0 / max(elapsed, MIN_ELAPSED_FOR_PROJECTION)), 2)
        return round(progress, 2)

    @api.model
    def _figures(self, objectives, phase, elapsed):
        """Aggregated figures of a set of objectives (used for KPIs, levels and snapshots)."""
        scores = [self._objective_score(o, phase, elapsed) for o in objectives]
        graded = objectives.filtered(lambda o: o.state == 'done')
        bands = {band: 0 for band in BANDS}
        for score in scores:
            bands[score_band(score)] += 1
        status = {key: 0 for key in STATUS_KEYS}
        for objective in objectives:
            if objective.status in status:
                status[objective.status] += 1
        count = len(objectives)
        score = average(scores)
        return {
            'count': count,
            'progress': average(objectives.mapped('progress'), 1),
            'score': score,
            'band': score_band(score) if count else False,
            'final_score': average(graded.mapped('final_score')) if graded else None,
            'graded': len(graded),
            'bands': bands,
            'status': status,
            'on_track_pct': round((status['on_track'] + status['achieved']) * 100.0 / count, 1) if count else 0.0,
        }

    # ------------------------------------------------------------------
    # Screen data
    # ------------------------------------------------------------------
    @api.model
    def _default_cycle(self):
        Cycle = self.env['okr.scale.cycle']
        return Cycle.get_current_cycle() or Cycle.search([('state', '!=', 'draft')], limit=1)

    @api.model
    def get_cycle_review_data(self, cycle_id=False, department_id=False):
        Cycle = self.env['okr.scale.cycle']
        cycle = Cycle.browse(cycle_id).exists() if cycle_id else self._default_cycle()
        department_id = department_id or False
        res = {
            'cycles': [{'id': c.id, 'name': c.display_name, 'state': c.state}
                       for c in Cycle.search([('state', '!=', 'draft')])],
            'departments': [{'id': d.id, 'name': d.display_name} for d in self.env['hr.department'].search([])],
            'department_id': department_id,
            'cycle': False,
        }
        if not cycle:
            return res
        today = fields.Date.context_today(self)
        phase, elapsed = self._cycle_phase(cycle, today)
        Objective = self.env['okr.scale.objective']
        objectives = Objective.search(self._scope_domain(cycle, department_id))
        krs = objectives.key_result_ids
        selection = Objective._fields['level']._description_selection(self.env)
        level_labels = dict(selection)
        status_labels = dict(Objective._fields['status']._description_selection(self.env))
        type_labels = dict(Objective._fields['okr_type']._description_selection(self.env))
        cycle_states = dict(Cycle._fields['state']._description_selection(self.env))
        scores = {o.id: self._objective_score(o, phase, elapsed) for o in objectives}

        # Check-in discipline: share of the expected check-ins submitted (key results of the scope)
        discipline = self.env['okr.scale.dashboard']._checkin_discipline(krs, today) if krs else {}

        overall = self._figures(objectives, phase, elapsed)
        overall.update({
            'key_results': len(krs),
            'kr_achieved': len(krs.filtered('achieved')),
            'checkin_rate': round(average(discipline.values(), 4) * 100, 1) if discipline else 0.0,
        })
        days_total = (cycle.date_end - cycle.date_start).days + 1
        days_left = max(0, (cycle.date_end - today).days)
        res.update({
            'cycle': {
                'id': cycle.id,
                'name': cycle.display_name,
                'date_start': fields.Date.to_string(cycle.date_start),
                'date_end': fields.Date.to_string(cycle.date_end),
                'state': cycle.state,
                'state_label': cycle_states.get(cycle.state, ''),
                'days_total': days_total,
                'days_left': days_left,
                'elapsed': round(elapsed, 1),
            },
            'phase': phase,
            'phase_label': {
                'planning': _('Planning'),
                'mid': _('Mid-cycle review'),
                'final': _('End-of-cycle retrospective'),
            }[phase],
            'score_mode': 'projected' if phase == 'mid' else 'final',
            'suggested_review_type': 'final' if phase == 'final' else 'mid',
            'overall': overall,
            'verdict': self._verdict(overall, phase, elapsed),
            'status': [{'key': key, 'label': status_labels.get(key, key), 'count': overall['status'][key]}
                       for key in STATUS_KEYS],
            'levels': [dict(self._figures(objectives.filtered(lambda o, lv=level: o.level == lv), phase, elapsed),
                            key=level, label=level_labels[level]) for level in LEVEL_KEYS],
            'types': self._types_data(objectives, scores, type_labels),
            'departments_table': self._departments_data(objectives, scores, discipline, phase, elapsed),
            'highlights': self._objective_rows(
                objectives.sorted(lambda o: (-scores[o.id], -o.progress, o.id))[:TOP_COUNT], scores, level_labels,
                status_labels),
            'lowlights': self._objective_rows(
                objectives.sorted(lambda o: (scores[o.id], o.progress, o.id))[:TOP_COUNT], scores, level_labels,
                status_labels),
            'carry_over': self._carry_over_data(cycle, objectives),
            'quotes': self._quotes(objectives),
            'reviews': self._reviews(cycle, department_id),
            'can_review': self.env['okr.scale.review']._okr_can_create_review(department_id),
        })
        # A lowlight is only a problem when it is below the sweet spot
        res['lowlights'] = [row for row in res['lowlights'] if row['score'] < 0.7]
        return res

    @api.model
    def _verdict(self, overall, phase, elapsed=100.0):
        if not overall['count']:
            return {'band': False, 'title': _('Nothing to review yet'),
                    'text': _('No running or closed objective in this scope.')}
        red = overall['bands']['red']
        projected = phase == 'mid'
        band = overall['band']
        if band == 'green':
            title = _('Heading to a great cycle') if projected else _('A successful cycle')
            text = _('The average score reaches the 0.7 sweet spot.')
        elif band == 'yellow':
            title = _('Progressing, below the sweet spot') if projected else _('Partially achieved')
            text = _('Good progress, but the average score stays under 0.7.')
        else:
            title = _('Off course') if projected else _('A difficult cycle')
            text = _('Scores are low: re-plan, unblock or narrow down the scope.')
        if red:
            text += ' ' + _('%s objective(s) in the red zone need attention.', red)
        if projected and elapsed < MIN_ELAPSED_FOR_PROJECTION:
            text += ' ' + _('Early in the cycle: projections are only indicative.')
        return {'band': band, 'title': title, 'text': text}

    @api.model
    def _types_data(self, objectives, scores, type_labels):
        rows = []
        for okr_type in ('committed', 'aspirational'):
            objs = objectives.filtered(lambda o, t=okr_type: o.okr_type == t)
            target = TYPE_TARGETS[okr_type]
            values = [scores[o.id] for o in objs]
            score = average(values)
            reached = len([v for v in values if v >= target - 0.005])
            if not objs:
                verdict = _('No objective of this type.')
            elif okr_type == 'committed':
                verdict = _('Committed objectives are promises: anything below 1.0 must be explained.') \
                    if score < 1.0 else _('Every commitment is delivered.')
            else:
                verdict = _('0.6 - 0.7 is a success for a stretch goal; a steady 1.0 means the bar was too low.') \
                    if score < 0.95 else _('Stretch goals fully achieved: aim higher next cycle.')
            rows.append({
                'key': okr_type,
                'label': type_labels[okr_type],
                'count': len(objs),
                'target': target,
                'score': score,
                'band': score_band(score) if objs else False,
                'reached': reached,
                'reached_pct': round(reached * 100.0 / len(objs), 1) if objs else 0.0,
                'verdict': verdict,
            })
        return rows

    @api.model
    def _departments_data(self, objectives, scores, discipline, phase, elapsed):
        by_department = defaultdict(lambda: self.env['okr.scale.objective'])
        for objective in objectives.filtered('department_id'):
            by_department[objective.department_id] |= objective
        rows = []
        for department, objs in by_department.items():
            figures = self._figures(objs, phase, elapsed)
            rates = [discipline[kr.id] for kr in objs.key_result_ids if kr.id in discipline]
            rate = round(average(rates, 4) * 100, 1) if rates else 0.0
            # During the cycle, progress is judged against the time elapsed
            pace = figures['progress'] / max(elapsed, MIN_ELAPSED_FOR_PROJECTION) if phase == 'mid' \
                else figures['progress'] / 100.0
            rows.append({
                'id': department.id,
                'name': department.display_name,
                'count': figures['count'],
                'progress': figures['progress'],
                'progress_band': score_band(pace),
                'score': figures['score'],
                'band': figures['band'],
                'on_track': figures['on_track_pct'],
                'on_track_band': score_band(figures['on_track_pct'] / 100.0),
                'discipline': rate,
                'discipline_band': score_band(rate / 100.0),
                'bands': figures['bands'],
            })
        return sorted(rows, key=lambda r: (-r['score'], r['name']))

    @api.model
    def _objective_rows(self, objectives, scores, level_labels, status_labels):
        return [{
            'id': o.id,
            'name': o.name,
            'owner': o.owner_id.name or '',
            'user_id': o.owner_id.id,
            'level': o.level,
            'level_label': level_labels.get(o.level, ''),
            'department': o.department_id.name or '',
            'okr_type': o.okr_type,
            'progress': round(o.progress, 1),
            'score': scores[o.id],
            'band': score_band(scores[o.id]),
            'state': o.state,
            'status': o.status,
            'status_label': status_labels.get(o.status, ''),
        } for o in objectives]

    @api.model
    def _carry_over_data(self, cycle, objectives):
        next_cycle = cycle._okr_next_cycle()
        krs = objectives.key_result_ids.filtered(lambda kr: not kr.achieved)
        rows = []
        can_any = False
        for kr in krs.sorted(lambda k: (k.objective_id.level_sequence, k.objective_id.id, k.sequence, k.id))[:MAX_CARRY_OVER]:
            objective = kr.objective_id
            carried = bool(kr.sudo().carried_to_ids)
            allowed = objective._okr_can_carry_over()
            can_any = can_any or (allowed and not carried)
            rows.append({
                'id': kr.id,
                'name': kr.name,
                'objective_id': objective.id,
                'objective': objective.name,
                'level': objective.level,
                'owner': kr.owner_id.name or '',
                'user_id': kr.owner_id.id,
                'progress': round(kr.progress, 1),
                'current': kr.current_value,
                'target': kr.target_value,
                'unit': kr.unit or '',
                'carried': carried,
                'allowed': allowed,
            })
        return {
            'next_cycle': {'id': next_cycle.id, 'name': next_cycle.display_name} if next_cycle else False,
            'key_results': rows,
            'total': len(krs),
            'can_carry_over': can_any,
        }

    @api.model
    def _quotes(self, objectives):
        quotes = []
        kinds = (('lessons_learned', _('Lesson learned')), ('self_assessment', _('Self-assessment')))
        for objective in objectives.sorted(lambda o: (o.state != 'done', o.level_sequence, o.id)):
            for field_name, label in kinds:
                text = (objective[field_name] or '').strip()
                if text:
                    quotes.append({
                        'key': '%s-%s' % (objective.id, field_name),
                        'objective_id': objective.id,
                        'objective': objective.name,
                        'owner': objective.owner_id.name or '',
                        'user_id': objective.owner_id.id,
                        'kind': field_name,
                        'kind_label': label,
                        'text': text,
                    })
        return quotes[:MAX_QUOTES]

    @api.model
    def _reviews(self, cycle, department_id):
        domain = [('cycle_id', '=', cycle.id)]
        if department_id:
            domain += ['|', ('department_id', '=', False), ('department_id', 'child_of', department_id)]
        Review = self.env['okr.scale.review']
        type_labels = dict(Review._fields['review_type']._description_selection(self.env))
        state_labels = dict(Review._fields['state']._description_selection(self.env))
        return [{
            'id': r.id,
            'name': r.name,
            'review_type': r.review_type,
            'type_label': type_labels.get(r.review_type, ''),
            'department': r.department_id.name or _('Company-wide'),
            'date': fields.Date.to_string(r.date),
            'facilitator': r.facilitator_id.name or '',
            'user_id': r.facilitator_id.id,
            'state': r.state,
            'state_label': state_labels.get(r.state, ''),
            'score': r.snapshot_avg_score,
        } for r in Review.search(domain, limit=20)]
