{
    'name': 'OKR Scale - Template Library',
    'summary': 'Ready-to-use OKR templates for dental clinics: browse, apply in one click, save your own',
    'description': """
OKR Scale - Template Library
============================
* Template categories with icon and color
* OKR templates: inspiring objective, suggested level and type, 3 to 4 measurable key results with measurement hints
* Premium gallery with category side panel
* "Use template" wizard: cycle, level, owner, alignment, inline target adjustment, draft objective created with the user's rights
* "Save as template" from any objective (OKR managers)
* 25 templates for a dental clinic chain (DMAG)
""",
    'version': '17.0.1.0.0',
    'category': 'Human Resources/OKR',
    'author': 'DMAG',
    'license': 'LGPL-3',
    'depends': ['okr_scale'],
    'data': [
        'security/ir.model.access.csv',
        'data/okr_template_category_data.xml',
        'data/okr_template_data.xml',
        'views/okr_template_banner.xml',
        'views/okr_template_category_views.xml',
        'views/okr_template_views.xml',
        'wizard/okr_template_apply_views.xml',
        'views/okr_objective_views.xml',
        'views/okr_template_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'okr_scale_template/static/src/**/*',
        ],
    },
    'installable': True,
}
