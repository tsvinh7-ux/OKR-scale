from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


class OkrCarryOver(models.TransientModel):
    _name = 'okr.scale.carry.over'
    _description = 'Carry Key Results Over to the Next Cycle'

    source_cycle_id = fields.Many2one('okr.scale.cycle', 'From Cycle', required=True)
    target_cycle_id = fields.Many2one(
        'okr.scale.cycle', 'To Cycle', required=True,
        compute='_compute_target_cycle_id', store=True, readonly=False, precompute=True,
        domain="[('id', '!=', source_cycle_id), ('state', '!=', 'closed')]")
    key_result_ids = fields.Many2many(
        'okr.scale.key.result', string='Key Results',
        domain="[('cycle_id', '=', source_cycle_id), ('achieved', '=', False), "
               "('objective_state', 'in', ('running', 'done'))]")
    objective_count = fields.Integer(compute='_compute_objective_count')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        context = self.env.context
        if not res.get('source_cycle_id') and context.get('active_model') == 'okr.scale.cycle':
            res['source_cycle_id'] = context.get('active_id')
        if 'key_result_ids' in fields_list and not res.get('key_result_ids') and context.get('carry_kr_ids'):
            res['key_result_ids'] = [(6, 0, context['carry_kr_ids'])]
        return res

    @api.depends('source_cycle_id')
    def _compute_target_cycle_id(self):
        for wizard in self:
            if wizard.source_cycle_id and not wizard.target_cycle_id:
                wizard.target_cycle_id = wizard.source_cycle_id._okr_next_cycle()

    @api.depends('key_result_ids')
    def _compute_objective_count(self):
        for wizard in self:
            wizard.objective_count = len(wizard.key_result_ids.objective_id)

    def _target_objective(self, objective):
        """Objective of the target cycle receiving the key results of ``objective`` (created once)."""
        existing = self.env['okr.scale.objective'].search([
            ('carried_from_id', '=', objective.id), ('cycle_id', '=', self.target_cycle_id.id),
            ('state', 'in', ('draft', 'to_approve'))], limit=1)
        if existing:
            return existing, False
        parent_kr = False
        if objective.parent_key_result_id:
            # Keep the alignment when the upper key result was carried over too
            parent_kr = self.env['okr.scale.key.result'].search([
                ('carried_from_id', '=', objective.parent_key_result_id.id),
                ('cycle_id', '=', self.target_cycle_id.id)], limit=1)
        vals = {
            'name': objective.name,
            'description': objective.description,
            'cycle_id': self.target_cycle_id.id,
            'company_id': self.target_cycle_id.company_id.id,
            'level': objective.level,
            'employee_id': objective.employee_id.id,
            'department_id': objective.department_id.id,
            'owner_id': objective.owner_id.id,
            'okr_type': objective.okr_type,
            'visibility': objective.visibility,
            'tag_ids': [(6, 0, objective.tag_ids.ids)],
            'parent_key_result_id': parent_kr.id if parent_kr else False,
            'carried_from_id': objective.id,
        }
        return self.env['okr.scale.objective'].create(vals), True

    @api.model
    def _key_result_values(self, kr, objective):
        return {
            'objective_id': objective.id,
            'name': kr.name,
            'description': kr.description,
            'sequence': kr.sequence,
            'owner_id': kr.owner_id.id,
            'metric_type': kr.metric_type,
            'unit': kr.unit,
            'weight': kr.weight,
            'progress_method': kr.progress_method,
            'start_value': kr.current_value,
            'current_value': kr.current_value,
            'target_value': kr.target_value,
            'carried_from_id': kr.id,
        }

    def action_confirm(self):
        self.ensure_one()
        target = self.target_cycle_id
        if target == self.source_cycle_id:
            raise UserError(_('Choose another cycle to carry the key results over to.'))
        if target.state == 'closed':
            raise UserError(_('Cycle %s is closed.', target.display_name))
        krs = self.key_result_ids.filtered(lambda kr: not kr.achieved and not kr.sudo().carried_to_ids)
        if not krs:
            raise UserError(_('Select at least one unfinished key result that was not carried over yet.'))
        new_objectives = self.env['okr.scale.objective']
        for objective in krs.objective_id:
            if not objective._okr_can_carry_over():
                raise AccessError(_('You are not allowed to carry "%s" over to another cycle.', objective.name))
            obj_krs = krs.filtered(lambda kr, o=objective: kr.objective_id == o)
            new_objective, created = self._target_objective(objective)
            new_krs = self.env['okr.scale.key.result'].create(
                [self._key_result_values(kr, new_objective) for kr in obj_krs])
            new_objectives |= new_objective
            kr_list = Markup('').join(Markup('<li>%s</li>') % kr.name for kr in obj_krs)
            # The source objective may be closed: post as the current user on a record they can read.
            objective.check_access_rule('read')
            objective.sudo().message_post(
                body=Markup('%s<ul>%s</ul>') % (
                    _('Key results carried over to cycle %s:', target.display_name), kr_list),
                author_id=self.env.user.partner_id.id)
            intro = _('Carried over from %(objective)s (cycle %(cycle)s).', objective=objective.name,
                      cycle=objective.cycle_id.display_name) if created else \
                _('Key results added from %(objective)s (cycle %(cycle)s).', objective=objective.name,
                  cycle=objective.cycle_id.display_name)
            new_objective.message_post(body=Markup('%s<ul>%s</ul>') % (
                intro, Markup('').join(Markup('<li>%s</li>') % kr.name for kr in new_krs)))
        action = self.env['ir.actions.act_window']._for_xml_id('okr_scale.okr_objective_action')
        action.update({
            'domain': [('id', 'in', new_objectives.ids)],
            'context': {'default_cycle_id': target.id},
            'name': _('Carried over to %s', target.display_name),
        })
        if len(new_objectives) == 1:
            action.update({'res_id': new_objectives.id, 'views': [(False, 'form')], 'view_mode': 'form'})
        return action
