"""Explicit cfg= injection and serve config pinning."""

from __future__ import annotations

import copy
import json
import threading
from dataclasses import replace

import pytest

from travelogue.config import (
    LayoutConfig,
    RenderConfig,
    RenderReadingConfig,
    config_override,
    default_mixed_proximity_seconds,
    default_screen_plan_scope,
    default_web_layout_engine,
    get_config,
    reading_profile_defaults,
    reset_config_cache,
)
from travelogue.render.context import build_render_context
from travelogue.render.golden_regression import load_golden_trip
from travelogue.render.reading_profile import load_experience_matrix, reset_experience_matrix_cache
from travelogue.web.serve import TripPreviewHandler


@pytest.fixture(autouse=True)
def _reset_caches():
    reset_config_cache()
    reset_experience_matrix_cache()
    yield
    reset_config_cache()
    reset_experience_matrix_cache()


def test_reading_profile_defaults_from_cfg():
    base = get_config()
    cfg = replace(
        base,
        render=RenderConfig(
            reading=RenderReadingConfig(
                default_profile="performance",
                share_profile="legacy",
                mobile_profile="magazine",
                longshot_surface_profile="default_hybrid",
            )
        ),
    )
    defaults = reading_profile_defaults(cfg)
    assert defaults["draft_web_profile"] == "performance"
    assert defaults["mobile_profile"] == "magazine"


def test_build_render_context_cfg_param_beats_global():
    trip = copy.deepcopy(load_golden_trip())
    global_cfg = replace(
        get_config(),
        render=RenderConfig(reading=RenderReadingConfig(default_profile="legacy")),
    )
    local_cfg = replace(
        get_config(),
        render=RenderConfig(reading=RenderReadingConfig(default_profile="performance")),
    )
    with config_override(global_cfg):
        ctx = build_render_context(trip, cfg=local_cfg)
    profile = json.loads(ctx["readingJson"])["profile"]
    assert profile == "performance"


def test_experience_matrix_cache_tracks_mtime(tmp_path, monkeypatch):
    matrix = tmp_path / "experience-matrix.yaml"
    matrix.write_text("profiles: {}\ndefaults: {}\n", encoding="utf-8")
    monkeypatch.setattr(
        "travelogue.render.reading_profile._MATRIX_PATH",
        matrix,
    )
    reset_experience_matrix_cache()
    first = load_experience_matrix()
    matrix.write_text("profiles: {x: {}}\ndefaults: {}\n", encoding="utf-8")
    second = load_experience_matrix()
    assert first is not second


def test_serve_handler_config_scope_isolates_threads():
    base = get_config()
    results: dict[str, str] = {}
    barrier = threading.Barrier(2)
    handler = TripPreviewHandler.__new__(TripPreviewHandler)

    def worker(name: str, profile: str) -> None:
        cfg = replace(
            base,
            render=RenderConfig(reading=RenderReadingConfig(default_profile=profile)),
        )
        handler.app_config = cfg
        with handler._app_config_scope():
            barrier.wait(timeout=5)
            results[name] = get_config().render.reading.default_profile

    t_a = threading.Thread(target=worker, args=("a", "legacy"))
    t_b = threading.Thread(target=worker, args=("b", "performance"))
    t_a.start()
    t_b.start()
    t_a.join(timeout=10)
    t_b.join(timeout=10)

    assert results == {"a": "legacy", "b": "performance"}


def test_default_layout_helpers_use_cfg_param():
    base = get_config()
    local = replace(
        base,
        layout=LayoutConfig(
            web_layout_engine="legacy",
            screen_plan_scope="chapter",
            mixed_proximity_seconds=99.0,
        ),
    )
    global_cfg = replace(
        base,
        layout=LayoutConfig(
            web_layout_engine="screens",
            screen_plan_scope="day",
            mixed_proximity_seconds=12.0,
        ),
    )

    with config_override(global_cfg):
        assert default_web_layout_engine("web", cfg=local) == "legacy"
        assert default_screen_plan_scope(cfg=local) == "chapter"
        assert default_mixed_proximity_seconds(cfg=local) == 99.0
        assert default_web_layout_engine("web") == "screens"


def test_apply_layout_to_trip_respects_cfg_engine():
    from travelogue.services.layout import apply_layout_to_trip

    trip = {
        "assets": [
            {"id": f"a{i}", "type": "image", "width": 1600, "height": 900, "aspectKind": "landscape", "layoutEligible": True}
            for i in range(1, 5)
        ],
        "chapters": [],
        "exportLayout": "web",
        "meta": {"title": "t"},
    }
    screens_cfg = replace(get_config(), layout=LayoutConfig(web_layout_engine="screens"))
    legacy_cfg = replace(get_config(), layout=LayoutConfig(web_layout_engine="legacy"))

    with config_override(legacy_cfg):
        result = apply_layout_to_trip(trip, export_layout="web", cfg=screens_cfg)
    assert trip.get("layoutEngine") == "screens"
    assert result.summary_text
