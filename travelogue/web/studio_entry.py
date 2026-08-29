"""Preview entry deep-link payload (Phase 4 M16 · F-P4-PRV-06).

GET /__travelogue/trips/{tripId}/entry returns a small, read-only payload that
lets the success overlay open the preview at a "peak" screen instead of the
cover. Pure functions over trip.json; never mutates the trip.
"""

from __future__ import annotations

from typing import Any

from travelogue.cover_engine import resolve_cover_opening_style, studio_style_options
from travelogue.cover_engine.craft import HERO_SET, is_hero_style
from travelogue.cover_engine.registry import get_style
from travelogue.cover_engine.resolve import legacy_map
from travelogue.config.cover_craft import CRAFT_ATTR_VALUE, is_cover_craft_enabled
from travelogue.services.decor_line import chapter_has_voice
from travelogue.templating.summary import build_template_summary
from travelogue.web.studio_aesthetic import build_aesthetic_entry_summary
from travelogue.web.studio_constants import STUDIO_USER_NOTES_MAX_LEN
from travelogue.web.studio_telemetry import build_pipeline_telemetry_summary


def _cover_craft_entry(resolved_style: str, style_rec: Any) -> dict[str, Any]:
    """CCF payload for Studio cover style controls (FE-CCF-*)."""
    enabled = is_cover_craft_enabled()
    options = studio_style_options()
    option_ids = {str(o.get("id") or "") for o in options}
    in_options = resolved_style in option_ids
    legacy = bool(enabled and resolved_style and not in_options)
    label = ""
    if style_rec is not None:
        label = str(style_rec.studio_label or style_rec.label or resolved_style)
    elif resolved_style:
        label = resolved_style
    return {
        "enabled": enabled,
        "version": CRAFT_ATTR_VALUE if enabled else None,
        "heroSet": list(HERO_SET),
        "legacyCurrent": legacy,
        "legacyStyleId": resolved_style if legacy else None,
        "legacyLabel": label if legacy else None,
        "legacyHint": (
            f"当前为经典版式「{label}」，可切换到现行三款。"
            if legacy and label
            else None
        ),
        "isHeroStyle": is_hero_style(resolved_style),
    }


def _ordered_screens(trip: dict) -> list[tuple[str, list[str], str | None]]:
    """All (screenId, assetIds, arcSegment) across chapters in document order."""
    screens: list[tuple[str, list[str], str | None]] = []
    for chapter in trip.get("chapters") or []:
        for screen in chapter.get("screens") or []:
            sid = screen.get("screenId")
            if not sid:
                continue
            aids = [
                slot.get("assetId")
                for slot in (screen.get("slots") or [])
                if slot.get("assetId")
            ]
            arc = screen.get("arcSegment")
            arc_str = str(arc) if arc else None
            screens.append((str(sid), aids, arc_str))
    return screens


def _peak_screen_score(screen: dict) -> float:
    slots = screen.get("slots") or []
    aids = [s.get("assetId") for s in slots if s.get("assetId")]
    score = 1.0
    if len(aids) <= 1:
        score += 0.5
    return score


def resolve_peak_screen_id(trip: dict) -> str | None:
    """Peak screen for the preview deep link (PRD-PHASE4 §8.5 fallback chain).

    Guaranteed non-None when any screen exists:
      1. best-scored screen with arcSegment == \"peak\" and assets
      2. first screen with arcSegment == \"peak\"
      3. largest scene cluster -> first matching screen
      4. first content screen (has >=1 asset slot)
      5. first screen
    """
    screens = _ordered_screens(trip)
    if not screens:
        return None

    best_sid: str | None = None
    best_score = float("-inf")
    screen_by_id: dict[str, dict] = {}
    for chapter in trip.get("chapters") or []:
        for screen in chapter.get("screens") or []:
            sid = screen.get("screenId")
            if sid:
                screen_by_id[str(sid)] = screen

    for sid, aids, arc in screens:
        if arc == "peak" and aids:
            score = _peak_screen_score(screen_by_id.get(sid, {}))
            if score > best_score:
                best_score = score
                best_sid = sid
            elif score == best_score and best_sid is not None:
                best_sid = sid
    if best_sid:
        return best_sid

    for sid, _aids, arc in screens:
        if arc == "peak":
            return sid

    clustering = (trip.get("curation") or {}).get("clustering") or {}
    clusters = clustering.get("clusters") or []
    if clusters:
        largest = max(clusters, key=lambda c: len(c.get("assetIds") or []))
        cluster_aids = {str(a) for a in (largest.get("assetIds") or [])}
        if cluster_aids:
            for sid, aids, _arc in screens:
                if any(str(a) in cluster_aids for a in aids):
                    return sid

    for sid, aids, _arc in screens:
        if aids:
            return sid

    return screens[0][0]


