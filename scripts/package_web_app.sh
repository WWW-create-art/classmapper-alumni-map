#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT="$ROOT/dist/classmapper-alumni-map-web-app.zip"
TEMP_OUTPUT="$ROOT/dist/classmapper-alumni-map-web-app.$$.zip"

if [ -x "$ROOT/.venv/bin/python" ]; then
  PYTHON="$ROOT/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
else
  PYTHON="python"
fi

mkdir -p "$ROOT/dist"
"$PYTHON" "$ROOT/scripts/build_pwa.py"

(
  cd "$ROOT/web-app"
  zip -qr "$TEMP_OUTPUT" .
)

mv "$TEMP_OUTPUT" "$OUTPUT"

echo "Built $OUTPUT"
