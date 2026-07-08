"""MCS ↔ LTE adapter (PRD §3.3, T6)."""

from __future__ import annotations

from travelogue.config import AppConfig, MosaicConfig, get_config
from travelogue.layout_engine.mosaic.pattern_catalog import MosaicPattern, default_registry


def read_templates_from_lte(cfg: AppConfig | None = None) -> bool:
    app = cfg or get_config()
    te = getattr(app.layout, "template_engine", None)
    if te is None or not getattr(te, "enabled", True):
        return False
    return bool(getattr(te, "read_templates_from_lte", False))


def lte_rollout_eligible(pattern_id: str) -> bool:
    """LTE extras with rollout.percent<=0 stay out of MCS until enabled (W3 parity)."""
    if not read_templates_from_lte():
        return True
    try:
        from travelogue.layout_templates.registry import get_engine

        tpl = get_engine().get(pattern_id)
    except KeyError:
        return True
    rollout = tpl.rollout or {}
    try:
        pct = int(rollout.get("percent", 100))
    except (TypeError, ValueError):
        pct = 100
    return pct > 0


def mosaic_registry(cfg: AppConfig | None = None) -> dict[str, MosaicPattern]:
    """Return MosaicPattern registry for MCS candidate generation."""
    if not read_templates_from_lte(cfg):
        return default_registry()
    from travelogue.layout_templates.legacy_bridge import export_mosaic_pattern
    from travelogue.layout_templates.registry import get_engine

    patterns: dict[str, MosaicPattern] = {
        t.id: export_mosaic_pattern(t) for t in get_engine().list_active()
    }
    app = cfg or get_config()
    te = getattr(app.layout, "template_engine", None)
    if te is not None:
        for pid in getattr(te, "overrides_disable", ()) or ():
            patterns.pop(str(pid), None)
    from travelogue.layout_engine.mosaic.runtime import get_mosaic_disabled_patterns

    for pid in get_mosaic_disabled_patterns():
        patterns.pop(str(pid), None)
    return patterns


def _lte_template(pattern_id: str):
    from travelogue.layout_templates.registry import get_engine

    return get_engine().get(pattern_id)


def _runtime_base_weight_override(pattern_id: str) -> float | None:
    """Approved runtime weights from config_governance (§9.4)."""
    from travelogue.templating.admin_store import load_runtime

    runtime = load_runtime()
    overrides = runtime.get("layout_template_base_weights") or {}
    if not isinstance(overrides, dict):
        return None
    raw = overrides.get(pattern_id)
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def template_base_weight(pattern_id: str, *, cfg: AppConfig | None = None) -> float:
    """LTE scoring.base_weight multiplier (1.0 when LTE off or unknown).

    The LTE switch is checked first so that disabling read_templates_from_lte
    fully restores P15 weighting — runtime governance overrides only apply
    while the engine is enabled.
    """
    if not read_templates_from_lte(cfg):
        return 1.0
    runtime_w = _runtime_base_weight_override(pattern_id)
    if runtime_w is not None:
        return runtime_w
    try:
        tpl = _lte_template(pattern_id)
    except KeyError:
        return 1.0
    try:
        return float((tpl.scoring or {}).get("base_weight") or 1.0)
    except (TypeError, ValueError):
        return 1.0


