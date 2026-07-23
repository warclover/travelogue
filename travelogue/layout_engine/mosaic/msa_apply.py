"""MSA · apply parametric instance onto solidified screens (S-MSA-05)."""

from __future__ import annotations

from typing import Any

from travelogue.config.mosaic import (
    SlotAdaptationConfig,
    effective_slot_adaptation_enabled,
)
from travelogue.layout_engine.mosaic.msa_profile import MsaProfile, build_msa_profile
from travelogue.layout_engine.mosaic.msa_solve import (
    MSA_M1_PATTERN_WHITELIST,
    solve_all_variants,
    stage_track_lists,
)
from travelogue.layout_engine.mosaic.runtime import get_effective_mosaic_config
from travelogue.layout_templates.geometry import slot_display_aspect
from travelogue.layout_templates.models import TemplateStage
from travelogue.layout_templates.registry import get_engine


def _window_assets(
    screen: dict[str, Any], assets_map: dict[str, Any] | None
) -> list[dict[str, Any]]:
    assets_map = assets_map or {}
    out: list[dict[str, Any]] = []
    for slot in screen.get("slots") or []:
        aid = slot.get("assetId")
        if not aid:
            continue
        asset = assets_map.get(aid)
        if isinstance(asset, dict):
            out.append(asset)
        else:
            out.append({"id": aid})
    return out


def _primary_layout_key(variant_results: dict[str, Any]) -> str:
    if "web" in variant_results:
        return "web"
    if "default" in variant_results:
        return "default"
    return next(iter(variant_results))


def maybe_apply_slot_adaptation(
    screen: dict[str, Any],
    pattern_id: str,
    *,
    assets_map: dict[str, Any] | None = None,
    cfg: Any | None = None,
) -> dict[str, Any]:
    """Persist trackOverride + refresh displayAspect when MSA parent is ON.

    Parent OFF ⇒ zero writes (AC-MSA-01). Returns a log-facing summary dict.
    """
    mosaic_cfg = cfg if cfg is not None else get_effective_mosaic_config()
    summary: dict[str, Any] = {
        "msaProfile": None,
        "rHeroTarget": None,
        "trackOverride": None,
        "slotFits": None,
        "msaOutcome": "skipped_parent_off",
        "cropRisk": None,
        "whitespaceRatio": None,
    }
    if not effective_slot_adaptation_enabled(mosaic_cfg):
        return summary

    sa: SlotAdaptationConfig = getattr(mosaic_cfg, "slot_adaptation", None) or SlotAdaptationConfig()
    try:
        template = get_engine().get(pattern_id)
    except KeyError:
        summary["msaOutcome"] = "msa_solve_miss"
        return summary

    if pattern_id not in MSA_M1_PATTERN_WHITELIST:
        summary["msaOutcome"] = "skipped_not_whitelisted"
        return summary

    assets = _window_assets(screen, assets_map)
    profile: MsaProfile = build_msa_profile(assets, cfg=sa)
    summary["msaProfile"] = profile.to_dict()
    summary["rHeroTarget"] = profile.r_hero_target

    if profile.r_hero_target is None:
        summary["msaOutcome"] = "msa_solve_miss"
        return summary

    variant_results = solve_all_variants(
        template, r_hero_target=float(profile.r_hero_target), cfg=sa
    )
    by_variant: dict[str, Any] = {}
    any_ok = False
    for layout, result in variant_results.items():
        entry = {
            "ok": result.ok,
            "reason": result.reason,
            "cols": list(result.cols),
            "rows": list(result.rows),
            "mainDisplayAspect": result.main_display_aspect,
            "mainArea": result.main_area,
        }
        by_variant[layout] = entry
        if result.ok:
            any_ok = True

    primary = _primary_layout_key(variant_results)
    primary_result = variant_results[primary]
    geo = screen.setdefault("layoutGeometry", {})
    base_cols, base_rows = stage_track_lists(template.stage)

    if primary_result.ok:
        track = {"cols": list(primary_result.cols), "rows": list(primary_result.rows)}
        geo["trackOverride"] = track
        geo["cols"] = list(track["cols"])
        geo["rows"] = list(track["rows"])
        summary["trackOverride"] = dict(track)
        summary["msaOutcome"] = "applied"
        stage = TemplateStage(
            aspect=template.stage.aspect,
            cols=tuple(track["cols"]),
            rows=tuple(track["rows"]),
            gap=template.stage.gap,
        )
    else:
        # Miss: keep solidified static tracks; do not invent override (D-MSA-09).
        geo.pop("trackOverride", None)
        geo["cols"] = list(base_cols)
        geo["rows"] = list(base_rows)
        summary["trackOverride"] = None
        summary["msaOutcome"] = "msa_solve_miss"
        stage = TemplateStage(
            aspect=template.stage.aspect,
            cols=tuple(base_cols),
            rows=tuple(base_rows),
            gap=template.stage.gap,
        )

    if by_variant:
        geo["trackOverrideByVariant"] = {
            k: (
                {"cols": v["cols"], "rows": v["rows"]}
                if v.get("ok")
                else {"miss": True, "reason": v.get("reason")}
            )
            for k, v in by_variant.items()
        }
        # Per-variant miss telemetry (BLK-04)
        summary["variantOutcomes"] = {
            k: ("applied" if v.get("ok") else "msa_solve_miss") for k, v in by_variant.items()
        }

    slot_by_index = {s.index: s for s in template.slots}
    slot_fits: list[str] = []
    for slot in screen.get("slots") or []:
        idx = int(slot.get("slot", -1))
        meta = slot_by_index.get(idx)
        if meta is None:
            slot_fits.append(str(slot.get("fit") or "cover"))
            continue
        slot["displayAspect"] = round(slot_display_aspect(meta.rect, stage), 4)
        fit = str(slot.get("fit") or "cover")
        slot_fits.append(fit)
    summary["slotFits"] = slot_fits

    # Persist a compact msa blob for compose → MosaicWindowLog
    geo["msa"] = {
        "outcome": summary["msaOutcome"],
        "profile": summary["msaProfile"],
        "rHeroTarget": summary["rHeroTarget"],
        "variantOutcomes": summary.get("variantOutcomes"),
    }
    # any_ok unused for primary-path outcome; kept for future multi-variant OR
    _ = any_ok
    return summary
