"""Local preview: serve the built site and rebuild whenever the data, templates or styles change."""

import functools
import http.server
import threading
import time
from pathlib import Path

from .content import ContentError, load_content
from .site import STATIC_DIR, build

TEMPLATES_DIR = Path(__file__).parent / "templates"


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # one line per request drowns out the rebuild messages
        pass


def serve(data_dir: Path, out: Path, port: int, *, strict: bool) -> None:
    def rebuild() -> None:
        try:
            content = load_content(data_dir, strict=strict)
            pages = build(content, out, draft=not strict)
        except ContentError as error:
            print("\n".join(["Not rebuilt:", *error.problems]))
        except OSError as error:  # e.g. Windows briefly locking a file the server is sending
            print(f"Not rebuilt, will retry on the next change: {error}")
        else:
            for warning in content.warnings:
                print(f"warning: {warning}")
            print(f"{time.strftime('%H:%M:%S')} built {pages} pages")

    rebuild()
    handler = functools.partial(_QuietHandler, directory=str(out))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"Serving http://127.0.0.1:{port}/  (Ctrl+C to stop)")

    watched = [data_dir, TEMPLATES_DIR, STATIC_DIR]
    last = _snapshot(watched)
    try:
        while True:
            time.sleep(1)
            current = _snapshot(watched)
            if current != last:
                last = current
                rebuild()
    except KeyboardInterrupt:
        server.shutdown()


def _snapshot(directories: list[Path]) -> dict[Path, float]:
    return {
        path: path.stat().st_mtime
        for directory in directories
        for path in directory.rglob("*")
        if path.is_file()
    }
