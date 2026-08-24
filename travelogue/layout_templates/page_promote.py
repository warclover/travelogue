"""Compile atelier ``page-*`` packets into LTE YAML.

Compile-time only. Runtime LTE reads ``templates/page-*.yaml``.
The engine never scans ``docs/templates/reserve/``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from travelogue.paths import ROOT

RESERVE_DIR = ROOT / "docs" / "templates" / "reserve"
FACES_JS = RESERVE_DIR / "faces.js"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

# P0 gold-sample faces used by magazine-16-standard.
P0_PAGE_IDS: tuple[str, ...] = (
    "page-1-hero-land-wide",
    "page-2-pair-port",
    "page-2-1p1l-wide",
    "page-3-port",
    "page-3-2l1p-hero-left",
    "page-4-grid-land-wide",
    "page-5-3p2l-center",
    "page-5-3p2l-center-flip",
    "page-6-grid-land",
    "page-6-1l5l-wide-left",
    "page-6-1l5l-wide-right",
)

LTE_SLOT_MAX = 9
PAGE_SLOT_MAX = 10
SNAP_EPS = 0.15  # percent of stage


def _slot_max_for(page_id: str) -> int:
    """Journal mosaic stays at 9; portfolio ``page-*`` faces may use 10."""
    if str(page_id).startswith("page-"):
        return PAGE_SLOT_MAX
    return LTE_SLOT_MAX
_BOX_RE = re.compile(
    r"left:\s*([\d.]+),\s*top:\s*([\d.]+),\s*width:\s*([\d.]+),\s*height:\s*([\d.]+)"
)
_ID_RE = re.compile(r'id:\s*"(page-[^"]+)"')


@dataclass(frozen=True)
class PercentBox:
    left: float
    top: float
    width: float
    height: float

    @property
    def right(self) -> float:
        return self.left + self.width

    @property
    def bottom(self) -> float:
        return self.top + self.height


@dataclass
class PromoteSkip:
    page_id: str
    reason: str


def load_face_boxes(faces_js: Path = FACES_JS) -> dict[str, list[PercentBox]]:
    """Parse ``faces.js`` photo slots (ignore copy / copies)."""
    text = faces_js.read_text(encoding="utf-8")
    ids = list(_ID_RE.finditer(text))
    out: dict[str, list[PercentBox]] = {}
    for i, match in enumerate(ids):
        pid = match.group(1)
        end = ids[i + 1].start() if i + 1 < len(ids) else len(text)
        chunk = text[match.start() : end]
        boxes: list[PercentBox] = []
        slots_m = re.search(r"\bslots:\s*\[(.*?)\]", chunk, re.S)
        if slots_m:
            for left, top, width, height in _BOX_RE.findall(slots_m.group(1)):
                boxes.append(
                    PercentBox(float(left), float(top), float(width), float(height))
                )
        else:
            slot_m = re.search(r"(?<![a-z])slot:\s*\{([^}]+)\}", chunk)
            if slot_m:
                hit = _BOX_RE.search(slot_m.group(1))
                if hit:
                    left, top, width, height = hit.groups()
                    boxes.append(
                        PercentBox(float(left), float(top), float(width), float(height))
                    )
        if boxes:
            out[pid] = boxes
    return out


def _unique_axis(values: list[float], *, eps: float = SNAP_EPS) -> list[float]:
    ordered = sorted(values)
    out = [ordered[0]]
    for value in ordered[1:]:
        if value - out[-1] > eps:
            out.append(value)
        else:
            out[-1] = (out[-1] + value) / 2.0
    return out


def _snap(value: float, axis: list[float]) -> int:
    best_i = 0
    best_d = abs(value - axis[0])
    for i, edge in enumerate(axis):
        dist = abs(value - edge)
        if dist < best_d:
            best_d = dist
            best_i = i
    return best_i


def boxes_to_grid(
    boxes: list[PercentBox],
) -> tuple[list[float], list[float], list[tuple[int, int, int, int]]]:
    """Convert percent boxes to weighted tracks + 1-based closed rects."""
    xs = [0.0, 100.0]
    ys = [0.0, 100.0]
    for box in boxes:
        xs.extend([box.left, box.right])
        ys.extend([box.top, box.bottom])
    xs = _unique_axis(xs)
    ys = _unique_axis(ys)
    if xs[0] > 0:
        xs.insert(0, 0.0)
    if xs[-1] < 100:
        xs.append(100.0)
    if ys[0] > 0:
        ys.insert(0, 0.0)
    if ys[-1] < 100:
        ys.append(100.0)
    cols = [round(xs[i + 1] - xs[i], 6) for i in range(len(xs) - 1)]
    rows = [round(ys[i + 1] - ys[i], 6) for i in range(len(ys) - 1)]
    if any(w <= 0 for w in cols + rows):
        raise ValueError("degenerate track after snap")
    rects: list[tuple[int, int, int, int]] = []
    for box in boxes:
        c0 = _snap(box.left, xs) + 1
        c1 = _snap(box.right, xs)
        r0 = _snap(box.top, ys) + 1
        r1 = _snap(box.bottom, ys)
        if c1 < c0:
            c1 = c0
        if r1 < r0:
            r1 = r0
        rects.append((c0, c1, r0, r1))
    return cols, rows, rects


def _gap_cells(
    cols_n: int,
    rows_n: int,
    rects: list[tuple[int, int, int, int]],
) -> list[list[int]]:
    covered: set[tuple[int, int]] = set()
    for c0, c1, r0, r1 in rects:
        for c in range(c0, c1 + 1):
            for r in range(r0, r1 + 1):
                covered.add((c, r))
    gaps: list[list[int]] = []
    for r in range(1, rows_n + 1):
        c = 1
        while c <= cols_n:
            if (c, r) in covered:
                c += 1
                continue
            start = c
            while c <= cols_n and (c, r) not in covered:
                c += 1
            gaps.append([start, c - 1, r, r])
    return gaps


def _lte_role(orient: str, *, index: int, slot_count: int) -> str:
    key = str(orient or "").strip().lower()
    if key == "portrait":
        return "portrait"
    if key == "square":
        return "square"
    if slot_count == 1 and index == 0:
        return "main"
    return "landscape"


def _packet(page_id: str, reserve_dir: Path = RESERVE_DIR) -> dict[str, Any]:
    path = reserve_dir / page_id / "packet.yaml"
    if not path.is_file():
        return {}
    try:
        import yaml
    except ImportError:  # pragma: no cover
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def compile_page(
    page_id: str,
    boxes: list[PercentBox],
    *,
    reserve_dir: Path = RESERVE_DIR,
) -> dict[str, Any]:
    slot_max = _slot_max_for(page_id)
    if len(boxes) > slot_max:
        raise ValueError(f"{page_id} has {len(boxes)} slots; LTE max is {slot_max}")
    packet = _packet(page_id, reserve_dir)
    pkt_slots = packet.get("slots") if isinstance(packet.get("slots"), list) else []
    if pkt_slots and len(pkt_slots) != len(boxes):
        raise ValueError(
            f"{page_id} packet slots {len(pkt_slots)} != faces.js boxes {len(boxes)}"
        )
    cols, rows, rects = boxes_to_grid(boxes)
    n = len(boxes)
    lte_slots: list[dict[str, Any]] = []
    mix_p = 0
    mix_land = 0
    for i, rect in enumerate(rects):
        raw = pkt_slots[i] if i < len(pkt_slots) and isinstance(pkt_slots[i], dict) else {}
        orient = str(raw.get("orient") or "")
        role = _lte_role(orient, index=i, slot_count=n)
        if role == "portrait":
            mix_p += 1
        else:
            mix_land += 1
        lte_slots.append(
            {
                "index": i,
                "rect": list(rect),
                "role": role,
                "fit": "cover",
            }
        )
    usage_raw = packet.get("usage") if isinstance(packet.get("usage"), dict) else {}
    display = str(packet.get("displayName") or page_id)
    summary = display
    if len(summary) > 120:
        summary = summary[:117] + "..."
    gaps = _gap_cells(len(cols), len(rows), rects)
    doc: dict[str, Any] = {
        "id": page_id,
        "version": 1,
        "status": "experimental",
        "kind": "primitive" if n == 1 else "composite",
        "displayName": display,
        "description": (
            "Promoted from atelier reserve (compile-time). "
            "Engine does not read docs/templates/reserve/."
        ),
        "stage": {
            "aspect": "16:9",
            "cols": cols,
            "rows": rows,
            "variants": [
                {"layout": "web", "aspect": "16:9"},
                {"layout": "mobile", "aspect": "9:16"},
            ],
        },
        "photoCount": {"min": n, "max": n},
        "mix": {"portrait": mix_p, "landscape": mix_land},
        "slots": lte_slots,
        "constraints": {
            "portrait_forbidden_in_wide_slots": [],
            "landscape_forbidden_in_tall_slots": [],
            "intentionalGaps": gaps,
        },
        "scoring": {
            "base_weight": 1.0,
            "tags": ["page", "portfolio", "atelier-promote"],
        },
        "render": {
            "gridClass": f"layout-screen__grid--{page_id}",
            "cssBundle": "journal-screens.css",
            "fitPolicy": "auto_delegate",
        },
        "usage": {
            "summary": summary,
            "whenToUse": str(usage_raw.get("whenToUse") or "作品集成册页序点名这张脸时。"),
            "whenNotToUse": str(
                usage_raw.get("whenNotToUse") or "游记拼图不要选；只由成册系列 patternId 消费。"
            ),
        },
        "_legacy": {
            "sourceAtelier": page_id,
            "css_verified": True,
        },
    }
    if n > 1:
        doc["balancePolicy"] = "weighted_tracks"
    return doc


def dump_template_yaml(doc: dict[str, Any]) -> str:
    import yaml

    body = yaml.safe_dump(
        doc,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=88,
    )
    header = (
        "# Promoted page-* face · compile-time from docs/templates/reserve.\n"
        "# Engine does not read the atelier tree (ISO-05 / D-PFM-16).\n"
        "# experimental; list_active skips page-* so journal MCS never picks these SKUs.\n"
    )
    return header + body


def promote_pages(
    *,
    ids: list[str] | None = None,
    reserve_dir: Path = RESERVE_DIR,
    templates_dir: Path = TEMPLATES_DIR,
    write: bool = True,
) -> tuple[list[str], list[PromoteSkip]]:
    """Compile selected (or all eligible) faces. Returns (written ids, skips)."""
    faces_js = reserve_dir / "faces.js"
    boxes_by_id = load_face_boxes(faces_js)
    wanted = list(ids) if ids is not None else sorted(boxes_by_id)
    written: list[str] = []
    skips: list[PromoteSkip] = []
    templates_dir.mkdir(parents=True, exist_ok=True)
    for page_id in wanted:
        boxes = boxes_by_id.get(page_id)
        if not boxes:
            skips.append(PromoteSkip(page_id, "no faces.js geometry"))
            continue
        try:
            doc = compile_page(page_id, boxes, reserve_dir=reserve_dir)
        except ValueError as exc:
            skips.append(PromoteSkip(page_id, str(exc)))
            continue
        if write:
            path = templates_dir / f"{page_id}.yaml"
            path.write_text(dump_template_yaml(doc), encoding="utf-8")
        written.append(page_id)
    return written, skips
