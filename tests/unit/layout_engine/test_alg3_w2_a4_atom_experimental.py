"""ALG-V3 W2-A4 · Atom experimental_relax (opt-in; AC-12 / X04 / BLK-08)."""

from __future__ import annotations

from travelogue.config.mosaic import MosaicConfig
from travelogue.config.shot_grouping import (
    AtomConfig,
    ShotGroupMosaicPolicy,
    shot_grouping_from_dict,
)
from travelogue.layout_engine.mosaic.candidates import (
    generate_window_candidates_with_rejections,
)
from travelogue.layout_engine.planner.scene_atoms import (
    adjacent_compatible,
    atom_gate_limits,
    resolve_atom_gate_policy,
    split_into_atoms,
    window_violates_atom,
)
from travelogue.orchestrator.happy_path_recipe import RESEARCH_DEFAULT_FALSE


def _photo(
    aid: str,
    taken: str,
    *,
    sg: str = "sg-a",
    sc: int = 1,
    kind: str = "landscape",
) -> dict:
    w, h = (1600, 900) if kind == "landscape" else (900, 1600)
    return {
        "id": aid,
        "type": "photo",
        "shotGroupId": sg,
        "sceneClusterId": sc,
        "takenAt": taken,
        "aspectKind": kind,
        "width": w,
        "height": h,
        "sharpness": 0.6,
    }


def _gap_corpus() -> tuple[list[str], dict[str, dict], dict[str, str]]:
    """Same SG/SC; adjacent gaps 700s → hard-reject at default 600s, pass at ×2."""
    assets = {
        "a0": _photo("a0", "2025-01-01T10:00:00Z"),
        "a1": _photo("a1", "2025-01-01T10:11:40Z"),  # +700s
        "a2": _photo("a2", "2025-01-01T10:23:20Z"),  # +700s
        "a3": _photo("a3", "2025-01-01T10:35:00Z"),  # +700s
    }
    ids = ["a0", "a1", "a2", "a3"]
    aspects = {k: v["aspectKind"] for k, v in assets.items()}
    return ids, assets, aspects  # type: ignore[return-value]


def test_a4_experimental_defaults_off() -> None:
    cfg = AtomConfig()
    assert cfg.experimental_relax is False
    assert cfg.experimental_relax_gap_scale == 2.0
    assert cfg.experimental_relax_span_scale == 1.5
    assert cfg.mosaic_share_floor_observe == 0.70
    assert atom_gate_limits(cfg) == (600.0, 7200.0)


def test_a4_loader_camel_and_scale_floor() -> None:
    ssg = shot_grouping_from_dict(
        {
            "mosaic": {
                "atom": {
                    "experimentalRelax": True,
                    "experimentalRelaxGapScale": 0.5,  # clamped to ≥1
                    "experimentalRelaxSpanScale": 3.0,
                    "mosaicShareFloorObserve": 0.65,
                }
            }
        }
    )
    atom = ssg.mosaic.atom
    assert atom.experimental_relax is True
    assert atom.experimental_relax_gap_scale == 1.0
    assert atom.experimental_relax_span_scale == 3.0
    assert atom.mosaic_share_floor_observe == 0.65


def test_a4_flag_off_behavior_unchanged_on_gap_corpus() -> None:
    ids, assets, _ = _gap_corpus()
    off = AtomConfig(enabled=True, experimental_relax=False)
    baseline = AtomConfig(enabled=True)  # defaults
    assert window_violates_atom(ids, assets, off) == "atom_gap"
    assert window_violates_atom(ids, assets, baseline) == "atom_gap"
    ok, reason = adjacent_compatible(assets["a0"], assets["a1"], off)
    assert not ok and reason == "atom_gap"


def test_a4_flag_on_widens_gap_only() -> None:
    ids, assets, _ = _gap_corpus()
    on = AtomConfig(enabled=True, experimental_relax=True)
    assert window_violates_atom(ids, assets, on) is None
    gap, span = atom_gate_limits(on)
    assert gap == 1200.0
    assert span == 7200.0 * 1.5


