"""resolve_output_recipe · 纯函数解析层（BE-OR-11 / PRD §10.1）."""

from __future__ import annotations

from typing import Any

from travelogue.export.output_recipe.config_loader import (
    copy_text,
    get_preset,
    load_band_thresholds,
    preset_id_for_intent,
)
from travelogue.export.output_recipe.kept_n import count_kept_n
from travelogue.export.output_recipe.types import (
    ALL_INTENTS,
    INTENT_TO_PLATFORM,
    PHASE_A_INTENTS,
    PHASE_B_INTENTS,
    PHASE_UNAVAILABLE_INTENTS,
    PLATFORM_TO_INTENT,
    BandThresholds,
    OutputRecipe,
    OutputRecipeError,
)


def classify_band(
    kept_n: int,
    thresholds: BandThresholds | None = None,
) -> str:
    """kept_n → sparse | ambiguous | narrative（AC-OR-01）."""
    t = thresholds or load_band_thresholds()
    n = max(0, int(kept_n))
    if n <= t.sparse_max:
        return "sparse"
    if n <= t.ambiguous_max:
        return "ambiguous"
    return "narrative"


def resolve_output_recipe(
    *,
    kept_n: int | None = None,
    trip: dict[str, Any] | None = None,
    locale: str = "zh",
    entrypoint: str = "preview",
    enabled: bool = True,
    session_override: dict[str, Any] | None = None,
    trip_output: dict[str, Any] | None = None,
    intent: str | None = None,
    platform: str | None = None,
    thresholds: BandThresholds | None = None,
    fallback_kept_n: int | None = None,
) -> OutputRecipe:
    """Band × locale × override → OutputRecipe.

    优先级（D-OR-10）：
      显式 session/cli override > trip.output > band 默认（Ambiguous 按入口矩阵）
    """
    t = thresholds or load_band_thresholds()
    n = int(kept_n) if kept_n is not None else count_kept_n(trip, fallback=fallback_kept_n)
    band = classify_band(n, t)
    loc = (locale or "zh").strip().lower() or "zh"
    ep = (entrypoint or "preview").strip().lower()
    if ep not in ("preview", "shelf", "cli"):
        raise OutputRecipeError("E_OR_INVALID_ENTRYPOINT", f"未知入口: {entrypoint}")

    # Feature flag off → 固定 wechat_chat（D-OR-24 / AC-OR-13）
    if not enabled:
        return _build_from_intent(
            "chat_longshot",
            band=band,
            kept_n=n,
            locale=loc,
            entrypoint=ep,
            layout=_default_layout(band),
            source="flag_disabled",
            needs_intent=False,
            thresholds=t,
        )

    from travelogue.config.edition import is_portfolio_trip

    portfolio = is_portfolio_trip(trip)

    # locale=zh 永不被 IG hook 改写（AC-OR-10）
    trip_out = trip_output
    if trip_out is None and trip is not None:
        raw = trip.get("output")
        trip_out = raw if isinstance(raw, dict) else None

    explicit_intent, explicit_platform, source = _merge_overrides(
        intent=intent,
        platform=platform,
        session_override=session_override,
        trip_output=None if portfolio else trip_out,
    )

    if explicit_intent or explicit_platform:
        resolved_intent = _resolve_intent_platform_pair(
            intent=explicit_intent,
            platform=explicit_platform,
        )
        layout_override = None
        if session_override and session_override.get("layout"):
            layout_override = str(session_override["layout"])
        elif (not portfolio) and trip_out and trip_out.get("layout"):
            layout_override = str(trip_out["layout"])
        return _build_from_intent(
            resolved_intent,
            band=band,
            kept_n=n,
            locale=loc,
            entrypoint=ep,
            layout=layout_override or _layout_for_intent(resolved_intent, band),
            source=source,
            needs_intent=False,
            thresholds=t,
        )

    # D-PFM-25 · 作品集不进 Ambiguous 意图矩阵；默认走「这一本 + 页图」。
    if portfolio:
        return _portfolio_bypass(band=band, kept_n=n, locale=loc, entrypoint=ep)

    # Ambiguous · 无 intent · 入口矩阵（D-OR-16 / §8.3）
    if band == "ambiguous":
        if ep == "preview":
            return _needs_intent_stub(band=band, kept_n=n, locale=loc, entrypoint=ep)
        if ep == "cli":
            raise OutputRecipeError(
                "E_OR_INTENT_REQUIRED",
                "Ambiguous 相册须指定 --intent 或 --platform",
            )
        # shelf → fallback chat + 弱提示
        return _build_from_intent(
            "chat_longshot",
            band=band,
            kept_n=n,
            locale=loc,
            entrypoint=ep,
            layout="single",
            source="band_default",
            needs_intent=False,
            thresholds=t,
            extra_hints=(copy_text("hint.ambiguous_shelf"),),
        )

    # Sparse / Narrative 默认
    default_intent = "chat_longshot"
    # Overseas：永不因 IG hook 改写 zh；en Narrative 切 IG 未授权
    if loc != "zh" and loc.startswith("en"):
        # OQ-OR-03 建议 archive；Phase A 仍落 chat_longshot，不切 IG
        default_intent = "chat_longshot"

    return _build_from_intent(
        default_intent,
        band=band,
        kept_n=n,
        locale=loc,
        entrypoint=ep,
        layout=_default_layout(band),
        source="band_default",
        needs_intent=False,
        thresholds=t,
    )


