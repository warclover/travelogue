"""Helpers to build mini trips and capture layout snapshots for golden tests."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from travelogue.config import get_config
from travelogue.curation.curate_patterns import pattern_hint_for_bucket
from travelogue.curation.layout_planner import build_chapters_from_buckets, summarize_orientations
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
    base = datetime(2025, 6, 1, 10, 0, tzinfo=UTC)
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


def build_mosaic_portrait3_trip() -> tuple[list[list[str]], dict[str, str], list[dict]]:
    """Single bucket of 3 portraits — MCS golden for screen-portrait-3."""
    assets = [_asset(f"p{i}", 900, 1600, offset_hours=i * 0.01) for i in range(1, 4)]
    buckets = [[a["id"] for a in assets]]
    aspects = {a["id"]: a["aspectKind"] for a in assets}
    return buckets, aspects, assets


def build_mosaic_portrait4_trip() -> tuple[list[list[str]], dict[str, str], list[dict]]:
    """Single bucket of 4 portraits — MCS golden for screen-portrait-4."""
    assets = [_asset(f"p{i}", 900, 1600, offset_hours=i * 0.01) for i in range(1, 5)]
    buckets = [[a["id"] for a in assets]]
    aspects = {a["id"]: a["aspectKind"] for a in assets}
    return buckets, aspects, assets


def build_mosaic_portrait8_trip() -> tuple[list[list[str]], dict[str, str], list[dict]]:
    """Eight portraits in one bucket — MCS golden for screen-portrait-grid-8."""
    assets = [
        _asset(f"p{i}", 900, 1600, offset_hours=(i * 8.0) / 3600.0) for i in range(1, 9)
    ]
    buckets = [[a["id"] for a in assets]]
    aspects = {a["id"]: a["aspectKind"] for a in assets}
    return buckets, aspects, assets


def build_mosaic_landscape9_trip() -> tuple[list[list[str]], dict[str, str], list[dict]]:
    """Nine landscapes — MCS golden for screen-landscape-9 (trip_total>50 for nine quota)."""
    assets = [_asset(f"l{i}", 2000, 1200, offset_hours=i * 0.01) for i in range(1, 10)]
    buckets = [[a["id"] for a in assets]]
    aspects = {a["id"]: a["aspectKind"] for a in assets}
    return buckets, aspects, assets


def build_mosaic_landscape6_trip() -> tuple[list[list[str]], dict[str, str], list[dict]]:
    """Single bucket of 6 landscapes — MCS golden for screen-landscape-6."""
    assets = [_asset(f"l{i}", 2000, 1200, offset_hours=i * 0.01) for i in range(1, 7)]
    buckets = [[a["id"] for a in assets]]
    aspects = {a["id"]: a["aspectKind"] for a in assets}
    return buckets, aspects, assets


def build_mosaic_eligible_trip() -> tuple[list[list[str]], dict[str, str], list[dict]]:
    """40 assets (8×5) — trip_total≥35, each window has 3P+2L for mosaic-5 candidates."""
    assets: list[dict] = []
    aspects: dict[str, str] = {}
    buckets: list[list[str]] = []
    for b in range(8):
        bucket: list[str] = []
        for i in range(5):
            idx = b * 5 + i
            aid = f"m{idx:02d}"
            kind = "portrait" if i < 3 else "landscape"
            assets.append(
                _asset(
                    aid,
                    900 if kind == "portrait" else 2000,
                    1600 if kind == "portrait" else 1200,
                    offset_hours=float(idx) * 0.1,
                    sharpness=0.75,
                )
            )
            aspects[aid] = assets[-1]["aspectKind"]
            bucket.append(aid)
        buckets.append(bucket)
    return buckets, aspects, assets


def build_mixed_aspects_trip() -> tuple[list[list[str]], dict[str, str], list[dict]]:
    """6 assets · 2×3-window MCS (portrait + 2 landscape per bucket)."""
    assets = [
        _asset("p1", 900, 1600, offset_hours=0),
        _asset("l1", 2000, 1200, offset_hours=0.5),
        _asset("l2", 2000, 1200, offset_hours=1),
        _asset("p2", 900, 1600, offset_hours=24),
        _asset("l3", 2000, 1200, offset_hours=24.5),
        _asset("l4", 2000, 1200, offset_hours=25),
    ]
    buckets = [["p1", "l1", "l2"], ["p2", "l3", "l4"]]
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


def _mosaic_cfg_for_golden():
    base = get_config()
    return replace(
        base,
        mosaic=replace(
            base.mosaic,
            enabled=True,
            enabled_window_sizes=(3, 4, 5, 6, 8, 9),
            unified_mode=True,
            scorer_version="p15-s2",
            min_candidate_score=0.0,
        ),
    )


def plan_mosaic_screens(
    buckets: list[list[str]],
    aspects: dict[str, str],
    assets: list[dict],
    *,
    trip_photo_total: int | None = None,
    orientation_summary: dict[str, int] | None = None,
) -> list[dict]:
    """Plan with Phase 15 MCS enabled (S2 unified windows)."""
    import travelogue.config as config_mod

    cfg = _mosaic_cfg_for_golden()
    orig = config_mod.get_config
    config_mod.get_config = lambda: cfg  # type: ignore[assignment]
    try:
        return plan_legacy_screens(
            buckets,
            aspects,
            assets,
            trip_photo_total=trip_photo_total,
            orientation_summary=orientation_summary,
        )
    finally:
        config_mod.get_config = orig


def build_layout_density_golden_trip() -> tuple[list[list[str]], dict[str, str], list[dict]]:
    """≥35 assets · demo-day-3 equivalent for layout-density CI (mixed mosaic windows)."""
    buckets, aspects, assets = build_mosaic_eligible_trip()
    for a in assets:
        if aspects.get(a["id"]) == "portrait":
            a["tags"] = ["person"]
    return buckets, aspects, assets


def build_chapter_hero_layout_trip() -> tuple[list[list[str]], dict[str, str], list[dict]]:
    """Single chapter · 10 landscapes — chapter hero (AC-LD-08) without mosaic skip."""
    assets = [
        _asset(f"l{i}", 2000, 1200, offset_hours=i * 0.05, sharpness=0.85)
        for i in range(1, 11)
    ]
    buckets = [[a["id"] for a in assets]]
    aspects = {a["id"]: a["aspectKind"] for a in assets}
    return buckets, aspects, assets


def build_person_portrait_layout_trip() -> tuple[list[list[str]], dict[str, str], list[dict]]:
    """Portraits tagged person — face contain contract (AC-LD-08)."""
    assets = [
        _asset(f"p{i}", 900, 1600, offset_hours=i * 0.1, sharpness=0.8)
        for i in range(1, 7)
    ]
    for a in assets:
        a["tags"] = ["person"]
    buckets = [[a["id"] for a in assets]]
    aspects = {a["id"]: a["aspectKind"] for a in assets}
    return buckets, aspects, assets


def plan_legacy_screens(
    buckets: list[list[str]],
    aspects: dict[str, str],
    assets: list[dict],
    *,
    mosaic_enabled: bool | None = None,
    trip_photo_total: int | None = None,
    orientation_summary: dict[str, int] | None = None,
    layout_density: str | None = None,
) -> list[dict]:
    if mosaic_enabled is not None:
        import travelogue.config as config_mod

        base = get_config()
        patched = replace(
            base,
            mosaic=replace(base.mosaic, enabled=mosaic_enabled),
        )
        orig = config_mod.get_config
        config_mod.get_config = lambda: patched  # type: ignore[assignment]
        try:
            return plan_legacy_screens(buckets, aspects, assets)
        finally:
            config_mod.get_config = orig

    non_empty = [b for b in buckets if b]
    hints = [
        pattern_hint_for_bucket(i + 1, len(non_empty), b, aspects)  # type: ignore[arg-type]
        for i, b in enumerate(non_empty)
    ]
    summary = orientation_summary or summarize_orientations(
        assets, export_layout="web"
    ).to_dict()
    total = trip_photo_total if trip_photo_total is not None else len(assets)
    return build_chapters_from_buckets(
        buckets,
        aspects,  # type: ignore[arg-type]
        export_layout="web",
        layout_engine="screens",
        assets=assets,
        orientation_summary=summary,
        trip_photo_total=total,
        pattern_hints=hints,
        layout_density=layout_density,
    )


def load_golden(name: str) -> dict[str, Any]:
    path = GOLDEN_DIR / name / "expected.layout.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)
