"""Agent 2 · Storyteller — rule-based copy stub (no LLM)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from travelogue.config import AppConfig
from travelogue.paths import MANIFEST_PATH
from travelogue.services.copy_subject import (
    is_generic_place,
    narrative_copy_subject,
    user_place_explicit,
)
from travelogue.util.datetime_ import utc_now_iso as _utc_now_iso

# F-NAR-05 · manifest limits (F-NAR-01)
HOOK_MAX = 56
LEAD_MAX = 80
EPILOGUE_MAX = 80

BANNED_PHRASES: tuple[str, ...] = (
    "综上所述",
    "值得一提的是",
    "不可否认",
    "众所周知",
    "总而言之",
    "换句话说",
    "美不胜收",
    "令人难忘",
)

GENERIC_COPY_WORDS: tuple[str, ...] = (
    "值得",
    "难忘",
    "美好",
    "精彩",
    "瞬间",
    "回忆",
    "旅程",
    "风景",
    "记录",
)


@lru_cache(maxsize=1)
def _manifest_limits() -> dict[str, int]:
    if not MANIFEST_PATH.is_file():
        return {
            "hookMaxChars": HOOK_MAX,
            "chapterLeadMaxChars": LEAD_MAX,
            "epilogueMaxChars": EPILOGUE_MAX,
            "captionMaxChars": 60,
        }
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    lim = data.get("limits") or {}
    return {
        "hookMaxChars": int(lim.get("hookMaxChars", HOOK_MAX)),
        "chapterLeadMaxChars": int(lim.get("chapterLeadMaxChars", LEAD_MAX)),
        "epilogueMaxChars": int(lim.get("epilogueMaxChars", EPILOGUE_MAX)),
        "captionMaxChars": int(lim.get("captionMaxChars", 60)),
    }


def _strip_banned(text: str) -> str:
    out = text
    for phrase in BANNED_PHRASES:
        out = out.replace(phrase, "")
    for word in GENERIC_COPY_WORDS:
        out = out.replace(word, "")
    return re.sub(r"\s{2,}", " ", out).strip()


def _finalize_copy(text: str, max_chars: int, *, seen: set[str] | None = None) -> str:
    """Clamp length, drop banned phrases, optional de-dupe within a narrate run."""
    t = _strip_banned((text or "").strip())
    if not t:
        return ""
    if seen is not None:
        base = t[:max_chars]
        candidate = base
        n = 2
        while candidate in seen:
            suffix = f"·{n}"
            candidate = (base[: max(0, max_chars - len(suffix))] + suffix)[:max_chars]
            n += 1
        seen.add(candidate)
        return candidate
    return t[:max_chars]


from travelogue.services.errors import NarrateError  # re-exported for CLI/tests


@dataclass
class NarrateResult:
    fields_updated: list[str]


def _parse_iso_date(raw: str) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None


def _format_date_span(start: str, end: str) -> str:
    ds, de = _parse_iso_date(start), _parse_iso_date(end)
    if ds and de and ds.date() != de.date():
        if ds.year == de.year and ds.month == de.month:
            return f"{ds.month}月{ds.day}日到{de.day}日"
        if ds.year == de.year:
            return f"{ds.month}月{ds.day}日到{de.month}月{de.day}日"
        return f"{ds.year}年{ds.month}月{ds.day}日"
    if ds:
        return f"{ds.month}月{ds.day}日"
    return ""


def _chapter_asset_ids(chapter: dict) -> list[str]:
    ids: list[str] = []
    for item in chapter.get("items") or []:
        if item.get("type") == "media-card" and item.get("assetId"):
            ids.append(item["assetId"])
    return ids


def _chapter_places(chapter: dict, assets: dict[str, dict]) -> list[str]:
    places: list[str] = []
    cur = (chapter.get("curation") or {}).get("places") or []
    for p in cur:
        if p and p not in places:
            places.append(p)
    for aid in _chapter_asset_ids(chapter):
        city = ((assets.get(aid) or {}).get("place") or {}).get("city")
        if city and city not in places:
            places.append(city)
    return places


def _voice_excerpt(chapter: dict, assets: dict[str, dict]) -> str:
    for aid in _chapter_asset_ids(chapter):
        voice = (assets.get(aid) or {}).get("voice") or {}
        preview = (voice.get("transcriptPreview") or voice.get("transcript") or "").strip()
        if preview:
            return preview[:40]
    return ""


def _format_asset_date(raw: str) -> str:
    dt = _parse_iso_date(raw)
    if not dt:
        return ""
    return f"{dt.month}月{dt.day}日"


def _trip_day_count(meta: dict) -> int:
    ds = _parse_iso_date(meta.get("dateStart", ""))
    de = _parse_iso_date(meta.get("dateEnd", ""))
    if ds and de:
        return max(1, (de.date() - ds.date()).days + 1)
    return 1


def _pick_template(templates: list[str], seed: str) -> str:
    if not templates:
        return ""
    idx = sum(ord(c) for c in seed) % len(templates)
    return templates[idx]


STUB_CAPTION_TEMPLATES: dict[str, tuple[str, ...]] = {
    "portrait": ("{place}的竖幅。", "抬头看见{place}。", "{date}的{place}。"),
    "landscape": ("{place}的远景。", "横展开的{place}。", "{date}留在{place}。"),
    "panorama": ("{place}徐徐展开。", "宽幅里的{place}。", "全景里的{place}。"),
    "square": ("{place}的一格。", "方框里的{place}。", "{date}·{place}。"),
    "tall": ("{place}的竖长一张。", "向上延伸的{place}。", "{date}的{place}。"),
    "default": ("{place}的一张。", "旅途里的一张。", "{date}的{place}。"),
}


def _caption_place_for_asset(
    asset: dict,
    *,
    default_place: str,
    meta: dict | None = None,
    intent: dict | None = None,
    assets: list[dict] | None = None,
) -> str:
    from travelogue.services.copy_subject import suppress_chapter_geo_places

    if meta is not None and suppress_chapter_geo_places(meta, intent=intent, assets=assets):
        return default_place or "这里"
    city = ((asset.get("place") or {}).get("city") or "").strip()
    return city or default_place or "这里"


def _build_stub_caption(
    asset: dict,
    *,
    default_place: str,
    meta: dict | None = None,
    intent: dict | None = None,
    assets: list[dict] | None = None,
) -> str:
    place = _caption_place_for_asset(
        asset,
        default_place=default_place,
        meta=meta,
        intent=intent,
        assets=assets,
    )
    date = _format_asset_date(str(asset.get("takenAt") or ""))
    kind = str(asset.get("aspectKind") or "default")
    templates = STUB_CAPTION_TEMPLATES.get(kind) or STUB_CAPTION_TEMPLATES["default"]
    template = _pick_template(list(templates), str(asset.get("id") or place))
    return template.format(place=place, date=date or "这一天").strip()


def _stub_caption_asset_ids(trip: dict) -> list[str]:
    from travelogue.curation.asset_caption import chapter_caption_asset_ids

    ids: list[str] = []
    cover = trip.get("coverAssetId")
    if cover:
        ids.append(str(cover))
    for ch in trip.get("chapters") or []:
        for aid in chapter_caption_asset_ids(ch)[:2]:
            if aid not in ids:
                ids.append(aid)
    return ids


def _apply_stub_captions(
    trip: dict,
    *,
    default_place: str,
    regenerate: bool = False,
    dry_run: bool = False,
    max_chars: int = 60,
    meta: dict | None = None,
    intent: dict | None = None,
) -> list[str]:
    from travelogue.curation.asset_caption import (
        apply_caption_to_trip,
        find_item_for_asset,
        resolve_caption,
    )

    meta = meta if meta is not None else trip.get("meta") or {}
    intent = intent if intent is not None else trip.get("intent")
    asset_list = trip.get("assets") or []
    assets = {a["id"]: a for a in asset_list if a.get("id")}
    updated: list[str] = []
    for aid in _stub_caption_asset_ids(trip):
        asset = assets.get(aid)
        if not asset or asset.get("edited") or asset.get("skipCaption"):
            continue
        has_caption = False
        for ch in trip.get("chapters") or []:
            item = find_item_for_asset(ch, aid)
            if item and item.get("edited"):
                has_caption = True
                break
        if has_caption:
            continue
        if not regenerate and resolve_caption(None, asset).strip():
            continue
        caption = _finalize_copy(
            _build_stub_caption(
                asset,
                default_place=default_place,
                meta=meta,
                intent=intent,
                assets=asset_list,
            ),
            max_chars,
        )
        if not caption:
            continue
        if not dry_run:
            apply_caption_to_trip(trip, aid, caption)
        updated.append(f"assets.{aid}.caption")
    return updated


def _build_hook(
    meta: dict,
    *,
    photo_count: int,
    tone: str,
    intent: dict | None = None,
    assets: list[dict] | None = None,
) -> str:
    place = narrative_copy_subject(meta, intent=intent, assets=assets)
    title = meta.get("title") or "旅途"
    span = _format_date_span(meta.get("dateStart", ""), meta.get("dateEnd", ""))

    if tone == "documentary":
        if span and photo_count:
            return f"{place}，{span}，{photo_count} 张照片。"
        if span:
            return f"{place}，{span}。"
        return f"{title} · {place}。"

    day_count = _trip_day_count(meta)
    # W2 Copy · 读者向 stub（去「碎片 / 帧」工程口吻）
    templates = [
        f"在{place}的{day_count}天，{photo_count} 张照片汇成这一页。",
        f"{place}·{span or f'{day_count}天'}，慢慢翻。",
        f"走进{place}，{photo_count} 张照片留在这里。",
        f"{title} · 关于{place}的{day_count}天。",
    ]
    if span and photo_count:
        templates.append(f"在{place}的{span}，{photo_count} 张照片汇成这一页。")
    seed = str(title or place)
    return _pick_template(templates, seed)


def _chapter_day_label(chapter: dict, assets: dict[str, dict]) -> str:
    dates: list[datetime] = []
    for aid in _chapter_asset_ids(chapter):
        raw = (assets.get(aid) or {}).get("takenAt") or ""
        dt = _parse_iso_date(str(raw))
        if dt:
            dates.append(dt)
    if dates:
        earliest = min(dates)
        return f"{earliest.month}月{earliest.day}日"
    title = (chapter.get("title") or "").strip()
    if title and "月" in title and "日" in title:
        return title
    return ""


def _build_lead_frame(chapter_index: int, day_label: str, place: str) -> str:
    parts = [f"第{chapter_index}天"]
    if day_label:
        parts.append(day_label)
    if place:
        parts.append(place)
    return " · ".join(parts) + "。"


def _build_lead(
    chapter: dict,
    *,
    meta: dict,
    intent: dict | None = None,
    assets: dict[str, dict],
    default_place: str,
    tone: str,
    chapter_index: int,
    chapter_total: int,
) -> str:
    title = (chapter.get("title") or "").strip()
    from travelogue.services.copy_subject import suppress_chapter_geo_places

    places = _chapter_places(chapter, assets)
    asset_list = list(assets.values())
    if suppress_chapter_geo_places(meta, intent=intent, assets=asset_list):
        place = default_place
    elif places and user_place_explicit(meta, intent=intent):
        place = places[0]
    elif places and is_generic_place((meta.get("places") or ["旅途"])[0]):
        place = default_place
    else:
        place = places[0] if places else default_place
    n = len(_chapter_asset_ids(chapter))
    voice = _voice_excerpt(chapter, assets)

    if voice and tone != "documentary":
        lead = f"「{voice}」——{title or place}。" if title else f"「{voice}」"
        return lead

    if tone != "documentary":
        day_label = _chapter_day_label(chapter, assets)
        place_str = place or title or default_place
        return _build_lead_frame(chapter_index, day_label, place_str)

    if chapter_index == 1:
        if tone == "documentary":
            return f"开篇 · {title or place}，{n} 张。"
        return f"从{title or '这里'}开始，{place}比想象中安静。"

    if chapter_index >= chapter_total and chapter_total > 1:
        if tone == "documentary":
            return f"收尾 · {title or place}。"
        return f"快到尾声，{title or place}还留着余温。"

    if tone == "documentary":
        return f"{title or place}，{n} 张。"
    subject = place or title or "这一段"
    if n >= 2:
        return f"{subject}这一段，{n} 张慢慢铺开。"
    return f"{subject}，再走一步。"


def _build_epilogue(
    meta: dict,
    *,
    tone: str,
    intent: dict | None = None,
    assets: list[dict] | None = None,
) -> str:
    place = narrative_copy_subject(meta, intent=intent, assets=assets)
    if tone == "documentary":
        return f"把{place}收进这一本。"
    return f"下次再见，{place}。"


def run_narrate(
    trip: dict,
    *,
    tone: str | None = None,
    dry_run: bool = False,
    provider: str | None = None,
    regenerate: bool = False,
    cache_dir: Path | None = None,
    chapter_id: str | None = None,
    scope: str | None = None,
    cfg: AppConfig | None = None,
) -> NarrateResult:
    """Fill meta.hook, chapter leads, captions, epilogue (stub or LLM)."""
    from travelogue.config import get_config
    from travelogue.services.llm_narrate import run_llm_narrate
    from travelogue.services.narrative_scope import (
        apply_scope_cleanup,
        assert_chapter_narrate_allowed,
        resolve_narrative_scope,
    )

    app_cfg = cfg or get_config()
    scope_val = resolve_narrative_scope(override=scope, cfg=app_cfg)
    if not dry_run:
        apply_scope_cleanup(trip, scope_val)
        curation = trip.setdefault("curation", {})
        curation["narrativeScope"] = scope_val

    prov = (provider or app_cfg.llm.provider or "stub").strip().lower()
    if prov not in ("stub", "deepseek", "dashscope"):
        raise NarrateError("E_NARRATE_PROVIDER", f"unknown provider {prov!r}")
    if chapter_id:
        from travelogue.services.llm_narrate import _chapter_indices, _planned_fields

        _chapter_indices(trip, chapter_id)
        assert_chapter_narrate_allowed(trip, chapter_id, scope_val)
    if chapter_id and prov == "stub":
        if dry_run:
            return NarrateResult(
                fields_updated=_planned_fields(
                    trip,
                    regenerate=regenerate,
                    chapter_id=chapter_id,
                    scope=scope_val,
                    cfg=app_cfg,
                )
            )
    if not app_cfg.narrative.copy_generation_enabled:
        return NarrateResult(fields_updated=[])
    if prov == "stub":
        result = _run_narrate_stub(
            trip,
            tone=tone,
            dry_run=dry_run,
            regenerate=regenerate,
            scope=scope_val,
            cfg=app_cfg,
        )
        return result
    result = run_llm_narrate(
        trip,
        provider=prov,
        tone=tone,
        dry_run=dry_run,
        regenerate=regenerate,
        cache_dir=cache_dir,
        chapter_id=chapter_id,
        scope=scope_val,
        cfg=app_cfg,
    )
    if not dry_run:
        from travelogue.services.decor_line import apply_decor_lines

        decor_updates = apply_decor_lines(
            trip,
            regenerate=regenerate,
            chapter_id=chapter_id,
            cfg=app_cfg,
        )
        if decor_updates:
            result.fields_updated.extend(decor_updates)
    return result


def _run_narrate_stub(
    trip: dict,
    *,
    tone: str | None = None,
    dry_run: bool = False,
    regenerate: bool = False,
    scope: str = "frame",
    cfg: AppConfig | None = None,
) -> NarrateResult:
    """Rule-based hook and chapter leads (no LLM)."""
    from travelogue.services.narrative_scope import chapter_lead_allowed

    meta = trip.setdefault("meta", {})
    if tone:
        meta["tone"] = tone if tone in ("relaxed", "documentary") else meta.get("tone", "relaxed")

    updated: list[str] = []
    intent = trip.get("intent")
    asset_list = trip.get("assets") or []
    place = narrative_copy_subject(meta, intent=intent, assets=asset_list)
    tone_val = meta.get("tone") or "relaxed"
    assets = {a["id"]: a for a in asset_list}
    photo_count = sum(1 for a in assets.values() if a.get("type", "image") == "image")
    chapters = trip.get("chapters") or []
    chapter_total = len(chapters)

    lead_seen: set[str] = set()

    lim = _manifest_limits()

    if not meta.get("edited") and (regenerate or not (meta.get("hook") or "").strip()):
        if not dry_run:
            meta["hook"] = _finalize_copy(
                _build_hook(
                    meta,
                    photo_count=photo_count,
                    tone=tone_val,
                    intent=intent,
                    assets=asset_list,
                ),
                lim["hookMaxChars"],
            )
        updated.append("meta.hook")

    from travelogue.services.decor_line import apply_decor_lines

    updated.extend(
        apply_decor_lines(
            trip,
            regenerate=regenerate,
            dry_run=dry_run,
            cfg=cfg,
        )
    )

    for ch in chapters:
        if ch.get("edited"):
            continue
        if not chapter_lead_allowed(ch, chapters, scope):
            continue
        if not regenerate and (ch.get("lead") or "").strip():
            continue
        idx = int(ch.get("index") or 0)
        if not dry_run:
            ch["lead"] = _finalize_copy(
                _build_lead(
                    ch,
                    meta=meta,
                    intent=intent,
                    assets=assets,
                    default_place=place,
                    tone=tone_val,
                    chapter_index=idx,
                    chapter_total=chapter_total,
                ),
                lim["chapterLeadMaxChars"],
                seen=lead_seen,
            )
        updated.append(f"chapters[{ch.get('index')}].lead")

    if chapter_total >= 2 and (regenerate or not (trip.get("epilogue") or "").strip()):
        if not dry_run:
            trip["epilogue"] = _finalize_copy(
                _build_epilogue(meta, tone=tone_val, intent=intent, assets=asset_list),
                lim["epilogueMaxChars"],
            )
        updated.append("epilogue")

    caption_updates = _apply_stub_captions(
        trip,
        default_place=place,
        regenerate=regenerate,
        dry_run=dry_run,
        max_chars=lim["captionMaxChars"],
        meta=meta,
        intent=intent,
    )
    updated.extend(caption_updates)

    if dry_run:
        return NarrateResult(fields_updated=updated)

    from travelogue.services.pipeline_state import append_pipeline_run, set_pipeline_status

    set_pipeline_status(trip, "copy_draft")
    append_pipeline_run(
        trip,
        {
            "runId": f"narrate-{_utc_now_iso()}",
            "agent": "storyteller",
            "startedAt": _utc_now_iso(),
            "finishedAt": _utc_now_iso(),
            "model": "rule-stub",
        },
    )
    trip["updatedAt"] = _utc_now_iso()
    return NarrateResult(fields_updated=updated)
