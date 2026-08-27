"""OLT M1 · outputs.json ledger (QA-OLT-01 / AC-OLT-01–07/13/25/28/29).

Clones ``trip.render_golden.json`` only (BLK-OLT-07).
"""

from __future__ import annotations

import copy
import json
import os
from dataclasses import replace
from pathlib import Path

import pytest

from travelogue.config import AppConfig
from travelogue.config.runtime import app_config_scope
from travelogue.export.longshot import EXPORT_OUTPUT_DIRNAME, LongshotExportResult, LongshotOutput
from travelogue.export.output_ledger import (
    LEDGER_NAME,
    LEDGER_SCHEMA_VERSION,
    append_output,
    drop_output_row,
    ledger_path,
    load_trip_dict,
    lookup_output_meta,
    output_ledger_enabled,
    read_ledger,
    record_dispatch_result,
    record_successful_output,
    resolve_output_id,
)
from travelogue.export.platform_profiles import get_profile
from travelogue.render.golden_regression import load_golden_trip

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


def _png(export_dir: Path, name: str) -> Path:
    path = export_dir / name
    path.write_bytes(b"png")
    return path


def _record(
    trip: dict,
    *,
    output_id: str,
    profile: str,
    files: list[str],
    label: str = "小红书",
    surface: str = "card",
    stale_inputs: list[str] | None = None,
    stale_options: list[str] | None = None,
) -> dict:
    inputs = stale_inputs or ["structure", "copy", "bundle"]
    options = stale_options or []
    rec = {
        "outputId": output_id,
        "profile": profile,
        "surface": surface,
        "label": label,
        "edition": "journal",
        "createdAt": "2026-08-26T03:11:07Z",
        "spec": {"width": 1080, "height": 1440, "format": "png", "scale": 1},
        "files": files,
        "fileCount": len(files),
        "source": {
            "structureFp": "st:aaaaaaaa",
            "copyFp": "cp:bbbbbbbb",
            "bundleFp": "lse16f41315f6a",
            "optionsFp": None,
        },
        "staleInputs": inputs,
        "staleOptions": options,
    }
    return rec


def test_schema_roundtrip(tmp_path: Path) -> None:
    trip_dir, trip = _trip(tmp_path)
    export_dir = trip_dir / EXPORT_OUTPUT_DIRNAME
    _png(export_dir, "雨后京都-xhs-01.png")
    rec = _record(trip, output_id="xiaohongshu", profile="xiaohongshu", files=["雨后京都-xhs-01.png"])
    path = append_output(trip_dir, rec)
    assert path is not None
    assert path.name == LEDGER_NAME
    rows = read_ledger(trip_dir)
    assert rows is not None
    assert len(rows) == 1
    assert rows[0]["outputId"] == "xiaohongshu"
    assert rows[0]["files"] == ["雨后京都-xhs-01.png"]
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schemaVersion"] == LEDGER_SCHEMA_VERSION


def test_version_mismatch_returns_none(tmp_path: Path) -> None:
    trip_dir, _trip_data = _trip(tmp_path)
    path = ledger_path(trip_dir)
    path.write_text(
        json.dumps({"schemaVersion": 99, "outputs": []}, ensure_ascii=False),
        encoding="utf-8",
    )
    assert read_ledger(trip_dir) is None


def test_heal_drops_partial_and_counts_one_scandir(tmp_path: Path) -> None:
    trip_dir, trip = _trip(tmp_path)
    export_dir = trip_dir / EXPORT_OUTPUT_DIRNAME
    for i in range(48):
        _png(export_dir, f"页-{i:02d}.png")
    _png(export_dir, "雨后京都-xhs-01.png")
    append_output(
        trip_dir,
        _record(
            trip,
            output_id="portfolio_pages",
            profile="portfolio_pages",
            files=[f"页-{i:02d}.png" for i in range(48)],
            label="作品集页图",
            surface="folio",
        ),
    )
    append_output(
        trip_dir,
        _record(trip, output_id="xiaohongshu", profile="xiaohongshu", files=["雨后京都-xhs-01.png"]),
    )
    (export_dir / "页-00.png").unlink()
    calls = {"n": 0}

    def counting_scandir(path):
        calls["n"] += 1
        return os.scandir(path)

    rows = read_ledger(trip_dir, scandir=counting_scandir)
    assert calls["n"] == 1
    assert rows is not None
    assert [r["outputId"] for r in rows] == ["xiaohongshu"]