def mcs_diversity_config(*, cfg: AppConfig | None = None) -> dict[str, float | str]:
    """§9.4 MCS candidate diversity (off | mmr | dpp)."""
    defaults: dict[str, float | str] = {"mode": "mmr", "lambda": 0.65}
    if not read_templates_from_lte(cfg):
        return defaults
    from pathlib import Path

    import yaml

    app = cfg or get_config()
    te = getattr(app.layout, "template_engine", None)
    if te is not None:
        cfg_mode = getattr(te, "diversity_mode", None)
        if cfg_mode in ("off", "mmr", "dpp"):
            out: dict[str, float | str] = {"mode": str(cfg_mode)}
            cfg_lambda = getattr(te, "diversity_lambda", None)
            if cfg_lambda is not None:
                try:
                    out["lambda"] = float(cfg_lambda)
                except (TypeError, ValueError):
                    out["lambda"] = float(defaults["lambda"])
            else:
                out["lambda"] = float(defaults["lambda"])
            return out
    policy_path = Path(getattr(te, "policy_path", "travelogue/layout_templates/lte_policy.yaml"))
    if not policy_path.is_file():
        return defaults
    try:
        doc = yaml.safe_load(policy_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return defaults
    mcs = doc.get("mcs_integration") or {}
    scoring = mcs.get("scoring") if isinstance(mcs.get("scoring"), dict) else {}
    diversity = scoring.get("diversity") if isinstance(scoring.get("diversity"), dict) else {}
    mode = str(diversity.get("mode", defaults["mode"])).strip().lower()
    if mode not in ("off", "mmr", "dpp"):
        mode = str(defaults["mode"])
    out: dict[str, float | str] = {"mode": mode}
    try:
        out["lambda"] = float(diversity.get("lambda", defaults["lambda"]))
    except (TypeError, ValueError):
        out["lambda"] = float(defaults["lambda"])
    return out


def template_rhythm_max_per_chapter(pattern_id: str, *, cfg: AppConfig | None = None) -> int | None:
    """LTE scoring.rhythm.max_per_chapter cap (None = no LTE cap)."""
    if not read_templates_from_lte(cfg):
        return None
    try:
        tpl = _lte_template(pattern_id)
    except KeyError:
        return None
    rhythm = (tpl.scoring or {}).get("rhythm") or {}
    if not isinstance(rhythm, dict):
        return None
    raw = rhythm.get("max_per_chapter")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def template_diversity_bonus(pattern_id: str, *, cfg: AppConfig | None = None) -> float:
    """LTE scoring.rhythm.diversity_bonus multiplier bump (0 when LTE off)."""
    if not read_templates_from_lte(cfg):
        return 0.0
    try:
        tpl = _lte_template(pattern_id)
    except KeyError:
        return 0.0
    rhythm = (tpl.scoring or {}).get("rhythm") or {}
    if not isinstance(rhythm, dict):
        return 0.0
    raw = rhythm.get("diversity_bonus")
    if raw is None:
        return 0.0
    try:
        return max(0.0, float(raw))
    except (TypeError, ValueError):
        return 0.0


def resolve_render_grid_class(pattern_id: str, *, cfg: AppConfig | None = None) -> str | None:
    """Resolve grid CSS class from LTE YAML or legacy constants."""
    if read_templates_from_lte(cfg):
        try:
            return _lte_template(pattern_id).render_grid_class
        except KeyError:
            pass
    from travelogue.layout_engine.mosaic.constants import PATTERN_GRID_CLASS

    gc = PATTERN_GRID_CLASS.get(pattern_id)
    if gc:
        return gc
    from travelogue.layout_engine.planner.screen_planner import PATTERN_GRID_CLASS as planner_classes

    return planner_classes.get(pattern_id)


def resolve_slot_fit(
    pattern_id: str,
    slot_index: int,
    role: str,
    asset: dict | None,
    *,
    cfg: AppConfig | None = None,
) -> str:
    """R-P16-06 fit layer L1: LTE slot fit → curate applies before render."""
    from travelogue.curation.asset_subject import portrait_fit_for_asset

    asset = asset or {}
    default = portrait_fit_for_asset(asset, default="cover") if role == "portrait" else "cover"
    if not read_templates_from_lte(cfg):
        return default
    try:
        tpl = _lte_template(pattern_id)
    except KeyError:
        return default
    slot_meta = next((s for s in tpl.slots if s.index == slot_index), None)
    if slot_meta is None:
        return default
    declared = slot_meta.fit or tpl.render_fit_policy or "auto"
    hints = tpl.compatibility_hints or {}
    hint_fit = hints.get("fit") or hints.get("defaultFit")
    if declared == "auto" and hint_fit:
        declared = str(hint_fit)
    if declared == "auto":
        return default
    return str(declared)


def _mosaic_slot_count(pattern_id: str) -> int | None:
    from travelogue.layout_contract.rhythm import pattern_slot_count

    n = pattern_slot_count(pattern_id)
    if n is not None:
        return n
    if read_templates_from_lte():
        try:
            tpl = _lte_template(pattern_id)
            return tpl.photo_count_max
        except KeyError:
            pass
    from travelogue.layout_engine.mosaic.pattern_catalog import default_registry

    pat = default_registry().get(pattern_id)
    return pat.slot_count if pat else None


def mosaic_pattern_disabled(
    pattern_id: str,
    *,
    cfg: MosaicConfig | None = None,
) -> bool:
    """True when patternId must not be emitted (LTE status/overrides + window-size gates)."""
    from travelogue.layout_engine.mosaic.runtime import (
        get_effective_mosaic_config,
        mosaic_window_size_enabled,
    )

    app = get_config()
    mosaic_cfg = cfg or get_effective_mosaic_config()

    if read_templates_from_lte(app):
        try:
            tpl = _lte_template(pattern_id)
            if tpl.status in ("deprecated", "disabled"):
                return True
        except KeyError:
            pass
        if not lte_rollout_eligible(pattern_id):
            return True
        te = getattr(app.layout, "template_engine", None)
        if te is not None:
            disabled = getattr(te, "overrides_disable", ()) or ()
            if pattern_id in disabled:
                return True
    else:
        from travelogue.layout_engine.mosaic.constants import (
            PATTERN_MOSAIC_5_2P_3L_BALANCED,
            PATTERN_MOSAIC_5_MAIN_LAND_2P_2L,
        )

        if pattern_id in (
            PATTERN_MOSAIC_5_2P_3L_BALANCED,
            PATTERN_MOSAIC_5_MAIN_LAND_2P_2L,
        ):
            return True

    if mosaic_cfg is None:
        return False
    n = _mosaic_slot_count(pattern_id)
    if n == 5 and not mosaic_window_size_enabled(5, mosaic_cfg):
        return True
    if n == 6 and not mosaic_window_size_enabled(6, mosaic_cfg):
        return True
    max_slots = int(getattr(getattr(app.layout, "template_engine", None), "max_mosaic_slots", 9) or 9)
    if n is not None and n > max_slots:
        return True
    return False
