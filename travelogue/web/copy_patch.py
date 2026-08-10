"""Apply inline copy edits from draft HTML preview to trip.json."""

from __future__ import annotations

from travelogue.errors import CodeError
from travelogue.util.datetime_ import utc_now_iso as _utc_now_iso

HOOK_MAX = 56
EPILOGUE_MAX = 80
LEAD_MAX = 80
DECOR_LINE_MAX = 30
SCREEN_COPY_KICKER_MAX = 30
SCREEN_COPY_BODY_MAX = 80
CAPTION_MAX = 60
TITLE_MAX = 14
META_TITLE_MAX = 20
ANCHOR_MAX = 24
ANCHOR_MAX_ITEMS = 3
TRANSCRIPT_MAX = 2000


class CopyPatchError(CodeError):
    pass


def _find_screen_by_ids(trip: dict, chapter_id: str, screen_id: str) -> dict | None:
    for ch in trip.get("chapters") or []:
        if ch.get("id") != chapter_id:
            continue
        for sc in ch.get("screens") or []:
            if sc.get("screenId") == screen_id:
                return sc
    return None


def _find_item_by_asset_id(trip: dict, asset_id: str) -> dict | None:
    for ch in trip.get("chapters") or []:
        for it in ch.get("items") or []:
            if it.get("type") == "media-card" and it.get("assetId") == asset_id:
                return it
            if it.get("type") in ("media-row", "media-scroll"):
                if asset_id in (it.get("assetIds") or []):
                    return it
    return None


