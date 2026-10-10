{
    'name': 'OKR Scale',
    'summary': 'Objectives & Key Results: cycles, alignment, check-ins, permissions, dashboard',
    'description': """
OKR Scale - core
================
* Year / quarter cycles with check-in cadence
* Company, department and individual objectives aligned to upper key results
* Key results measured manually or from aligned objectives (extensible)
* Weekly check-ins with confidence, blockers, next steps and manager review
* Approval workflow, end-of-cycle grading (0.0 - 1.0)
* Level based permissions (company / department / individual) and visibility
* Overall OKR dashboard
""",
    'version': '17.0.1.0.0',
    'category': 'Human Resources/OKR',
    'author': 'DMAG',
    'license': 'LGPL-3',
    'depends': ['hr', 'mail', 'web_hierarchy'],
    'data': [
        'security/okr_security.xml',
        'security/ir.model.access.csv',
        'data/okr_data.xml',
        'data/okr_mail_templates.xml',
        'views/okr_cycle_views.xml',
        'views/okr_key_result_views.xml',
        'views/okr_checkin_views.xml',
        'views/okr_weekly_views.xml',
        'views/okr_objective_views.xml',
        'views/okr_tag_views.xml',
        'views/okr_dashboard_views.xml',
        'views/okr_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'okr_scale/static/src/**/*',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'application': True,
    'installable': True,
}
