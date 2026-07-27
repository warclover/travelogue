"""Unit tests for person-safe cover crop solver."""

from __future__ import annotations

from travelogue.layout_engine.crop_solver import (
    NormBox,
    apply_slot_crop_focals,
    cover_window,
    crop_safety,
    faces_from_asset,
    protect_box_from_asset,
    solve_slot_focal,
)


def test_cover_window_vertical_uses_percentage_not_center() -> None:
    # slot taller than asset → crop Y; py=0 pins top, py=1 pins bottom
    top = cover_window(slot_ar=1.0, asset_ar=0.5, px=0.5, py=0.0)
    assert top.axis == "y"
    assert abs(top.visible_h - 0.5) < 1e-9
    assert abs(top.y0) < 1e-9

    bottom = cover_window(slot_ar=1.0, asset_ar=0.5, px=0.5, py=1.0)
    assert abs(bottom.y0 - 0.5) < 1e-9

    mid = cover_window(slot_ar=1.0, asset_ar=0.5, px=0.5, py=0.5)
    assert abs(mid.y0 - 0.25) < 1e-9


def test_cover_window_horizontal_uses_percentage() -> None:
    left = cover_window(slot_ar=0.5, asset_ar=1.0, px=0.0, py=0.5)
    assert left.axis == "x"
    assert abs(left.visible_w - 0.5) < 1e-9
    assert abs(left.x0) < 1e-9

    right = cover_window(slot_ar=0.5, asset_ar=1.0, px=1.0, py=0.5)
    assert abs(right.x0 - 0.5) < 1e-9


def test_solve_shifts_focal_to_keep_protect_inside() -> None:
    # Wide landscape photo into square-ish tall slot → vertical crop.
    # Face near top; default prefer (0.5, 0.45) would leave top out if center-cropped,
    # but percentage with solved py should keep protect inside.
    asset = {
        "width": 1000,
        "height": 2000,  # ar=0.5
        "focalPoint": {"x": 0.5, "y": 0.8},  # prefer bottom
        "protectBox": {"x": 0.35, "y": 0.05, "w": 0.3, "h": 0.2},  # near top
        "faces": [{"x": 0.40, "y": 0.08, "w": 0.2, "h": 0.12}],
    }
    result = solve_slot_focal(asset, slot_ar=1.0)  # vh = 0.5
    assert result.feasible
    # py must be low enough that window covers y in [0.05, 0.25]
    assert result.focal_y < 0.45
    win = result.window
    assert win.y0 <= 0.05 + 1e-6
    assert win.y1 >= 0.25 - 1e-6
    assert not result.safety.face_clipped
    assert result.safety.protect_containment >= 0.99


def test_solve_infeasible_when_protect_taller_than_window() -> None:
    asset = {
        "width": 1000,
        "height": 2000,  # ar=0.5
        "focalPoint": {"x": 0.5, "y": 0.5},
        "protectBox": {"x": 0.2, "y": 0.1, "w": 0.6, "h": 0.7},  # taller than vh=0.5
        "faces": [{"x": 0.35, "y": 0.15, "w": 0.3, "h": 0.25}],
    }
    result = solve_slot_focal(asset, slot_ar=1.0)
    assert not result.feasible
    # Still centers protect; face may be clipped
    assert 0.0 <= result.focal_y <= 1.0


def test_boundary_py_zero_and_one() -> None:
    asset_top = {
        "width": 800,
        "height": 1600,
        "focalPoint": {"x": 0.5, "y": 0.5},
        "protectBox": {"x": 0.4, "y": 0.0, "w": 0.2, "h": 0.2},
        "faces": [{"x": 0.4, "y": 0.0, "w": 0.2, "h": 0.15}],
    }
    r0 = solve_slot_focal(asset_top, 1.0)
    assert abs(r0.focal_y) < 1e-6 or r0.focal_y < 0.05

    asset_bot = {
        "width": 800,
        "height": 1600,
        "focalPoint": {"x": 0.5, "y": 0.5},
        "protectBox": {"x": 0.4, "y": 0.8, "w": 0.2, "h": 0.2},
        "faces": [{"x": 0.4, "y": 0.82, "w": 0.2, "h": 0.15}],
    }
    r1 = solve_slot_focal(asset_bot, 1.0)
    assert r1.focal_y > 0.9