def apply_copy_patch(trip: dict, path: str, value: str) -> str:
    """
    Apply one edit path. Returns a short label for logging.

    Paths: meta.hook, meta.title, meta.coverOpeningStyle, epilogue, chapters.<id>.lead, ...
           chapters.<id>.items.<index>.caption|voice.transcript,
           items.<assetId>.caption|title, assets.<assetId>.caption|voice.transcript
    """
    value = (value or "").strip()
    meta = trip.setdefault("meta", {})

    if path == "meta.hook":
        from travelogue.domain.copy_origin import mark_origin

        meta["hook"] = value[:HOOK_MAX]
        mark_origin(meta, "hookOrigin")
        return "meta.hook"

    if path == "meta.title":
        from travelogue.cover_engine.title_art.engine import mark_title_art_stale
        from travelogue.services.trip import apply_intent

        cleaned = value[:META_TITLE_MAX].strip()
        apply_intent(trip, title=cleaned if cleaned else None)
        meta["edited"] = True
        # PRD-COVER-CALLIGRAPHY-TITLE-V1 §7 stale 合同 / AC-CAL-09：主串是贴纸
        # 的字面来源，题目一变，已生成的贴纸就是「旧文案」——必须置 stale，
        # 禁止继续把改名前烧进 PNG 里的旧字当作「已更新」展示。
        mark_title_art_stale(trip)
        return "meta.title"

    if path == "meta.coverOpeningStyle":
        from travelogue.cover_engine import assignable_style_ids, is_assignable
        from travelogue.cover_engine.title_art.engine import mark_title_art_stale

        cleaned = value.strip()
        if not is_assignable(cleaned):
            allowed = assignable_style_ids()
            raise CopyPatchError(
                "E_COPY_PATCH",
                f"invalid coverOpeningStyle {cleaned!r}; expected one of {allowed}",
            )
        meta["coverOpeningStyle"] = cleaned
        meta["edited"] = True
        # 换了 Opening 风格，白名单归属（D-CAL-10）、§6.2 定位 rect 都要重算。
        mark_title_art_stale(trip)
        return "meta.coverOpeningStyle"

    if path == "meta.worksBrandMode":
        from travelogue.domain.works_brand import normalize_works_brand_mode

        meta["worksBrandMode"] = normalize_works_brand_mode(value)
        meta["edited"] = True
        return "meta.worksBrandMode"

    if path == "meta.worksBrandText":
        from travelogue.domain.works_brand import BRAND_TEXT_MAX

        meta["worksBrandText"] = value[:BRAND_TEXT_MAX]
        meta["edited"] = True
        return "meta.worksBrandText"

    if path == "export.longshotDensity":
        cleaned = value.strip().lower()
        if cleaned not in ("default", "compact"):
            raise CopyPatchError(
                "E_COPY_PATCH",
                f"invalid longshotDensity {cleaned!r}; expected default|compact",
            )
        export = trip.setdefault("export", {})
        export["longshotDensity"] = cleaned
        return "export.longshotDensity"

    if path.startswith("chapters.") and path.endswith(".curation.memoryAnchors"):
        ch_id = path[len("chapters.") : -len(".curation.memoryAnchors")]
        anchors = [
            part.strip()[:ANCHOR_MAX]
            for part in value.replace("，", ",").split(",")
            if part.strip()
        ][:ANCHOR_MAX_ITEMS]
        for ch in trip.get("chapters") or []:
            if ch.get("id") == ch_id:
                curation = ch.setdefault("curation", {})
                if anchors:
                    curation["memoryAnchors"] = anchors
                else:
                    curation.pop("memoryAnchors", None)
                ch["edited"] = True
                return path
        raise CopyPatchError("E_COPY_PATCH", f"unknown chapter {ch_id!r}")

    if path == "epilogue":
        from travelogue.domain.copy_origin import ORIGIN_USER

        trip["epilogue"] = value[:EPILOGUE_MAX]
        trip["epilogueOrigin"] = ORIGIN_USER
        meta["edited"] = True
        return "epilogue"

    if path.startswith("chapters.") and path.endswith(".title"):
        from travelogue.domain.copy_origin import mark_origin

        ch_id = path[len("chapters.") : -len(".title")]
        for ch in trip.get("chapters") or []:
            if ch.get("id") == ch_id:
                ch["title"] = value[:TITLE_MAX]
                mark_origin(ch, "titleOrigin")
                return path
        raise CopyPatchError("E_COPY_PATCH", f"unknown chapter {ch_id!r}")

    if path.startswith("chapters.") and path.endswith(".lead"):
        from travelogue.domain.copy_origin import mark_origin

        ch_id = path[len("chapters.") : -len(".lead")]
        for ch in trip.get("chapters") or []:
            if ch.get("id") == ch_id:
                ch["lead"] = value[:LEAD_MAX]
                mark_origin(ch, "leadOrigin")
                return path
        raise CopyPatchError("E_COPY_PATCH", f"unknown chapter {ch_id!r}")

    if path.startswith("chapters.") and path.endswith(".decorLine"):
        from travelogue.domain.copy_origin import mark_origin

        ch_id = path[len("chapters.") : -len(".decorLine")]
        for ch in trip.get("chapters") or []:
            if ch.get("id") == ch_id:
                ch["decorLine"] = value[:DECOR_LINE_MAX]
                mark_origin(ch, "decorLineOrigin")
                return path
        raise CopyPatchError("E_COPY_PATCH", f"unknown chapter {ch_id!r}")

    if path.startswith("chapters.") and ".screens." in path and ".copy." in path:
        parts = path.split(".")
        if len(parts) == 6 and parts[0] == "chapters" and parts[2] == "screens" and parts[4] == "copy":
            ch_id, screen_id, field = parts[1], parts[3], parts[5]
            screen = _find_screen_by_ids(trip, ch_id, screen_id)
            if not screen:
                raise CopyPatchError(
                    "E_COPY_PATCH",
                    f"unknown screen {screen_id!r} in chapter {ch_id!r}",
                )
            copy = screen.setdefault("copy", {})
            if field == "kicker":
                if value:
                    copy["kicker"] = value[:SCREEN_COPY_KICKER_MAX]
                else:
                    copy.pop("kicker", None)
                screen["edited"] = True
                return path
            if field == "body":
                if value:
                    copy["body"] = value[:SCREEN_COPY_BODY_MAX]
                else:
                    copy.pop("body", None)
                screen["edited"] = True
                return path
            raise CopyPatchError("E_COPY_PATCH", f"unsupported screen copy field {field!r}")
        raise CopyPatchError("E_COPY_PATCH", f"unsupported path {path!r}")

    if path.startswith("chapters.") and ".items." in path:
        parts = path.split(".")
        if len(parts) >= 5 and parts[0] == "chapters" and parts[2] == "items":
            ch_id = parts[1]
            try:
                idx = int(parts[3])
            except ValueError as exc:
                raise CopyPatchError("E_COPY_PATCH", f"invalid item index in {path!r}") from exc
            field = ".".join(parts[4:])
            for ch in trip.get("chapters") or []:
                if ch.get("id") != ch_id:
                    continue
                items = ch.get("items") or []
                if idx < 0 or idx >= len(items):
                    raise CopyPatchError("E_COPY_PATCH", f"item index {idx} out of range for {ch_id!r}")
                item = items[idx]
                if field == "caption":
                    from travelogue.domain.copy_origin import mark_origin

                    item["caption"] = value[:CAPTION_MAX]
                    mark_origin(item, "captionOrigin")
                    return path
                if field == "voice.transcript":
                    voice = item.setdefault("voice", {})
                    voice["transcript"] = value[:TRANSCRIPT_MAX]
                    return path
                raise CopyPatchError("E_COPY_PATCH", f"unsupported item field {field!r}")
        raise CopyPatchError("E_COPY_PATCH", f"unsupported path {path!r}")

    if path.startswith("items.") and path.endswith(".caption"):
        from travelogue.domain.copy_origin import mark_origin

        asset_id = path[len("items.") : -len(".caption")]
        item = _find_item_by_asset_id(trip, asset_id)
        if item:
            item["caption"] = value[:CAPTION_MAX]
            mark_origin(item, "captionOrigin")
            return path
        assets = {a.get("id"): a for a in trip.get("assets") or [] if a.get("id")}
        asset = assets.get(asset_id)
        if not asset:
            raise CopyPatchError("E_COPY_PATCH", f"unknown item asset {asset_id!r}")
        asset["caption"] = value[:CAPTION_MAX]
        mark_origin(asset, "captionOrigin")
        return path

    if path.startswith("assets.") and path.endswith(".caption"):
        from travelogue.domain.copy_origin import mark_origin

        asset_id = path[len("assets.") : -len(".caption")]
        assets = {a.get("id"): a for a in trip.get("assets") or [] if a.get("id")}
        asset = assets.get(asset_id)
        if not asset:
            raise CopyPatchError("E_COPY_PATCH", f"unknown asset {asset_id!r}")
        from travelogue.curation.asset_caption import apply_caption_to_trip

        apply_caption_to_trip(trip, asset_id, value[:CAPTION_MAX] if value else "")
        mark_origin(asset, "captionOrigin")
        return path

    if path.startswith("assets.") and path.endswith(".skipCaption"):
        asset_id = path[len("assets.") : -len(".skipCaption")]
        assets = {a.get("id"): a for a in trip.get("assets") or [] if a.get("id")}
        asset = assets.get(asset_id)
        if not asset:
            raise CopyPatchError("E_COPY_PATCH", f"unknown asset {asset_id!r}")
        if value.lower() in ("true", "1", "yes"):
            asset["skipCaption"] = True
            asset.pop("caption", None)
        else:
            asset.pop("skipCaption", None)
        return path

    if path.startswith("items.") and path.endswith(".title"):
        asset_id = path[len("items.") : -len(".title")]
        item = _find_item_by_asset_id(trip, asset_id)
        if not item or item.get("type") != "media-card":
            raise CopyPatchError("E_COPY_PATCH", f"unknown media-card {asset_id!r}")
        item["title"] = value[:TITLE_MAX]
        item["edited"] = True
        return path

    if path.startswith("assets.") and path.endswith(".voice.transcript"):
        asset_id = path[len("assets.") : -len(".voice.transcript")]
        assets = {a.get("id"): a for a in trip.get("assets") or [] if a.get("id")}
        asset = assets.get(asset_id)
        if not asset:
            raise CopyPatchError("E_COPY_PATCH", f"unknown asset {asset_id!r}")
        voice = asset.setdefault("voice", {})
        voice["transcript"] = value[:TRANSCRIPT_MAX]
        return path

    raise CopyPatchError("E_COPY_PATCH", f"unsupported path {path!r}")


