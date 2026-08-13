"""AEL L2 roles + punch-in — AC-AEL-10/11/12/22/27/28."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from travelogue.config.album_editorial import EffectiveAel, album_editorial_lab_from_dict
from travelogue.export.album_ssc import apply_card_ssc
from travelogue.export.card_grouper import CardPlan, plan_cards
from travelogue.export.card_templates import CARD_TEMPLATES
from travelogue.layout_contract.editorial_role import (
    EDITORIAL_ROLES,
    editorial_role_for_asset,
    translate_p33_label,
)
from travelogue.layout_engine.crop_solver import solve_slot_tighten

pytestmark = pytest.mark.unit


def test_editorial_role_rules_ac10() -> None:
    portrait = {
        "nativeWidth": 800,
        "nativeHeight": 1200,
        "faces": [{"x": 0.3, "y": 0.2, "w": 0.3, "h": 0.25}],
    }
    role, group = editorial_role_for_asset(portrait)
    assert role == "portrait"
    assert group is False

    vista = {"nativeWidth": 1600, "nativeHeight": 900}
    role, group = editorial_role_for_asset(vista)
    assert role == "vista"
    assert group is False

    crowd = {
        "nativeWidth": 1600,
        "nativeHeight": 1066,
        "quality": {"faceCount": 4},
        "faces": [{"x": 0.1 * i, "y": 0.2, "w": 0.08, "h": 0.1} for i in range(4)],
    }
    role, group = editorial_role_for_asset(crowd)
    assert role == "portrait"
    assert group is True

    empty = {"nativeWidth": 1600, "nativeHeight": 900, "faces": [], "quality": {}}
    _role, group = editorial_role_for_asset(empty)
    assert group is False


def test_food_not_vista_ac12() -> None:
    food = {"nativeWidth": 1600, "nativeHeight": 900, "subjectClass": "food"}
    role, group = editorial_role_for_asset(food)
    assert role == "detail"
    assert group is False


def test_detail_main_ok_when_no_hero_ac11() -> None:
    """No vista/portrait in the card pool → detail on main is not penalized."""
    from travelogue.export.card_grouper import _role_soft_penalty

    template = CARD_TEMPLATES["card-1-full-frame"]
    path = Path("detail.jpg")
    lookup = lambda p: {  # noqa: E731
        "nativeWidth": 900,
        "nativeHeight": 900,
        "subjectClass": "architecture",
    }
    pen = _role_soft_penalty(template, [path], lookup)
    assert pen == 0.0


def test_p33_labels_translate_ac22_ac27() -> None:
    assert set(EDITORIAL_ROLES) <= {
        "vista",
        "portrait",
        "detail",
        "sequence",
        "unused",
    }
    photo, slot = translate_p33_label("主图")
    assert photo == "vista"
    assert slot == "main"
    photo, slot = translate_p33_label("竖图")
    assert photo == "portrait"
    assert slot == "portrait"
    photo, slot = translate_p33_label("横图")
    assert photo == "vista"
    assert slot == "landscape"
    photo, slot = translate_p33_label("细节")
    assert photo == "detail"
    assert slot != "main"
    photo, slot = translate_p33_label("小图")
    assert photo == "detail"
    assert slot != "main"
    with pytest.raises(KeyError):
        translate_p33_label("small")
    with pytest.raises(KeyError):
        translate_p33_label("main-photo")


def test_tighten_skips_groups_ac28() -> None:
    asset = {
        "nativeWidth": 2000,
        "nativeHeight": 1500,
        "quality": {"faceCount": 4},
        "faces": [{"x": 0.1 * i, "y": 0.2, "w": 0.08, "h": 0.1} for i in range(4)],
    }
    assert solve_slot_tighten(asset, 0.75) is None


def test_tighten_prefers_keep_feet_over_bust_ac28() -> None:
    asset = {
        "nativeWidth": 2000,
        "nativeHeight": 1500,
        "faces": [{"x": 0.46, "y": 0.18, "w": 0.08, "h": 0.10}],
        "protectBox": {"x": 0.40, "y": 0.16, "w": 0.20, "h": 0.70},
    }
    got = solve_slot_tighten(asset, 0.75)
    assert got is not None
    assert got.mode == "keep_feet"
    cover_w = 0.75 / (2000 / 1500)
    assert got.window.w * got.window.h < cover_w - 1e-6


def test_one_slot_share_within_ga_plus_10pp(tmp_path: Path) -> None:
    photos: list[Path] = []
    for i in range(24):
        size = (1600, 900) if i % 3 == 0 else (900, 1200)
        p = tmp_path / f"p{i:02d}.jpg"
        Image.new("RGB", size, (40 + i, 80, 120)).save(p, format="JPEG")
        photos.append(p)
    off = plan_cards(photos, avoid_immediate_repeat=True)
    assets = {
        p: {
            "nativeWidth": 900 if i % 3 else 1600,
            "nativeHeight": 1200 if i % 3 else 900,
            "faces": [{"x": 0.3, "y": 0.2, "w": 0.3, "h": 0.3}] if i % 3 else [],
        }
        for i, p in enumerate(photos)
    }
    on = plan_cards(
        photos,
        avoid_immediate_repeat=True,
        assets_by_path=assets,
        role_soft=True,
        cluster_soft=True,
    )
    def _share(plans: list[CardPlan]) -> float:
        if not plans:
            return 0.0
        return sum(1 for c in plans if c.template.slot_count == 1) / len(plans)

    assert _share(on) <= _share(off) + 0.10 + 1e-9


def test_ssc_same_count_swap_keeps_slot_count(tmp_path: Path) -> None:
    t = CARD_TEMPLATES["card-2-stack-equal"]
    paths = []
    assets: dict = {}
    for i, size in enumerate(((800, 1200), (800, 1200))):
        p = tmp_path / f"s{i}.jpg"
        Image.new("RGB", size, (20, 40, 80)).save(p, format="JPEG")
        paths.append(p)
        assets[p] = {
            "nativeWidth": size[0],
            "nativeHeight": size[1],
            "faces": [{"x": 0.3, "y": 0.35, "w": 0.4, "h": 0.4}],
        }
    ael = EffectiveAel(
        enabled=True,
        crop=True,
        roles=True,
        contain_on_fail=True,
        face_hard_gate=True,
        group_face_min=3,
        max_solve_ms=8000,
    )
    result = apply_card_ssc(
        CardPlan(template=t, photos=tuple(paths)),
        assets.get,
        ael,
    )
    assert result.template.slot_count == 2
    assert len(result.photos) == 2


def test_tighten_config_round_trip() -> None:
    lab = album_editorial_lab_from_dict(
        {"enabled": True, "crop": {"enabled": True, "tighten": True}}
    )
    assert lab.crop.tighten is True
    from travelogue.config.app import AppConfig
    from travelogue.config.album_editorial import effective_ael

    ael = effective_ael(
        AppConfig(album_editorial_lab=lab),
        "album_spread",
    )
    assert ael.tighten is True
    ael_xhs = effective_ael(AppConfig(album_editorial_lab=lab), "xiaohongshu")
    assert ael_xhs.tighten is False
