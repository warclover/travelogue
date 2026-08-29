"""OLT M2 · outputSummary + GET/DELETE outputs (BE-OLT-07/08/09 · AC-OLT-13/20/26)."""

from __future__ import annotations

import copy
import json
import os
import time
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from travelogue.config import AppConfig
from travelogue.config.runtime import app_config_scope
from travelogue.domain.output_fingerprint import source_snapshot
from travelogue.export.longshot import EXPORT_OUTPUT_DIRNAME
from travelogue.export.output_ledger import (
    append_output,
    build_output_summary,
    delete_output,
    record_is_outdated,
)
from travelogue.render.context import longshot_bundle_version
from travelogue.render.golden_regression import load_golden_trip
from travelogue.web.studio_dispatch import ROUTE_SPECS, _CAPTURE_MATCHERS, _compile_route
from travelogue.web.studio_handlers.common import match_trip_output_item, match_trip_outputs
import pytest

from tests.studio_test_helpers import MockStudioHandler
from travelogue.services.trip_factory import create_trip
from travelogue.web.studio_handlers.trip_handlers import handle_get_outputs
from travelogue.web.studio_trips import list_studio_trips

pytestmark = [pytest.mark.unit, pytest.mark.pipeline_isolation]


def _trip(tmp_path: Path) -> tuple[Path, dict]:
    trip = copy.deepcopy(load_golden_trip())
    trip_dir = tmp_path / "render-golden-demo"
    export_dir = trip_dir / EXPORT_OUTPUT_DIRNAME
    export_dir.mkdir(parents=True)
    (trip_dir / "trip.json").write_text(
        json.dumps(trip, ensure_ascii=False), encoding="utf-8"
    )
    return trip_dir, trip


def _record(trip: dict, *, output_id: str, profile: str, files: list[str], **extra: object) -> dict:
    bundle = longshot_bundle_version(trip)
    rec = {
        "outputId": output_id,
        "profile": profile,
        "surface": extra.get("surface") or "card",
        "label": extra.get("label") or "小红书",
        "edition": "journal",
        "createdAt": extra.get("createdAt") or "2026-08-26T03:11:07Z",
        "spec": {"format": "png"},
        "files": files,
        "fileCount": len(files),
        "source": extra.get("source")
        or source_snapshot(trip, bundle_fp=bundle, stale_options=()),
        "staleInputs": extra.get("staleInputs") or ["structure", "copy", "bundle"],
        "staleOptions": extra.get("staleOptions") or [],
    }
    return rec


def test_outputs_routes_registered() -> None:
    get_path = "/__travelogue/trips/{tripId}/outputs"
    delete_path = "/__travelogue/trips/{tripId}/outputs/{outputId}"
    gets = [s for s in ROUTE_SPECS if s.path == get_path and s.method == "GET"]
    deletes = [s for s in ROUTE_SPECS if s.path == delete_path and s.method == "DELETE"]
    assert gets and gets[0].handler == "trip_handlers.handle_get_outputs" and gets[0].auth
    assert deletes and deletes[0].handler == "trip_handlers.handle_delete_output"
    assert get_path in _CAPTURE_MATCHERS
    assert delete_path in _CAPTURE_MATCHERS
    assert _compile_route(gets[0]).match("/__travelogue/trips/demo/outputs") == "demo"
    assert match_trip_outputs("/__travelogue/trips/demo/outputs") == "demo"
    assert match_trip_output_item("/__travelogue/trips/demo/outputs/wechat_chat:whole") == (
        "demo",
        "wechat_chat:whole",
    )


def test_trips_omit_output_summary_when_flag_off(tmp_path: Path) -> None:
    trip_dir, trip = _trip(tmp_path)
    (trip_dir / EXPORT_OUTPUT_DIRNAME / "a.png").write_bytes(b"png")
    append_output(
        trip_dir,
        _record(trip, output_id="xiaohongshu", profile="xiaohongshu", files=["a.png"]),
    )
    cfg = replace(AppConfig(), studio=replace(AppConfig().studio, output_ledger=False))
    with app_config_scope(cfg):
        rows = list_studio_trips(tmp_path)
    assert rows
    assert "outputSummary" not in rows[0]


