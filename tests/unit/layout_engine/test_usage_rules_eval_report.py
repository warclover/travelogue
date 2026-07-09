"""URO P0-c · eval report + blind review script tests."""



from __future__ import annotations

from scripts.usage_rules_blind_review import init_template, score_review
from scripts.usage_rules_eval_common import ensure_trip_screen_ids, evaluate_trip_off_on, load_trip
from tests._repo_root import repo_root

ROOT = repo_root(__file__)


def test_evaluate_trip_off_on_fixture_smoke():
    trip = load_trip("golden-mixed-scenes", trips_dir=ROOT / "trips", use_fixture=True)
    assert trip is not None
    row = evaluate_trip_off_on(
        "golden-mixed-scenes",
        trip,
        work_dir=ROOT / ".cache" / "test-usage-rules-eval" / "golden-mixed-scenes",
    )
    assert row["tripId"] == "golden-mixed-scenes"
    assert row["layoutSnapshotEqual"] is True
    assert "off" in row and "on" in row


def test_blind_review_score_passes():
    doc = init_template()
    for pair in doc["tripPairs"]:
        pair["preference"] = "on"
    result = score_review(doc)
    assert result["scoredPairs"] == len(doc["tripPairs"])
    assert result["onPreferredRate"] == 1.0
    assert result["passesAcUroBlind"] is True


def test_blind_review_score_studio_veto():
    doc = init_template()
    for pair in doc["tripPairs"]:
        if pair.get("studioVeto"):
            pair["preference"] = "off"
        else:
            pair["preference"] = "on"
    result = score_review(doc)
    assert result["passesAcUroBlind"] is False
    assert "chuanzang-studio" in result["studioVetoLosses"]


def test_eval_report_script_import():
    import scripts.usage_rules_eval_report as mod

    assert callable(mod.main)


def test_run_variant_on_uses_config_override_for_rules(monkeypatch):
    """enabled=true must reach evaluate_reject via get_config() during curate."""
    from dataclasses import replace

    import travelogue.layout_engine.mosaic.candidates as mosaic_candidates
    from scripts.usage_rules_eval_common import run_variant
    from travelogue.config import get_config
    from travelogue.config.layout import UsageRulesConfig

    trip = load_trip("golden-mixed-scenes", trips_dir=ROOT / "trips", use_fixture=True)
    assert trip is not None
    base = get_config(reload=True)
    cfg_on = replace(
        base,
        layout=replace(
            base.layout,
            usage_rules=UsageRulesConfig(enabled=True, hero_gap_threshold=0.15),
        ),
    )
    calls = {"enabled": 0}
    orig = mosaic_candidates.evaluate_reject

    def counting(*args, **kwargs):
        cfg = kwargs.get("cfg")
        if cfg is None:
            from travelogue.layout_engine.usage_rules.evaluator import _usage_rules_config

            cfg = _usage_rules_config()
        if cfg.enabled:
            calls["enabled"] += 1
        return orig(*args, **kwargs)

    monkeypatch.setattr(mosaic_candidates, "evaluate_reject", counting)
    work = ROOT / ".cache" / "test-usage-rules-eval" / "override-smoke"
    on = run_variant(trip, usage_enabled=True, work_dir=work / "on", cfg_base=cfg_on)
    assert on["usageRulesEnabled"] is True
    assert calls["enabled"] > 0
    assert on["metrics"]["usageRules"]["enabled"] is True


def test_ensure_trip_screen_ids_fills_missing():
    trip = {
        "chapters": [
            {
                "id": "ch-02",
                "screens": [
                    {"screenId": "ch-02-sc-01", "patternId": "screen-portrait-1", "slots": []},
                    {"patternId": "screen-landscape-1", "slots": []},
                ],
            }
        ]
    }
    n = ensure_trip_screen_ids(trip)
    assert n == 1
    assert trip["chapters"][0]["screens"][1]["screenId"] == "ch-02-sc-02"


def test_blind_review_init_template_schema():
    doc = init_template()
    assert doc["gate"] == "AC-URO-BLIND"
    assert doc["blindThreshold"] == 0.55
    assert len(doc["tripPairs"]) >= 8
