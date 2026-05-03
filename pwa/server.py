#!/usr/bin/env python3
"""
Display Format PWA Server

No external dependencies - uses Python stdlib only.

Serves the Display PWA static files from the directory this script lives in.
The display file (display.org) is served as a static file from the same directory.

The PWA fetches /display.org directly and auto-updates via SSE push or polling.

Configuration via environment variables:
  DISPLAY_FILE  - Path to the org file to serve (default: <script_dir>/display.org)
  PORT          - HTTP port to listen on (default: 8907)
  HOST          - Host to bind to (default: 0.0.0.0)

Usage:
  cd display-skills/pwa && python3 server.py

Then open http://localhost:8907 in a browser.
"""

import os
import sys
import json
import time
import mimetypes
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# --- Configuration ---
STATIC_DIR = Path(__file__).parent.resolve()
DEFAULT_DISPLAY_FILE = str(STATIC_DIR / "display.org")
DISPLAY_FILE = os.environ.get("DISPLAY_FILE", DEFAULT_DISPLAY_FILE)
PORT = int(os.environ.get("PORT", "8907"))
HOST = os.environ.get("HOST", "0.0.0.0")

# --- SSE clients ---
sse_clients = []
sse_lock = threading.Lock()

# --- File watching ---
file_mtime = 0.0
watch_lock = threading.Lock()


def get_file_mtime():
    """Get the modification time of the display file."""
    try:
        return os.path.getmtime(DISPLAY_FILE)
    except OSError:
        return 0.0


def read_display_file():
    """Read the display file contents, returning empty string if missing."""
    try:
        with open(DISPLAY_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""
    except OSError:
        return ""


def notify_sse_clients(event_type="update", data=None):
    """Send an event to all connected SSE clients."""
    if data is None:
        data = read_display_file()
    msg = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    with sse_lock:
        dead = []
        for i, client in enumerate(sse_clients):
            try:
                client.wfile.write(msg.encode("utf-8"))
                client.wfile.flush()
            except Exception:
                dead.append(i)
        for i in reversed(dead):
            sse_clients.pop(i)


def file_watcher_polling():
    """Poll-based file watcher. Checks every 0.5 seconds for mtime changes."""
    global file_mtime
    file_mtime = get_file_mtime()
    while True:
        time.sleep(0.5)
        current_mtime = get_file_mtime()
        if current_mtime != file_mtime:
            with watch_lock:
                file_mtime = current_mtime
            notify_sse_clients()


def file_watcher_inotify():
    """Inotify-based file watcher. Falls back to polling if inotify is unavailable."""
    global file_mtime
    try:
        import inotify.adapters
        import inotify.constants
    except ImportError:
        return False

    # Ensure parent directory exists so inotify can watch
    parent = os.path.dirname(DISPLAY_FILE) or str(STATIC_DIR)
    file_mtime = get_file_mtime()

    try:
        i = inotify.adapters.Inotify()
        i.add_watch(parent, mask=inotify.constants.IN_CLOSE_WRITE |
                    inotify.constants.IN_MOVED_TO | inotify.constants.IN_CREATE |
                    inotify.constants.IN_DELETE)
    except Exception:
        return False

    def _watch():
        global file_mtime
        for event in i.event_gen(yield_nones=False):
            _, event_type_names, path, filename = event
            fname = os.path.join(path, filename) if filename else path
            if os.path.abspath(fname) == os.path.abspath(DISPLAY_FILE):
                with watch_lock:
                    file_mtime = get_file_mtime()
                notify_sse_clients()

    thread = threading.Thread(target=_watch, daemon=True)
    thread.start()
    return True


class DisplayHandler(BaseHTTPRequestHandler):
    """HTTP handler for the Display PWA."""

    def log_message(self, format, *args):
        """Quiet logging - only errors."""
        if args and "200" not in str(args[0]):
            super().log_message(format, *args)

    def _send_response(self, code, content, content_type="text/html", headers=None):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        if headers:
            for k, v in headers.items():
                self.send_header(k, v)
        self.end_headers()
        if isinstance(content, str):
            content = content.encode("utf-8")
        self.wfile.write(content)

    def do_GET(self):
        path = self.path.split("?")[0]  # strip query string

        # --- SSE endpoint ---
        if path == "/api/events":
            self._handle_sse()
            return

        # --- Static file serving ---
        if path == "/":
            path = "/index.html"

        # Prevent path traversal
        safe_path = Path(STATIC_DIR / path.lstrip("/")).resolve()
        if not str(safe_path).startswith(str(STATIC_DIR)):
            self._send_response(403, "Forbidden", "text/plain")
            return

        if not safe_path.is_file():
            self._send_response(404, "Not Found", "text/plain")
            return

        content_type = mimetypes.guess_type(str(safe_path))[0] or "application/octet-stream"
        # .org files should be text/plain, not Lotus Organizer
        if safe_path.suffix == '.org':
            content_type = 'text/plain; charset=utf-8'

        try:
            with open(safe_path, "rb") as f:
                content = f.read()
        except OSError:
            self._send_response(500, "Internal Server Error", "text/plain")
            return

        # Aggressive no-cache for display.org so the PWA always gets fresh content
        headers = {}
        if safe_path.name == "display.org":
            headers["Cache-Control"] = "no-cache, no-store, must-revalidate"

        self._send_response(200, content, content_type, headers)

    def _handle_sse(self):
        """Handle Server-Sent Events connection."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        # Register this client
        with sse_lock:
            sse_clients.append(self)

        # Send initial content
        try:
            content = read_display_file()
            msg = f"event: update\ndata: {json.dumps(content)}\n\n"
            self.wfile.write(msg.encode("utf-8"))
            self.wfile.flush()
        except Exception:
            pass

        # Keep connection alive with heartbeat
        try:
            while True:
                time.sleep(15)
                self.wfile.write(b": heartbeat\n\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            with sse_lock:
                if self in sse_clients:
                    sse_clients.remove(self)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()


def main():
    # Ensure display.org exists (empty file is fine - PWA shows "Waiting for content...")
    if not os.path.exists(DISPLAY_FILE):
        Path(DISPLAY_FILE).touch()

    print(f"Display PWA Server")
    print(f"  File: {DISPLAY_FILE}")
    print(f"  URL:  http://{HOST}:{PORT}")
    print(f"  Static dir: {STATIC_DIR}")
    print()

    # Try inotify first, fall back to polling
    if not file_watcher_inotify():
        print("  inotify unavailable, using polling fallback")
        watcher = threading.Thread(target=file_watcher_polling, daemon=True)
        watcher.start()
    else:
        print("  inotify watcher active")

    server = HTTPServer((HOST, PORT), DisplayHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()