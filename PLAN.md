# Config Caching Migration Plan

## Already Done (Completed)
- [x] `config/__init__.py` - Central cached config module
- [x] `database/database.py` - Persistent SQLite connection
- [x] `bot.py` - Main entrypoint
- [x] `cogs/email.py` - Reference implementation
- [x] Simple cogs: check_lock, request_otp, addcredits, removecredit, leaderboard, sell_stats, goon, checkbalance, secure

## In Progress - UI Modules
- [ ] `cogs/autobuy.py` - Replace `_autobuy_cfg()` and module-level config
- [ ] `cogs/set_channel.py` - Use cached config
- [ ] `cogs/send_embed.py` - Use cached config
- [ ] `cogs/auth_code.py` - Use cached config
- [ ] `cogs/stats.py` - Use cached config
- [ ] `cogs/menu.py` - Use cached config
- [ ] `ui/buttons/autobuy.py` - Replace `_autobuy_cfg()` hot path
- [ ] `ui/modals/autobuy.py` - Replace `_autobuy_cfg()`, `_owner_ids()`, `_logs_channel_id()`
- [ ] `ui/modals/modal_one.py` - Replace inline config load
- [ ] `ui/modals/modal_two.py` - Replace inline config load
- [ ] `ui/buttons/link_account.py` - Replace `bconfig()`

## Shared Modules
- [ ] `shared/send_logs.py` - Replace inline config load
- [ ] `shared/embeds.py` - Replace inline config load
- [ ] `shared/post_verification.py` - Replace inline config load
- [ ] `shared/fetch_inbox.py` - Check if has config load

## Securing Modules
- [ ] `securing/autobuy_hold_check.py` - Replace `_load_domain()`
- [ ] `securing/account_filters.py` - Replace `_load_reject_cfg()`
- [ ] `securing/recovery_secure.py` - Replace module-level config
- [ ] `securing/utils/proxy.py` - Replace `_load_proxy_cfg()`

## Minecraft Modules
- [ ] `minecraft/get_hypixel.py` - Replace module-level config
- [ ] `minecraft/get_donut.py` - Already uses Path caching, but can use get_config

## Mail Modules
- [ ] `mail/discord_forward.py` - Replace `_load_config()`
- [ ] `mail/server.py` - Check if has config load
