#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

cd "$ROOT"

if [[ ! -f config/config.json ]]; then
  if [[ -f config/config.json.example ]]; then
    cp config/config.json.example config/config.json
    echo "[*] Created config/config.json from config.json.example"
    echo "    Edit it now: bot token, owners, domain, mail webhooks."
    echo "    Then re-run ./setup.sh"
    exit 1
  fi
  echo "Missing config/config.json and config/config.json.example"
  exit 1
fi

if [[ ! -f config/bot.json && -f config/bot.json.example ]]; then
  cp config/bot.json.example config/bot.json
  echo "[*] Created config/bot.json from bot.json.example"
fi

# Prefer python3.12+, fall back to python3
PY="${PYTHON:-}"
if [[ -z "$PY" ]]; then
  if command -v python3.12 >/dev/null 2>&1; then PY=python3.12
  elif command -v python3.14 >/dev/null 2>&1; then PY=python3.14
  else PY=python3
  fi
fi

if [[ ! -d .venv ]]; then
  "$PY" -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi

echo "[*] Starting Discord bot with PM2..."
pm2 start ecosystem.config.cjs

echo
echo "[+] AutoSecure Bot is running."
echo "    Logs:     pm2 logs"
echo "    Status:   pm2 status"
echo
echo "Before the bot works, edit config/config.json with your Discord bot token and owner ID."
