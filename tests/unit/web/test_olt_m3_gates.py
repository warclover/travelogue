"""OLT · QA-OLT-06 数据面 + QA-OLT-07 书架耗时（不拧发布默认）。

夹具只克隆 ``trip.render_golden.json``（BLK-OLT-07）。
"""

from __future__ import annotations

import copy
import json
import time
from dataclasses import replace
from pathlib import Path

import pytest

from travelogue.config import AppConfig
from travelogue.config.runtime import app_config_scope
from travelogue.export.longshot import EXPORT_OUTPUT_DIRNAME
from travelogue.export.output_ledger import (
    read_ledger,
    record_successful_output,
)
from travelogue.render.context import longshot_bundle_version
from travelogue.render.golden_regression import load_golden_trip
from travelogue.web.studio_handlers.trip_handlers import handle_get_outputs, handle_trips
from travelogue.web.studio_trips import list_studio_trips

from tests.studio_test_helpers import MockStudioHandler

pytestmark = [pytest.mark.unit, pytest.mark.pipeline_isolation]


def test_qa_olt_05_seam_budget_unchanged() -> None:
    """AC-OLT-21 · 窄缝仍 12/14；账本/指纹不进窄缝表。"""
    text = Path("docs/dual-pipeline-ownership.md").read_text(encoding="utf-8")
    assert "上限 14 · 现 12" in text
    from scripts.lint_dual_pipeline_ownership import SEAM_FILES

    assert "travelogue/export/output_ledger.py" not in SEAM_FILES
    assert "travelogue/domain/output_fingerprint.py" not in SEAM_FILES

_LEDGER_ON = replace(AppConfig(), studio=replace(AppConfig().studio, output_ledger=True))
_LEDGER_OFF = replace(AppConfig(), studio=replace(AppConfig().studio, output_ledger=False))


def _clone_trip(parent: Path, trip_id: str, golden: dict) -> tuple[Path, dict]:
    trip = copy.deepcopy(golden)
    trip_dir = parent / trip_id
    export_dir = trip_dir / EXPORT_OUTPUT_DIRNAME
    export_dir.mkdir(parents=True)
    (trip_dir / "trip.json").write_text(
        json.dumps(trip, ensure_ascii=False), encoding="utf-8"
    )
    return trip_dir, trip


def _png(export_dir: Path, name: str) -> None:
    (export_dir / name).write_bytes(b"png")


def _export(
    trip_dir: Path,
    trip: dict,
    *,
    profile: str,
    files: list[str],
    segmented: bool = False,
) -> None:
    bundle = longshot_bundle_version(trip)
    written = record_successful_output(
        trip_dir,
        trip=trip,
        profile=profile,
        files=files,
        spec={"format": "png"},
        bundle_fp=bundle,
        segmented=segmented,
    )
    assert written is not None


def test_qa_olt_06_three_chips_reexport_wechat_heal(tmp_path: Path) -> None:
    """导三种 → 三券 → 重导仍三 → 微信两态四条 → 手删文件剩三。"""
    trip_dir, trip = _clone_trip(tmp_path, "render-golden-demo", load_golden_trip())
    export_dir = trip_dir / EXPORT_OUTPUT_DIRNAME
    _png(export_dir, "雨后京都-xhs-01.png")
    _png(export_dir, "雨后京都-moments-01.png")
    _png(export_dir, "雨后京都-长图.png")
    _export(trip_dir, trip, profile="xiaohongshu", files=["雨后京都-xhs-01.png"])
    _export(trip_dir, trip, profile="wechat_moments", files=["雨后京都-moments-01.png"])
    _export(trip_dir, trip, profile="wechat_chat", files=["雨后京都-长图.png"], segmented=False)

    with app_config_scope(_LEDGER_ON):
        row = list_studio_trips(tmp_path)[0]
        handler = MockStudioHandler(tmp_path)
        handle_get_outputs(handler, trip_dir.name)
    assert row["outputSummary"]["total"] == 3
    assert len(row["outputSummary"]["chips"]) == 3
    labels = {c["label"] for c in row["outputSummary"]["chips"]}
    assert labels == {"小红书", "朋友圈", "微信群"}
    assert all("fileCount" not in c for c in row["outputSummary"]["chips"])
    assert handler.response is not None
    assert handler.response[0] == 200
    assert len(handler.response[1]["outputs"]) == 3

    _png(export_dir, "雨后京都-xhs-02.png")
    _export(trip_dir, trip, profile="xiaohongshu", files=["雨后京都-xhs-02.png"])
    with app_config_scope(_LEDGER_ON):
        after_redo = list_studio_trips(tmp_path)[0]
        handler2 = MockStudioHandler(tmp_path)
        handle_get_outputs(handler2, trip_dir.name)
    assert after_redo["outputSummary"]["total"] == 3
    assert len(after_redo["outputSummary"]["chips"]) == 3
    assert handler2.response is not None
    xhs = next(o for o in handler2.response[1]["outputs"] if o["outputId"] == "xiaohongshu")
    assert xhs["files"] == ["雨后京都-xhs-02.png"]

    _png(export_dir, "雨后京都-ch01.png")
    _export(trip_dir, trip, profile="wechat_chat", files=["雨后京都-ch01.png"], segmented=True)
    rows = read_ledger(trip_dir)
    assert rows is not None
    assert {r["outputId"] for r in rows} == {
        "xiaohongshu",
        "wechat_moments",
        "wechat_chat:whole",
        "wechat_chat:chapter",
    }
    with app_config_scope(_LEDGER_ON):
        four = list_studio_trips(tmp_path)[0]
    assert four["outputSummary"]["total"] == 4
    assert len(four["outputSummary"]["chips"]) == 3
    assert four["outputSummary"]["chips"][0]["label"]  # no empty chip

    (export_dir / "雨后京都-moments-01.png").unlink()
    healed = read_ledger(trip_dir)
    assert healed is not None
    assert {r["outputId"] for r in healed} == {
        "xiaohongshu",
        "wechat_chat:whole",
        "wechat_chat:chapter",
    }
    with app_config_scope(_LEDGER_ON):
        leftover = list_studio_trips(tmp_path)[0]
        handler3 = MockStudioHandler(tmp_path)
        handle_get_outputs(handler3, trip_dir.name)
    assert leftover["outputSummary"]["total"] == 3
    assert len(leftover["outputSummary"]["chips"]) == 3
    assert all(c["label"] for c in leftover["outputSummary"]["chips"])
    assert handler3.response is not None
    assert handler3.response[0] == 200
    assert len(handler3.response[1]["outputs"]) == 3


