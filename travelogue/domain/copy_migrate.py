"""PFM · 切身份 / 钉页数后回填手改文案（BE-PFM-25 / D-PFM-24）。

优先 assetId，其次同章顺序。回填不上的进 ``studio.copyOrphans``，禁止静默丢。
作品集 V1 正文纯图（D-PFM-22）：导语 / 图注 / 屏内 copy 不回填到正文页。
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from travelogue.config.edition import EDITION_PORTFOLIO, normalize_edition
from travelogue.domain.copy_origin import (
    ORIGIN_USER,
    is_user_protected,
    mark_origin,
)

KIND_TITLE = "title"
KIND_LEAD = "lead"
KIND_DECOR = "decorLine"
KIND_CAPTION = "caption"
KIND_KICKER = "kicker"
KIND_BODY = "body"

# 作品集正文不排这些（封面题名仍走章 title）。
_PORTFOLIO_BODY_KINDS = frozenset(
    {KIND_LEAD, KIND_DECOR, KIND_CAPTION, KIND_KICKER, KIND_BODY}
)


def collect_user_copy(trip: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    """Only user-protected / edited fragments. Meta hook 与 asset 级 caption 留在原对象。"""
    if not isinstance(trip, Mapping):
        return []
    out: list[dict[str, Any]] = []
    for ch in trip.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        ch_id = str(ch.get("id") or "") or None
        if is_user_protected(ch, "titleOrigin") and str(ch.get("title") or "").strip():
            out.append(_frag(KIND_TITLE, ch.get("title"), chapter_id=ch_id))
        if is_user_protected(ch, "leadOrigin") and str(ch.get("lead") or "").strip():
            out.append(_frag(KIND_LEAD, ch.get("lead"), chapter_id=ch_id))
        if is_user_protected(ch, "decorLineOrigin") and str(ch.get("decorLine") or "").strip():
            out.append(_frag(KIND_DECOR, ch.get("decorLine"), chapter_id=ch_id))
        for item in ch.get("items") or []:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "media-card":
                continue
            if not is_user_protected(item, "captionOrigin"):
                continue
            text = str(item.get("caption") or "").strip()
            if not text:
                continue
            aid = str(item.get("assetId") or "").strip()
            out.append(_frag(KIND_CAPTION, text, chapter_id=ch_id, asset_ids=[aid] if aid else []))
        for screen in ch.get("screens") or []:
            if not isinstance(screen, dict):
                continue
            copy = screen.get("copy") if isinstance(screen.get("copy"), dict) else {}
            meta = screen.get("copyMeta") if isinstance(screen.get("copyMeta"), dict) else {}
            aids = _screen_asset_ids(screen)
            sid = str(screen.get("screenId") or "") or None
            if _screen_field_is_user(screen, meta, "kicker") and str(copy.get("kicker") or "").strip():
                out.append(
                    _frag(
                        KIND_KICKER,
                        copy.get("kicker"),
                        chapter_id=ch_id,
                        asset_ids=aids,
                        screen_id=sid,
                    )
                )
            if _screen_field_is_user(screen, meta, "body") and str(copy.get("body") or "").strip():
                out.append(
                    _frag(
                        KIND_BODY,
                        copy.get("body"),
                        chapter_id=ch_id,
                        asset_ids=aids,
                        screen_id=sid,
                    )
                )
    return _dedupe(out)


def migrate_copy_after_recompose(
    trip: dict[str, Any],
    fragments: Iterable[Mapping[str, Any]] | None,
    *,
    edition: str,
) -> list[dict[str, Any]]:
    """回填 ``fragments`` + 旧 ``copyOrphans``。返回仍放不下的草稿。"""
    studio = trip.get("studio")
    if not isinstance(studio, dict):
        studio = {}
        trip["studio"] = studio
    prior = [
        frag
        for frag in (_normalize_orphan(x) for x in (studio.get("copyOrphans") or []))
        if frag
    ]
    incoming = _dedupe([*_normalize_many(fragments), *prior])
    body_ok = normalize_edition(edition) != EDITION_PORTFOLIO
    leftovers: list[dict[str, Any]] = []
    for frag in incoming:
        kind = str(frag.get("kind") or "")
        if not body_ok and kind in _PORTFOLIO_BODY_KINDS:
            leftovers.append({**frag, "reason": frag.get("reason") or "portfolio_body"})
            continue
        if _place_fragment(trip, frag):
            continue
        leftovers.append({**frag, "reason": frag.get("reason") or "no_slot"})
    if leftovers:
        studio["copyOrphans"] = leftovers
    else:
        studio.pop("copyOrphans", None)
    return leftovers


def _place_fragment(trip: dict[str, Any], frag: Mapping[str, Any]) -> bool:
    kind = str(frag.get("kind") or "")
    text = str(frag.get("text") or "").strip()
    if not kind or not text:
        return True
    ch_id = str(frag.get("chapterId") or "") or None
    if kind in {KIND_TITLE, KIND_LEAD, KIND_DECOR}:
        ch = _chapter_by_id(trip, ch_id)
        if ch is None:
            return False
        if kind == KIND_TITLE:
            ch["title"] = text
            mark_origin(ch, "titleOrigin")
        elif kind == KIND_LEAD:
            ch["lead"] = text
            mark_origin(ch, "leadOrigin")
        else:
            ch["decorLine"] = text
            mark_origin(ch, "decorLineOrigin")
        return True
    if kind == KIND_CAPTION:
        item = _item_by_asset_ids(trip, frag.get("assetIds") or [])
        if item is None:
            return False
        item["caption"] = text
        mark_origin(item, "captionOrigin")
        return True
    if kind in {KIND_KICKER, KIND_BODY}:
        screen = _best_screen(trip, frag)
        if screen is None:
            return False
        copy = screen.setdefault("copy", {})
        copy[kind] = text
        screen["edited"] = True
        meta = screen.setdefault("copyMeta", {})
        meta["kickerSource" if kind == KIND_KICKER else "bodySource"] = ORIGIN_USER
        return True
    return False


def _chapter_by_id(trip: Mapping[str, Any], chapter_id: str | None) -> dict[str, Any] | None:
    if not chapter_id:
        return None
    for ch in trip.get("chapters") or []:
        if isinstance(ch, dict) and str(ch.get("id") or "") == chapter_id:
            return ch
    return None


def _item_by_asset_ids(trip: Mapping[str, Any], asset_ids: Iterable[Any]) -> dict[str, Any] | None:
    wanted = {str(x).strip() for x in asset_ids if str(x).strip()}
    if not wanted:
        return None
    for ch in trip.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        for item in ch.get("items") or []:
            if not isinstance(item, dict) or item.get("type") != "media-card":
                continue
            if str(item.get("assetId") or "") in wanted:
                return item
    return None


def _best_screen(trip: Mapping[str, Any], frag: Mapping[str, Any]) -> dict[str, Any] | None:
    wanted = {str(x).strip() for x in (frag.get("assetIds") or []) if str(x).strip()}
    ch_id = str(frag.get("chapterId") or "")
    best: tuple[int, dict[str, Any]] | None = None
    fallback: dict[str, Any] | None = None
    for ch in trip.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        same_ch = str(ch.get("id") or "") == ch_id
        for screen in ch.get("screens") or []:
            if not isinstance(screen, dict):
                continue
            if same_ch and fallback is None:
                fallback = screen
            overlap = len(wanted.intersection(_screen_asset_ids(screen)))
            if overlap and (best is None or overlap > best[0]):
                best = (overlap, screen)
    if best:
        return best[1]
    return fallback


def _screen_asset_ids(screen: Mapping[str, Any]) -> list[str]:
    ids: list[str] = []
    for slot in screen.get("slots") or []:
        if not isinstance(slot, dict):
            continue
        aid = str(slot.get("assetId") or "").strip()
        if aid:
            ids.append(aid)
    return ids


def _screen_field_is_user(screen: Mapping[str, Any], meta: Mapping[str, Any], field: str) -> bool:
    source_key = "kickerSource" if field == "kicker" else "bodySource"
    if str(meta.get(source_key) or "") == ORIGIN_USER:
        return True
    return bool(screen.get("edited"))


def _frag(
    kind: str,
    text: object,
    *,
    chapter_id: str | None = None,
    asset_ids: list[str] | None = None,
    screen_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "kind": kind,
        "text": str(text or "").strip(),
    }
    if chapter_id:
        row["chapterId"] = chapter_id
    if asset_ids:
        row["assetIds"] = [a for a in asset_ids if a]
    if screen_id:
        row["screenId"] = screen_id
    if reason:
        row["reason"] = reason
    return row


def _normalize_orphan(raw: object) -> dict[str, Any] | None:
    if not isinstance(raw, Mapping):
        return None
    text = str(raw.get("text") or "").strip()
    kind = str(raw.get("kind") or "").strip()
    if not text or not kind:
        return None
    return _frag(
        kind,
        text,
        chapter_id=str(raw.get("chapterId") or "") or None,
        asset_ids=[str(x) for x in (raw.get("assetIds") or []) if x],
        screen_id=str(raw.get("screenId") or "") or None,
        reason=str(raw.get("reason") or "") or None,
    )


def _normalize_many(rows: Iterable[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw in rows or []:
        frag = _normalize_orphan(raw)
        if frag:
            out.append(frag)
    return out


def _dedupe(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple] = set()
    out: list[dict[str, Any]] = []
    for raw in rows:
        frag = _normalize_orphan(raw)
        if not frag:
            continue
        key = (
            str(frag.get("kind") or ""),
            str(frag.get("text") or ""),
            str(frag.get("chapterId") or ""),
            tuple(str(x) for x in (frag.get("assetIds") or [])),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(frag)
    return out
