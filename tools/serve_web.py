"""Serve the pygbag web build (build/web) and forward /cdn/* to the pygbag CDN.

When the page is opened from localhost, pygbag's loader fetches its runtime from
/cdn/ on the same server, so we relay those requests (and cache them on disk).

Usage:  python -m pygbag --build .   then   python tools/serve_web.py [port]
"""
import http.server
import os
import ssl
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "build" / "web"
CACHE = ROOT.parent / "cdn-cache"
CDN = "https://pygame-web.github.io/cdn/"

ctx = ssl.create_default_context()
for bundle in (os.environ.get("SSL_CERT_FILE"), "/root/.ccr/ca-bundle.crt"):
    if bundle and os.path.exists(bundle):
        ctx.load_verify_locations(bundle)
opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def do_GET(self):
        if not self.path.startswith("/cdn/"):
            return super().do_GET()
        rel = self.path[5:].split("#")[0].split("?")[0].lstrip("/")
        cached = CACHE / rel
        if not cached.is_file():
            try:
                with opener.open(CDN + rel, timeout=60) as r:
                    data = r.read()
            except Exception as e:  # noqa: BLE001
                self.send_error(404, f"CDN fetch failed: {e}")
                return
            cached.parent.mkdir(parents=True, exist_ok=True)
            cached.write_bytes(data)
        data = cached.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", self.guess_type(str(cached)))
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


Handler.extensions_map.update({".wasm": "application/wasm", ".js": "text/javascript",
                               ".apk": "application/octet-stream"})

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"Serving {ROOT} on http://localhost:{port}/")
    http.server.ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
