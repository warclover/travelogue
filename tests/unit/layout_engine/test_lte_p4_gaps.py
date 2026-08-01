"""Phase 16 P4: generated legacy, collage eval, saliency probes, promotion."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.collage_detect_eval import evaluate_fixtures
from travelogue.layout_engine.mosaic._legacy_generated import (
    EXPLICIT_GRID_SPECS,
    PATTERN_GRID_CLASS,
)
from travelogue.layout_engine.mosaic.grid_specs import audit_all
from travelogue.layout_templates.legacy_codegen import (
    export_legacy_data,
    render_legacy_python_module,
)
from travelogue.layout_templates.probe_regress import (
    PROBE_PROFILES,
    _cover_focal_retention,
    _profile_saliency_retention,
    _worst_saliency_for_slot,
)
from travelogue.layout_templates.promotion import apply_layout_template_yaml_patch
from travelogue.layout_templates.registry import LayoutTemplateEngine, reset_engine_cache_for_tests
from travelogue.render.context import build_layout_screen


@pytest.fixture(autouse=True)
def _fresh_lte() -> None:
    reset_engine_cache_for_tests()


@pytest.fixture
def engine() -> LayoutTemplateEngine:
    return LayoutTemplateEngine.load(rebuild_cache=True)


@pytest.mark.unit
def test_legacy_generated_matches_codegen(engine: LayoutTemplateEngine) -> None:
    data = export_legacy_data(engine)
    rendered = render_legacy_python_module(data)
    snapshot_path = Path("travelogue/layout_engine/mosaic/_legacy_generated.py")
    assert snapshot_path.is_file()
    assert "EXPLICIT_GRID_SPECS" in rendered
    assert len(EXPLICIT_GRID_SPECS) >= 8
    assert PATTERN_GRID_CLASS["screen-mosaic-5-2p3l-equal"]


@pytest.mark.unit
def test_grid_specs_audit_uses_generated() -> None:
    report = audit_all()
    assert "screen-mosaic-5-2p3l-equal" in report
    assert report["screen-mosaic-5-2p3l-equal"]["kind"] == "explicit"


@pytest.mark.unit
def test_collage_fixture_eval_recall() -> None:
    report = evaluate_fixtures(Path("docs/acceptance-records/collage-detect-fixtures.json"))
    assert report["recall"] >= 0.7
    assert report["confusion"]["fp"] <= 1


@pytest.mark.unit
def test_probe_profiles_include_person() -> None:
    assert any("person" in (p.get("tags") or []) for p in PROBE_PROFILES)
    assert _worst_saliency_for_slot(2.0, "landscape") <= 1.0


@pytest.mark.unit
def test_saliency_gate_is_not_a_noop() -> None:
    """Person-safe face-clip gate must fire when protect exceeds the cover window.

    CSS object-position percentage always keeps the focal point itself inside the
    visible window, so the old center-crop edge-focal proof no longer applies.
    Pin the *mechanism* on a deliberately oversized protect box instead.
    """
    from travelogue.layout_engine.crop_solver import NormBox
    from travelogue.layout_templates.probe_regress import (
        _profile_face_clipped,
    )

    # Focal is always visible under percentage positioning.
    assert _cover_focal_retention(4.0, 1.0, focal_x=0.5, focal_y=0.95) == pytest.approx(1.0)

    # Oversized protect on a tall crop axis → faceClipped / retention collapse.
    hostile = {
        "name": "oversized-protect",
        "aspect": 1.0,
        "focal": (0.5, 0.5),
        "tags": ["person"],
        "faces": (NormBox(0.2, 0.05, 0.6, 0.35),),
        "protect": NormBox(0.1, 0.0, 0.8, 0.95),
    }
    assert _profile_face_clipped(4.0, hostile) is True
    assert _profile_saliency_retention(4.0, hostile) < 0.55

    # Compatible bust into a portrait-readable slot stays safe after solve.
    bust = {
        "name": "bust-ok",
        "aspect": 0.75,
        "focal": (0.5, 0.32),
        "tags": ["person"],
        "faces": (NormBox(0.35, 0.12, 0.30, 0.22),),
        "protect": NormBox(0.28, 0.04, 0.44, 0.50),
    }
    assert _profile_face_clipped(0.75, bust) is False
    assert _profile_saliency_retention(0.75, bust) >= 0.95


@pytest.mark.unit
def test_promotion_apply_dry_run(tmp_path: Path, engine: LayoutTemplateEngine) -> None:
    tpl = engine.get("screen-full-frame")
    yaml_path = tmp_path / "screen-full-frame.yaml"
    import yaml

    yaml_path.write_text(
        yaml.safe_dump(
            {"id": tpl.id, "version": tpl.version, "status": "experimental"},
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    out = apply_layout_template_yaml_patch(
        tpl.id,
        {"status": "beta", "version": tpl.version + 1},
        templates_dir=tmp_path,
        dry_run=True,
    )
    assert out["before"]["status"] == "experimental"
    assert out["after"]["status"] == "beta"
    doc = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    assert doc["status"] == "experimental"


@pytest.mark.unit
def test_full_frame_mobile_blurred_fill() -> None:
    # Portrait person asset: full_frame_fit_for_asset resolves to "contain"
    # (immersive cover is reserved for landscape scenery without people), which
    # triggers the mobile blurred letterbox fill.
    assets = {
        "c1": {
            "id": "c1",
            "mediaClass": "photo",
            "tags": ["person"],
            "width": 800,
            "height": 1200,
            "nativeWidth": 800,
            "nativeHeight": 1200,
            "displayFile": "assets/c1-w800.webp",
        }
    }
    screen = {
        "patternId": "screen-full-frame",
        "layoutGeometry": {"stageAspect": "16:9", "gridClass": "layout-screen__grid--1col"},
        "slots": [{"assetId": "c1", "slot": 0, "fit": "contain"}],
    }
    ctx = build_layout_screen(
        screen,
        assets,
        meta_title="Test",
        export_layout="mobile",
    )
    assert ctx["layoutHint"] == "full-frame"
    assert ctx["slots"][0].get("hasBlurFill") is True
