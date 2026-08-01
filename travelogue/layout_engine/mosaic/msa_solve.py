"""MSA · track-weight solve with fixed topology (S-MSA-02)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from travelogue.config.mosaic import SlotAdaptationConfig, SlotAdaptationSolveConfig
from travelogue.layout_templates.geometry import slot_display_aspect, solve_tracks
from travelogue.layout_templates.models import TemplateDef, TemplateStage

# M1 whitelist · O-MSA-03 / 七席 S-02 冻结
MSA_M1_PATTERN_WHITELIST: frozenset[str] = frozenset(
    {
        # 横主 hero
        "screen-mosaic-6-main-hero-plus-5",
        "screen-mosaic-5-main-hero-plus-4",
        "screen-mosaic-4-hero-70-sidebar",
        # 竖主（实验 SKU + GA 竖主）
        "screen-mosaic-5-1p4l-portrait-hero",
        "screen-mosaic-5-2p3l-portrait-hero-rail",
        "screen-mosaic-5-main-portrait-3land",
    }
)

MAIN_AR_TOL = 0.08


@dataclass(frozen=True)
class MsaSolveResult:
    ok: bool
    cols: list[float]
    rows: list[float]
    main_display_aspect: float | None
    main_area: float | None
    reason: str  # applied | msa_solve_miss | skipped_not_whitelisted | no_target


def stage_track_lists(stage: TemplateStage) -> tuple[list[float], list[float]]:
    if stage.cols and stage.rows:
        return list(stage.cols), list(stage.rows)
    if stage.grid:
        return [1.0] * stage.grid[0], [1.0] * stage.grid[1]
    return [1.0], [1.0]


def slot_area_fraction(
    rect: tuple[int, int, int, int], cols: Sequence[float], rows: Sequence[float]
) -> float:
    c0, c1, r0, r1 = rect
    col_sum = sum(cols) or 1.0
    row_sum = sum(rows) or 1.0
    col_frac = sum(cols[c0 - 1 : c1]) / col_sum
    row_frac = sum(rows[r0 - 1 : r1]) / row_sum
    return col_frac * row_frac


def _main_slot(template: TemplateDef) -> Any | None:
    for slot in template.slots:
        if slot.role == "main":
            return slot
    return template.slots[0] if template.slots else None


def _eligibility(template: TemplateDef) -> dict[str, Any]:
    return (template.constraints or {}).get("eligibility") or {}


def _area_floor(template: TemplateDef) -> float:
    elig = _eligibility(template)
    band = elig.get("heroAreaBand")
    if isinstance(band, (list, tuple)) and band:
        try:
            return float(band[0])
        except (TypeError, ValueError):
            pass
    dominance = str(elig.get("heroDominance") or "").lower()
    if dominance == "extreme":
        return 0.55
    return 0.35


def _prominence_floor(template: TemplateDef) -> float | None:
    """Extreme hero families require main/max_aux ≥ 3 (MTSO/MGQ)."""
    elig = _eligibility(template)
    if str(elig.get("heroDominance") or "").lower() == "extreme":
        return 3.0
    return None


def main_is_portrait_family(template: TemplateDef) -> bool:
    elig = _eligibility(template)
    kinds = {str(k).lower() for k in (elig.get("eligibleAspectKinds") or [])}
    if not kinds:
        return False
    return "portrait" in kinds and "landscape" not in kinds


def resolve_main_r_star(template: TemplateDef, *, r_land: float | None, r_port: float | None) -> float | None:
    """Pick main-slot AR target: land peak for landscape-main, port peak for portrait-main."""
    elig = _eligibility(template)
    if main_is_portrait_family(template):
        if r_port is not None and r_port > 0:
            return float(r_port)
        try:
            target = elig.get("targetDisplayAspect")
            if target is not None:
                return float(target)
        except (TypeError, ValueError):
            pass
        return None
    return float(r_land) if r_land is not None and r_land > 0 else None


def _prominence_ratio(
    template: TemplateDef, cols: Sequence[float], rows: Sequence[float]
) -> float | None:
    main = _main_slot(template)
    if main is None:
        return None
    main_a = slot_area_fraction(tuple(main.rect), cols, rows)
    others = [
        slot_area_fraction(tuple(s.rect), cols, rows)
        for s in template.slots
        if s.index != main.index
    ]
    if not others:
        return None
    denom = max(others)
    if denom <= 0:
        return None
    return main_a / denom


def _clamp_weights(
    cols: list[float],
    rows: list[float],
    *,
    wmin: float,
    wmax: float,
) -> tuple[list[float], list[float]]:
    return (
        [min(wmax, max(wmin, float(c))) for c in cols],
        [min(wmax, max(wmin, float(r))) for r in rows],
    )


def _stage_with(
    aspect: str,
    cols: Sequence[float],
    rows: Sequence[float],
    *,
    gap: str | None = None,
) -> TemplateStage:
    return TemplateStage(
        aspect=aspect,
        cols=tuple(float(c) for c in cols),
        rows=tuple(float(r) for r in rows),
        gap=gap,
    )


def _local_refine(
    *,
    aspect: str,
    main_rect: tuple[int, int, int, int],
    cols: list[float],
    rows: list[float],
    r_star: float,
    amin: float,
    solve_cfg: SlotAdaptationSolveConfig,
    gap: str | None,
) -> tuple[list[float], list[float]]:
    cols, rows = _clamp_weights(
        cols, rows, wmin=solve_cfg.track_weight_min, wmax=solve_cfg.track_weight_max
    )
    stage0 = _stage_with(aspect, cols, rows, gap=gap)
    best_err = abs(slot_display_aspect(main_rect, stage0) - r_star)
    for _ in range(max(8, int(solve_cfg.max_iters))):
        improved = False
        for i in range(len(cols)):
            for factor in (0.85, 0.92, 1.08, 1.15, 1.25, 1.5, 2.0):
                trial_c = list(cols)
                trial_c[i] *= factor
                trial_c, trial_r = _clamp_weights(
                    trial_c,
                    rows,
                    wmin=solve_cfg.track_weight_min,
                    wmax=solve_cfg.track_weight_max,
                )
                if slot_area_fraction(main_rect, trial_c, trial_r) + 1e-9 < amin:
                    continue
                st = _stage_with(aspect, trial_c, trial_r, gap=gap)
                err = abs(slot_display_aspect(main_rect, st) - r_star)
                if err + 1e-9 < best_err:
                    cols, rows = trial_c, trial_r
                    best_err = err
                    improved = True
        for i in range(len(rows)):
            for factor in (0.85, 0.92, 1.08, 1.15, 1.25, 1.5, 2.0):
                trial_r = list(rows)
                trial_r[i] *= factor
                trial_c, trial_r = _clamp_weights(
                    cols,
                    trial_r,
                    wmin=solve_cfg.track_weight_min,
                    wmax=solve_cfg.track_weight_max,
                )
                if slot_area_fraction(main_rect, trial_c, trial_r) + 1e-9 < amin:
                    continue
                st = _stage_with(aspect, trial_c, trial_r, gap=gap)
                err = abs(slot_display_aspect(main_rect, st) - r_star)
                if err + 1e-9 < best_err:
                    cols, rows = trial_c, trial_r
                    best_err = err
                    improved = True
        if not improved:
            break
    return cols, rows


def solve_track_override(
    template: TemplateDef,
    *,
    r_hero_target: float,
    stage_aspect: str | None = None,
    cfg: SlotAdaptationConfig | None = None,
) -> MsaSolveResult:
    """Solve cols/rows so main displayAspect ≈ ``r_hero_target``; topology fixed."""
    sa = cfg or SlotAdaptationConfig()
    solve_cfg: SlotAdaptationSolveConfig = sa.solve or SlotAdaptationSolveConfig()
    base_cols, base_rows = stage_track_lists(template.stage)

    if template.id not in MSA_M1_PATTERN_WHITELIST:
        return MsaSolveResult(
            ok=False,
            cols=base_cols,
            rows=base_rows,
            main_display_aspect=None,
            main_area=None,
            reason="skipped_not_whitelisted",
        )
    if r_hero_target <= 0:
        return MsaSolveResult(
            ok=False,
            cols=base_cols,
            rows=base_rows,
            main_display_aspect=None,
            main_area=None,
            reason="no_target",
        )

    main = _main_slot(template)
    if main is None:
        return MsaSolveResult(
            ok=False,
            cols=base_cols,
            rows=base_rows,
            main_display_aspect=None,
            main_area=None,
            reason="msa_solve_miss",
        )

    aspect = stage_aspect or template.stage.aspect
    amin = _area_floor(template)
    main_rect = tuple(main.rect)

    solved_cols, solved_rows = solve_tracks(
        [(float(r_hero_target), 1.0)],
        stage_aspect=aspect,
        rects=[main_rect],
    )
    if len(solved_cols) != len(base_cols) or len(solved_rows) != len(base_rows):
        solved_cols, solved_rows = list(base_cols), list(base_rows)

    solved_cols, solved_rows = _local_refine(
        aspect=aspect,
        main_rect=main_rect,
        cols=list(solved_cols),
        rows=list(solved_rows),
        r_star=float(r_hero_target),
        amin=amin,
        solve_cfg=solve_cfg,
        gap=template.stage.gap,
    )

    stage_f = _stage_with(aspect, solved_cols, solved_rows, gap=template.stage.gap)
    main_ar = slot_display_aspect(main_rect, stage_f)
    main_area = slot_area_fraction(main_rect, solved_cols, solved_rows)
    prom = _prominence_ratio(template, solved_cols, solved_rows)
    pmin = _prominence_floor(template)
    prom_fail = pmin is not None and (prom is None or prom + 1e-9 < pmin)
    if (
        abs(main_ar - r_hero_target) > MAIN_AR_TOL
        or main_area + 1e-9 < amin
        or prom_fail
    ):
        return MsaSolveResult(
            ok=False,
            cols=base_cols,
            rows=base_rows,
            main_display_aspect=round(main_ar, 4),
            main_area=round(main_area, 4),
            reason="msa_solve_miss",
        )
    return MsaSolveResult(
        ok=True,
        cols=[round(float(c), 4) for c in solved_cols],
        rows=[round(float(r), 4) for r in solved_rows],
        main_display_aspect=round(main_ar, 4),
        main_area=round(main_area, 4),
        reason="applied",
    )


def list_stage_variants(template: TemplateDef) -> list[dict[str, str]]:
    """Return activated stage variants; default to primary aspect when absent."""
    raw_stage = (template.raw or {}).get("stage") or {}
    variants = raw_stage.get("variants")
    out: list[dict[str, str]] = []
    if isinstance(variants, list):
        for item in variants:
            if not isinstance(item, dict):
                continue
            layout = str(item.get("layout") or "default")
            aspect = str(item.get("aspect") or template.stage.aspect)
            out.append({"layout": layout, "aspect": aspect})
    if not out:
        out.append({"layout": "default", "aspect": template.stage.aspect})
    return out


def solve_all_variants(
    template: TemplateDef,
    *,
    r_hero_target: float,
    cfg: SlotAdaptationConfig | None = None,
) -> dict[str, MsaSolveResult]:
    """Per-variant solve (BLK-MSA-04); each miss falls back independently."""
    results: dict[str, MsaSolveResult] = {}
    for variant in list_stage_variants(template):
        results[variant["layout"]] = solve_track_override(
            template,
            r_hero_target=r_hero_target,
            stage_aspect=variant["aspect"],
            cfg=cfg,
        )
    return results
