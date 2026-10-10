from odoo import _, models
from odoo.exceptions import AccessError


class OkrObjective(models.Model):
    _inherit = 'okr.scale.objective'

    def _okr_template_line_vals(self):
        """Template key result values built from this objective's key results."""
        self.ensure_one()
        lines = []
        for kr in self.key_result_ids:
            vals = {
                'sequence': kr.sequence,
                'name': kr.name,
                'metric_type': kr.metric_type,
                'unit': kr.unit,
                'start_value': kr.start_value,
                'target_value': kr.target_value,
                'weight': kr.weight,
                'hint': kr.description,
            }
            if kr.progress_method != 'manual' or (
                    kr.metric_type != 'boolean' and kr.start_value == kr.target_value):
                # Progress came from aligned objectives: propose a percentage to measure.
                vals.update(metric_type='percent', unit='%', start_value=0.0, target_value=100.0)
            if kr.metric_type == 'boolean':
                vals.update(start_value=0.0, target_value=1.0)
            lines.append((0, 0, vals))
        return lines

    def action_save_as_template(self):
        """Turn this objective and its key results into a reusable template (OKR managers)."""
        self.ensure_one()
        if not self.env.user.has_group('okr_scale.group_okr_manager'):
            raise AccessError(_('Only OKR managers can save an objective as a template.'))
        template = self.env['okr.scale.template'].create({
            'name': self.name,
            'description': self.description,
            'level': self.level,
            'okr_type': self.okr_type,
            'source_objective_id': self.id,
            'line_ids': self._okr_template_line_vals(),
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Template'),
            'res_model': 'okr.scale.template',
            'res_id': template.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_start_from_template(self):
        """Open the template gallery to fill this draft objective with a template."""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('okr_scale_template.okr_template_action')
        action['context'] = {'okr_tpl_objective_id': self.id}
        action['name'] = _('Choose a template for "%s"', self.name)
        return action