def test_same_output_id_replaces(tmp_path: Path) -> None:
    trip_dir, trip = _trip(tmp_path)
    export_dir = trip_dir / EXPORT_OUTPUT_DIRNAME
    _png(export_dir, "a.png")
    _png(export_dir, "b.png")
    append_output(
        trip_dir,
        _record(trip, output_id="xiaohongshu", profile="xiaohongshu", files=["a.png"]),
    )
    append_output(
        trip_dir,
        _record(trip, output_id="xiaohongshu", profile="xiaohongshu", files=["b.png"]),
    )
    rows = read_ledger(trip_dir)
    assert rows is not None
    assert len(rows) == 1
    assert rows[0]["files"] == ["b.png"]


def test_wechat_chat_whole_and_chapter_coexist(tmp_path: Path) -> None:
    trip_dir, trip = _trip(tmp_path)
    export_dir = trip_dir / EXPORT_OUTPUT_DIRNAME
    _png(export_dir, "雨后京都-长图.png")
    _png(export_dir, "雨后京都-ch01.png")
    record_successful_output(
        trip_dir,
        trip=trip,
        profile="wechat_chat",
        files=["雨后京都-长图.png"],
        spec={"format": "png"},
        bundle_fp="lse16f41315f6a",
        segmented=False,
    )
    record_successful_output(
        trip_dir,
        trip=trip,
        profile="wechat_chat",
        files=["雨后京都-ch01.png"],
        spec={"format": "png"},
        bundle_fp="lse16f41315f6a",
        segmented=True,
    )
    rows = read_ledger(trip_dir)
    assert rows is not None
    ids = {r["outputId"] for r in rows}
    assert ids == {"wechat_chat:whole", "wechat_chat:chapter"}
    labels = {r["outputId"]: r["label"] for r in rows}
    assert labels["wechat_chat:whole"] == "微信群"
    assert labels["wechat_chat:chapter"] == "微信群 · 分章"


def test_custom_does_not_write(tmp_path: Path) -> None:
    trip_dir, trip = _trip(tmp_path)
    export_dir = trip_dir / EXPORT_OUTPUT_DIRNAME
    _png(export_dir, "custom.png")
    assert resolve_output_id("custom") is None
    assert (
        record_successful_output(
            trip_dir,
            trip=trip,
            profile="custom",
            files=["custom.png"],
            spec={"width": 1080, "height": 1920},
            bundle_fp="lse16f41315f6a",
        )
        is None
    )
    assert not ledger_path(trip_dir).is_file()


def test_flag_on_by_default() -> None:
    with app_config_scope(AppConfig()):
        assert output_ledger_enabled() is True


def test_flag_off_still_rolls_back() -> None:
    cfg = replace(AppConfig(), studio=replace(AppConfig().studio, output_ledger=False))
    with app_config_scope(cfg):
        assert output_ledger_enabled() is False