def build_intent_summary(trip: dict) -> dict[str, Any]:
    """Compact intent summary for the entry payload."""
    intent = trip.get("intent") or {}
    meta = trip.get("meta") or {}
    title = str(intent.get("title") or meta.get("title") or "我的旅途").strip()[:20]
    # PMX D3 · 展示名与编辑 SSOT 分列；封面 DOM 只绑 displayTitle
    from travelogue.domain.title_humanize import resolve_display_title
    display_title = resolve_display_title(meta if isinstance(meta, dict) else {})
    assets = trip.get("assets") or []
    featured = sum(1 for a in assets if a.get("userTier") == "featured")
    clustering = (trip.get("curation") or {}).get("clustering") or {}
    segments = clustering.get("segments") or []
    user_notes = str(intent.get("userNotes") or trip.get("userNotes") or "").strip()
    subjects = intent.get("featuredSubjects") or []
    cohort = (trip.get("curation") or {}).get("cohort") or {}
    return {
        "title": title or "我的旅途",
        "displayTitle": display_title or title or "我的旅途",
        "featuredCount": featured,
        "segmentCount": len(segments),
        "hasUserNotes": bool(user_notes),
        "userNotes": user_notes[:STUDIO_USER_NOTES_MAX_LEN] if user_notes else "",
        "featuredSubjectCount": len(subjects) if isinstance(subjects, list) else 0,
        "cohortDuoCount": int(cohort.get("duoCount") or 0) if cohort else 0,
    }


def build_title_art_ui(trip: dict) -> dict[str, Any]:
    """SAS · AI Sheet 装帧标题状态（读 ``meta.titleArt``，无工程名）。"""
    meta = trip.get("meta") if isinstance(trip.get("meta"), dict) else {}
    ta = meta.get("titleArt") if isinstance(meta.get("titleArt"), dict) else None
    if not ta or not ta.get("enabled"):
        return {
            "ready": False,
            "stale": False,
            "engine": None,
            "statusLabel": "尚未生成",
        }
    engine = str(ta.get("engine") or "").strip()
    engine_label = (
        "AI 手写体" if engine == "diffusion-fixed-prompt-v1" else "字库合成"
    )
    stale = bool(ta.get("stale"))
    if stale:
        status = f"已过期 · {engine_label}"
    else:
        status = f"已生成 · {engine_label}"
        if ta.get("fallbackFrom"):
            status += "（已回退字库）"
    return {
        "ready": True,
        "stale": stale,
        "engine": engine or None,
        "statusLabel": status,
    }


def build_intent_brief_ui(trip: dict) -> dict[str, Any]:
    """SAS W2 · user-facing Intent Brief chip (no Agent / raw JSON names)."""
    intent = trip.get("intent") if isinstance(trip.get("intent"), dict) else {}
    brief = intent.get("intentBrief") if isinstance(intent.get("intentBrief"), dict) else None
    if not brief:
        return {
            "ready": False,
            "statusLabel": "尚未解析",
            "detail": "",
            "source": None,
        }
    source = str(brief.get("source") or "").strip() or None
    bits: list[str] = []
    if source in ("llm", "cache"):
        bits.append("已就绪")
    elif source == "fallback":
        bits.append("本机兜底")
    else:
        bits.append("已有摘要")
    cluster = brief.get("clusterHints") if isinstance(brief.get("clusterHints"), dict) else {}
    if cluster.get("preferFewerChapters") is True:
        bits.append("偏少章")
    elif cluster.get("preferFewerChapters") is False:
        bits.append("可多分章")
    detail_parts: list[str] = []
    tone = str(brief.get("tone") or "").strip()
    if tone:
        detail_parts.append(tone[:20])
    title_hint = str(brief.get("titleHint") or "").strip()
    if title_hint:
        detail_parts.append(title_hint[:20])
    return {
        "ready": True,
        "statusLabel": " · ".join(bits[:2]) or "已有摘要",
        "detail": " · ".join(detail_parts)[:48],
        "source": source if source in ("llm", "cache", "fallback") else None,
    }


