#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$ROOT_DIR/.venv/bin/python"
if [ ! -x "$PYTHON" ]; then
  PYTHON="python3"
fi

cd "$ROOT_DIR"
"$PYTHON" main.py data/jielong.csv --no-open
"$PYTHON" scripts/build_pwa.py
bash scripts/build_macos_app.sh
rm -f dist/classmapper-pwa.zip
(cd web-app && zip -qr ../dist/classmapper-pwa.zip .)
