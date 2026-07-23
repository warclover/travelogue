"""Layout template publish validator (PRD §6)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from travelogue.layout_templates.aspect_constants import (
    AR_LADDER,
    AR_LADDER_TOL,
    LANDSCAPE_AR_BLOCK_HIGH,
    LANDSCAPE_AR_MAX,
    LANDSCAPE_AR_MIN,
    PORTRAIT_AR_BLOCK_HIGH,
    PORTRAIT_AR_BLOCK_LOW,
    PORTRAIT_AR_MAX,
    PORTRAIT_AR_MIN,
)
from travelogue.layout_templates.css_gen import (
    grid_templates_for,
    slot_cells,
    validate_css_bundle,
)
from travelogue.layout_templates.geometry import slot_aspect_table
from travelogue.layout_templates.models import TemplateDef, TemplateSlot, TemplateStage
from travelogue.layout_templates.registry import get_engine

ValidateMode = Literal["ci", "publish"]


@dataclass
class ValidationIssue:
    code: str
    message: str
    level: str = "error"  # error | warn | block


@dataclass
class ValidationReport:
    ok: bool
    template_id: str
    issues: list[ValidationIssue] = field(default_factory=list)

    def add(self, code: str, message: str, *, level: str = "error") -> None:
        self.issues.append(ValidationIssue(code=code, message=message, level=level))
        if level in ("error", "block"):
            self.ok = False


def _track_counts(stage: TemplateStage) -> tuple[int, int]:
    if stage.cols and stage.rows:
        return len(stage.cols), len(stage.rows)
    if stage.grid:
        return stage.grid[0], stage.grid[1]
    return 3, 3


def _stage_track_cells(stage: TemplateStage) -> set[tuple[int, int]]:
    cols, rows = _track_counts(stage)
    return {(c, r) for c in range(1, cols + 1) for r in range(1, rows + 1)}


def _slot_cells(rect: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    c0, c1, r0, r1 = rect
    return {(c, r) for c in range(c0, c1 + 1) for r in range(r0, r1 + 1)}


def _main_slot_counts_as_portrait(template: TemplateDef) -> bool:
    """MTSO · portrait-hero mains declare eligibleAspectKinds: [portrait]."""
    elig = (template.constraints or {}).get("eligibility") or {}
    kinds = {
        str(k).lower()
        for k in (elig.get("eligibleAspectKinds") or elig.get("eligible_aspect_kinds") or [])
    }
    return "portrait" in kinds and "landscape" not in kinds


def _role_counts(template: TemplateDef) -> tuple[int, int]:
    main_as_portrait = _main_slot_counts_as_portrait(template)
    portrait = 0
    landscape_like = 0
    for s in template.slots:
        if s.role == "portrait":
            portrait += 1
        elif s.role == "main" and main_as_portrait:
            portrait += 1
        elif s.role in ("landscape", "main", "tile", "square"):
            landscape_like += 1
    return portrait, landscape_like


def _nearest_ladder_delta(ar: float) -> float:
    return min(abs(ar - ladder) for ladder in AR_LADDER)


def _ar_ladder_sign_off(template: TemplateDef, slot_index: int) -> bool:
    """True when constraints.arLadderSignOff records manual approval (V-P16-13)."""
    raw = (template.constraints or {}).get("arLadderSignOff") or {}
    if not isinstance(raw, dict):
        return False
    entry = raw.get(str(slot_index), raw.get(slot_index))
    if not isinstance(entry, dict):
        return False
    return bool(str(entry.get("signedBy") or "").strip()) and bool(
        str(entry.get("signedAt") or "").strip()
    )


def _check_overlaps(template: TemplateDef, report: ValidationReport) -> None:
    for i, a in enumerate(template.slots):
        cells_a = _slot_cells(a.rect)
        for b in template.slots[i + 1 :]:
            overlap = cells_a & _slot_cells(b.rect)
            if overlap:
                report.add(
                    "V-P16-01",
                    f"slots {a.index} and {b.index} overlap on cells {sorted(overlap)}",
                )


def _check_gaps(template: TemplateDef, report: ValidationReport) -> None:
    if template.kind == "stack":
        return
    stage_cells = _stage_track_cells(template.stage)
    covered: set[tuple[int, int]] = set()
    for slot in template.slots:
        covered |= _slot_cells(slot.rect)
    gaps = stage_cells - covered
    intentional = template.constraints.get("intentionalGaps") or []
    declared: set[tuple[int, int]] = set()
    for gap in intentional:
        if isinstance(gap, (list, tuple)) and len(gap) == 4:
            declared |= _slot_cells(tuple(int(x) for x in gap))
    undeclared = gaps - declared
    if undeclared:
        report.add(
            "V-P16-02",
            f"undeclared gap cells {sorted(undeclared)} (declare in constraints.intentionalGaps)",
        )


# LTN R-A3 · slots >6 frozen except grandfathered 8/9 SKUs (Wave C may prune further).
_GRANDFATHERED_DENSE_SLOT_IDS: frozenset[str] = frozenset(
    {
        "screen-portrait-grid-8",
        "screen-portrait-9",
        "screen-landscape-9",
    }
)


def _check_photo_count(template: TemplateDef, report: ValidationReport) -> None:
    n = len(template.slots)
    if n != template.photo_count_min or n != template.photo_count_max:
        report.add(
            "V-P16-03",
            f"len(slots)={n} != photoCount min/max "
            f"{template.photo_count_min}/{template.photo_count_max}",
        )
    if template.photo_count_max > 9 or n > 9:
        report.add("V-P16-12", "photoCount.max and slots must be ≤ 9", level="block")
    # LTN R-A3 freeze: new templates with >6 slots blocked unless grandfathered.
    if (n > 6 or template.photo_count_max > 6) and template.id not in _GRANDFATHERED_DENSE_SLOT_IDS:
        if template.status != "deprecated":
            report.add(
                "V-LTN-FREEZE",
                f"slots/photoCount={max(n, template.photo_count_max)} > 6 blocked "
                f"(LTN R-A3 freeze; grandfather or written exemption required)",
                level="block",
            )


def _check_mix(template: TemplateDef, report: ValidationReport) -> None:
    p, land = _role_counts(template)
    if template.mix_portrait is not None and template.mix_portrait != p:
        report.add("V-P16-09", f"mix.portrait={template.mix_portrait} != role count {p}")
    if template.mix_landscape is not None and template.mix_landscape != land:
        report.add("V-P16-09", f"mix.landscape={template.mix_landscape} != role count {land}")


def _check_tracks_and_bounds(template: TemplateDef, report: ValidationReport) -> None:
    cols_n, rows_n = _track_counts(template.stage)
    if template.stage.cols:
        for i, w in enumerate(template.stage.cols):
            if w <= 0:
                report.add("V-P16-14", f"stage.cols[{i}] must be > 0")
    if template.stage.rows:
        for i, w in enumerate(template.stage.rows):
            if w <= 0:
                report.add("V-P16-14", f"stage.rows[{i}] must be > 0")
    for slot in template.slots:
        c0, c1, r0, r1 = slot.rect
        if c0 < 1 or r0 < 1 or c1 < c0 or r1 < r0:
            report.add("V-P16-14", f"slot {slot.index} rect {slot.rect} invalid")
        if c1 > cols_n or r1 > rows_n:
            report.add(
                "V-P16-14",
                f"slot {slot.index} rect {slot.rect} exceeds stage tracks ({cols_n}×{rows_n})",
            )


def _is_portrait_stage(stage: TemplateStage) -> bool:
    return stage.aspect in ("9:16",)


def _is_uniform_grid(template: TemplateDef) -> bool:
    """Uniform-grid primitive: every cell shares one AR (no weighted tracks).

    In such grids `role` denotes the accepted photo type, not the cell shape —
    a portrait photo may sit in a wide cell via object-fit (legacy mixed grids
    like screen-portrait-2-landscape-2). The role↔cell-AR orientation check is
    therefore not actionable and must not hard-block (PRD §6: V-P16-04 is
    error/warn). Composite weighted-track templates keep the hard block.
    """
    st = template.stage
    return (
        template.kind == "primitive"
        and st.grid is not None
        and st.cols is None
        and st.rows is None
    )


def _check_role_aspect(template: TemplateDef, report: ValidationReport, *, mode: ValidateMode) -> None:
    if template.kind == "stack":
        return
    portrait_stage = _is_portrait_stage(template.stage)
    uniform_grid = _is_uniform_grid(template)

    def _lvl(desired: str) -> str:
        # Orientation mismatch on a uniform grid is structurally unavoidable.
        if uniform_grid and desired in ("block", "error"):
            return "warn"
        return desired

    for row in slot_aspect_table(template):
        ar = row.display_aspect
        role = row.role
        if portrait_stage:
            if role == "portrait" and ar > PORTRAIT_AR_BLOCK_HIGH:
                report.add(
                    "V-P16-04",
                    f"slot {row.index} portrait on 9:16 stage displayAspect {ar:.3f} too wide",
                    level=_lvl("block") if mode == "publish" else "warn",
                )
            elif role in ("landscape", "tile") and ar < LANDSCAPE_AR_MIN:
                report.add(
                    "V-P16-04",
                    f"slot {row.index} {role} on 9:16 stage displayAspect {ar:.3f} too tall",
                    level=_lvl("block") if mode == "publish" else "warn",
                )
            continue
        if role == "portrait":
            if ar < PORTRAIT_AR_BLOCK_LOW or ar > PORTRAIT_AR_BLOCK_HIGH:
                report.add(
                    "V-P16-04",
                    f"slot {row.index} portrait displayAspect {ar:.3f} outside "
                    f"[{PORTRAIT_AR_BLOCK_LOW}, {PORTRAIT_AR_BLOCK_HIGH}]",
                    level=_lvl("block") if mode == "publish" else "warn",
                )
            elif ar < PORTRAIT_AR_MIN or ar > PORTRAIT_AR_MAX:
                report.add(
                    "V-P16-04",
                    f"slot {row.index} portrait displayAspect {ar:.3f} outside "
                    f"recommended [{PORTRAIT_AR_MIN}, {PORTRAIT_AR_MAX}]",
                    level="warn",
                )
        elif role in ("landscape", "tile", "square"):
            if ar > LANDSCAPE_AR_BLOCK_HIGH:
                level = _lvl("block") if mode == "publish" else "warn"
                report.add(
                    "V-P16-04",
                    f"slot {row.index} {role} displayAspect {ar:.3f} > {LANDSCAPE_AR_BLOCK_HIGH}",
                    level=level,
                )
            elif ar < LANDSCAPE_AR_MIN or ar > LANDSCAPE_AR_MAX:
                report.add(
                    "V-P16-04",
                    f"slot {row.index} {role} displayAspect {ar:.3f} outside "
                    f"recommended [{LANDSCAPE_AR_MIN}, {LANDSCAPE_AR_MAX}]",
                    level="warn",
                )
        elif role == "main":
            if ar > LANDSCAPE_AR_BLOCK_HIGH:
                level = "warn"
                if mode == "publish" and not _ar_ladder_sign_off(template, row.index):
                    level = "block"
                report.add(
                    "V-P16-04",
                    f"slot {row.index} main displayAspect {ar:.3f} extreme; needs sign-off",
                    level=level,
                )


def _check_ar_ladder(template: TemplateDef, report: ValidationReport, *, mode: ValidateMode) -> None:
    if template.kind == "stack":
        report.add("V-P16-S04", "stack template skips 3×3 displayAspect ladder", level="warn")
        return
    for row in slot_aspect_table(template):
        delta = _nearest_ladder_delta(row.display_aspect)
        if delta <= AR_LADDER_TOL:
            continue
        if row.role == "main":
            if mode == "publish" and not _ar_ladder_sign_off(template, row.index):
                report.add(
                    "V-P16-13",
                    f"slot {row.index} main displayAspect {row.display_aspect:.3f} "
                    f"off AR ladder (Δ={delta:.3f}); needs sign-off",
                    level="block",
                )
            continue
        report.add(
            "V-P16-13",
            f"slot {row.index} displayAspect {row.display_aspect:.3f} "
            f"not on AR ladder (Δ={delta:.3f})",
            level="warn",
        )


def _check_balance_policy(template: TemplateDef, report: ValidationReport) -> None:
    policy = template.balance_policy
    if not policy:
        return
    if policy == "equal_height":
        by_col: dict[int, list[TemplateSlot]] = {}
        for slot in template.slots:
            c0, c1, _, _ = slot.rect
            if c0 == c1:
                by_col.setdefault(c0, []).append(slot)
        for col, slots in by_col.items():
            spans = {s.rect[3] - s.rect[2] + 1 for s in slots if s.role == "landscape"}
            if len(spans) > 1:
                report.add(
                    "V-P16-10",
                    f"equal_height: column {col} landscape row spans differ {spans}",
                    level="warn",
                )
    if policy == "equal_width":
        by_row: dict[int, list[TemplateSlot]] = {}
        for slot in template.slots:
            _, _, r0, r1 = slot.rect
            if r0 == r1:
                by_row.setdefault(r0, []).append(slot)
        for row_idx, slots in by_row.items():
            spans = {s.rect[1] - s.rect[0] + 1 for s in slots if s.role == "landscape"}
            if len(spans) > 1:
                report.add(
                    "V-P16-10",
                    f"equal_width: row {row_idx} landscape col spans differ {spans}",
                    level="warn",
                )


def _check_main_slot_policy(
    template: TemplateDef,
    report: ValidationReport,
    *,
    mode: ValidateMode,
) -> None:
    """V-P16-MAIN-01 · 16:9 main hero+tile templates declare eligibility (or legacy mainSlotPolicy)."""
    if template.kind != "composite":
        return
    main_rows = [row for row in slot_aspect_table(template) if row.role == "main"]
    if not main_rows:
        return
    for row in main_rows:
        if abs(row.display_aspect - (16 / 9)) > AR_LADDER_TOL:
            continue
        constraints = template.constraints or {}
        elig = constraints.get("eligibility")
        legacy = constraints.get("mainSlotPolicy")
        policy = None
        if isinstance(elig, dict) and (
            elig.get("eligibleAspectKinds") or elig.get("targetDisplayAspect")
        ):
            policy = elig
        elif isinstance(legacy, dict) and legacy:
            policy = legacy
        if not isinstance(policy, dict) or not policy:
            level = "warn" if mode == "ci" else "block"
            report.add(
                "V-P16-MAIN-01",
                f"slot {row.index} main targets 16:9; "
                "constraints.eligibility (or legacy mainSlotPolicy) required",
                level=level,
            )
            continue
        # Single spelling via shared normalizer (AC-TPC-18).
        from travelogue.layout_engine.contract.eligibility_normalize import (
            normalize_eligibility_spec,
        )

        policy = normalize_eligibility_spec(policy)
        slot_idx = policy.get("slotIndex")
        if slot_idx is not None and int(slot_idx) != row.index:
            report.add(
                "V-P16-MAIN-01",
                f"eligibility/mainSlotPolicy.slotIndex {slot_idx} != main slot {row.index}",
                level="warn",
            )
        target = policy.get("targetDisplayAspect")
        if target is not None:
            try:
                target_f = float(target)
            except (TypeError, ValueError):
                report.add(
                    "V-P16-MAIN-01",
                    "eligibility.targetDisplayAspect must be numeric",
                    level="warn",
                )
            else:
                if abs(target_f - row.display_aspect) > AR_LADDER_TOL:
                    report.add(
                        "V-P16-MAIN-01",
                        f"eligibility.targetDisplayAspect {target_f:.4f} "
                        f"≠ slot displayAspect {row.display_aspect:.4f}",
                        level="warn",
                    )


def _check_stack(template: TemplateDef, report: ValidationReport) -> None:
    if template.kind != "stack":
        return
    if template.stage.grid and template.stage.grid != (1, len(template.slots)):
        if not (template.stage.cols == (1,) and template.stage.rows):
            report.add("V-P16-S01", "stack template must use cols=[1] + rows or 1×N grid")
    if "stack" not in template.render_grid_class and "landscape-stack" not in template.render_grid_class:
        report.add(
            "V-P16-S03",
            f"stack render.gridClass {template.render_grid_class!r} missing stack marker",
        )


def _check_css(template: TemplateDef, report: ValidationReport) -> None:
    if template.kind == "stack":
        return
    cols, rows = grid_templates_for(template)
    if not cols or not rows:
        report.add("V-P16-05", "failed to derive grid-template from stage")
        return
    for msg in validate_css_bundle(template):
        if msg.startswith("WARN"):
            report.add("V-P16-05", msg[5:], level="warn")
        else:
            report.add("V-P16-05", msg)
    for slot in template.slots:
        expected_cells = slot_cells(template.stage, slot.rect)
        if not expected_cells:
            report.add("V-P16-06", f"slot {slot.index} covers no track cells")


def _usage_doc(template: TemplateDef) -> dict:
    raw = template.raw.get("usage") if isinstance(template.raw, dict) else None
    return raw if isinstance(raw, dict) else {}


def _known_template_docs() -> dict[str, dict]:
    """All registry templates' raw docs (empty on load failure — checks degrade)."""
    try:
        engine = get_engine()
    except Exception:
        return {}
    return {tid: t.raw for tid, t in engine._templates.items()}


