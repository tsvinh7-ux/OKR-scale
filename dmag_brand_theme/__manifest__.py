{
    'name': 'DMAG Brand Theme',
    'summary': 'DMAG colors for the Odoo backend (navbar, buttons, links)',
    'version': '17.0.1.0.0',
    'category': 'Hidden/Theme',
    'author': 'DMAG',
    'license': 'LGPL-3',
    'depends': ['web'],
    'assets': {
        'web._assets_primary_variables': [
            ('before', 'web/static/src/scss/primary_variables.scss',
             'dmag_brand_theme/static/src/scss/primary_variables.scss'),
        ],
    },
    'installable': True,
}
