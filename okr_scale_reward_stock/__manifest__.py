{
    'name': 'OKR Scale - Reward Inventory',
    'summary': 'Manage reward store gifts in Inventory: stock levels, pre-orders and deliveries',
    'description': """
OKR Scale - Reward Inventory
============================
* "Track in inventory" on reward items: a storable product is created automatically
* Available quantity read from the warehouse (free quantity) instead of a manual counter
* Pre-orders when the gift is not in stock yet (configurable)
* An approved redemption creates a delivery order; validating one validates the other
* Rejected or cancelled redemptions cancel their delivery
""",
    'version': '17.0.1.0.0',
    'category': 'Human Resources/OKR',
    'author': 'DMAG',
    'license': 'LGPL-3',
    'depends': ['okr_scale_reward', 'stock'],
    'data': [
        'views/okr_reward_item_views.xml',
        'views/okr_redemption_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'auto_install': False,
    'installable': True,
}