def _chapter_date_label(curation: dict) -> str:
    """SNR F2 · 章眉副信息：daySpan →「M月D日」或跨度，主标题可让位地点/场景。"""
    span = [str(d)[:10] for d in (curation.get("daySpan") or []) if d]
    if not span:
        return ""
    try:
        from datetime import date

        d0 = date.fromisoformat(span[0])
        if len(span) == 1:
            return f"{d0.month}月{d0.day}日"
        d1 = date.fromisoformat(span[-1])
        if d0 == d1:
            return f"{d0.month}月{d0.day}日"
        if d0.month == d1.month and d0.year == d1.year:
            return f"{d0.month}月{d0.day}–{d1.day}日"
        return f"{d0.month}月{d0.day}日–{d1.month}月{d1.day}日"
    except ValueError:
        return ""


def build_chapter_summaries(trip: dict) -> list[dict[str, Any]]:
    """Chapter id/title/anchors for preview edit drawer."""
    rows: list[dict[str, Any]] = []
    for ch in trip.get("chapters") or []:
        ch_id = ch.get("id")
        if not ch_id:
            continue
        curation = ch.get("curation") or {}
        title_cap = 16 if curation.get("isAppendix") else 12
        appendix_ids = [str(a) for a in (curation.get("appendixAssetIds") or []) if a]
        title = str(ch.get("title") or ch_id)[:title_cap]
        date_label = _chapter_date_label(curation if isinstance(curation, dict) else {})
        # 主标题已含日期时不重复副信息
        if date_label and date_label.replace("–", "")[:4] in title.replace("–", ""):
            date_label = ""
        rows.append(
            {
                "id": str(ch_id),
                "title": title,
                "dateLabel": date_label,
                "memoryAnchors": list(curation.get("memoryAnchors") or [])[:3],
                "copyIntent": dict(curation.get("copyIntent") or {}),
                "hasVoice": chapter_has_voice(ch, trip),
                "isAppendix": bool(curation.get("isAppendix")),
                "appendixReason": str(curation.get("appendixReason") or ""),
                "appendixCount": len(appendix_ids),
                "appendixAssetIds": appendix_ids,
            }
        )
    return rows


def build_asset_media_index(trip: dict) -> dict[str, str]:
    """assetId → mediaClass for Studio collage override (PRD §3.4)."""
    out: dict[str, str] = {}
    for asset in trip.get("assets") or []:
        aid = asset.get("id")
        if aid:
            out[str(aid)] = str(asset.get("mediaClass") or "photo")
    return out


