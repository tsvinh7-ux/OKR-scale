import math

from werkzeug.exceptions import Forbidden
from werkzeug.urls import url_encode

from odoo import _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.okr_scale_portal.models.okr_objective import PORTAL_STATES
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

TEXT_MAX_LENGTH = 2000
CHECKIN_TEXT_FIELDS = ('achievements', 'blockers', 'next_steps')


def _parse_float(value):
    """Parse a number typed by a customer: accepts '1234.5', '1234,5' and '1,234.5'."""
    value = (value or '').strip().replace(' ', '').replace(' ', '')
    if not value:
        raise ValueError('empty')
    if ',' in value and '.' not in value:
        value = value.replace(',', '.')
    else:
        value = value.replace(',', '')
    number = float(value)
    if not math.isfinite(number) or abs(number) >= 1e15:
        raise ValueError('out of range')
    return number


class OkrCustomerPortal(CustomerPortal):

    def _okr_portal_domain(self):
        return [('portal_shared', '=', True), ('state', 'in', PORTAL_STATES)]

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'okr_count' in counters:
            Objective = request.env['okr.scale.objective']
            values['okr_count'] = Objective.search_count(self._okr_portal_domain()) \
                if Objective.check_access_rights('read', raise_exception=False) else 0
        return values

    # ------------------------------------------------------------------
    # My OKRs
    # ------------------------------------------------------------------
    def _okr_searchbar_sortings(self):
        return {
            'date': {'label': _('Newest'), 'order': 'create_date desc, id desc'},
            'name': {'label': _('Name'), 'order': 'name, id'},
            'progress': {'label': _('Progress'), 'order': 'progress desc, id desc'},
        }

    def _okr_searchbar_filters(self):
        return {
            'all': {'label': _('All'), 'domain': []},
            'running': {'label': _('Running'), 'domain': [('state', '=', 'running')]},
            'done': {'label': _('Closed'), 'domain': [('state', '=', 'done')]},
        }

    @http.route(['/my/okrs', '/my/okrs/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_okrs(self, page=1, sortby=None, filterby=None, cycle=None, **kw):
        Objective = request.env['okr.scale.objective']
        if not Objective.check_access_rights('read', raise_exception=False):
            return request.redirect('/my')
        values = self._prepare_portal_layout_values()

        searchbar_sortings = self._okr_searchbar_sortings()
        searchbar_filters = self._okr_searchbar_filters()
        sortby = sortby if sortby in searchbar_sortings else 'date'
        filterby = filterby if filterby in searchbar_filters else 'all'

        base_domain = self._okr_portal_domain()
        cycles = request.env['okr.scale.cycle'].browse(
            [cycle.id for [cycle] in Objective._read_group(base_domain, ['cycle_id'])]).sudo().sorted()
        try:
            cycle_id = int(cycle) if cycle else False
        except ValueError:
            cycle_id = False
        selected_cycle = cycles.filtered(lambda c: c.id == cycle_id)

        domain = base_domain + searchbar_filters[filterby]['domain']
        if selected_cycle:
            domain += [('cycle_id', '=', selected_cycle.id)]

        okr_count = Objective.search_count(domain)
        pager = portal_pager(
            url='/my/okrs',
            url_args={'sortby': sortby, 'filterby': filterby, 'cycle': selected_cycle.id or None},
            total=okr_count,
            page=page,
            step=self._items_per_page,
        )
        objectives = Objective.search(domain, order=searchbar_sortings[sortby]['order'],
                                      limit=self._items_per_page, offset=pager['offset'])
        request.session['my_okrs_history'] = objectives.ids[:100]

        values.update({
            # Access was checked by the search: render with sudo (names of internal owners).
            'objectives': objectives.sudo(),
            'page_name': 'okr',
            'default_url': '/my/okrs',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'sortby': sortby,
            'filterby': filterby,
            'okr_cycles': cycles,
            'okr_selected_cycle': selected_cycle,
        })
        return request.render('okr_scale_portal.portal_my_okrs', values)

    # ------------------------------------------------------------------
    # Objective detail
    # ------------------------------------------------------------------
    def _okr_check_objective_access(self, objective_id):
        """Return the objective (sudo) if the current user may see it on the portal.

        Access tokens are deliberately not accepted: only logged in users
        allowed by the record rules see shared objectives.
        """
        objective_sudo = self._document_check_access('okr.scale.objective', objective_id)
        if not objective_sudo._is_portal_visible():
            raise MissingError(_('This objective is not shared on the portal.'))
        return objective_sudo

    def _okr_checkin_messages(self):
        return {
            'value': _('Enter a valid number for the new value.'),
            'confidence': _('The confidence must be between 1 and 10.'),
            'text': _('Comments are limited to %s characters.', TEXT_MAX_LENGTH),
            'state': _('Check-ins are only possible on running objectives.'),
        }

    def _okr_get_page_view_values(self, objective_sudo, **kwargs):
        user = request.env.user
        key_results = objective_sudo.key_result_ids
        checkin_krs = key_results.filtered(lambda kr: kr._portal_can_checkin(user))
        values = {
            'page_name': 'okr',
            'okr_objective': objective_sudo,
            'okr_key_results': key_results,
            'okr_checkin_kr_ids': checkin_krs.ids,
            'okr_checkins': objective_sudo.checkin_ids.filtered(lambda c: c.state != 'draft')[:20],
            'okr_checkin_done': kwargs.get('checkin') == 'done',
            'okr_checkin_error': self._okr_checkin_messages().get(kwargs.get('checkin_error')),
            'okr_error_kr_id': kwargs.get('kr'),
        }
        return self._get_page_view_values(objective_sudo, None, values, 'my_okrs_history', False)

    @http.route('/my/okr/<int:objective_id>', type='http', auth='user', website=True)
    def portal_my_okr(self, objective_id, **kw):
        try:
            objective_sudo = self._okr_check_objective_access(objective_id)
        except (AccessError, MissingError):
            raise request.not_found()
        values = self._okr_get_page_view_values(objective_sudo, **kw)
        return request.render('okr_scale_portal.portal_my_okr', values)

    # ------------------------------------------------------------------
    # Check-in
    # ------------------------------------------------------------------
    def _okr_parse_checkin(self, kr_sudo, post):
        """Validate the posted check-in. Return (values, error code)."""
        values = {}
        if kr_sudo.progress_method == 'manual':
            try:
                values['new_value'] = _parse_float(post.get('new_value'))
            except (TypeError, ValueError):
                return values, 'value'
            if kr_sudo.metric_type == 'boolean' and values['new_value'] not in (0.0, 1.0):
                return values, 'value'
        try:
            confidence = int(post.get('confidence') or 0)
        except (TypeError, ValueError):
            confidence = 0
        if not 1 <= confidence <= 10:
            return values, 'confidence'
        values['confidence'] = str(confidence)
        for fname in CHECKIN_TEXT_FIELDS:
            text = (post.get(fname) or '').strip()
            if len(text) > TEXT_MAX_LENGTH:
                return values, 'text'
            values[fname] = text
        return values, None

    @http.route('/my/okr/kr/<int:kr_id>/checkin', type='http', auth='user', methods=['POST'], website=True)
    def portal_okr_checkin(self, kr_id, **post):
        KeyResult = request.env['okr.scale.key.result']
        kr_sudo = KeyResult.sudo().browse(kr_id).exists()
        if not kr_sudo:
            raise request.not_found()
        try:
            self._okr_check_objective_access(kr_sudo.objective_id.id)
        except (AccessError, MissingError):
            raise request.not_found()
        kr = KeyResult.browse(kr_sudo.id)
        objective = kr_sudo.objective_id
        url = f'/my/okr/{objective.id}'
        if objective.state != 'running':
            return request.redirect(f"{url}?{url_encode({'checkin_error': 'state', 'kr': kr.id})}")
        if not kr._portal_can_checkin():
            raise Forbidden()
        values, error = self._okr_parse_checkin(kr_sudo, post)
        if error:
            return request.redirect(f"{url}?{url_encode({'checkin_error': error, 'kr': kr.id})}#kr-{kr.id}")
        kr._portal_submit_checkin(values)
        return request.redirect(f'{url}?checkin=done#kr-{kr.id}')
