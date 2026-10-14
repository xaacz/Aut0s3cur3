# Config Conversion Plan

## Pattern to apply:
Replace all module-level `json.load(open("config/config.json"))` and `json.load(open("config/bot.json"))` with cached config imports from `config` module.

Also replace inline `json.load(open(...))` calls in hot paths with cached config functions.

## Files to update:

### Cogs (module-level config + command alias lookup)
- [x] cogs/email.py (already done - reference pattern)
- [x] cogs/autobuy.py
- [ ] cogs/secure.py
- [ ] cogs/set_channel.py
- [ ] cogs/send_embed.py
- [ ] cogs/check_lock.py
- [ ] cogs/request_otp.py
- [ ] cogs/addcredits.py
- [ ] cogs/removecredit.py
- [ ] cogs/leaderboard.py
- [ ] cogs/sell_stats.py
- [ ] cogs/goon.py
- [ ] cogs/checkbalance.py
- [ ] cogs/auth_code.py
- [ ] cogs/stats.py
- [ ] cogs/menu.py (uses inline config load/save)

### Shared modules
- [ ] shared/send_logs.py
- [ ] shared/embeds.py
- [ ] shared/post_verification.py
- [ ] shared/fetch_inbox.py
- [ ] shared/post_hit.py

### UI modules
- [ ] ui/buttons/autobuy.py
- [ ] ui/buttons/link_account.py
- [ ] ui/modals/autobuy.py
- [ ] ui/modals/modal_one.py
- [ ] ui/modals/modal_two.py

### Securing modules
- [ ] securing/secure.py
- [ ] securing/recovery_secure.py
- [ ] securing/autobuy_hold_check.py
- [ ] securing/account_filters.py
- [ ] securing/utils/proxy.py

### Minecraft modules
- [ ] minecraft/get_hypixel.py
- [ ] minecraft/get_donut.py

### Mail modules
- [ ] mail/discord_forward.py
- [ ] mail/server.py

## Helper methods available in config module:
- get_config() → main config dict
- get_bot_config() → bot.json dict
- get_autobuy_config() → config["autobuy"]
- get_autosecure_config() → config["autosecure"]
- get_enabled_commands() → bot.json["enabled_commands"]
- get_command_alias(name) → alias lookup
- reload_config() → force reload on next access
- save_config(config) → save + reload
- save_bot_config(config) → save + reload