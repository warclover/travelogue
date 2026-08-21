"""YAML config loading and Studio patch helpers."""

from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from typing import Any

from travelogue.config._common import (
    normalize_arc_mode,
    normalize_narrative_scope,
    normalize_tri_state,
    yaml,
)
from travelogue.config.aesthetic import aesthetic_from_dict
from travelogue.config.app import AppConfig
from travelogue.config.bookends import bookends_config_from_dict
from travelogue.config.clustering import GeocodeConfig, clustering_from_dict
from travelogue.config.cohort import CohortConfig
from travelogue.config.cover_scoring_params import CoverScoringParams
from travelogue.config.cull import cull_from_dict
from travelogue.config.curate import CurateConfig, cover_scoring_v2_from_dict
from travelogue.config.errors import ConfigError
from travelogue.config.food_role import food_role_config_from_dict
from travelogue.config.ingest import ingest_from_dict
from travelogue.config.layout import (
    LayoutConfig,
    editorial_4mix_from_dict,
    editorial_portrait_row_from_dict,
    landscape_2_editorial_from_dict,
    landscape_3_editorial_from_dict,
    layout_feedback_from_dict,
    layout_rhythm_from_dict,
    layout_scoring_from_dict,
    layout_strategy_engine_from_dict,
    layout_template_engine_from_dict,
    mixed_1l1p_from_dict,
    mixed_1p2l_from_dict,
    portrait_2_variants_from_dict,
    usage_rules_from_dict,
)
from travelogue.config.misc import (
    ExportConfig,
    LlmConfig,
    NarrativeConfig,
    pipeline_from_dict,
    render_from_dict,
)
from travelogue.config.moment import moment_config_from_dict
from travelogue.config.mosaic import mosaic_from_dict
from travelogue.config.phase6 import phase6_from_dict
from travelogue.config.shot_grouping import shot_grouping_from_dict
from travelogue.config.studio import (
    DEFAULT_LONGSHOT2_PLATFORMS,
    GcsPosterBricConfig,
    Longshot2Config,
    OutputRecipeBandsConfig,
    OutputRecipeConfig,
    PortfolioPipelineConfig,
    StudioConfig,
)
from travelogue.config.template import TemplateAdminConfig, TemplateRouterConfig
from travelogue.config.ai_capability import ai_capability_config_from_dict
from travelogue.config.title_art import title_art_config_from_dict
from travelogue.config.cover_craft import cover_craft_config_from_dict
from travelogue.config.album_editorial import album_editorial_lab_from_dict
from travelogue.config.tracking import TrackedDict, collect_unknown_keys, wrap_tracked
from travelogue.config.vision import vision_from_dict
from travelogue.config.yaml_loader import load_yaml_mapping
from travelogue.config_helpers import cfg_bool, cfg_int
from travelogue.paths import ROOT
from travelogue.util.llm_presets import PROVIDER_PRESETS

_log = logging.getLogger(__name__)


def _parse_longshot2_config(studio_raw: dict[str, Any]) -> Longshot2Config:
    raw = studio_raw.get("longshot2") if isinstance(studio_raw.get("longshot2"), dict) else {}
    platforms_raw = raw.get("platforms", list(DEFAULT_LONGSHOT2_PLATFORMS))
    if isinstance(platforms_raw, str):
        platforms: tuple[str, ...] = (platforms_raw,)
    elif isinstance(platforms_raw, (list, tuple)):
        platforms = tuple(str(x).strip() for x in platforms_raw if str(x).strip())
    else:
        platforms = DEFAULT_LONGSHOT2_PLATFORMS
    smart = raw.get("smart_crop") if isinstance(raw.get("smart_crop"), dict) else {}
    if not smart and isinstance(raw.get("smartCrop"), dict):
        smart = raw["smartCrop"]
    return Longshot2Config(
        enabled=cfg_bool(raw, "enabled", "enabled", True) if raw else True,
        platforms=platforms or DEFAULT_LONGSHOT2_PLATFORMS,
        smart_crop_enabled=cfg_bool(smart, "enabled", "enabled", False) if smart else False,
    )


def _parse_output_recipe_config(studio_raw: dict[str, Any]) -> OutputRecipeConfig:
    raw = studio_raw.get("output_recipe")
    if not isinstance(raw, dict):
        raw = studio_raw.get("outputRecipe")
    if not isinstance(raw, dict):
        raw = {}
    bands_raw = raw.get("bands") if isinstance(raw.get("bands"), dict) else {}
    return OutputRecipeConfig(
        enabled=cfg_bool(raw, "enabled", "enabled", False) if raw else False,
        bands=OutputRecipeBandsConfig(
            sparse_max=cfg_int(bands_raw, "sparse_max", "sparseMax", 9),
            ambiguous_max=cfg_int(bands_raw, "ambiguous_max", "ambiguousMax", 30),
            narrative_chapter_hint_at=cfg_int(
                bands_raw, "narrative_chapter_hint_at", "narrativeChapterHintAt", 50
            ),
        ),
    )


