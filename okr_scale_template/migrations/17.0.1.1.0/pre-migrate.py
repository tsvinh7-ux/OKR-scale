"""Give the key result lines of the shipped templates an XML id.

Up to 17.0.1.0.0 the lines were created through ``line_ids`` commands, without
XML id. They are now separate ``noupdate`` records (so that they can be
translated). Registering the existing lines under the new XML ids keeps the
upgrade from creating a second set of lines, and keeps any user edit.
"""


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        INSERT INTO ir_model_data (module, name, model, res_id, noupdate)
             SELECT 'okr_scale_template', tpl.name || '_kr' || (line.sequence / 10),
                    'okr.scale.template.line', line.id, true
               FROM ir_model_data tpl
               JOIN okr_scale_template_line line ON line.template_id = tpl.res_id
              WHERE tpl.module = 'okr_scale_template'
                AND tpl.model = 'okr.scale.template'
                AND line.sequence IN (10, 20, 30, 40)
                AND NOT EXISTS (
                    SELECT 1 FROM ir_model_data x
                     WHERE x.module = 'okr_scale_template'
                       AND x.name = tpl.name || '_kr' || (line.sequence / 10))
                AND line.id = (
                    SELECT min(l2.id) FROM okr_scale_template_line l2
                     WHERE l2.template_id = line.template_id AND l2.sequence = line.sequence)
    """)