def test_trips_output_summary_on_by_default(tmp_path: Path) -> None:
    """BE-OLT-10 · 发布默认开旗时 /trips 带 outputSummary。"""
    trip_dir, trip = _trip(tmp_path)
    (trip_dir / EXPORT_OUTPUT_DIRNAME / "a.png").write_bytes(b"png")
    append_output(
        trip_dir,
        _record(trip, output_id="xiaohongshu", profile="xiaohongshu", files=["a.png"]),
    )
    with app_config_scope(AppConfig()):
        row = list_studio_trips(tmp_path)[0]
    assert row["outputSummary"]["total"] == 1
    assert row["outputSummary"]["chips"][0]["label"] == "小红书"


def test_trips_output_summary_and_stale_from_ledger(tmp_path: Path) -> None:
    trip_dir, trip = _trip(tmp_path)
    export_dir = trip_dir / EXPORT_OUTPUT_DIRNAME
    (export_dir / "folio.png").write_bytes(b"png")
    (export_dir / "xhs.png").write_bytes(b"png")
    (export_dir / "pack.zip").write_bytes(b"zip")
    append_output(
        trip_dir,
        _record(
            trip,
            output_id="portfolio_pages",
            profile="portfolio_pages",
            files=["folio.png"],
            surface="folio",
            label="作品集页图",
            createdAt="2026-08-20T00:00:00Z",
        ),
    )
    stale_src = source_snapshot(
        trip, bundle_fp=longshot_bundle_version(trip), stale_options=()
    )
    stale_src = dict(stale_src)
    stale_src["structureFp"] = "st:deadbeef"
    append_output(
        trip_dir,
        _record(
            trip,
            output_id="xiaohongshu",
            profile="xiaohongshu",
            files=["xhs.png"],
            surface="card",
            label="小红书",
            createdAt="2026-08-24T00:00:00Z",
            source=stale_src,
        ),
    )
    append_output(
        trip_dir,
        _record(
            trip,
            output_id="share_zip",
            profile="share_zip",
            files=["pack.zip"],
            surface="bundle",
            label="分享包",
        ),
    )
    cfg = replace(AppConfig(), studio=replace(AppConfig().studio, output_ledger=True))
    with app_config_scope(cfg):
        rows = list_studio_trips(tmp_path)
    row = rows[0]
    summary = row["outputSummary"]
    assert summary["total"] == 3
    labels = [c["label"] for c in summary["chips"]]
    assert labels[0] == "作品集页图"
    assert "分享包" not in labels
    assert all("fileCount" not in chip for chip in summary["chips"])
    states = {c["label"]: c["state"] for c in summary["chips"]}
    assert states["作品集页图"] == "ready"
    assert states["小红书"] == "outdated"
    assert row["longshotStale"] is True


def test_summary_ready_when_fingerprints_match(tmp_path: Path) -> None:
    trip_dir, trip = _trip(tmp_path)
    (trip_dir / EXPORT_OUTPUT_DIRNAME / "a.png").write_bytes(b"png")
    rec = _record(trip, output_id="xiaohongshu", profile="xiaohongshu", files=["a.png"])
    append_output(trip_dir, rec)
    bundle = longshot_bundle_version(trip)
    assert record_is_outdated(rec, trip, bundle) is False
    summary = build_output_summary([rec], trip, bundle)
    assert summary["chips"][0]["state"] == "ready"
    cfg = replace(AppConfig(), studio=replace(AppConfig().studio, output_ledger=True))
    with app_config_scope(cfg):
        row = list_studio_trips(tmp_path)[0]
    assert row["longshotStale"] is False
    assert row["outputSummary"]["chips"][0]["state"] == "ready"


def test_delete_output_removes_file_and_row(tmp_path: Path) -> None:
    trip_dir, trip = _trip(tmp_path)
    path = trip_dir / EXPORT_OUTPUT_DIRNAME / "a.png"
    path.write_bytes(b"png")
    append_output(
        trip_dir,
        _record(trip, output_id="xiaohongshu", profile="xiaohongshu", files=["a.png"]),
    )
    assert delete_output(trip_dir, "xiaohongshu") is True
    assert not path.exists()
    assert delete_output(trip_dir, "xiaohongshu") is False


