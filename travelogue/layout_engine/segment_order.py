"""LSE-CAP-06 segment bucket order optimizer (§4.5.6)."""

from __future__ import annotations

from travelogue.layout_contract.scoring import sort_bucket_asset_ids
from travelogue.layout_contract.subject import asset_has_person


def _subject_key(asset: dict) -> str:
    if asset_has_person(asset):
        return "person"
    bucket = str(asset.get("subjectBucket") or "").strip().lower()
    if bucket in ("portrait", "food", "temple", "landscape", "street"):
        return bucket
    tags = asset.get("tags") or []
    if tags:
        return str(tags[0]).lower()
    return "other"


def _cohesion_score(order: list[str], assets_map: dict[str, dict]) -> float:
    if len(order) < 2:
        return 0.0
    score = 0.0
    for left, right in zip(order, order[1:]):
        la = _subject_key(assets_map.get(left, {}))
        rb = _subject_key(assets_map.get(right, {}))
        if la == rb:
            score += 1.0
        elif la == "person" and rb == "person":
            score += 1.0
    return score


def _reorder_block(block: list[str], assets_map: dict[str, dict]) -> list[str]:
    if len(block) <= 2:
        return list(block)
    groups: dict[str, list[str]] = {}
    order_keys: list[str] = []
    for aid in block:
        key = _subject_key(assets_map.get(aid, {}))
        if key not in groups:
            groups[key] = []
            order_keys.append(key)
        groups[key].append(aid)
    if len(order_keys) <= 1:
        return list(block)
    primary = "person" if "person" in groups else order_keys[0]
    ordered: list[str] = []
    for key in [primary] + [k for k in order_keys if k != primary]:
        ordered.extend(groups.get(key) or [])
    return ordered


def _reorder_within_runs(ordered: list[str], assets_map: dict[str, dict]) -> list[str]:
    """Reorder inside burst blocks and equal-takenAt groups only (takenAt monotonic)."""
    out: list[str] = []
    i = 0
    while i < len(ordered):
        aid = ordered[i]
        asset = assets_map.get(aid, {})
        bg = asset.get("burstGroupId")
        ts = asset.get("takenAt")
        block = [aid]
        j = i + 1
        while j < len(ordered):
            nxt = assets_map.get(ordered[j], {})
            same_burst = bool(bg) and nxt.get("burstGroupId") == bg
            same_ts = (not bg) and ts and nxt.get("takenAt") == ts
            if same_burst or same_ts:
                block.append(ordered[j])
                j += 1
            else:
                break
        if len(block) > 1:
            out.extend(_reorder_block(block, assets_map))
        else:
            out.append(aid)
        i = j
    return out


def optimize_bucket_asset_ids(
    bucket: list[str],
    assets_map: dict[str, dict],
    *,
    max_segment_len: int = 30,
) -> list[str]:
    """Fail-open segment optimizer: preserve takenAt monotonic + burst integrity."""
    if not bucket:
        return []
    base = sort_bucket_asset_ids(bucket, assets_map)
    if len(base) > max(max_segment_len, 1):
        return base
    optimized = _reorder_within_runs(base, assets_map)
    if _cohesion_score(optimized, assets_map) >= _cohesion_score(base, assets_map):
        return optimized
    return base


def apply_segment_order_to_buckets(
    buckets: list[list[str]],
    assets: list[dict],
    *,
    enabled: bool,
    max_segment_len: int = 30,
) -> bool:
    """Mutate buckets in place when CAP-06 enabled; return True if any bucket changed."""
    if not enabled or not buckets:
        return False
    assets_map = {str(a["id"]): a for a in assets if a.get("id")}
    changed = False
    for i, bucket in enumerate(buckets):
        optimized = optimize_bucket_asset_ids(
            bucket,
            assets_map,
            max_segment_len=max_segment_len,
        )
        if optimized != bucket:
            changed = True
        buckets[i] = optimized
    return changed


def same_person_run_lengths(bucket: list[str], assets_map: dict[str, dict]) -> list[int]:
    runs: list[int] = []
    current = 0
    for aid in bucket:
        if asset_has_person(assets_map.get(aid, {})):
            current += 1
        else:
            if current:
                runs.append(current)
            current = 0
    if current:
        runs.append(current)
    return runs