def build_entry(
    trip: dict,
    trip_id: str,
    *,
    aesthetic_enabled: bool = True,
    trip_dir: Any = None,
    ai_surface_enabled: bool | None = None,
    llm_ready: bool | None = None,
) -> dict[str, Any]:
    """Assemble the entry payload (previewUrl, peakScreenId, intentSummary)."""
    peak = resolve_peak_screen_id(trip)
    preview_url = f"/{trip_id}/index.html"
    scroll_share_url = f"{preview_url}?share=1"
    if peak:
        preview_url = f"{preview_url}#screen-{peak}"
        scroll_share_url = f"{scroll_share_url}#screen-{peak}"
    pipeline = trip.get("pipeline") or {}
    telemetry = build_pipeline_telemetry_summary(trip)
    curation = trip.get("curation") or {}
    raw_style = str((trip.get("meta") or {}).get("coverOpeningStyle") or "").strip()
    resolved = resolve_cover_opening_style(trip)
    style_rec = get_style(resolved)
    explain = curation.get("coverStyleExplain") if isinstance(curation, dict) else None
    narrative_posture = _narrative_posture_entry(
        trip,
        ai_surface_enabled=ai_surface_enabled,
        llm_ready=llm_ready,
    )
    return {
        "previewUrl": preview_url,
        "scrollShareUrl": scroll_share_url,
        "peakScreenId": peak,
        "intentSummary": build_intent_summary(trip),
        "intentBriefUi": build_intent_brief_ui(trip),
        "titleArtUi": build_title_art_ui(trip),
        "pipelineStatus": pipeline.get("status"),
        "g1Pending": pipeline.get("status") == "structure_draft",
        "derivativesStatus": str(pipeline.get("derivativesStatus") or "") or None,
        "derivativesReady": pipeline.get("derivativesStatus") == "ready",
        "derivativesPreparing": int(pipeline.get("derivativesPreparing") or 0),
        "coverAssetId": str(trip.get("coverAssetId") or "") or None,
        "chapters": build_chapter_summaries(trip),
        "layoutSuggestions": _layout_suggestions_entry(curation if isinstance(curation, dict) else {}),
        "layoutFeedback": _layout_feedback_entry(curation if isinstance(curation, dict) else {}),
        "telemetry": telemetry,
        "aesthetic": build_aesthetic_entry_summary(
            trip,
            enabled=aesthetic_enabled,
            trip_dir=trip_dir,
        ),
        "template": build_template_summary(trip),
        "assetMediaById": build_asset_media_index(trip),
            "coverOpeningStyle": resolved,
        "coverOpeningStyleRaw": raw_style or None,
        "coverStyleOptions": studio_style_options(),
        "coverCraft": _cover_craft_entry(resolved, style_rec),
        "coverJointLocked": bool(curation.get("coverJointLocked")) if isinstance(curation, dict) else False,
        "coverStyleExplain": explain if isinstance(explain, dict) else None,
        "coverStyleLabel": (style_rec.studio_label or style_rec.label) if style_rec else resolved,
        "coverLegacyMapped": legacy_map(raw_style) is not None,
        "coverIsPlaceholder": (
            not bool(curation.get("coverJointLocked"))
            if isinstance(curation, dict)
            else True
        ),
        "layoutVibe": _layout_vibe_entry(trip),
        "layoutVibeOptions": _layout_vibe_options(),
        **edition_chrome(trip),
        "portfolioPipelineEnabled": _portfolio_pipeline_enabled(),
        "bookends": _bookends_entry_summary(trip, curation if isinstance(curation, dict) else {}),
        "appendixOutlierCount": len(
            (curation.get("excludedTimeOutlierAssetIds") or [])
            if isinstance(curation, dict)
            else []
        ),
        "worksBrand": _works_brand_entry(trip),
        "longshotDensity": _longshot_density_entry(trip),
        "shareCopyPack": _share_copy_pack_entry(trip),
        # SNR D-SNR-01 · 成册叙事姿态（chrome 用，不进 screen copy region）
        "narrativePosture": narrative_posture,
    }


def _layout_suggestions_entry(curation: dict) -> list[dict[str, Any]]:
    """ACP W3 · G1 secondary hints (advisory; SHD-ACP-02 length already clipped)."""
    raw = curation.get("layoutSuggestions")
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw[:16]:
        if not isinstance(item, dict):
            continue
        ch = str(item.get("chapterId") or "").strip()
        text = str(item.get("suggestion") or "").strip()
        if not ch or not text:
            continue
        out.append(
            {
                "chapterId": ch,
                "suggestedPatternId": str(item.get("suggestedPatternId") or "") or None,
                "suggestion": text[:36],
                "accepted": bool(item.get("accepted")),
                "confidence": item.get("confidence"),
            }
        )
    return out


