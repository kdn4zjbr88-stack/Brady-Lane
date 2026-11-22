"""Pack the pygbag web build into ONE double-clickable HTML file.

Browsers won't let a page opened from disk (file://) fetch files next to it, so the
game archive is embedded as base64 and served to the loader by a tiny fetch() shim.
The Python runtime itself still loads from the pygbag CDN, so playing needs internet.

Usage:  python -m pygbag --build .   then   python tools/make_single_html.py
"""
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "build" / "web"
OUT = ROOT / "Play Brady.html"

html = (WEB / "index.html").read_text(encoding="utf-8")
payload = base64.b64encode((WEB / "brady.tar.gz").read_bytes()).decode()

shim = f"""<script>
/* Brady single-file shim: serve the embedded game archive instead of fetching it. */
(function () {{
  const b64 = "{payload}";
  const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
  const realFetch = window.fetch.bind(window);
  window.fetch = function (input, init) {{
    const url = (typeof input === "string") ? input : (input && input.url) || "";
    if (/brady\\.tar\\.gz(\\?|#|$)/.test(url)) {{
      return Promise.resolve(new Response(bytes.slice(0), {{
        status: 200, headers: {{"Content-Type": "application/octet-stream"}}
      }}));
    }}
    return realFetch(input, init);
  }};
}})();
</script>
"""

head = html.find("<head>")
if head == -1:
    raise SystemExit("index.html has no <head>")
html = html[:head + len("<head>")] + "\n" + shim + html[head + len("<head>"):]
html = html.replace("<title>brady</title>", "<title>Brady: Genitopia</title>")
OUT.write_text(html, encoding="utf-8")
print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
