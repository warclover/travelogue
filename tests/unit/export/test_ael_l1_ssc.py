"""AEL L1 SSC — AC-AEL-04/05/06/07/08/09/23/25. Sequence ruler, not PNG hash."""

from __future__ import annotations

import ast
import io
from pathlib import Path

import pytest
from PIL import Image

from travelogue.config.album_editorial import EffectiveAel, album_editorial_lab_from_dict
from travelogue.config.app import AppConfig
from travelogue.export.album_ssc import apply_card_ssc, slots_are_equal_ar
from travelogue.export.card_grouper import CardPlan
from travelogue.export.card_renderer import DEFAULT_BG, SlotCropHint, render_card
from travelogue.export.card_templates import CARD_TEMPLATES
from travelogue.export.collage_pack import collage_plan_fingerprint, export_collage_pack
from travelogue.layout_engine.crop_solver import (
    any_face_outside,
    cover_window,
    group_face_count,
    solve_slot_focal,
)
from travelogue.services.trip_factory import create_trip

pytestmark = pytest.mark.unit

_REPO = Path(__file__).resolve().parents[3]
_CARD = (1080, 1440)


def _ael_crop() -> EffectiveAel:
    return EffectiveAel(
        enabled=True,
        crop=True,
        contain_on_fail=True,
        face_hard_gate=True,
        group_face_min=3,
        max_solve_ms=8000,
    )


def _jpeg(path: Path, *, size: tuple[int, int], color=(40, 80, 160)) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, format="JPEG", quality=90)
    return path


def _seed_kept_photos(trip_dir: Path, n: int) -> None:
    import json

    trip_json = trip_dir / "trip.json"
    data = json.loads(trip_json.read_text(encoding="utf-8"))
    assets = []
    ids: list[str] = []
    for i in range(n):
        aid = f"ael-l1-{i:02d}"
        ids.append(aid)
        rel = f"source/{aid}.jpg"
        size = (900, 600) if i % 2 == 0 else (600, 900)
        _jpeg(trip_dir / rel, size=size, color=(30 + i * 10, 80, 160))
        assets.append(
            {
                "id": aid,
                "type": "image",
                "sourceFile": rel,
                "layoutEligible": True,
            }
        )
    data["assets"] = assets
    curation = data.setdefault("curation", {})
    curation["displayedAssetIds"] = ids
    cull = curation.setdefault("cullSummary", {})
    cull["layoutEligibleCount"] = n
    cull["finalLayoutEligibleCount"] = n
    trip_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _cfg(*, crop: bool) -> AppConfig:
    return AppConfig(
        album_editorial_lab=album_editorial_lab_from_dict(
            {"enabled": True, "crop": {"enabled": crop}}
        )
    )


def _face_inside(asset: dict, slot_ar: float) -> bool:
    solved = solve_slot_focal(asset, slot_ar)
    return not any_face_outside(asset, solved.window)


def test_ac04_face_on_edge_does_not_cover_clip(tmp_path: Path) -> None:
    """Portrait with a too-tall face in card-4 main (1.125) → swap or contain."""
    template = CARD_TEMPLATES["card-4-square-top-triband"]
    risky = _jpeg(tmp_path / "face.jpg", size=(1000, 1333), color=(200, 40, 40))
    safe = [
        _jpeg(tmp_path / f"p{i}.jpg", size=(800, 1200), color=(40, 40 + i * 20, 180))
        for i in range(3)
    ]
    asset_risky = {
        "width": 1000,
        "height": 1333,
        "faces": [{"x": 0.25, "y": 0.0, "w": 0.5, "h": 0.72}],
        "quality": {"faceCount": 1},
    }
    assets = {
        risky: asset_risky,
        **{p: {"width": 800, "height": 1200} for p in safe},
    }
    # Main slot 1.125 crops vertically; face taller than the cover window.
    assert not _face_inside(asset_risky, 1.125)
    plan = CardPlan(template=template, photos=(risky, *safe))
    result = apply_card_ssc(plan, assets.get, _ael_crop())
    idx = list(result.photos).index(risky)
    slot_ar = float(template.slots[idx].display_aspect)
    hint = result.hints[idx]
    if hint.fit == "cover":
        assert _face_inside(asset_risky, slot_ar)
    else:
        assert hint.fit == "contain"


