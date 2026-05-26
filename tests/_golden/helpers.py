"""Helpers to build mini trips and capture layout snapshots for golden tests."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from travelogue.curation.layout_planner import build_chapters_from_buckets, summarize_orientations
from travelogue.curation.curate_patterns import pattern_hint_for_bucket
from travelogue.media.image_ops import classify_aspect

GOLDEN_DIR = Path(__file__).resolve().parent


def _asset(
    aid: str,
    w: int,
    h: int,
    *,
    offset_hours: float = 0.0,
    sharpness: float | None = None,
) -> dict:
    base = datetime(2025, 6, 1, 10, 0, tzinfo=timezone.utc)
    taken = (base + timedelta(hours=offset_hours)).isoformat().replace("+00:00", "Z")
    a: dict[str, Any] = {
        "id": aid,
        "type": "image",
        "width": w,
        "height": h,
        "aspectKind": classify_aspect(w, h),
        "takenAt": taken,
        "curation": {"layoutEligible": True},
    }
    if sharpness is not None:
        a["quality"] = {"sharpness": sharpness}
    return a


def build_portrait_heavy_trip() -> tuple[list[list[str]], dict[str, str], list[dict]]:
    """6 portrait assets in 2 buckets — matches golden portrait-heavy fixture."""
    assets = [
        _asset("p1", 900, 1600, offset_hours=0),
        _asset("p2", 900, 1600, offset_hours=1),
        _asset("p3", 900, 1600, offset_hours=2),
        _asset("p4", 900, 1600, offset_hours=24),
        _asset("p5", 900, 1600, offset_hours=25),
        _asset("p6", 900, 1600, offset_hours=26),
    ]
    buckets = [["p1", "p2", "p3"], ["p4", "p5", "p6"]]
    aspects = {a["id"]: a["aspectKind"] for a in assets}
    return buckets, aspects, assets


def build_mixed_aspects_trip() -> tuple[list[list[str]], dict[str, str], list[dict]]:
    """8 assets mixed portrait/landscape in 2 buckets."""
    assets = [
        _asset("p1", 900, 1600, offset_hours=0),
        _asset("l1", 2000, 1200, offset_hours=0.5),
        _asset("l2", 2000, 1200, offset_hours=1),
        _asset("p2", 900, 1600, offset_hours=1.5),
        _asset("l3", 2000, 1200, offset_hours=24),
        _asset("p3", 900, 1600, offset_hours=24.5),
        _asset("l4", 2000, 1200, offset_hours=25),
        _asset("p4", 900, 1600, offset_hours=25.5),
    ]
    buckets = [["p1", "l1", "l2", "p2"], ["l3", "p3", "l4", "p4"]]
    aspects = {a["id"]: a["aspectKind"] for a in assets}
    return buckets, aspects, assets


def layout_snapshot(chapters: list[dict]) -> dict[str, Any]:
    return {
        "chapters": [
            {
                "id": ch.get("id"),
                "patternId": ch.get("patternId"),
                "screens": [
                    {
                        "patternId": s.get("patternId"),
                        "slotAssetIds": [
                            slot.get("assetId")
                            for slot in (s.get("slots") or [])
                            if slot.get("assetId")
                        ],
                    }
                    for s in (ch.get("screens") or [])
                ],
            }
            for ch in chapters
        ]
    }


def plan_legacy_screens(
    buckets: list[list[str]],
    aspects: dict[str, str],
    assets: list[dict],
) -> list[dict]:
    non_empty = [b for b in buckets if b]
    hints = [
        pattern_hint_for_bucket(i + 1, len(non_empty), b, aspects)  # type: ignore[arg-type]
        for i, b in enumerate(non_empty)
    ]
    summary = summarize_orientations(assets, export_layout="web").to_dict()
    return build_chapters_from_buckets(
        buckets,
        aspects,  # type: ignore[arg-type]
        export_layout="web",
        layout_engine="screens",
        assets=assets,
        orientation_summary=summary,
        trip_photo_total=len(assets),
        pattern_hints=hints,
    )


def load_golden(name: str) -> dict[str, Any]:
    path = GOLDEN_DIR / name / "expected.layout.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)
