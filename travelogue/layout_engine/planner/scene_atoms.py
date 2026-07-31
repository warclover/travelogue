"""Scene Atom · Cluster-Boundary-First V1 (planner memory only).

See docs/PLAN-CLUSTER-BOUNDARY-FIRST-MOSAIC-V1.md §3 P1 (已审定稿).
"""

from __future__ import annotations

from typing import Any

from travelogue.config.shot_grouping import AtomConfig
from travelogue.layout_contract.burst import parse_taken_ts

_INVALID_SCENE_CLUSTER = frozenset({None, "", -1, "-1"})


def _scene_cluster_value(asset: dict[str, Any]) -> Any:
    if "sceneClusterId" not in asset:
        return None
    return asset.get("sceneClusterId")


def scene_cluster_is_valid(value: Any) -> bool:
    return value not in _INVALID_SCENE_CLUSTER


def _semantic_category(asset: dict[str, Any]) -> str | None:
    tag = asset.get("semanticTag")
    if isinstance(tag, dict):
        cat = tag.get("category")
        return str(cat) if cat else None
    return None


def adjacent_compatible(
    prev: dict[str, Any],
    cur: dict[str, Any],
    policy: AtomConfig,
) -> tuple[bool, str | None]:
    """Whether ``cur`` may continue the atom ending at ``prev``."""
    sg_a = prev.get("shotGroupId")
    sg_b = cur.get("shotGroupId")
    if not sg_a or not sg_b or str(sg_a) != str(sg_b):
        return False, "shot_group_mismatch"

    ta = parse_taken_ts(prev)
    tb = parse_taken_ts(cur)
    if ta is not None and tb is not None:
        gap = abs(tb - ta)
        if gap > float(policy.max_gap_seconds):
            return False, "atom_gap"

    mode = (policy.scene_cluster_mode or "compatible").lower()
    if mode != "off":
        sc_a = _scene_cluster_value(prev)
        sc_b = _scene_cluster_value(cur)
        va, vb = scene_cluster_is_valid(sc_a), scene_cluster_is_valid(sc_b)
        if mode == "force_same":
            # Treat invalid as its own singleton key — never merge with others.
            if sc_a != sc_b:
                return False, "scene_cluster_mismatch"
        else:  # compatible
            if va and vb and sc_a != sc_b:
                return False, "scene_cluster_mismatch"
            if va != vb:
                # valid id must not mix with -1 / missing
                return False, "scene_cluster_valid_invalid_mix"

    if policy.category_jump_is_hard:
        ca, cb = _semantic_category(prev), _semantic_category(cur)
        if ca and cb and ca != cb:
            return False, "category_jump"

    return True, None


def window_span_seconds(asset_ids: list[str], assets_by_id: dict[str, dict]) -> float | None:
    stamps = [
        t
        for aid in asset_ids
        if (t := parse_taken_ts(assets_by_id.get(aid) or {})) is not None
    ]
    if len(stamps) < 2:
        return None
    return float(max(stamps) - min(stamps))


def window_violates_atom(
    asset_ids: list[str],
    assets_by_id: dict[str, dict],
    policy: AtomConfig,
) -> str | None:
    """Return reject reason when a multi-slot window crosses atom boundaries.

    ``None`` means OK (or policy disabled / too few ids).
    """
    if not policy.enabled:
        return None
    if len(asset_ids) < 2:
        return None

    span = window_span_seconds(asset_ids, assets_by_id)
    if span is not None and span > float(policy.max_window_span_seconds):
        return "atom_window_span"

    # Order by takenAt for adjacency checks (screen slot order may be reordered).
    def _sort_key(aid: str) -> tuple[float, str]:
        t = parse_taken_ts(assets_by_id.get(aid) or {})
        return (t if t is not None else 0.0, aid)

    ordered = sorted(asset_ids, key=_sort_key)
    for i in range(1, len(ordered)):
        prev = assets_by_id.get(ordered[i - 1]) or {}
        cur = assets_by_id.get(ordered[i]) or {}
        ok, reason = adjacent_compatible(prev, cur, policy)
        if not ok:
            return reason or "atom_boundary"
    return None


def max_prefix_in_atom(
    asset_ids: list[str],
    assets_by_id: dict[str, dict],
    policy: AtomConfig,
    *,
    max_n: int | None = None,
) -> int:
    """Longest prefix of ``asset_ids`` (display/cursor order) that stays in one atom."""
    if not asset_ids:
        return 0
    if not policy.enabled:
        return len(asset_ids) if max_n is None else min(len(asset_ids), max_n)
    limit = len(asset_ids) if max_n is None else min(len(asset_ids), max_n)
    if limit <= 0:
        return 0
    n = 1
    while n < limit:
        window = asset_ids[: n + 1]
        if window_violates_atom(window, assets_by_id, policy):
            break
        n += 1
    return n


def split_into_atoms(
    asset_ids: list[str],
    assets_by_id: dict[str, dict],
    policy: AtomConfig,
) -> list[list[str]]:
    """Split a takenAt-sorted id list into atoms (planner memory)."""
    if not asset_ids:
        return []
    if not policy.enabled:
        return [list(asset_ids)]
    atoms: list[list[str]] = []
    cur: list[str] = [asset_ids[0]]
    for aid in asset_ids[1:]:
        prev = assets_by_id.get(cur[-1]) or {}
        nxt = assets_by_id.get(aid) or {}
        ok, _ = adjacent_compatible(prev, nxt, policy)
        # Also enforce window span within growing atom
        if ok:
            trial = cur + [aid]
            if window_violates_atom(trial, assets_by_id, policy):
                ok = False
        if ok:
            cur.append(aid)
        else:
            atoms.append(cur)
            cur = [aid]
    atoms.append(cur)
    return atoms
