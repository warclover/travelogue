"""Happy Path Recipe · CSC W0 read-only snapshot (PRD-COMPLETION-SURFACE-CONVERGENCE-V1).

This module declares the *current* Studio default surface as a serializable contract.
W0 does **not** change runtime behavior: ``run_trip`` / AppConfig defaults stay as-is.
Later waves may mount this recipe as SSOT and derive settings from ``l1_keys``.

ALG-V3 D5: TriState leaves are collected into ``tristate_flags`` so bool→TriState
migrations cannot silently drop keys from the enablement inventory.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any, get_args, get_origin

from travelogue.config import AppConfig
from travelogue.config._common import TriState
from travelogue.constants import (
    ADVANCED_SETTINGS_KEYS,
    L0_OPS_ROOTS,
    L1_RESULT_KEYS,
    RECIPE_ID_STUDIO_DEFAULT,
)
from travelogue.orchestrator.studio_profile import StudioProfile

_TRISTATE_VALUES = frozenset({"true", "false", "auto"})

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
# Bool paths use False; TriState paths use false/auto (ready-only) — see tier_for_flag_path.
RESEARCH_DEFAULT_FALSE: frozenset[str] = frozenset(
    {
        "aesthetic.mllm.enabled",
        "bookends.plugins.closing_vl_rerank",
        "bookends.plugins.opening_vl_rerank",
        "layout.scoring.prefix_beam_enabled",
        "narrative.decor_line_llm_enabled",
        "cull.allow_cpu_ml",
        "geocode.enabled",
        "shot_grouping.scene.adaptive_soft_split",
    }
)


def _annotation_is_tristate(annotation: object) -> bool:
    if annotation is TriState or annotation == "TriState":
        return True
    if isinstance(annotation, str):
        return "TriState" in annotation or (
            "true" in annotation and "false" in annotation and "auto" in annotation
        )
    origin = get_origin(annotation)
    if origin is not None:
        # typing.Literal["true", "false", "auto"] (TriState alias)
        args = set(get_args(annotation))
        if args and args <= _TRISTATE_VALUES and len(args) == 3:
            return True
    return False


def iter_bool_paths(obj: Any, prefix: str = "") -> list[tuple[str, bool]]:
    """Walk a dataclass tree and collect ``path -> bool`` leaves."""
    bools, _tris = iter_flag_paths(obj, prefix=prefix)
    return bools


def iter_flag_paths(
    obj: Any, prefix: str = ""
) -> tuple[list[tuple[str, bool]], list[tuple[str, str]]]:
    """Walk a dataclass tree; collect bool leaves and TriState string leaves.

    TriState fields are identified by annotation (not by value alone), so a
    bool→TriState migration cannot drop the key from the inventory.
    """
    if not is_dataclass(obj):
        return [], []
    bools: list[tuple[str, bool]] = []
    tris: list[tuple[str, str]] = []
    for f in fields(obj):
        value = getattr(obj, f.name)
        path = f"{prefix}.{f.name}" if prefix else f.name
        if _annotation_is_tristate(f.type):
            tris.append((path, str(value).strip().lower()))
        elif isinstance(value, bool):
            bools.append((path, value))
        elif is_dataclass(value):
            sub_b, sub_t = iter_flag_paths(value, path)
            bools.extend(sub_b)
            tris.extend(sub_t)
    return bools, tris


def appconfig_bool_map(cfg: AppConfig | None = None) -> dict[str, bool]:
    cfg = cfg if cfg is not None else AppConfig()
    return {path: value for path, value in sorted(iter_bool_paths(cfg))}


def appconfig_tristate_map(cfg: AppConfig | None = None) -> dict[str, str]:
    cfg = cfg if cfg is not None else AppConfig()
    _bools, tris = iter_flag_paths(cfg)
    return {path: value for path, value in sorted(tris)}


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
    return tier_for_flag_path(path, default_value=default_value)


def tier_for_flag_path(path: str, *, default_value: bool | str) -> str:
    """Tier label for bool or TriState inventory paths (ALG-V3 D5)."""
    if path in DANGER_DEFAULT_FALSE:
        return "danger"
    if path in RESEARCH_DEFAULT_FALSE:
        return "research"
    if isinstance(default_value, str):
        # TriState: only "true" is happy-path-candidate; false/auto stay advanced
        if default_value == "true":
            return "happy_path_candidate"
        return "advanced_or_research"
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
    tris = appconfig_tristate_map(cfg)
    true_paths = [p for p, v in bools.items() if v]
    false_paths = [p for p, v in bools.items() if not v]
    tiers = {p: tier_for_flag_path(p, default_value=v) for p, v in bools.items()}
    for p, v in tris.items():
        tiers[p] = tier_for_flag_path(p, default_value=v)
    return {
        "recipe_id": RECIPE_ID_STUDIO_DEFAULT,
        "schema_version": 1,
        "note": (
            "CSC W0 read-only snapshot. Runtime still uses AppConfig + "
            "StudioProfile.studio_default(); this document does not enforce yet. "
            "ALG-V3 D5: TriState leaves live in tristate_flags."
        ),
        "orchestration": orchestration_snapshot(profile),
        "layout_exit": {
            "studio_export_layout": str(profile.export_layout),
            "web_layout_engine_config": str(cfg.layout.web_layout_engine),
            "note": "mobile→legacy / web|auto→config; strangler incomplete (CSC root-cause).",
        },
        "appconfig_bools": bools,
        "tristate_flags": tris,
        "counts": {
            "bool_fields": len(bools),
            "default_true": len(true_paths),
            "default_false": len(false_paths),
            "tristate_fields": len(tris),
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
