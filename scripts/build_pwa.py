from __future__ import annotations

import json
import math
import shutil
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_HTML = ROOT / "蹭饭地图结果" / "蹭饭地图.html"
SOURCE_MAP_DATA = ROOT / "蹭饭地图结果" / "map-data.json"
SOURCE_ROSTER = ROOT / "data" / "jielong.csv"
WEB_APP = ROOT / "web-app"
ICON_DIR = WEB_APP / "assets" / "icons"
DATA_DIR = WEB_APP / "data"

HEAD_SNIPPET = """    <meta http-equiv="Cache-Control" content="no-store, no-cache, must-revalidate, max-age=0">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <meta name="theme-color" content="#1976d2">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-title" content="同学蹭饭地图">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <link rel="manifest" href="./manifest.webmanifest">
    <link rel="apple-touch-icon" href="./assets/icons/icon-192.png">
"""

BODY_SNIPPET = """    <script>
        (function() {
            try {
                localStorage.removeItem('classmapper-roster-v1');
            } catch (error) {}

            if ('caches' in window) {
                caches.keys()
                    .then(function(keys) {
                        return Promise.all(keys
                            .filter(function(key) { return key.indexOf('classmapper-pwa-') === 0; })
                            .map(function(key) { return caches.delete(key); }));
                    })
                    .catch(function() {});
            }
        })();

        if ('serviceWorker' in navigator && ['http:', 'https:'].includes(location.protocol)) {
            (function() {
                var refreshing = false;

                navigator.serviceWorker.addEventListener('controllerchange', function() {
                    if (refreshing) {
                        return;
                    }
                    refreshing = true;
                    window.location.reload();
                });

                function activateWaitingWorker(registration) {
                    if (registration && registration.waiting) {
                        registration.waiting.postMessage({ type: 'SKIP_WAITING' });
                    }
                }

                window.addEventListener('load', function() {
                    navigator.serviceWorker.register('./sw.js', { updateViaCache: 'none' }).catch(function() {
                        return navigator.serviceWorker.register('./sw.js');
                    }).then(function(registration) {
                        activateWaitingWorker(registration);
                        registration.update().catch(function() {});
                        registration.addEventListener('updatefound', function() {
                            var worker = registration.installing;
                            if (!worker) {
                                return;
                            }
                            worker.addEventListener('statechange', function() {
                                if (worker.state === 'installed' && navigator.serviceWorker.controller) {
                                    worker.postMessage({ type: 'SKIP_WAITING' });
                                }
                            });
                        });
                    }).catch(function() {});
                });
            })();
        }
    </script>
"""


def main() -> None:
    if not SOURCE_HTML.exists():
        raise FileNotFoundError(f"请先生成地图文件: {SOURCE_HTML}")

    WEB_APP.mkdir(exist_ok=True)
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    html = SOURCE_HTML.read_text(encoding="utf-8")
    html = inject_once(html, "</head>", HEAD_SNIPPET, "manifest.webmanifest")
    html = inject_once(html, "</body>", BODY_SNIPPET, "serviceWorker")
    (WEB_APP / "index.html").write_text(html, encoding="utf-8")
    (WEB_APP / ".nojekyll").write_text("", encoding="utf-8")
    shutil.copy2(SOURCE_MAP_DATA, DATA_DIR / "map-data.json")
    shutil.copy2(SOURCE_ROSTER, DATA_DIR / "jielong.csv")

    write_manifest()
    write_service_worker()
    write_refresh_page()
    write_robots()
    write_icons()
    print(f"Built {WEB_APP}")


def inject_once(html: str, marker: str, snippet: str, signature: str) -> str:
    if signature in html:
        return html
    return html.replace(marker, snippet + marker, 1)


def write_manifest() -> None:
    manifest = {
        "name": "同学蹭饭地图",
        "short_name": "蹭饭地图",
        "description": "同学大学分布地图",
        "start_url": "./index.html",
        "scope": "./",
        "display": "fullscreen",
        "display_override": ["fullscreen", "standalone", "minimal-ui"],
        "background_color": "#f5f7fb",
        "theme_color": "#1976d2",
        "orientation": "any",
        "icons": [
            {
                "src": "./assets/icons/icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable",
            },
            {
                "src": "./assets/icons/icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable",
            },
        ],
    }
    (WEB_APP / "manifest.webmanifest").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_service_worker() -> None:
    sw = """const CACHE_NAME = 'classmapper-pwa-v16';
const CACHE_PREFIX = 'classmapper-pwa-';

self.addEventListener('install', (event) => {
  event.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key.startsWith(CACHE_PREFIX)).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
      .then(() => self.clients.matchAll({ type: 'window', includeUncontrolled: true }))
      .then((clients) => Promise.all(clients.map((client) => {
        if ('navigate' in client) {
          return client.navigate(client.url).catch(() => {});
        }
        return Promise.resolve();
      })))
  );
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
    return;
  }
  if (event.data && event.data.type === 'CLEAR_CLASSMAPPER_CACHE') {
    event.waitUntil(
      caches.keys()
        .then((keys) => Promise.all(keys.filter((key) => key.startsWith(CACHE_PREFIX)).map((key) => caches.delete(key))))
    );
  }
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  if (url.origin !== location.origin || event.request.method !== 'GET') {
    return;
  }

  if (url.pathname.endsWith('/data/jielong.csv') || url.pathname.endsWith('/data/map-data.json')) {
    event.respondWith(fetch(new Request(event.request, { cache: 'reload' })));
    return;
  }

  if (event.request.mode === 'navigate') {
    const freshRequest = new Request(event.request, { cache: 'reload' });
    event.respondWith(
      fetch(freshRequest)
        .catch(() => new Response('<!doctype html><meta charset="utf-8"><title>需要联网刷新</title><body style="font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;padding:24px;text-align:center;"><h3>需要联网刷新</h3><p>请连上网络后重新打开同学蹭饭地图。</p></body>', {
          headers: { 'Content-Type': 'text/html; charset=utf-8' }
        }))
    );
    return;
  }

  event.respondWith(
    fetch(new Request(event.request, { cache: 'reload' }))
  );
});
"""
    (WEB_APP / "sw.js").write_text(sw, encoding="utf-8")


