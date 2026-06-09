#!/usr/bin/env python3
"""Lite copy v1.1 offline metrics → JSON record."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from travelogue.config import AppConfig, NarrativeConfig
from travelogue.services.copy_metrics import record_copy_metrics
from travelogue.services.decor_line import apply_decor_lines

MIN_CHAPTER_SAMPLES = 20
AC_COPY_01_MEDIAN_MAX = 120


def _fixture_trips() -> list[dict]:
    voice_trip = {
        "tripId": "copy-opt-voice",
        "meta": {"title": "语音", "tone": "relaxed"},
        "assets": [
            {
                "id": "a1",
                "type": "image",
                "tags": ["雨"],
                "voice": {"transcriptPreview": "雨太大了，先回酒店拿伞"},
            }
        ],
        "chapters": [
            {
                "id": "ch-01",
                "index": 1,
                "patternId": "open",
                "title": "雨后",
                "items": [{"type": "media-card", "assetId": "a1"}],
                "curation": {"memoryAnchors": ["鸭川"]},
            }
        ],
    }
    sparse = {
        "tripId": "copy-opt-sparse",
        "meta": {"title": "空"},
        "assets": [{"id": "a1", "type": "image", "tags": ["街景"]}],
        "chapters": [
            {
                "id": "ch-01",
                "index": 1,
                "patternId": "open",
                "title": "一章",
                "items": [{"type": "media-card", "assetId": "a1"}],
            }
        ],
    }
    return [voice_trip, sparse]


def _bulk_sample_trip(*, chapter_count: int = 24) -> dict:
    anchors = ["鸭川", "寺庙", "拉面", "雨", "京都", "河原町"]
    assets: list[dict] = []
    chapters: list[dict] = []
    for i in range(chapter_count):
        aid = f"a{i:02d}"
        anchor = anchors[i % len(anchors)]
        tag = anchors[(i + 2) % len(anchors)]
        asset: dict = {
            "id": aid,
            "type": "image",
            "tags": [tag],
            "place": {"city": "京都"},
        }
        if i % 3 == 0:
            asset["voice"] = {"transcriptPreview": f"走到{anchor}，风很轻"}
        assets.append(asset)
        curation: dict = {"memoryAnchors": [anchor], "places": ["京都"]}
        chapters.append(
            {
                "id": f"ch-{i + 1:02d}",
                "index": i + 1,
                "patternId": "open",
                "title": f"第{i + 1}章",
                "items": [{"type": "media-card", "assetId": aid}],
                "curation": curation,
            }
        )
    return {
        "tripId": "copy-opt-bulk",
        "meta": {"title": "批量验收", "tone": "relaxed", "hook": "京都几日。"},
        "epilogue": "先这样。",
        "assets": assets,
        "chapters": chapters,
    }


def _book_lite_copy_char_total(trip: dict) -> int:
    hook = str((trip.get("meta") or {}).get("hook") or "").strip()
    epilogue = str(trip.get("epilogue") or "").strip()
    decor = [
        str(ch.get("decorLine") or "").strip()
        for ch in trip.get("chapters") or []
        if str(ch.get("decorLine") or "").strip()
    ]
    return sum(len(part) for part in [hook, epilogue, *decor])


def main() -> int:
    parser = argparse.ArgumentParser(description="Lite copy v1.1 acceptance metrics")
    parser.add_argument(
        "--write",
        type=Path,
        default=REPO / "docs" / "acceptance-records" / "copy-opt-metrics.json",
    )
    parser.add_argument(
        "--write-blind",
        type=Path,
        default=REPO / "docs" / "acceptance-records" / "copy-opt-blind-review.json",
    )
    args = parser.parse_args()
    cfg = AppConfig(
        narrative=NarrativeConfig(
            decor_line_enabled=True,
            decor_line_voice_first=True,
            decor_line_llm_enabled=False,
        )
    )
    trips = _fixture_trips() + [_bulk_sample_trip(chapter_count=24)]
    total = 0
    filled = 0
    empty = 0
    generic_hits = 0
    sample_rows: list[dict] = []
    book_char_totals: list[int] = []
    last_metrics: dict = {}
    for trip in trips:
        apply_decor_lines(trip, cfg=cfg)
        last_metrics = record_copy_metrics(trip)
        generic_hits += int(last_metrics.get("generic_phrase_hits") or 0)
        book_char_totals.append(_book_lite_copy_char_total(trip))
        for ch in trip.get("chapters") or []:
            total += 1
            line = (ch.get("decorLine") or "").strip()
            if line:
                filled += 1
                sample_rows.append(
                    {
                        "chapterId": ch.get("id"),
                        "decorLine": line,
                        "verdict": None,
                        "tags": [],
                    }
                )
            else:
                empty += 1
    median_chars = int(statistics.median(book_char_totals)) if book_char_totals else 0
    ac_copy_01_pass = median_chars <= AC_COPY_01_MEDIAN_MAX and total >= MIN_CHAPTER_SAMPLES
    record = {
        "generatedAt": datetime.now(UTC).isoformat(),
        "phase": "lite-copy-v1.1",
        "metrics": {
            "decor_line_fill_rate": round(filled / total, 3) if total else 0.0,
            "decor_line_empty_rate": round(empty / total, 3) if total else 0.0,
            "generic_phrase_hits": generic_hits,
            "chapters_sampled": total,
            "chapters_with_decor_line": filled,
            "copy_total_chars_median": median_chars,
            "intent_adoption_rate": last_metrics.get("intent_adoption_rate", 0.0),
        },
        "acceptance": {
            "AC-COPY-01": {
                "pass": ac_copy_01_pass,
                "median_chars": median_chars,
                "max_median": AC_COPY_01_MEDIAN_MAX,
            },
            "AC-COPY-11": {
                "pass": total >= MIN_CHAPTER_SAMPLES,
                "chapters_sampled": total,
                "min_samples": MIN_CHAPTER_SAMPLES,
            },
        },
        "notes": "Synthetic fixtures; complete blind review in copy-opt-blind-review.json",
    }
    blind_samples = sample_rows[:30]
    blind = {
        "phase": "lite-copy-v1.1",
        "reviewDate": None,
        "reviewer": None,
        "sampleSize": 30,
        "criteria": [
            "不抢镜、不画蛇添足",
            "像我的旅行 / 走心",
            "点到即止",
        ],
        "samples": blind_samples,
        "summary": {
            "passRate": None,
            "notes": f"Auto-seeded {len(blind_samples)} chapters; fill verdict manually for AC-COPY-17",
        },
    }
    args.write.parent.mkdir(parents=True, exist_ok=True)
    args.write.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.write_blind.parent.mkdir(parents=True, exist_ok=True)
    args.write_blind.write_text(json.dumps(blind, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0 if ac_copy_01_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
