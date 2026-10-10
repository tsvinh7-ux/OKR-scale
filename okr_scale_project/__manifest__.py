{
    'name': 'OKR Scale - Project',
    'summary': 'Measure key results from project tasks',
    'description': """
OKR Scale - Project
===================
* Link key results to projects and tasks
* Key result progress computed from completed tasks (count or allocated hours)
* OKR smart button on projects, key result field on tasks
* "Linked tasks done" KPI on the OKR dashboard
""",
    'version': '17.0.1.0.0',
    'category': 'Human Resources/OKR',
    'author': 'DMAG',
    'license': 'LGPL-3',
    'depends': ['okr_scale', 'project'],
    'data': [
        'views/okr_key_result_views.xml',
        'views/project_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
