{
    'name': 'OKR Scale - Customer Portal',
    'summary': 'Share objectives with B2B customers on the portal: view progress, check in, discuss',
    'description': """
OKR Scale - Customer Portal
===========================
* Share objectives with a B2B customer (commercial entity) on the customer portal
* View only or view and check-in access per objective
* Portal users of the customer can own key results and check in on them
* Portal pages: My OKRs list, objective detail, check-in form, discussion
* E-mail reminders for portal key result owners
""",
    'version': '17.0.1.0.0',
    'category': 'Human Resources/OKR',
    'author': 'DMAG',
    'license': 'LGPL-3',
    'depends': ['okr_scale', 'portal'],
    'data': [
        'security/ir.model.access.csv',
        'security/okr_portal_security.xml',
        'data/mail_template_data.xml',
        'views/okr_objective_views.xml',
        'views/okr_key_result_views.xml',
        'views/okr_portal_templates.xml',
    ],
    'installable': True,
}
