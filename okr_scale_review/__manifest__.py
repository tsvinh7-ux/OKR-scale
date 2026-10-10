{
    'name': 'OKR Scale - Cycle Review',
    'summary': 'Mid-cycle review and end-of-cycle retrospective, scores per level, carry-over of unfinished key results',
    'description': """
OKR Scale - Cycle Review
========================
* "Cycle Review" screen: scores per level on the 0.0 - 1.0 scale, grade bands, committed vs aspirational,
  department heat map, highlights / needs attention, lessons learned wall
* Review meetings (mid-cycle and final retrospective) with what went well, what to improve,
  lessons learned, decisions and a frozen snapshot of the figures
* Carry unfinished key results over to the next cycle (start = previous current value)
* Automatic reminders for the mid-cycle review (50 % of the cycle) and the final review
""",
    'version': '17.0.1.0.0',
    'category': 'Human Resources/OKR',
    'author': 'DMAG',
    'license': 'LGPL-3',
    'depends': ['okr_scale'],
    'data': [
        'security/okr_review_security.xml',
        'security/ir.model.access.csv',
        'data/okr_review_data.xml',
        'views/okr_review_views.xml',
        'views/okr_cycle_views.xml',
        'views/okr_objective_views.xml',
        'wizard/okr_carry_over_views.xml',
        'views/okr_review_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'okr_scale_review/static/src/**/*',
        ],
    },
    'installable': True,
}
