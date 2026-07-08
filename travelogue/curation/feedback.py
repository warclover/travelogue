from travelogue.layout_contract.feedback import *  # noqa: F403
def record_g1_edit(
    trip_id: str,
    before: dict,
    after: dict,
    *,
    user_id: str | None = None,
) -> G1EditRecord:
    dist = g1_edit_distance(before, after)
    edit_type = classify_edit_type(before, after)
    rec = G1EditRecord(
        trip_id=trip_id,
        edit_type=edit_type,
        before_snapshot=before,
        after_snapshot=after,
        distance=dist,
        user_id=user_id,
    )
    rec.weight = edit_weight_for_record(rec)
    return rec


def _chapter_asset_sets(plan: dict) -> set[str]:
    out: set[str] = set()
    for ch in plan.get("chapters") or plan.get("chapterPlan") or []:
        for item in ch.get("items") or []:
            aid = item.get("assetId")
            if aid:
                out.add(aid)
        for screen in ch.get("screens") or []:
            for slot in screen.get("slots") or []:
                aid = slot.get("assetId")
                if aid:
                    out.add(aid)
    return out


def _chapter_heroes(plan: dict) -> dict[str, str]:
    heroes = plan.get("chapterHeroAssetIds") or {}
    if heroes:
        return dict(heroes)
    out: dict[str, str] = {}
    for ch in plan.get("chapters") or []:
        hid = (ch.get("curation") or {}).get("heroAssetId")
        if ch.get("id") and hid:
            out[ch["id"]] = hid
    return out


def _screen_patterns(plan: dict) -> list[str]:
    pids: list[str] = []
    for ch in plan.get("chapters") or []:
        for s in ch.get("screens") or []:
            pid = s.get("patternId")
            if pid:
                pids.append(pid)
    return pids
