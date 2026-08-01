"""Cluster-Boundary-First · Scene Atom + SSG policy wiring tests."""

from __future__ import annotations

from travelogue.config.mosaic import MosaicConfig
from travelogue.config.shot_grouping import (
    AtomConfig,
    ShotGroupingConfig,
    ShotGroupMosaicPolicy,
    resolve_shot_group_mosaic_policy,
    shot_grouping_from_dict,
)
from travelogue.layout_engine.mosaic.candidates import (
    generate_window_candidates_with_rejections,
)
from travelogue.layout_engine.mosaic.shot_group_gate import (
    hard_reject_cross_shot_group,
    ssg_cross_group_hard_reject_active,
    ssg_hard_reject_active,
)
from travelogue.layout_engine.planner.scene_atoms import (
    adjacent_compatible,
    pack_atom_page_sizes,
    prefer_window_sizes_for_atom,
    window_violates_atom,
)


def test_ssg_active_false_on_mosaic_config_alone() -> None:
    """P0 regression lock: MosaicConfig has no shot_grouping → silent False."""
    assert not ssg_hard_reject_active(MosaicConfig())
    assert not ssg_cross_group_hard_reject_active(MosaicConfig())


def test_ssg_active_true_on_policy_value_object() -> None:
    policy = ShotGroupMosaicPolicy(cross_group_hard_reject=True, same_group_anti_slice=True)
    assert ssg_hard_reject_active(policy)
    assert ssg_cross_group_hard_reject_active(policy)


def test_resolve_policy_from_app_like_object() -> None:
    app = type("App", (), {"shot_grouping": ShotGroupingConfig()})()
    policy = resolve_shot_group_mosaic_policy(app)
    assert policy.cross_group_hard_reject is True
    assert policy.atom.enabled is True


def test_atom_config_from_dict() -> None:
    cfg = shot_grouping_from_dict(
        {
            "enabled": "true",
            "mosaic": {
                "atom": {
                    "enabled": True,
                    "max_gap_seconds": 900,
                    "scene_cluster_mode": "compatible",
                }
            },
        }
    )
    assert cfg.mosaic.atom.enabled is True
    assert cfg.mosaic.atom.max_gap_seconds == 900.0
    assert cfg.mosaic.atom.scene_cluster_mode == "compatible"


def test_scene_cluster_compatible_contracts() -> None:
    policy = AtomConfig(enabled=True, scene_cluster_mode="compatible", max_gap_seconds=600)
    base = {
        "shotGroupId": "sg-1",
        "takenAt": "2015-04-27T10:00:00Z",
    }
    ok, _ = adjacent_compatible(
        {**base, "sceneClusterId": 0},
        {**base, "sceneClusterId": 0, "takenAt": "2015-04-27T10:01:00Z"},
        policy,
    )
    assert ok
    ok, reason = adjacent_compatible(
        {**base, "sceneClusterId": 0},
        {**base, "sceneClusterId": -1, "takenAt": "2015-04-27T10:01:00Z"},
        policy,
    )
    assert not ok
    assert reason == "scene_cluster_valid_invalid_mix"
    ok, _ = adjacent_compatible(
        {**base, "sceneClusterId": -1},
        {**base, "sceneClusterId": -1, "takenAt": "2015-04-27T10:01:00Z"},
        policy,
    )
    assert ok
    ok, reason = adjacent_compatible(
        {**base, "sceneClusterId": 1},
        {**base, "sceneClusterId": 2, "takenAt": "2015-04-27T10:01:00Z"},
        policy,
    )
    assert not ok
    assert reason == "scene_cluster_mismatch"


def test_window_span_hard_reject() -> None:
    policy = AtomConfig(enabled=True, max_window_span_seconds=7200)
    assets = {
        "a": {
            "shotGroupId": "sg-1",
            "sceneClusterId": -1,
            "takenAt": "2015-04-27T13:00:00Z",
        },
        "b": {
            "shotGroupId": "sg-1",
            "sceneClusterId": -1,
            "takenAt": "2015-04-27T16:00:00Z",
        },
        "c": {
            "shotGroupId": "sg-1",
            "sceneClusterId": -1,
            "takenAt": "2015-04-27T23:30:00Z",
        },
    }
    # label #4-like: >2h span
    assert window_violates_atom(["a", "b", "c"], assets, policy) == "atom_window_span"


