"""EA-00 folio metrics: sample A/B/C plus identity checks."""

from __future__ import annotations

import importlib.util
import sys

from tests._repo_root import repo_root

ROOT = repo_root(__file__)


def _load_mod():
    path = ROOT / "scripts" / "ea00_folio_metrics.py"
    spec = importlib.util.spec_from_file_location("ea00_folio_metrics_test", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["ea00_folio_metrics_test"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_caliber_doc_is_the_frozen_ea00_page() -> None:
    mod = _load_mod()
    assert mod.CALIBER_DOC == "docs/成册指标口径定义.md"
    assert (ROOT / mod.CALIBER_DOC).is_file()
    text = (ROOT / mod.CALIBER_DOC).read_text(encoding="utf-8")
    for symbol in (
        "placedEligible",
        "intakeLoss",
        "overflowCapped",
        "placementGap",
        "emptyRenderedPages",
        "inputSnapshotHash",
    ):
        assert symbol in text


def test_sample_a_capacity_and_gap_split() -> None:
    mod = _load_mod()
    s = mod.SAMPLE_A
    loss, capped, gap, unplaced = mod.compute_unplaced_split(
        eligible=s["eligible"],
        intake_n=s["intakeN"],
        placed_eligible=s["placedEligible"],
        capacity_n=s["capacityN"],
    )
    assert (loss, capped, gap, unplaced) == (
        s["intakeLoss"],
        s["overflowCapped"],
        s["placementGap"],
        s["unplacedEligible"],
    )
    assert s["preComposeExcluded"] == s["folderN"] - s["eligible"]
    assert abs(s["placedEligible"] / s["eligible"] - s["coverage"]) < 1e-12
    assert s["eligible"] == s["placedEligible"] + unplaced
    assert s["eligible"] == s["placedEligible"] + loss + capped + gap


def test_sample_b_duplicate_placements_keep_coverage() -> None:
    mod = _load_mod()
    s = mod.SAMPLE_B
    # 38 unique eligible + two extra refs of a1,a2.
    unique = [f"e{i:02d}" for i in range(38)]
    slots = unique + ["e00", "e01"]
    trip = {
        "assets": [{"id": f"e{i:02d}", "type": "image"} for i in range(40)],
    }
    metrics = mod.compute_asset_metrics(
        trip=trip,
        eligible_ids=[f"e{i:02d}" for i in range(40)],
        intake_ids=[f"e{i:02d}" for i in range(40)],
        slot_asset_ids_=slots,
        capacity_n=None,
    )
    assert metrics.placement_occurrences == s["placementOccurrences"]
    assert metrics.placed_unique == s["placedUnique"]
    assert metrics.placed_eligible == s["placedEligible"]
    assert metrics.foreign_placed == s["foreignPlaced"]
    assert metrics.duplicate_placements == s["duplicatePlacements"]
    assert metrics.overflow_capped == s["overflowCapped"]
    assert metrics.placement_gap == s["placementGap"]
    assert abs(metrics.coverage - s["coverage"]) < 1e-12
    status, reason, trip_fail, integrity = mod.classify_status(
        input_reasons=[],
        asset=metrics,
        pages=mod.compute_page_metrics(
            screens=[{"patternId": "page-1-hero-land-right", "slots": [{"assetId": "e00"}]}],
            slot_count_for=lambda _pid: 1,
            planned_page_count=None,
        ),
        rendered_page_count=1,
        pipeline_error=None,
    )
    assert status == "outputInvalid"
    assert integrity is True
    assert trip_fail is False
    assert "duplicatePlacements" in (reason or "")


def test_sample_c_omitted_vs_partial_not_empty() -> None:
    mod = _load_mod()
    s = mod.SAMPLE_C
    screens = (
        [{"patternId": "full", "slots": [{"assetId": "a"}, {"assetId": "b"}]}] * 11
        + [{"patternId": "partial", "slots": [{"assetId": "x"}, {}]}] * 3
    )
    pages = mod.compute_page_metrics(
        screens=screens,
        slot_count_for=lambda pid: 2,
        planned_page_count=s["plannedPageCount"],
    )
    assert pages.rendered_page_count == s["renderedPageCount"]
    assert pages.omitted_planned_pages == s["omittedPlannedPages"]
    assert pages.empty_rendered_pages == s["emptyRenderedPages"]
    assert pages.partial_pages == s["partialPages"]
    assert pages.full_pages == s["fullPages"]
    assert (
        pages.empty_rendered_pages + pages.partial_pages + pages.full_pages
        == pages.rendered_page_count
    )


def test_every_ok_row_passes_identities() -> None:
    mod = _load_mod()
    trip = {"assets": [{"id": f"a{i}", "type": "image"} for i in range(10)]}
    asset = mod.compute_asset_metrics(
        trip=trip,
        eligible_ids=[f"a{i}" for i in range(8)],
        intake_ids=[f"a{i}" for i in range(8)],
        slot_asset_ids_=[f"a{i}" for i in range(6)],
        capacity_n=7,
    )
    pages = mod.compute_page_metrics(
        screens=[
            {"patternId": "p2", "slots": [{"assetId": "a0"}, {"assetId": "a1"}]},
            {"patternId": "p2", "slots": [{"assetId": "a2"}, {}]},
            {"patternId": "p2", "slots": [{"assetId": "a3"}, {"assetId": "a4"}]},
            {"patternId": "p2", "slots": [{"assetId": "a5"}, {}]},
        ],
        slot_count_for=lambda _pid: 2,
        planned_page_count=5,
    )
    status, reason, trip_fail, integrity = mod.classify_status(
        input_reasons=[],
        asset=asset,
        pages=pages,
        rendered_page_count=pages.rendered_page_count,
        pipeline_error=None,
    )
    row = mod.build_compose_row(
        comparison_run_id="t",
        trip_id="demo",
        pipeline="series",
        edition="portfolio",
        status=status,
        input_snapshot_hash="x",
        eligible_sequence_hash="y",
        arm_config_hash="z",
        code_revision="abc",
        series_catalog_hash="s",
        template_registry_hash="t",
        asset=asset,
        pages=pages,
        eligible_chapter_count=2,
        chapter_fail=0,
        trip_fail=trip_fail,
        integrity_fail=integrity,
        error_code=None,
        error_stage=None,
        invalid_reason=reason,
        plan_ms_samples=[10.0, 12.0, 11.0],
        series_id="magazine-16-standard",
        selection_resolution="capped",
        identity_fails=mod.identity_failures(
            {
                **{
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
            }
        ),
    )
    assert status == "ok"
    assert not row["identityFailures"]
    assert not mod.identity_failures(row)
    assert row["caliberDoc"] == mod.CALIBER_DOC
    assert row["surface"] == "landscape-16x9"
    assert row["pageRenderFail"] is None


def test_breath_screens_are_not_content_pages() -> None:
    mod = _load_mod()
    chapters = [
        {
            "screens": [
                {"patternId": "screen-breath-pause", "slots": []},
                {"patternId": "screen-decor-rule", "slots": []},
                {"patternId": "page-1-hero-land-right", "slots": [{"assetId": "a"}]},
            ]
        }
    ]
    screens = mod.iter_content_screens(chapters)
    assert [s["patternId"] for s in screens] == ["page-1-hero-land-right"]


def test_pipeline_fail_nulls_coverage_not_zero() -> None:
    mod = _load_mod()
    row = mod.build_compose_row(
        comparison_run_id="t",
        trip_id="demo",
        pipeline="mosaic",
        edition="journal",
        status="pipelineFail",
        input_snapshot_hash="x",
        eligible_sequence_hash="y",
        arm_config_hash="z",
        code_revision="abc",
        series_catalog_hash="s",
        template_registry_hash="t",
        asset=None,
        pages=None,
        eligible_chapter_count=None,
        chapter_fail=None,
        trip_fail=True,
        integrity_fail=False,
        error_code="PortfolioUnavailableError",
        error_stage="plan",
        invalid_reason=None,
        plan_ms_samples=[8.0],
        series_id=None,
        selection_resolution=None,
    )
    assert row["coverage"] is None
    assert row["renderedPageCount"] is None
    assert row["tripFail"] is True
    assert row["planMsMedian"] == 8.0


def test_aggregate_does_not_rank_density() -> None:
    mod = _load_mod()
    rows = [
        {
            "tripId": "t1",
            "pipeline": "mosaic",
            "status": "ok",
            "coverage": 0.9,
            "placedEligible": 9,
            "eligible": 10,
            "band": "sparse-60-140",
            "planMsMedian": 20,
            "density": 3.0,
        },
        {
            "tripId": "t1",
            "pipeline": "series",
            "status": "ok",
            "coverage": 0.7,
            "placedEligible": 7,
            "eligible": 10,
            "band": "sparse-60-140",
            "planMsMedian": 5,
            "density": 1.0,
        },
    ]
    summary = mod.aggregate_shadow_rows(rows, tie_tolerance=0.02)
    assert "density" not in summary["winTieLoss"]
    assert summary["winTieLoss"]["mosaic"] == 1
    assert summary["scoringNote"].startswith("density")
    assert abs(summary["series"]["microCoverage"] - 0.7) < 1e-12
    assert abs(summary["mosaic"]["macroCoverage"] - 0.9) < 1e-12
    assert abs(summary["coverageSets"]["allValid"]["series"]["microCoverage"] - 0.7) < 1e-12
    assert summary["coverageSets"]["pairedOk"]["nPairs"] == 1


def test_aggregate_splits_all_valid_and_paired_ok() -> None:
    """Headline coverage uses the same valid-input queue; Δ uses both-ok pairs only."""
    mod = _load_mod()
    rows = [
        {
            "tripId": "clean",
            "pipeline": "mosaic",
            "status": "ok",
            "coverage": 0.9,
            "placedEligible": 9,
            "eligible": 10,
            "band": "sparse-60-140",
            "planMsMedian": 1,
        },
        {
            "tripId": "clean",
            "pipeline": "series",
            "status": "ok",
            "coverage": 0.8,
            "placedEligible": 8,
            "eligible": 10,
            "overflowCapped": 0,
            "placementGap": 2,
            "intakeLoss": 0,
            "band": "sparse-60-140",
            "planMsMedian": 2,
        },
        {
            "tripId": "dirty",
            "pipeline": "mosaic",
            "status": "outputInvalid",
            "coverage": 0.99,
            "placedEligible": 99,
            "eligible": 100,
            "band": "overflow-424-1000",
            "planMsMedian": 1,
            "duplicatePlacements": 1,
        },
        {
            "tripId": "dirty",
            "pipeline": "series",
            "status": "ok",
            "coverage": 0.2,
            "placedEligible": 20,
            "eligible": 100,
            "overflowCapped": 70,
            "placementGap": 10,
            "intakeLoss": 0,
            "band": "overflow-424-1000",
            "planMsMedian": 2,
        },
    ]
    summary = mod.aggregate_shadow_rows(rows, tie_tolerance=0.02)
    all_v = summary["coverageSets"]["allValid"]
    pair = summary["coverageSets"]["pairedOk"]
    assert all_v["mosaic"]["n"] == 2
    assert all_v["series"]["n"] == 2
    assert abs(all_v["mosaic"]["microCoverage"] - 108 / 110) < 1e-12
    assert abs(all_v["series"]["microCoverage"] - 28 / 110) < 1e-12
    assert pair["nPairs"] == 1
    assert pair["tripIds"] == ["clean"]
    assert abs(pair["mosaic"]["microCoverage"] - 0.9) < 1e-12
    assert abs(pair["series"]["microCoverage"] - 0.8) < 1e-12
    assert summary["winTieLoss"]["mosaic"] == 1
    cons = summary["seriesConservation"]
    assert cons["eligible"] == 110
    assert cons["placedEligible"] == 28
    assert cons["overflowCapped"] == 70
    assert cons["placementGap"] == 12
    assert cons["unplacedEligible"] == 82
    assert summary["mosaic"]["pipelineFailureRate"] == 0.5
    assert summary["series"]["pipelineFailureRate"] == 0.0
    # Headline numbers are all-valid, not the mixed-queue ok-only set.
    assert abs(summary["mosaic"]["microCoverage"] - all_v["mosaic"]["microCoverage"]) < 1e-12
    assert abs(summary["series"]["microCoverage"] - all_v["series"]["microCoverage"]) < 1e-12


def test_paired_coverage_delta_none_unless_both_ok() -> None:
    mod = _load_mod()
    ok = {"status": "ok", "coverage": 0.8}
    other_ok = {"status": "ok", "coverage": 0.5}
    invalid = {"status": "outputInvalid", "coverage": 0.99}
    assert abs(mod.paired_coverage_delta(ok, other_ok) - 0.3) < 1e-12
    assert mod.paired_coverage_delta(ok, invalid) is None
    assert mod.paired_coverage_delta(invalid, other_ok) is None
    assert mod.paired_coverage_delta({"coverage": 0.9}, {"coverage": 0.1}) is None
