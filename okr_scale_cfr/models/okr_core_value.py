from odoo import api, fields, models


class OkrCoreValue(models.Model):
    _name = 'okr.scale.core.value'
    _description = 'OKR Core Value'
    _order = 'sequence, id'

    name = fields.Char(required=True, translate=True)
    description = fields.Text(translate=True)
    icon = fields.Char(help='Emoji displayed next to the value, e.g. 🤝')
    color = fields.Integer()
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    recognition_count = fields.Integer(compute='_compute_recognition_count')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'A core value with this name already exists.'),
    ]

    @api.depends('name', 'icon')
    def _compute_display_name(self):
        for value in self:
            value.display_name = '%s %s' % (value.icon, value.name) if value.icon else value.name

    def _compute_recognition_count(self):
        data = self.env['okr.scale.recognition']._read_group(
            [('core_value_ids', 'in', self.ids)], ['core_value_ids'], ['__count'])
        counts = {value.id: count for value, count in data}
        for value in self:
            value.recognition_count = counts.get(value.id, 0)
