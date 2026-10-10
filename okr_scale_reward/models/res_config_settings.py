from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    okr_reward_monthly_allowance = fields.Integer(
        'Monthly Giving Allowance', config_parameter='okr_scale_reward.monthly_allowance',
        help='Points each user can give with recognitions every month. It does not reduce their own wallet.')
    okr_reward_max_points_per_recognition = fields.Integer(
        'Max Points per Recognition', config_parameter='okr_scale_reward.max_points_per_recognition',
        help='Maximum points given to each receiver of a recognition.')
    okr_reward_checkin_points = fields.Integer(
        'Points per Check-in', config_parameter='okr_scale_reward.checkin_points',
        help='Granted for a submitted check-in, at most once per key result and check-in period.')
    okr_reward_kr_achieved_points = fields.Integer(
        'Points per Achieved Key Result', config_parameter='okr_scale_reward.kr_achieved_points',
        help='Granted once to the owner when a key result reaches its target.')
    okr_reward_objective_achieved_points = fields.Integer(
        'Points per Successful Objective', config_parameter='okr_scale_reward.objective_achieved_points',
        help='Granted once to the owner when an objective is closed with a final score of at least 0.7.')
