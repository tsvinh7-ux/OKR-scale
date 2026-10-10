from random import randint

from odoo import fields, models


class OkrTag(models.Model):
    _name = 'okr.scale.tag'
    _description = 'OKR Tag'
    _order = 'name'

    name = fields.Char(required=True, translate=True)
    color = fields.Integer(default=lambda self: randint(1, 11))

    _sql_constraints = [('name_uniq', 'unique (name)', 'Tag name already exists!')]
