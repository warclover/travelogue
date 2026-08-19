#!/usr/bin/env python3
"""设计工坊静态服。扫描 series/*.yaml 与 page-*/packet.yaml。只服务本夹。引擎不读。"""
from __future__ import annotations

import json
import re
import sys
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
PORT = 18765
ID_RE = re.compile(r"^[a-z][a-z0-9-]{1,47}$")
PAGE_ID_RE = re.compile(r"^page-(\d+)-[a-z0-9-]+$")
PROGRAMS = ("opener", "hero", "mosaic", "grid", "breath", "peak", "closer")
ORIENTS = ("portrait", "landscape", "square")


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


def parse_mix(text: str) -> dict[str, int]:
    raw = re.search(r"^mix:\s*\{([^}]*)\}", text, re.M)
    out = {"portrait": 0, "landscape": 0, "square": 0}
    if not raw:
        return out
    for key in out:
        hit = re.search(rf"{key}:\s*(\d+)", raw.group(1))
        if hit:
            out[key] = int(hit.group(1))
    return out


def parse_orients(text: str) -> list[str]:
    found = re.findall(r"orient:\s*(portrait|landscape|square)", text)
    return found or []


def badge_of(mix: dict[str, int]) -> str:
    parts = []
    if mix.get("portrait"):
        parts.append(f"{mix['portrait']}P")
    if mix.get("landscape"):
        parts.append(f"{mix['landscape']}L")
    if mix.get("square"):
        parts.append(f"{mix['square']}S")
    return "".join(parts) or "?"


def even_slots(orients: list[str]) -> list[dict]:
    n = max(1, len(orients))
    gap = 1.5
    margin = 5.0
    inner = 100.0 - margin * 2 - gap * (n - 1)
    width = inner / n
    boxes = []
    for i, orient in enumerate(orients):
        if orient == "portrait":
            height = min(90.0, width * (64.0 / 27.0))
        elif orient == "landscape":
            height = min(90.0, width * (4.0 / 3.0))
        else:
            height = min(90.0, width * (16.0 / 9.0))
        boxes.append({
            "left": round(margin + i * (width + gap), 4),
            "top": round((100.0 - height) / 2.0, 4),
            "width": round(width, 4),
            "height": round(height, 4),
            "orient": orient,
        })
    return boxes


