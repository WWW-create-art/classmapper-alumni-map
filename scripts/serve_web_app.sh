#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${1:-8080}"

if [ ! -f "$ROOT_DIR/web-app/index.html" ]; then
  PYTHON="$ROOT_DIR/.venv/bin/python"
  if [ ! -x "$PYTHON" ]; then
    PYTHON="python3"
  fi
  "$PYTHON" "$ROOT_DIR/scripts/build_pwa.py"
fi

LAN_IP="$(ipconfig getifaddr en0 2>/dev/null || true)"
if [ -z "$LAN_IP" ]; then
  LAN_IP="$(ipconfig getifaddr en1 2>/dev/null || true)"
fi

echo "电脑打开: http://localhost:$PORT/"
if [ -n "$LAN_IP" ]; then
  echo "手机同一 Wi-Fi 打开: http://$LAN_IP:$PORT/"
fi
echo "按 Ctrl+C 停止服务"

cd "$ROOT_DIR/web-app"
python3 -m http.server "$PORT" --bind 0.0.0.0
