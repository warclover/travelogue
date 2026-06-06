"""Asset feature assembly (M1)."""

from __future__ import annotations

from dataclasses import dataclass

from travelogue.curation.layout_planner import AspectKind, aspect_kind_for_asset


@dataclass
class AssetFeature:
    asset_id: str
    aspect_kind: AspectKind
    width: int
    height: int
    sharpness: float
    featured: bool
    has_person: bool
    focal_x: float | None
    focal_y: float | None
    taken_at: str | None
    burst_group_id: str | None


def assemble_feature(asset: dict) -> AssetFeature:
    tags = asset.get("tags") or []
    has_person = any(
        str(t).lower() in ("person", "people", "portrait", "face") for t in tags
    )
    fp = asset.get("focalPoint") or {}
    q = asset.get("quality") or {}
    return AssetFeature(
        asset_id=str(asset.get("id") or ""),
        aspect_kind=aspect_kind_for_asset(asset),
        width=int(asset.get("width") or 0),
        height=int(asset.get("height") or 0),
        sharpness=float(q.get("sharpness") or 0.0),
        featured=bool(asset.get("featured")),
        has_person=has_person,
        focal_x=float(fp["x"]) if fp.get("x") is not None else None,
        focal_y=float(fp["y"]) if fp.get("y") is not None else None,
        taken_at=asset.get("takenAt"),
        burst_group_id=asset.get("burstGroupId"),
    )


def assemble_map(assets_by_id: dict[str, dict]) -> dict[str, AssetFeature]:
    return {aid: assemble_feature(a) for aid, a in assets_by_id.items() if aid}


def feature_summary_for_window(
    asset_ids: list[str],
    assets_by_id: dict[str, dict],
) -> dict[str, float | int | str]:
    """PRD §5.2 · compact window features for decision logs / candidates."""
    feats = [
        assemble_feature(assets_by_id[aid])
        for aid in asset_ids
        if aid in assets_by_id
    ]
    if not feats:
        return {}
    portraits = sum(1 for f in feats if f.aspect_kind == "portrait")
    landscapes = sum(1 for f in feats if f.aspect_kind == "landscape")
    sharp_avg = sum(f.sharpness for f in feats) / len(feats)
    person_n = sum(1 for f in feats if f.has_person)
    burst_ids = {f.burst_group_id for f in feats if f.burst_group_id}
    return {
        "windowSize": len(asset_ids),
        "portraitCount": portraits,
        "landscapeCount": landscapes,
        "personAssetCount": person_n,
        "avgSharpness": round(sharp_avg, 4),
        "burstGroupCount": len(burst_ids),
    }