def scan_face(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    pid = grab(text, "id") or path.parent.name
    if not PAGE_ID_RE.match(pid) or pid != path.parent.name:
        return None
    mix = parse_mix(text)
    orients = parse_orients(text)
    if not orients:
        orients = (
            ["portrait"] * mix["portrait"]
            + ["landscape"] * mix["landscape"]
            + ["square"] * mix["square"]
        )
    slot_count = int(grab(text, "slotCount") or "0") or len(orients)
    return {
        "id": pid,
        "displayName": grab(text, "displayName") or pid,
        "status": grab(text, "status") or "sketch",
        "badge": grab(text, "badge") or badge_of(mix),
        "role": grab(text, "role") or pid,
        "program": grab(text, "program") or "mosaic",
        "familyId": grab(text, "familyId") or pid,
        "slotCount": slot_count,
        "mix": mix,
        "hasSketch": (path.parent / "sketch.png").is_file(),
        "hasUsage": (path.parent / "USAGE.md").is_file(),
        "fromScan": True,
        "slots": even_slots(orients),
    }


def list_faces() -> list[dict]:
    faces = []
    for path in sorted(ROOT.glob("page-*/packet.yaml")):
        face = scan_face(path)
        if face:
            faces.append(face)
    return faces


def usage_md(data: dict, badge: str, mix: dict[str, int]) -> str:
    pid = data["id"]
    return (
        f"# 使用说明 · `{pid}`\n\n"
        f"本页由 [packet.yaml](./packet.yaml) 投影，不另写散文。"
        f"示意图：缺则导出页型包硬拒。微缩：[../gallery.html](../gallery.html)。\n\n"
        f"| 项 | 内容 |\n|----|------|\n"
        f"| **备用 id** | `{pid}` |\n"
        f"| **中文名** | {data['displayName']} |\n"
        f"| **状态** | `sketch` · 工坊草案 |\n"
        f"| **账徽** | `{badge}` |\n"
        f"| **槽账** | {data['slotCount']} 槽 · 竖 {mix['portrait']} · 横 {mix['landscape']} · 方 {mix['square']} |\n"
        f"| **舞台** | 16:9 |\n"
        f"| **裁切** | 相对该槽三条；朝向不符禁入 |\n"
        f"| **何时用** | {data['whenToUse']} |\n"
        f"| **何时不用** | {data['whenNotToUse']} |\n"
        f"| **角色 / 纲领** | `{data['role']}` / `{data['program']}` |\n"
    )


def packet_yaml(data: dict, badge: str, mix: dict[str, int], orients: list[str]) -> str:
    slot_lines = []
    for i, orient in enumerate(orients):
        aspect = {"portrait": "3:4", "landscape": "4:3", "square": "1:1"}[orient]
        slot_lines.append(
            f"  - {{ index: {i}, role: {orient}, orient: {orient}, aspect: \"{aspect}\" }}"
        )
    return "\n".join([
        "# 设计工坊数据包 · 非正式合同。引擎不读。",
        f"id: {data['id']}",
        "version: 1",
        "status: sketch",
        "kind: primitive",
        f"displayName: {data['displayName']}",
        f"familyId: {data['familyId']}",
        f"canonical: {data['id']}",
        "related: []",
        "replaces: null",
        f"program: {data['program']}",
        "densityClass: standard",
        f"role: {data['role']}",
        "stage:",
        "  aspect: \"16:9\"",
        f"slotCount: {data['slotCount']}",
        f"mix: {{ portrait: {mix['portrait']}, landscape: {mix['landscape']}, square: {mix['square']} }}",
        "slots:",
        *slot_lines,
        "copyRegions: []",
        "fitPolicy: relative-to-slot",
        "glyph:",
        f"  badge: {badge}",
        "  thumb: 扫夹均分草案，不是审过的几何",
        "sourceSketch: sketch.png",
        "",
    ])


def append_catalog(data: dict, badge: str, mix: dict[str, int]) -> None:
    pid = data["id"]
    catalog = ROOT / "catalog.yaml"
    text = catalog.read_text(encoding="utf-8") if catalog.is_file() else "faces:\n"
    if re.search(rf"^  - id: {re.escape(pid)}$", text, re.M):
        return
    block = (
        f"  - id: {pid}\n"
        f"    status: sketch\n"
        f"    displayName: {data['displayName']}\n"
        f"    badge: {badge}\n"
        f"    mix: {{ portrait: {mix['portrait']}, landscape: {mix['landscape']}, square: {mix['square']} }}\n"
        f"    role: {data['role']}\n"
        f"    familyId: {data['familyId']}\n"
        f"    related: []\n"
        f"    replaces: null\n"
        f"    packet: {pid}/packet.yaml\n"
        f"    usage: {pid}/USAGE.md\n"
        f"    sketch: {pid}/sketch.png\n"
    )
    catalog.write_text(text.rstrip() + "\n" + block, encoding="utf-8")
    table = ROOT / "CATALOG.md"
    if not table.is_file():
        return
    md = table.read_text(encoding="utf-8")
    row = (
        f"| `{pid}` | {data['displayName']} | `{badge}` | `{badge}` | `{data['role']}` | "
        f"（扫夹新建） | 未定 | sketch |\n"
    )
    if f"| `{pid}` |" in md:
        return
    lines = md.splitlines(keepends=True)
    insert_at = None
    for i, line in enumerate(lines):
        if line.startswith("| `page-"):
            insert_at = i + 1
    if insert_at is None:
        return
    lines.insert(insert_at, row)
    table.write_text("".join(lines), encoding="utf-8")


def create_face(payload: dict) -> dict:
    pid = str(payload.get("id") or "").strip()
    if not PAGE_ID_RE.match(pid) or not ID_RE.match(pid):
        raise ValueError("id 须为 page-{槽数}-{词}，小写字母数字和连字符。")
    named = int(PAGE_ID_RE.match(pid).group(1))
    raw_slots = payload.get("slots") or []
    orients = []
    for row in raw_slots:
        orient = row if isinstance(row, str) else str((row or {}).get("orient") or "")
        if orient not in ORIENTS:
            raise ValueError("槽朝向只许 portrait / landscape / square。")
        orients.append(orient)
    if not orients:
        raise ValueError("至少一槽。")
    if named != len(orients):
        raise ValueError(f"id 中数字 {named} ≠ 槽数 {len(orients)}。")
    program = str(payload.get("program") or "mosaic").strip()
    if program not in PROGRAMS:
        raise ValueError("program 须为七词之一。")
    data = {
        "id": pid,
        "displayName": str(payload.get("displayName") or pid).strip() or pid,
        "program": program,
        "role": str(payload.get("role") or pid).strip() or pid,
        "familyId": str(payload.get("familyId") or pid).strip() or pid,
        "slotCount": len(orients),
        "whenToUse": str(payload.get("whenToUse") or "待写").strip() or "待写",
        "whenNotToUse": str(payload.get("whenNotToUse") or "待写").strip() or "待写",
    }
    if not re.match(r"^[a-z][a-z0-9-]{0,47}$", data["role"]):
        raise ValueError("role 须为小写字母开头的短 id。")
    folder = ROOT / pid
    if folder.exists():
        raise ValueError(f"已有夹 {pid}。")
    mix = {
        "portrait": orients.count("portrait"),
        "landscape": orients.count("landscape"),
        "square": orients.count("square"),
    }
    badge = badge_of(mix)
    folder.mkdir()
    (folder / "packet.yaml").write_text(packet_yaml(data, badge, mix, orients), encoding="utf-8")
    (folder / "USAGE.md").write_text(usage_md(data, badge, mix), encoding="utf-8")
    append_catalog(data, badge, mix)
    face = scan_face(folder / "packet.yaml")
    if not face:
        raise ValueError("写完后扫夹失败。")
    return face


class Server(ThreadingHTTPServer):
    allow_reuse_address = False


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("设计工坊 %s\n" % (fmt % args))

    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path == "/series/index.json":
            self._json(200, {"books": list_books()})
            return
        if path == "/atelier/faces.json":
            faces = list_faces()
            roles = {
                row["id"]: {
                    "role": row["role"],
                    "program": row["program"],
                    "familyId": row["familyId"],
                }
                for row in faces
            }
            self._json(200, {"faces": faces, "roles": roles})
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path != "/atelier/pages":
            self.send_error(404, "Not Found")
            return
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0 or length > 200_000:
            self._json(400, {"error": "请求太大或是空的。"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            face = create_face(payload)
        except ValueError as err:
            self._json(400, {"error": str(err)})
            return
        except Exception:
            self._json(500, {"error": "写盘失败。"})
            return
        self._json(201, {"face": face})


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
    url = f"http://127.0.0.1:{port}/gallery.html"
    print(f"设计工坊 {url}", flush=True)
    print("GET /series/index.json · GET /atelier/faces.json · POST /atelier/pages · 引擎不读 · Ctrl+C 结束", flush=True)
    threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停", flush=True)


if __name__ == "__main__":
    main()