def test_a4_observe_floor_never_auto_widens() -> None:
    """BLK-08 / X04 companion: floor is observe-only; does not flip relax."""
    tight = AtomConfig(
        enabled=True,
        experimental_relax=False,
        mosaic_share_floor_observe=0.99,
    )
    loose_floor = AtomConfig(
        enabled=True,
        experimental_relax=False,
        mosaic_share_floor_observe=0.01,
    )
    assert atom_gate_limits(tight) == atom_gate_limits(loose_floor)
    resolved = resolve_atom_gate_policy(tight)
    assert resolved is tight  # no copy when relax off
    # Mutating floor alone never enables experimental_relax
    assert tight.experimental_relax is False
    assert loose_floor.experimental_relax is False


def test_a4_research_firewall_lists_new_flag() -> None:
    assert "shot_grouping.mosaic.atom.experimental_relax" in RESEARCH_DEFAULT_FALSE


def _atom_boundary_count(
    ids: list[str],
    assets: dict[str, dict],
    aspects: dict[str, str],
    atom: AtomConfig,
) -> int:
    policy = ShotGroupMosaicPolicy(
        cross_group_hard_reject=False,
        same_group_anti_slice=False,
        atom=atom,
    )
    result = generate_window_candidates_with_rejections(
        ids,
        aspects,  # type: ignore[arg-type]
        assets,
        cfg=MosaicConfig(enabled=True, enabled_window_sizes=(4,)),
        ssg_policy=policy,
    )
    return sum(1 for r in result.rejected if r.get("reason") == "atom_boundary")


def test_ac12_atom_boundary_funnel_drop_when_relax_on() -> None:
    """AC-12 funnel leg: atom_boundary share ↓ ≥25% (absolute count on fixture)."""
    ids, assets, aspects = _gap_corpus()
    off_n = _atom_boundary_count(
        ids, assets, aspects, AtomConfig(enabled=True, experimental_relax=False)
    )
    on_n = _atom_boundary_count(
        ids, assets, aspects, AtomConfig(enabled=True, experimental_relax=True)
    )
    assert off_n > 0, "fixture must produce atom_boundary rejects when flag off"
    drop = (off_n - on_n) / off_n
    assert drop >= 0.25, f"atom_boundary drop {drop:.2%} < 25% (off={off_n} on={on_n})"


def test_ac12_multi_slot_share_meets_observe_floor() -> None:
    """AC-12 / X04: not funnel-only — multi-slot share ≥ mosaic_share_floor_observe."""
    # 8 photos, gaps 700s → default splits to many singletons; relax keeps longer atoms.
    assets: dict[str, dict] = {}
    ids: list[str] = []
    for i in range(8):
        aid = f"p{i}"
        # ISO via 700s steps (avoid invalid HH:MM when minute≥60)
        h = 10 + (i * 700) // 3600
        rem = (i * 700) % 3600
        m, s = rem // 60, rem % 60
        taken = f"2025-01-01T{h:02d}:{m:02d}:{s:02d}Z"
        assets[aid] = _photo(aid, taken)
        ids.append(aid)

    off = AtomConfig(enabled=True, experimental_relax=False)
    on = AtomConfig(
        enabled=True,
        experimental_relax=True,
        mosaic_share_floor_observe=0.70,
    )
    atoms_off = split_into_atoms(ids, assets, off)
    atoms_on = split_into_atoms(ids, assets, on)

    def _multi_slot_share(atoms: list[list[str]]) -> float:
        assert atoms
        return sum(1 for a in atoms if len(a) >= 2) / len(atoms)

    share_on = _multi_slot_share(atoms_on)
    share_off = _multi_slot_share(atoms_off)
    # Relax should not shrink multi-slot share vs default on this gap corpus.
    assert share_on >= share_off
    assert share_on >= float(on.mosaic_share_floor_observe), (
        f"multi-slot share {share_on:.2f} < floor {on.mosaic_share_floor_observe}"
    )