def _check_usage(template: TemplateDef, report: ValidationReport) -> None:
    """V-P16-U01..03 · usage contract checks (字数/结构由 JSON Schema 保证)."""
    usage = _usage_doc(template)
    if not usage:
        if template.status == "ga":
            report.add(
                "V-P16-U02",
                "ga template missing usage block (summary/whenToUse/whenNotToUse)",
                level="warn",
            )
        return

    known = _known_template_docs()
    siblings = usage.get("siblings") or []
    for entry in siblings:
        if not isinstance(entry, dict):
            continue
        sid = str(entry.get("id") or "")
        if sid == template.id:
            report.add("V-P16-U01", f"usage.siblings references self ({sid})")
            continue
        if known and sid not in known:
            report.add("V-P16-U01", f"usage.siblings id {sid!r} not found in registry")
            continue
        # Reciprocity is advisory: A documents B, B should document A back.
        other_usage = known.get(sid, {}).get("usage") if known else None
        if isinstance(other_usage, dict):
            back_ids = {
                str(e.get("id") or "")
                for e in (other_usage.get("siblings") or [])
                if isinstance(e, dict)
            }
            if template.id not in back_ids:
                report.add(
                    "V-P16-U03",
                    f"sibling {sid} does not reference {template.id} back",
                    level="warn",
                )

    if template.status == "ga":
        for key in ("whenToUse", "whenNotToUse"):
            if not str(usage.get(key) or "").strip():
                report.add(
                    "V-P16-U02",
                    f"ga template usage missing {key}",
                    level="warn",
                )