def test_ac04_single_slot_falls_back_to_contain(tmp_path: Path) -> None:
    template = CARD_TEMPLATES["card-1-full-frame"]
    photo = _jpeg(tmp_path / "tall.jpg", size=(1000, 2000), color=(180, 40, 40))
    asset = {
        "width": 1000,
        "height": 2000,
        "faces": [{"x": 0.3, "y": 0.0, "w": 0.4, "h": 0.8}],
        "quality": {"faceCount": 1},
    }
    assert not _face_inside(asset, 0.75)
    result = apply_card_ssc(
        CardPlan(template=template, photos=(photo,)),
        {photo: asset}.get,
        _ael_crop(),
    )
    assert result.hints[0].fit == "contain"


def test_ac05_group_four_faces_not_clipped(tmp_path: Path) -> None:
    template = CARD_TEMPLATES["card-6-bookend-rows"]
    group = _jpeg(tmp_path / "group.jpg", size=(1600, 900), color=(40, 160, 80))
    others = [
        _jpeg(tmp_path / f"o{i}.jpg", size=(1600, 900) if i % 2 == 0 else (800, 1200))
        for i in range(5)
    ]
    faces = [
        {"x": 0.05, "y": 0.20, "w": 0.12, "h": 0.35},
        {"x": 0.25, "y": 0.18, "w": 0.12, "h": 0.35},
        {"x": 0.45, "y": 0.22, "w": 0.12, "h": 0.35},
        {"x": 0.65, "y": 0.20, "w": 0.12, "h": 0.35},
    ]
    asset_group = {
        "width": 1600,
        "height": 900,
        "faces": faces,
        "quality": {"faceCount": 4},
    }
    assert group_face_count(asset_group) == 4
    assert not _face_inside(asset_group, 0.75)
    # Portrait slot index 1 on bookend-rows.
    photos = [others[0], group, others[1], others[2], others[3], others[4]]
    assets = {group: asset_group}
    for p in others:
        assets[p] = {"width": 800, "height": 1200}
    result = apply_card_ssc(
        CardPlan(template=template, photos=tuple(photos)),
        assets.get,
        _ael_crop(),
    )
    idx = list(result.photos).index(group)
    slot_ar = float(template.slots[idx].display_aspect)
    hint = result.hints[idx]
    if hint.fit == "cover":
        solved = solve_slot_focal(asset_group, slot_ar)
        assert not any_face_outside(asset_group, solved.window)
        win = cover_window(slot_ar, 1600 / 900, solved.focal_x, solved.focal_y)
        for box in faces:
            x1 = box["x"] + box["w"]
            y1 = box["y"] + box["h"]
            assert box["x"] >= win.x0 - 1e-6
            assert box["y"] >= win.y0 - 1e-6
            assert x1 <= win.x1 + 1e-6
            assert y1 <= win.y1 + 1e-6
    else:
        assert hint.fit == "contain"


def test_ac05_zero_faces_is_not_a_group() -> None:
    assert group_face_count({"quality": {"faceCount": 0}, "faces": []}) == 0
    assert group_face_count({}) == 0


def test_ac06_landscape_sky_not_hard_cover(tmp_path: Path) -> None:
    template = CARD_TEMPLATES["card-6-bookend-rows"]
    sky = _jpeg(tmp_path / "sky.jpg", size=(1500, 1000), color=(80, 140, 220))
    others = [
        _jpeg(tmp_path / f"s{i}.jpg", size=(800, 1200), color=(90, 90, 90))
        for i in range(5)
    ]
    asset_sky = {
        "width": 1500,
        "height": 1000,
        "focalPoint": {"x": 0.5, "y": 0.10},
    }
    # Portrait slot 1: 3:2 into 0.75 is high crop_risk.
    photos = [others[0], sky, others[1], others[2], others[3], others[4]]
    assets = {sky: asset_sky, **{p: {"width": 800, "height": 1200} for p in others}}
    result = apply_card_ssc(
        CardPlan(template=template, photos=tuple(photos)),
        assets.get,
        _ael_crop(),
    )
    idx = list(result.photos).index(sky)
    slot_ar = float(template.slots[idx].display_aspect)
    hint = result.hints[idx]
    if hint.fit == "cover":
        # Swapped onto a landscape-shaped slot (mismatch collapsed).
        assert slot_ar >= 1.3
    else:
        assert hint.fit == "contain"