def test_no_person_asset_unchanged() -> None:
    asset = {
        "width": 1600,
        "height": 900,
        "focalPoint": {"x": 0.42, "y": 0.33},
    }
    result = solve_slot_focal(asset, slot_ar=1.5)
    assert result.feasible
    assert abs(result.focal_x - 0.42) < 1e-9
    assert abs(result.focal_y - 0.33) < 1e-9
    assert not result.safety.has_person
    assert not result.safety.face_clipped


def test_face_clipped_detects_half_face() -> None:
    win = cover_window(1.0, 0.5, 0.5, 0.5)  # y0=0.25, y1=0.75
    face = NormBox(0.4, 0.20, 0.2, 0.15)  # straddles top edge
    safety = crop_safety(window=win, faces=[face], protect=face)
    assert safety.face_clipped


def test_protect_box_fallback_chain() -> None:
    assert protect_box_from_asset({"protectBox": {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2}}).x == 0.1
    faces_asset = {"faces": [{"x": 0.2, "y": 0.2, "w": 0.1, "h": 0.1}, {"x": 0.5, "y": 0.3, "w": 0.1, "h": 0.1}]}
    u = protect_box_from_asset(faces_asset)
    assert u is not None
    assert abs(u.x - 0.2) < 1e-9
    assert abs(u.x1 - 0.6) < 1e-9
    assert protect_box_from_asset({"salientBox": {"x": 0.3, "y": 0.3, "w": 0.2, "h": 0.2}}).x == 0.3
    assert protect_box_from_asset({}) is None


def test_faces_from_asset_normalized_only() -> None:
    assert len(faces_from_asset({"faces": [{"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2}]})) == 1
    # Pixel-like tuples (>1) are ignored without image dims
    assert faces_from_asset({"faces": [(10, 20, 100, 120)]}) == []
    assert len(faces_from_asset({"salientBox": {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2}})) == 1


def test_apply_slot_crop_focals_writes_fields() -> None:
    screen = {
        "slots": [
            {
                "slot": 0,
                "assetId": "a0",
                "fit": "cover",
                "displayAspect": 1.0,
            },
            {
                "slot": 1,
                "assetId": "a1",
                "fit": "contain",
                "displayAspect": 1.0,
            },
        ]
    }
    assets = {
        "a0": {
            "width": 1000,
            "height": 2000,
            "focalPoint": {"x": 0.5, "y": 0.8},
            "protectBox": {"x": 0.35, "y": 0.05, "w": 0.3, "h": 0.2},
            "faces": [{"x": 0.4, "y": 0.08, "w": 0.2, "h": 0.12}],
        },
        "a1": {"width": 1000, "height": 2000, "focalPoint": {"x": 0.5, "y": 0.5}},
    }
    summaries = apply_slot_crop_focals(screen, assets_map=assets)
    assert "cropFocal" in screen["slots"][0]
    assert "cropSafety" in screen["slots"][0]
    assert screen["slots"][0]["cropFocal"]["y"] < 0.45
    assert "cropFocal" not in screen["slots"][1]
    assert summaries[0]["feasible"] is True
    assert summaries[1]["skipped"] is True


def test_apply_slot_crop_focals_flips_contain_when_unsafe() -> None:
    screen = {
        "slots": [
            {
                "slot": 0,
                "assetId": "a0",
                "fit": "cover",
                "displayAspect": 3.5,  # ultra-wide stack slot
            }
        ]
    }
    assets = {
        "a0": {
            "width": 1000,
            "height": 1500,
            "focalPoint": {"x": 0.5, "y": 0.4},
            "protectBox": {"x": 0.2, "y": 0.1, "w": 0.6, "h": 0.7},
            "faces": [{"x": 0.35, "y": 0.15, "w": 0.3, "h": 0.25}],
        }
    }
    summaries = apply_slot_crop_focals(screen, assets_map=assets)
    assert screen["slots"][0]["fit"] == "contain"
    assert screen["slots"][0].get("cropContain") is True
    assert summaries[0]["containFlipped"] is True