def _parse_gcs_poster_bric_config(
    data: dict[str, Any], studio_raw: dict[str, Any]
) -> GcsPosterBricConfig:
    """PRD key features.gcs_poster_bric; also accept studio.gcs_poster_bric."""
    features = data.get("features") if isinstance(data.get("features"), dict) else {}
    raw = features.get("gcs_poster_bric") if isinstance(features.get("gcs_poster_bric"), dict) else None
    if raw is None and isinstance(features.get("gcsPosterBric"), dict):
        raw = features["gcsPosterBric"]
    if raw is None:
        raw = studio_raw.get("gcs_poster_bric")
    if not isinstance(raw, dict):
        raw = studio_raw.get("gcsPosterBric")
    if not isinstance(raw, dict):
        raw = {}
    return GcsPosterBricConfig(
        enabled=cfg_bool(raw, "enabled", "enabled", True) if raw else True,
    )


def _parse_portfolio_pipeline_config(studio_raw: dict[str, Any]) -> PortfolioPipelineConfig:
    raw = studio_raw.get("portfolio_pipeline")
    if not isinstance(raw, dict):
        raw = studio_raw.get("portfolioPipeline")
    if not isinstance(raw, dict):
        raw = {}
    override = raw.get("min_kept_override", raw.get("minKeptOverride"))
    min_kept: int | None
    if override is None or override == "":
        min_kept = None
    else:
        try:
            parsed = int(override)
        except (TypeError, ValueError):
            parsed = 0
        min_kept = parsed if parsed > 0 else None
    return PortfolioPipelineConfig(
        enabled=cfg_bool(raw, "enabled", "enabled", False),
        homepage_entry=cfg_bool(raw, "homepage_entry", "homepageEntry", False),
        allow_refine_switch=cfg_bool(raw, "allow_refine_switch", "allowRefineSwitch", True),
        max_pages=cfg_int(raw, "max_pages", "maxPages", 48),
        min_kept_override=min_kept,
    )

LSE_BEAT_PROFILE_VALUES = frozenset({"flat", "classic_magazine", "dense_mid"})
LSE_CAPABILITY_KEYS = frozenset(
    {
        "saliency_scoring",
        "tone_harmony",
        "hungarian_assignment",
        "quality_unified",
        "segment_order_optimizer",
        "implicit_feedback_export",
        "highlight_windows",
        "editorial_hints",
        "beat_profile",
    }
)


_PATCH_CONFIG_LOCK = threading.Lock()


def patch_config_file(path: Path, patch: dict[str, Any]) -> None:
    """Merge whitelisted keys into config.yaml on disk (atomic replace)."""
    if yaml is None:
        raise RuntimeError("PyYAML required to patch config")
    with _PATCH_CONFIG_LOCK:
        _patch_config_file_unlocked(path, patch)