def test_ac25_equal_grid_does_not_swap(tmp_path: Path) -> None:
    template = CARD_TEMPLATES["card-9-grid-equal"]
    assert slots_are_equal_ar(template)
    photos = [
        _jpeg(tmp_path / f"g{i}.jpg", size=(800, 1200), color=(i * 20, 40, 80))
        for i in range(9)
    ]
    risky = photos[0]
    assets = {
        risky: {
            "width": 800,
            "height": 1600,
            "faces": [{"x": 0.3, "y": 0.0, "w": 0.4, "h": 0.8}],
            "quality": {"faceCount": 1},
        }
    }
    for p in photos[1:]:
        assets[p] = {"width": 800, "height": 1200}
    result = apply_card_ssc(
        CardPlan(template=template, photos=tuple(photos)),
        assets.get,
        _ael_crop(),
    )
    assert result.photos == tuple(photos)
    assert result.hints[0].fit == "contain"
    assert all(h.fit == "cover" for h in result.hints[1:])


def test_ac08_contain_uses_paper_color(tmp_path: Path) -> None:
    template = CARD_TEMPLATES["card-1-full-frame"]
    photo = _jpeg(tmp_path / "wide.jpg", size=(2000, 1000), color=(220, 30, 30))
    hint = SlotCropHint(fit="contain", focal=(0.5, 0.45))
    data, diag = render_card(
        [photo], template, canvas_wh=_CARD, slot_hints=(hint,)
    )
    assert diag["fit"] == "mixed"
    assert diag["slotFits"] == ["contain"]
    with Image.open(io.BytesIO(data)) as im:
        assert im.getpixel((2, 2)) == DEFAULT_BG
        assert im.getpixel((_CARD[0] // 2, _CARD[1] // 2)) != DEFAULT_BG


def test_ac07_crop_on_does_not_change_template_sequence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    trips = tmp_path / "trips"
    create_trip("ael-l1-seq", trips, title="ael-l1-seq")
    trip_dir = trips / "ael-l1-seq"
    _seed_kept_photos(trip_dir, 8)
    import travelogue.export.collage_pack as pack

    captured: list[tuple] = []
    orig = pack.plan_cards

    def _wrap(*args: object, **kwargs: object):
        plans = orig(*args, **kwargs)
        captured.append(collage_plan_fingerprint(plans))
        return plans

    monkeypatch.setattr(pack, "plan_cards", _wrap)
    export_collage_pack(trip_dir, platform="album_spread", cfg=_cfg(crop=False))
    export_collage_pack(trip_dir, platform="album_spread", cfg=_cfg(crop=True))
    assert len(captured) == 2
    assert captured[0] == captured[1]


def test_xhs_stays_cover_when_ael_crop_on(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    trips = tmp_path / "trips"
    create_trip("ael-l1-xhs", trips, title="ael-l1-xhs")
    trip_dir = trips / "ael-l1-xhs"
    _seed_kept_photos(trip_dir, 6)
    seen: list[object] = []

    def _wrap(photos, template, **kwargs):
        seen.append(kwargs.get("slot_hints"))
        from travelogue.export.card_renderer import render_card as real

        return real(photos, template, **kwargs)

    monkeypatch.setattr("travelogue.export.collage_pack.render_card", _wrap)
    export_collage_pack(trip_dir, platform="xiaohongshu", cfg=_cfg(crop=True))
    assert seen
    assert all(h is None for h in seen)


def test_ac09_ssc_does_not_import_judge_or_llm() -> None:
    path = _REPO / "travelogue" / "export" / "album_ssc.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
        elif isinstance(node, ast.Import):
            imported.extend(a.name for a in node.names)
    joined = " ".join(imported)
    assert "mosaic_judge" not in joined
    assert "travelogue.llm" not in joined
    assert "travelogue.ai" not in joined
    assert "layout_engine.mosaic" not in joined


def test_ac23_export_does_not_import_mosaic() -> None:
    root = _REPO / "travelogue" / "export"
    offenders: list[str] = []
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            mod = ""
            if isinstance(node, ast.ImportFrom) and node.module:
                mod = node.module
            elif isinstance(node, ast.Import):
                mod = ",".join(a.name for a in node.names)
            if "layout_engine.mosaic" in mod:
                offenders.append(f"{path.name}: {mod}")
    assert not offenders
