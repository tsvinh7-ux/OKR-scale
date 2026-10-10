from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.okr_scale.models.okr_common import LEVELS
from ..models.okr_template import METRIC_TYPES


class OkrTemplateApply(models.TransientModel):
    _name = 'okr.scale.template.apply'
    _description = 'Create an Objective from a Template'

    template_id = fields.Many2one('okr.scale.template', 'Template', required=True, ondelete='cascade')
    template_description = fields.Html(related='template_id.description')
    category_id = fields.Many2one(related='template_id.category_id')
    objective_id = fields.Many2one(
        'okr.scale.objective', 'Fill Objective', ondelete='cascade',
        help='Existing draft objective that receives the key results of the template.')
    replace_title = fields.Boolean('Use the template title',
                                   help='Replace the title of the objective by the one below.')
    name = fields.Char('Objective', required=True)
    cycle_id = fields.Many2one(
        'okr.scale.cycle', 'Cycle', domain=[('state', '!=', 'closed')],
        default=lambda self: self.env['okr.scale.cycle'].get_current_cycle())
    level = fields.Selection(LEVELS, default='individual')
    employee_id = fields.Many2one('hr.employee', 'Employee',
                                  default=lambda self: self.env.user.employee_id)
    department_id = fields.Many2one('hr.department', 'Department')
    owner_id = fields.Many2one('res.users', 'Owner', domain=[('share', '=', False)],
                               help='Leave empty to let OKR choose: the employee, the department manager or you.')
    okr_type = fields.Selection([
        ('committed', 'Committed'),
        ('aspirational', 'Aspirational'),
    ], 'Type', default='committed')
    parent_key_result_id = fields.Many2one(
        'okr.scale.key.result', 'Align to Key Result',
        domain="[('cycle_id', '=', cycle_id), ('objective_state', 'in', ('draft', 'to_approve', 'running'))]",
        help='Upper key result this objective contributes to.')
    line_ids = fields.One2many('okr.scale.template.apply.line', 'wizard_id', 'Key Results')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        template = self.env['okr.scale.template'].browse(res.get('template_id'))
        if not template:
            return res
        objective = self.env['okr.scale.objective'].browse(res.get('objective_id'))
        context = self.env.context
        if 'default_name' not in context:
            res['name'] = template.name
        if 'default_okr_type' not in context:
            res['okr_type'] = template.okr_type
        if objective:
            res.update(cycle_id=objective.cycle_id.id, level=objective.level, okr_type=objective.okr_type)
        elif not self.env.context.get('default_level'):
            res.update(self._default_level_values(template.level))
        res['line_ids'] = [Command.create({
            'sequence': line.sequence,
            'name': line.name,
            'metric_type': line.metric_type,
            'unit': line.unit,
            'start_value': line.start_value,
            'target_value': line.target_value,
            'weight': line.weight,
            'hint': line.hint,
        }) for line in template.line_ids]
        return res

    def _default_level_values(self, level):
        """Propose the template level when the user may use it, else the closest allowed one."""
        user = self.env.user
        is_admin = user.has_group('okr_scale.group_okr_admin')
        employee = user.employee_id
        if level == 'company' and is_admin:
            return {'level': 'company'}
        Department = self.env['hr.department'].sudo()
        managed = Department.search([('okr_manager_user_ids', 'in', user.ids)], limit=1)
        if employee.department_id and user in employee.sudo().department_id.okr_manager_user_ids:
            managed = employee.department_id
        if level in ('company', 'department') and (managed or is_admin):
            department = managed or employee.department_id
            if department:
                return {'level': 'department', 'department_id': department.id}
        return {'level': 'individual', 'employee_id': employee.id,
                'department_id': employee.department_id.id}

    @api.onchange('level')
    def _onchange_level(self):
        employee = self.env.user.employee_id
        if self.level == 'individual' and not self.employee_id:
            self.employee_id = employee
        if self.level == 'department' and not self.department_id:
            self.department_id = employee.department_id

    @api.onchange('cycle_id')
    def _onchange_cycle_id(self):
        if self.parent_key_result_id and self.parent_key_result_id.cycle_id != self.cycle_id:
            self.parent_key_result_id = False

    def _prepare_key_results(self):
        self.ensure_one()
        lines = self.line_ids.filtered('include')
        if not lines:
            raise UserError(_('Keep at least one key result.'))
        commands = []
        for line in lines:
            vals = {
                'sequence': line.sequence,
                'name': line.name,
                'metric_type': line.metric_type,
                'unit': line.unit,
                'start_value': line.start_value,
                'target_value': line.target_value,
                'current_value': line.start_value,
                'weight': line.weight,
                'description': line.hint,
            }
            if line.metric_type == 'boolean':
                vals.update(start_value=0.0, target_value=1.0, current_value=0.0)
            elif line.start_value == line.target_value:
                raise ValidationError(_('The target of "%s" must differ from its start value.', line.name))
            if self.owner_id:
                vals['owner_id'] = self.owner_id.id
            commands.append(Command.create(vals))
        return commands

    def _prepare_objective(self):
        self.ensure_one()
        if not self.cycle_id:
            raise UserError(_('Choose the cycle of the objective.'))
        vals = {
            'name': self.name,
            'description': self.template_id.description,
            'cycle_id': self.cycle_id.id,
            'level': self.level,
            'okr_type': self.okr_type,
            'parent_key_result_id': self.parent_key_result_id.id,
            'key_result_ids': self._prepare_key_results(),
        }
        if self.level == 'individual':
            vals['employee_id'] = self.employee_id.id
        elif self.level == 'department':
            vals.update(department_id=self.department_id.id, employee_id=False)
        else:
            vals.update(department_id=False, employee_id=False)
        if self.owner_id:
            vals['owner_id'] = self.owner_id.id
        return vals

    def action_apply(self):
        """Create (or fill) a draft objective with the user's own rights, then open it."""
        self.ensure_one()
        if self.objective_id:
            objective = self.objective_id
            if objective.state != 'draft':
                raise UserError(_('Only draft objectives can be filled from a template.'))
            vals = {'key_result_ids': self._prepare_key_results()}
            if self.replace_title:
                vals['name'] = self.name
            if not objective.description and self.template_id.description:
                vals['description'] = self.template_id.description
            objective.write(vals)
        else:
            objective = self.env['okr.scale.objective'].create(self._prepare_objective())
        # Users only read templates: the counter is bookkeeping, not a business edit.
        self.template_id.sudo().usage_count += 1
        objective.message_post(body=_('Created from the template "%s".', self.template_id.name))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'okr.scale.objective',
            'res_id': objective.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'current',
        }


class OkrTemplateApplyLine(models.TransientModel):
    _name = 'okr.scale.template.apply.line'
    _description = 'Key Result to Create from a Template'
    _order = 'sequence, id'

    wizard_id = fields.Many2one('okr.scale.template.apply', required=True, ondelete='cascade')
    include = fields.Boolean('Keep', default=True)
    sequence = fields.Integer(default=10)
    name = fields.Char('Key Result', required=True)
    metric_type = fields.Selection(METRIC_TYPES, default='number', required=True)
    unit = fields.Char()
    start_value = fields.Float('Start')
    target_value = fields.Float('Target', default=100.0)
    weight = fields.Float(default=1.0)
    hint = fields.Text('How to measure')