def test_get_outputs_empty_when_no_ledger(tmp_path: Path) -> None:
    """AC-OLT-20 · 无账本返回空列表，不是 404。"""
    trips_dir = tmp_path / "trips"
    create_trip("demo-olt-empty", trips_dir, title="无账本", place="京都")
    cfg = replace(AppConfig(), studio=replace(AppConfig().studio, output_ledger=True))
    with app_config_scope(cfg):
        handler = MockStudioHandler(trips_dir)
        handle_get_outputs(handler, "demo-olt-empty")
    assert handler.response == (200, {"ok": True, "outputs": []})


def test_get_outputs_empty_when_flag_off(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_dir, trip = _trip(trips_dir)
    (trip_dir / EXPORT_OUTPUT_DIRNAME / "a.png").write_bytes(b"png")
    append_output(
        trip_dir,
        _record(trip, output_id="xiaohongshu", profile="xiaohongshu", files=["a.png"]),
    )
    cfg = replace(AppConfig(), studio=replace(AppConfig().studio, output_ledger=False))
    with app_config_scope(cfg):
        handler = MockStudioHandler(trips_dir)
        handle_get_outputs(handler, trip_dir.name)
    assert handler.response == (200, {"ok": True, "outputs": []})


def test_get_outputs_404_when_trip_missing(tmp_path: Path) -> None:
    handler = MockStudioHandler(tmp_path / "trips")
    handle_get_outputs(handler, "missing-trip")
    assert handler.response == (404, {"ok": False, "error": "trip not found"})


def test_flag_off_longshot_stale_still_uses_mtime(tmp_path: Path) -> None:
    """AC-OLT-26 · 关旗逐字回到 mtime；开旗才换指纹（即使账本已写且指纹匹配）。"""
    trip_dir, trip = _trip(tmp_path)
    export_dir = trip_dir / EXPORT_OUTPUT_DIRNAME
    png = export_dir / f"{trip_dir.name}-xhs-01.png"
    png.write_bytes(b"png")
    older = time.time() - 120
    os.utime(png, (older, older))
    trip["updatedAt"] = (
        datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )
    (trip_dir / "trip.json").write_text(
        json.dumps(trip, ensure_ascii=False), encoding="utf-8"
    )
    rec = _record(
        trip,
        output_id="xiaohongshu",
        profile="xiaohongshu",
        files=[png.name],
        surface="card",
        label="小红书",
    )
    append_output(trip_dir, rec)
    bundle = longshot_bundle_version(trip)
    assert record_is_outdated(rec, trip, bundle) is False

    off_cfg = replace(AppConfig(), studio=replace(AppConfig().studio, output_ledger=False))
    with app_config_scope(off_cfg):
        off = list_studio_trips(tmp_path)[0]
    assert "outputSummary" not in off
    assert off["longshotStale"] is True

    cfg = replace(AppConfig(), studio=replace(AppConfig().studio, output_ledger=True))
    with app_config_scope(cfg):
        on = list_studio_trips(tmp_path)[0]
    assert on["longshotStale"] is False
    assert on["outputSummary"]["chips"][0]["state"] == "ready"


def test_build_book_zero_output_dom_order() -> None:
    """AC-OLT-14 · buildBook 只在有副券时插行；C12 票根不再挂工程编码。"""
    shelf = Path("templates/studio/homepage-v2/shelf.js").read_text(encoding="utf-8")
    i_main = shelf.index("openMeta.appendChild(stubMain)")
    i_stubs = shelf.index("if (stubs)")
    assert i_main < i_stubs
    assert "openMeta.appendChild(code)" not in shelf
    assert "v2-shelf__code" not in shelf
    assert 'openMeta.classList.add("v2-shelf__stub--chips")' in shelf
    assert "allowReadyBadge(trip)" in shelf