def _check_id_naming(template: TemplateDef, report: ValidationReport) -> None:
    if template.status != "deprecated" and template.id.endswith("-deprecated"):
        report.add("V-P16-08", "active template id looks deprecated", level="warn")
    if template.status == "deprecated" and template.id.endswith("-v2"):
        report.add("V-P16-08", "deprecated id uses -v2 suffix; prefer new id", level="warn")


def validate_template_def(
    template: TemplateDef,
    *,
    mode: ValidateMode = "ci",
) -> ValidationReport:
    """Run §6 publish gates. mode=publish enables strict blocks (AC-P16-03)."""
    report = ValidationReport(ok=True, template_id=template.id)
    _check_photo_count(template, report)
    _check_overlaps(template, report)
    _check_gaps(template, report)
    _check_mix(template, report)
    _check_tracks_and_bounds(template, report)
    _check_role_aspect(template, report, mode=mode)
    _check_ar_ladder(template, report, mode=mode)
    _check_main_slot_policy(template, report, mode=mode)
    _check_balance_policy(template, report)
    _check_stack(template, report)
    _check_css(template, report)
    _check_id_naming(template, report)
    _check_usage(template, report)
    return report


class LayoutTemplateGeometryHook:
    """Management-side hooks injected into templating.admission (R-P16-12)."""

    def validate_for_publish(self, template_id: str) -> ValidationReport:
        template = get_engine().get(template_id)
        return validate_template_def(template, mode="publish")

    def slot_aspect_table(self, template_id: str) -> list:
        from travelogue.layout_templates.geometry import slot_aspect_table as table

        return table(get_engine().get(template_id))

    def geometry_diff(self, template_id: str, va: int, vb: int) -> dict:
        from travelogue.layout_templates.geometry_diff import geometry_diff as _diff

        return _diff(template_id, va, vb)


def format_slot_aspect_doc(template: TemplateDef) -> str:
    """Markdown slot aspect table (AC-P16-04)."""
    lines = [
        f"# {template.id}",
        "",
        f"- displayName: {template.display_name}",
        f"- status: {template.status}",
        f"- stage: {template.stage.aspect}",
        "",
        "| slot | role | displayAspect |",
        "|------|------|---------------|",
    ]
    for row in slot_aspect_table(template):
        lines.append(f"| {row.index} | {row.role} | {row.display_aspect:.4f} |")
    lines.append("")
    return "\n".join(lines)
