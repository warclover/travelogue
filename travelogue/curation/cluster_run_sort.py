"""Bucket asset ordering: burst > cluster run > time (Phase 3 · G-P3-C09)."""

from __future__ import annotations

from travelogue.curation.curate_scoring import asset_sharpness, sort_bucket_asset_ids


def sort_bucket_asset_ids_run_aware(bucket: list[str], assets_by_id: dict[str, dict]) -> list[str]:
    """Preserve burst groups, then sceneClusterId runs, then takenAt order."""
    items = [(aid, assets_by_id.get(aid, {})) for aid in bucket]
    items.sort(key=lambda x: x[1].get("takenAt") or "")

    result: list[str] = []
    i = 0
    while i < len(items):
        aid, asset = items[i]
        burst_id = asset.get("burstGroupId")
        if burst_id:
            group = [aid]
            j = i + 1
            while j < len(items) and items[j][1].get("burstGroupId") == burst_id:
                group.append(items[j][0])
                j += 1
            group.sort(key=lambda x: -asset_sharpness(assets_by_id.get(x, {})))
            result.extend(group)
            i = j
            continue

        cluster_id = asset.get("sceneClusterId")
        if cluster_id is not None and cluster_id != -1:
            group = [aid]
            j = i + 1
            while j < len(items) and items[j][1].get("sceneClusterId") == cluster_id:
                if items[j][1].get("burstGroupId"):
                    break
                group.append(items[j][0])
                j += 1
            group.sort(key=lambda x: assets_by_id.get(x, {}).get("takenAt") or "")
            result.extend(group)
            i = j
            continue

        result.append(aid)
        i += 1

    return result


def sort_bucket_asset_ids_for_clustering(
    bucket: list[str],
    assets_by_id: dict[str, dict],
    *,
    run_aware: bool,
) -> list[str]:
    if run_aware and any(
        (assets_by_id.get(aid) or {}).get("sceneClusterId") not in (None, -1) for aid in bucket
    ):
        return sort_bucket_asset_ids_run_aware(bucket, assets_by_id)
    return sort_bucket_asset_ids(bucket, assets_by_id)
