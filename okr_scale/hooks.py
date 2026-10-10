def post_init_hook(env):
    env['res.users']._okr_sync_manager_group()
