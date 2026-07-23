from __future__ import annotations

import json
import math
import shutil
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_HTML = ROOT / "蹭饭地图结果" / "蹭饭地图.html"
WEB_APP = ROOT / "web-app"
ICON_DIR = WEB_APP / "assets" / "icons"

HEAD_SNIPPET = """    <meta name="theme-color" content="#1976d2">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-title" content="同学蹭饭地图">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <link rel="manifest" href="./manifest.webmanifest">
    <link rel="apple-touch-icon" href="./assets/icons/icon-192.png">
"""

BODY_SNIPPET = """    <script>
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
                    navigator.serviceWorker.register('./sw.js').then(function(registration) {
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

    html = SOURCE_HTML.read_text(encoding="utf-8")
    html = inject_once(html, "</head>", HEAD_SNIPPET, "manifest.webmanifest")
    html = inject_once(html, "</body>", BODY_SNIPPET, "serviceWorker")
    (WEB_APP / "index.html").write_text(html, encoding="utf-8")
    (WEB_APP / ".nojekyll").write_text("", encoding="utf-8")

    write_manifest()
    write_service_worker()
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
    sw = """const CACHE_NAME = 'classmapper-pwa-v13';
const LOCAL_ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './robots.txt',
  './assets/icons/icon-192.png',
  './assets/icons/icon-512.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(LOCAL_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  if (url.origin !== location.origin || event.request.method !== 'GET') {
    return;
  }

  if (event.request.mode === 'navigate') {
    const freshRequest = new Request(event.request, { cache: 'reload' });
    event.respondWith(
      fetch(freshRequest)
        .then((response) => {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put('./index.html', copy));
          return response;
        })
        .catch(() => caches.match('./index.html'))
    );
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then((cached) => cached || fetch(event.request).then((response) => {
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
        return response;
      }))
  );
});
"""
    (WEB_APP / "sw.js").write_text(sw, encoding="utf-8")


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
