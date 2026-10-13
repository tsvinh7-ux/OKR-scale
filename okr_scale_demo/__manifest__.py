{
    'name': 'OKR Scale - DMAG Demo Data',
    'summary': 'Realistic DMAG demo: organisation, cycles, OKRs, check-ins, CFR, rewards, portal, templates',
    'description': """
OKR Scale - DMAG Demo Data
==========================
Loads a complete, realistic demo of the OKR suite for "DMAG - Nen Tang Van Hanh & Tang Truong Nha Khoa":
organisation and users, yearly / quarterly cycles, aligned company, department and individual OKRs,
weekly check-ins history, CFR (kudos, feedback, 1:1), reward store, customer portal and templates.

The data is created once by a post-install hook. Install it on a dedicated demo database only.
""",
    'version': '17.0.1.0.0',
    'category': 'Human Resources/OKR',
    'author': 'DMAG',
    'license': 'LGPL-3',
    'depends': [
        'okr_scale',
        'okr_scale_project',
        'okr_scale_cfr',
        'okr_scale_reward',
        'okr_scale_portal',
        'okr_scale_template',
        'okr_scale_review',
        'dmag_brand_theme',
    ],
    'data': [],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
}
