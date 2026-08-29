"""Share-Face Purity · open-path migrate, temporal sort, weak-caption density (SFP)."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

_ORDINAL_FACE_RE = re.compile(r"·\s*(?:[二三四五六七八九十]|\d+)\s*$")


def strip_ordinal_face_title(title: str) -> str:
    """Sequence Pass · drop reader-facing ·二/·三/·N suffixes (layer-0)."""
    t = (title or "").strip()
    if not t:
        return t
    cleaned = _ORDINAL_FACE_RE.sub("", t).strip().rstrip("·• ")
    return cleaned or t


def _chapter_asset_ids_local(chapter: dict[str, Any]) -> list[str]:
    """Layer-0 chapter asset id collect (avoid curation import)."""
    try:
        from travelogue.layout_contract.chapter_items import collect_screen_asset_ids

        if chapter.get("screens"):
            return list(collect_screen_asset_ids(chapter))
    except Exception:
        pass
    ids: list[str] = []
    for item in chapter.get("items") or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "media-card" and item.get("assetId"):
            ids.append(str(item["assetId"]))
        elif item.get("type") in ("media-row", "media-scroll"):
            ids.extend(str(a) for a in (item.get("assetIds") or []) if a)
    return ids


def emit_sfp_event(event: str, meta: dict[str, Any] | None = None) -> None:
    """Best-effort SFP telemetry · never break curate/render/open paths."""
    try:
        from travelogue.domain.studio_events import append_studio_homepage_event

        append_studio_homepage_event(event, meta)
    except Exception:
        pass


def migrate_ordinal_chapter_titles(trip: dict[str, Any] | None) -> list[str]:
    """D-SFP-12 · strip reader-facing ·二/·三 from non-user chapter titles (idempotent)."""
    from travelogue.domain.copy_origin import is_user_protected

    trip = trip if isinstance(trip, dict) else None
    if not trip:
        return []
    updated: list[str] = []
    for ch in trip.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        if (ch.get("curation") or {}).get("isAppendix"):
            continue
        if is_user_protected(ch, "titleOrigin"):
            continue
        raw = str(ch.get("title") or "").strip()
        cleaned = strip_ordinal_face_title(raw)
        if cleaned and cleaned != raw:
            ch["title"] = cleaned[:12]
            updated.append(str(ch.get("id") or ""))
    if updated:
        emit_sfp_event(
            "sfp_chapter_title_sequence_pass",
            {"count": len(updated), "chapterIds": updated[:12]},
        )
    return updated


def enforce_no_ordinal_face_titles(trip: dict[str, Any] | None) -> list[str]:
    """§4.1④ · curate 后闸：非用户锁章名不得残留序号腔（strip + emit）。"""
    return migrate_ordinal_chapter_titles(trip)


def migrate_share_face_purity_on_open(trip: dict[str, Any] | None) -> dict[str, Any]:
    """D-SFP-12 · silent open/pipeline migrate for dirty displayTitle + ordinal titles.

    Skips user-protected magazine title (titleOrigin=user) and
    user-locked chapter titles. Returns ``{displayTitle, chapters, changed}``.
    """
    from travelogue.domain.copy_origin import is_user_protected
    from travelogue.domain.title_humanize import migrate_stale_display_title

    trip = trip if isinstance(trip, dict) else None
    if not trip:
        return {"displayTitle": False, "chapters": [], "changed": False}

    meta = trip.get("meta") if isinstance(trip.get("meta"), dict) else None
    display_migrated = False
    if meta is not None and not is_user_protected(meta, "titleOrigin"):
        display_migrated = bool(migrate_stale_display_title(meta))
        if display_migrated:
            emit_sfp_event(
                "sfp_display_title_migrated",
                {
                    "title": str(meta.get("title") or "")[:32],
                    "displayTitle": str(meta.get("displayTitle") or "")[:32],
                },
            )

    import importlib

    migrate_cross_year_chapter_titles = importlib.import_module(
        "travelogue.curation.chapter_titles"
    ).migrate_cross_year_chapter_titles

    chapter_ids = migrate_ordinal_chapter_titles(trip)
    year_ids = migrate_cross_year_chapter_titles(trip)
    # SNR D-SNR-03 · 非手改章名 idempotent 薄章名 refresh（与 D-SFP-12 同纪律）
    thin_ids: list[str] = []
    try:
        refresh_chapter_titles_on_trip = importlib.import_module(
            "travelogue.curation.chapter_titles"
        ).refresh_chapter_titles_on_trip

        thin_paths = refresh_chapter_titles_on_trip(trip)
        for path in thin_paths:
            # paths like chapters[0].title → keep chapter id when possible
            m = path
            thin_ids.append(str(m))
    except Exception:
        thin_ids = []
    lead_ids: list[str] = []
    try:
        fill_empty_stub_leads = importlib.import_module(
            "travelogue.services.narrate"
        ).fill_empty_stub_leads
        lead_ids = list(fill_empty_stub_leads(trip) or [])
    except Exception:
        lead_ids = []
    all_chapter_ids = list(dict.fromkeys([*chapter_ids, *year_ids, *thin_ids, *lead_ids]))
    return {
        "displayTitle": display_migrated,
        "chapters": all_chapter_ids,
        "changed": bool(display_migrated or all_chapter_ids),
    }


def chapter_temporal_key(chapter: dict[str, Any], assets_by_id: dict[str, dict]) -> tuple[int, str]:
    """Return ``(timestamp_ms or max, chapter_id)`` for stable ascending sort."""
    best: int | None = None
    for aid in _chapter_asset_ids_local(chapter):
        asset = assets_by_id.get(str(aid)) or {}
        raw = str(asset.get("takenAt") or "").strip()
        if not raw:
            continue
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            continue
        ms = int(dt.timestamp() * 1000)
        if best is None or ms < best:
            best = ms
    # No reliable time → sort last (D-SFP-07)
    return (best if best is not None else 2**62, str(chapter.get("id") or ""))


def sort_chapters_by_temporal_key(
    chapters: list[dict[str, Any]],
    assets: list[dict] | None,
) -> tuple[list[dict[str, Any]], bool]:
    """D-SFP-07 · SSOT chapter order by min reliable takenAt; appendix stays at end."""
    if not chapters:
        return chapters, False
    assets_by_id = {
        str(a["id"]): a for a in (assets or []) if isinstance(a, dict) and a.get("id")
    }
    main: list[dict[str, Any]] = []
    appendix: list[dict[str, Any]] = []
    for ch in chapters:
        if not isinstance(ch, dict):
            continue
        if (ch.get("curation") or {}).get("isAppendix"):
            appendix.append(ch)
        else:
            main.append(ch)
    keyed = [(chapter_temporal_key(ch, assets_by_id), i, ch) for i, ch in enumerate(main)]
    sorted_main = [ch for _, _, ch in sorted(keyed, key=lambda t: (t[0], t[1]))]
    reordered = sorted_main != main
    out = sorted_main + appendix
    if reordered:
        for i, ch in enumerate(out, start=1):
            if "index" in ch:
                ch["index"] = i
        emit_sfp_event(
            "sfp_chapter_time_sort_applied",
            {"chapterCount": len(sorted_main), "appendixCount": len(appendix)},
        )
    return out, reordered


def suppress_repeated_weak_captions(
    captions_by_asset: dict[str, str],
    *,
    max_same: int = 3,
) -> dict[str, str]:
    """§4.3 · blank captions that repeat the same short label ≥ max_same times."""
    counts: dict[str, int] = {}
    for cap in captions_by_asset.values():
        key = (cap or "").strip()
        if key:
            counts[key] = counts.get(key, 0) + 1
    banned = {k for k, n in counts.items() if n >= max_same and len(k) <= 6}
    if not banned:
        return captions_by_asset
    return {
        aid: ("" if (cap or "").strip() in banned else cap)
        for aid, cap in captions_by_asset.items()
    }
