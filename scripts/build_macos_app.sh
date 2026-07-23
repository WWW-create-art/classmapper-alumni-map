#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_DIR="$ROOT_DIR/dist/同学蹭饭地图.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"

rm -rf "$APP_DIR"
rm -rf "$ROOT_DIR/dist/ClassMapper.app"
mkdir -p "$MACOS_DIR" "$RESOURCES_DIR"

cp "$ROOT_DIR/app-src/Info.plist" "$CONTENTS_DIR/Info.plist"
cp "$ROOT_DIR/app-src/launcher.zsh" "$MACOS_DIR/ClassMapper"
if [ -f "$ROOT_DIR/web-app/index.html" ]; then
  cp "$ROOT_DIR/web-app/index.html" "$RESOURCES_DIR/蹭饭地图.html"
  cp "$ROOT_DIR/web-app/manifest.webmanifest" "$RESOURCES_DIR/manifest.webmanifest"
  cp "$ROOT_DIR/web-app/sw.js" "$RESOURCES_DIR/sw.js"
  cp -R "$ROOT_DIR/web-app/assets" "$RESOURCES_DIR/assets"
else
  cp "$ROOT_DIR/蹭饭地图结果/蹭饭地图.html" "$RESOURCES_DIR/蹭饭地图.html"
fi
chmod +x "$MACOS_DIR/ClassMapper"

plutil -lint "$CONTENTS_DIR/Info.plist" >/dev/null
echo "Built $APP_DIR"