def _layout_feedback_entry(curation: dict) -> list[dict[str, Any]]:
    raw = curation.get("layoutFeedback")
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw[:32]:
        if not isinstance(item, dict):
            continue
        ch = str(item.get("chapterId") or "").strip()
        reason = str(item.get("reason") or "").strip()
        if not ch or not reason:
            continue
        out.append(
            {
                "chapterId": ch,
                "reason": reason,
                "notedAt": item.get("notedAt"),
            }
        )
    return out


def _layout_vibe_entry(trip: dict) -> str:
    from travelogue.config.layout_vibe import resolve_layout_vibe

    return resolve_layout_vibe(trip)


def _edition_entry(trip: dict) -> str:
    from travelogue.config.edition import resolve_edition

    return resolve_edition(trip)


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _trip_folder_count(trip: dict) -> int:
    return sum(
        1
        for a in trip.get("assets") or []
        if isinstance(a, dict) and a.get("type", "image") == "image"
    )


def _leftover_is_capacity(portfolio: dict[str, Any]) -> bool:
    """True leftover = 档位装不下. False = 编排没排满 (do not push journal)."""
    overflow = portfolio.get("overflow") if isinstance(portfolio.get("overflow"), dict) else {}
    res = str(overflow.get("resolution") or portfolio.get("overflowResolution") or "")
    placed = _as_int(portfolio.get("photosPlaced"), -1)
    kept = _as_int(portfolio.get("photosKept"))
    leftover = kept - placed if placed >= 0 and kept > 0 and placed < kept else 0
    if leftover <= 0:
        return False
    cap = _as_int(overflow.get("capacity") or portfolio.get("capacity"))
    if res == "placement_gap":
        return False
    if cap > 0 and placed < cap:
        return False
    if res in {"capped", "tier_upgraded_then_capped", "tier_upgraded"}:
        return True
    return kept > cap if cap > 0 else True


def _overflow_line(portfolio: dict[str, Any] | None) -> str:
    """PFO W1 · 角标默认一句人话，不写「本册收录 P / M」。"""
    if not isinstance(portfolio, dict):
        return ""
    placed = _as_int(portfolio.get("photosPlaced"), -1)
    kept = _as_int(portfolio.get("photosKept"))
    leftover = kept - placed if placed >= 0 and kept > 0 and placed < kept else 0
    if leftover > 0:
        if _leftover_is_capacity(portfolio):
            return f"有 {leftover} 张没放进这本，要的话用游记能全收。"
        return f"编排没排满，有 {leftover} 张没放进这本。"
    folder = _as_int(portfolio.get("folderCount"))
    pages = _as_int(portfolio.get("pageCount"))
    if folder > 0 and pages > 0:
        return f"文件夹 {folder} 张，做成大约一本 {pages} 页。"
    return ""


def _overflow_detail(portfolio: dict[str, Any] | None) -> str:
    """One human ledger: 入册 / 未排. Never mix folder + kept + placed in one breath."""
    if not isinstance(portfolio, dict):
        return ""
    placed = _as_int(portfolio.get("photosPlaced"), -1)
    kept = _as_int(portfolio.get("photosKept"))
    leftover = kept - placed if placed >= 0 and kept > 0 and placed < kept else 0
    if leftover > 0 and placed >= 0:
        return f"入册 {placed} 张 · 未排 {leftover} 张"
    folder = _as_int(portfolio.get("folderCount"))
    if folder > 0 and placed >= 0:
        return f"文件夹 {folder} 张 · 入册 {placed} 张"
    if folder > 0:
        return f"文件夹 {folder} 张"
    return ""


def import_success_chrome(trip: dict) -> dict[str, Any]:
    """FirstSuccess payload: 人话规格 / 溢出，不带芯片目录。"""
    from travelogue.config.edition import EDITION_PORTFOLIO, resolve_edition

    if resolve_edition(trip) != EDITION_PORTFOLIO:
        return {}
    folio = _portfolio_counts(trip)
    return {
        "overflowLine": _overflow_line(folio) or None,
        "overflowDetail": _overflow_detail(folio) or None,
        "portfolio": folio,
    }


