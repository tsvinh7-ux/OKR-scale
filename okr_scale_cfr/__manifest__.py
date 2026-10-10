{
    'name': 'OKR Scale - CFR',
    'summary': 'Conversations, Feedback and Recognition around OKRs',
    'description': """
OKR Scale - CFR
===============
* Recognition wall (kudos) linked to company core values and OKRs
* Continuous, transparent feedback, spontaneous or on request (anonymity optional, off by default)
* 1:1 / OKR conversations with agenda, notes, action items and calendar meetings
* Extra dashboard indicators, "Most recognized" ranking and personal workspace tile
""",
    'version': '17.0.1.1.0',
    'category': 'Human Resources/OKR',
    'author': 'DMAG',
    'license': 'LGPL-3',
    'depends': ['okr_scale', 'calendar'],
    'data': [
        'security/okr_cfr_security.xml',
        'security/ir.model.access.csv',
        'data/okr_cfr_data.xml',
        'views/res_config_settings_views.xml',
        'views/okr_cfr_templates.xml',
        'views/okr_core_value_views.xml',
        'views/okr_recognition_views.xml',
        'views/okr_feedback_views.xml',
        'wizard/okr_feedback_request_views.xml',
        'views/okr_conversation_views.xml',
        'views/okr_objective_views.xml',
        'views/okr_cfr_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'okr_scale_cfr/static/src/scss/okr_cfr.scss',
        ],
    },
    'installable': True,
}
