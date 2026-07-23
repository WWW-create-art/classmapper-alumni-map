from __future__ import annotations

import base64
import mimetypes
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB_APP = ROOT / "web-app"
DIST = ROOT / "dist"
OUTPUT = DIST / "同学蹭饭地图-同学版.html"


def main() -> None:
    html = (WEB_APP / "index.html").read_text(encoding="utf-8")
    html = make_viewer_only(html)
    html = inline_leaflet_css(html)
    html = inline_leaflet_js(html)
    DIST.mkdir(exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Built {OUTPUT}")


def make_viewer_only(html: str) -> str:
    html = re.sub(
        r'\s*<button type="button" id="adminToggleBtn" aria-pressed="false">管理</button>',
        "",
        html,
        count=1,
    )
    html = re.sub(r'\s*<button[^>]*id="viewerDocBtn"[^>]*>文档</button>', "", html, count=1)
    html = re.sub(
        r'\s*<section class="admin-panel" id="adminPanel" hidden>[\s\S]*?</section>',
        "",
        html,
        count=1,
    )
    html = remove_inline_scripts_containing(html, ["serviceWorker.register"])
    html = strip_admin_javascript(html)
    return html


def remove_inline_scripts_containing(html: str, needles: list[str]) -> str:
    script_pattern = re.compile(r"\s*<script(?![^>]*\bsrc=)[^>]*>[\s\S]*?</script>")

    def replace(match: re.Match[str]) -> str:
        block = match.group(0)
        if "let mapData =" in block and "function initMap" in block:
            return block
        if any(needle in block for needle in needles):
            return ""
        return block

    return script_pattern.sub(replace, html)


def strip_admin_javascript(html: str) -> str:
    html = re.sub(r"\n\s*const ADMIN_KEY = 'classmapper-admin-v1';", "", html)
    html = re.sub(r"\n\s*const ADMIN_PASSWORD_SHA256 = .*?;", "", html)
    html = re.sub(r"\n\s*const ADMIN_PASSWORD_LEGACY_HASH = .*?;", "", html)
    html = re.sub(r"\n\s*const GITHUB_PUBLISH_CONFIG = .*?;", "", html)

    admin_bindings = [
        r"\n\s*bindClick\('adminToggleBtn', toggleAdminPanel\);",
        r"\n\s*bindClick\('closeAdminBtn', closeAdminPanel\);",
        r"\n\s*bindSubmit\('loginForm', handleLogin\);",
        r"\n\s*bindClick\('lockAdminBtn', lockAdmin\);",
        r"\n\s*bindSubmit\('recordForm', saveRecord\);",
        r"\n\s*bindClick\('clearEditBtn', clearEditForm\);",
        r"\n\s*bindInput\('nameInput', updateNamePrivacyPreview\);",
        r"\n\s*bindClick\('appendImportBtn', function\(\) \{[\s\S]*?\n\s*\}\);",
        r"\n\s*bindClick\('replaceImportBtn', function\(\) \{[\s\S]*?\n\s*\}\);",
        r"\n\s*bindClick\('exportCsvBtn', exportCsv\);",
        r"\n\s*bindClick\('publishOnlineBtn', publishRosterOnline\);",
        r"\n\s*bindClick\('resetRosterBtn', resetRoster\);",
        r"\n\s*bindClick\('recordList', handleRecordAction\);",
        r"\n\s*bindClick\('viewerDocBtn', downloadViewerDocument\);",
        r"\n\s*renderSchoolOptions\(\);",
        r"\n\s*updateAdminUi\(\);",
    ]
    for pattern in admin_bindings:
        html = re.sub(pattern, "", html, count=1)

    html = re.sub(r"\n\s*renderAdminList\(\);", "", html)
    html = re.sub(r"\n\s*setAdminMessage\(getRosterSummary\(\)\);", "", html)
    return html


def inline_leaflet_css(html: str) -> str:
    css_path = WEB_APP / "assets" / "vendor" / "leaflet" / "leaflet.min.css"
    css = css_path.read_text(encoding="utf-8")
    css = inline_css_urls(css, css_path.parent)
    tag_pattern = re.compile(
        r'\s*<link rel="stylesheet" href="\./assets/vendor/leaflet/leaflet\.min\.css" />'
    )
    return tag_pattern.sub(lambda _: f"\n    <style>\n{css}\n    </style>", html, count=1)


def inline_leaflet_js(html: str) -> str:
    js = (WEB_APP / "assets" / "vendor" / "leaflet" / "leaflet.min.js").read_text(encoding="utf-8")
    js = js.replace("</script", "<\\/script")
    tag_pattern = re.compile(
        r'\s*<script src="\./assets/vendor/leaflet/leaflet\.min\.js"></script>'
    )
    return tag_pattern.sub(lambda _: f"\n    <script>\n{js}\n    </script>", html, count=1)


def inline_css_urls(css: str, base_dir: Path) -> str:
    def replace(match: re.Match[str]) -> str:
        raw_path = match.group(1).strip("\"'")
        if raw_path.startswith(("data:", "http:", "https:", "#")):
            return match.group(0)
        asset_path = (base_dir / raw_path).resolve()
        if not asset_path.exists():
            return match.group(0)
        mime_type = mimetypes.guess_type(asset_path.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(asset_path.read_bytes()).decode("ascii")
        return f"url(data:{mime_type};base64,{encoded})"

    return re.sub(r"url\(([^)]+)\)", replace, css)


if __name__ == "__main__":
    main()
