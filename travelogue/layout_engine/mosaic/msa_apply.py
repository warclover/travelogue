"""MSA · apply parametric instance onto solidified screens (S-MSA-05)."""

from __future__ import annotations

from typing import Any

from travelogue.config.mosaic import (
    SlotAdaptationConfig,
    effective_slot_adaptation_enabled,
)
from travelogue.layout_engine.mosaic.msa_assign import refine_aux_assignment
from travelogue.layout_engine.mosaic.msa_fit import apply_crop_risk_fits
from travelogue.layout_engine.mosaic.msa_profile import MsaProfile, build_msa_profile
from travelogue.layout_engine.mosaic.msa_solve import (
    MSA_M1_PATTERN_WHITELIST,
    resolve_main_r_star,
    slot_area_fraction,
    solve_all_variants,
    solve_track_override,
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


def _refresh_display_aspects(
    screen: dict[str, Any],
    template: Any,
    stage: TemplateStage,
    cols: list[float],
    rows: list[float],
) -> list[float]:
    slot_by_index = {s.index: s for s in template.slots}
    slot_areas: list[float] = []
    for slot in screen.get("slots") or []:
        idx = int(slot.get("slot", -1))
        meta = slot_by_index.get(idx)
        if meta is None:
            slot_areas.append(0.0)
            continue
        slot["displayAspect"] = round(slot_display_aspect(meta.rect, stage), 4)
        slot_areas.append(slot_area_fraction(meta.rect, cols, rows))
    return slot_areas


def maybe_apply_slot_adaptation(
    screen: dict[str, Any],
    pattern_id: str,
    *,
    assets_map: dict[str, Any] | None = None,
    cfg: Any | None = None,
) -> dict[str, Any]:
    """Persist trackOverride + fit/contain when MSA parent is ON.

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

    r_star = resolve_main_r_star(
        template, r_land=profile.r_hero_target, r_port=profile.r_port_target
    )
    summary["rHeroTarget"] = r_star
    if r_star is None:
        summary["msaOutcome"] = "msa_solve_miss"
        return summary

    variant_results = solve_all_variants(
        template, r_hero_target=float(r_star), cfg=sa
    )
    by_variant: dict[str, Any] = {}
    for layout, result in variant_results.items():
        by_variant[layout] = {
            "ok": result.ok,
            "reason": result.reason,
            "cols": list(result.cols),
            "rows": list(result.rows),
            "mainDisplayAspect": result.main_display_aspect,
            "mainArea": result.main_area,
        }

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
        cols, rows = list(track["cols"]), list(track["rows"])
    else:
        geo.pop("trackOverride", None)
        geo["cols"] = list(base_cols)
        geo["rows"] = list(base_rows)
        summary["trackOverride"] = None
        summary["msaOutcome"] = "msa_solve_miss"
        cols, rows = list(base_cols), list(base_rows)

    stage = TemplateStage(
        aspect=template.stage.aspect,
        cols=tuple(cols),
        rows=tuple(rows),
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
        summary["variantOutcomes"] = {
            k: ("applied" if v.get("ok") else "msa_solve_miss") for k, v in by_variant.items()
        }

    slot_areas = _refresh_display_aspects(screen, template, stage, cols, rows)
    swapped = refine_aux_assignment(screen, assets_map=assets_map or {})
    summary["auxSwap"] = bool(swapped)

    risks, whitespace = apply_crop_risk_fits(
        screen,
        assets_map=assets_map or {},
        slot_areas=slot_areas,
        cfg=sa,
    )

    # D-06 · if high crop_risk remains cover-only due to budget, one re-solve toward
    # the riskiest landscape photo AR (land-main families), then re-fit once.
    theta = float(sa.crop_risk_contain_threshold)
    n_contain = sum(1 for s in screen.get("slots") or [] if s.get("msaContain"))
    whitespace_capped = bool(
        risks and max(risks) >= theta - 1e-9 and n_contain == 0 and whitespace <= 1e-9
    )
    if whitespace_capped and profile.r_hero_target is not None:
        # Bias toward riskiest land asset AR if available
        bias_r = float(profile.r_hero_target)
        worst_i = max(range(len(risks)), key=lambda i: risks[i])
        slots = screen.get("slots") or []
        if 0 <= worst_i < len(slots):
            aid = slots[worst_i].get("assetId")
            asset = (assets_map or {}).get(aid) if aid else None
            if isinstance(asset, dict):
                try:
                    wr = float(asset["width"]) / float(asset["height"])
                    if wr > 1.05:
                        bias_r = wr
                except (TypeError, ValueError, KeyError, ZeroDivisionError):
                    pass
        retry = solve_track_override(
            template, r_hero_target=bias_r, stage_aspect=template.stage.aspect, cfg=sa
        )
        if retry.ok:
            track = {"cols": list(retry.cols), "rows": list(retry.rows)}
            geo["trackOverride"] = track
            geo["cols"] = list(track["cols"])
            geo["rows"] = list(track["rows"])
            summary["trackOverride"] = dict(track)
            summary["msaOutcome"] = "applied"
            summary["whitespaceResolve"] = True
            cols, rows = list(track["cols"]), list(track["rows"])
            stage = TemplateStage(
                aspect=template.stage.aspect,
                cols=tuple(cols),
                rows=tuple(rows),
                gap=template.stage.gap,
            )
            slot_areas = _refresh_display_aspects(screen, template, stage, cols, rows)
            # Reset MSA contain flags before second fit pass
            for s in screen.get("slots") or []:
                if s.get("msaContain"):
                    s.pop("msaContain", None)
                    if str(s.get("fit")) == "contain":
                        s["fit"] = "cover"
            risks, whitespace = apply_crop_risk_fits(
                screen,
                assets_map=assets_map or {},
                slot_areas=slot_areas,
                cfg=sa,
            )
            whitespace_capped = bool(
                risks
                and max(risks) >= theta - 1e-9
                and not any(s.get("msaContain") for s in screen.get("slots") or [])
            )

    summary["cropRisk"] = risks
    summary["whitespaceRatio"] = whitespace
    summary["whitespaceCapped"] = whitespace_capped

    slot_fits = [str(s.get("fit") or "cover") for s in screen.get("slots") or []]
    summary["slotFits"] = slot_fits
    if summary["msaOutcome"] == "msa_solve_miss" and any(
        s.get("msaContain") for s in screen.get("slots") or []
    ):
        summary["msaOutcome"] = "applied_fit_only"

    geo["msa"] = {
        "outcome": summary["msaOutcome"],
        "profile": summary["msaProfile"],
        "rHeroTarget": summary["rHeroTarget"],
        "variantOutcomes": summary.get("variantOutcomes"),
        "cropRisk": risks,
        "whitespaceRatio": whitespace,
        "auxSwap": bool(swapped),
        "whitespaceCapped": whitespace_capped,
        "whitespaceResolve": bool(summary.get("whitespaceResolve")),
    }
    geo["whitespaceRatio"] = whitespace
    return summary
