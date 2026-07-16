#!/usr/bin/env python3
"""Lint trip directory: meta.title must appear in rendered HTML <title> tags.

Catches shelf/preview drift (bookshelf shows trip.json title, index.html still
has a stale magazine name).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
HTML_NAMES = ("index.html", "index-mobile.html", "index-present.html")


def _html_title(html: str) -> str | None:
    match = TITLE_RE.search(html)
    if not match:
        return None
    return re.sub(r"\s+", " ", match.group(1)).strip()


def check_trip_html_title_consistency(trip_dir: Path) -> list[str]:
    """Return failure messages for ``trip_dir`` (empty list means OK)."""
    trip_dir = trip_dir.resolve()
    trip_json = trip_dir / "trip.json"
    failures: list[str] = []
    if not trip_json.is_file():
        return [f"{trip_dir}: missing trip.json"]

    try:
        data = json.loads(trip_json.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"{trip_json}: parse error ({exc})"]

    if not isinstance(data, dict):
        return [f"{trip_json}: top level must be an object"]

    meta_title = str((data.get("meta") or {}).get("title") or "").strip()
    if not meta_title:
        return [f"{trip_json}: meta.title is empty"]

    html_paths = [trip_dir / name for name in HTML_NAMES if (trip_dir / name).is_file()]
    if not html_paths:
        return [f"{trip_dir}: no rendered index*.html next to trip.json"]

    for html_path in html_paths:
        try:
            html = html_path.read_text(encoding="utf-8")
        except OSError as exc:
            failures.append(f"{html_path}: unreadable ({exc})")
            continue
        page_title = _html_title(html)
        if not page_title:
            failures.append(f"{html_path}: missing <title>")
            continue
        if meta_title not in page_title and page_title not in meta_title:
            failures.append(
                f"{html_path}: <title>={page_title!r} does not match meta.title={meta_title!r}"
            )
    return failures


def collect_trip_dirs(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    for path in paths:
        path = path.resolve()
        if path.is_file() and path.name == "trip.json":
            out.append(path.parent)
        elif path.is_dir():
            if (path / "trip.json").is_file():
                out.append(path)
            for candidate in sorted(path.rglob("trip.json")):
                out.append(candidate.parent)
    seen: set[Path] = set()
    unique: list[Path] = []
    for item in out:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Lint trip meta.title vs rendered HTML <title> consistency"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="trip directories or trip.json paths (default: schemas/fixtures + tests/fixtures)",
    )
    args = parser.parse_args(argv)
    targets = (
        collect_trip_dirs(list(args.paths))
        if args.paths
        else collect_trip_dirs([Path("schemas/fixtures"), Path("tests/fixtures")])
    )
    if not targets:
        print("lint_trip_html_title: no trip directories found", file=sys.stderr)
        return 1

    failed = 0
    for trip_dir in targets:
        # Schema-only fixtures without rendered HTML are skipped (not failures).
        if not any((trip_dir / name).is_file() for name in HTML_NAMES):
            continue
        failures = check_trip_html_title_consistency(trip_dir)
        if failures:
            failed += 1
            for item in failures:
                print(f"FAIL {item}", file=sys.stderr)
        else:
            print(f"OK {trip_dir}")

    if failed:
        print(f"lint_trip_html_title: {failed} failure(s)", file=sys.stderr)
        return 1
    print("lint_trip_html_title: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
