"""SSG · coverage / same-group metrics (AC-SSG-01 / AC-SSG-02)."""

from __future__ import annotations

from collections.abc import Sequence


def eligible_clustered_photos(assets: Sequence[dict]) -> list[dict]:
    """Photos that participate in the vision+scene projection path."""
    out: list[dict] = []
    for a in assets:
        if not isinstance(a, dict) or a.get("type") == "video":
            continue
        if a.get("sceneClusterId") is None:
            continue
        out.append(a)
    return out


def shot_group_coverage_ratio(assets: Sequence[dict]) -> float:
    """Fraction of clustered photos with non-empty ``shotGroupId`` (AC-SSG-01)."""
    eligible = eligible_clustered_photos(assets)
    if not eligible:
        return 1.0
    hit = sum(1 for a in eligible if a.get("shotGroupId"))
    return hit / float(len(eligible))


def same_shot_group_rate(
    pairs: Sequence[tuple[str, str]],
    assets_by_id: dict[str, dict],
) -> float:
    """Share of labeled neighbor pairs that share ``shotGroupId`` (AC-SSG-02)."""
    if not pairs:
        return 1.0
    ok = 0
    for a, b in pairs:
        ga = (assets_by_id.get(a) or {}).get("shotGroupId")
        gb = (assets_by_id.get(b) or {}).get("shotGroupId")
        if ga and gb and ga == gb:
            ok += 1
    return ok / float(len(pairs))
