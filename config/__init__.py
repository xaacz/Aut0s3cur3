"""Centralized config access with in-memory caching.

All modules should use ``get_config()`` / ``get_bot_config()`` instead of
``json.load(open("config/config.json"))`` to avoid repeated file I/O on every
call.  The cache auto-refreshes when the file mtime changes so on-disk edits
(e.g. from the web dashboard) are picked up without a restart.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Callable

_CONFIG_DIR = Path("config")
_CONFIG_PATH = _CONFIG_DIR / "config.json"
_BOT_PATH = _CONFIG_DIR / "bot.json"

_lock = threading.Lock()

# Cache entries: (data, mtime, inode_mtime)
_config_cache: dict[str, tuple[Any, float]] | None = None
_bot_cache: tuple[Any, float] | None = None


def _load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _has_changed(path: Path, cached_mtime: float | None) -> bool:
    try:
        return path.stat().st_mtime > (cached_mtime or 0.0)
    except OSError:
        return True


def get_config() -> dict:
    """Return the main config dict, cached and auto-refreshed on file change."""
    global _config_cache
    with _lock:
        if _config_cache is None or _config_cache["mtime"] is None or _has_changed(_CONFIG_PATH, _config_cache["mtime"]):
            _config_cache = {"data": _load_json(_CONFIG_PATH), "mtime": _CONFIG_PATH.stat().st_mtime}
        return _config_cache["data"]


def get_bot_config() -> dict:
    """Return the bot.json config dict, cached and auto-refreshed on file change."""
    global _bot_cache
    with _lock:
        cached = _bot_cache
        if cached is None or _has_changed(_BOT_PATH, cached[1]):
            data = _load_json(_BOT_PATH)
            _bot_cache = (data, _BOT_PATH.stat().st_mtime)
            return data
        return cached[0]


def get_autobuy_config() -> dict:
    """Shortcut for config.get('autobuy') or {}."""
    return get_config().get("autobuy") or {}


def get_autosecure_config() -> dict:
    """Shortcut for config.get('autosecure') or {}."""
    return get_config().get("autosecure") or {}


def get_enabled_commands() -> dict:
    """Shortcut for bot.json enabled_commands."""
    return get_bot_config().get("enabled_commands", {})


def get_command_alias(name: str) -> str:
    """Get the alias for a command name from bot.json."""
    return get_enabled_commands().get("aliases", {}).get(name, name)


def reload_config() -> None:
    """Force a reload of both config files on next access.

    Call this after writing changes to config files (e.g. /set channel command).
    """
    global _config_cache, _bot_cache
    with _lock:
        _config_cache = None
        _bot_cache = None


def save_config(config: dict) -> None:
    """Write config dict to disk and invalidate cache."""
    with _lock:
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
            f.write("\n")
    reload_config()


def save_bot_config(config: dict) -> None:
    """Write bot.json dict to disk and invalidate cache."""
    with _lock:
        with open(_BOT_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
            f.write("\n")
    reload_config()