def test_dispatch_does_not_write_when_flag_off(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    trip_dir, _trip_data = _trip(tmp_path)
    export_dir = trip_dir / EXPORT_OUTPUT_DIRNAME
    png = _png(export_dir, "雨后京都-xhs-01.png")
    result = LongshotExportResult(
        outputs=[LongshotOutput(path=png)],
        platform="xiaohongshu",
        profile_label="小红书",
    )
    monkeypatch.setattr(
        "travelogue.export.collage_pack.export_collage_pack",
        lambda *args, **kwargs: result,
    )
    from travelogue.export.dispatch import dispatch_export

    cfg = replace(AppConfig(), studio=replace(AppConfig().studio, output_ledger=False))
    with app_config_scope(cfg):
        out = dispatch_export(trip_dir, platform="xiaohongshu")
    assert out is result
    assert not ledger_path(trip_dir).is_file()


def test_dispatch_writes_when_flag_on(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    trip_dir, _trip_data = _trip(tmp_path)
    export_dir = trip_dir / EXPORT_OUTPUT_DIRNAME
    png = _png(export_dir, "雨后京都-xhs-01.png")
    result = LongshotExportResult(
        outputs=[LongshotOutput(path=png)],
        platform="xiaohongshu",
        profile_label="小红书",
    )
    monkeypatch.setattr(
        "travelogue.export.collage_pack.export_collage_pack",
        lambda *args, **kwargs: result,
    )
    from travelogue.export.dispatch import dispatch_export

    cfg = replace(AppConfig(), studio=replace(AppConfig().studio, output_ledger=True))
    with app_config_scope(cfg):
        dispatch_export(trip_dir, platform="xiaohongshu")
    rows = read_ledger(trip_dir)
    assert rows is not None
    assert rows[0]["outputId"] == "xiaohongshu"
    assert rows[0]["label"] == "小红书"


def test_dispatch_skips_custom_result(tmp_path: Path) -> None:
    trip_dir, trip = _trip(tmp_path)
    export_dir = trip_dir / EXPORT_OUTPUT_DIRNAME
    png = _png(export_dir, "custom.png")
    result = LongshotExportResult(
        outputs=[LongshotOutput(path=png)],
        platform="custom",
    )
    record_dispatch_result(
        trip_dir,
        result,
        platform="custom",
        bundle_fp="lse16f41315f6a",
        trip=trip,
    )
    assert not ledger_path(trip_dir).is_file()


def test_yaml_surfaces_and_stale_tables() -> None:
    moments = get_profile("wechat_moments")
    assert moments.surface == "scroll"
    assert "longshotDensity" in moments.stale_options
    pages = get_profile("portfolio_pages")
    assert pages.surface == "folio"
    assert "longshotDensity" not in pages.stale_options
    grid = get_profile("moments_grid")
    assert grid.surface == "grid"
    assert "options" not in grid.stale_inputs
    assert lookup_output_meta("share_zip") is not None
    assert lookup_output_meta("pdf") is not None
    assert lookup_output_meta("custom") is None


def test_public_bundle_accessor_matches_private() -> None:
    from travelogue.render.context import _longshot_bundle_version, longshot_bundle_version

    trip = copy.deepcopy(load_golden_trip())
    assert longshot_bundle_version(trip) == _longshot_bundle_version(trip)


def test_load_trip_dict_reads_golden_clone(tmp_path: Path) -> None:
    trip_dir, trip = _trip(tmp_path)
    loaded = load_trip_dict(trip_dir)
    assert loaded["tripId"] == trip["tripId"]


def test_enabled_flag_from_config() -> None:
    cfg = replace(AppConfig(), studio=replace(AppConfig().studio, output_ledger=True))
    with app_config_scope(cfg):
        assert output_ledger_enabled() is True


def test_empty_portfolio_pages_drops_stale_row(tmp_path: Path) -> None:
    trip_dir, trip = _trip(tmp_path)
    export_dir = trip_dir / EXPORT_OUTPUT_DIRNAME
    _png(export_dir, "页-01.png")
    append_output(
        trip_dir,
        _record(
            trip,
            output_id="portfolio_pages",
            profile="portfolio_pages",
            files=["页-01.png"],
            label="页图",
            surface="folio",
        ),
    )
    result = LongshotExportResult(outputs=[], platform="portfolio_pages")
    record_dispatch_result(
        trip_dir,
        result,
        platform="portfolio_pages",
        bundle_fp="lse16f41315f6a",
        trip=trip,
    )
    rows = read_ledger(trip_dir) or []
    assert all(rec["outputId"] != "portfolio_pages" for rec in rows)
    assert (export_dir / "页-01.png").is_file()


def test_concurrent_append_keeps_both_rows(tmp_path: Path) -> None:
    import threading

    trip_dir, trip = _trip(tmp_path)
    export_dir = trip_dir / EXPORT_OUTPUT_DIRNAME
    _png(export_dir, "a.png")
    _png(export_dir, "b.png")
    errors: list[BaseException] = []

    def write(output_id: str, name: str) -> None:
        try:
            append_output(
                trip_dir,
                _record(
                    trip,
                    output_id=output_id,
                    profile=output_id,
                    files=[name],
                    label=output_id,
                ),
            )
        except BaseException as exc:  # noqa: BLE001 — collect worker errors
            errors.append(exc)

    workers = [
        threading.Thread(target=write, args=("xiaohongshu", "a.png")),
        threading.Thread(target=write, args=("wechat_moments", "b.png")),
    ]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()
    assert errors == []
    rows = read_ledger(trip_dir)
    assert rows is not None
    assert {rec["outputId"] for rec in rows} == {"xiaohongshu", "wechat_moments"}


def test_drop_output_row_keeps_files(tmp_path: Path) -> None:
    trip_dir, trip = _trip(tmp_path)
    export_dir = trip_dir / EXPORT_OUTPUT_DIRNAME
    _png(export_dir, "页-01.png")
    append_output(
        trip_dir,
        _record(
            trip,
            output_id="portfolio_pages",
            profile="portfolio_pages",
            files=["页-01.png"],
            label="页图",
            surface="folio",
        ),
    )
    assert drop_output_row(trip_dir, "portfolio_pages") is True
    assert drop_output_row(trip_dir, "portfolio_pages") is False
    assert (export_dir / "页-01.png").is_file()
    assert (read_ledger(trip_dir) or []) == []
