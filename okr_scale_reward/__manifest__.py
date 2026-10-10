{
    'name': 'OKR Scale - Rewards & Store',
    'summary': 'Reward points for recognitions and OKR results, gift store and redemptions',
    'description': """
OKR Scale - Rewards & Store
===========================
* Immutable point ledger and personal wallet
* Monthly allowance to give points with recognitions
* Automatic points for check-ins, achieved key results and successful objectives
* Gift store with stock and redemption approval workflow
* Leaderboard, "Top points" ranking, dashboard indicators and personal workspace tiles
* Optional inventory integration: okr_scale_reward_stock
""",
    'version': '17.0.1.1.0',
    'category': 'Human Resources/OKR',
    'author': 'DMAG',
    'license': 'LGPL-3',
    'depends': ['okr_scale_cfr', 'product'],
    'data': [
        'security/okr_reward_security.xml',
        'security/ir.model.access.csv',
        'data/okr_reward_data.xml',
        'views/okr_reward_templates.xml',
        'views/okr_point_transaction_views.xml',
        'views/okr_reward_item_views.xml',
        'views/okr_redemption_views.xml',
        'views/okr_recognition_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/okr_reward_redeem_views.xml',
        'wizard/okr_point_grant_views.xml',
        'views/okr_reward_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'okr_scale_reward/static/src/scss/okr_reward.scss',
        ],
    },
    'installable': True,
}
