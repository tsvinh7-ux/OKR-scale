{
    'name': 'OKR Scale - Customer Portal',
    'summary': 'Share objectives with customer contacts on the portal, read-only or edit, like Project sharing',
    'description': """
OKR Scale - Customer Portal
===========================
* Share an objective with customer contacts (collaborators), like Project sharing
* Read-only or edit access per collaborator; share wizard creates portal accounts and sends invitations
* Edit collaborators check in on every key result; portal key result owners become edit collaborators
* DMAG branded portal: My OKRs cards, objective page with progress ring, check-in form, timeline, discussion
* E-mail reminders for portal key result owners
""",
    'version': '17.0.2.0.0',
    'category': 'Human Resources/OKR',
    'author': 'DMAG',
    'license': 'LGPL-3',
    'depends': ['okr_scale', 'portal'],
    'data': [
        'security/ir.model.access.csv',
        'security/okr_portal_security.xml',
        'data/mail_template_data.xml',
        'wizard/okr_share_wizard_views.xml',
        'views/okr_objective_views.xml',
        'views/okr_key_result_views.xml',
        'views/okr_portal_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'okr_scale/static/src/scss/okr_brand.scss',
            'okr_scale_portal/static/src/scss/okr_portal.scss',
        ],
    },
    'installable': True,
}
