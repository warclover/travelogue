"""Load clustering golden fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures" / "clustering"

GOLDEN_TRIP_IDS = (
    "golden-kyoto-gps",
    "golden-no-gps",
    "golden-mixed-scenes",
    "synthetic-gps",
)


def fixture_dir(trip_id: str) -> Path:
    return FIXTURES_ROOT / trip_id


def load_fixture_assets(trip_id: str) -> list[dict[str, Any]]:
    path = fixture_dir(trip_id) / "assets-manifest.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "assets" in raw:
        return list(raw["assets"])
    if isinstance(raw, list):
        return raw
    raise ValueError(f"invalid manifest: {path}")


def load_fixture_golden_segments(trip_id: str) -> list[dict[str, Any]]:
    path = fixture_dir(trip_id) / "segments-golden.json"
    if not path.is_file():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, list) else []
