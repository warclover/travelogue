"""P5-8.1 · P-EVAL layout blind-review helpers."""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.eval.peval import (
    append_peval_pair,
    beam_pick_changed_count,
    build_layout_peval_objective,
    load_peval_record,
)


def test_beam_pick_changed_count() -> None:
    curation = {
        "layoutDecisionLog": [
            {
                "events": [
                    {"type": "beam_pick", "changed": True},
                    {"type": "beam_pick", "changed": False},
                ]
            },
            {"events": [{"type": "beam_pick", "changed": True}]},
        ]
    }
    assert beam_pick_changed_count(curation) == 2
    assert beam_pick_changed_count({}) == 0


def test_build_layout_peval_objective() -> None:
    legacy = {"curation": {}}
    beam = {
        "curation": {
            "layoutDecisionLog": [{"events": [{"type": "beam_pick", "changed": True}]}],
            "degradationReason": None,
        }
    }
    obj = build_layout_peval_objective(
        legacy,
        beam,
        weights_preset="phase3b",
        identical=False,
        legacy_metrics={"screenCount": 10},
        beam_metrics={"screenCount": 11},
    )
    assert obj["protocol"] == "P5-PEVAL"
    assert obj["beamPickChanged"] == 1
    assert obj["legacyScreens"] == 10
    assert obj["beamScreens"] == 11


def test_append_peval_pair_dedupes_trip(tmp_path: Path) -> None:
    record_path = tmp_path / "phase5-peval.json"
    append_peval_pair({"tripId": "demo", "objective": {"identicalToLegacy": True}}, path=record_path)
    append_peval_pair({"tripId": "demo", "objective": {"identicalToLegacy": False}}, path=record_path)
    data = json.loads(record_path.read_text(encoding="utf-8"))
    assert len(data["pairs"]) == 1
    assert data["pairs"][0]["objective"]["identicalToLegacy"] is False


def test_load_peval_record_defaults() -> None:
    data = load_peval_record(Path("/nonexistent/peval.json"))
    assert data["recordId"] == "phase5-peval"
    assert data["protocol"] == "P-EVAL"
