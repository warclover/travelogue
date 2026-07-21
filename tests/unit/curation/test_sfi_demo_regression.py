"""QA-SFI-04 · 仙本那 / 武大瘦 fixture 回归（FX-SFI-01/03/06）。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.config import get_config
from travelogue.curation.curate import run_curate
from travelogue.curation.time_outlier import (
    detect_time_outlier_ids,
    substantial_segment_count,
)
from travelogue.render.moment_exif import format_moment_exif_line

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "sfi"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_substantial_segment_ignores_stray_singleton() -> None:
    # 24 + 1 stray → only one substantial segment
    assert substantial_segment_count([24, 1], dated_total=25) == 1
    # two real trips
    assert substantial_segment_count([40, 35], dated_total=75) >= 2


def test_semporna_stray_isolated_without_year_span_title() -> None:
    trip = _load("trip.sfi_semporna_outlier.json")
    run_curate(trip, cfg=get_config())
    outliers = (trip.get("curation") or {}).get("excludedTimeOutlierAssetIds") or []
    assert "asset-250" in outliers
    titles = [str(ch.get("title") or "") for ch in trip.get("chapters") or []]
    joined = "|".join(titles)
    assert "2018–2020" not in joined
    assert "2018-2020" not in joined
    assert "11月30日" not in joined  # stray date must not headline a content chapter
    assert not any((ch.get("curation") or {}).get("isAppendix") for ch in trip["chapters"])


def test_semporna_two_outliers_build_appendix() -> None:
    trip = _load("trip.sfi_semporna_appendix.json")
    run_curate(trip, cfg=get_config())
    chapters = trip.get("chapters") or []
    appendix = [ch for ch in chapters if (ch.get("curation") or {}).get("isAppendix")]
    assert len(appendix) == 1
    assert appendix[0]["title"].startswith("往年 · 旧照 ·")
    assert "2 张" in appendix[0]["title"]
    content = [ch for ch in chapters if not (ch.get("curation") or {}).get("isAppendix")]
    assert 1 <= len(content) <= 5
    joined = "|".join(str(ch.get("title") or "") for ch in content)
    assert "2018–2020" not in joined


def test_wuhan_low_confidence_suppresses_absolute_year() -> None:
    trip = _load("trip.sfi_wuhan_lowconf.json")
    assets = trip.get("assets") or []
    assert assets
    assert all(a.get("dateConfidence") == "low" for a in assets)
    sample = dict(assets[0])
    sample["place"] = {"city": "武汉"}
    line = format_moment_exif_line(sample)
    assert line is not None
    assert "2015" not in line
    assert "武汉" in line


def test_yearbook_two_substantial_segments_still_exempt() -> None:
    assets = []
    for i in range(10):
        assets.append(
            {
                "id": f"s{i}",
                "takenAt": f"2019-03-{(i % 5) + 1:02d}T12:00:00Z",
                "layoutEligible": True,
            }
        )
    for i in range(10):
        assets.append(
            {
                "id": f"t{i}",
                "takenAt": f"2021-08-{(i % 5) + 1:02d}T12:00:00Z",
                "layoutEligible": True,
            }
        )
    assert detect_time_outlier_ids(assets, segment_sizes=[10, 10]) == []
