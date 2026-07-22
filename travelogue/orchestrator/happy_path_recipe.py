"""Happy Path Recipe · CSC W0 read-only snapshot (PRD-COMPLETION-SURFACE-CONVERGENCE-V1).

This module declares the *current* Studio default surface as a serializable contract.
W0 does **not** change runtime behavior: ``run_trip`` / AppConfig defaults stay as-is.
Later waves may mount this recipe as SSOT and derive settings from ``l1_keys``.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any

from travelogue.config import AppConfig
from travelogue.orchestrator.studio_profile import StudioProfile

RECIPE_ID_STUDIO_DEFAULT = "studio_default"

# CSC §0.0.1 Danger tier · must remain default False on Happy Path.
DANGER_DEFAULT_FALSE: frozenset[str] = frozenset(
    {
        "studio.g1_confirm_structure",
        "mosaic.allow_drop",
        "clustering.force_recluster",
        "layout.strategy_engine.enabled",
        "studio.layout_templates_internal",
    }
)

# Initial Research tier seeds (firewall False · not a backlog to enable).
RESEARCH_DEFAULT_FALSE: frozenset[str] = frozenset(
    {
        "aesthetic.mllm.enabled",
        "bookends.plugins.closing_vl_rerank",
        "bookends.plugins.opening_vl_rerank",
        "layout.scoring.prefix_beam_enabled",
        "narrative.decor_line_llm_enabled",
        "cull.allow_cpu_ml",
        "geocode.enabled",
    }
)

# Config top-level ops roots (L0) · not counted in L1≤10 budget (CSC D-CSC-04).
L0_OPS_ROOTS: tuple[str, ...] = (
    "trips_dir",
    "llm",
    "ffmpeg",
    "geocode",
)

# W1 target: user-visible result knobs (≤10). Settings UI should prefer these.
# Paths are AppConfig-ish; TriState UI maps onto *.enabled where noted.
L1_RESULT_KEYS: tuple[str, ...] = (
    "clustering.enabled",
    "vision.enabled",
    "ingest.copy_source_files",
)

# Visible in settings but must stay Advanced / Danger (not L1).
ADVANCED_SETTINGS_KEYS: tuple[str, ...] = (
    "layout.scoring.enabled",
    "studio.g1_confirm_structure",
)


def iter_bool_paths(obj: Any, prefix: str = "") -> list[tuple[str, bool]]:
    """Walk a dataclass tree and collect ``path -> bool`` leaves."""
    if not is_dataclass(obj):
        return []
    out: list[tuple[str, bool]] = []
    for f in fields(obj):
        value = getattr(obj, f.name)
        path = f"{prefix}.{f.name}" if prefix else f.name
        if isinstance(value, bool):
            out.append((path, value))
        elif is_dataclass(value):
            out.extend(iter_bool_paths(value, path))
    return out


def appconfig_bool_map(cfg: AppConfig | None = None) -> dict[str, bool]:
    cfg = cfg if cfg is not None else AppConfig()
    return {path: value for path, value in sorted(iter_bool_paths(cfg))}


def orchestration_snapshot(profile: StudioProfile | None = None) -> dict[str, Any]:
    """Thin orchestration face of ``StudioProfile`` (not full AppConfig)."""
    profile = profile if profile is not None else StudioProfile.studio_default()
    return {
        "run_clustering": bool(profile.run_clustering),
        "apply_editorial_hints": bool(profile.apply_editorial_hints),
        "export_layout": str(profile.export_layout),
        "apply_layout_on_curate": bool(profile.apply_layout_on_curate),
        "ingest": {
            "resume_ingest": bool(profile.ingest.resume_ingest),
            "use_parallel_embed": bool(profile.ingest.use_parallel_embed),
        },
    }


def tier_for_bool_path(path: str, *, default_value: bool) -> str:
    """Best-effort W0 tier label (human refinement continues in inventory docs)."""
    if path in DANGER_DEFAULT_FALSE:
        return "danger"
    if path in RESEARCH_DEFAULT_FALSE:
        return "research"
    if not default_value:
        return "advanced_or_research"
    return "happy_path_candidate"


def build_happy_path_recipe(
    *,
    cfg: AppConfig | None = None,
    profile: StudioProfile | None = None,
) -> dict[str, Any]:
    """Build JSON-serializable Happy Path Recipe snapshot (read-only contract)."""
    cfg = cfg if cfg is not None else AppConfig()
    profile = profile if profile is not None else StudioProfile.studio_default()
    bools = appconfig_bool_map(cfg)
    true_paths = [p for p, v in bools.items() if v]
    false_paths = [p for p, v in bools.items() if not v]
    tiers = {p: tier_for_bool_path(p, default_value=v) for p, v in bools.items()}
    return {
        "recipe_id": RECIPE_ID_STUDIO_DEFAULT,
        "schema_version": 1,
        "note": (
            "CSC W0 read-only snapshot. Runtime still uses AppConfig + "
            "StudioProfile.studio_default(); this document does not enforce yet."
        ),
        "orchestration": orchestration_snapshot(profile),
        "layout_exit": {
            "studio_export_layout": str(profile.export_layout),
            "web_layout_engine_config": str(cfg.layout.web_layout_engine),
            "note": "mobile→legacy / web|auto→config; strangler incomplete (CSC root-cause).",
        },
        "appconfig_bools": bools,
        "counts": {
            "bool_fields": len(bools),
            "default_true": len(true_paths),
            "default_false": len(false_paths),
        },
        "tiers": tiers,
        "l0_ops_roots": list(L0_OPS_ROOTS),
        "l1_keys": list(L1_RESULT_KEYS),
        "advanced_settings_keys": list(ADVANCED_SETTINGS_KEYS),
        "advanced": sorted(
            p for p, t in tiers.items() if t in {"advanced_or_research", "research", "danger"}
        ),
        "danger_must_stay_false": sorted(DANGER_DEFAULT_FALSE),
        "settings_inventory": (
            "docs/acceptance-records/csc-w0-settings-surface-inventory.md"
        ),
    }


def studio_default_recipe() -> dict[str, Any]:
    """Canonical Studio Happy Path recipe (``recipe_id=studio_default``)."""
    return build_happy_path_recipe()
