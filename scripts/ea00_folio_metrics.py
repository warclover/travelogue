#!/usr/bin/env python3
"""EA-00 folio metrics — pure functions. Do not invent a second caliber.

Source of truth: ``docs/成册指标口径定义.md`` (frozen 2026-09-01).
``EA-02a`` / ``EA-02b`` / ``MG-02`` must call these symbols. This module
never imports journal or portfolio compose entry points.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from statistics import median
from typing import Any, Literal

CALIBER_DOC = "docs/成册指标口径定义.md"
SURFACE_LANDSCAPE_16X9 = "landscape-16x9"
MEASUREMENT_STAGE_COMPOSE = "compose"

PipelineName = Literal["mosaic", "series"]
RowStatus = Literal["ok", "inputInvalid", "metricInvalid", "outputInvalid", "pipelineFail"]

# EA-00 §0.2 / §10: structure screens are never content pages.
BREATH_PATTERN = "screen-breath-pause"
_STRUCTURE_PREFIXES = ("screen-breath", "screen-decor")
_STRUCTURE_IDS = frozenset(
    {
        BREATH_PATTERN,
        "cover",
        "toc",
        "closing",
        "screen-cover",
        "screen-toc",
        "screen-closing",
    }
)

# EA-00 §12 hand-worked samples. Tests must keep these numbers.
SAMPLE_A = {
    "folderN": 100,
    "eligible": 80,
    "intakeN": 80,
    "capacityN": 72,
    "placedEligible": 70,
    "preComposeExcluded": 20,
    "intakeLoss": 0,
    "overflowCapped": 8,
    "placementGap": 2,
    "unplacedEligible": 10,
    "coverage": 0.875,
}
SAMPLE_B = {
    "eligible": 40,
    "intakeN": 40,
    "placementOccurrences": 40,
    "placedUnique": 38,
    "placedEligible": 38,
    "foreignPlaced": 0,
    "duplicatePlacements": 2,
    "overflowCapped": 0,
    "placementGap": 2,
    "coverage": 0.95,
}
SAMPLE_C = {
    "plannedPageCount": 16,
    "renderedPageCount": 14,
    "omittedPlannedPages": 2,
    "emptyRenderedPages": 0,
    "partialPages": 3,
    "fullPages": 11,
}


SlotCountFn = Callable[[str], int | None]


@dataclass
class AssetMetrics:
    folder_n: int
    eligible: int
    eligible_ids: list[str]
    intake_n: int
    intake_ids: list[str]
    slot_asset_ids: list[str]
    placement_occurrences: int
    placed_ids: list[str]
    placed_unique: int
    placed_eligible_ids: list[str]
    placed_eligible: int
    foreign_ids: list[str]
    foreign_placed: int
    duplicate_asset_ids: list[str]
    duplicate_placements: int
    coverage: float | None
    pre_compose_excluded: int
    cull_discard: int | None
    intake_loss: int
    capacity_n: int | None
    overflow_capped: int
    placement_gap: int
    unplaced_eligible: int


@dataclass
class PageMetrics:
    planned_page_count: int | None
    rendered_page_count: int
    omitted_planned_pages: int | None
    declared_slots: int
    empty_rendered_pages: int
    partial_pages: int
    full_pages: int
    empty_slots: int
    empty_slot_rate: float | None
    page_degraded: int | None
    unknown_templates: list[str] = field(default_factory=list)
    overflow_slots: list[str] = field(default_factory=list)
    zero_slot_templates: list[str] = field(default_factory=list)


def is_content_screen(screen: Mapping[str, Any] | None) -> bool:
    """True iff this screen is a compose content page (EA-00 §0.2)."""
    if not isinstance(screen, Mapping):
        return False
    pid = str(screen.get("patternId") or "").strip()
    if not pid:
        return False
    lower = pid.lower()
    if pid in _STRUCTURE_IDS or lower in _STRUCTURE_IDS:
        return False
    return not lower.startswith(_STRUCTURE_PREFIXES)


def iter_content_screens(chapters: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for ch in chapters or []:
        if not isinstance(ch, Mapping):
            continue
        for screen in ch.get("screens") or []:
            if is_content_screen(screen):
                out.append(dict(screen))
    return out


def slot_asset_ids(screens: Sequence[Mapping[str, Any]]) -> list[str]:
    """Non-empty slot assetId sequence; duplicates kept (EA-00 §1)."""
    ids: list[str] = []
    for screen in screens:
        for slot in screen.get("slots") or []:
            if not isinstance(slot, Mapping):
                continue
            aid = str(slot.get("assetId") or "").strip()
            if aid:
                ids.append(aid)
    return ids


def filled_count(screen: Mapping[str, Any]) -> int:
    n = 0
    for slot in screen.get("slots") or []:
        if isinstance(slot, Mapping) and str(slot.get("assetId") or "").strip():
            n += 1
    return n


def folder_n(trip: Mapping[str, Any] | None) -> int:
    n = 0
    for asset in (trip or {}).get("assets") or []:
        if not isinstance(asset, Mapping):
            continue
        if asset.get("type", "image") == "video":
            continue
        n += 1
    return n


def eligible_id_list(trip: Mapping[str, Any] | None) -> tuple[list[str], list[str]]:
    """Return (ordered unique eligible ids, input-invalid reasons)."""
    seen: set[str] = set()
    ordered: list[str] = []
    reasons: list[str] = []
    missing = 0
    for asset in (trip or {}).get("assets") or []:
        if not isinstance(asset, Mapping):
            continue
        if asset.get("type", "image") == "video":
            continue
        if asset.get("layoutEligible", True) is False:
            continue
        aid = str(asset.get("id") or "").strip()
        if not aid:
            missing += 1
            continue
        if aid in seen:
            reasons.append(f"duplicateEligibleId:{aid}")
            continue
        seen.add(aid)
        ordered.append(aid)
    if missing:
        reasons.append(f"missingEligibleId:{missing}")
    return ordered, reasons


def cull_discard_count(trip: Mapping[str, Any] | None) -> int | None:
    """Count image assets with a cull/user exclude reason; None if incomplete."""
    from travelogue.curation.photo_cull import CULL_EXCLUDE_REASONS

    extra = {"user", "user_exclude", "duplicate", "low_quality", "low_resolution"}
    known = CULL_EXCLUDE_REASONS | extra
    discarded = 0
    incomplete = False
    for asset in (trip or {}).get("assets") or []:
        if not isinstance(asset, Mapping):
            continue
        if asset.get("type", "image") == "video":
            continue
        if asset.get("layoutEligible", True) is not False:
            continue
        reason = str(asset.get("excludeReason") or "").strip()
        if not reason:
            incomplete = True
            continue
        if reason in known:
            discarded += 1
        else:
            incomplete = True
    if incomplete and discarded == 0:
        return None
    if incomplete:
        return None
    return discarded


def unique_in_order(ids: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in ids:
        aid = str(raw or "").strip()
        if not aid or aid in seen:
            continue
        seen.add(aid)
        out.append(aid)
    return out


def compute_unplaced_split(
    *,
    eligible: int,
    intake_n: int,
    placed_eligible: int,
    capacity_n: int | None,
) -> tuple[int, int, int, int]:
    """Return (intakeLoss, overflowCapped, placementGap, unplacedEligible).

    EA-00 §3.2 — the only allowed split. Do not read overflow.resolution.
    """
    intake_loss = max(0, eligible - intake_n)
    if capacity_n is None:
        overflow_capped = 0
        placement_gap = max(0, intake_n - placed_eligible)
    else:
        overflow_capped = max(0, intake_n - capacity_n)
        placement_gap = max(0, min(intake_n, capacity_n) - placed_eligible)
    unplaced = intake_loss + overflow_capped + placement_gap
    return intake_loss, overflow_capped, placement_gap, unplaced


def compute_asset_metrics(
    *,
    trip: Mapping[str, Any] | None,
    eligible_ids: Sequence[str],
    intake_ids: Sequence[str],
    slot_asset_ids_: Sequence[str],
    capacity_n: int | None,
) -> AssetMetrics:
    eligible_list = unique_in_order(eligible_ids)
    eligible_set = set(eligible_list)
    intake_list = unique_in_order(aid for aid in intake_ids if str(aid) in eligible_set)
    slots = [str(x) for x in slot_asset_ids_ if str(x).strip()]
    placed_unique_list = unique_in_order(slots)
    placed_set = set(placed_unique_list)
    placed_eligible_list = [aid for aid in placed_unique_list if aid in eligible_set]
    foreign = [aid for aid in placed_unique_list if aid not in eligible_set]
    from collections import Counter

    counts = Counter(slots)
    duplicate_ids = [aid for aid, n in counts.items() if n > 1]
    duplicate_placements = max(0, len(slots) - len(placed_set))
    placed_eligible = len(placed_eligible_list)
    eligible = len(eligible_list)
    intake_n = len(intake_list)
    coverage = (placed_eligible / eligible) if eligible else None
    intake_loss, overflow_capped, placement_gap, unplaced = compute_unplaced_split(
        eligible=eligible,
        intake_n=intake_n,
        placed_eligible=placed_eligible,
        capacity_n=capacity_n,
    )
    fn = folder_n(trip)
    return AssetMetrics(
        folder_n=fn,
        eligible=eligible,
        eligible_ids=eligible_list,
        intake_n=intake_n,
        intake_ids=intake_list,
        slot_asset_ids=slots,
        placement_occurrences=len(slots),
        placed_ids=placed_unique_list,
        placed_unique=len(placed_set),
        placed_eligible_ids=placed_eligible_list,
        placed_eligible=placed_eligible,
        foreign_ids=foreign,
        foreign_placed=len(foreign),
        duplicate_asset_ids=duplicate_ids,
        duplicate_placements=duplicate_placements,
        coverage=coverage,
        pre_compose_excluded=fn - eligible,
        cull_discard=cull_discard_count(trip),
        intake_loss=intake_loss,
        capacity_n=capacity_n,
        overflow_capped=overflow_capped,
        placement_gap=placement_gap,
        unplaced_eligible=unplaced,
    )


def compute_page_metrics(
    *,
    screens: Sequence[Mapping[str, Any]],
    slot_count_for: SlotCountFn,
    planned_page_count: int | None,
    page_degraded: int | None = None,
) -> PageMetrics:
    unknown: list[str] = []
    overflow: list[str] = []
    zero_slot: list[str] = []
    empty_pages = 0
    partial = 0
    full = 0
    empty_slots = 0
    declared = 0
    for screen in screens:
        pid = str(screen.get("patternId") or "").strip()
        slots_n = slot_count_for(pid)
        filled = filled_count(screen)
        if slots_n is None:
            unknown.append(pid)
            continue
        if slots_n <= 0:
            zero_slot.append(pid)
            continue
        if filled > slots_n:
            overflow.append(pid)
        declared += slots_n
        empty_slots += max(0, slots_n - filled)
        if filled == 0:
            empty_pages += 1
        elif filled < slots_n:
            partial += 1
        else:
            full += 1
    rendered = len(screens)
    omitted = None if planned_page_count is None else max(0, planned_page_count - rendered)
    rate = (empty_slots / declared) if declared else None
    return PageMetrics(
        planned_page_count=planned_page_count,
        rendered_page_count=rendered,
        omitted_planned_pages=omitted,
        declared_slots=declared,
        empty_rendered_pages=empty_pages,
        partial_pages=partial,
        full_pages=full,
        empty_slots=empty_slots,
        empty_slot_rate=rate,
        page_degraded=page_degraded,
        unknown_templates=unknown,
        overflow_slots=overflow,
        zero_slot_templates=zero_slot,
    )


def eligible_chapter_indices(
    chapters: Sequence[Mapping[str, Any]] | None,
    buckets: Sequence[Sequence[str]] | None,
    eligible_ids: Sequence[str],
) -> list[int]:
    eligible_set = {str(x) for x in eligible_ids}
    indices: list[int] = []
    chs = list(chapters or [])
    bucks = list(buckets or [])
    n = max(len(chs), len(bucks))
    for i in range(n):
        ids: list[str] = []
        if i < len(bucks):
            ids = [str(x) for x in (bucks[i] or []) if str(x).strip()]
        elif i < len(chs):
            for item in chs[i].get("items") or []:
                if isinstance(item, Mapping):
                    aid = str(item.get("assetId") or item.get("id") or "").strip()
                    if aid:
                        ids.append(aid)
        if any(aid in eligible_set for aid in ids):
            indices.append(i)
    return indices


def chapter_fail_count(
    *,
    eligible_indices: Sequence[int],
    output_chapters: Sequence[Mapping[str, Any]] | None,
) -> int:
    chs = list(output_chapters or [])
    fail = 0
    for i in eligible_indices:
        screens = []
        if i < len(chs) and isinstance(chs[i], Mapping):
            screens = [s for s in (chs[i].get("screens") or []) if is_content_screen(s)]
        if not screens:
            fail += 1
    return fail


def identity_failures(row: Mapping[str, Any]) -> list[str]:
    """Return names of EA-00 identities that this row breaks.

    ``pipelineFail`` rows with null coverage fields are skipped.
    """
    status = row.get("status")
    if status == "pipelineFail":
        return []
    if row.get("coverage") is None and row.get("eligible") in (None, 0):
        if status == "inputInvalid":
            return []
    fails: list[str] = []

    def _num(name: str) -> float | None:
        val = row.get(name)
        if val is None:
            return None
        try:
            return float(val)
        except (TypeError, ValueError):
            return None

    eligible = _num("eligible")
    intake_n = _num("intakeN")
    placed_eligible = _num("placedEligible")
    coverage = _num("coverage")
    if eligible is not None and placed_eligible is not None:
        unplaced = eligible - placed_eligible
        if abs(unplaced - (row.get("unplacedEligible") or unplaced)) > 1e-9:
            if row.get("unplacedEligible") is not None:
                fails.append("unplacedEligible")
        if coverage is not None:
            if eligible > 0:
                expected = placed_eligible / eligible
                if abs(coverage - expected) > 1e-9:
                    fails.append("coverage")
            if coverage < -1e-12 or coverage > 1 + 1e-12:
                fails.append("coverageRange")
        if intake_n is not None:
            if not (placed_eligible <= intake_n + 1e-9 <= eligible + 1e-9):
                fails.append("placedEligible_intakeN_eligible")
        intake_loss = _num("intakeLoss")
        overflow_capped = _num("overflowCapped")
        placement_gap = _num("placementGap")
        if None not in (intake_loss, overflow_capped, placement_gap):
            split = intake_loss + overflow_capped + placement_gap
            if abs(split - (eligible - placed_eligible)) > 1e-9:
                fails.append("unplacedSplit")
            if abs(eligible - (placed_eligible + split)) > 1e-9:
                fails.append("eligibleConservation")
    dup = _num("duplicatePlacements")
    if dup is not None and dup < -1e-12:
        fails.append("duplicatePlacements")
    foreign = _num("foreignPlaced")
    if foreign is not None and foreign < -1e-12:
        fails.append("foreignPlaced")
    folder = _num("folderN")
    if folder is not None and eligible is not None:
        pre = _num("preComposeExcluded")
        if pre is not None and abs(pre - (folder - eligible)) > 1e-9:
            fails.append("preComposeExcluded")

    rendered = _num("renderedPageCount")
    empty_p = _num("emptyRenderedPages")
    partial = _num("partialPages")
    full = _num("fullPages")
    if None not in (rendered, empty_p, partial, full):
        if abs((empty_p + partial + full) - rendered) > 1e-9:
            fails.append("pagePartition")
    declared = _num("declaredSlots")
    empty_slots = _num("emptySlots")
    if None not in (declared, empty_slots):
        if empty_slots < -1e-12 or empty_slots > declared + 1e-9:
            fails.append("emptySlotsRange")
        rate = _num("emptySlotRate")
        if declared > 0 and rate is not None:
            if rate < -1e-12 or rate > 1 + 1e-12:
                fails.append("emptySlotRate")
            expected_rate = empty_slots / declared
            if abs(rate - expected_rate) > 1e-9:
                fails.append("emptySlotRate")
    planned = row.get("plannedPageCount")
    omitted = row.get("omittedPlannedPages")
    if planned is not None and rendered is not None and omitted is not None:
        if abs(float(omitted) - max(0, float(planned) - rendered)) > 1e-9:
            fails.append("omittedPlannedPages")
    return fails


def classify_status(
    *,
    input_reasons: Sequence[str],
    asset: AssetMetrics | None,
    pages: PageMetrics | None,
    rendered_page_count: int | None,
    pipeline_error: str | None,
    metric_reasons: Sequence[str] = (),
) -> tuple[RowStatus, str | None, bool, bool]:
    """Return (status, invalidReason, tripFail, integrityFail)."""
    if input_reasons:
        return "inputInvalid", ";".join(input_reasons), False, False
    if metric_reasons:
        return "metricInvalid", ";".join(metric_reasons), False, False
    if pipeline_error:
        return "pipelineFail", None, True, False
    if rendered_page_count is None or rendered_page_count <= 0:
        return "pipelineFail", None, True, False
    if asset is None or pages is None:
        return "metricInvalid", "missingComputedMetrics", False, False

    integrity: list[str] = []
    if asset.foreign_placed > 0:
        integrity.append("foreignPlaced")
    if asset.duplicate_placements > 0:
        integrity.append("duplicatePlacements")
    if asset.placed_eligible > asset.intake_n:
        integrity.append("placedEligible>intakeN")
    if pages.unknown_templates:
        integrity.append("unknownTemplate")
    if pages.overflow_slots:
        integrity.append("filled>slotCount")
    if pages.zero_slot_templates:
        integrity.append("emptySlotDeclaration")
    probe = {
        "status": "ok",
        "eligible": asset.eligible,
        "intakeN": asset.intake_n,
        "placedEligible": asset.placed_eligible,
        "coverage": asset.coverage,
        "unplacedEligible": asset.unplaced_eligible,
        "intakeLoss": asset.intake_loss,
        "overflowCapped": asset.overflow_capped,
        "placementGap": asset.placement_gap,
        "duplicatePlacements": asset.duplicate_placements,
        "foreignPlaced": asset.foreign_placed,
        "folderN": asset.folder_n,
        "preComposeExcluded": asset.pre_compose_excluded,
        "renderedPageCount": pages.rendered_page_count,
        "emptyRenderedPages": pages.empty_rendered_pages,
        "partialPages": pages.partial_pages,
        "fullPages": pages.full_pages,
        "declaredSlots": pages.declared_slots,
        "emptySlots": pages.empty_slots,
        "emptySlotRate": pages.empty_slot_rate,
        "plannedPageCount": pages.planned_page_count,
        "omittedPlannedPages": pages.omitted_planned_pages,
    }
    ident = identity_failures(probe)
    if ident:
        integrity.extend(f"identity:{name}" for name in ident)
    if pages.declared_slots == 0 and not pages.unknown_templates and not pages.zero_slot_templates:
        return "metricInvalid", "declaredSlots=0", False, False
    if integrity:
        return "outputInvalid", ";".join(dict.fromkeys(integrity)), False, True
    return "ok", None, False, False


def density_of(placed_eligible: int | None, rendered_page_count: int | None) -> float | None:
    if placed_eligible is None or not rendered_page_count:
        return None
    return placed_eligible / rendered_page_count


def median_ms(samples: Sequence[float]) -> float | None:
    vals = [float(x) for x in samples]
    if not vals:
        return None
    return float(median(vals))


def percentile(samples: Sequence[float], p: float) -> float | None:
    vals = sorted(float(x) for x in samples)
    if not vals:
        return None
    if len(vals) == 1:
        return vals[0]
    idx = (len(vals) - 1) * (p / 100.0)
    lo = int(idx)
    hi = min(lo + 1, len(vals) - 1)
    frac = idx - lo
    return vals[lo] * (1.0 - frac) + vals[hi] * frac


def build_compose_row(
    *,
    comparison_run_id: str,
    trip_id: str,
    pipeline: PipelineName,
    edition: str,
    status: RowStatus,
    input_snapshot_hash: str,
    eligible_sequence_hash: str,
    arm_config_hash: str,
    code_revision: str,
    series_catalog_hash: str,
    template_registry_hash: str,
    asset: AssetMetrics | None,
    pages: PageMetrics | None,
    eligible_chapter_count: int | None,
    chapter_fail: int | None,
    trip_fail: bool,
    integrity_fail: bool,
    error_code: str | None,
    error_stage: str | None,
    invalid_reason: str | None,
    plan_ms_samples: Sequence[float],
    series_id: str | None,
    selection_resolution: str | None,
    band: str | None = None,
    identity_fails: Sequence[str] = (),
) -> dict[str, Any]:
    """Assemble one EA-00 §11 row. Null what pipelineFail cannot compute."""
    plan_samples = [round(float(x), 3) for x in plan_ms_samples]
    null_assets = status == "pipelineFail" or asset is None
    row: dict[str, Any] = {
        "comparisonRunId": comparison_run_id,
        "tripId": trip_id,
        "pipeline": pipeline,
        "edition": edition,
        "surface": SURFACE_LANDSCAPE_16X9,
        "measurementStage": MEASUREMENT_STAGE_COMPOSE,
        "status": status,
        "inputSnapshotHash": input_snapshot_hash,
        "eligibleSequenceHash": eligible_sequence_hash,
        "armConfigHash": arm_config_hash,
        "codeRevision": code_revision,
        "seriesCatalogHash": series_catalog_hash,
        "templateRegistryHash": template_registry_hash,
        "caliberDoc": CALIBER_DOC,
        "band": band,
        "folderN": None if null_assets else asset.folder_n,
        "eligible": None if null_assets else asset.eligible,
        "intakeN": None if null_assets else asset.intake_n,
        "placedEligible": None if null_assets else asset.placed_eligible,
        "placedUnique": None if null_assets else asset.placed_unique,
        "placementOccurrences": None if null_assets else asset.placement_occurrences,
        "coverage": None if null_assets else asset.coverage,
        "duplicatePlacements": None if null_assets else asset.duplicate_placements,
        "foreignPlaced": None if null_assets else asset.foreign_placed,
        "preComposeExcluded": None if null_assets else asset.pre_compose_excluded,
        "cullDiscard": None if null_assets else asset.cull_discard,
        "intakeLoss": None if null_assets else asset.intake_loss,
        "capacityN": None if null_assets else asset.capacity_n,
        "overflowCapped": None if null_assets else asset.overflow_capped,
        "placementGap": None if null_assets else asset.placement_gap,
        "unplacedEligible": None if null_assets else asset.unplaced_eligible,
        "plannedPageCount": None if pages is None else pages.planned_page_count,
        "renderedPageCount": None if pages is None else pages.rendered_page_count,
        "pageCount": None if pages is None else pages.rendered_page_count,
        "omittedPlannedPages": None if pages is None else pages.omitted_planned_pages,
        "declaredSlots": None if pages is None else pages.declared_slots,
        "emptyRenderedPages": None if pages is None else pages.empty_rendered_pages,
        "partialPages": None if pages is None else pages.partial_pages,
        "fullPages": None if pages is None else pages.full_pages,
        "emptySlots": None if pages is None else pages.empty_slots,
        "emptySlotRate": None if pages is None else pages.empty_slot_rate,
        "pageDegraded": None if pages is None else pages.page_degraded,
        "eligibleChapterCount": eligible_chapter_count,
        "chapterFail": chapter_fail,
        "tripFail": trip_fail,
        "integrityFail": integrity_fail,
        "pageRenderFail": None,
        "attemptedRenderPages": None,
        "errorCode": error_code,
        "errorStage": error_stage,
        "invalidReason": invalid_reason,
        "planMsSamples": plan_samples,
        "planMsMedian": median_ms(plan_samples),
        "renderMs": None,
        "exportMs": None,
        "density": None
        if null_assets or pages is None
        else density_of(asset.placed_eligible, pages.rendered_page_count),
        "seriesId": series_id,
        "selectionResolution": selection_resolution,
        "duplicateAssetIds": [] if null_assets else list(asset.duplicate_asset_ids),
        "foreignAssetIds": [] if null_assets else list(asset.foreign_ids),
        "identityFailures": list(identity_fails),
        "unknownTemplates": [] if pages is None else list(pages.unknown_templates),
    }
    if status == "pipelineFail":
        for key in (
            "plannedPageCount",
            "renderedPageCount",
            "pageCount",
            "omittedPlannedPages",
            "declaredSlots",
            "emptyRenderedPages",
            "partialPages",
            "fullPages",
            "emptySlots",
            "emptySlotRate",
            "pageDegraded",
            "density",
            "eligibleChapterCount",
            "chapterFail",
        ):
            row[key] = None
    return row


def _valid_input_row(row: Mapping[str, Any] | None) -> bool:
    return bool(row) and row.get("status") not in {"inputInvalid", "metricInvalid"}


def _ok_row(row: Mapping[str, Any] | None) -> bool:
    return bool(row) and row.get("status") == "ok" and row.get("coverage") is not None


def paired_coverage_delta(series_row: Mapping[str, Any], mosaic_row: Mapping[str, Any]) -> float | None:
    """Coverage Δ for paired-ok only. Either arm not ok → None (render as —)."""
    if not _ok_row(series_row) or not _ok_row(mosaic_row):
        return None
    return float(series_row["coverage"]) - float(mosaic_row["coverage"])


def _coverage_rows(pipe_rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """all-valid coverage: valid input with a computable coverage (includes outputInvalid)."""
    return [
        r
        for r in pipe_rows
        if _valid_input_row(r) and r.get("coverage") is not None
    ]


def _coverage_block(xs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    placed = sum(int(r["placedEligible"] or 0) for r in xs)
    eligible = sum(int(r["eligible"] or 0) for r in xs)
    coverages = [float(r["coverage"]) for r in xs]
    return {
        "n": len(xs),
        "placedEligible": placed,
        "eligible": eligible,
        "microCoverage": (placed / eligible) if eligible else None,
        "macroCoverage": median_ms(coverages),
    }


def series_conservation(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """EA-00 §3 split over all-valid series rows. intakeLoss is observed, not folded in."""
    xs = _coverage_rows([r for r in rows if r.get("pipeline") == "series"])
    eligible = sum(int(r["eligible"] or 0) for r in xs)
    placed = sum(int(r["placedEligible"] or 0) for r in xs)
    overflow_capped = sum(int(r.get("overflowCapped") or 0) for r in xs)
    placement_gap = sum(int(r.get("placementGap") or 0) for r in xs)
    intake_loss = sum(int(r.get("intakeLoss") or 0) for r in xs)
    unplaced = eligible - placed
    return {
        "eligible": eligible,
        "placedEligible": placed,
        "overflowCapped": overflow_capped,
        "placementGap": placement_gap,
        "intakeLoss": intake_loss,
        "unplacedEligible": unplaced,
        "overflowCappedShare": (overflow_capped / unplaced) if unplaced else None,
        "placementGapShare": (placement_gap / unplaced) if unplaced else None,
    }


def aggregate_shadow_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    tie_tolerance: float,
) -> dict[str, Any]:
    """EA-00 §9: all-valid coverage vs paired-ok pairing. Density is never ranked.

    all-valid: every valid-input row with a coverage number (outputInvalid included).
    paired-ok: only trips where both arms are status=ok; used for Δ and win/tie/loss.
    Headline mosaic/series microCoverage is all-valid so both pipelines share a queue.
    """
    by_trip: dict[str, dict[str, Mapping[str, Any]]] = {}
    for row in rows:
        by_trip.setdefault(str(row.get("tripId") or ""), {})[str(row.get("pipeline") or "")] = row

    paired_ok_ids = [
        trip_id
        for trip_id, arms in by_trip.items()
        if _ok_row(arms.get("mosaic")) and _ok_row(arms.get("series"))
    ]

    def _pipe_rows(name: str, subset: Sequence[Mapping[str, Any]] | None = None) -> list[Mapping[str, Any]]:
        src = rows if subset is None else subset
        return [r for r in src if r.get("pipeline") == name]

    def _pipe_stats(name: str, subset: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
        pipe_rows = _pipe_rows(name, subset)
        ok_rows = [r for r in pipe_rows if _ok_row(r)]
        valid = [r for r in pipe_rows if _valid_input_row(r)]
        cov = _coverage_block(_coverage_rows(pipe_rows))
        plan = [float(r["planMsMedian"]) for r in pipe_rows if r.get("planMsMedian") is not None]
        fail = sum(1 for r in valid if r.get("status") == "pipelineFail")
        integrity = sum(1 for r in valid if r.get("status") == "outputInvalid")
        n_valid = len(valid)
        return {
            "pipeline": name,
            "okTrips": len(ok_rows),
            "validInputTrips": n_valid,
            "microCoverage": cov["microCoverage"],
            "macroCoverage": cov["macroCoverage"],
            "coverageN": cov["n"],
            "placedEligible": cov["placedEligible"],
            "eligible": cov["eligible"],
            "planMsMedian": median_ms(plan),
            "planMsP90": percentile(plan, 90),
            "tripFailRate": (fail / n_valid) if n_valid else None,
            "pipelineFailureRate": ((fail + integrity) / n_valid) if n_valid else None,
            "inputInvalid": sum(1 for r in pipe_rows if r.get("status") == "inputInvalid"),
            "metricInvalid": sum(1 for r in pipe_rows if r.get("status") == "metricInvalid"),
            "outputInvalid": integrity,
            "pipelineFail": fail,
        }

    def _paired_ok_pipe(name: str) -> dict[str, Any]:
        xs = [
            by_trip[tid][name]
            for tid in paired_ok_ids
            if name in by_trip[tid]
        ]
        cov = _coverage_block(xs)
        return {
            "pipeline": name,
            "n": cov["n"],
            "placedEligible": cov["placedEligible"],
            "eligible": cov["eligible"],
            "microCoverage": cov["microCoverage"],
            "macroCoverage": cov["macroCoverage"],
        }

    def _band_all_valid(band: str) -> dict[str, Any]:
        band_rows = [r for r in rows if r.get("band") == band]
        return {
            "band": band,
            "mosaic": _pipe_stats("mosaic", band_rows),
            "series": _pipe_stats("series", band_rows),
        }

    def _band_paired_ok(band: str) -> dict[str, Any]:
        ids = [tid for tid in paired_ok_ids if (by_trip[tid].get("series") or {}).get("band") == band
               or (by_trip[tid].get("mosaic") or {}).get("band") == band]
        xs = []
        for tid in ids:
            xs.extend(by_trip[tid].values())
        mosaic_xs = [r for r in xs if r.get("pipeline") == "mosaic"]
        series_xs = [r for r in xs if r.get("pipeline") == "series"]
        return {
            "band": band,
            "mosaic": _coverage_block(mosaic_xs),
            "series": _coverage_block(series_xs),
        }

    deltas: list[float] = []
    wins = ties = losses = 0
    paired: list[dict[str, Any]] = []
    for trip_id, arms in sorted(by_trip.items()):
        series = arms.get("series")
        mosaic = arms.get("mosaic")
        if not _ok_row(series) or not _ok_row(mosaic):
            paired.append(
                {
                    "tripId": trip_id,
                    "band": (series or mosaic or {}).get("band"),
                    "coverageDelta": None,
                    "planMsDelta": None,
                    "statusPair": [
                        None if mosaic is None else mosaic.get("status"),
                        None if series is None else series.get("status"),
                    ],
                }
            )
            continue
        delta = paired_coverage_delta(series, mosaic)
        assert delta is not None
        deltas.append(delta)
        if abs(delta) <= tie_tolerance:
            ties += 1
            verdict = "tie"
        elif delta > 0:
            wins += 1
            verdict = "series"
        else:
            losses += 1
            verdict = "mosaic"
        plan_s = series.get("planMsMedian")
        plan_m = mosaic.get("planMsMedian")
        plan_delta = (
            None if plan_s is None or plan_m is None else float(plan_s) - float(plan_m)
        )
        paired.append(
            {
                "tripId": trip_id,
                "band": series.get("band") or mosaic.get("band"),
                "coverageSeries": series.get("coverage"),
                "coverageMosaic": mosaic.get("coverage"),
                "coverageDelta": delta,
                "planMsDelta": plan_delta,
                "verdict": verdict,
            }
        )

    bands = ["sparse-60-140", "regular-196-326", "overflow-424-1000"]
    mosaic_stats = _pipe_stats("mosaic")
    series_stats = _pipe_stats("series")
    return {
        "caliberDoc": CALIBER_DOC,
        "tieTolerance": tie_tolerance,
        "scoringNote": "density/pageCount/emptySlotRate are recorded, never ranked",
        "coverageSetNote": (
            "allValid = valid-input rows with coverage (outputInvalid included); "
            "pairedOk = both arms status=ok (win/tie/loss and coverage Δ only)"
        ),
        "mosaic": mosaic_stats,
        "series": series_stats,
        "coverageSets": {
            "allValid": {
                "mosaic": {
                    "n": mosaic_stats["coverageN"],
                    "placedEligible": mosaic_stats["placedEligible"],
                    "eligible": mosaic_stats["eligible"],
                    "microCoverage": mosaic_stats["microCoverage"],
                    "macroCoverage": mosaic_stats["macroCoverage"],
                },
                "series": {
                    "n": series_stats["coverageN"],
                    "placedEligible": series_stats["placedEligible"],
                    "eligible": series_stats["eligible"],
                    "microCoverage": series_stats["microCoverage"],
                    "macroCoverage": series_stats["macroCoverage"],
                },
            },
            "pairedOk": {
                "nPairs": len(paired_ok_ids),
                "tripIds": sorted(paired_ok_ids),
                "mosaic": _paired_ok_pipe("mosaic"),
                "series": _paired_ok_pipe("series"),
                "bands": [_band_paired_ok(b) for b in bands],
            },
        },
        "seriesConservation": series_conservation(rows),
        "pairedCoverageDeltaMedian": median_ms(deltas),
        "pairedCoverageDeltaQ1": percentile(deltas, 25),
        "pairedCoverageDeltaQ3": percentile(deltas, 75),
        "winTieLoss": {"series": wins, "tie": ties, "mosaic": losses},
        "bands": [_band_all_valid(b) for b in bands],
        "pairs": paired,
        "inputInvalidTrips": sorted(
            {
                str(r.get("tripId"))
                for r in rows
                if r.get("status") == "inputInvalid"
            }
        ),
        "metricInvalidTrips": sorted(
            {
                str(r.get("tripId"))
                for r in rows
                if r.get("status") == "metricInvalid"
            }
        ),
    }


def as_jsonable(row: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(row)
    return payload


def dataclass_row(obj: Any) -> dict[str, Any]:
    return asdict(obj)
