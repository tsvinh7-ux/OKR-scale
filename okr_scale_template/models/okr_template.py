from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression

from odoo.addons.okr_scale.models.okr_common import LEVELS

METRIC_TYPES = [
    ('number', 'Number'),
    ('percent', 'Percentage'),
    ('currency', 'Amount'),
    ('boolean', 'Done / Not done'),
]


class OkrTemplateCategory(models.Model):
    _name = 'okr.scale.template.category'
    _description = 'OKR Template Category'
    _order = 'sequence, id'

    name = fields.Char(required=True, translate=True)
    icon = fields.Char(default='fa-bullseye', help='Font Awesome class, e.g. fa-heart.')
    color = fields.Integer(help='Color of the category chip (0 to 11).')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    description = fields.Char(translate=True)
    template_ids = fields.One2many('okr.scale.template', 'category_id', 'Templates')
    template_count = fields.Integer(compute='_compute_template_count')

    def _compute_template_count(self):
        data = self.env['okr.scale.template']._read_group(
            [('category_id', 'in', self.ids)], ['category_id'], ['__count'])
        counts = {category.id: count for category, count in data}
        for category in self:
            category.template_count = counts.get(category.id, 0)

    def action_view_templates(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('okr_scale_template.okr_template_action')
        action['context'] = {'searchpanel_default_category_id': self.id}
        return action


class OkrTemplate(models.Model):
    _name = 'okr.scale.template'
    _description = 'OKR Template'
    _order = 'sequence, usage_count desc, id'

    name = fields.Char('Objective', required=True, translate=True,
                       help='Inspiring, qualitative objective proposed by this template.')
    description = fields.Html(translate=True, help='Why this objective matters and when to use it.')
    category_id = fields.Many2one('okr.scale.template.category', 'Category', index=True, ondelete='restrict')
    category_color = fields.Integer(related='category_id.color')
    category_icon = fields.Char(related='category_id.icon')
    level = fields.Selection(LEVELS, 'Suggested Level', required=True, default='department')
    okr_type = fields.Selection([
        ('committed', 'Committed'),
        ('aspirational', 'Aspirational'),
    ], 'Type', default='committed', required=True)
    keywords = fields.Char(translate=True, help='Words used to find this template, comma separated.')
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    usage_count = fields.Integer('Used', readonly=True, copy=False,
                                 help='Number of objectives created from this template.')
    line_ids = fields.One2many('okr.scale.template.line', 'template_id', 'Key Results', copy=True)
    line_count = fields.Integer('Key Result Count', compute='_compute_line_info')
    line_preview = fields.Text(compute='_compute_line_info',
                               help='Names of the first key results, one per line (gallery cards).')
    source_objective_id = fields.Many2one('okr.scale.objective', 'Created From', readonly=True, copy=False,
                                          ondelete='set null')

    @api.depends('line_ids.name', 'line_ids.sequence')
    def _compute_line_info(self):
        for template in self:
            lines = template.line_ids.sorted(lambda line: (line.sequence, line.id))
            template.line_count = len(lines)
            template.line_preview = '\n'.join(lines[:3].mapped('name'))

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        if name and operator in ('ilike', 'like', '=ilike', '=like'):
            domain = expression.AND([
                ['|', ('name', operator, name), ('keywords', operator, name)], domain or []])
            return self._search(domain, limit=limit, order=order)
        return super()._name_search(name, domain, operator, limit, order)

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        """Give the side panel the icon and color of each category."""
        result = super().search_panel_select_range(field_name, **kwargs)
        if field_name == 'category_id' and result.get('values'):
            ids = [value['id'] for value in result['values'] if value.get('id')]
            categories = {c.id: c for c in self.env['okr.scale.template.category'].browse(ids).exists()}
            for value in result['values']:
                category = categories.get(value.get('id'))
                if category:
                    value['okr_tpl_icon'] = category.icon or 'fa-bullseye'
                    value['okr_tpl_color'] = category.color or 0
        return result

    def copy(self, default=None):
        default = dict(default or {})
        if 'name' not in default:
            default['name'] = _('%s (copy)', self.name)
        return super().copy(default)

    def action_use_template(self):
        """Open the wizard creating an objective from this template."""
        self.ensure_one()
        context = {
            key: value for key, value in self.env.context.items()
            if not key.startswith(('default_', 'search_default_', 'searchpanel_'))
        }
        context['default_template_id'] = self.id
        target = self.env.context.get('okr_tpl_objective_id')
        if target:
            context['default_objective_id'] = target
        return {
            'type': 'ir.actions.act_window',
            'name': _('Use template'),
            'res_model': 'okr.scale.template.apply',
            'view_mode': 'form',
            'target': 'new',
            'context': context,
        }


class OkrTemplateLine(models.Model):
    _name = 'okr.scale.template.line'
    _description = 'OKR Template Key Result'
    _order = 'template_id, sequence, id'

    template_id = fields.Many2one('okr.scale.template', 'Template', required=True, index=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    name = fields.Char('Key Result', required=True, translate=True)
    metric_type = fields.Selection(METRIC_TYPES, default='number', required=True)
    unit = fields.Char(translate=True, help='Unit displayed next to values, e.g. patients, %, minutes.')
    start_value = fields.Float('Start')
    target_value = fields.Float('Target', default=100.0)
    weight = fields.Float(default=1.0)
    hint = fields.Text('How to measure', translate=True,
                       help='Data source and calculation rule, so that everybody measures the same way.')
    is_decreasing = fields.Boolean(compute='_compute_is_decreasing',
                                   help='The lower the better (e.g. no-show rate, waiting time).')

    @api.depends('start_value', 'target_value', 'metric_type')
    def _compute_is_decreasing(self):
        for line in self:
            line.is_decreasing = line.metric_type != 'boolean' and line.target_value < line.start_value

    @api.constrains('start_value', 'target_value', 'metric_type', 'weight')
    def _check_values(self):
        for line in self:
            if line.metric_type != 'boolean' and line.start_value == line.target_value:
                raise ValidationError(_('The target of "%s" must differ from its start value.', line.name))
            if line.weight < 0:
                raise ValidationError(_('The weight of a key result cannot be negative.'))

    @api.onchange('metric_type')
    def _onchange_metric_type(self):
        if self.metric_type == 'boolean':
            self.start_value, self.target_value = 0.0, 1.0
        elif self.metric_type == 'percent' and not self.unit:
            self.unit = '%'