def write_refresh_page() -> None:
    html = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Cache-Control" content="no-store, no-cache, must-revalidate, max-age=0">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
  <title>正在刷新同学蹭饭地图</title>
  <style>
    html, body {
      height: 100%;
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f5f7fb;
      color: #1f2937;
    }
    body {
      display: grid;
      place-items: center;
      padding: 24px;
      text-align: center;
      box-sizing: border-box;
    }
    .panel {
      max-width: 360px;
      line-height: 1.6;
    }
    .title {
      margin: 0 0 8px;
      font-size: 18px;
      font-weight: 700;
    }
    .text {
      margin: 0;
      font-size: 14px;
      color: #4b5563;
    }
  </style>
</head>
<body>
  <div class="panel">
    <p class="title">正在切到最新版</p>
    <p class="text">会自动清理旧缓存，然后重新打开地图。</p>
  </div>
  <script>
    (async function() {
      try {
        localStorage.removeItem('classmapper-roster-v1');
      } catch (error) {}

      try {
        if ('caches' in window) {
          const keys = await caches.keys();
          await Promise.all(keys
            .filter((key) => key.indexOf('classmapper-pwa-') === 0)
            .map((key) => caches.delete(key)));
        }
      } catch (error) {}

      try {
        if ('serviceWorker' in navigator) {
          const registrations = await navigator.serviceWorker.getRegistrations();
          await Promise.all(registrations.map((registration) => registration.unregister()));
        }
      } catch (error) {}

      window.location.replace('./?fresh=' + Date.now());
    })();
  </script>
</body>
</html>
"""
    (WEB_APP / "refresh.html").write_text(html, encoding="utf-8")


def write_robots() -> None:
    (WEB_APP / "robots.txt").write_text(
        "User-agent: *\nDisallow: /\n",
        encoding="utf-8",
    )


def write_icons() -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont

        for size in (192, 512):
            image = Image.new("RGB", (size, size), "#1976d2")
            draw = ImageDraw.Draw(image)
            draw.rounded_rectangle(
                [size * 0.13, size * 0.13, size * 0.87, size * 0.87],
                radius=int(size * 0.17),
                fill="#ffffff",
            )
            draw.ellipse(
                [size * 0.38, size * 0.2, size * 0.62, size * 0.44],
                fill="#1976d2",
            )
            draw.polygon(
                [
                    (size * 0.5, size * 0.78),
                    (size * 0.29, size * 0.42),
                    (size * 0.71, size * 0.42),
                ],
                fill="#1976d2",
            )
            font = find_font(size)
            if font:
                text = "蹭"
                bbox = draw.textbbox((0, 0), text, font=font)
                draw.text(
                    ((size - bbox[2] + bbox[0]) / 2, size * 0.49),
                    text,
                    fill="#ffffff",
                    font=font,
                    anchor="mm",
                )
            image.save(ICON_DIR / f"icon-{size}.png")
    except Exception:
        for size in (192, 512):
            write_simple_png(ICON_DIR / f"icon-{size}.png", size, size, (25, 118, 210))


def find_font(size: int):
    try:
        from PIL import ImageFont
    except Exception:
        return None

    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Supplemental/Songti.ttc",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, int(size * 0.28))
    return None


def write_simple_png(path: Path, width: int, height: int, color: tuple[int, int, int]) -> None:
    row = bytes(color) * width
    raw = b"".join(b"\x00" + row for _ in range(height))
    compressor = zlib.compressobj()
    data = compressor.compress(raw) + compressor.flush()

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            len(payload).to_bytes(4, "big")
            + kind
            + payload
            + zlib.crc32(kind + payload).to_bytes(4, "big")
        )

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", width.to_bytes(4, "big") + height.to_bytes(4, "big") + b"\x08\x02\x00\x00\x00")
    png += chunk(b"IDAT", data)
    png += chunk(b"IEND", b"")
    path.write_bytes(png)


if __name__ == "__main__":
    main()