def normalize_studio_intent(intent: str | None) -> str | None:
    """Studio 下线九宫格：旧 session moments_grid → moments_scroll（CLI 显式 intent 不走此函数）."""
    if intent is None:
        return None
    raw = str(intent).strip()
    if not raw:
        return None
    if raw == "moments_grid":
        return "moments_scroll"
    return raw


def _merge_overrides(
    *,
    intent: str | None,
    platform: str | None,
    session_override: dict[str, Any] | None,
    trip_output: dict[str, Any] | None,
) -> tuple[str | None, str | None, str]:
    """Return (intent, platform, source) from highest-priority override present."""
    if session_override:
        si = session_override.get("intent")
        sp = session_override.get("platform")
        if si or sp:
            norm_i = normalize_studio_intent(str(si).strip() if si else None)
            norm_p = str(sp).strip() if sp else None
            if norm_p == "moments_grid":
                # session 里残留九宫格平台 → 朋友圈连读
                norm_p = "wechat_moments"
                if not norm_i:
                    norm_i = "moments_scroll"
            return (
                norm_i,
                norm_p,
                "session_override",
            )
    if intent or platform:
        # CLI / request body explicit — treat as session-level for source labeling
        src = "session_override" if (intent or platform) else "band_default"
        # Prefer intent_choice when only intent; platform_alias when only platform
        if intent and not platform:
            src = "intent_choice"
        elif platform and not intent:
            src = "platform_alias"
        elif intent and platform:
            src = "intent_choice"
        return (
            str(intent).strip() if intent else None,
            str(platform).strip() if platform else None,
            src,
        )
    if trip_output:
        ti = trip_output.get("intent")
        tp = trip_output.get("platform")
        if ti or tp or trip_output.get("preset_id") or trip_output.get("recipe_id"):
            return (
                str(ti).strip() if ti else None,
                str(tp).strip() if tp else None,
                "trip_override",
            )
    return None, None, "band_default"


def _resolve_intent_platform_pair(
    *,
    intent: str | None,
    platform: str | None,
) -> str:
    """Validate intent/platform; conflict → 400（IMPLEMENTATION 优先级表）."""
    intent_n = (intent or "").strip() or None
    platform_n = (platform or "").strip() or None

    if intent_n:
        if intent_n not in ALL_INTENTS:
            raise OutputRecipeError("E_OR_INVALID_INTENT", f"未知意图: {intent_n}")
        if intent_n in PHASE_UNAVAILABLE_INTENTS:
            raise OutputRecipeError(
                "E_OR_INTENT_UNAVAILABLE",
                f"意图尚未开放: {intent_n}",
            )
        if platform_n:
            expected = INTENT_TO_PLATFORM.get(intent_n)
            # wechat_moments ↔ moments_scroll
            if expected and platform_n != expected:
                # allow alias moments_scroll platform name
                mapped = PLATFORM_TO_INTENT.get(platform_n)
                if mapped != intent_n:
                    raise OutputRecipeError(
                        "E_OR_INTENT_PLATFORM_CONFLICT",
                        f"--intent {intent_n} 与 --platform {platform_n} 冲突",
                    )
        return intent_n

    if platform_n:
        mapped = PLATFORM_TO_INTENT.get(platform_n)
        if mapped is None:
            raise OutputRecipeError(
                "E_OR_UNKNOWN_PLATFORM",
                f"未知或未映射的 platform: {platform_n}",
            )
        if mapped in PHASE_UNAVAILABLE_INTENTS:
            raise OutputRecipeError(
                "E_OR_INTENT_UNAVAILABLE",
                f"意图尚未开放: {mapped}",
            )
        return mapped

    raise OutputRecipeError("E_OR_INVALID_INTENT", "须指定 intent 或 platform")


def _default_layout(band: str) -> str:
    if band == "sparse":
        return "single"
    if band == "narrative":
        return "by_chapter"
    return "single"


def _layout_for_intent(intent: str, band: str) -> str:
    if intent == "moments_scroll":
        return "content_balanced"
    if intent == "moments_grid":
        return "grid"
    if intent == "poster_bric":
        return "collage"
    if intent in ("xiaohongshu", "album_spread"):
        return "collage"
    if intent == "instagram_carousel":
        return "content_balanced"
    return _default_layout(band)


def _portfolio_bypass(
    *,
    band: str,
    kept_n: int,
    locale: str,
    entrypoint: str,
) -> OutputRecipe:
    """AC-PFM-19 · no intent card; Dock CTA is 导出作品集."""
    return OutputRecipe(
        recipe_id="portfolio.pack",
        preset_id="",
        intent="",
        engine="",
        band=band,
        kept_n=kept_n,
        locale=locale,
        platform="",
        layout="",
        needs_intent=False,
        source="portfolio_bypass",
        cta_label="导出作品集",
        product_label="",
        entrypoint=entrypoint,
    )


