"""YAML config loading and Studio patch helpers."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from travelogue.config._common import normalize_arc_mode, normalize_narrative_scope, yaml
from travelogue.config.aesthetic import aesthetic_from_dict
from travelogue.config.app import AppConfig
from travelogue.config.clustering import GeocodeConfig, clustering_from_dict
from travelogue.config.cohort import CohortConfig
from travelogue.config.cull import cull_from_dict
from travelogue.config.curate import CurateConfig, cover_scoring_v2_from_dict
from travelogue.config.ingest import ingest_from_dict
from travelogue.config.moment import moment_config_from_dict
from travelogue.config.layout import (
    LayoutConfig,
    layout_feedback_from_dict,
    layout_rhythm_from_dict,
    layout_scoring_from_dict,
    layout_strategy_engine_from_dict,
    layout_template_engine_from_dict,
)
from travelogue.config.misc import (
    ExportConfig,
    LlmConfig,
    NarrativeConfig,
    pipeline_from_dict,
    render_from_dict,
)
from travelogue.config.mosaic import mosaic_from_dict
from travelogue.config.phase6 import phase6_from_dict
from travelogue.config.studio import StudioConfig
from travelogue.config.template import TemplateAdminConfig, TemplateRouterConfig
from travelogue.config.vision import vision_from_dict
from travelogue.config_helpers import cfg_bool
from travelogue.curation.cover_scoring_params import CoverScoringParams
from travelogue.llm.presets import PROVIDER_PRESETS
from travelogue.paths import ROOT

_log = logging.getLogger(__name__)

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


def patch_config_file(path: Path, patch: dict[str, Any]) -> None:
    """Merge whitelisted keys into config.yaml on disk."""
    if yaml is None:
        raise RuntimeError("PyYAML required to patch config")
    data: dict[str, Any] = {}
    if path.is_file():
        with path.open(encoding="utf-8") as f:
            loaded = yaml.safe_load(f) or {}
            if isinstance(loaded, dict):
                data = loaded
    allowed_clustering = {"enabled", "segmentCurateMode", "sceneClusterMode"}
    allowed_vision = {"enabled"}
    allowed_layout_scoring = {"enabled"}
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
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def load_config(path: Path | None = None) -> AppConfig:
    """Load config.yaml from path, or ./config.yaml, or defaults."""
    candidates = [path, Path.cwd() / "config.yaml", ROOT / "config.yaml"]
    cfg_path = next((p for p in candidates if p and p.is_file()), None)
    data: dict[str, Any] = {}
    if cfg_path and yaml is not None:
        with cfg_path.open(encoding="utf-8") as f:
            loaded = yaml.safe_load(f) or {}
            if isinstance(loaded, dict):
                data = loaded
    trips = data.get("trips_dir", "./trips")
    trips_dir = Path(trips)
    if not trips_dir.is_absolute():
        base = Path.cwd()
        try:
            from travelogue.desktop.bundle import exe_dir, is_frozen

            if is_frozen():
                base = exe_dir()
        except Exception:
            _log.debug("frozen exe_dir lookup failed; using cwd for trips_dir", exc_info=True)
        trips_dir = (base / trips_dir).resolve()
    ingest_raw = data.get("ingest") if isinstance(data.get("ingest"), dict) else {}
    layout_raw = data.get("layout") if isinstance(data.get("layout"), dict) else {}
    web_engine = str(layout_raw.get("web_layout_engine", "screens")).strip().lower()
    if web_engine not in ("legacy", "screens"):
        web_engine = "screens"
    scope = str(layout_raw.get("screen_plan_scope", "day")).strip().lower()
    if scope not in ("chapter", "day"):
        scope = "day"
    mixed_gap = float(layout_raw.get("mixed_proximity_seconds", 12.0))
    layout_density_top = data.get("layoutDensity") if isinstance(data.get("layoutDensity"), dict) else {}
    layout_density_enabled = bool(
        layout_density_top.get("enabled", layout_raw.get("layout_density_enabled", True))
    )
    scoring_raw = layout_raw.get("scoring") if isinstance(layout_raw.get("scoring"), dict) else {}
    rhythm_raw = layout_raw.get("rhythm") if isinstance(layout_raw.get("rhythm"), dict) else {}
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
    vision_raw = data.get("vision") if isinstance(data.get("vision"), dict) else {}
    narrative_raw = data.get("narrative") if isinstance(data.get("narrative"), dict) else {}
    llm_raw = data.get("llm") if isinstance(data.get("llm"), dict) else {}
    geocode_raw = data.get("geocode") if isinstance(data.get("geocode"), dict) else {}
    curate_raw = data.get("curate") if isinstance(data.get("curate"), dict) else {}
    curate_layout_raw = curate_raw.get("layout") if isinstance(curate_raw.get("layout"), dict) else {}
    render_raw = data.get("render") if isinstance(data.get("render"), dict) else {}
    clustering_raw = data.get("clustering") if isinstance(data.get("clustering"), dict) else {}
    pipeline_raw = data.get("pipeline") if isinstance(data.get("pipeline"), dict) else {}
    cull_raw = data.get("cull") if isinstance(data.get("cull"), dict) else {}
    studio_raw = data.get("studio") if isinstance(data.get("studio"), dict) else {}
    phase6_raw = data.get("phase6") if isinstance(data.get("phase6"), dict) else {}
    template_router_raw = data.get("template_router") if isinstance(data.get("template_router"), dict) else {}
    template_admin_raw = data.get("template_admin") if isinstance(data.get("template_admin"), dict) else {}
    cohort_raw = data.get("cohort") if isinstance(data.get("cohort"), dict) else {}
    aesthetic_raw = data.get("aesthetic") if isinstance(data.get("aesthetic"), dict) else {}
    mosaic_raw = data.get("mosaic") if isinstance(data.get("mosaic"), dict) else {}
    layout_top = data.get("layout") if isinstance(data.get("layout"), dict) else {}
    mosaic_v2 = layout_top.get("mosaic_v2") if isinstance(layout_top.get("mosaic_v2"), dict) else {}
    if mosaic_v2:
        mosaic_raw = {**mosaic_v2, **mosaic_raw}
    banned_raw = narrative_raw.get("banned_phrases") or []
    banned = tuple(str(p) for p in banned_raw if p) if isinstance(banned_raw, list) else ()
    llm_provider = str(llm_raw.get("provider", "stub")).strip().lower()
    if llm_provider not in ("stub", "deepseek", "dashscope"):
        llm_provider = "stub"
    llm_preset = PROVIDER_PRESETS.get(llm_provider, {})
    llm_base = llm_raw.get("base_url")
    llm_base_url = str(llm_base).strip() if llm_base else None
    return AppConfig(
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
            rhythm=layout_rhythm_from_dict(rhythm_raw),
            template_engine=layout_template_engine_from_dict(template_engine_raw),
            strategy_engine=layout_strategy_engine_from_dict(strategy_engine_raw),
            scoring=layout_scoring_from_dict(scoring_raw),
            feedback=layout_feedback_from_dict(feedback_raw),
        ),
        clustering=clustering_from_dict(clustering_raw),
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
            moment=moment_config_from_dict(
                curate_raw.get("moment") if isinstance(curate_raw.get("moment"), dict) else {}
            ),
        ),
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
    )
