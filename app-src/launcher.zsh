#!/bin/zsh
set -euo pipefail

SCRIPT_PATH="${0:A}"
MACOS_DIR="${SCRIPT_PATH:h}"
CONTENTS_DIR="${MACOS_DIR:h}"
MAP_FILE="$CONTENTS_DIR/Resources/蹭饭地图.html"

MAP_URL="$(/usr/bin/python3 -c 'import pathlib, sys; print(pathlib.Path(sys.argv[1]).resolve().as_uri())' "$MAP_FILE")"

for BROWSER in "Google Chrome" "Microsoft Edge" "Brave Browser" "Chromium"; do
  if /usr/bin/osascript -e "id of application \"$BROWSER\"" >/dev/null 2>&1; then
    /usr/bin/open -na "$BROWSER" --args --app="$MAP_URL"
    exit 0
  fi
done

/usr/bin/open "$MAP_URL"
