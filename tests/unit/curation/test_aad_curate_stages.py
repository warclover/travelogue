"""AC-AAD-11 · curate stage unit smoke (AAD-10 shell stages)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from travelogue.config import get_config
from travelogue.curation.curate import (
    CurateError,
    _CurateBucketPlan,
    _CuratePreflight,
    _stage_aesthetic_align,
    _stage_resolve_buckets,
)

pytestmark = pytest.mark.unit


def test_stage_aesthetic_align_noop_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[int] = []

    def _boom(*_a, **_k):
        called.append(1)

    monkeypatch.setattr(
        "travelogue.curation.aesthetic_score.apply_aesthetic_alignment",
        _boom,
    )
    cfg = get_config()
    cfg = replace(cfg, aesthetic=replace(cfg.aesthetic, enabled=False))
    _stage_aesthetic_align({"assets": []}, trip_dir=Path("."), app_cfg=cfg)
    assert called == []


def test_stage_aesthetic_align_calls_when_enabled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    called: list[int] = []

    def _ok(*_a, **_k):
        called.append(1)

    monkeypatch.setattr(
        "travelogue.curation.aesthetic_score.apply_aesthetic_alignment",
        _ok,
    )
    cfg = get_config()
    cfg = replace(cfg, aesthetic=replace(cfg.aesthetic, enabled=True))
    _stage_aesthetic_align({"assets": [{"id": "a"}]}, trip_dir=tmp_path, app_cfg=cfg)
    assert called == [1]


def test_stage_resolve_buckets_tier_requires_structure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "travelogue.layout_engine.adapter.should_layout_only_replan",
        lambda *_a, **_k: MagicMock(layout_only=False, reason=None),
    )
    monkeypatch.setattr(
        "travelogue.curation.curate._build_layout_only_bucket_plan",
        lambda *_a, **_k: None,
    )
    pre = MagicMock(spec=_CuratePreflight)
    pre.app_cfg = get_config()
    with pytest.raises(CurateError) as ei:
        _stage_resolve_buckets(
            {},
            pre,
            curate_scope="tier",
            trip_dir=None,
            cohort_summary=None,
        )
    assert ei.value.code == "E_CURATE_NO_STRUCTURE"


def test_stage_resolve_buckets_full_builds(monkeypatch: pytest.MonkeyPatch) -> None:
    plan = _CurateBucketPlan(
        buckets=[["a", "b"]],
        bucket_segment_ids=["s1"],
        bucket_segment_ids_all=[["s1"]],
        segments=[],
        segment_labels={},
        curation_segments=[],
        meta_places=[],
    )
    monkeypatch.setattr(
        "travelogue.layout_engine.adapter.should_layout_only_replan",
        lambda *_a, **_k: MagicMock(layout_only=False, reason=None),
    )
    monkeypatch.setattr(
        "travelogue.curation.curate._build_curate_buckets",
        lambda *_a, **_k: plan,
    )
    monkeypatch.setattr(
        "travelogue.curation.album_profile.write_album_profile",
        lambda *_a, **_k: None,
    )
    pre = MagicMock(spec=_CuratePreflight)
    pre.app_cfg = get_config()
    out = _stage_resolve_buckets(
        {"curation": {}},
        pre,
        curate_scope="full",
        trip_dir=None,
        cohort_summary={"faces": 1},
    )
    assert out is plan
    assert out.buckets == [["a", "b"]]
