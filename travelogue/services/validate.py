"""L1 schema + L2 manifest validation."""

from __future__ import annotations

import json
import re
from pathlib import Path

from travelogue.paths import MANIFEST_PATH, SCHEMA_PATH

# Shipping magazine faces look like page-1-hero-land-wide (not matcher fixtures page-grid-4).
_PROMOTED_PAGE_ID = re.compile(r"^page-\d+-")


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def validation_error_code(err: str) -> str:
    """Extract E_VALIDATE_* code from validate_trip error string."""
    token = err.split()[0]
    if token.startswith("E_VALIDATE"):
        return token
    return "E_VALIDATE"


def char_len(s: str) -> int:
    return len(s)


ROW_LAYOUTS = frozenset(
    {
        "landscape-triple",
        "landscape-pair",
        "portrait-triple",
        "portrait-pair",
        "square-triple",
        "square-pair",
    }
)
ROW_LAYOUT_COUNTS: dict[str, int] = {
    "landscape-triple": 3,
    "landscape-pair": 2,
    "portrait-triple": 3,
    "portrait-pair": 2,
    "square-triple": 3,
    "square-pair": 2,
}
CARD_SLOTS = frozenset({"panorama", "square", "tall"})
ASPECT_KINDS = frozenset({"portrait", "landscape", "square", "panorama", "tall"})


def validate_schema(trip: dict, schema_path: Path | None = None) -> list[str]:
    try:
        import jsonschema
    except ImportError:
        return ["WARN: jsonschema not installed; skip L1 (pip install jsonschema)"]

    schema = load_json(schema_path or SCHEMA_PATH)
    validator = jsonschema.Draft202012Validator(schema)
    errors: list[str] = []
    for err in sorted(validator.iter_errors(trip), key=lambda e: list(e.path)):
        path = ".".join(str(p) for p in err.path) or "(root)"
        errors.append(f"E_VALIDATE_SCHEMA [{path}] {err.message}")
    errors.extend(validate_page_pattern_ids(trip))
    return errors


def validate_page_pattern_ids(trip: dict) -> list[str]:
    """Allow page-* persist on portfolio trips only; promoted faces must exist in LTE.

    Matcher fixtures (``page-grid-4``) stay schema-legal but are not shipping SKUs.
    Journal MCS still cannot select ``page-*`` (list_active skip); this is persist isolation.
    """
    from travelogue.config.edition import is_portfolio_trip

    is_portfolio = is_portfolio_trip(trip)
    errors: list[str] = []
    engine = None
    for ci, ch in enumerate(trip.get("chapters") or []):
        if not isinstance(ch, dict):
            continue
        for si, sc in enumerate(ch.get("screens") or []):
            if not isinstance(sc, dict):
                continue
            pid = str(sc.get("patternId") or "")
            if not pid.startswith("page-"):
                continue
            path = f"chapters[{ci}].screens[{si}].patternId"
            if not is_portfolio:
                errors.append(
                    f"E_VALIDATE_SCHEMA [{path}] page-* is portfolio-only ({pid})"
                )
                continue
            if not _PROMOTED_PAGE_ID.match(pid):
                continue
            if engine is None:
                from travelogue.layout_templates.registry import get_engine

                engine = get_engine()
            try:
                engine.get(pid)
            except KeyError:
                errors.append(f"E_VALIDATE_SCHEMA [{path}] unknown page face {pid}")
    return errors


def asset_map(trip: dict) -> dict[str, dict]:
    return {a["id"]: a for a in trip.get("assets", [])}


def chapter_asset_ids(chapter: dict) -> list[str]:
    """Asset ids referenced by chapter items and screens."""
    ids: list[str] = []
    for it in chapter.get("items", []):
        itype = it.get("type")
        if itype == "media-card":
            aid = it.get("assetId")
            if aid:
                ids.append(aid)
        elif itype in ("media-row", "media-scroll"):
            ids.extend(it.get("assetIds") or [])
    for screen in chapter.get("screens") or []:
        for slot in screen.get("slots") or []:
            aid = slot.get("assetId")
            if aid:
                ids.append(aid)
    return ids


def chapter_visual_units(chapter: dict) -> int:
    """
    Count presentation units in a chapter (VR-P05).

    Each media-card, media-row, or media-scroll block counts as 1;
    each layout-screen counts as 1 (allows 1 card + multiple screens).
    """
    units = 0
    for it in chapter.get("items", []):
        itype = it.get("type")
        if itype in ("media-card", "media-row", "media-scroll"):
            units += 1
    units += len(chapter.get("screens") or [])
    return units


def _cover_ids_for_moment_check(trip: dict) -> set[str]:
    out: set[str] = set()
    primary = str(trip.get("coverAssetId") or "").strip()
    if primary:
        out.add(primary)
    by_layout = (trip.get("curation") or {}).get("coverByLayout") or {}
    if isinstance(by_layout, dict):
        for value in by_layout.values():
            aid = str(value or "").strip()
            if aid:
                out.add(aid)
    return out


