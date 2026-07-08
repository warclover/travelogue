"""Narrative services respect explicit cfg= over global config."""

from __future__ import annotations

from dataclasses import replace

import pytest

from travelogue.config import NarrativeConfig, config_override, get_config, reset_config_cache
from travelogue.render.context import build_render_context
from travelogue.render.golden_regression import load_golden_trip
from travelogue.services.narrative_scope import resolve_narrative_scope
from travelogue.services.narrative_validate import banned_phrases, validate_narrative


@pytest.fixture(autouse=True)
def _reset_config_cache():
    reset_config_cache()
    yield
    reset_config_cache()


def test_resolve_narrative_scope_uses_cfg_param():
    global_cfg = replace(get_config(), narrative=NarrativeConfig(scope="frame"))
    local_cfg = replace(get_config(), narrative=NarrativeConfig(scope="full"))

    with config_override(global_cfg):
        assert resolve_narrative_scope(cfg=local_cfg) == "full"
        assert resolve_narrative_scope() == "frame"


def test_banned_phrases_uses_cfg_param():
    custom = ("自定义禁用",)
    global_cfg = get_config()
    local_cfg = replace(global_cfg, narrative=NarrativeConfig(banned_phrases=custom))

    with config_override(global_cfg):
        assert "自定义禁用" in banned_phrases(local_cfg)
        assert "自定义禁用" not in banned_phrases()


def test_validate_narrative_uses_cfg_banned_phrases():
    trip = {
        "meta": {"hook": "综上所述，一段旅程。"},
        "assets": [],
        "chapters": [],
    }
    local_cfg = replace(get_config(), narrative=NarrativeConfig(banned_phrases=("综上所述",)))

    issues = validate_narrative(trip, cfg=local_cfg)
    assert any("VR-N01" in issue for issue in issues)


def test_build_render_context_cover_title_respects_cfg_scope():
    import copy

    trip = copy.deepcopy(load_golden_trip())
    trip.setdefault("meta", {})["title"] = "测试标题"
    trip.setdefault("curation", {}).pop("narrativeScope", None)

    frame_cfg = replace(get_config(), narrative=NarrativeConfig(scope="frame"))
    full_cfg = replace(get_config(), narrative=NarrativeConfig(scope="full"))

    with config_override(frame_cfg):
        ctx_frame = build_render_context(trip, cfg=full_cfg, reading_profile_override="legacy")
    assert ctx_frame["coverShowTitle"] is True

    with config_override(full_cfg):
        ctx_full = build_render_context(trip, cfg=frame_cfg, reading_profile_override="legacy")
    assert ctx_full["coverShowTitle"] is False
