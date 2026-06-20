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
        meta["hook"] = value[:HOOK_MAX]
        meta["edited"] = True
        return "meta.hook"

    if path == "meta.title":
        from travelogue.services.trip import apply_intent

        cleaned = value[:META_TITLE_MAX].strip()
        apply_intent(trip, title=cleaned if cleaned else None)
        meta["edited"] = True
        return "meta.title"

    if path == "meta.coverOpeningStyle":
        from travelogue.services.cover_opening_style import COVER_OPENING_STYLES

        cleaned = value.strip()
        if cleaned not in COVER_OPENING_STYLES:
            raise CopyPatchError(
                "E_COPY_PATCH",
                f"invalid coverOpeningStyle {cleaned!r}; expected one of {COVER_OPENING_STYLES}",
            )
        meta["coverOpeningStyle"] = cleaned
        meta["edited"] = True
        return "meta.coverOpeningStyle"

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
        trip["epilogue"] = value[:EPILOGUE_MAX]
        meta["edited"] = True
        return "epilogue"

    if path.startswith("chapters.") and path.endswith(".lead"):
        ch_id = path[len("chapters.") : -len(".lead")]
        for ch in trip.get("chapters") or []:
            if ch.get("id") == ch_id:
                ch["lead"] = value[:LEAD_MAX]
                ch["edited"] = True
                return path
        raise CopyPatchError("E_COPY_PATCH", f"unknown chapter {ch_id!r}")

    if path.startswith("chapters.") and path.endswith(".decorLine"):
        ch_id = path[len("chapters.") : -len(".decorLine")]
        for ch in trip.get("chapters") or []:
            if ch.get("id") == ch_id:
                ch["decorLine"] = value[:DECOR_LINE_MAX]
                ch["edited"] = True
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
                    item["caption"] = value[:CAPTION_MAX]
                    item["edited"] = True
                    return path
                if field == "voice.transcript":
                    voice = item.setdefault("voice", {})
                    voice["transcript"] = value[:TRANSCRIPT_MAX]
                    return path
                raise CopyPatchError("E_COPY_PATCH", f"unsupported item field {field!r}")
        raise CopyPatchError("E_COPY_PATCH", f"unsupported path {path!r}")

    if path.startswith("items.") and path.endswith(".caption"):
        asset_id = path[len("items.") : -len(".caption")]
        item = _find_item_by_asset_id(trip, asset_id)
        if item:
            item["caption"] = value[:CAPTION_MAX]
            item["edited"] = True
            return path
        assets = {a.get("id"): a for a in trip.get("assets") or [] if a.get("id")}
        asset = assets.get(asset_id)
        if not asset:
            raise CopyPatchError("E_COPY_PATCH", f"unknown item asset {asset_id!r}")
        asset["caption"] = value[:CAPTION_MAX]
        return path

    if path.startswith("assets.") and path.endswith(".caption"):
        asset_id = path[len("assets.") : -len(".caption")]
        assets = {a.get("id"): a for a in trip.get("assets") or [] if a.get("id")}
        asset = assets.get(asset_id)
        if not asset:
            raise CopyPatchError("E_COPY_PATCH", f"unknown asset {asset_id!r}")
        from travelogue.curation.asset_caption import apply_caption_to_trip

        apply_caption_to_trip(trip, asset_id, value[:CAPTION_MAX] if value else "")
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
        pipe = trip.setdefault("pipeline", {})
        if pipe.get("status") == "copy_locked":
            pipe["status"] = "copy_draft"
            locks = pipe.setdefault("locks", {})
            locks["copy"] = False
        copy_paths = {
            p
            for p in paths
            if p in ("meta.hook", "epilogue") or p.endswith(".decorLine") or p.endswith(".lead")
        }
        if copy_paths:
            from travelogue.services.copy_metrics import record_copy_metrics

            record_copy_metrics(trip)
    return updated
