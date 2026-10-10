from odoo import api, fields, models


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    okr_manager_user_ids = fields.Many2many(
        'res.users', 'okr_scale_department_manager_rel', 'department_id', 'user_id',
        string='OKR Managers', compute='_compute_okr_manager_user_ids', store=True, recursive=True,
        help='Users managing this department or one of its parent departments. '
             'Used by OKR record rules.')

    @api.depends('manager_id.user_id', 'parent_id.okr_manager_user_ids')
    def _compute_okr_manager_user_ids(self):
        for department in self:
            department.okr_manager_user_ids = department.parent_id.okr_manager_user_ids | department.manager_id.user_id


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    okr_manager_user_ids = fields.Many2many(
        'res.users', 'okr_scale_employee_manager_rel', 'employee_id', 'user_id',
        string='OKR Managers', compute='_compute_okr_manager_user_ids', store=True, recursive=True,
        help='Users in the management chain of this employee (direct managers and department managers). '
             'Used by OKR record rules.')

    @api.depends('parent_id.user_id', 'parent_id.okr_manager_user_ids', 'department_id.okr_manager_user_ids', 'user_id')
    def _compute_okr_manager_user_ids(self):
        for employee in self:
            managers = (
                employee.parent_id.user_id
                | employee.parent_id.okr_manager_user_ids
                | employee.department_id.okr_manager_user_ids
            )
            employee.okr_manager_user_ids = managers - employee.user_id