def _needs_intent_stub(
    *,
    band: str,
    kept_n: int,
    locale: str,
    entrypoint: str,
) -> OutputRecipe:
    return OutputRecipe(
        recipe_id="pending.intent",
        preset_id="",
        intent="",
        engine="",
        band=band,
        kept_n=kept_n,
        locale=locale,
        platform="",
        layout="",
        needs_intent=True,
        source="band_default",
        cta_label=copy_text("intent.select_and_export"),
        product_label="",
        entrypoint=entrypoint,
        user_hints=(copy_text("intent.title", n=kept_n),),
    )


def _build_from_intent(
    intent: str,
    *,
    band: str,
    kept_n: int,
    locale: str,
    entrypoint: str,
    layout: str,
    source: str,
    needs_intent: bool,
    thresholds: BandThresholds,
    extra_hints: tuple[str, ...] = (),
) -> OutputRecipe:
    if intent not in ALL_INTENTS:
        raise OutputRecipeError("E_OR_INVALID_INTENT", f"未知意图: {intent}")
    if intent in PHASE_UNAVAILABLE_INTENTS:
        raise OutputRecipeError(
            "E_OR_INTENT_UNAVAILABLE",
            f"意图尚未开放: {intent}",
        )

    preset_id = preset_id_for_intent(intent, layout=layout)
    preset = get_preset(preset_id)
    phases = preset.get("phases") or []
    if "hidden" in phases and intent == "instagram_carousel":
        # hook_only：可解析但标记状态；不改变 zh 默认（仅显式请求时到达）
        pass

    platform = str(preset.get("platform") or INTENT_TO_PLATFORM[intent])
    engine = str(preset.get("engine") or "")
    hints: list[str] = list(extra_hints)
    if (
        intent == "chat_longshot"
        and band == "narrative"
        and kept_n >= thresholds.narrative_chapter_hint_at
    ):
        hints.append(copy_text("hint.narrative_deep"))
    if intent == "moments_grid":
        n_grid = min(9, max(0, kept_n))
        hints.append(copy_text("intent.grid", n=n_grid))
        hints.append(copy_text("hint.grid_count"))

    cta_key = str(preset.get("cta_key") or "")
    if intent == "chat_longshot":
        cta_key = "cta.narrative_chat" if band == "narrative" else "cta.sparse_chat"
    label_key = str(preset.get("product_label_key") or "")

    ig_state = preset.get("instagram_preset_state")
    if intent == "instagram_carousel":
        ig_state = ig_state or "hook_only"
    else:
        ig_state = None

    # locale=zh：强制忽略任何海外默认污染
    if locale == "zh" and intent == "instagram_carousel" and source == "band_default":
        raise OutputRecipeError(
            "E_OR_LOCALE_GUARD",
            "locale=zh 默认不得使用 Instagram 配方",
        )

    return OutputRecipe(
        recipe_id=preset_id,
        preset_id=preset_id,
        intent=intent,
        engine=engine,
        band=band,
        kept_n=kept_n,
        locale=locale,
        platform=platform,
        layout=str(preset.get("layout") or layout),
        count_policy=dict(preset.get("count_policy") or {}),
        geometry=dict(preset.get("geometry") or {}),
        pad_mode=preset.get("pad_mode"),
        packing=str(preset.get("packing") or "none"),
        quality={"scale": 2},
        publish_guide_key=str(preset.get("publish_guide_key") or ""),
        user_hints=tuple(hints),
        needs_intent=needs_intent,
        source=source,
        instagram_preset_state=str(ig_state) if ig_state else None,
        cta_label=copy_text(cta_key) if cta_key else "",
        product_label=copy_text(label_key) if label_key else "",
        entrypoint=entrypoint,
    )


def ambiguous_intent_options(*, phase: str = "B", kept_n: int = 0) -> list[dict[str, str]]:
    """Ambiguous 卡选项。Studio：发群 > 朋友圈连读（九宫格已下线）。"""
    _ = kept_n
    opts = [
        {
            "intent": "chat_longshot",
            "label": copy_text("intent.chat"),
            "weight": "primary",
        },
        {
            "intent": "moments_scroll",
            "label": copy_text("intent.scroll"),
            "weight": "secondary",
        },
    ]
    allowed = PHASE_B_INTENTS if str(phase).upper() in ("B", "B0", "B1") else PHASE_A_INTENTS
    for o in opts:
        if o["intent"] not in allowed:
            raise OutputRecipeError(
                "E_OR_INVALID_INTENT",
                f"ambiguous option intent not allowed: {o['intent']!r}",
            )
        if o["intent"] == "moments_scroll" and "九宫格" in o["label"]:
            raise OutputRecipeError(
                "E_OR_INVALID_INTENT",
                "scroll label must not contain 九宫格",
            )
    return opts
