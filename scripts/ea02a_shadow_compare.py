#!/usr/bin/env python3
"""EA-02a · landscape-16x9 series vs mosaic shadow compare.

Reads ``trips/<id>/trip.json``. Builds one compose-ready snapshot per trip,
deep-copies it for each arm and each timing run, then records EA-00 metrics.
Never writes ``trip.json``. Not a pytest. Do not import from
``pipeline_isolation`` tests.

Usage:
    python scripts/ea02a_shadow_compare.py
    python scripts/ea02a_shadow_compare.py --quick --trips demo-album
    python scripts/ea02a_shadow_compare.py --runs 3 --warmup 1
    python scripts/ea02a_shadow_compare.py --from-jsonl docs/acceptance-records/ea-02a-shadow-compare-2026-09-01.jsonl
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
import time
from dataclasses import dataclass, replace
from datetime import date, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import ea00_folio_metrics as folio

# Declared before seeing results (EA-00 §9.1). Do not retune after a run.
TIE_TOLERANCE = 0.02
SURFACE = folio.SURFACE_LANDSCAPE_16X9
CALIBER_DOC = folio.CALIBER_DOC

# Asset-file counts from 收敛任务清单 EA-02a. Band is the grouping key, not a score.
TRIP_TABLE: tuple[tuple[str, str, int], ...] = (
    ("demo-album", "sparse-60-140", 60),
    ("demo-20ecc928d6", "sparse-60-140", 96),
    ("demo-d21946c6a9", "sparse-60-140", 104),
    ("demo-03ca76b26d", "sparse-60-140", 118),
    ("demo-49551086fe", "sparse-60-140", 124),
    ("demo-005", "sparse-60-140", 126),
    ("demo-1b67b06546", "sparse-60-140", 140),
    ("demo-817f1f8801", "regular-196-326", 196),
    ("demo-65db8fd377", "regular-196-326", 204),
    ("demo-1bfe89d31c", "regular-196-326", 204),
    ("_bai_w1b_titleart", "regular-196-326", 232),
    ("demo-3ee2727aea", "regular-196-326", 326),
    ("demo-81d3442e92", "overflow-424-1000", 424),
    ("demo-e52494839a", "overflow-424-1000", 536),
    ("demo-0ebda73294", "overflow-424-1000", 540),
    ("demo-6395848778", "overflow-424-1000", 630),
    ("demo-9a32512fea", "overflow-424-1000", 806),
    ("demo-de855740dc", "overflow-424-1000", 806),
    ("demo-2019", "overflow-424-1000", 864),
    ("demo-1d4f92d534", "overflow-424-1000", 1000),
)
BAND_BY_TRIP = {tid: band for tid, band, _n in TRIP_TABLE}
FILES_BY_TRIP = {tid: n for tid, _band, n in TRIP_TABLE}


def canonical_json(obj: Any) -> str:
    def conv(value: Any) -> Any:
        if isinstance(value, dict):
            return {str(k): conv(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
        if isinstance(value, (list, tuple)):
            return [conv(v) for v in value]
        if isinstance(value, (set, frozenset)):
            return [conv(v) for v in sorted(value, key=lambda x: str(x))]
        if isinstance(value, Path):
            return value.as_posix()
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)

    return json.dumps(conv(obj), ensure_ascii=False, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def code_revision(root: Path) -> str:
    try:
        head = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=root, text=True
        ).strip()
        dirty = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=root, text=True
        ).strip()
        return f"{head}+dirty" if dirty else head
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def series_catalog_hash() -> str:
    from travelogue.layout_engine.editorial_series.catalog import official_series_dir

    root = official_series_dir()
    digest = hashlib.sha256()
    for path in sorted(root.glob("*.yaml")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def template_registry_hash() -> str:
    from travelogue.layout_templates.registry import DEFAULT_TEMPLATES_DIR, _content_hash

    return _content_hash(DEFAULT_TEMPLATES_DIR)


def with_portfolio_enabled(cfg: Any) -> Any:
    studio = cfg.studio
    pipe = replace(studio.portfolio_pipeline, enabled=True)
    return replace(cfg, studio=replace(studio, portfolio_pipeline=pipe))


def arm_config_hash(*, pipeline: str, edition: str, cfg: Any) -> str:
    scoring = cfg.layout.scoring
    mosaic = cfg.mosaic
    pipe = cfg.studio.portfolio_pipeline
    payload = {
        "pipeline": pipeline,
        "edition": edition,
        "portfolioPipelineEnabled": bool(pipe.enabled),
        "mosaicEnabled": bool(mosaic.enabled),
        "scoringEnabled": bool(scoring.enabled),
        "beamWidth": int(scoring.beam_width),
        "searchTimeoutMs": int(scoring.search_timeout_ms),
        "maxEvaluationsPerTrip": int(scoring.max_evaluations_per_trip),
        "maxPages": int(pipe.max_pages or 48),
    }
    return sha256_text(canonical_json(payload))


@dataclass
class ComposeSnapshot:
    trip_id: str
    trip: dict[str, Any]
    chapters: list[dict[str, Any]]
    buckets: list[list[str]]
    aspects: dict[str, Any]
    assets: list[dict[str, Any]]
    app_cfg: Any
    skip_screen_ids: set[str]
    ready: Any
    preflight: Any
    eligible_ids: list[str]
    input_reasons: list[str]
    input_snapshot_hash: str
    eligible_sequence_hash: str


class RegistrySlotCount:
    def __init__(self) -> None:
        self.error: str | None = None
        try:
            from travelogue.layout_templates.registry import get_engine

            self.engine = get_engine()
        except Exception as exc:  # noqa: BLE001 — collector must not crash the run
            self.engine = None
            self.error = f"{type(exc).__name__}:{exc}"

    def __call__(self, pattern_id: str) -> int | None:
        if self.engine is None:
            return None
        try:
            return len(self.engine.get(pattern_id).slots)
        except KeyError:
            return None


@dataclass
class ArmAttempt:
    ok: bool
    chapters: list[dict[str, Any]] | None
    meta: dict[str, Any] | None
    trip: dict[str, Any] | None
    plan_ms: float
    error_code: str | None
    error_message: str | None


def load_trip(trip_dir: Path) -> dict[str, Any]:
    path = trip_dir / "trip.json"
    return json.loads(path.read_text(encoding="utf-8"))


def build_snapshot(
    trip_raw: dict[str, Any],
    *,
    trip_dir: Path,
    cfg: Any,
) -> ComposeSnapshot:
    from travelogue.config.edition import apply_refine_edition
    from travelogue.curation.album_profile import write_album_profile
    from travelogue.curation.compose_stages import (
        align_non_empty_buckets,
        peel_time_outliers,
        prepare_compose_draft,
        resolve_compose_scoring,
    )
    from travelogue.curation.curate import (
        _build_curate_buckets,
        _curate_preflight,
        _stage_aesthetic_align,
    )
    from travelogue.curation.curate_stages import stage_refresh_cull_cohort
    from travelogue.curation.curation_adapter import apply_curation_adapter_hints
    from travelogue.curation.intent_hints import (
        apply_editorial_intent_hints,
        prior_chapter_memory_anchors,
    )

    trip = copy.deepcopy(trip_raw)
    apply_refine_edition(trip, "journal", cfg)
    trip.pop("chapters", None)
    apply_curation_adapter_hints(trip, cfg=cfg)
    apply_editorial_intent_hints(trip)
    saved_memory_anchors = prior_chapter_memory_anchors(trip)
    cohort_summary = stage_refresh_cull_cohort(
        trip,
        trip_dir=trip_dir,
        cfg=cfg,
        curate_scope="full",
        refresh_algorithms=False,
    )
    preflight = _curate_preflight(
        trip,
        export_layout="web",
        layout_engine="screens",
        trip_dir=trip_dir,
        cfg=cfg,
        saved_memory_anchors=saved_memory_anchors,
    )
    _stage_aesthetic_align(trip, trip_dir=trip_dir, app_cfg=preflight.app_cfg)
    bucket_plan = _build_curate_buckets(trip, preflight)
    write_album_profile(trip)
    if cohort_summary:
        trip.setdefault("curation", {})["cohort"] = cohort_summary
    aligned = align_non_empty_buckets(bucket_plan, preflight)
    peeled = peel_time_outliers(aligned, preflight)
    draft = prepare_compose_draft(
        trip, preflight, peeled, cohort_summary=cohort_summary
    )
    ready = resolve_compose_scoring(
        trip,
        preflight,
        draft,
        curate_scope="full",
        cohort_summary=cohort_summary,
    )
    eligible_ids, input_reasons = folio.eligible_id_list(trip)
    if not eligible_ids:
        input_reasons = list(input_reasons) + ["eligible=0"]
    payload = {
        "eligibleIds": eligible_ids,
        "buckets": ready.non_empty_buckets,
        "skipScreenIds": sorted(preflight.skip_screen_ids),
        "assets": [
            {
                "id": a.get("id"),
                "layoutEligible": a.get("layoutEligible", True),
                "type": a.get("type", "image"),
            }
            for a in (trip.get("assets") or [])
            if isinstance(a, dict)
        ],
        "chapterScreens": [
            {
                "id": ch.get("id"),
                "screens": [
                    {
                        "patternId": s.get("patternId"),
                        "assetIds": folio.slot_asset_ids([s]),
                    }
                    for s in (ch.get("screens") or [])
                ],
            }
            for ch in ready.chapters
        ],
    }
    return ComposeSnapshot(
        trip_id=trip_dir.name,
        trip=trip,
        chapters=ready.chapters,
        buckets=ready.non_empty_buckets,
        aspects=ready.aspects,
        assets=list(preflight.layout_assets),
        app_cfg=preflight.app_cfg,
        skip_screen_ids=set(preflight.skip_screen_ids),
        ready=ready,
        preflight=preflight,
        eligible_ids=eligible_ids,
        input_reasons=input_reasons,
        input_snapshot_hash=sha256_text(canonical_json(payload)),
        eligible_sequence_hash=sha256_text(canonical_json(eligible_ids)),
    )


def mosaic_intake_ids(buckets: list[list[str]]) -> list[str]:
    ids: list[str] = []
    for bucket in buckets:
        ids.extend(str(x) for x in bucket if str(x).strip())
    return ids


def series_intake_ids(
    assets: list[dict[str, Any]],
    trip: dict[str, Any],
    buckets: list[list[str]],
) -> list[str]:
    """Same grouping as compose_portfolio_trip (observe intake, do not change it)."""
    from travelogue.layout_engine.editorial_series.fill import (
        fill_groups_from_assets,
        is_sparse_collection,
        pack_thin_fill_groups,
    )
    from travelogue.layout_engine.editorial_series.match import groups_from_assets

    if is_sparse_collection(assets):
        groups = groups_from_assets(assets, buckets=buckets)
    else:
        groups = pack_thin_fill_groups(
            fill_groups_from_assets(assets, trip=trip, buckets=buckets),
            buckets=buckets,
        )
    ids: list[str] = []
    for group in groups:
        ids.extend(str(x) for x in (group.get("asset_ids") or []) if str(x).strip())
    return ids


def series_planned_and_capacity(series_id: str | None, meta: dict[str, Any]) -> tuple[int | None, int | None]:
    fulfill = meta.get("sequenceFulfillment") or {}
    planned = fulfill.get("plannedPages")
    overflow = meta.get("overflow") or {}
    cap = overflow.get("capacity")
    if planned is not None and cap:
        return int(planned), int(cap)
    if not series_id:
        return (int(planned) if planned is not None else None, int(cap) if cap else None)
    from travelogue.layout_engine.editorial_series.catalog import load_official_series
    from travelogue.layout_engine.editorial_series.match import series_capacity

    for row in load_official_series():
        if str(row.get("id") or "") == series_id:
            seq = row.get("sequence") or []
            return len(seq), series_capacity(row) or None
    return (int(planned) if planned is not None else None, int(cap) if cap else None)


def mosaic_page_degraded(screens: list[dict[str, Any]]) -> int:
    n = 0
    for screen in screens:
        log = screen.get("log") if isinstance(screen.get("log"), dict) else {}
        if screen.get("fallbackUsed") or log.get("fallbackUsed"):
            n += 1
    return n


def run_mosaic(snapshot: ComposeSnapshot) -> ArmAttempt:
    from travelogue.config.edition import apply_refine_edition
    from travelogue.config.moment import effective_secondary_boost
    from travelogue.layout_engine.api import compose_trip

    trip = copy.deepcopy(snapshot.trip)
    apply_refine_edition(trip, "journal", snapshot.app_cfg)
    chapters = copy.deepcopy(snapshot.chapters)
    buckets = copy.deepcopy(snapshot.buckets)
    aspects = copy.deepcopy(snapshot.aspects)
    assets = copy.deepcopy(snapshot.assets)
    ready = snapshot.ready
    preflight = snapshot.preflight
    t0 = time.perf_counter_ns()
    try:
        out_chapters, meta = compose_trip(
            chapters,
            buckets=buckets,
            aspects=aspects,
            assets=assets,
            app_cfg=snapshot.app_cfg,
            scoring_enabled=ready.layout_cfg.scoring.enabled,
            weights=ready.scoring_weights,
            beam_width=ready.layout_cfg.scoring.beam_width,
            degradation=ready.degradation,
            arc_mode=preflight.cur_cfg.arc_mode,
            arc_profile=ready.arc_profile,
            chapter_heroes=copy.deepcopy(ready.chapter_heroes),
            orientation_summary=ready.summary_dict,
            skip_screen_asset_ids=set(snapshot.skip_screen_ids),
            mixed_proximity_seconds=ready.layout_cfg.mixed_proximity_seconds,
            trip_photo_total=len(assets),
            search_timeout_ms=ready.layout_cfg.scoring.search_timeout_ms,
            max_candidates_per_bucket=ready.layout_cfg.scoring.max_candidates_per_bucket,
            max_evaluations_per_trip=ready.layout_cfg.scoring.max_evaluations_per_trip,
            allow_burst_split=ready.layout_cfg.scoring.allow_burst_split,
            wall_clock_limits_output=ready.layout_cfg.scoring.wall_clock_limits_output,
            subject_run_tolerance=ready.layout_cfg.scoring.subject_run_tolerance,
            enable_food_grid=preflight.cur_cfg.enable_food_grid,
            mundane_grid_buckets=preflight.cur_cfg.mundane_grid_buckets,
            intent_peak_chapters=ready.intent_peak,
            enable_gravity_balance=preflight.cur_cfg.enable_gravity_balance,
            max_consecutive_same_pattern=preflight.cur_cfg.max_consecutive_same_pattern,
            skip_duplicate_signatures=ready.layout_cfg.scoring.skip_duplicate_signatures,
            incremental_scoring=ready.layout_cfg.scoring.incremental,
            max_evaluations_per_segment=ready.layout_cfg.scoring.max_evaluations_per_segment,
            moment_secondary_ids=set(ready.secondary_hints),
            moment_secondary_boost=effective_secondary_boost(preflight.cur_cfg.moment),
        )
        ms = (time.perf_counter_ns() - t0) / 1e6
        return ArmAttempt(True, out_chapters, meta or {}, trip, ms, None, None)
    except Exception as exc:  # noqa: BLE001 — tripFail must be recorded, not raised
        ms = (time.perf_counter_ns() - t0) / 1e6
        return ArmAttempt(False, None, None, trip, ms, type(exc).__name__, str(exc))


def run_series(snapshot: ComposeSnapshot) -> ArmAttempt:
    from travelogue.config.edition import apply_refine_edition
    from travelogue.layout_engine.editorial_series import compose_portfolio_trip

    cfg = with_portfolio_enabled(snapshot.app_cfg)
    trip = copy.deepcopy(snapshot.trip)
    apply_refine_edition(trip, "portfolio", cfg)
    chapters = copy.deepcopy(snapshot.chapters)
    t0 = time.perf_counter_ns()
    try:
        out_chapters, meta = compose_portfolio_trip(
            chapters,
            buckets=copy.deepcopy(snapshot.buckets),
            aspects=copy.deepcopy(snapshot.aspects),
            assets=copy.deepcopy(snapshot.assets),
            app_cfg=cfg,
            trip=trip,
        )
        ms = (time.perf_counter_ns() - t0) / 1e6
        return ArmAttempt(True, out_chapters, meta or {}, trip, ms, None, None)
    except Exception as exc:  # noqa: BLE001 — tripFail must be recorded, not raised
        ms = (time.perf_counter_ns() - t0) / 1e6
        return ArmAttempt(False, None, None, trip, ms, type(exc).__name__, str(exc))


def _pick_attempt(ok: ArmAttempt | None, any_attempt: ArmAttempt | None) -> ArmAttempt | None:
    return ok or any_attempt


def measure_pair(
    snapshot: ComposeSnapshot,
    *,
    warmup: int,
    runs: int,
    log: Any,
) -> tuple[tuple[list[float], ArmAttempt | None], tuple[list[float], ArmAttempt | None]]:
    """Warmup then official runs, mosaic/series alternating (EA-00 §6)."""
    samples: dict[str, list[float]] = {"mosaic": [], "series": []}
    last_ok: dict[str, ArmAttempt | None] = {"mosaic": None, "series": None}
    last_any: dict[str, ArmAttempt | None] = {"mosaic": None, "series": None}
    runners = {"mosaic": run_mosaic, "series": run_series}

    def _once(pipeline: str, label: str) -> None:
        attempt = runners[pipeline](snapshot)
        last_any[pipeline] = attempt
        if attempt.ok:
            last_ok[pipeline] = attempt
        if label.startswith("run"):
            samples[pipeline].append(attempt.plan_ms)
        log(f"    {pipeline} {label} {attempt.plan_ms:.0f}ms ok={attempt.ok}")

    for i in range(max(0, warmup)):
        _once("mosaic", f"warmup {i + 1}")
        _once("series", f"warmup {i + 1}")
    official = max(1, runs)
    for i in range(official):
        _once("mosaic", f"run {i + 1}/{official}")
        _once("series", f"run {i + 1}/{official}")
    return (
        (samples["mosaic"], _pick_attempt(last_ok["mosaic"], last_any["mosaic"])),
        (samples["series"], _pick_attempt(last_ok["series"], last_any["series"])),
    )


def row_from_attempt(
    *,
    snapshot: ComposeSnapshot,
    pipeline: str,
    attempt: ArmAttempt | None,
    samples: list[float],
    slot_count_for: RegistrySlotCount,
    comparison_run_id: str,
    code_rev: str,
    catalog_hash: str,
    registry_hash: str,
    hash_mismatch: list[str],
) -> dict[str, Any]:
    edition = "journal" if pipeline == "mosaic" else "portfolio"
    cfg = snapshot.app_cfg if pipeline == "mosaic" else with_portfolio_enabled(snapshot.app_cfg)
    input_reasons = list(snapshot.input_reasons)
    input_reasons.extend(hash_mismatch)
    metric_reasons: list[str] = []
    if slot_count_for.error:
        metric_reasons.append(f"registry:{slot_count_for.error}")

    if input_reasons:
        status, reason, trip_fail, integrity = folio.classify_status(
            input_reasons=input_reasons,
            asset=None,
            pages=None,
            rendered_page_count=None,
            pipeline_error=None,
        )
        return folio.build_compose_row(
            comparison_run_id=comparison_run_id,
            trip_id=snapshot.trip_id,
            pipeline=pipeline,  # type: ignore[arg-type]
            edition=edition,
            status=status,
            input_snapshot_hash=snapshot.input_snapshot_hash,
            eligible_sequence_hash=snapshot.eligible_sequence_hash,
            arm_config_hash=arm_config_hash(pipeline=pipeline, edition=edition, cfg=cfg),
            code_revision=code_rev,
            series_catalog_hash=catalog_hash,
            template_registry_hash=registry_hash,
            asset=None,
            pages=None,
            eligible_chapter_count=None,
            chapter_fail=None,
            trip_fail=trip_fail,
            integrity_fail=integrity,
            error_code=None,
            error_stage="snapshot",
            invalid_reason=reason,
            plan_ms_samples=samples,
            series_id=None,
            selection_resolution=None,
            band=BAND_BY_TRIP.get(snapshot.trip_id),
        )

    if attempt is None or not attempt.ok or attempt.chapters is None:
        err = None if attempt is None else attempt.error_code
        status, reason, trip_fail, integrity = folio.classify_status(
            input_reasons=[],
            asset=None,
            pages=None,
            rendered_page_count=0,
            pipeline_error=err or "empty",
            metric_reasons=metric_reasons,
        )
        return folio.build_compose_row(
            comparison_run_id=comparison_run_id,
            trip_id=snapshot.trip_id,
            pipeline=pipeline,  # type: ignore[arg-type]
            edition=edition,
            status=status,
            input_snapshot_hash=snapshot.input_snapshot_hash,
            eligible_sequence_hash=snapshot.eligible_sequence_hash,
            arm_config_hash=arm_config_hash(pipeline=pipeline, edition=edition, cfg=cfg),
            code_revision=code_rev,
            series_catalog_hash=catalog_hash,
            template_registry_hash=registry_hash,
            asset=None,
            pages=None,
            eligible_chapter_count=None,
            chapter_fail=None,
            trip_fail=True,
            integrity_fail=False,
            error_code=err,
            error_stage="plan",
            invalid_reason=reason,
            plan_ms_samples=samples,
            series_id=None,
            selection_resolution=None,
            band=BAND_BY_TRIP.get(snapshot.trip_id),
        )

    screens = folio.iter_content_screens(attempt.chapters)
    meta = attempt.meta or {}
    series_id = str(meta.get("seriesId") or "") or None
    if pipeline == "series":
        intake = series_intake_ids(snapshot.assets, attempt.trip or snapshot.trip, snapshot.buckets)
        planned, capacity = series_planned_and_capacity(series_id, meta)
        fulfill = meta.get("sequenceFulfillment") or {}
        degraded = fulfill.get("demotedPages")
        page_degraded = int(degraded) if degraded is not None else None
        resolution = None
        overflow = meta.get("overflow")
        if isinstance(overflow, dict):
            resolution = overflow.get("resolution")
    else:
        intake = mosaic_intake_ids(snapshot.buckets)
        planned, capacity = None, None
        page_degraded = mosaic_page_degraded(screens)
        resolution = None

    asset = folio.compute_asset_metrics(
        trip=snapshot.trip,
        eligible_ids=snapshot.eligible_ids,
        intake_ids=intake,
        slot_asset_ids_=folio.slot_asset_ids(screens),
        capacity_n=capacity,
    )
    pages = folio.compute_page_metrics(
        screens=screens,
        slot_count_for=slot_count_for,
        planned_page_count=planned,
        page_degraded=page_degraded,
    )
    ch_idx = folio.eligible_chapter_indices(
        snapshot.chapters, snapshot.buckets, snapshot.eligible_ids
    )
    ch_fail = folio.chapter_fail_count(
        eligible_indices=ch_idx, output_chapters=attempt.chapters
    )
    status, reason, trip_fail, integrity = folio.classify_status(
        input_reasons=[],
        asset=asset,
        pages=pages,
        rendered_page_count=pages.rendered_page_count,
        pipeline_error=None,
        metric_reasons=metric_reasons,
    )
    probe = {
        "status": status,
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
    ident = folio.identity_failures(probe)
    return folio.build_compose_row(
        comparison_run_id=comparison_run_id,
        trip_id=snapshot.trip_id,
        pipeline=pipeline,  # type: ignore[arg-type]
        edition=edition,
        status=status,
        input_snapshot_hash=snapshot.input_snapshot_hash,
        eligible_sequence_hash=snapshot.eligible_sequence_hash,
        arm_config_hash=arm_config_hash(pipeline=pipeline, edition=edition, cfg=cfg),
        code_revision=code_rev,
        series_catalog_hash=catalog_hash,
        template_registry_hash=registry_hash,
        asset=asset,
        pages=pages,
        eligible_chapter_count=len(ch_idx),
        chapter_fail=ch_fail,
        trip_fail=trip_fail,
        integrity_fail=integrity,
        error_code=None,
        error_stage=None if status == "ok" else "plan",
        invalid_reason=reason,
        plan_ms_samples=samples,
        series_id=series_id,
        selection_resolution=str(resolution) if resolution else None,
        band=BAND_BY_TRIP.get(snapshot.trip_id),
        identity_fails=ident,
    )


def invalidate_hash_pairs(rows: list[dict[str, Any]]) -> None:
    by_trip: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_trip.setdefault(str(row["tripId"]), []).append(row)
    for pair in by_trip.values():
        if len(pair) < 2:
            continue
        hashes = {row["inputSnapshotHash"] for row in pair}
        seqs = {row["eligibleSequenceHash"] for row in pair}
        if len(hashes) == 1 and len(seqs) == 1:
            continue
        for row in pair:
            row["status"] = "inputInvalid"
            row["invalidReason"] = "snapshotOrEligibleHashMismatch"
            row["errorStage"] = "snapshot"
            row["tripFail"] = False
            row["integrityFail"] = False


def render_markdown(
    *,
    rows: list[dict[str, Any]],
    summary: dict[str, Any],
    comparison_run_id: str,
    warmup: int,
    runs: int,
    skipped: list[str],
    unofficial: bool,
) -> str:
    def pct(val: Any) -> str:
        if val is None:
            return "—"
        return f"{100 * float(val):.1f}%"

    def num(val: Any, digits: int = 0) -> str:
        if val is None:
            return "—"
        if digits == 0:
            return str(int(round(float(val))))
        return f"{float(val):.{digits}f}"

    lines = [
        "# EA-02a 横版 series vs mosaic 影子对照",
        "",
        "| 属性 | 内容 |",
        "|------|------|",
        f"| 日期 | {date.today().isoformat()} |",
        f"| 任务 | [收敛任务清单.md](../收敛任务清单.md) `EA-02a` |",
        f"| 口径 | [成册指标口径定义.md](../成册指标口径定义.md) |",
        f"| comparisonRunId | `{comparison_run_id}` |",
        f"| surface | `{SURFACE}` · `measurementStage=compose` |",
        f"| 计时 | 预热 {warmup} + 正式 {runs} · `perf_counter_ns` · 主值 planMsMedian |",
        f"| tieTolerance | {TIE_TOLERANCE}（跑前声明，见结果不得改） |",
        f"| 代码 | `{rows[0]['codeRevision'] if rows else 'unknown'}` |",
        f"| dataRowsHash | `{summary.get('dataRowsHash') or '—'}` |",
        f"| 结论 | **已完成 · 有阻断性发现 · 非质量通过** |",
        "",
        "## 怎么读",
        "",
        "1. **这不是谁更好看的排名。** coverage / 失败 / 耗时按 EA-00 采集；density、页数、emptySlotRate 只记录，不评分。",
        "2. 每趟旅行从同一份 compose 前快照深拷贝，两臂交替。采集时点是 `compose_trip` / `compose_portfolio_trip` 刚返回的内容屏。",
        "3. series 的 overflowCapped 与 placementGap 用口径 §3 公式拆开，不用 `overflow.resolution`。",
        "4. **两套覆盖率不得混用**：`all-valid` 纳入全部有效输入（`outputInvalid` 仍算 coverage，完整性失败另报）；`paired-ok` 只纳入两侧均为 `ok` 的配对，专供 Δ 与 win/tie/loss。总览主表是 all-valid。",
        "5. **mosaic 的 planMs 只覆盖 `compose_trip` 二次 beam**。窗级 MCS 发生在公共快照的 `build_chapters_from_buckets`，两边共享，不计进 planMs。series 的 planMs 才是选系列 + 装填全过程。因此 planMs 不能解释成「谁排一整本更快」。",
        "6. 任务清单量级按**磁盘资产文件数**分组；行内 `folderN` 是 `trip.assets` 图片记录数，两者不必相等。",
        "7. 对照行的 `tripId` 使用 `trips/<id>/` 目录名，避免克隆旅行共用 JSON `tripId` 把两趟合并作废。",
        "",
        "## 阻断性发现（不是门槛，禁止当排名）",
        "",
        "行级数据足以改变阶段 5 顺序；本页 **不是** series 或 mosaic 的质量通过证明。",
        "",
        "- **容量策略 vs 装填失败必须拆开。** 阶段 5 不从 `SE-01` 三种性格起手：先 `SE-00a` 收敛容量内 `placementGap`，再 `SE-00b` 拍板超量容量策略（舍弃 / 拆卷 / 扩容），最后才进入均衡、人物、风景。",
        "- **纯 placement gap**（`overflowCapped=0`，容量几乎没用尽）：`_bai_w1b_titleart`（gap 44）、`demo-3ee2727aea`（gap 36）。",
        "- **gap 主导的混合原因**：`demo-65db8fd377`（overflowCapped=2 + placementGap=30）。不要当成干净容量内失败。",
        "- **capped 不可忽略的混合原因**：`demo-1d4f92d534`、`demo-0ebda73294`。不要和纯 gap 捆成同一个修复。`demo-005` 是稀疏档小缺口，适合当回归样例。",
        "- **mosaic 可作覆盖参照，不能当健康基线。** 最小修复：要么注册 `screen-square-1`，要么禁止规划器产出；compose 边界加全册 asset ID 唯一性断言。",
        "- mosaic `planMs≈0` 不能读成「游记排版零成本」——重活在共享快照的窗级 MCS。",
    ]
    if unofficial:
        lines += [
            "",
            f"> **非正式计时**：本次 `--runs {runs}` / `--warmup {warmup}`，未满足口径默认预热 1 + 正式 3。覆盖与失败数字仍按同一口径；planMs 不能当正式对照。",
        ]
    lines += ["", "## 总览", ""]
    mosaic = summary["mosaic"]
    series = summary["series"]
    cons = summary.get("seriesConservation") or {}
    paired_ok = (summary.get("coverageSets") or {}).get("pairedOk") or {}
    lines += [
        "### all-valid coverage（正式验收主表 · 同一有效输入队列）",
        "",
        "`outputInvalid` 的 coverage 仍计入分子分母；完整性失败只出现在 pipelineFailureRate。",
        "",
        "| 管线 | 有效输入 | ok | coverage N | microCoverage | macroCoverage | tripFailRate | pipelineFailureRate | planMs 中位 | planMs P90 |",
        "|------|----------|----|------------|---------------|---------------|--------------|---------------------|-------------|------------|",
        f"| mosaic | {mosaic['validInputTrips']} | {mosaic['okTrips']} | {mosaic.get('coverageN', '—')} | {pct(mosaic['microCoverage'])} | {pct(mosaic['macroCoverage'])} | {pct(mosaic['tripFailRate'])} | {pct(mosaic['pipelineFailureRate'])} | {num(mosaic['planMsMedian'], 1)} | {num(mosaic['planMsP90'], 1)} |",
        f"| series | {series['validInputTrips']} | {series['okTrips']} | {series.get('coverageN', '—')} | {pct(series['microCoverage'])} | {pct(series['macroCoverage'])} | {pct(series['tripFailRate'])} | {pct(series['pipelineFailureRate'])} | {num(series['planMsMedian'], 1)} | {num(series['planMsP90'], 1)} |",
        "",
        "### series 资产守恒（all-valid）",
        "",
        f"`eligible {cons.get('eligible', '—')} = placed {cons.get('placedEligible', '—')}"
        f" + overflowCapped {cons.get('overflowCapped', '—')}"
        f" + placementGap {cons.get('placementGap', '—')}"
        f" + intakeLoss {cons.get('intakeLoss', '—')}`",
        "",
        f"未入册 {cons.get('unplacedEligible', '—')} 张中："
        f" overflowCapped {pct(cons.get('overflowCappedShare'))}（产品策略），"
        f" placementGap {pct(cons.get('placementGapShare'))}（工程鲁棒性）。",
        "",
        "### paired-ok coverage（仅两侧均为 ok · Δ 与胜负）",
        "",
        f"{paired_ok.get('nPairs', 0)} 对。win / tie / loss（series 相对 mosaic，容差 {TIE_TOLERANCE}）："
        f" **{summary['winTieLoss']['series']}** / **{summary['winTieLoss']['tie']}** / **{summary['winTieLoss']['mosaic']}**",
        "",
        f"配对 coverage 差（series − mosaic）：中位 {pct(summary['pairedCoverageDeltaMedian'])} · Q1 {pct(summary['pairedCoverageDeltaQ1'])} · Q3 {pct(summary['pairedCoverageDeltaQ3'])}",
        "",
        "| 管线 | N | microCoverage | macroCoverage |",
        "|------|---|---------------|---------------|",
        f"| mosaic | {(paired_ok.get('mosaic') or {}).get('n', '—')} | {pct((paired_ok.get('mosaic') or {}).get('microCoverage'))} | {pct((paired_ok.get('mosaic') or {}).get('macroCoverage'))} |",
        f"| series | {(paired_ok.get('series') or {}).get('n', '—')} | {pct((paired_ok.get('series') or {}).get('microCoverage'))} | {pct((paired_ok.get('series') or {}).get('macroCoverage'))} |",
        "",
        "### 量级分组（all-valid）",
        "",
        "| 量级 | mosaic micro | series micro | mosaic macro | series macro | mosaic N | series N |",
        "|------|--------------|--------------|--------------|--------------|----------|----------|",
    ]
    for block in summary["bands"]:
        m = block["mosaic"]
        s = block["series"]
        lines.append(
            f"| {block['band']} | {pct(m['microCoverage'])} | {pct(s['microCoverage'])} | {pct(m['macroCoverage'])} | {pct(s['macroCoverage'])} | {m.get('coverageN', '—')} | {s.get('coverageN', '—')} |"
        )
    if summary["inputInvalidTrips"] or summary["metricInvalidTrips"]:
        lines += ["", "### 未进入管线胜负", ""]
        if summary["inputInvalidTrips"]:
            lines.append("- inputInvalid: " + ", ".join(f"`{t}`" for t in summary["inputInvalidTrips"]))
        if summary["metricInvalidTrips"]:
            lines.append("- metricInvalid: " + ", ".join(f"`{t}`" for t in summary["metricInvalidTrips"]))
    if skipped:
        lines += ["", "### 跳过（无 trip.json）", "", ", ".join(f"`{t}`" for t in skipped)]

    lines += [
        "",
        "## 分旅行配对",
        "",
        "Δ 仅两侧 `status=ok` 时填写；`outputInvalid` 等配对显示 —（与 paired-ok 同一谓词）。",
        "",
        "| trip | 量级 | mosaic cov | series cov | Δ | mosaic 状态 | series 状态 | mosaic planMs | series planMs | series overflowCapped | series placementGap | mosaic placementGap |",
        "|------|------|------------|------------|---|-------------|-------------|---------------|---------------|----------------------|---------------------|---------------------|",
    ]
    by_trip: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        by_trip.setdefault(str(row["tripId"]), {})[str(row["pipeline"])] = row
    for trip_id, _band, _n in TRIP_TABLE:
        arms = by_trip.get(trip_id)
        if not arms:
            continue
        m = arms.get("mosaic") or {}
        s = arms.get("series") or {}
        delta = folio.paired_coverage_delta(s, m)
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{trip_id}`",
                    BAND_BY_TRIP.get(trip_id, "—"),
                    pct(m.get("coverage")),
                    pct(s.get("coverage")),
                    pct(delta),
                    str(m.get("status") or "—"),
                    str(s.get("status") or "—"),
                    num(m.get("planMsMedian"), 1),
                    num(s.get("planMsMedian"), 1),
                    num(s.get("overflowCapped")),
                    num(s.get("placementGap")),
                    num(m.get("placementGap")),
                ]
            )
            + " |"
        )

    unknown: dict[str, int] = {}
    for row in rows:
        for pid in row.get("unknownTemplates") or []:
            unknown[str(pid)] = unknown.get(str(pid), 0) + 1
    if unknown:
        lines += [
            "",
            "### Registry 未知模板（mosaic 内容屏）",
            "",
            "按 EA-00，最终 `patternId` 必须能在同次 Registry 查到 `len(template.slots)`。"
            "下列 ID 仍被 mosaic 产出，但不在源码 `screen-*.yaml` / `page-*.yaml` 中，故记 `outputInvalid`。",
            "",
        ]
        for pid, n in sorted(unknown.items()):
            lines.append(f"- `{pid}` × {n}")

    lines += [
        "",
        "## 失败与完整性（分列，不可相加）",
        "",
        "| trip | pipeline | status | tripFail | integrityFail | chapterFail | emptyRenderedPages | omittedPlannedPages | pageDegraded | invalidReason |",
        "|------|----------|--------|----------|---------------|-------------|--------------------|---------------------|--------------|---------------|",
    ]
    for row in rows:
        if row.get("status") == "ok" and not row.get("chapterFail") and not row.get("emptyRenderedPages"):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['tripId']}`",
                    str(row["pipeline"]),
                    str(row["status"]),
                    str(row.get("tripFail")),
                    str(row.get("integrityFail")),
                    num(row.get("chapterFail")),
                    num(row.get("emptyRenderedPages")),
                    num(row.get("omittedPlannedPages")),
                    num(row.get("pageDegraded")),
                    str(row.get("invalidReason") or "—"),
                ]
            )
            + " |"
        )

    lines += [
        "",
        "## 复跑",
        "",
        "```text",
        "python scripts/ea02a_shadow_compare.py --write-markdown docs/acceptance-records/ea-02a-shadow-compare-2026-09-01.md",
        "python scripts/ea02a_shadow_compare.py --from-jsonl docs/acceptance-records/ea-02a-shadow-compare-2026-09-01.jsonl",
        "```",
        "",
        "`--from-jsonl` 只重算汇总与 Markdown，不重跑 compose；数据行按原文拷贝，`dataRowsHash` 校验行级未改。密度与页数列刻意不进总览排名。",
        "",
    ]
    return "\n".join(lines)


def select_trips(requested: list[str] | None, limit: int | None) -> list[str]:
    ids = [tid for tid, _band, _n in TRIP_TABLE]
    if requested:
        unknown = [t for t in requested if t not in BAND_BY_TRIP]
        if unknown:
            raise SystemExit(f"unknown trip id(s): {', '.join(unknown)}")
        ids = list(requested)
    if limit is not None:
        ids = ids[: max(0, limit)]
    return ids


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="EA-02a landscape series vs mosaic shadow compare")
    p.add_argument("--trips", nargs="*", help="Subset of trip ids from the EA-02a table")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--runs", type=int, default=3, help="Official timing runs (EA-00 default 3)")
    p.add_argument("--warmup", type=int, default=1, help="Warmup runs discarded from planMs")
    p.add_argument("--quick", action="store_true", help="warmup=0 runs=1 (unofficial timing)")
    p.add_argument("--trips-dir", type=Path, default=ROOT / "trips")
    p.add_argument(
        "--write-markdown",
        type=Path,
        default=ROOT / "docs" / "acceptance-records" / "ea-02a-shadow-compare-2026-09-01.md",
    )
    p.add_argument(
        "--write-jsonl",
        type=Path,
        default=ROOT / "docs" / "acceptance-records" / "ea-02a-shadow-compare-2026-09-01.jsonl",
    )
    p.add_argument(
        "--from-jsonl",
        type=Path,
        default=None,
        help="Re-aggregate an existing JSONL (no compose). Copies data rows unchanged; rewrites _summary + markdown.",
    )
    return p.parse_args(argv)


def hash_data_row_blobs(blobs: list[bytes]) -> str:
    digest = hashlib.sha256()
    for blob in blobs:
        digest.update(blob)
    return digest.hexdigest()


def serialize_data_row(row: dict[str, Any]) -> bytes:
    return (json.dumps(row, ensure_ascii=False) + "\n").encode("utf-8")


def split_jsonl_file(path: Path) -> tuple[list[bytes], list[dict[str, Any]], dict[str, Any]]:
    """Split JSONL into original data-row bytes and parsed summary. Data lines stay verbatim."""
    data_blobs: list[bytes] = []
    rows: list[dict[str, Any]] = []
    meta: dict[str, Any] = {}
    raw = path.read_bytes()
    if not raw:
        return data_blobs, rows, meta
    for line in raw.splitlines(keepends=True):
        payload = line.strip()
        if not payload:
            continue
        obj = json.loads(payload)
        if isinstance(obj, dict) and "_summary" in obj:
            inner = obj["_summary"]
            meta = inner if isinstance(inner, dict) else obj
            continue
        blob = line if line.endswith(b"\n") else line + b"\n"
        data_blobs.append(blob)
        rows.append(obj)
    return data_blobs, rows, meta


def write_jsonl(path: Path, data_blobs: list[bytes], summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        for blob in data_blobs:
            fh.write(blob if blob.endswith(b"\n") else blob + b"\n")
        fh.write((json.dumps({"_summary": summary}, ensure_ascii=False) + "\n").encode("utf-8"))


def load_rows_from_jsonl(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    _blobs, rows, meta = split_jsonl_file(path)
    return rows, meta


def rerender_from_jsonl(args: argparse.Namespace) -> int:
    src = Path(args.from_jsonl)
    data_blobs, rows, meta = split_jsonl_file(src)
    if not rows:
        raise SystemExit(f"no data rows in {src}")
    digest = hash_data_row_blobs(data_blobs)
    prev = meta.get("dataRowsHash")
    if prev and prev != digest:
        raise SystemExit(f"dataRowsHash mismatch in {src}: stored {prev} != {digest}")
    summary = folio.aggregate_shadow_rows(rows, tie_tolerance=TIE_TOLERANCE)
    comparison_run_id = str(meta.get("comparisonRunId") or rows[0].get("comparisonRunId") or "ea02a-rerender")
    warmup = int(meta.get("warmup") if meta.get("warmup") is not None else 1)
    runs = int(meta.get("runs") if meta.get("runs") is not None else 3)
    unofficial = bool(meta.get("unofficialTiming"))
    skipped = list(meta.get("skipped") or [])
    summary["comparisonRunId"] = comparison_run_id
    summary["warmup"] = warmup
    summary["runs"] = runs
    summary["unofficialTiming"] = unofficial
    summary["skipped"] = skipped
    summary["dataRowsHash"] = digest
    jsonl_path = Path(args.write_jsonl)
    write_jsonl(jsonl_path, data_blobs, summary)
    md = render_markdown(
        rows=rows,
        summary=summary,
        comparison_run_id=comparison_run_id,
        warmup=warmup,
        runs=runs,
        skipped=skipped,
        unofficial=unofficial,
    )
    md_path = Path(args.write_markdown)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md, encoding="utf-8")
    print(f"re-aggregated {len(rows)} rows from {src}")
    print(f"dataRowsHash {digest}")
    print(f"wrote {md_path}")
    print(f"wrote {jsonl_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.from_jsonl:
        return rerender_from_jsonl(args)
    warmup = 0 if args.quick else args.warmup
    runs = 1 if args.quick else args.runs
    unofficial = warmup < 1 or runs < 3
    trip_ids = select_trips(args.trips, args.limit)
    comparison_run_id = "ea02a-" + datetime.now().strftime("%Y%m%d-%H%M%S")

    from travelogue.config import get_config

    cfg = get_config()
    slot_count_for = RegistrySlotCount()
    code_rev = code_revision(ROOT)
    catalog_hash = series_catalog_hash()
    registry_hash = template_registry_hash()

    print(f"EA-02a {comparison_run_id} warmup={warmup} runs={runs} trips={len(trip_ids)}")
    print(f"caliber: {CALIBER_DOC}  tieTolerance={TIE_TOLERANCE}")
    rows: list[dict[str, Any]] = []
    skipped: list[str] = []

    def log(msg: str) -> None:
        print(msg, flush=True)

    def persist() -> None:
        invalidate_hash_pairs(rows)
        summary = folio.aggregate_shadow_rows(rows, tie_tolerance=TIE_TOLERANCE)
        summary["comparisonRunId"] = comparison_run_id
        summary["warmup"] = warmup
        summary["runs"] = runs
        summary["unofficialTiming"] = unofficial
        summary["skipped"] = skipped
        jsonl_path = Path(args.write_jsonl)
        data_blobs = [serialize_data_row(row) for row in rows]
        summary["dataRowsHash"] = hash_data_row_blobs(data_blobs)
        write_jsonl(jsonl_path, data_blobs, summary)
        md = render_markdown(
            rows=rows,
            summary=summary,
            comparison_run_id=comparison_run_id,
            warmup=warmup,
            runs=runs,
            skipped=skipped,
            unofficial=unofficial,
        )
        md_path = Path(args.write_markdown)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(md, encoding="utf-8")

    for trip_id in trip_ids:
        trip_dir = Path(args.trips_dir) / trip_id
        trip_json = trip_dir / "trip.json"
        if not trip_json.is_file():
            log(f"SKIP {trip_id}: missing trip.json")
            skipped.append(trip_id)
            continue
        log(f"== {trip_id} ({BAND_BY_TRIP.get(trip_id)}) ==")
        snapshot_ms = None
        try:
            trip_raw = load_trip(trip_dir)
            t_snap = time.perf_counter_ns()
            snapshot = build_snapshot(trip_raw, trip_dir=trip_dir, cfg=cfg)
            snapshot_ms = (time.perf_counter_ns() - t_snap) / 1e6
            log(f"  snapshot {snapshot_ms:.0f}ms eligible={len(snapshot.eligible_ids)}")
        except Exception as exc:  # noqa: BLE001
            log(f"  snapshot fail: {type(exc).__name__}: {exc}")
            dummy = {
                "comparisonRunId": comparison_run_id,
                "tripId": trip_id,
                "pipeline": "mosaic",
                "edition": "journal",
                "surface": SURFACE,
                "measurementStage": folio.MEASUREMENT_STAGE_COMPOSE,
                "status": "metricInvalid",
                "inputSnapshotHash": "",
                "eligibleSequenceHash": "",
                "armConfigHash": "",
                "codeRevision": code_rev,
                "seriesCatalogHash": catalog_hash,
                "templateRegistryHash": registry_hash,
                "caliberDoc": CALIBER_DOC,
                "band": BAND_BY_TRIP.get(trip_id),
                "invalidReason": f"{type(exc).__name__}:{exc}",
                "errorStage": "snapshot",
                "tripFail": False,
                "integrityFail": False,
                "planMsSamples": [],
                "planMsMedian": None,
                "snapshotMs": None,
                "jsonTripId": trip_id,
            }
            other = dict(dummy)
            other["pipeline"] = "series"
            other["edition"] = "portfolio"
            rows.extend([dummy, other])
            persist()
            continue

        (mosaic_samples, mosaic_attempt), (series_samples, series_attempt) = measure_pair(
            snapshot, warmup=warmup, runs=runs, log=log
        )
        mosaic_row = row_from_attempt(
            snapshot=snapshot,
            pipeline="mosaic",
            attempt=mosaic_attempt,
            samples=mosaic_samples,
            slot_count_for=slot_count_for,
            comparison_run_id=comparison_run_id,
            code_rev=code_rev,
            catalog_hash=catalog_hash,
            registry_hash=registry_hash,
            hash_mismatch=[],
        )
        series_row = row_from_attempt(
            snapshot=snapshot,
            pipeline="series",
            attempt=series_attempt,
            samples=series_samples,
            slot_count_for=slot_count_for,
            comparison_run_id=comparison_run_id,
            code_rev=code_rev,
            catalog_hash=catalog_hash,
            registry_hash=registry_hash,
            hash_mismatch=[],
        )
        pair = [mosaic_row, series_row]
        for row in pair:
            row["snapshotMs"] = None if snapshot_ms is None else round(snapshot_ms, 3)
            row["jsonTripId"] = str((snapshot.trip or {}).get("tripId") or "")
        invalidate_hash_pairs(pair)
        rows.extend(pair)
        persist()
        log(
            f"  mosaic {mosaic_row['status']} cov={mosaic_row.get('coverage')}  "
            f"series {series_row['status']} cov={series_row.get('coverage')}"
        )

    persist()
    log(f"wrote {args.write_markdown}")
    log(f"wrote {args.write_jsonl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