def apply_copy_patches(trip: dict, patches: list[dict]) -> list[str]:
    paths = [str(p.get("path") or "") for p in patches if p.get("path")]
    from travelogue.templating.guardrails import enforce_copy_paths

    try:
        enforce_copy_paths(trip, paths)
    except ValueError as exc:
        if str(exc).startswith("E_TEMPLATE_GUARDRAIL"):
            raise CopyPatchError("E_TEMPLATE_GUARDRAIL", str(exc).split(": ", 1)[-1]) from exc
        raise
    updated: list[str] = []
    for patch in patches:
        path = patch.get("path")
        if not path:
            continue
        updated.append(apply_copy_patch(trip, str(path), str(patch.get("value") or "")))
    if updated:
        trip["updatedAt"] = _utc_now_iso()
        from travelogue.services.pipeline_state import revert_copy_lock_for_edit

        revert_copy_lock_for_edit(trip)
        copy_paths = {
            p
            for p in paths
            if p in ("meta.hook", "epilogue") or p.endswith(".decorLine") or p.endswith(".lead")
        }
        if copy_paths:
            from travelogue.services.copy_metrics import record_copy_metrics

            record_copy_metrics(trip)
        # D2 · non-title save path: migrate stale displayTitle (title patches dual-write in apply_intent)
        if "meta.title" not in updated:
            from travelogue.domain.title_humanize import migrate_stale_display_title

            meta = trip.get("meta") if isinstance(trip.get("meta"), dict) else None
            if migrate_stale_display_title(meta):
                try:
                    from travelogue.domain.studio_events import append_studio_homepage_event

                    append_studio_homepage_event(
                        "rename_propagation_migrated",
                        {
                            "title": str((meta or {}).get("title") or "")[:32],
                            "displayTitle": str((meta or {}).get("displayTitle") or "")[:32],
                            "via": "save_copy",
                        },
                    )
                except Exception:
                    pass
    return updated
