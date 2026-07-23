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
    <style>
        .pwa-install-panel {
            position: fixed;
            top: 50%;
            left: 50%;
            z-index: 2200;
            display: none;
            width: min(360px, calc(100% - 32px));
            transform: translate(-50%, -50%);
            align-items: stretch;
            flex-direction: column;
            gap: 10px;
            padding: 14px;
            color: #172033;
            background: rgba(255, 255, 255, 0.95);
            border: 1px solid rgba(28, 40, 58, 0.13);
            border-radius: 8px;
            box-shadow: 0 18px 46px rgba(21, 35, 53, 0.24);
            backdrop-filter: blur(10px);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        .pwa-install-panel.is-visible {
            display: flex;
        }

        .pwa-install-panel__copy {
            flex: 1 1 auto;
            min-width: 0;
            line-height: 1.35;
        }

        .pwa-install-panel__title {
            display: block;
            font-size: 14px;
            font-weight: 800;
        }

        .pwa-install-panel__note {
            display: block;
            margin-top: 2px;
            font-size: 12px;
            color: #536072;
        }

        .pwa-install-panel__actions {
            flex: 0 0 auto;
            display: grid;
            grid-template-columns: 1fr 1fr 34px;
            gap: 6px;
        }

        .pwa-install-panel button {
            min-height: 34px;
            border: 0;
            border-radius: 7px;
            padding: 0 10px;
            color: #fff;
            background: #1976d2;
            font-size: 13px;
            font-weight: 800;
        }

        .pwa-install-panel button.secondary {
            color: #1f2a3a;
            background: #edf2f7;
        }

        .pwa-install-panel button.close {
            width: 34px;
            padding: 0;
            color: #536072;
            background: transparent;
            font-size: 22px;
            line-height: 1;
        }

        @media (max-width: 430px) {
            .pwa-install-panel__actions {
                grid-template-columns: 1fr 1fr 34px;
            }
        }
    </style>
"""

BODY_SNIPPET = """    <div id="pwaInstallPanel" class="pwa-install-panel" role="dialog" aria-live="polite" aria-label="全屏打开">
        <span class="pwa-install-panel__copy">
            <strong class="pwa-install-panel__title">全屏打开</strong>
            <span class="pwa-install-panel__note" id="pwaInstallNote">点全屏可立即隐藏浏览器栏，安装后从图标进入更像应用。</span>
        </span>
        <span class="pwa-install-panel__actions">
            <button type="button" id="pwaInstallBtn">安装</button>
            <button type="button" id="pwaFullscreenBtn" class="secondary">全屏</button>
            <button type="button" id="pwaDismissBtn" class="close" aria-label="关闭">×</button>
        </span>
    </div>
    <script>
        if ('serviceWorker' in navigator && ['http:', 'https:'].includes(location.protocol)) {
            window.addEventListener('load', function() {
                navigator.serviceWorker.register('./sw.js').catch(function() {});
            });
        }

        (function() {
            var panel = document.getElementById('pwaInstallPanel');
            var installBtn = document.getElementById('pwaInstallBtn');
            var fullscreenBtn = document.getElementById('pwaFullscreenBtn');
            var dismissBtn = document.getElementById('pwaDismissBtn');
            var note = document.getElementById('pwaInstallNote');
            var deferredInstallPrompt = null;
            var dismissedKey = 'classmapper-pwa-install-dismissed';
            var isiOS = /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
            var isAndroid = /Android/i.test(navigator.userAgent);
            var restoreTimer = 0;

            function isAppMode() {
                return window.matchMedia('(display-mode: fullscreen)').matches ||
                    window.matchMedia('(display-mode: standalone)').matches ||
                    window.navigator.standalone === true;
            }

            function isFullscreenActive() {
                return !!(document.fullscreenElement || document.webkitFullscreenElement);
            }

            function canRequestFullscreen() {
                var root = document.documentElement;
                return !!(root.requestFullscreen || root.webkitRequestFullscreen);
            }

            function updatePanel(reason) {
                if (!panel || isAppMode() || isFullscreenActive() || sessionStorage.getItem(dismissedKey) === '1') {
                    if (panel) {
                        panel.classList.remove('is-visible');
                    }
                    return;
                }
                if (!isAndroid && !isiOS && !deferredInstallPrompt) {
                    return;
                }

                installBtn.style.display = '';
                fullscreenBtn.style.display = '';
                installBtn.textContent = '安装';
                note.textContent = reason === 'restore'
                    ? '刚刚退出了全屏，点一下可以回到全屏。安装后更稳定。'
                    : '点全屏可立即隐藏浏览器栏，安装后从图标进入更像应用。';
                if (isiOS && !deferredInstallPrompt) {
                    note.textContent = '在 Safari 里点分享，再选“添加到主屏幕”。';
                    installBtn.textContent = '知道了';
                } else if (!deferredInstallPrompt) {
                    installBtn.style.display = 'none';
                }
                if (!canRequestFullscreen()) {
                    fullscreenBtn.style.display = 'none';
                }
                panel.classList.add('is-visible');
            }

            function schedulePanelUpdate(reason) {
                window.clearTimeout(restoreTimer);
                restoreTimer = window.setTimeout(function() {
                    updatePanel(reason);
                }, reason === 'restore' ? 450 : 900);
            }

            window.addEventListener('beforeinstallprompt', function(event) {
                event.preventDefault();
                deferredInstallPrompt = event;
                updatePanel();
            });

            document.addEventListener('fullscreenchange', function() {
                if (isFullscreenActive()) {
                    panel.classList.remove('is-visible');
                } else {
                    schedulePanelUpdate('restore');
                }
            });

            document.addEventListener('webkitfullscreenchange', function() {
                if (isFullscreenActive()) {
                    panel.classList.remove('is-visible');
                } else {
                    schedulePanelUpdate('restore');
                }
            });

            window.addEventListener('pageshow', function() {
                schedulePanelUpdate();
            });

            document.addEventListener('visibilitychange', function() {
                if (!document.hidden) {
                    schedulePanelUpdate();
                }
            });

            if (installBtn) {
                installBtn.addEventListener('click', function() {
                    if (deferredInstallPrompt) {
                        deferredInstallPrompt.prompt();
                        deferredInstallPrompt.userChoice.finally(function() {
                            deferredInstallPrompt = null;
                            panel.classList.remove('is-visible');
                        });
                    } else {
                        sessionStorage.setItem(dismissedKey, '1');
                        panel.classList.remove('is-visible');
                    }
                });
            }

            if (fullscreenBtn) {
                fullscreenBtn.addEventListener('click', function() {
                    var root = document.documentElement;
                    var request = root.requestFullscreen || root.webkitRequestFullscreen;
                    if (request) {
                        try {
                            var result = request.call(root);
                            if (result && result.catch) {
                                result.catch(function() {});
                            }
                        } catch (error) {}
                    }
                    panel.classList.remove('is-visible');
                });
            }

            if (dismissBtn) {
                dismissBtn.addEventListener('click', function() {
                    sessionStorage.setItem(dismissedKey, '1');
                    panel.classList.remove('is-visible');
                });
            }

            schedulePanelUpdate();
        })();
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
    sw = """const CACHE_NAME = 'classmapper-pwa-v4';
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

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  if (url.origin !== location.origin || event.request.method !== 'GET') {
    return;
  }

  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
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
