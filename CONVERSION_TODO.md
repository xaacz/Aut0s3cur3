# Config Caching Conversion Progress

## Completed
- [x] `config/__init__.py` - already has cached config module with `get_config()`, `get_bot_config()`, `get_command_alias()`, `get_autobuy_config()`, `get_autosecure_config()`, `save_config()`, `save_bot_config()`, `reload_config()`
- [x] `securing/utils/secure.py` - replaced inline `json.load(open("config/config.json"))` with `get_config()`
- [x] `securing/utils/security/change_primary_alias.py` - replaced inline import and json.load with `get_config()`
- [x] `minecraft/check_server_ban.py` - replaced `_load_cfg()` with `get_config()`
- [x] `cogs/refresh_posts.py` - replaced `_load_bot_config()` with `get_bot_config()`
- [x] `minecraft/get_hypixel.py` - replaced module-level config with `get_config()`
- [x] `minecraft/get_donut.py` - replaced custom `_donut_key()` file read with `get_config()`
- [x] `mail/discord_forward.py` - replaced `_load_config()` with `get_config()`
- [x] `ui/modals/modal_one.py` - replaced inline config loads in callbacks
- [x] `ui/modals/modal_two.py` - replaced inline config load
- [x] `ui/buttons/link_account.py` - replaced `bconfig()` with cached `get_bot_config()`
- [x] `ui/buttons/autobuy.py` - replaced `_autobuy_cfg()` with `get_autobuy_config()`
- [x] `ui/modals/autobuy.py` - replaced `_autobuy_cfg()`, `_owner_ids()`, `_logs_channel_id()` with cached config
- [x] `shared/send_logs.py` - replaced inline config load with `get_config()`
- [x] `shared/embeds.py` - replaced inline file read with `get_bot_config()`
- [x] `shared/post_verification.py` - replaced inline file read with `get_bot_config()`
- [x] `securing/autobuy_hold_check.py` - replaced `_load_domain()` file read with `get_config()`
- [x] `securing/account_filters.py` - replaced `_load_reject_cfg()` file read with `get_autosecure_config()`
- [x] `securing/recovery_secure.py` - replaced module-level config with `get_config()`
- [x] `securing/utils/proxy.py` - replaced `_load_proxy_cfg()` file read with `get_config()`
- [x] `cogs/set_channel.py` - replaced inline config reads/writes with cached config + `save_config`
- [x] All simple cogs already updated

## Remaining Checks
- [x] Search for any remaining `open("config/config.json` patterns - found only in `CONVERSION_PLAN.md` (docs) and `config/__init__.py` (the cached module itself, which legitimately opens the file)
- [x] Search for any remaining `open("config/bot.json` patterns - found only in `CONVERSION_PLAN.md` (docs)