def _validate_moment_refs(trip: dict, assets: dict[str, dict]) -> list[str]:
    """Phase 23 · momentAssetId must reference a valid asset and belong to momentPoolIds."""
    errors: list[str] = []
    moment_id = str(trip.get("momentAssetId") or "").strip()
    if not moment_id:
        return errors
    if moment_id not in assets:
        errors.append(f"E_VALIDATE_REF momentAssetId missing: {moment_id}")
        return errors
    if assets[moment_id].get("type") != "image":
        errors.append(f"E_VALIDATE_REF momentAssetId must be image: {moment_id}")
    pool = (trip.get("curation") or {}).get("momentPoolIds") or []
    if isinstance(pool, list) and pool and moment_id not in pool:
        errors.append(
            f"E_VALIDATE_REF momentAssetId {moment_id} not in curation.momentPoolIds"
        )
    if moment_id in _cover_ids_for_moment_check(trip):
        errors.append(
            f"E_VALIDATE_REF momentAssetId must not equal cover: {moment_id}"
        )
    return errors


def validate_manifest(
    trip: dict,
    manifest: dict | None = None,
    *,
    manifest_path: Path | None = None,
) -> list[str]:
    if manifest is None:
        manifest = load_json(manifest_path or MANIFEST_PATH)
    errors: list[str] = []
    limits = manifest.get("limits", {})
    assets = asset_map(trip)
    meta = trip.get("meta", {})
    pipe = trip.get("pipeline", {})
    status = pipe.get("status")

    if char_len(meta.get("title", "")) > limits.get("tripTitleMaxChars", 20):
        errors.append("E_VALIDATE_LIMIT meta.title too long")
    if meta.get("hook") and char_len(meta["hook"]) > limits.get("hookMaxChars", 56):
        errors.append("E_VALIDATE_LIMIT meta.hook too long")

    max_photos = int(limits.get("maxPhotosPerTrip", 250))
    if len(assets) > max_photos:
        errors.append(
            f"E_INGEST_LIMIT_PHOTOS asset count {len(assets)} exceeds maxPhotosPerTrip {max_photos} (VR-L06)"
        )

    max_videos = int(limits.get("maxVideosPerTrip", 3))
    trip_videos = sum(1 for a in assets.values() if a.get("type") == "video")
    if trip_videos > max_videos:
        errors.append(
            f"E_VALIDATE_MANIFEST video count {trip_videos} exceeds maxVideosPerTrip {max_videos} (VR-L07)"
        )

    max_voices = int(limits.get("maxVoicePerTrip", 15))
    trip_voices = sum(1 for a in assets.values() if a.get("voice"))
    if trip_voices > max_voices:
        errors.append(
            f"E_VALIDATE_MANIFEST voice count {trip_voices} exceeds maxVoicePerTrip {max_voices} (VR-L08)"
        )

    max_videos_per_ch = int(limits.get("maxVideosPerChapter", 1))

    cover = trip.get("coverAssetId")
    if cover and cover not in assets and status not in ("draft_ingest",):
        errors.append(f"E_VALIDATE_REF coverAssetId missing: {cover}")
    elif cover and cover in assets and assets[cover].get("type") == "video":
        errors.append("E_VALIDATE_MANIFEST cover cannot be video (VR-M01)")

    errors.extend(_validate_moment_refs(trip, assets))

    chapters = trip.get("chapters", [])
    min_c = limits.get("minChapters", 3)
    max_c = limits.get("maxChapters", 5)
    if status not in ("draft_ingest",) and chapters:
        if not (min_c <= len(chapters) <= max_c):
            errors.append(f"E_VALIDATE_MANIFEST chapter count {len(chapters)} not in [{min_c},{max_c}]")
    elif status not in ("draft_ingest", "ingest_ready") and not chapters:
        errors.append("E_VALIDATE_MANIFEST chapters required after curate")

    card_asset_ids: list[str] = []
    has_moment_voice = False

    for i, ch in enumerate(chapters):
        idx = ch.get("index", i + 1)
        pid = ch.get("patternId", "")
        title_max = limits.get("chapterTitleMaxChars", 12)
        if (ch.get("curation") or {}).get("isAppendix"):
            title_max = max(int(title_max), 16)
        if char_len(ch.get("title", "")) > title_max:
            errors.append(f"E_VALIDATE_LIMIT chapters[{i}].title too long")
        is_appendix = bool((ch.get("curation") or {}).get("isAppendix"))
        if idx == 1 and pid != "open":
            errors.append("E_VALIDATE_MANIFEST first chapter must be open (VR-P02)")
        # VR-P03 · last content chapter (附录不计) must be close
        content_chapters = [
            c for c in chapters if not (c.get("curation") or {}).get("isAppendix")
        ]
        if (
            content_chapters
            and ch is content_chapters[-1]
            and not is_appendix
            and pid != "close"
        ):
            errors.append("E_VALIDATE_MANIFEST last chapter must be close (VR-P03)")

        items = ch.get("items", [])
        if pid == "moment" and chapter_visual_units(ch) < 2:
            errors.append(
                "E_VALIDATE_MANIFEST moment chapter needs >=2 visual units "
                "(media-card/row/scroll or layout-screen) (VR-P05)"
            )

        ch_videos = [
            aid
            for aid in chapter_asset_ids(ch)
            if aid in assets and assets[aid].get("type") == "video"
        ]
        if len(ch_videos) > max_videos_per_ch:
            errors.append(
                f"E_VALIDATE_MANIFEST chapters[{i}] video count {len(ch_videos)} "
                f"exceeds maxVideosPerChapter {max_videos_per_ch} (VR-M03)"
            )

        for it in items:
            if it.get("type") == "media-card":
                aid = it.get("assetId")
                if aid not in assets:
                    errors.append(f"E_VALIDATE_REF unknown assetId {aid}")
                else:
                    card_asset_ids.append(aid)
                    a = assets[aid]
                    if idx == 1 and a.get("type") == "video":
                        errors.append("E_VALIDATE_MANIFEST video in first chapter (VR-M02)")
                    if a.get("type") == "video" and a.get("hasAudio") and a.get("voice"):
                        errors.append("E_VALIDATE_MANIFEST video+audio cannot have voice (VR-M04)")
                    if a.get("voice") and pid == "moment":
                        has_moment_voice = True
                cap = it.get("caption") or ""
                if char_len(cap) > limits.get("captionMaxChars", 60):
                    errors.append(f"E_VALIDATE_LIMIT caption too long on {aid}")
                slot = (it.get("layout") or {}).get("slot")
                if slot and slot not in CARD_SLOTS:
                    errors.append(f"E_VALIDATE_LAYOUT unknown layout.slot {slot!r}")

            elif it.get("type") == "media-row":
                rl = it.get("rowLayout")
                if not rl:
                    errors.append("E_VALIDATE_LAYOUT media-row missing rowLayout (VR-L01)")
                elif rl not in ROW_LAYOUTS:
                    errors.append(f"E_VALIDATE_LAYOUT unknown rowLayout {rl!r}")
                else:
                    aids = it.get("assetIds") or []
                    expected = ROW_LAYOUT_COUNTS.get(rl)
                    if expected and len(aids) != expected:
                        errors.append(
                            f"E_VALIDATE_LAYOUT rowLayout {rl} expects {expected} assets, got {len(aids)}"
                        )
                for aid in it.get("assetIds") or []:
                    if aid not in assets:
                        errors.append(f"E_VALIDATE_REF unknown assetId {aid}")

            elif it.get("type") == "media-scroll":
                aids = it.get("assetIds") or []
                if pid == "gallery" and (len(aids) < 3 or len(aids) > 5):
                    errors.append(
                        f"E_VALIDATE_MANIFEST gallery media-scroll needs 3–5 assets, got {len(aids)} (VR-P04)"
                    )
                for aid in aids:
                    if aid not in assets:
                        errors.append(f"E_VALIDATE_REF unknown assetId {aid}")

    for aid, a in assets.items():
        kind = a.get("aspectKind")
        if kind is not None and kind not in ASPECT_KINDS:
            errors.append(f"E_VALIDATE_LAYOUT asset {aid} invalid aspectKind {kind!r}")

    if len(card_asset_ids) != len(set(card_asset_ids)):
        errors.append("E_VALIDATE_MANIFEST duplicate asset in media-card (VR-R03)")

    if trip_voices and not has_moment_voice:
        errors.append("E_VALIDATE_MANIFEST voice exists but no moment chapter with voice (VR-M05)")

    locks = pipe.get("locks", {})
    if status == "structure_locked" and not locks.get("structure"):
        errors.append("E_VALIDATE_MANIFEST structure_locked but locks.structure false (VR-S01)")
    if status == "copy_locked" and not locks.get("copy"):
        errors.append("E_VALIDATE_MANIFEST copy_locked but locks.copy false (VR-S02)")

    from travelogue.services.narrative_validate import validate_narrative

    errors.extend(validate_narrative(trip))

    return errors


def validate_trip(
    trip: dict,
    *,
    level: str = "all",
    schema_path: Path | None = None,
    manifest_path: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    if level in ("schema", "all"):
        errors.extend(validate_schema(trip, schema_path))
    if level in ("manifest", "all"):
        if manifest_path is None:
            from travelogue.paths import manifest_path_for
            from travelogue.templating.resolver import resolve_effective_template

            manifest_path = manifest_path_for(resolve_effective_template(trip))
        manifest = load_json(manifest_path or MANIFEST_PATH)
        errors.extend(validate_manifest(trip, manifest))
    if level in ("l3", "all"):
        from travelogue.templating.l3_validate import validate_template_capabilities

        errors.extend(validate_template_capabilities(trip))
    return errors
