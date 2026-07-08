"""P17 CAP-14 editorial hints + CAP-15 highlight windows."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from scripts.phase3_ig2_report import _cfg_for_mode, load_fixture_trip
from travelogue.layout_engine.editorial_hints import build_editorial_hints
from travelogue.layout_engine.highlight_windows import (
    begin_chapter_highlight_windows,
    clear_chapter_highlight_windows,
    current_highlight_boost,
    detect_highlight_windows,
)


def test_detect_highlight_windows_top_windows() -> None:
    assets = [
        {"id": f"a{i}", "quality": {"sharpness": 0.3 + i * 0.05}, "tags": ["person"] if i % 2 == 0 else []}
        for i in range(12)
    ]
    assets_map = {a["id"]: a for a in assets}
    ids = [a["id"] for a in assets]
    windows = detect_highlight_windows(ids, assets_map, window_sizes=(5,), max_windows=1)
    assert len(windows) == 1
    assert len(windows[0]) == 5


def test_current_highlight_boost_context() -> None:
    begin_chapter_highlight_windows((frozenset({"a", "b", "c"}),))
    try:
        assert current_highlight_boost(["a", "b", "c"], default_boost=1.25) == 1.25
        assert current_highlight_boost(["x", "y"], default_boost=1.25) == 1.0
    finally:
        clear_chapter_highlight_windows()


def test_build_editorial_hints_breath_and_folio() -> None:
    chapters = [
        {
            "id": "ch-01",
            "screens": [
                {"patternId": "screen-landscape-3", "slots": [{}, {}, {}]},
                {"patternId": "screen-mosaic-5-main-hero-plus-4", "slots": [{}, {}, {}, {}, {}]},
                {"patternId": "screen-landscape-4", "slots": [{}, {}, {}, {}]},
                {
                    "patternId": "screen-landscape-1",
                    "slots": [{"assetId": "a1", "displayAspect": 1.6}],
                },
                {
                    "patternId": "screen-landscape-1",
                    "slots": [{"assetId": "a2", "displayAspect": 1.5}],
                },
            ],
        }
    ]
    assets = {
        "a1": {"id": "a1", "dominantTone": "#E8A050"},
        "a2": {"id": "a2", "dominantTone": "#E8A060"},
    }
    hints = build_editorial_hints(chapters, assets, breath_gap_threshold=2)
    assert hints["version"] == 1
    assert hints["chapters"]
    ch0 = hints["chapters"][0]
    assert "breathHint" in ch0 or "folioHint" in ch0


def test_curate_writes_editorial_hints_when_cap_on(tmp_path: Path) -> None:
    trip = load_fixture_trip("golden-p17-mixed-person")
    base = _cfg_for_mode("p3_full")
    se = replace(base.layout.strategy_engine, enabled=True)
    caps = replace(se.capabilities, editorial_hints=True)
    cfg = replace(base, layout=replace(base.layout, strategy_engine=replace(se, capabilities=caps)))
    body = dict(trip)
    body.setdefault("pipeline", {})["status"] = "structure_draft"
    body.pop("chapters", None)
    from travelogue.curation.clustering import run_clustering_layer
    from travelogue.curation.curate import run_curate

    run_clustering_layer(body, trip_dir=tmp_path / "cl", cfg=cfg)
    run_curate(body, apply_layout=True, trip_dir=tmp_path, cfg=cfg)
    hints = (body.get("curation") or {}).get("editorialHints")
    assert isinstance(hints, dict)
    assert hints.get("version") == 1


def test_editorial_hints_unchanged_when_cap_off(tmp_path: Path) -> None:
    """AC-P17-25 · cap off 时 editorial 快照与 baseline 一致。"""
    trip = load_fixture_trip("golden-p17-mixed-person")
    base = _cfg_for_mode("p3_full")
    se_off = replace(base.layout.strategy_engine, enabled=True)
    caps_off = replace(se_off.capabilities, editorial_hints=False, highlight_windows=False)
    cfg_off = replace(
        base,
        layout=replace(base.layout, strategy_engine=replace(se_off, capabilities=caps_off)),
    )
    body = dict(trip)
    body.setdefault("pipeline", {})["status"] = "structure_draft"
    body.pop("chapters", None)
    from travelogue.curation.clustering import run_clustering_layer
    from travelogue.curation.curate import run_curate

    run_clustering_layer(body, trip_dir=tmp_path / "cl-off", cfg=cfg_off)
    run_curate(body, apply_layout=True, trip_dir=tmp_path / "off", cfg=cfg_off)
    hints_off = (body.get("curation") or {}).get("editorialHints")
    assert hints_off is None or hints_off == {}


def test_editorial_render_snapshot_unchanged_without_hints() -> None:
    """AC-P17-25 · 无 editorialHints 时 breath/folio 渲染输入不变。"""
    from travelogue.layout_engine.editorial_hints import build_editorial_hints

    chapters = [
        {
            "id": "ch-01",
            "screens": [
                {"patternId": "screen-landscape-1", "slots": [{"assetId": "a1"}]},
            ],
        }
    ]
    assets = {"a1": {"id": "a1", "dominantTone": "#ccc"}}
    hints = build_editorial_hints(chapters, assets, breath_gap_threshold=99)
    assert hints.get("chapters") == [] or not hints.get("chapters")
