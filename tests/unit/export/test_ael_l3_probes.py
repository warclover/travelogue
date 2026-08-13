"""AEL L3 probes — AC-AEL-13/14/15/16/26/27."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from travelogue.config.album_editorial import EffectiveAel, album_editorial_lab_from_dict
from travelogue.export.album_probes import mix_probe_cards
from travelogue.export.album_ssc import apply_card_ssc
from travelogue.export.card_grouper import CardPlan, assign_photos_to_slots
from travelogue.export.card_templates import (
    CARD_TEMPLATES,
    PROBE_MIX_IDS,
    PROBE_TEMPLATES,
    pick_template_for_count,
)

pytestmark = pytest.mark.unit

_REPO = Path(__file__).resolve().parents[3]


def _jpeg(path: Path, *, size: tuple[int, int], color=(40, 80, 160)) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, format="JPEG", quality=90)
    return path


def _portraits(tmp_path: Path, n: int) -> list[Path]:
    return [
        _jpeg(tmp_path / f"p{i:02d}.jpg", size=(800, 1200), color=(30 + i * 8, 70, 110))
        for i in range(n)
    ]


def _landscapes(tmp_path: Path, n: int) -> list[Path]:
    return [
        _jpeg(tmp_path / f"l{i:02d}.jpg", size=(1600, 900), color=(20 + i * 8, 90, 140))
        for i in range(n)
    ]


def _mature_plan(photos: list[Path], *, card_index: int = 0) -> CardPlan:
    template = pick_template_for_count(len(photos), card_index=card_index)
    return CardPlan(
        template=template,
        photos=tuple(assign_photos_to_slots(photos, template)),
    )


def _ael(**kwargs: object) -> EffectiveAel:
    base: dict[str, object] = {
        "enabled": True,
        "crop": True,
        "roles": True,
        "probes": True,
        "contain_on_fail": True,
        "face_hard_gate": True,
        "group_face_min": 3,
        "max_solve_ms": 8000,
        "max_per_spread": 1,
        "max_share": 0.20,
        "allowlist": PROBE_MIX_IDS,
        "tighten": True,
        "cluster_soft": True,
    }
    base.update(kwargs)
    return EffectiveAel(**base)  # type: ignore[arg-type]


def test_probes_not_in_mature_library_ac13() -> None:
    assert CARD_TEMPLATES.keys().isdisjoint(PROBE_TEMPLATES)
    for tid in PROBE_TEMPLATES:
        assert tid.startswith("probe-")


def test_empty_allowlist_selects_nothing_ac13_ac26(tmp_path: Path) -> None:
    photos = _portraits(tmp_path, 8)
    plans = [_mature_plan(photos[i : i + 4], card_index=i) for i in range(0, 8, 4)]
    ael = _ael(allowlist=(), max_share=1.0)
    assert mix_probe_cards(plans, None, ael) == plans


def test_probes_off_keeps_l2_plans_ac16(tmp_path: Path) -> None:
    photos = _portraits(tmp_path, 8)
    plans = [_mature_plan(photos[i : i + 4], card_index=i) for i in range(0, 8, 4)]
    ael = _ael(probes=False, max_share=1.0)
    assert mix_probe_cards(plans, None, ael) == plans


def test_split_six_slot_into_square(tmp_path: Path) -> None:
    photos = _portraits(tmp_path, 6)
    plans = [_mature_plan(photos)]
    assert plans[0].template.slot_count == 6
    out = mix_probe_cards(plans, None, _ael(max_share=1.0))
    assert any(p.template.id == "probe-square" for p in out)
    assert sum(len(p.photos) for p in out) == 6
    assert all(p.template.slot_count == len(p.photos) for p in out)


def test_split_sixteen_tall_remainder_is_plannable(tmp_path: Path) -> None:
    """16-2 leftover is 14, which is not a mature slot count — must not crash."""
    photos = _portraits(tmp_path, 16)
    plans = [_mature_plan(photos)]
    assert plans[0].template.slot_count == 16
    out = mix_probe_cards(
        plans, None, _ael(max_share=1.0, allowlist=("probe-tall",))
    )
    assert any(p.template.id == "probe-tall" for p in out)
    assert sum(len(p.photos) for p in out) == 16
    assert all(p.template.slot_count == len(p.photos) for p in out)


def test_mix_same_count_square_ac13(tmp_path: Path) -> None:
    photos = _portraits(tmp_path, 8)
    plans = [_mature_plan(photos[i : i + 4], card_index=i) for i in range(0, 8, 4)]
    out = mix_probe_cards(plans, None, _ael(max_share=1.0))
    probe_ids = [p.template.id for p in out if p.template.id in PROBE_TEMPLATES]
    assert "probe-square" in probe_ids
    assert all(p.template.slot_count == len(p.photos) for p in out)
    assert all(p.photos for p in out)


def test_quota_one_per_spread_and_share_ac14(tmp_path: Path) -> None:
    photos = _portraits(tmp_path, 20)
    plans = [_mature_plan(photos[i : i + 4], card_index=i) for i in range(0, 20, 4)]
    assert len(plans) == 5
    out = mix_probe_cards(plans, None, _ael(max_share=0.20, max_per_spread=1))
    probe_ids = [p.template.id for p in out if p.template.id in PROBE_TEMPLATES]
    assert len(probe_ids) <= max(1, int(5 * 0.20))
    for i in range(0, len(out), 2):
        left = out[i]
        right = out[i + 1] if i + 1 < len(out) else None
        n_probe = int(left.template.id in PROBE_TEMPLATES)
        if right is not None:
            n_probe += int(right.template.id in PROBE_TEMPLATES)
        assert n_probe <= 1


def test_example_allowlist_excludes_triptych_ac26() -> None:
    text = (_REPO / "docs" / "config-ael-dogfood.example.yaml").read_text(encoding="utf-8")
    active = [
        line.strip()
        for line in text.splitlines()
        if line.strip().startswith("- probe-") and not line.lstrip().startswith("#")
    ]
    assert "probe-triptych" not in " ".join(active)
    assert "probe-triptych" in text


def test_triptych_only_when_allowlisted(tmp_path: Path) -> None:
    photos = _portraits(tmp_path, 6)
    plans = [_mature_plan(photos[i : i + 3], card_index=i) for i in range(0, 6, 3)]
    mix_only = mix_probe_cards(plans, None, _ael(max_share=1.0, allowlist=PROBE_MIX_IDS))
    assert all(p.template.id != "probe-triptych" for p in mix_only)
    with_eval = mix_probe_cards(
        plans,
        None,
        _ael(max_share=1.0, allowlist=("probe-triptych",)),
    )
    assert any(p.template.id == "probe-triptych" for p in with_eval)


def test_ssc_fail_reverts_when_contain_off_ac15(tmp_path: Path) -> None:
    photos = _landscapes(tmp_path, 4)
    plans = [_mature_plan(photos[i : i + 2], card_index=i) for i in range(0, 4, 2)]
    lookup = {
        p: {
            "nativeWidth": 1600,
            "nativeHeight": 900,
            "width": 1600,
            "height": 900,
            "faces": [{"x": 0.05, "y": 0.15, "w": 0.7, "h": 0.55}],
            "quality": {"faceCount": 1},
        }
        for p in photos
    }.get
    ael = _ael(
        max_share=1.0,
        contain_on_fail=False,
        allowlist=("probe-tall",),
        roles=False,
        tighten=False,
    )
    out = mix_probe_cards(plans, lookup, ael)
    assert all(p.template.id not in PROBE_TEMPLATES for p in out)


def test_lock_template_keeps_probe(tmp_path: Path) -> None:
    photos = _portraits(tmp_path, 4)
    plan = CardPlan(
        template=PROBE_TEMPLATES["probe-square"],
        photos=tuple(assign_photos_to_slots(photos, PROBE_TEMPLATES["probe-square"])),
    )
    ael = _ael(probes=True, roles=True, crop=True)
    ssc = apply_card_ssc(plan, None, ael, lock_template=True)
    assert ssc.template.id == "probe-square"


def test_no_p33_geometry_ac27() -> None:
    assert all("p33" not in tid for tid in PROBE_TEMPLATES)
    assert "small" not in PROBE_TEMPLATES
    assert "main-photo" not in PROBE_TEMPLATES


def test_config_example_allowlist_default_empty() -> None:
    lab = album_editorial_lab_from_dict(
        {"enabled": True, "probes": {"enabled": True, "allowlist": []}}
    )
    assert lab.probes.allowlist == ()
