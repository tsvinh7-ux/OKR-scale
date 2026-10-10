from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class OkrObjectiveCollaborator(models.Model):
    _name = 'okr.scale.objective.collaborator'
    _description = 'OKR Objective Collaborator (portal sharing)'
    _order = 'objective_id, id'

    objective_id = fields.Many2one('okr.scale.objective', 'Objective', required=True, index=True,
                                   ondelete='cascade')
    partner_id = fields.Many2one('res.partner', 'Collaborator', required=True, index=True,
                                 ondelete='cascade')
    partner_email = fields.Char(related='partner_id.email')
    access_mode = fields.Selection([
        ('read', 'Read-only'),
        ('edit', 'Edit'),
    ], 'Access', default='read', required=True,
        help='Read-only: follows the progress and discusses in the chatter.\n'
             'Edit: can also check in on every key result of the objective and attach files.')
    company_id = fields.Many2one(related='objective_id.company_id', store=True)
    user_id = fields.Many2one('res.users', 'Portal User', compute='_compute_user_id')

    _sql_constraints = [
        ('unique_collaborator', 'UNIQUE(objective_id, partner_id)',
         'A contact can only be added once as collaborator of an objective.'),
    ]

    @api.depends('objective_id', 'partner_id')
    def _compute_display_name(self):
        for collaborator in self:
            collaborator.display_name = f'{collaborator.objective_id.display_name} - {collaborator.partner_id.display_name}'

    @api.depends('partner_id')
    def _compute_user_id(self):
        for collaborator in self:
            collaborator.user_id = collaborator.partner_id.sudo().user_ids[:1]

    @api.constrains('partner_id')
    def _check_partner_not_internal(self):
        for collaborator in self.sudo():
            if collaborator.partner_id.user_ids.filtered(lambda u: not u.share):
                raise ValidationError(_(
                    '%s is an employee: employees see objectives according to the OKR visibility, '
                    'they cannot be portal collaborators.', collaborator.partner_id.display_name))

    def _check_objective_rights(self):
        if not self.env.su:
            self.objective_id._check_can_share()

    def _check_key_result_owners(self):
        """Portal owners of key results must stay edit collaborators."""
        for collaborator in self.sudo():
            owners = collaborator.objective_id.key_result_ids.owner_id
            if collaborator.partner_id in owners.partner_id:
                raise UserError(_(
                    '%(partner)s owns key results of "%(objective)s": reassign them before removing '
                    'the collaborator or making it read-only.',
                    partner=collaborator.partner_id.display_name, objective=collaborator.objective_id.name))

    @api.model_create_multi
    def create(self, vals_list):
        collaborators = super().create(vals_list)
        collaborators._check_objective_rights()
        return collaborators

    def write(self, vals):
        self._check_objective_rights()
        if vals.get('access_mode') == 'read':
            self.filtered(lambda c: c.access_mode == 'edit')._check_key_result_owners()
        res = super().write(vals)
        if 'objective_id' in vals:
            self._check_objective_rights()
        return res

    def unlink(self):
        self._check_objective_rights()
        self._check_key_result_owners()
        return super().unlink()
