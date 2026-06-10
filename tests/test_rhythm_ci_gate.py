"""排版规则优化 B3 · 节奏 post-check CI 断言门禁（OQ-09=B 渐进收口）。

灰度观测期（mode=log）已在 demo 样本连续多轮 violations=0，
此处将 R-06 / R-08 / V-09 审计升级为 CI 硬断言：合成代表性样本
（竖版重 / mosaic 混排 / 人物竖版）规划结果必须零节奏违规。
"""

from __future__ import annotations

from tests._golden.helpers import (
    build_mosaic_eligible_trip,
    build_person_portrait_layout_trip,
    build_portrait_heavy_trip,
    plan_legacy_screens,
    plan_mosaic_screens,
)
from travelogue.curation.layout_constraints import audit_rhythm_violations


def _assert_zero_violations(chapters: list[dict]) -> None:
    viol = audit_rhythm_violations(chapters)
    assert viol == [], [v.to_dict() for v in viol]


def test_ci_gate_portrait_heavy_legacy() -> None:
    buckets, aspects, assets = build_portrait_heavy_trip()
    _assert_zero_violations(plan_legacy_screens(buckets, aspects, assets))


def test_ci_gate_person_portraits_legacy() -> None:
    buckets, aspects, assets = build_person_portrait_layout_trip()
    _assert_zero_violations(plan_legacy_screens(buckets, aspects, assets))


def test_ci_gate_mosaic_eligible_mcs() -> None:
    buckets, aspects, assets = build_mosaic_eligible_trip()
    _assert_zero_violations(plan_mosaic_screens(buckets, aspects, assets))


def test_ci_gate_long_portrait_run_with_breaks() -> None:
    """R-08 · 长竖版游程 + 横版可换气：朝向 streak 必须被强制打断。"""
    from tests._golden.helpers import _asset
    from travelogue.curation.curate_patterns import pattern_hint_for_bucket
    from travelogue.curation.layout_planner import (
        build_chapters_from_buckets,
        summarize_orientations,
    )

    assets = [
        _asset(f"p{i:02d}", 900, 1600, offset_hours=i * 0.1) for i in range(16)
    ] + [
        _asset(f"l{i}", 2000, 1200, offset_hours=2.0 + i * 0.1) for i in range(4)
    ]
    buckets = [[a["id"] for a in assets]]
    aspects = {a["id"]: a["aspectKind"] for a in assets}
    hints = [pattern_hint_for_bucket(1, 1, buckets[0], aspects)]  # type: ignore[arg-type]
    chapters = build_chapters_from_buckets(
        buckets,
        aspects,  # type: ignore[arg-type]
        export_layout="web",
        layout_engine="screens",
        assets=assets,
        orientation_summary=summarize_orientations(assets, export_layout="web").to_dict(),
        trip_photo_total=len(assets),
        pattern_hints=hints,
    )
    _assert_zero_violations(chapters)