def test_label1_bookends_cross_shot_group_rejected_via_policy() -> None:
    """Human label #1 · bookends mixes sg-0c and sg-0d."""
    assets = {
        "asset-079": {
            "shotGroupId": "sg-scene-0c",
            "sceneClusterId": -1,
            "takenAt": "2015-04-27T22:51:46Z",
            "aspectKind": "portrait",
            "width": 900,
            "height": 1600,
        },
        "asset-081": {
            "shotGroupId": "sg-scene-0c",
            "sceneClusterId": -1,
            "takenAt": "2015-04-27T22:53:52Z",
            "aspectKind": "landscape",
            "width": 1600,
            "height": 900,
        },
        "asset-082": {
            "shotGroupId": "sg-scene-0d",
            "sceneClusterId": 0,
            "takenAt": "2015-04-27T22:57:02Z",
            "aspectKind": "landscape",
            "width": 1600,
            "height": 900,
        },
        "asset-080": {
            "shotGroupId": "sg-scene-0c",
            "sceneClusterId": -1,
            "takenAt": "2015-04-27T22:52:19Z",
            "aspectKind": "portrait",
            "width": 900,
            "height": 1600,
        },
    }
    ids = ["asset-079", "asset-081", "asset-082", "asset-080"]
    aspects = {k: v["aspectKind"] for k, v in assets.items()}  # type: ignore[misc]
    # SSG slice hard reject on bookends (prefers_burst false)
    assert hard_reject_cross_shot_group(
        "screen-mosaic-4-2p2l-portrait-bookends", ids, assets
    )
    policy = ShotGroupMosaicPolicy(
        cross_group_hard_reject=True,
        same_group_anti_slice=True,
        atom=AtomConfig(enabled=True, scene_cluster_mode="compatible"),
    )
    # Atom also rejects (shot group mismatch)
    assert window_violates_atom(ids, assets, policy.atom) == "shot_group_mismatch"

    result = generate_window_candidates_with_rejections(
        ids,
        aspects,  # type: ignore[arg-type]
        assets,
        cfg=MosaicConfig(enabled=True, enabled_window_sizes=(4, 5, 6)),
        ssg_policy=policy,
    )
    reasons = {r.get("reason") for r in result.rejected}
    assert "shot_group_cross" in reasons or "atom_boundary" in reasons
    # No hard_valid winner that kept the polluted window for bookends-like patterns
    assert not any(
        c.hard_valid and c.pattern_id == "screen-mosaic-4-2p2l-portrait-bookends"
        for c in result.candidates
    )


def test_human_label_contracts_from_json() -> None:
    """Pollution windows from dogfood labels must violate atom when enabled."""
    import json
    from pathlib import Path

    path = Path(
        "docs/acceptance-records/mcs-human-cluster-labels-demo-49cbe46479-2026-07-31.json"
    )
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    # Minimal synthetic assets: use shotGroup from label signals when present
    # Full trip not required — construct from known label ids in review notes.
    policy = AtomConfig(enabled=True, max_gap_seconds=600, max_window_span_seconds=7200)
    # #4 catastrophe: different shot groups + huge span
    assets = {
        "asset-042": {
            "shotGroupId": "sg-a",
            "sceneClusterId": -1,
            "takenAt": "2015-04-27T13:18:43Z",
        },
        "asset-075": {
            "shotGroupId": "sg-b",
            "sceneClusterId": -1,
            "takenAt": "2015-04-27T16:10:22Z",
        },
        "asset-100": {
            "shotGroupId": "sg-c",
            "sceneClusterId": 0,
            "takenAt": "2015-04-27T23:31:20Z",
        },
    }
    assert window_violates_atom(
        ["asset-042", "asset-075", "asset-100"], assets, policy
    ) is not None
    # Ensure JSON still lists required go cases
    labels = {row["n"]: row for row in data["labels"] if isinstance(row.get("n"), int)}
    assert 1 in labels and 4 in labels
    assert labels[11]["verdict"] == "pollution_remove"  # known residual for W1


def test_pack_atom_page_sizes_avoids_orphan_one() -> None:
    """W2 · n%3==1 should prefer 2+… over leaving a trailing single."""
    assert pack_atom_page_sizes(4) == [2, 2]
    assert pack_atom_page_sizes(5) == [3, 2]
    assert pack_atom_page_sizes(6) == [3, 3]
    assert pack_atom_page_sizes(7) == [2, 3, 2]
    assert sum(pack_atom_page_sizes(7)) == 7
    assert 1 not in pack_atom_page_sizes(7)
    assert pack_atom_page_sizes(3) == [3]
    assert pack_atom_page_sizes(2) == [2]
    assert pack_atom_page_sizes(1) == [1]


def test_prefer_window_sizes_for_atom_exact_and_no_orphan() -> None:
    # Exact fill of atom ranks first.
    assert prefer_window_sizes_for_atom([5, 4, 6], 4)[0] == 4
    # Prefer leaving a packable tail (6→4) over orphan leave=1 (5→4 leave1).
    ordered = prefer_window_sizes_for_atom([5, 4, 6], 8)
    assert ordered[0] == 4  # leave 4 packable
    assert 5 in ordered  # still attempted later


def test_sort_ids_by_taken_at_repairs_display_shuffle() -> None:
    from travelogue.layout_engine.planner.scene_atoms import sort_ids_by_taken_at

    assets = {
        "a": {"takenAt": "2015-04-29T08:29:02Z"},
        "b": {"takenAt": "2015-04-29T08:26:46Z"},
        "c": {"takenAt": "2015-04-29T08:27:55Z"},
    }
    # Display order shuffled like #10 (156 before 154/155).
    assert sort_ids_by_taken_at(["a", "b", "c"], assets) == ["b", "c", "a"]


def test_beach_series_page_packs_after_chrono_sort() -> None:
    """#10-shaped: 9 in-atom portraits → 3+3+3 after takenAt sort."""
    assert pack_atom_page_sizes(9) == [3, 3, 3]
    assert pack_atom_page_sizes(8) == [3, 3, 2]