#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

fuser -k 25/tcp 2>/dev/null || true

echo "[*] Starting Discord bot..."
"$ROOT/.venv/bin/python" "$ROOT/bot.py"