def _portfolio_counts(trip: dict) -> dict[str, Any]:
    studio = trip.get("studio")
    raw = studio.get("portfolio") if isinstance(studio, dict) else None
    if not isinstance(raw, dict):
        return {}
    match = raw.get("match") if isinstance(raw.get("match"), dict) else {}
    folder = raw.get("photosFolder") or match.get("folderCount")
    if not folder:
        folder = _trip_folder_count(trip) or None
    overflow = raw.get("overflow") if isinstance(raw.get("overflow"), dict) else None
    out = {
        "folderCount": folder,
        "pageCount": raw.get("pageCount"),
        "photosPlaced": raw.get("photosPlaced"),
        "photosKept": raw.get("photosKept"),
    }
    if overflow:
        out["overflow"] = {
            "count": overflow.get("count"),
            "resolution": overflow.get("resolution"),
            "capacity": overflow.get("capacity"),
        }
    return out


def edition_chrome(trip: dict) -> dict[str, Any]:
    """List + preview share this chrome: CTA, overflow, LVP visibility."""
    edition = _edition_entry(trip)
    portfolio = _portfolio_entry(trip)
    overflow = _overflow_line(portfolio)
    leftover = False
    if isinstance(portfolio, dict):
        placed = _as_int(portfolio.get("photosPlaced"), -1)
        kept = _as_int(portfolio.get("photosKept"))
        leftover = placed >= 0 and kept > 0 and placed < kept
    capacity_left = leftover and isinstance(portfolio, dict) and _leftover_is_capacity(portfolio)
    if edition == "portfolio":
        dock = {"short": "导出作品集", "aria": "导出作品集"}
    else:
        dock = {"short": "长图", "aria": "导出长图"}
    return {
        "edition": edition,
        "layoutVibeVisible": edition != "portfolio",
        "dockCta": dock,
        "overflowLine": overflow or None,
        "overflowDetail": _overflow_detail(portfolio) or None,
        "overflowCta": "改用游记（全收）" if capacity_left else None,
        "portfolio": portfolio,
    }


def _portfolio_pipeline_enabled() -> bool:
    from travelogue.config.edition import is_portfolio_pipeline_enabled
    from travelogue.config.runtime import get_config

    return is_portfolio_pipeline_enabled(get_config())


def _portfolio_entry(trip: dict) -> dict[str, Any] | None:
    from travelogue.config.edition import EDITION_PORTFOLIO, resolve_edition

    if resolve_edition(trip) != EDITION_PORTFOLIO:
        return None
    studio = trip.get("studio")
    if not isinstance(studio, dict):
        return {"overflow": None, "photosPlaced": None, "photosKept": None}
    raw = studio.get("portfolio")
    if not isinstance(raw, dict):
        return {"overflow": None, "photosPlaced": None, "photosKept": None}
    overflow = raw.get("overflow") if isinstance(raw.get("overflow"), dict) else None
    match = raw.get("match") if isinstance(raw.get("match"), dict) else {}
    from travelogue.layout_engine.editorial_series.catalog import load_official_series
    from travelogue.layout_engine.editorial_series.match import (
        catalog_chip_details,
        catalog_page_count_chips,
    )

    catalog = load_official_series()
    fulfillment = (
        raw.get("sequenceFulfillment")
        if isinstance(raw.get("sequenceFulfillment"), dict)
        else None
    )
    folder = raw.get("photosFolder") or match.get("folderCount")
    if not folder:
        folder = _trip_folder_count(trip) or None
    return {
        "seriesId": raw.get("seriesId"),
        "pageCount": raw.get("pageCount"),
        "pageCountSource": raw.get("pageCountSource") or "auto",
        "pageCountRequested": match.get("pageCountRequested"),
        "pageCountHint": match.get("pageCountHint"),
        "densityHint": match.get("densityHint"),
        "pageCountChips": catalog_page_count_chips(catalog),
        "pageCountChipDetails": catalog_chip_details(catalog),
        "photosPlaced": raw.get("photosPlaced"),
        "photosKept": raw.get("photosKept"),
        "folderCount": folder,
        "overflow": overflow,
        "sequenceFulfillment": fulfillment,
        "sparseCollection": bool(raw.get("sparseCollection")),
    }


