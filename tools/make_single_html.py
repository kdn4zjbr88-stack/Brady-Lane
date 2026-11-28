"""Pack the pygbag web build into ONE double-clickable HTML file.

Browsers won't let a page opened from disk (file://) fetch files next to it, so the
game archive is embedded as base64 and served to the loader by a tiny fetch() shim.
The Python runtime itself still loads from the pygbag CDN, so playing needs internet.

Usage:  python tools/make_single_html.py     (needs: pip install pygbag)

Only main.py and the brady/ package are bundled (no tests, docs or old builds).
"""
import base64
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAGE = ROOT / "build" / "stage" / "brady"
OUT = ROOT / "Play Brady.html"

shutil.rmtree(STAGE, ignore_errors=True)
STAGE.mkdir(parents=True)
shutil.copy(ROOT / "main.py", STAGE / "main.py")
shutil.copytree(ROOT / "brady", STAGE / "brady", ignore=shutil.ignore_patterns("__pycache__"))
subprocess.run([sys.executable, "-m", "pygbag", "--build", str(STAGE)], check=True,
               stdout=subprocess.DEVNULL)
WEB = STAGE / "build" / "web"

html = (WEB / "index.html").read_text(encoding="utf-8")
archive = next(WEB.glob("*.tar.gz"))          # named after the project folder
payload = base64.b64encode(archive.read_bytes()).decode()
pattern = re.escape(archive.name)

shim = f"""<script>
/* Brady single-file shim: serve the embedded game archive instead of fetching it. */
(function () {{
  const b64 = "{payload}";
  const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
  const realFetch = window.fetch.bind(window);
  window.fetch = function (input, init) {{
    const url = (typeof input === "string") ? input : (input && input.url) || "";
    if (/{pattern}(\\?|#|$)/.test(url)) {{
      return Promise.resolve(new Response(bytes.slice(0), {{
        status: 200, headers: {{"Content-Type": "application/octet-stream"}}
      }}));
    }}
    return realFetch(input, init);
  }};
}})();
</script>
"""

# Keep the game at 16:9 and as big as the window allows (the stock template stretches it).
fit_css = """<style>
html, body { background: #120e18 !important; margin: 0; overflow: hidden; }
canvas.emscripten#canvas {
  width: min(100vw, calc(100vh * 16 / 9)) !important;
  height: min(100vh, calc(100vw * 9 / 16)) !important;
  top: 50% !important; left: 50% !important; right: auto !important; bottom: auto !important;
  transform: translate(-50%, -50%); margin: 0 !important;
}
</style>
"""
html = html.replace("</head>", fit_css + "</head>", 1)

head = html.find("<head>")
if head == -1:
    raise SystemExit("index.html has no <head>")
html = html[:head + len("<head>")] + "\n" + shim + html[head + len("<head>"):]
html = re.sub(r"<title>.*?</title>", "<title>Brady: Genitopia</title>", html, count=1)
OUT.write_text(html, encoding="utf-8")
SITE = ROOT / "docs" / "index.html"          # GitHub Pages serves this as the game's web link
SITE.parent.mkdir(exist_ok=True)
SITE.write_text(html, encoding="utf-8")
print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