def _seed_shelf(trips_dir: Path, *, fat_id: str = "demo-olt-00") -> None:
    golden = load_golden_trip()
    for i in range(20):
        trip_id = f"demo-olt-{i:02d}"
        trip_dir, trip = _clone_trip(trips_dir, trip_id, golden)
        export_dir = trip_dir / EXPORT_OUTPUT_DIRNAME
        xhs = f"{trip_id}-xhs-01.png"
        moments = f"{trip_id}-moments-01.png"
        folio = f"{trip_id}-folio-00.png"
        _png(export_dir, xhs)
        _png(export_dir, moments)
        if trip_id == fat_id:
            folio_files = [f"{trip_id}-folio-{n:02d}.png" for n in range(48)]
            for name in folio_files:
                _png(export_dir, name)
            _export(trip_dir, trip, profile="portfolio_pages", files=folio_files)
        else:
            _png(export_dir, folio)
            _export(trip_dir, trip, profile="portfolio_pages", files=[folio])
        _export(trip_dir, trip, profile="xiaohongshu", files=[xhs])
        _export(trip_dir, trip, profile="wechat_moments", files=[moments])


def test_qa_olt_07_twenty_trips_get_trips_timing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-OLT-25 · 20 本 × 3 成品（含一条 48 文件 folio）GET /trips；每 trip 一次 scandir。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    _seed_shelf(trips_dir)

    from travelogue.export import output_ledger as ol

    calls = {"n": 0}
    real_existing = ol._existing_names

    def counting_existing(export_dir, scandir=None):
        calls["n"] += 1
        return real_existing(export_dir, scandir or ol.os.scandir)

    monkeypatch.setattr(ol, "_existing_names", counting_existing)

    def _get_trips(*, flag_on: bool) -> tuple[float, dict]:
        cfg = _LEDGER_ON if flag_on else _LEDGER_OFF
        with app_config_scope(cfg):
            handler = MockStudioHandler(trips_dir, path="/__travelogue/trips?limit=20")
            started = time.perf_counter()
            handle_trips(handler)
            elapsed_ms = (time.perf_counter() - started) * 1000
        assert handler.response is not None
        status, body = handler.response
        assert status == 200
        return elapsed_ms, body

    off_ms, off_body = _get_trips(flag_on=False)
    on_ms, on_body = _get_trips(flag_on=True)

    assert off_body["total"] == 20
    assert on_body["total"] == 20
    assert len(off_body["trips"]) == 20
    assert len(on_body["trips"]) == 20
    assert all("outputSummary" not in row for row in off_body["trips"])
    fat = next(row for row in on_body["trips"] if row["tripId"] == "demo-olt-00")
    assert fat["outputSummary"]["total"] == 3
    assert fat["outputSummary"]["chips"][0]["label"] == "作品集页图"
    assert all(len(row["outputSummary"]["chips"]) == 3 for row in on_body["trips"])
    assert calls["n"] == 20

    print(
        f"QA-OLT-07 GET /trips 20x3: flag_off={off_ms:.1f}ms flag_on={on_ms:.1f}ms "
        f"ratio={on_ms / off_ms if off_ms else float('inf'):.2f} scandir={calls['n']}"
    )
    # 改前 = 关旗 mtime 路径。允许账本读 JSON 的常数开销，但不接受数量级变慢。
    assert on_ms <= max(off_ms * 2.5, off_ms + 250.0)
