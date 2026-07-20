"""LTN dogfood AC · B-02 / D-02 / D-03 on fixed fixture."""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.layout_contract.ltn_dogfood import evaluate_dogfood_trip

FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "ltn"
    / "trip.ltn_dogfood_hero_chapter.json"
)


def test_dogfood_fixture_machine_gate():
    trip = json.loads(FIXTURE.read_text(encoding="utf-8"))
    report = evaluate_dogfood_trip(trip)
    assert report["machineOk"] is True
    assert report["AC-B-02"]["ok"] is True
    assert report["AC-B-02"]["heroMosaicCount"] == 1
    assert report["AC-D-03"]["ok"] is True
    assert report["AC-D-03"]["ratio"] >= 0.60
    assert report["AC-D-02"]["ok"] is True
    assert report["AC-D-01"]["humanRequired"] is True
    assert report["AC-D-01"]["proxyScore"] >= 7.0


def test_b02_fails_when_hero_flattened():
    trip = json.loads(FIXTURE.read_text(encoding="utf-8"))
    sc = trip["chapters"][0]["screens"][3]
    sc["preserveGroup"] = False
    report = evaluate_dogfood_trip(trip)
    assert report["AC-B-02"]["ok"] is False
    assert report["machineOk"] is False
