#!/usr/bin/env python3
"""DPI W0 · ratchet: ban *new* dual-pipeline branches outside seams / allowlist.

Scan: ``travelogue/**/*.py`` only. CSS prefix isolation is ``lte_journal_css_audit.py --fail-on-prefix-leak``.
Existing hits live in ``docs/acceptance-records/dpi-seam-baseline.json``.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOT = ROOT / "travelogue"
TESTS_ROOT = ROOT / "tests"
BASELINE = ROOT / "docs" / "acceptance-records" / "dpi-seam-baseline.json"

SEAM_FILES = frozenset(
    {
        "travelogue/curation/curate.py",
        "travelogue/curation/moment_scoring.py",
        "travelogue/render/assemble.py",
        "travelogue/render/reading_profile.py",
        "travelogue/render/context.py",
        "travelogue/export/dispatch.py",
        "travelogue/services/validate.py",
        "travelogue/layout_templates/css_gen.py",
        "travelogue/layout_templates/validator.py",
        "travelogue/render/engine.py",
        "travelogue/export/packager.py",
    }
)

JOURNAL_FIXTURE_TOKEN = "phase16-dogfood"
PORTFOLIO_FIXTURE_TOKEN = "layout_engine/fixtures/editorial_series"
PORTFOLIO_TEST_HINTS = ("portfolio", "editorial_series", "editorial_")


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _is_allowlisted(rel: str) -> bool:
    if rel == "travelogue/config/edition.py":
        return True
    if rel == "travelogue/cli/render_cmds.py":
        return True
    if rel.startswith("travelogue/export/portfolio_"):
        return True
    if rel.startswith("travelogue/layout_engine/editorial_series"):
        return True
    if rel.startswith("travelogue/web/studio"):
        return True
    return False


def _is_seam(rel: str) -> bool:
    return rel in SEAM_FILES


_BRANCH_NAME_RE = re.compile(
    r"\b(is_portfolio_trip|is_portfolio|hideChapterChrome|trip_is_portfolio)\b"
)


def _import_hits(tree: ast.AST) -> list[str]:
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            mod = node.module
            if "editorial_series" in mod or mod.endswith(".slot_match"):
                if "editorial_series" in mod or "editorial_series" in (node.module or ""):
                    out.append(f"import:{mod}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if "editorial_series" in alias.name:
                    out.append(f"import:{alias.name}")
    return out


def scan_python() -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if not SCAN_ROOT.is_dir():
        return hits
    for path in sorted(SCAN_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        rel = _rel(path)
        if _is_allowlisted(rel) or _is_seam(rel):
            continue
        text = path.read_text(encoding="utf-8")
        kinds: set[str] = set()
        if _BRANCH_NAME_RE.search(text):
            kinds.add("branch")
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError:
            tree = None
        if tree is not None:
            for item in _import_hits(tree):
                kinds.add(item)
        for kind in sorted(kinds):
            hits.append({"file": rel, "kind": kind})
    hits.sort(key=lambda h: (h["file"], h["kind"]))
    return hits


def _is_portfolio_test(rel: str) -> bool:
    name = rel.lower()
    if "dual_pipeline" in name:
        return False
    return any(hint in name for hint in PORTFOLIO_TEST_HINTS)


def scan_fixture_direction() -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if not TESTS_ROOT.is_dir():
        return hits
    for path in sorted(TESTS_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        rel = _rel(path)
        text = path.read_text(encoding="utf-8")
        portfolio_test = _is_portfolio_test(rel)
        if portfolio_test and JOURNAL_FIXTURE_TOKEN in text:
            hits.append({"file": rel, "kind": "fixture:phase16-dogfood"})
        if (not portfolio_test) and PORTFOLIO_FIXTURE_TOKEN in text:
            hits.append({"file": rel, "kind": "fixture:editorial_series"})
    hits.sort(key=lambda h: (h["file"], h["kind"]))
    return hits


def _signature(hits: list[dict[str, str]]) -> list[str]:
    return sorted({f"{h['file']}::{h['kind']}" for h in hits})


def _parse_expiry(raw: object) -> date | None:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def _grandfather_map(old: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    edges = old.get("edges") or []
    meta = old.get("grandfather") or {}
    for item in edges:
        if isinstance(item, str):
            sig = item
            info = meta.get(sig) or {}
        else:
            continue
        if sig:
            out[sig] = {
                "owner": str(info.get("owner") or "").strip(),
                "expiry": str(info.get("expiry") or "").strip(),
            }
    return out


def explain_file(rel: str) -> str:
    posix = rel.replace("\\", "/")
    if _is_allowlisted(posix):
        return f"{posix}: allowlist (shared shell / identity / portfolio exclusive)"
    if _is_seam(posix):
        return f"{posix}: registered seam (see docs/dual-pipeline-ownership.md)"
    if posix.startswith("travelogue/layout_engine/mosaic"):
        return f"{posix}: journal exclusive (mosaic)"
    if posix.startswith("travelogue/layout_engine/editorial_series"):
        return f"{posix}: portfolio exclusive (editorial_series)"
    if posix.startswith("templates/visual-journal/journal-screens"):
        return f"{posix}: journal exclusive CSS"
    if posix == "travelogue/render/chapters.py":
        return f"{posix}: journal builder re-export; identity dispatch is assemble.py only"
    if posix == "travelogue/render/journal_chapters.py":
        return f"{posix}: journal exclusive builder (highlight / longshot / breath / trip-index)"
    if posix == "travelogue/render/portfolio_chapters.py":
        return f"{posix}: portfolio exclusive builder (page-* / 16:9 / empty-chapter skip)"
    if posix == "travelogue/render/surface.py":
        return f"{posix}: shared surface; no edition branch after W2"
    return f"{posix}: not registered — new dual-pipeline marks here will fail the ratchet"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Write/refresh baseline when the hit set did not grow",
    )
    parser.add_argument(
        "--allow-growth",
        action="store_true",
        help="Permit baseline update when new edges appear",
    )
    parser.add_argument(
        "--explain",
        metavar="FILE",
        help="Print ownership for a repo-relative path and exit",
    )
    args = parser.parse_args(argv)

    if args.explain:
        print(explain_file(args.explain))
        return 0

    hits = scan_python() + scan_fixture_direction()
    sig = _signature(hits)
    report = {"count": len(sig), "edges": sig, "details": hits}

    if args.update_baseline:
        grandfather: dict[str, dict] = {}
        if BASELINE.is_file():
            old = json.loads(BASELINE.read_text(encoding="utf-8"))
            old_map = _grandfather_map(old)
            old_sig = set(old_map) or set(old.get("edges") or [])
            added = sorted(set(sig) - old_sig)
            if added and not args.allow_growth:
                print("refusing baseline update; new dual-pipeline edges:", file=sys.stderr)
                for a in added:
                    print(f"  + {a}", file=sys.stderr)
                return 1
            for edge in sig:
                prev = old_map.get(edge) or {}
                grandfather[edge] = {
                    "owner": prev.get("owner") or "dpi-w0",
                    "expiry": prev.get("expiry") or "2026-12-31",
                }
        else:
            for edge in sig:
                grandfather[edge] = {"owner": "dpi-w0", "expiry": "2026-12-31"}
        payload = {
            "count": len(sig),
            "edges": sig,
            "grandfather": grandfather,
            "details": hits,
            "note": "W2 ratchet. Remaining grandfather: output_recipe/resolve.py. CSS prefix leak is lte_journal_css_audit.py.",
        }
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"baseline updated: {len(sig)} dual-pipeline edges")
        return 0

    if not BASELINE.is_file():
        print("missing baseline; run with --update-baseline", file=sys.stderr)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    old = json.loads(BASELINE.read_text(encoding="utf-8"))
    gf = _grandfather_map(old)
    old_sig = set(gf) or set(old.get("edges") or [])
    new_sig = set(sig)
    added = sorted(new_sig - old_sig)
    removed = sorted(old_sig - new_sig)
    print(f"dual-pipeline ownership hits: {len(sig)} (baseline {len(old_sig)})")
    if removed:
        print(f"improved: removed {len(removed)} edge(s)")
    today = date.today()
    expired = []
    missing_meta = []
    for edge in sorted(new_sig & old_sig):
        info = gf.get(edge) or {}
        if not info.get("owner") or not info.get("expiry"):
            missing_meta.append(edge)
            continue
        exp = _parse_expiry(info.get("expiry"))
        if exp is None or exp < today:
            expired.append(edge)
    if missing_meta:
        print("REGRESSION: grandfather missing owner/expiry:", file=sys.stderr)
        for a in missing_meta:
            print(f"  ! {a}", file=sys.stderr)
        return 1
    if expired:
        print("REGRESSION: grandfather expiry passed:", file=sys.stderr)
        for a in expired:
            print(f"  ! {a} expiry={gf[a].get('expiry')}", file=sys.stderr)
        return 1
    if added:
        print("REGRESSION: new dual-pipeline marks outside seams/allowlist:", file=sys.stderr)
        for a in added:
            print(f"  + {a}", file=sys.stderr)
        print(
            "If this is an intentional seam, add it to SEAM_FILES / allowlist "
            "and document in docs/dual-pipeline-ownership.md.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
