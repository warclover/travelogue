"""VR-N* narrative validation and ingest journey hints."""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.media.ingest_preview import preview_multi_journey
from travelogue.media.ingest_report import format_ingest_report
from travelogue.services.narrative_validate import validate_narrative
from travelogue.services.validate import validate_trip

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "schemas" / "fixtures"


def _base_trip() -> dict:
    return json.loads((FIXTURES / "trip.copy_locked.json").read_text(encoding="utf-8"))


def test_vr_n01_banned_phrase():
    trip = _base_trip()
    trip["meta"]["hook"] = "值得一提的是，这次旅途很美。"
    errs = [e for e in validate_narrative(trip) if "VR-N01" in e]
    assert errs
    assert any("值得一提的是" in e for e in errs)


def test_vr_n02_overseas_place_without_asset():
    trip = _base_trip()
    trip.setdefault("meta", {})["places"] = ["巴黎", "上海"]
    for a in trip.get("assets") or []:
        a.pop("place", None)
    warns = [e for e in validate_narrative(trip) if "VR-N02" in e]
    assert warns
    assert any("巴黎" in e for e in warns)


def test_vr_n04_lead_repeats_title():
    trip = _base_trip()
    ch = trip["chapters"][0]
    ch["title"] = "5月–6月·林芝·2"
    ch["lead"] = "5月–6月·林芝·2，林芝。"
    errs = [e for e in validate_narrative(trip) if "VR-N04" in e]
    assert errs


def test_vr_n03_caption_transcript_overlap():
    trip = _base_trip()
    ch = trip["chapters"][1]
    card = next(it for it in ch["items"] if it.get("type") == "media-card")
    aid = card["assetId"]
    transcript = "今天天气很好，我们在湖边走了很久，阳光洒在湖面上。"
    card["caption"] = transcript
    for a in trip["assets"]:
        if a["id"] == aid:
            a["voice"] = {"transcript": transcript}
            break
    warns = [e for e in validate_narrative(trip) if "VR-N03" in e]
    assert warns


def test_validate_trip_includes_narrative_rules():
    trip = _base_trip()
    trip["meta"]["hook"] = "综上所述，旅途结束。"
    all_errs = validate_trip(trip, level="manifest")
    assert any("VR-N01" in e for e in all_errs)


def test_preview_multi_journey_two_segments():
    assets = []
    days = (
        "2024-01-01",
        "2024-01-03",
        "2024-01-05",
        "2024-02-20",
        "2024-02-22",
        "2024-02-24",
    )
    for day in days:
        assets.append(
            {
                "id": f"a-{day}",
                "type": "image",
                "width": 1200,
                "height": 800,
                "takenAt": f"{day}T12:00:00Z",
            }
        )
    hint = preview_multi_journey(assets, place="京都")
    assert hint is not None
    assert "合成一本" in hint


def test_ingest_report_shows_journey_hint():
    class FakeResult:
        stats = {
            "scanned": 10,
            "used": 10,
            "journey_hints": [
                "检测到可能包含 2 次旅行（1月·京都、2月·京都）；默认将合成一本游记（3–5 章），可在 G1 合并段或拆成多本"
            ],
        }

    text = format_ingest_report(FakeResult())
    assert "提示:" in text
    assert "合成一本" in text
