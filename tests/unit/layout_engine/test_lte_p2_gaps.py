"""Phase 16 P2 gaps: governance, MMR diversity, geometry, quotas."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_engine.mosaic.diversity import (
    pattern_similarity,
    rerank_scored_candidates_mmr,
)
from travelogue.layout_engine.mosaic.lte_adapter import mcs_diversity_config, template_base_weight
from travelogue.layout_templates.css_gen import generate_grid_css
from travelogue.layout_templates.geometry import slot_aspect_table, solve_tracks
from travelogue.layout_templates.models import TemplateStage
from travelogue.layout_templates.registry import (
    LayoutTemplateEngine,
    check_active_quotas,
    reset_engine_cache_for_tests,
)
from travelogue.templating.admin_store import _LOCK, _load_unlocked, _save_unlocked
from travelogue.templating.config_governance import (
    approve_router_change,
    patch_from_exposure_debt_proposals,
    propose_layout_weight_changes,
)


@pytest.fixture(autouse=True)
def _fresh_lte() -> None:
    reset_engine_cache_for_tests()


@pytest.fixture
def engine() -> LayoutTemplateEngine:
    return LayoutTemplateEngine.load(rebuild_cache=True)


@pytest.mark.unit
def test_patch_from_exposure_debt_proposals() -> None:
    patch = patch_from_exposure_debt_proposals(
        [
            {
                "templateId": "screen-mosaic-5-2p3l-equal",
                "suggestedBaseWeight": 1.12,
            }
        ],
        template_registry_version="abc123",
    )
    assert patch["layout_template_base_weights"]["screen-mosaic-5-2p3l-equal"] == pytest.approx(1.12)
    assert patch["templateRegistryVersion"] == "abc123"


@pytest.mark.unit
def test_runtime_base_weight_override_applied(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from travelogue.templating import admin_store

    state_path = tmp_path / "template_admin_state.json"
    monkeypatch.setattr(admin_store, "_STATE_PATH", state_path)
    monkeypatch.setattr("travelogue.domain.template_admin_state._ADMIN_STATE_PATH", state_path)
    monkeypatch.setattr("travelogue.domain.template_admin_state._RUNTIME_CACHE", None)
    with _LOCK:
        data = _load_unlocked()
        data["runtime"] = {
            "layout_template_base_weights": {"screen-mosaic-5-hero-3-2-plus-4": 1.5}
        }
        _save_unlocked(data)
    assert template_base_weight("screen-mosaic-5-hero-3-2-plus-4") == pytest.approx(1.5)


@pytest.mark.unit
def test_exposure_debt_semi_closed_loop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """eval → propose → dual approve → runtime template_base_weight (§9.4)."""
    from scripts.phase16_template_eval import (
        compute_exposure_debt_proposals,
        submit_exposure_proposals,
    )
    from travelogue.templating import admin_store

    state_path = tmp_path / "template_admin_state.json"
    monkeypatch.setattr(admin_store, "_STATE_PATH", state_path)
    monkeypatch.setattr("travelogue.domain.template_admin_state._ADMIN_STATE_PATH", state_path)
    monkeypatch.setattr("travelogue.domain.template_admin_state._RUNTIME_CACHE", None)

    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    active_ids = {t.id for t in engine.list_active()}
    exposure_share = {tid: (0.9 if tid == "screen-portrait-3" else 0.01) for tid in active_ids}
    proposals = compute_exposure_debt_proposals(exposure_share, engine)
    assert proposals

    report = {
        "exposureDebtProposals": proposals,
        "templateRegistryVersion": engine._content_hash,
    }
    pending = submit_exposure_proposals(report, operator="eval-op")
    assert pending["status"] == "pending"

    boosted = next(p for p in proposals if p["suggestedBaseWeight"] > p["currentBaseWeight"])
    approve_router_change(pending["id"], approver="approver-a")
    approve_router_change(pending["id"], approver="approver-b")

    assert template_base_weight(boosted["templateId"]) == pytest.approx(boosted["suggestedBaseWeight"])


@pytest.mark.unit
def test_propose_and_approve_layout_weights(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from travelogue.templating import admin_store

    state_path = tmp_path / "template_admin_state.json"
    monkeypatch.setattr(admin_store, "_STATE_PATH", state_path)
    monkeypatch.setattr("travelogue.domain.template_admin_state._ADMIN_STATE_PATH", state_path)
    monkeypatch.setattr("travelogue.domain.template_admin_state._RUNTIME_CACHE", None)
    req = propose_layout_weight_changes(
        [{"templateId": "screen-mosaic-5-2p3l-equal", "suggestedBaseWeight": 1.08}],
        operator="op-1",
        reason="test",
    )
    assert req["status"] == "pending"
    approve_router_change(req["id"], approver="op-2")
    approve_router_change(req["id"], approver="op-3")
    runtime = json.loads(state_path.read_text(encoding="utf-8"))["runtime"]
    assert runtime["layout_template_base_weights"]["screen-mosaic-5-2p3l-equal"] == pytest.approx(1.08)


@pytest.mark.unit
def test_mcs_diversity_config_reads_policy() -> None:
    cfg = mcs_diversity_config()
    assert cfg["mode"] in ("off", "mmr", "dpp")
    assert 0.0 < float(cfg["lambda"]) <= 1.0


@pytest.mark.unit
def test_pattern_similarity_distinguishes_templates(engine: LayoutTemplateEngine) -> None:
    a = "screen-mosaic-5-hero-3-2-plus-4"
    b = "screen-portrait-3"
    assert pattern_similarity(a, a) == 1.0
    assert pattern_similarity(a, b) < 0.5


@pytest.mark.unit
def test_mmr_prefers_diverse_pattern_when_scores_close() -> None:
    from travelogue.layout_engine.mosaic.candidates import ScreenCandidate

    state = ScreenLayoutPlannerState(nine_min=0, nine_max=9)
    state.pattern_counts = {"screen-portrait-3": 2}

    def _cand(pid: str, score: float) -> tuple[ScreenCandidate, float, list[str]]:
        return (
            ScreenCandidate(
                pattern_id=pid,
                ordered_asset_ids=["a", "b", "c", "d", "e"],
                screen={"patternId": pid, "slots": []},
                hard_valid=True,
            ),
            score,
            [],
        )

    scored = [
        _cand("screen-portrait-3", 0.92),
        _cand("screen-mosaic-5-2p3l-equal", 0.905),
    ]
    reranked = rerank_scored_candidates_mmr(scored, layout_state=state, mmr_lambda=0.35)
    assert reranked[0][0].pattern_id == "screen-mosaic-5-2p3l-equal"


@pytest.mark.unit
def test_solve_tracks_recovers_hero_weights(engine: LayoutTemplateEngine) -> None:
    tpl = engine.get("screen-mosaic-5-hero-3-2-plus-4")
    aspects = slot_aspect_table(tpl)
    targets = [(row.display_aspect, 1.0) for row in aspects]
    rects = [s.rect for s in tpl.slots]
    cols, rows = solve_tracks(targets, stage_aspect=tpl.stage.aspect, rects=rects)
    assert len(cols) == 3
    assert len(rows) == 2
    assert max(cols) / min(cols) >= 1.5


@pytest.mark.unit
def test_generate_grid_css_includes_gap() -> None:
    from travelogue.layout_templates.models import TemplateDef, TemplateSlot

    tpl = TemplateDef(
        id="test-gap",
        version=1,
        status="experimental",
        kind="composite",
        display_name="gap test",
        description="",
        aesthetic=None,
        balance_policy=None,
        stage=TemplateStage(aspect="16:9", cols=(1, 1), rows=(1, 1), gap="12px"),
        photo_count_min=2,
        photo_count_max=2,
        mix_portrait=None,
        mix_landscape=None,
        slots=(
            TemplateSlot(index=0, rect=(1, 1, 1, 1), role="main"),
            TemplateSlot(index=1, rect=(2, 2, 1, 1), role="landscape"),
        ),
        constraints={},
        compatibility_hints={},
        scoring={},
        render_grid_class="layout-screen__grid--test-gap",
        render_css_bundle="journal-screens.css",
        render_fit_policy=None,
        rollout={},
        raw={},
    )
    css = generate_grid_css(tpl)
    assert "gap: 12px" in css


@pytest.mark.unit
def test_check_active_quotas_warn_only(engine: LayoutTemplateEngine) -> None:
    warnings = check_active_quotas(engine)
    assert isinstance(warnings, list)
