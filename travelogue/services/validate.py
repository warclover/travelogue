"""L1 schema + L2 manifest validation."""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.paths import MANIFEST_PATH, SCHEMA_PATH


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
        if char_len(ch.get("title", "")) > limits.get("chapterTitleMaxChars", 12):
            errors.append(f"E_VALIDATE_LIMIT chapters[{i}].title too long")
        if idx == 1 and pid != "open":
            errors.append("E_VALIDATE_MANIFEST first chapter must be open (VR-P02)")
        if idx == len(chapters) and pid != "close":
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
            from travelogue.templating.resolver import resolve_effective_template
            from travelogue.paths import manifest_path_for

            manifest_path = manifest_path_for(resolve_effective_template(trip))
        manifest = load_json(manifest_path or MANIFEST_PATH)
        errors.extend(validate_manifest(trip, manifest))
    if level in ("l3", "all"):
        from travelogue.templating.l3_validate import validate_template_capabilities

        errors.extend(validate_template_capabilities(trip))
    return errors
