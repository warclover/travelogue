"""Scene Atom · Cluster-Boundary-First V1 (planner memory only).

See docs/PLAN-CLUSTER-BOUNDARY-FIRST-MOSAIC-V1.md §3 P1 (已审定稿).
"""

from __future__ import annotations

from typing import Any

from dataclasses import replace

from travelogue.config.shot_grouping import AtomConfig
from travelogue.layout_contract.burst import parse_taken_ts

_INVALID_SCENE_CLUSTER = frozenset({None, "", -1, "-1"})


def atom_gate_limits(policy: AtomConfig) -> tuple[float, float]:
    """Effective ``(max_gap_seconds, max_window_span_seconds)`` for hard gates.

    ALG-V3 W2-A4: scales only when ``experimental_relax`` is True.
    ``mosaic_share_floor_observe`` is intentionally unused (BLK-08 / never auto-widen).
    """
    gap = float(policy.max_gap_seconds)
    span = float(policy.max_window_span_seconds)
    if policy.experimental_relax:
        gap *= max(1.0, float(policy.experimental_relax_gap_scale))
        span *= max(1.0, float(policy.experimental_relax_span_scale))
    return gap, span


def resolve_atom_gate_policy(policy: AtomConfig) -> AtomConfig:
    """Return policy with experimental gap/span scales applied (idempotent copy).

    Does not read ``mosaic_share_floor_observe``. Clears ``experimental_relax`` on
    the copy so nested calls cannot double-scale.
    """
    if not policy.experimental_relax:
        return policy
    gap, span = atom_gate_limits(policy)
    return replace(
        policy,
        max_gap_seconds=gap,
        max_window_span_seconds=span,
        experimental_relax=False,
    )


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
    """Whether ``cur`` may continue the atom ending at ``prev``.

    Shot-group rule:
    - both present → must match
    - one present / one absent → mismatch (do not mix labeled with unlabeled)
    - both absent → ``missing_shot_group_mode``:
        ``time_bridge`` (default) continues with gap + half-hard sc;
        ``reject`` keeps fail-closed singleton atoms
    """
    policy = resolve_atom_gate_policy(policy)
    sg_a = prev.get("shotGroupId")
    sg_b = cur.get("shotGroupId")
    has_a = bool(sg_a)
    has_b = bool(sg_b)
    if has_a and has_b:
        if str(sg_a) != str(sg_b):
            return False, "shot_group_mismatch"
    elif has_a != has_b:
        return False, "shot_group_present_absent_mix"
    else:
        # Both missing shotGroupId.
        mode_sg = (policy.missing_shot_group_mode or "time_bridge").lower()
        if mode_sg == "reject":
            return False, "shot_group_missing"

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
    policy = resolve_atom_gate_policy(policy)
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


def sort_ids_by_taken_at(
    asset_ids: list[str],
    assets_by_id: dict[str, dict],
) -> list[str]:
    """Stable chronological order for page packs (display order may shuffle)."""

    def _key(aid: str) -> tuple[float, str]:
        t = parse_taken_ts(assets_by_id.get(aid) or {})
        return (t if t is not None else 0.0, aid)

    return sorted(asset_ids, key=_key)


def window_category_jump_count(
    asset_ids: list[str],
    assets_by_id: dict[str, dict],
) -> int:
    """Count semantic category changes along takenAt order (W1 soft signal)."""
    if len(asset_ids) < 2:
        return 0

    def _sort_key(aid: str) -> tuple[float, str]:
        t = parse_taken_ts(assets_by_id.get(aid) or {})
        return (t if t is not None else 0.0, aid)

    ordered = sorted(asset_ids, key=_sort_key)
    jumps = 0
    prev_cat: str | None = None
    for aid in ordered:
        cat = _semantic_category(assets_by_id.get(aid) or {})
        if prev_cat and cat and cat != prev_cat:
            jumps += 1
        if cat:
            prev_cat = cat
    return jumps


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


def _remainder_packable(remaining: int, capacities: tuple[int, ...]) -> bool:
    """Exact cover of ``remaining`` using only ``capacities`` (order irrelevant)."""
    if remaining == 0:
        return True
    if remaining < 0 or not capacities:
        return False
    caps = tuple(sorted({int(c) for c in capacities if int(c) > 0}, reverse=True))
    if not caps:
        return False
    reachable = {0}
    for _ in range(remaining):
        nxt: set[int] = set()
        for r in reachable:
            for c in caps:
                s = r + c
                if s == remaining:
                    return True
                if s < remaining:
                    nxt.add(s)
        if not nxt:
            break
        reachable = nxt
    return remaining in reachable


def pack_atom_page_sizes(
    n: int,
    capacities: tuple[int, ...] = (3, 2, 1),
) -> list[int]:
    """W2 · cut one atom of length ``n`` into page packs (same atom, time order).

    Prefer larger capacities; when ``(3,2,*)`` is available, avoid the classic
    ``n % 3 == 1`` orphan (e.g. 4→2+2, 7→2+2+3) instead of 3+1.
    """
    rem = max(0, int(n))
    if rem <= 0:
        return []
    caps = tuple(sorted({int(c) for c in capacities if int(c) > 0}, reverse=True))
    if not caps:
        return [1] * rem

    groups: list[int] = []
    # Anti-orphan for portrait-like (3,2) packing.
    if 3 in caps and 2 in caps and rem >= 4 and rem % 3 == 1:
        groups.append(2)
        rem -= 2

    while rem > 0:
        placed = False
        for c in caps:
            if c > rem:
                continue
            leave = rem - c
            # Prefer a cut that still covers the remainder exactly when possible.
            if leave == 0 or _remainder_packable(leave, caps):
                groups.append(c)
                rem = leave
                placed = True
                break
        if placed:
            continue
        # Fallback: largest fitting capacity (may leave a soft single).
        for c in caps:
            if c <= rem:
                groups.append(c)
                rem -= c
                placed = True
                break
        if not placed:
            groups.append(rem)
            break
    return groups


def prefer_window_sizes_for_atom(sizes: list[int], atom_len: int) -> list[int]:
    """Reorder MCS window sizes so the first page leaves a packable atom tail.

    Exact atom fill ranks first; orphan leave=1 ranks last. Stable among ties
    by preserving relative order of equal scores via original index.
    """
    if atom_len <= 0 or not sizes:
        return list(sizes)
    pack = tuple(sorted({int(s) for s in sizes if int(s) > 0}, reverse=True))

    def _key(item: tuple[int, int]) -> tuple[int, int, int]:
        idx, s = item
        leave = atom_len - s
        if leave < 0:
            return (9, 0, idx)
        if leave == 0:
            return (0, -s, idx)
        if leave in pack or _remainder_packable(leave, pack):
            return (1, -s, idx)
        if leave >= 2:
            return (2, -s, idx)
        return (3, -s, idx)  # leave == 1

    ordered = sorted(enumerate(sizes), key=_key)
    return [s for _, s in ordered]
