#!/usr/bin/env python3
"""
AI Daily News - LAN static server (for testing the PWA on a phone)

Usage:
  python3 scripts/serve.py            # default port 8000
  python3 scripts/serve.py 9000       # custom port

Features:
  - binds 0.0.0.0 so any device on the same LAN can connect
  - correct MIME types for webmanifest / json / svg (required for the manifest)
  - no-cache headers so every refresh shows the latest changes
"""

import os
import socket
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".webmanifest": "application/manifest+json",
        ".json": "application/json",
        ".svg": "image/svg+xml",
        ".woff2": "font/woff2",
    }

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def lan_ip() -> str:
    """Return this machine's LAN IPv4 address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    os.chdir(PROJECT_DIR)

    handler = partial(Handler, directory=PROJECT_DIR)
    httpd = ThreadingHTTPServer(("0.0.0.0", port), handler)

    ip = lan_ip()
    print("=" * 52)
    print("📱 AI Daily News - LAN preview server")
    print("=" * 52)
    print(f"  This computer : http://localhost:{port}/")
    print(f"  Phone         : http://{ip}:{port}/")
    print("-" * 52)
    print("  Tip: the phone and computer must be on the same Wi-Fi.")
    print("  Note: plain HTTP on the LAN is not a secure context, so the service worker")
    print("  will not register; navigation, archive, icons and add-to-home-screen still work.")
    print("=" * 52)
    print("Press Ctrl+C to stop.")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        httpd.server_close()


if __name__ == "__main__":
    main()
