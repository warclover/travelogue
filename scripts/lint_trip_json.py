#!/usr/bin/env python3
"""ADR-008 trip.json size + denylist lint (M-B5 / AC-ARC-11)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_WARN_BYTES = 512 * 1024
DEFAULT_MAX_BYTES = 2 * 1024 * 1024

FORBIDDEN_TOP_LEVEL_KEYS = frozenset(
    {
        "telemetry",
        "studioTelemetry",
        "embeddings",
        "clipEmbeddings",
        "debugLog",
        "_debug",
    }
)

CURATION_FORBIDDEN_KEYS = frozenset(
    {
        "layoutDecisionLog",
        "mosaicDecisionLog",
    }
)

ASSET_FORBIDDEN_KEYS = frozenset(
    {
        "embedding",
        "embeddings",
        "clipEmbedding",
        "clip_embedding",
        "faceEmbedding",
        "face_embedding",
        "sceneEmbedding",
        "scene_embedding",
    }
)

BASE64_DATA_URL = re.compile(r"^data:[^;]+;base64,", re.IGNORECASE)
MIN_BASE64_LEN = 256
MIN_EMBEDDING_VECTOR_LEN = 32


@dataclass
class LintReport:
    path: str
    bytes: int
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failures

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "bytes": self.bytes,
            "ok": self.ok,
            "failures": list(self.failures),
            "warnings": list(self.warnings),
            "summary": self.summary(),
        }

    def summary(self) -> str:
        if self.failures:
            return f"FAIL ({len(self.failures)}): " + "; ".join(self.failures[:3])
        if self.warnings:
            return f"WARN ({len(self.warnings)}): " + "; ".join(self.warnings[:3])
        return "OK"


def _looks_like_embedding_vector(value: Any) -> bool:
    if not isinstance(value, list) or len(value) < MIN_EMBEDDING_VECTOR_LEN:
        return False
    numeric = 0
    for item in value:
        if isinstance(item, (int, float)):
            numeric += 1
        else:
            return False
    return numeric == len(value)


def _scan_value(path: str, key: str, value: Any, report: LintReport) -> None:
    dotted = f"{path}.{key}" if path else key

    if key in CURATION_FORBIDDEN_KEYS and path == "curation":
        if isinstance(value, list):
            report.failures.append(f"denylist: {dotted} must not store full decision logs in trip.json")
        elif value not in (None,):
            report.failures.append(f"denylist: {dotted} must not be present in trip.json")

    if path.startswith("assets") and key in ASSET_FORBIDDEN_KEYS:
        report.failures.append(f"denylist: {dotted} embeddings belong in .cluster-cache/, not trip.json")

    if key.startswith("_debug") or key.endswith("DebugDump"):
        report.failures.append(f"denylist: {dotted} debug payload must live under runs/ or .cache/")

    if isinstance(value, str):
        if len(value) >= MIN_BASE64_LEN and BASE64_DATA_URL.match(value):
            report.failures.append(f"denylist: {dotted} contains inline base64 blob")
    elif isinstance(value, list) and key.lower().endswith("embedding") and _looks_like_embedding_vector(value):
        report.failures.append(f"denylist: {dotted} looks like an embedding vector")

    if isinstance(value, dict):
        _walk_dict(value, dotted, report)
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            if isinstance(item, dict):
                _walk_dict(item, f"{dotted}[{idx}]", report)


def _walk_dict(data: dict[str, Any], path: str, report: LintReport) -> None:
    for key, value in data.items():
        _scan_value(path, str(key), value, report)


def lint_trip_data(
    data: dict[str, Any],
    *,
    path: str = "<memory>",
    size_bytes: int | None = None,
    warn_bytes: int = DEFAULT_WARN_BYTES,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> LintReport:
    report = LintReport(path=path, bytes=size_bytes or 0)

    for key in data:
        if key in FORBIDDEN_TOP_LEVEL_KEYS:
            report.failures.append(f"denylist: top-level key {key!r} must not be stored in trip.json")

    from travelogue.curation.trip_migration import CURRENT_TRIP_VERSION

    raw_version = data.get("version")
    version = str(raw_version) if raw_version not in (None, "") else CURRENT_TRIP_VERSION
    if version != CURRENT_TRIP_VERSION:
        report.failures.append(
            f"version: {version!r} unsupported (supported: {CURRENT_TRIP_VERSION})"
        )

    _walk_dict(data, "", report)

    if size_bytes is not None:
        if size_bytes > max_bytes:
            report.failures.append(
                f"size: {size_bytes} bytes exceeds max {max_bytes} bytes ({max_bytes // 1024 // 1024} MiB)"
            )
        elif size_bytes > warn_bytes:
            report.warnings.append(
                f"size: {size_bytes} bytes exceeds warn threshold {warn_bytes} bytes ({warn_bytes // 1024} KiB)"
            )

    return report


def lint_trip_path(
    trip_path: Path,
    *,
    warn_bytes: int = DEFAULT_WARN_BYTES,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> LintReport:
    trip_path = trip_path.resolve()
    raw = trip_path.read_bytes()
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        report = LintReport(path=str(trip_path), bytes=len(raw))
        report.failures.append(f"parse: invalid JSON ({exc})")
        return report

    if not isinstance(data, dict):
        report = LintReport(path=str(trip_path), bytes=len(raw))
        report.failures.append("parse: trip.json top level must be an object")
        return report

    return lint_trip_data(
        data,
        path=str(trip_path),
        size_bytes=len(raw),
        warn_bytes=warn_bytes,
        max_bytes=max_bytes,
    )


def collect_trip_paths(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    for path in paths:
        path = path.resolve()
        if path.is_dir():
            candidate = path / "trip.json"
            if candidate.is_file():
                out.append(candidate)
            out.extend(sorted(path.glob("trip*.json")))
            out.extend(sorted(path.rglob("trip.json")))
        elif path.is_file():
            out.append(path)
    seen: set[Path] = set()
    unique: list[Path] = []
    for item in out:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint trip.json size and ADR-008 denylist")
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="trip.json files or directories containing trip.json",
    )
    parser.add_argument("--warn-bytes", type=int, default=DEFAULT_WARN_BYTES)
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON report")
    args = parser.parse_args(argv)

    targets = collect_trip_paths(list(args.paths)) if args.paths else collect_trip_paths(
        [
            Path("schemas/fixtures"),
            Path("tests/fixtures"),
        ]
    )
    if not targets:
        print("lint_trip_json: no trip.json files found", file=sys.stderr)
        return 1

    reports = [
        lint_trip_path(p, warn_bytes=args.warn_bytes, max_bytes=args.max_bytes) for p in targets
    ]
    failed = [r for r in reports if not r.ok]
    warned = [r for r in reports if r.warnings]

    if args.json:
        payload = {"reports": [r.to_dict() for r in reports], "ok": not failed}
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        for report in reports:
            level = "FAIL" if report.failures else ("WARN" if report.warnings else "OK")
            print(f"{level} {report.path} ({report.bytes} bytes) — {report.summary()}")
        if failed:
            print(f"\nlint_trip_json: {len(failed)} failure(s)", file=sys.stderr)
        elif warned:
            print(f"\nlint_trip_json: {len(warned)} warning(s)")
        else:
            print("lint_trip_json: OK")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