def _patch_config_file_unlocked(path: Path, patch: dict[str, Any]) -> None:
    data: dict[str, Any] = {}
    if path.is_file():
        with path.open(encoding="utf-8") as f:
            loaded = yaml.safe_load(f) or {}
            if isinstance(loaded, dict):
                data = loaded
    allowed_clustering = {"enabled", "segmentCurateMode", "sceneClusterMode"}
    allowed_vision = {"enabled"}
    # wall_clock_limits_output / prefer / capability stay operator-yaml only (FE-ALG3-04).
    allowed_layout_scoring = {"enabled"}
    allowed_ingest = {"copySourceFiles", "copy_source_files"}
    allowed_studio = {
        "g1ConfirmStructure",
        "g1_confirm_structure",
        "importDualModeEnabled",
        "import_dual_mode_enabled",
        "successRefinedDefaultEnabled",
        "success_refined_default_enabled",
        "importSheetLargeEnabled",
        "import_sheet_large_enabled",
        "layoutTemplatesInternal",
        "layout_templates_internal",
    }
    clu_patch = patch.get("clustering") if isinstance(patch.get("clustering"), dict) else {}
    vis_patch = patch.get("vision") if isinstance(patch.get("vision"), dict) else {}
    layout_patch = patch.get("layout") if isinstance(patch.get("layout"), dict) else {}
    studio_patch = patch.get("studio") if isinstance(patch.get("studio"), dict) else {}
    ingest_patch = patch.get("ingest") if isinstance(patch.get("ingest"), dict) else {}
    if clu_patch:
        target = data.setdefault("clustering", {})
        if not isinstance(target, dict):
            target = {}
            data["clustering"] = target
        for key, val in clu_patch.items():
            if key in allowed_clustering:
                target[key] = val
    if vis_patch:
        target = data.setdefault("vision", {})
        if not isinstance(target, dict):
            target = {}
            data["vision"] = target
        for key, val in vis_patch.items():
            if key in allowed_vision:
                target[key] = val
    scoring_patch = (
        layout_patch.get("scoring") if isinstance(layout_patch.get("scoring"), dict) else {}
    )
    if scoring_patch:
        layout_target = data.setdefault("layout", {})
        if not isinstance(layout_target, dict):
            layout_target = {}
            data["layout"] = layout_target
        scoring_target = layout_target.setdefault("scoring", {})
        if not isinstance(scoring_target, dict):
            scoring_target = {}
            layout_target["scoring"] = scoring_target
        for key, val in scoring_patch.items():
            if key in allowed_layout_scoring:
                scoring_target[key] = val
    strategy_engine_patch = (
        layout_patch.get("strategy_engine")
        if isinstance(layout_patch.get("strategy_engine"), dict)
        else {}
    )
    if strategy_engine_patch:
        layout_target = data.setdefault("layout", {})
        if not isinstance(layout_target, dict):
            layout_target = {}
            data["layout"] = layout_target
        se_target = layout_target.setdefault("strategy_engine", {})
        if not isinstance(se_target, dict):
            se_target = {}
            layout_target["strategy_engine"] = se_target
        if "enabled" in strategy_engine_patch:
            se_target["enabled"] = bool(strategy_engine_patch["enabled"])
        caps_patch = (
            strategy_engine_patch.get("capabilities")
            if isinstance(strategy_engine_patch.get("capabilities"), dict)
            else {}
        )
        if caps_patch:
            caps_target = se_target.setdefault("capabilities", {})
            if not isinstance(caps_target, dict):
                caps_target = {}
                se_target["capabilities"] = caps_target
            for key, val in caps_patch.items():
                if key not in LSE_CAPABILITY_KEYS:
                    continue
                if key == "beat_profile":
                    beat = str(val or "flat").strip().lower()
                    if beat not in LSE_BEAT_PROFILE_VALUES:
                        raise ValueError(
                            f"beat_profile must be one of {sorted(LSE_BEAT_PROFILE_VALUES)}"
                        )
                    caps_target[key] = beat
                else:
                    caps_target[key] = bool(val)
    if studio_patch:
        target = data.setdefault("studio", {})
        if not isinstance(target, dict):
            target = {}
            data["studio"] = target
        for key, val in studio_patch.items():
            if key in allowed_studio:
                mapping = {
                    "g1ConfirmStructure": "g1_confirm_structure",
                    "importDualModeEnabled": "import_dual_mode_enabled",
                    "successRefinedDefaultEnabled": "success_refined_default_enabled",
                    "importSheetLargeEnabled": "import_sheet_large_enabled",
                }
                norm_key = mapping.get(key, key)
                target[norm_key] = val
    if ingest_patch:
        target = data.setdefault("ingest", {})
        if not isinstance(target, dict):
            target = {}
            data["ingest"] = target
        for key, val in ingest_patch.items():
            if key not in allowed_ingest:
                continue
            norm_key = "copy_source_files" if key in ("copySourceFiles", "copy_source_files") else key
            target[norm_key] = bool(val)
    path.parent.mkdir(parents=True, exist_ok=True)
    # CQA I-CQA-12 · tmp + os.replace (no truncated YAML on concurrent PATCH)
    tmp = path.with_suffix(path.suffix + ".tmp")
    text = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
    with tmp.open("w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _read_strict_flag(data: dict[str, Any]) -> bool:
    if isinstance(data, TrackedDict):
        data.mark_keys("strict", "config")
    config_raw = data.get("config") if isinstance(data.get("config"), dict) else {}
    if isinstance(config_raw, TrackedDict):
        config_raw.mark_keys("strict")
    if "strict" in data:
        return bool(data.get("strict", False))
    if isinstance(config_raw, dict):
        return bool(config_raw.get("strict", False))
    return False


def _report_unknown_config_keys(keys: list[str], *, strict: bool) -> None:
    if not keys:
        return
    joined = ", ".join(keys)
    message = f"config: unknown keys: {joined}"
    if strict:
        raise ConfigError(message)
    _log.warning(message)


def _merge_user_llm_overlay(data: TrackedDict | dict[str, Any]) -> TrackedDict | dict[str, Any]:
    """Merge user_data config.user.yaml llm section (Desktop LLM Setup V1)."""
    try:
        from travelogue.config.user_overlay import load_user_llm_config_overlay

        overlay = load_user_llm_config_overlay()
    except Exception:
        return data
    llm_overlay = overlay.get("llm") if isinstance(overlay, dict) else None
    if not isinstance(llm_overlay, dict) or not llm_overlay:
        return data
    base_llm = data.get("llm") if isinstance(data.get("llm"), dict) else {}
    merged_llm = {**dict(base_llm), **dict(llm_overlay)}
    if isinstance(data, TrackedDict):
        data["llm"] = wrap_tracked(merged_llm, path="llm", allow_extra=True)
        return data
    out = dict(data)
    out["llm"] = merged_llm
    return out


def load_config(path: Path | None = None) -> AppConfig:
    """Load config.yaml from path, or ./config.yaml, or defaults."""
    from travelogue.paths import is_frozen, user_config_path, user_data_dir

    candidates: list[Path | None] = [path, Path.cwd() / "config.yaml"]
    if is_frozen():
        candidates.append(user_config_path())
    else:
        candidates.append(ROOT / "config.yaml")
    cfg_path = next((p for p in candidates if p and p.is_file()), None)
    data: TrackedDict | dict[str, Any] = {}
    if cfg_path and yaml is not None:
        text = cfg_path.read_text(encoding="utf-8")
        loaded = load_yaml_mapping(text, source=str(cfg_path))
        data = wrap_tracked(loaded)
    data = _merge_user_llm_overlay(data)
    if isinstance(data, TrackedDict):
        data.mark_keys("ffmpeg", "preview")
    strict = _read_strict_flag(data) if isinstance(data, TrackedDict) else False
    trips = data.get("trips_dir", "./trips")
    trips_dir = Path(trips)
    if not trips_dir.is_absolute():
        base = Path.cwd()
        try:
            if is_frozen():
                # Relative trips_dir is anchored at user_data_dir (portable or LocalAppData).
                base = user_data_dir()
        except Exception:
            _log.debug("frozen user_data_dir lookup failed; using cwd for trips_dir", exc_info=True)
        trips_dir = (base / trips_dir).resolve()
    ingest_raw = data.get("ingest") if isinstance(data.get("ingest"), dict) else {}
    if isinstance(ingest_raw, TrackedDict):
        ingest_raw.mark_keys(
            "max_videos",
            "max_video_source_sec",
            "max_video_clip_mb",
            "max_zip_mb",
            "maxVideos",
            "maxVideoSourceSec",
            "maxVideoClipMb",
            "maxZipMb",
        )
    layout_raw = data.get("layout") if isinstance(data.get("layout"), dict) else {}
    web_engine = str(layout_raw.get("web_layout_engine", "screens")).strip().lower()
    if web_engine not in ("legacy", "screens"):
        web_engine = "screens"
    scope = str(layout_raw.get("screen_plan_scope", "day")).strip().lower()
    if scope not in ("chapter", "day"):
        scope = "day"
    import warnings

    legacy_planner = str(layout_raw.get("planner_impl", "")).strip().lower()
    if legacy_planner == "curation":
        warnings.warn(
            "layout.planner_impl=curation was removed (M-D1); using layout_engine planner",
            UserWarning,
            stacklevel=2,
        )
    mixed_gap = float(
        layout_raw.get(
            "mixed_proximity_seconds",
            LayoutConfig().mixed_proximity_seconds,
        )
    )
    layout_density_top = data.get("layoutDensity") if isinstance(data.get("layoutDensity"), dict) else {}
    layout_density_enabled = bool(
        layout_density_top.get("enabled", layout_raw.get("layout_density_enabled", True))
    )
    scoring_raw = layout_raw.get("scoring") if isinstance(layout_raw.get("scoring"), dict) else {}
    rhythm_raw = layout_raw.get("rhythm") if isinstance(layout_raw.get("rhythm"), dict) else {}
    editorial_row_raw = (
        layout_raw.get("editorial_portrait_row")
        if isinstance(layout_raw.get("editorial_portrait_row"), dict)
        else {}
    )
    editorial_4mix_raw = (
        layout_raw.get("editorial_4mix")
        if isinstance(layout_raw.get("editorial_4mix"), dict)
        else {}
    )
    portrait_2_variants_raw = (
        layout_raw.get("portrait_2_variants")
        if isinstance(layout_raw.get("portrait_2_variants"), dict)
        else {}
    )
    mixed_1l1p_raw = (
        layout_raw.get("mixed_1l1p")
        if isinstance(layout_raw.get("mixed_1l1p"), dict)
        else {}
    )
    landscape_2_editorial_raw = (
        layout_raw.get("landscape_2_editorial")
        if isinstance(layout_raw.get("landscape_2_editorial"), dict)
        else {}
    )
    landscape_3_editorial_raw = (
        layout_raw.get("landscape_3_editorial")
        if isinstance(layout_raw.get("landscape_3_editorial"), dict)
        else {}
    )
    mixed_1p2l_raw = (
        layout_raw.get("mixed_1p2l")
        if isinstance(layout_raw.get("mixed_1p2l"), dict)
        else {}
    )
    usage_rules_raw = (
        layout_raw.get("usage_rules")
        if isinstance(layout_raw.get("usage_rules"), dict)
        else {}
    )
    feedback_raw = layout_raw.get("feedback") if isinstance(layout_raw.get("feedback"), dict) else {}
    strategy_engine_raw = (
        layout_raw.get("strategy_engine")
        if isinstance(layout_raw.get("strategy_engine"), dict)
        else {}
    )
    template_engine_raw = (
        layout_raw.get("template_engine") if isinstance(layout_raw.get("template_engine"), dict) else {}
    )
    export_raw = data.get("export") if isinstance(data.get("export"), dict) else {}
    if isinstance(export_raw, TrackedDict):
        export_raw.mark_keys(
            "max_zip_mb",
            "preview_width",
            "strip_exif",
            "previewWidth",
            "stripExif",
        )
    vision_raw = data.get("vision") if isinstance(data.get("vision"), dict) else {}
    narrative_raw = data.get("narrative") if isinstance(data.get("narrative"), dict) else {}
    llm_raw = data.get("llm") if isinstance(data.get("llm"), dict) else {}
    geocode_raw = data.get("geocode") if isinstance(data.get("geocode"), dict) else {}
    if isinstance(geocode_raw, TrackedDict):
        geocode_raw.mark_keys("enabled", "provider", "api_key_env", "apiKeyEnv")
    curate_raw = data.get("curate") if isinstance(data.get("curate"), dict) else {}
    curate_layout_raw = curate_raw.get("layout") if isinstance(curate_raw.get("layout"), dict) else {}
    bookends_raw = data.get("bookends") if isinstance(data.get("bookends"), dict) else {}
    render_raw = data.get("render") if isinstance(data.get("render"), dict) else {}
    clustering_raw = data.get("clustering") if isinstance(data.get("clustering"), dict) else {}
    shot_grouping_raw = (
        data.get("shotGrouping")
        if isinstance(data.get("shotGrouping"), dict)
        else (data.get("shot_grouping") if isinstance(data.get("shot_grouping"), dict) else {})
    )
    pipeline_raw = data.get("pipeline") if isinstance(data.get("pipeline"), dict) else {}
    cull_raw = data.get("cull") if isinstance(data.get("cull"), dict) else {}
    studio_raw = data.get("studio") if isinstance(data.get("studio"), dict) else {}
    phase6_raw = data.get("phase6") if isinstance(data.get("phase6"), dict) else {}
    template_router_raw = data.get("template_router") if isinstance(data.get("template_router"), dict) else {}
    template_admin_raw = data.get("template_admin") if isinstance(data.get("template_admin"), dict) else {}
    cohort_raw = data.get("cohort") if isinstance(data.get("cohort"), dict) else {}
    aesthetic_raw = data.get("aesthetic") if isinstance(data.get("aesthetic"), dict) else {}
    title_art_raw = (
        data.get("title_art") if isinstance(data.get("title_art"), dict) else data.get("titleArt")
    )
    title_art_raw = title_art_raw if isinstance(title_art_raw, dict) else {}
    cover_craft_raw = (
        data.get("cover_craft")
        if isinstance(data.get("cover_craft"), dict)
        else data.get("coverCraft")
    )
    cover_craft_raw = cover_craft_raw if isinstance(cover_craft_raw, dict) else {}
    album_editorial_raw = (
        data.get("album_editorial_lab")
        if isinstance(data.get("album_editorial_lab"), dict)
        else data.get("albumEditorialLab")
    )
    album_editorial_raw = (
        album_editorial_raw if isinstance(album_editorial_raw, dict) else {}
    )
    ai_capability_raw = (
        data.get("ai_capability")
        if isinstance(data.get("ai_capability"), dict)
        else data.get("aiCapability")
    )
    ai_capability_raw = ai_capability_raw if isinstance(ai_capability_raw, dict) else {}
    mosaic_raw = data.get("mosaic") if isinstance(data.get("mosaic"), dict) else {}
    layout_top = data.get("layout") if isinstance(data.get("layout"), dict) else {}
    if isinstance(layout_top, TrackedDict):
        layout_top.mark_keys("mosaic_v2", "mosaicV2")
    mosaic_v2 = layout_top.get("mosaic_v2") if isinstance(layout_top.get("mosaic_v2"), dict) else {}
    if mosaic_v2:
        if isinstance(mosaic_raw, TrackedDict) and isinstance(mosaic_v2, TrackedDict):
            merged = dict(mosaic_v2)
            merged.update(mosaic_raw)
            mosaic_raw = wrap_tracked(merged, path="mosaic", allow_extra=mosaic_raw.allow_extra)
        else:
            mosaic_raw = {**mosaic_v2, **mosaic_raw}
    banned_raw = narrative_raw.get("banned_phrases") or []
    banned = tuple(str(p) for p in banned_raw if p) if isinstance(banned_raw, list) else ()
    llm_provider = str(llm_raw.get("provider", "stub")).strip().lower()
    if llm_provider not in ("stub", "deepseek", "dashscope"):
        llm_provider = "stub"
    llm_preset = PROVIDER_PRESETS.get(llm_provider, {})
    llm_base = llm_raw.get("base_url")
    llm_base_url = str(llm_base).strip() if llm_base else None
    mosaic_defaults_used = not mosaic_raw
    if mosaic_defaults_used and (
        os.environ.get("TRAVELOGUE_CONFIG_VERBOSE", "").strip().lower() in ("1", "true", "yes")
        or os.environ.get("TRAVELOGUE_VERBOSE", "").strip().lower() in ("1", "true", "yes")
    ):
        defaults = mosaic_from_dict({})
        _log.info(
            "mosaic: no mosaic: section in config; using MosaicConfig defaults "
            "(enabled_window_sizes=%s)",
            defaults.enabled_window_sizes,
        )
    app_cfg = AppConfig(
        trips_dir=trips_dir,
        ingest=ingest_from_dict(ingest_raw),
        cull=cull_from_dict(cull_raw),
        pipeline=pipeline_from_dict(pipeline_raw),
        export=ExportConfig(max_zip_mb=int(export_raw.get("max_zip_mb", 25))),
        render=render_from_dict(render_raw),
        layout=LayoutConfig(
            web_layout_engine=web_engine,
            screen_plan_scope=scope,
            mixed_proximity_seconds=mixed_gap,
            layout_density_enabled=layout_density_enabled,
            editorial_portrait_row=editorial_portrait_row_from_dict(editorial_row_raw),
            editorial_4mix=editorial_4mix_from_dict(editorial_4mix_raw),
            portrait_2_variants=portrait_2_variants_from_dict(portrait_2_variants_raw),
            mixed_1l1p=mixed_1l1p_from_dict(mixed_1l1p_raw),
            landscape_2_editorial=landscape_2_editorial_from_dict(
                landscape_2_editorial_raw
            ),
            landscape_3_editorial=landscape_3_editorial_from_dict(
                landscape_3_editorial_raw
            ),
            mixed_1p2l=mixed_1p2l_from_dict(mixed_1p2l_raw),
            usage_rules=usage_rules_from_dict(usage_rules_raw),
            rhythm=layout_rhythm_from_dict(rhythm_raw),
            template_engine=layout_template_engine_from_dict(template_engine_raw),
            strategy_engine=layout_strategy_engine_from_dict(strategy_engine_raw),
            scoring=layout_scoring_from_dict(scoring_raw),
            feedback=layout_feedback_from_dict(feedback_raw),
        ),
        clustering=clustering_from_dict(clustering_raw),
        shot_grouping=shot_grouping_from_dict(shot_grouping_raw),
        vision=vision_from_dict(vision_raw),
        geocode=GeocodeConfig(enabled=bool(geocode_raw.get("enabled", False))),
        config_path=cfg_path,
        curate=CurateConfig(
            segment_gap_days=int(curate_raw.get("segment_gap_days", 14)),
            city_gap_days=int(curate_raw.get("city_gap_days", 3)),
            min_bucket_size=int(curate_raw.get("min_bucket_size", 3)),
            chapter_balance_enabled=bool(
                curate_raw.get("chapter_balance_enabled", curate_raw.get("chapterBalanceEnabled", True))
            ),
            chapter_balance_ratio=float(
                curate_raw.get("chapter_balance_ratio", curate_raw.get("chapterBalanceRatio", 0.55))
            ),
            arc_mode=normalize_arc_mode(curate_raw.get("arc_mode", "legacy")),
            arc_flat_variance_threshold=float(
                curate_raw.get("arc_flat_variance_threshold", 0.08)
            ),
            featured_weight=float(curate_raw.get("featured_weight", 1.35)),
            featured_min_for_cover_pool=int(curate_raw.get("featured_min_for_cover_pool", 2)),
            cover_scoring=CoverScoringParams.from_mapping(
                curate_raw.get("cover_scoring") or curate_raw.get("coverScoring")
            ),
            cover_scoring_version=str(
                curate_raw.get(
                    "cover_scoring_version",
                    curate_raw.get("coverScoringVersion", "v2"),
                )
            ).lower(),
            cover_scoring_v2=cover_scoring_v2_from_dict(curate_raw),
            cover_joint_enabled=bool(
                curate_raw.get(
                    "cover_joint_enabled",
                    curate_raw.get("coverJointEnabled", True),
                )
            ),
            cover_joint_top_k=int(
                curate_raw.get("cover_joint_top_k", curate_raw.get("coverJointTopK", 8))
            ),
            cover_joint_w_fit=float(
                curate_raw.get("cover_joint_w_fit", curate_raw.get("coverJointWFit", 0.35))
            ),
            cover_joint_w_avoid=float(
                curate_raw.get(
                    "cover_joint_w_avoid", curate_raw.get("coverJointWAvoid", 0.50)
                )
            ),
            enable_gravity_balance=bool(
                curate_layout_raw.get(
                    "enable_gravity_balance",
                    curate_raw.get("enable_gravity_balance", True),
                )
            ),
            enable_mmr_diversity=bool(
                curate_layout_raw.get(
                    "enable_mmr_diversity",
                    curate_raw.get("enable_mmr_diversity", True),
                )
            ),
            max_consecutive_same_pattern=int(
                curate_layout_raw.get(
                    "max_consecutive_same_pattern",
                    curate_raw.get("max_consecutive_same_pattern", 2),
                )
            ),
            longshot_mmr_lambda=float(
                curate_layout_raw.get(
                    "longshot_mmr_lambda",
                    curate_raw.get("longshot_mmr_lambda", 0.72),
                )
            ),
            enable_arc_breath=bool(
                curate_layout_raw.get(
                    "enable_arc_breath",
                    curate_raw.get("enable_arc_breath", True),
                )
            ),
            enable_food_grid=bool(
                curate_layout_raw.get(
                    "enable_food_grid",
                    curate_raw.get("enable_food_grid", True),
                )
            ),
            mundane_grid_buckets=tuple(
                str(x).strip().lower()
                for x in (
                    curate_layout_raw.get(
                        "mundane_grid_buckets",
                        curate_raw.get("mundane_grid_buckets", ["food"]),
                    )
                    or ["food"]
                )
                if str(x).strip()
            ),
            food_role=food_role_config_from_dict(
                curate_raw.get("food_role")
                if isinstance(curate_raw.get("food_role"), dict)
                else (
                    curate_raw.get("foodRole")
                    if isinstance(curate_raw.get("foodRole"), dict)
                    else {}
                )
            ),
            moment=moment_config_from_dict(
                curate_raw.get("moment") if isinstance(curate_raw.get("moment"), dict) else {}
            ),
        ),
        bookends=bookends_config_from_dict(bookends_raw),
        narrative=NarrativeConfig(
            tone_default=str(narrative_raw.get("tone_default", "relaxed")),
            max_auto_fix_retries=int(narrative_raw.get("max_auto_fix_retries", 2)),
            banned_phrases=banned,
            scope=normalize_narrative_scope(narrative_raw.get("scope", "frame")),
            decor_line_enabled=bool(narrative_raw.get("decor_line_enabled", True)),
            copy_generation_enabled=bool(
                narrative_raw.get(
                    "copy_generation_enabled",
                    narrative_raw.get("decor_line_enabled", True),
                )
            ),
            show_hook_in_draft=bool(narrative_raw.get("show_hook_in_draft", True)),
            decor_line_max_chars=int(narrative_raw.get("decor_line_max_chars", 30)),
            decor_line_candidates=int(narrative_raw.get("decor_line_candidates", 3)),
            decor_line_allow_empty=bool(narrative_raw.get("decor_line_allow_empty", True)),
            decor_line_intent_enabled=bool(narrative_raw.get("decor_line_intent_enabled", True)),
            decor_line_intent_optional=bool(narrative_raw.get("decor_line_intent_optional", True)),
            decor_line_intent_note_max_chars=int(
                narrative_raw.get("decor_line_intent_note_max_chars", 30)
            ),
            decor_line_min_fact_count=int(narrative_raw.get("decor_line_min_fact_count", 2)),
            decor_line_voice_first=bool(narrative_raw.get("decor_line_voice_first", True)),
            decor_line_llm_enabled=bool(narrative_raw.get("decor_line_llm_enabled", False)),
            decor_line_visual_facts_enabled=bool(
                narrative_raw.get("decor_line_visual_facts_enabled", True)
            ),
        ),
        llm=LlmConfig(
            provider=llm_provider,
            model=str(llm_raw.get("model") or llm_preset.get("default_model", "deepseek-chat")),
            api_key_env=str(llm_raw.get("api_key_env") or llm_preset.get("api_key_env", "DEEPSEEK_API_KEY")),
            base_url=llm_base_url,
            timeout_sec=int(llm_raw.get("timeout_sec", 120)),
            capability=normalize_tri_state(llm_raw.get("capability", "auto"), default="auto"),
            prefer_llm_when_ready=cfg_bool(
                llm_raw,
                "prefer_llm_when_ready",
                "preferLlmWhenReady",
                False,
            ),
            narrate_concurrency=cfg_int(
                llm_raw, "narrate_concurrency", "narrateConcurrency", 1
            ),
            narrate_concurrency_backoff=cfg_bool(
                llm_raw, "narrate_concurrency_backoff", "narrateConcurrencyBackoff", True
            ),
        ),
        studio=StudioConfig(
            g1_confirm_structure=bool(
                studio_raw.get("g1_confirm_structure", studio_raw.get("g1ConfirmStructure", False))
            ),
            import_dual_mode_enabled=cfg_bool(
                studio_raw, "import_dual_mode_enabled", "importDualModeEnabled", True
            ),
            success_refined_default_enabled=cfg_bool(
                studio_raw, "success_refined_default_enabled", "successRefinedDefaultEnabled", True
            ),
            import_sheet_large_enabled=cfg_bool(
                studio_raw, "import_sheet_large_enabled", "importSheetLargeEnabled", True
            ),
            layout_templates_internal=cfg_bool(
                studio_raw, "layout_templates_internal", "layoutTemplatesInternal", False
            ),
            ai_surface_enabled=cfg_bool(
                studio_raw, "ai_surface_enabled", "aiSurfaceEnabled", False
            ),
            longshot2=_parse_longshot2_config(studio_raw),
            output_recipe=_parse_output_recipe_config(studio_raw),
            gcs_poster_bric=_parse_gcs_poster_bric_config(data, studio_raw),
            portfolio_pipeline=_parse_portfolio_pipeline_config(studio_raw),
        ),
        phase6=phase6_from_dict(phase6_raw),
        template_router=TemplateRouterConfig(
            enabled=bool(template_router_raw.get("enabled", True)),
            default_template=str(
                template_router_raw.get("default_template", template_router_raw.get("defaultTemplate", "visual-journal"))
            ),
            confidence_threshold=float(
                template_router_raw.get(
                    "confidence_threshold",
                    template_router_raw.get("confidenceThreshold", 0.65),
                )
            ),
            allow_manual_override=bool(
                template_router_raw.get(
                    "allow_manual_override",
                    template_router_raw.get("allowManualOverride", True),
                )
            ),
            allowed_templates=tuple(
                str(x)
                for x in (
                    template_router_raw.get("allowed_templates")
                    or template_router_raw.get("allowedTemplates")
                    or ["visual-journal"]
                )
            ),
            beta_allowlist_trip_ids=tuple(
                str(x)
                for x in (
                    template_router_raw.get("beta_allowlist_trip_ids")
                    or template_router_raw.get("betaAllowlistTripIds")
                    or []
                )
            ),
            display_order=tuple(
                str(x)
                for x in (
                    template_router_raw.get("display_order")
                    or template_router_raw.get("displayOrder")
                    or ["visual-journal", "event-recap"]
                )
            ),
            shadow_mode=bool(
                template_router_raw.get("shadow_mode", template_router_raw.get("shadowMode", False))
            ),
            discovery_sort_mode=str(
                template_router_raw.get(
                    "discovery_sort_mode",
                    template_router_raw.get("discoverySortMode", "recommended"),
                )
            ),
        ),
        template_admin=TemplateAdminConfig(
            default_role_loopback=str(
                template_admin_raw.get("default_role_loopback", template_admin_raw.get("defaultRoleLoopback", "template_admin"))
            ),
            require_role_on_lan=bool(
                template_admin_raw.get("require_role_on_lan", template_admin_raw.get("requireRoleOnLan", True))
            ),
            lan_role=str(
                template_admin_raw.get("lan_role", template_admin_raw.get("lanRole", "template_operator"))
            ),
            require_token_on_loopback=bool(
                template_admin_raw.get(
                    "require_token_on_loopback",
                    template_admin_raw.get("requireTokenOnLoopback", False),
                )
            ),
            trust_client_role_header=bool(
                template_admin_raw.get(
                    "trust_client_role_header",
                    template_admin_raw.get("trustClientRoleHeader", True),
                )
            ),
        ),
        mosaic=mosaic_from_dict(mosaic_raw),
        cohort=CohortConfig(
            enabled=bool(cohort_raw.get("enabled", False)),
            match_threshold=float(cohort_raw.get("match_threshold", cohort_raw.get("matchThreshold", 0.78))),
            min_face_area_ratio=float(
                cohort_raw.get("min_face_area_ratio", cohort_raw.get("minFaceAreaRatio", 0.012))
            ),
            l0_face_count_fallback=bool(
                cohort_raw.get("l0_face_count_fallback", cohort_raw.get("l0FaceCountFallback", True))
            ),
            layout_weight=float(cohort_raw.get("layout_weight", cohort_raw.get("layoutWeight", 0.06))),
            mosaic_weight=float(cohort_raw.get("mosaic_weight", cohort_raw.get("mosaicWeight", 0.05))),
        ),
        aesthetic=aesthetic_from_dict(aesthetic_raw),
        title_art=title_art_config_from_dict(title_art_raw),
        cover_craft=cover_craft_config_from_dict(cover_craft_raw),
        album_editorial_lab=album_editorial_lab_from_dict(album_editorial_raw),
        ai_capability=ai_capability_config_from_dict(ai_capability_raw),
    )
    if isinstance(data, TrackedDict):
        _report_unknown_config_keys(collect_unknown_keys(data), strict=strict)
    return app_cfg
