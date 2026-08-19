#!/usr/bin/env python3
"""设计工坊静态服。扫描 series/*.yaml 出目录。只服务本夹。引擎不读。"""
from __future__ import annotations

import json
import re
import sys
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = 18765
ID_RE = re.compile(r"^[a-z][a-z0-9-]{1,47}$")


def grab(text: str, key: str) -> str:
    match = re.search(rf"^{key}:\s*(.+)$", text, re.M)
    if not match:
        return ""
    return match.group(1).strip().strip("\"'")


def face_slots() -> dict[str, int]:
    out: dict[str, int] = {}
    for pkt in ROOT.glob("page-*/packet.yaml"):
        text = pkt.read_text(encoding="utf-8")
        pid = grab(text, "id") or pkt.parent.name
        count = grab(text, "slotCount")
        if count.isdigit():
            out[pid] = int(count)
    return out


def parse_book(path: Path, slots: dict[str, int]) -> dict | None:
    text = path.read_text(encoding="utf-8")
    if not re.search(r"(?:^|\n)kind:\s*series\b", text):
        return None
    book_id = grab(text, "id")
    stem = path.stem
    if not book_id or book_id != stem or not ID_RE.match(book_id):
        return None
    page_count = int(grab(text, "pageCount") or "0") or 1
    density = grab(text, "density") or "standard"
    status = grab(text, "status") or "sketch"
    span_m = re.search(r"photo_span:\s*\[\s*(\d+)\s*,\s*(\d+)\s*\]", text)
    photo_span = [int(span_m.group(1)), int(span_m.group(2))] if span_m else [page_count * 3, page_count * 5]
    faces = re.findall(r"faceHint:\s*([a-z0-9-]+)", text)
    return {
        "id": book_id,
        "pageCount": page_count,
        "density": density,
        "status": status,
        "pages": len(faces),
        "slots": sum(slots.get(face, 0) for face in faces),
        "photoSpan": photo_span,
    }


def list_books() -> list[dict]:
    slots = face_slots()
    books = []
    for path in sorted((ROOT / "series").glob("*.yaml")):
        book = parse_book(path, slots)
        if book:
            books.append(book)
    return books


class Server(ThreadingHTTPServer):
    allow_reuse_address = False


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("备用库 %s\n" % (fmt % args))

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path == "/series/index.json":
            body = json.dumps({"books": list_books()}, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()


def main() -> None:
    httpd = None
    port = PORT
    for candidate in range(PORT, PORT + 10):
        try:
            httpd = Server(("127.0.0.1", candidate), Handler)
            port = candidate
            break
        except OSError:
            continue
    if httpd is None:
        raise SystemExit("无法绑定 127.0.0.1:18765–18774")
    url = f"http://127.0.0.1:{port}/gallery.html#tab=bind"
    print(f"备用库样例柜 {url}", flush=True)
    print("目录 GET /series/index.json · 引擎不读 · Ctrl+C 结束", flush=True)
    threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停", flush=True)


if __name__ == "__main__":
    main()