def _layout_vibe_options() -> list[dict[str, str]]:
    from travelogue.web.studio_handlers.layout_vibe_handlers import layout_vibe_options

    return layout_vibe_options()


def _works_brand_entry(trip: dict) -> dict:
    from travelogue.domain.works_brand import resolve_works_brand

    meta = trip.get("meta") if isinstance(trip.get("meta"), dict) else {}
    resolved = resolve_works_brand(meta)
    return {
        "mode": resolved["worksBrandMode"],
        "text": str(meta.get("worksBrandText") or "").strip()[:14],
        "line": resolved["worksBrandLine"],
        "show": resolved["showWorksBrand"],
    }


def _longshot_density_entry(trip: dict) -> str:
    from travelogue.domain.longshot_density import resolve_longshot_density

    return resolve_longshot_density(trip)


def _share_copy_pack_entry(trip: dict) -> dict:
    """Xiaohongshu copy pack fields (D-SFI-14 / OQ-2 · SNR D-SNR-10)."""
    from travelogue.domain.share_copy_pack import build_share_copy_pack
    from travelogue.web.studio_narrate import studio_llm_status

    status = studio_llm_status()
    pack = build_share_copy_pack(
        trip, llm_available=bool(status.get("llmAvailable"))
    )
    return {
        "title": pack["title"],
        "body": pack["body"],
        "topics": pack["topics"],
        "level": pack.get("level") or ("L1" if pack.get("body") else "L0"),
        "hint": pack.get("hint")
        or (
            "已带入杂志文案摘要 · 可粘贴后微调"
            if pack.get("body")
            else "标题和话题已备好 · 正文可粘贴后自填"
        ),
        "llmAvailable": bool(status.get("llmAvailable")),
    }


def _narrative_posture_entry(
    trip: dict,
    *,
    ai_surface_enabled: bool | None = None,
    llm_ready: bool | None = None,
) -> str:
    """SNR · album narrativePosture for preview chrome (fail → photo_led)."""
    try:
        from travelogue.domain.narrative_posture import resolve_narrative_posture
        from travelogue.web.ai_surface import resolve_ai_surface_enabled
        from travelogue.web.studio_narrate import studio_llm_status

        if ai_surface_enabled is None:
            ai_surface_enabled = resolve_ai_surface_enabled()
        if llm_ready is None:
            llm_ready = bool(studio_llm_status().get("llmAvailable"))
        return resolve_narrative_posture(
            trip,
            ai_surface_enabled=bool(ai_surface_enabled),
            llm_ready=bool(llm_ready),
        )
    except Exception:
        return "photo_led"


def _bookends_entry_summary(trip: dict, curation: dict) -> dict:
    """Compact bookends snapshot for Studio entry (B2b)."""
    try:
        from travelogue.cover_engine.api import build_bookends_studio_payload

        payload = build_bookends_studio_payload(trip)
        return {
            "panelTitle": payload.get("panelTitle"),
            "panelSubtitle": payload.get("panelSubtitle"),
            "userOneLiner": payload.get("userOneLiner"),
            "closingAssetId": payload.get("closingAssetId"),
            "closingPending": payload.get("closingPending"),
            "degraded": payload.get("degraded"),
            "lock": payload.get("lock"),
            "closingUserPicked": payload.get("closingUserPicked"),
            "mobileClosingEnabled": payload.get("mobileClosingEnabled"),
            "hasScreens": payload.get("hasScreens"),
        }
    except Exception:
        lock = curation.get("bookendsLock") if isinstance(curation.get("bookendsLock"), dict) else {}
        return {
            "panelTitle": "封面与封底",
            "panelSubtitle": "画册的第一眼与最后一眼",
            "userOneLiner": "",
            "closingAssetId": curation.get("closingAssetId") if "closingAssetId" in curation else None,
            "closingPending": "closingAssetId" not in curation,
            "degraded": bool(curation.get("bookendsDegraded")),
            "lock": {"opening": bool(lock.get("opening")), "closing": bool(lock.get("closing"))},
            "closingUserPicked": bool(curation.get("closingUserPicked")),
            "mobileClosingEnabled": False,
            "hasScreens": False,
        }
