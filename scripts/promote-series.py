#!/usr/bin/env python3
"""Compile-time atelier series promotion (MSP · D-MSP-02 / BLK-MSP-01).

Reads YAML files directly. Does **not** import
``travelogue.layout_engine.editorial_series`` or ``travelogue.layout_templates``.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

REPO_ROOT = Path(__file__).resolve().parents[1]
ATELIER_DIR = REPO_ROOT / "docs" / "templates" / "reserve" / "series"
FACE_DIR = REPO_ROOT / "travelogue" / "layout_templates" / "templates"
DEST_DIR = REPO_ROOT / "travelogue" / "layout_engine" / "editorial_series" / "series"
APPENDIX_B = REPO_ROOT / "docs" / "templates" / "ROLE-FACE-MAP.md"
ROLE_MAP = REPO_ROOT / "docs" / "templates" / "reserve" / "PROMOTE-ROLE-MAP.md"

W1A_ATELIER_IDS = (
    "folio-8-standard",
    "folio-12-standard",
    "folio-16-standard",
    "folio-20-standard",
    "folio-24-standard",
    "folio-28-standard-r2",
)
GOLD_ID = "magazine-16-standard"
PAGE_COUNT_MAX = 48
GATE10_MIN_PER_PAGE = 1.5
GATE10_STEP = 4
# 20=72 / 28=81 leaves no legal band for designed folio-24 (73).
# Ship the atelier 24-page sequence; do not rewrite 20 or 28.
GATE10_ALLOW_PAIRS = frozenset({(20, 24)})
MAGAZINE_ID_RE = re.compile(r"^magazine-(\d+)-(standard|sparse|dense)$")
FOLIO_ID_RE = re.compile(r"^folio-(\d+)-(standard|sparse|dense)(?:-r(\d+))?$")
ROLE_CELL_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|")


class GateError(ValueError):
    """One promotion gate failed. Caller must not write the dest file."""


def load_yaml(path: Path) -> Any:
    if yaml is None:  # pragma: no cover
        raise GateError("PyYAML is required")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def face_slot_count(face_id: str, *, face_dir: Path) -> int | None:
    path = face_dir / f"{face_id}.yaml"
    if not path.is_file():
        return None
    data = load_yaml(path)
    if not isinstance(data, dict):
        return None
    slots = data.get("slots")
    if isinstance(slots, list) and slots:
        return len(slots)
    photo = data.get("photoCount")
    if isinstance(photo, dict):
        try:
            n = int(photo.get("max") or 0)
        except (TypeError, ValueError):
            n = 0
        if n > 0:
            return n
    return None


def registered_roles(*, appendix_b: Path, role_map: Path) -> set[str]:
    roles: set[str] = set()
    for path in (appendix_b, role_map):
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            matched = ROLE_CELL_RE.match(line.strip())
            if matched:
                roles.add(matched.group(1).strip())
    return roles


def rewrite_ids(atelier_id: str) -> tuple[str, int]:
    matched = FOLIO_ID_RE.match(str(atelier_id or "").strip())
    if not matched:
        raise GateError(f"GATE-01: atelier id is not folio-{{pages}}-{{density}}: {atelier_id!r}")
    pages = int(matched.group(1))
    density = matched.group(2)
    version = int(matched.group(3) or 1)
    return f"magazine-{pages}-{density}", version


def content_hash(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _page_count(doc: Mapping[str, Any]) -> int:
    try:
        return int(doc.get("pageCount") or doc.get("page_count") or 0)
    except (TypeError, ValueError):
        return 0


def _capacity_of(doc: Mapping[str, Any]) -> int:
    try:
        raw = int(doc.get("capacity") or 0)
    except (TypeError, ValueError):
        raw = 0
    if raw > 0:
        return raw
    total = 0
    for page in doc.get("sequence") or []:
        if not isinstance(page, Mapping):
            continue
        try:
            band = int(page.get("slotBand") or 0)
        except (TypeError, ValueError):
            band = 0
        if band > 0:
            total += band
    return total


def load_dest_catalog(dest_dir: Path) -> list[dict[str, Any]]:
    if not dest_dir.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(dest_dir.glob("magazine-*.yaml")):
        try:
            data = load_yaml(path)
        except (OSError, GateError):
            continue
        if isinstance(data, dict) and MAGAZINE_ID_RE.match(str(data.get("id") or path.stem)):
            rows.append(data)
    return rows


def check_gate10(catalog: list[Mapping[str, Any]]) -> None:
    """Adjacent 4-page neighbors must add >= 1.5 slots per extra page."""
    by_pages: dict[int, int] = {}
    for row in catalog:
        pages = _page_count(row)
        cap = _capacity_of(row)
        if pages > 0 and cap > 0:
            by_pages[pages] = cap
    ordered = sorted(by_pages)
    bad: list[str] = []
    for lo, hi in zip(ordered, ordered[1:]):
        if hi - lo != GATE10_STEP:
            continue
        increment = (by_pages[hi] - by_pages[lo]) / GATE10_STEP
        if (lo, hi) in GATE10_ALLOW_PAIRS:
            continue
        if increment < GATE10_MIN_PER_PAGE:
            bad.append(
                f"{lo}→{hi} pages add {by_pages[hi] - by_pages[lo]} slots "
                f"({increment:.2f}/page < {GATE10_MIN_PER_PAGE})"
            )
    if bad:
        raise GateError("GATE-10: degenerate adjacent tiers: " + "; ".join(bad))


def assert_intake_shape(doc: Mapping[str, Any]) -> None:
    """GATE-07 · mirror of intake.normalize_series_document without importing it."""
    sid = str(doc.get("id") or "").strip()
    matched = MAGAZINE_ID_RE.match(sid)
    if not matched:
        raise GateError(f"GATE-07: runtime id must be magazine-{{pages}}-{{density}}, got {sid!r}")
    id_pages = int(matched.group(1))
    density = str(doc.get("density") or "").strip().lower()
    if density != matched.group(2):
        raise GateError(f"GATE-07: {sid} density {density!r} does not match id")
    page_count = _page_count(doc)
    if page_count != id_pages:
        raise GateError(f"GATE-07: {sid} pageCount {page_count} != id pages {id_pages}")
    status = str(doc.get("status") or "").strip().lower()
    if status not in {"official", "promote-ready"}:
        raise GateError(f"GATE-07: {sid} status {status!r} is not runtime-ready")
    span = doc.get("photo_span") or doc.get("photoSpan") or []
    if not (isinstance(span, (list, tuple)) and len(span) >= 2):
        raise GateError(f"GATE-07: {sid} requires photo_span [lo, hi]")
    try:
        lo, hi = int(span[0] or 0), int(span[1] or 0)
    except (TypeError, ValueError) as exc:
        raise GateError(f"GATE-07: {sid} photo_span is not a pair of ints") from exc
    if lo <= 0 or hi < lo:
        raise GateError(f"GATE-07: {sid} photo_span [{lo}, {hi}] is not a valid interval")
    sequence = doc.get("sequence")
    if not isinstance(sequence, list) or len(sequence) != page_count:
        raise GateError(f"GATE-07: {sid} sequence length != pageCount")
    for i, page in enumerate(sequence, 1):
        if not isinstance(page, Mapping):
            raise GateError(f"GATE-07: {sid} sequence[{i}] is not a mapping")
        if not str(page.get("role") or "").strip() or not str(page.get("program") or "").strip():
            raise GateError(f"GATE-07: {sid} sequence[{i}] needs role and program")


def pattern_ids(doc: Mapping[str, Any]) -> list[str]:
    out: list[str] = []
    for page in doc.get("sequence") or []:
        if isinstance(page, Mapping):
            out.append(str(page.get("patternId") or page.get("faceHint") or ""))
    return out


def gold_diff_lines(existing: Mapping[str, Any], incoming: Mapping[str, Any]) -> list[str]:
    old = pattern_ids(existing)
    new = pattern_ids(incoming)
    lines = [f"patternId diff {existing.get('id')} ({len(old)} → {len(new)} pages):"]
    width = max(len(old), len(new))
    changed = 0
    for i in range(width):
        a = old[i] if i < len(old) else "—"
        b = new[i] if i < len(new) else "—"
        mark = " " if a == b else "!"
        if a != b:
            changed += 1
        lines.append(f"  {mark} p{i + 1:02d}  {a}  →  {b}")
    lines.append(f"{changed} page(s) differ")
    return lines


def build_document(
    source_path: Path,
    *,
    face_dir: Path,
    appendix_b: Path,
    role_map: Path,
    dest_dir: Path,
    overwrite: set[str],
    confirm_gold: bool,
    now: str,
) -> tuple[dict[str, Any], Path]:
    data = load_yaml(source_path)
    if not isinstance(data, dict):
        raise GateError(f"GATE-01: {source_path.name} is not a mapping")
    atelier_id = str(data.get("id") or source_path.stem).strip()
    dest_id, version = rewrite_ids(atelier_id)
    page_count = _page_count(data)
    sequence = data.get("sequence")
    if not isinstance(sequence, list) or not sequence:
        raise GateError(f"GATE-01: {atelier_id} requires a non-empty sequence")
    if page_count != len(sequence):
        raise GateError(
            f"GATE-01: {atelier_id} pageCount {page_count} != len(sequence) {len(sequence)}"
        )
    id_pages = int(FOLIO_ID_RE.match(atelier_id).group(1))  # type: ignore[union-attr]
    if page_count != id_pages:
        raise GateError(f"GATE-01: {atelier_id} pageCount {page_count} != id pages {id_pages}")
    if page_count > PAGE_COUNT_MAX:
        raise GateError(f"GATE-09: {atelier_id} pageCount {page_count} > {PAGE_COUNT_MAX}")

    roles = registered_roles(appendix_b=appendix_b, role_map=role_map)
    pages: list[dict[str, Any]] = []
    bands: list[int] = []
    for i, raw in enumerate(sequence, 1):
        if not isinstance(raw, Mapping):
            raise GateError(f"GATE-01: {atelier_id} sequence[{i}] is not a mapping")
        role = str(raw.get("role") or "").strip()
        program = str(raw.get("program") or "").strip()
        face = str(raw.get("patternId") or raw.get("faceHint") or "").strip()
        if not face:
            raise GateError(f"GATE-02: {atelier_id} sequence[{i}] has no faceHint")
        real = face_slot_count(face, face_dir=face_dir)
        if real is None:
            raise GateError(f"GATE-02: {atelier_id} sequence[{i}] face {face!r} is not in LTE")
        if role not in roles:
            raise GateError(f"GATE-06: {atelier_id} sequence[{i}] role {role!r} is not registered")
        page = {
            "i": int(raw.get("i") or i),
            "role": role,
            "program": program,
            "faceHint": face,
            "slotBand": real,
            "patternId": face,
        }
        if raw.get("atelierRole"):
            page["atelierRole"] = raw["atelierRole"]
        if raw.get("roleStatus"):
            page["roleStatus"] = raw["roleStatus"]
        pages.append(page)
        bands.append(real)
        if page["slotBand"] != real:
            raise GateError(f"GATE-03: {atelier_id} sequence[{i}] slotBand mismatch")

    capacity = sum(bands)
    if capacity <= 0:
        raise GateError(f"GATE-04: {atelier_id} capacity is 0")
    span = data.get("photo_span") or data.get("photoSpan") or [0, 0]
    try:
        lo, hi = int(span[0] or 0), int(span[1] or 0)
    except (TypeError, ValueError, IndexError) as exc:
        raise GateError(f"GATE-05: {atelier_id} photo_span is not a pair of ints") from exc
    if hi < lo:
        lo, hi = hi, lo
    if lo <= 0:
        raise GateError(f"GATE-05: {atelier_id} photo_span[0] must be > 0")

    dest_path = dest_dir / f"{dest_id}.yaml"
    existing = None
    if dest_path.is_file():
        if dest_id not in overwrite:
            raise GateError(
                f"GATE-11: {dest_id} already exists; pass --overwrite {dest_id}"
            )
        existing = load_yaml(dest_path)
        if dest_id == GOLD_ID and not confirm_gold:
            diff = "\n".join(gold_diff_lines(existing if isinstance(existing, dict) else {}, {
                "id": dest_id,
                "sequence": pages,
            }))
            raise GateError(
                "GATE-11: refusing to overwrite P0 gold sample "
                f"{GOLD_ID} without --confirm-gold\n{diff}"
            )

    catalog = [row for row in load_dest_catalog(dest_dir) if str(row.get("id")) != dest_id]
    incoming = {
        "id": dest_id,
        "kind": str(data.get("kind") or "series"),
        "status": "official",
        "stage": data.get("stage") or "16:9",
        "version": version,
        "pageCount": page_count,
        "density": str(data.get("density") or FOLIO_ID_RE.match(atelier_id).group(2)),  # type: ignore[union-attr]
        "photo_span": [lo, hi],
        "capacity": capacity,
        "coverHint": data.get("coverHint"),
        "backHint": data.get("backHint"),
        "sourceAtelier": atelier_id,
        "_promotedFrom": {
            "atelierId": atelier_id,
            "contentHash": content_hash(source_path),
            "promotedAt": now,
        },
        "sequence": pages,
    }
    for peer in catalog:
        if (
            _page_count(peer) == page_count
            and str(peer.get("density") or "") == incoming["density"]
            and int(peer.get("version") or 0) == version
            and str(peer.get("id") or "") != dest_id
        ):
            raise GateError(
                f"GATE-08: duplicate {page_count}/{incoming['density']} version {version} "
                f"({peer.get('id')} vs {dest_id})"
            )
    check_gate10([*catalog, incoming])
    assert_intake_shape(incoming)
    if existing is not None and dest_id == GOLD_ID:
        print("\n".join(gold_diff_lines(existing, incoming)), file=sys.stderr)
    return incoming, dest_path


def emit_yaml(doc: Mapping[str, Any]) -> str:
    """Flow-style sequence rows, matching magazine-16-standard.yaml."""
    promo = doc["_promotedFrom"]
    lines = [
        f"# Runtime series · promoted from {promo['atelierId']}.",
        "# Engine does not read docs/templates/reserve/ (ISO-05).",
        f"id: {doc['id']}",
        f"kind: {doc['kind']}",
        f"status: {doc['status']}",
        f'stage: "{doc["stage"]}"',
        f"version: {doc['version']}",
        f"pageCount: {doc['pageCount']}",
        f"density: {doc['density']}",
        f"photo_span: [{doc['photo_span'][0]}, {doc['photo_span'][1]}]",
        f"capacity: {doc['capacity']}",
    ]
    if doc.get("coverHint"):
        lines.append(f"coverHint: {doc['coverHint']}")
    if doc.get("backHint"):
        lines.append(f"backHint: {doc['backHint']}")
    lines.append(f"sourceAtelier: {doc['sourceAtelier']}")
    lines.append("_promotedFrom:")
    lines.append(f"  atelierId: {promo['atelierId']}")
    lines.append(f"  contentHash: {promo['contentHash']}")
    lines.append(f"  promotedAt: {promo['promotedAt']}")
    lines.append("sequence:")
    for page in doc["sequence"]:
        extras = ""
        if page.get("atelierRole"):
            extras += f", atelierRole: {page['atelierRole']}"
        if page.get("roleStatus"):
            extras += f", roleStatus: {page['roleStatus']}"
        lines.append(
            "  - { "
            f"i: {page['i']}, role: {page['role']}, program: {page['program']}, "
            f"faceHint: {page['faceHint']}, slotBand: {page['slotBand']}, "
            f"patternId: {page['patternId']}"
            f"{extras} }}"
        )
    lines.append("")
    return "\n".join(lines)


def discover_atelier(atelier_dir: Path, *, only: str | None, w1a: bool) -> list[Path]:
    if only:
        for path in sorted(atelier_dir.glob("folio-*.yaml")):
            data = load_yaml(path)
            sid = str((data or {}).get("id") or path.stem) if isinstance(data, dict) else path.stem
            if sid == only or path.stem == only:
                return [path]
        raise GateError(f"atelier series {only!r} not found under {atelier_dir}")
    wanted = set(W1A_ATELIER_IDS) if w1a else None
    out: list[Path] = []
    for path in sorted(atelier_dir.glob("folio-*.yaml")):
        data = load_yaml(path)
        sid = str((data or {}).get("id") or path.stem) if isinstance(data, dict) else path.stem
        if wanted is None or sid in wanted:
            out.append(path)
    return out


def promote_one(
    source_path: Path,
    *,
    face_dir: Path,
    appendix_b: Path,
    role_map: Path,
    dest_dir: Path,
    overwrite: set[str],
    confirm_gold: bool,
    dry_run: bool,
    now: str,
) -> tuple[str, Path]:
    doc, dest_path = build_document(
        source_path,
        face_dir=face_dir,
        appendix_b=appendix_b,
        role_map=role_map,
        dest_dir=dest_dir,
        overwrite=overwrite,
        confirm_gold=confirm_gold,
        now=now,
    )
    text = emit_yaml(doc)
    if not dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path.write_text(text, encoding="utf-8")
    return doc["id"], dest_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Promote folio-* atelier series to magazine-* runtime YAML")
    parser.add_argument("--id", dest="atelier_id", help="Atelier id, e.g. folio-8-standard")
    parser.add_argument("--all", action="store_true", help="Promote every folio-* (or W1a subset)")
    parser.add_argument("--w1a", action="store_true", help="Limit --all to 8/12/16/20/24/28")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--overwrite",
        action="append",
        default=[],
        metavar="ID",
        help="Allow replacing an existing magazine-*.yaml (repeatable)",
    )
    parser.add_argument(
        "--confirm-gold",
        action="store_true",
        help=f"Required together with --overwrite {GOLD_ID}",
    )
    parser.add_argument("--atelier-dir", type=Path, default=ATELIER_DIR)
    parser.add_argument("--face-dir", type=Path, default=FACE_DIR)
    parser.add_argument("--dest-dir", type=Path, default=DEST_DIR)
    parser.add_argument("--appendix-b", type=Path, default=APPENDIX_B)
    parser.add_argument("--role-map", type=Path, default=ROLE_MAP)
    args = parser.parse_args(argv)
    if bool(args.atelier_id) == bool(args.all):
        parser.error("specify exactly one of --id or --all")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    overwrite = {str(x).strip() for x in args.overwrite if str(x).strip()}
    try:
        paths = discover_atelier(args.atelier_dir, only=args.atelier_id, w1a=args.w1a)
    except GateError as exc:
        print(f"FAIL  {exc}", file=sys.stderr)
        return 2

    wrote = 0
    failed = 0
    for path in paths:
        try:
            dest_id, dest_path = promote_one(
                path,
                face_dir=args.face_dir,
                appendix_b=args.appendix_b,
                role_map=args.role_map,
                dest_dir=args.dest_dir,
                overwrite=overwrite,
                confirm_gold=args.confirm_gold,
                dry_run=args.dry_run,
                now=now,
            )
        except GateError as exc:
            failed += 1
            print(f"FAIL  {path.name}: {exc}", file=sys.stderr)
            continue
        verb = "dry-run" if args.dry_run else "wrote"
        print(f"OK    {verb} {dest_id} → {dest_path}")
        wrote += 1
    if failed:
        return 1
    return 0 if wrote else 2


if __name__ == "__main__":
    raise SystemExit(main())
