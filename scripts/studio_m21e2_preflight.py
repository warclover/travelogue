"""M21-e2 preflight gate for v3 homepage physical retirement.

Usage:
  python scripts/studio_m21e2_preflight.py
  python scripts/studio_m21e2_preflight.py --observed-release --json --out reports/m21-e2-preflight.json
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

CANDIDATE_DELETE_PATHS = (
    "templates/studio/studio.html",
    "templates/studio/studio.js",
    "templates/studio/studio.css",
    "templates/studio/js/navigation.js",
    "templates/studio/js/render.js",
    "templates/studio/js/sheet.js",
    "templates/studio/js/samples.js",
    "templates/studio/js/init.js",
    "templates/studio/js/viewport.js",
)

REFERENCE_TOKENS = (
    "studio.html",
    "studio.js",
    "studio.css",
    "./js/navigation.js",
    "./js/render.js",
    "./js/sheet.js",
    "./js/samples.js",
    "./js/init.js",
    "./js/viewport.js",
    "js/navigation.js",
    "js/render.js",
    "js/sheet.js",
    "js/samples.js",
    "js/init.js",
    "js/viewport.js",
)

TEXT_EXTS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".html",
    ".css",
    ".md",
    ".yml",
    ".yaml",
    ".toml",
    ".json",
    ".txt",
}

IGNORE_REFERENCE_PATHS = {
    "scripts/studio_m21e2_preflight.py",
    "tests/test_studio_m21e2_preflight.py",
}

LEGACY_TEST_HELPERS = {
    "tests/_studio_js.py",
}


@dataclass(frozen=True)
class RefHit:
    path: str
    token: str


def _iter_repo_text_files() -> list[Path]:
    out: list[Path] = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if any(part in {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"} for part in p.parts):
            continue
        if p.suffix.lower() not in TEXT_EXTS:
            continue
        out.append(p)
    return out


def _is_candidate_file(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    return rel in set(CANDIDATE_DELETE_PATHS)


def _is_legacy_test(path: Path, body: str) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    return rel.startswith("tests/") and "legacy_homepage" in body


def _classify_bucket(path: Path, body: str) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel in LEGACY_TEST_HELPERS:
        return "legacy_test_refs"
    if rel.startswith("travelogue/") or rel.startswith("templates/"):
        return "runtime_blockers"
    if rel.startswith(".github/workflows/"):
        return "runtime_blockers"
    if rel.startswith("tests/"):
        return "legacy_test_refs" if _is_legacy_test(path, body) else "test_blockers"
    if rel.startswith("docs/"):
        return "doc_refs"
    return "other_refs"


def scan_references() -> dict[str, list[dict[str, str]]]:
    buckets: dict[str, list[dict[str, str]]] = {
        "runtime_blockers": [],
        "test_blockers": [],
        "legacy_test_refs": [],
        "doc_refs": [],
        "other_refs": [],
    }
    seen: set[tuple[str, str]] = set()
    for path in _iter_repo_text_files():
        rel = path.relative_to(ROOT).as_posix()
        if rel in IGNORE_REFERENCE_PATHS:
            continue
        if _is_candidate_file(path):
            continue
        try:
            body = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for token in REFERENCE_TOKENS:
            if token not in body:
                continue
            key = (rel, token)
            if key in seen:
                continue
            seen.add(key)
            bucket = _classify_bucket(path, body)
            buckets[bucket].append({"path": rel, "token": token})
    for key in buckets:
        buckets[key].sort(key=lambda x: (x["path"], x["token"]))
    return buckets


def build_report(observed_release: bool = False) -> dict[str, Any]:
    refs = scan_references()
    ready = observed_release and not refs["runtime_blockers"] and not refs["test_blockers"]
    reasons: list[str] = []
    if not observed_release:
        reasons.append("OBSERVATION_WINDOW_REQUIRED")
    if refs["runtime_blockers"]:
        reasons.append("RUNTIME_REFERENCES_PRESENT")
    if refs["test_blockers"]:
        reasons.append("NON_LEGACY_TEST_REFERENCES_PRESENT")
    if not reasons:
        reasons.append("READY_FOR_M21_E2")
    return {
        "schema": "studio-m21-e2-preflight/v1",
        "observed_release": observed_release,
        "candidate_delete_paths": list(CANDIDATE_DELETE_PATHS),
        "references": refs,
        "ready": ready,
        "reasons": reasons,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="M21-e2 v3 retirement preflight")
    parser.add_argument("--observed-release", action="store_true", help="set true after one release observation window")
    parser.add_argument("--json", action="store_true", help="print full report as JSON")
    parser.add_argument("--out", type=Path, default=None, help="optional JSON output path")
    args = parser.parse_args(argv)

    report = build_report(observed_release=bool(args.observed_release))
    if args.out:
        out_path = (ROOT / args.out).resolve() if not args.out.is_absolute() else args.out
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"ready={report['ready']}")
        print("reasons=" + ",".join(report["reasons"]))
        print(f"runtime_blockers={len(report['references']['runtime_blockers'])}")
        print(f"test_blockers={len(report['references']['test_blockers'])}")
        print(f"legacy_test_refs={len(report['references']['legacy_test_refs'])}")
        print(f"doc_refs={len(report['references']['doc_refs'])}")

    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
