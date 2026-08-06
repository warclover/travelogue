"""PRD-BATCH-EXPORT-MULTISELECT-V1 Stage 1 · export_trip_longshot_batch 单测。

只测调度层本身（顺序调用 / 部分失败继续 / 取消中断）；不重复测 CardGrouper /
Playwright 渲染细节（已由 collage_pack / longshot 现有测试覆盖）。
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from travelogue.export.longshot import LongshotCancelled, LongshotExportError, LongshotExportResult
from travelogue.export.longshot_batch import (
    BatchExportRequest,
    export_trip_longshot_batch,
)

pytestmark = pytest.mark.unit


def _fake_result(platform: str) -> LongshotExportResult:
    return LongshotExportResult(platform=platform, page_count=1)


def test_batch_runs_all_requests_in_order(tmp_path: Path) -> None:
    calls: list[str] = []

    def fake_export(trip_dir, *, platform, **_kwargs):
        calls.append(platform)
        return _fake_result(platform)

    requests = [
        BatchExportRequest(platform="xiaohongshu"),
        BatchExportRequest(platform="wechat_official"),
        BatchExportRequest(platform="album_spread"),
    ]
    with patch("travelogue.export.longshot_batch.export_trip_longshot", side_effect=fake_export):
        results = export_trip_longshot_batch(tmp_path, requests=requests)

    assert calls == ["xiaohongshu", "wechat_official", "album_spread"]
    assert [r.platform for r in results] == calls
    assert all(r.ok for r in results)


def test_batch_continues_after_item_failure(tmp_path: Path) -> None:
    def fake_export(trip_dir, *, platform, **_kwargs):
        if platform == "wechat_moments":
            raise LongshotExportError("E_LNG_CAPTURE_TOO_LARGE", "太大了")
        return _fake_result(platform)

    requests = [
        BatchExportRequest(platform="xiaohongshu"),
        BatchExportRequest(platform="wechat_moments"),
        BatchExportRequest(platform="album_spread"),
    ]
    with patch("travelogue.export.longshot_batch.export_trip_longshot", side_effect=fake_export):
        results = export_trip_longshot_batch(tmp_path, requests=requests)

    assert [r.platform for r in results] == ["xiaohongshu", "wechat_moments", "album_spread"]
    assert results[0].ok is True
    assert results[1].ok is False
    assert results[1].error_code == "E_LNG_CAPTURE_TOO_LARGE"
    assert results[2].ok is True  # 第 3 项仍跑完，未被第 2 项失败阻塞（D-BEX-05）


def test_batch_continues_after_unexpected_exception(tmp_path: Path) -> None:
    def fake_export(trip_dir, *, platform, **_kwargs):
        if platform == "xiaohongshu":
            raise RuntimeError("boom")
        return _fake_result(platform)

    requests = [
        BatchExportRequest(platform="xiaohongshu"),
        BatchExportRequest(platform="album_spread"),
    ]
    with patch("travelogue.export.longshot_batch.export_trip_longshot", side_effect=fake_export):
        results = export_trip_longshot_batch(tmp_path, requests=requests)

    assert results[0].ok is False
    assert results[0].error_code == "E_LNG_CAPTURE_FAILED"
    assert "boom" in results[0].error_message
    assert results[1].ok is True


def test_batch_stops_before_next_item_when_cancelled(tmp_path: Path) -> None:
    calls: list[str] = []
    cancelled = {"flag": False}

    def fake_export(trip_dir, *, platform, **_kwargs):
        calls.append(platform)
        cancelled["flag"] = True  # 模拟第一项跑完后用户取消
        return _fake_result(platform)

    requests = [
        BatchExportRequest(platform="xiaohongshu"),
        BatchExportRequest(platform="album_spread"),
    ]
    with patch("travelogue.export.longshot_batch.export_trip_longshot", side_effect=fake_export):
        results = export_trip_longshot_batch(
            tmp_path, requests=requests, cancel_check=lambda: cancelled["flag"]
        )

    assert calls == ["xiaohongshu"]
    assert len(results) == 1
    assert results[0].ok is True


def test_batch_reraises_longshot_cancelled_mid_item(tmp_path: Path) -> None:
    def fake_export(trip_dir, *, platform, **_kwargs):
        if platform == "wechat_moments":
            raise LongshotCancelled()
        return _fake_result(platform)

    requests = [
        BatchExportRequest(platform="xiaohongshu"),
        BatchExportRequest(platform="wechat_moments"),
        BatchExportRequest(platform="album_spread"),
    ]
    with patch("travelogue.export.longshot_batch.export_trip_longshot", side_effect=fake_export):
        with pytest.raises(LongshotCancelled):
            export_trip_longshot_batch(tmp_path, requests=requests)


def test_batch_progress_callback_receives_item_context(tmp_path: Path) -> None:
    seen: list[tuple] = []

    def fake_export(trip_dir, *, platform, progress=None, **_kwargs):
        if progress:
            progress(1, 3, "正在合成第 1/3 张…")
        return _fake_result(platform)

    def on_progress(item_index, item_total, item_platform, cur, total, hint):
        seen.append((item_index, item_total, item_platform, cur, total, hint))

    requests = [
        BatchExportRequest(platform="xiaohongshu"),
        BatchExportRequest(platform="album_spread"),
    ]
    with patch("travelogue.export.longshot_batch.export_trip_longshot", side_effect=fake_export):
        export_trip_longshot_batch(tmp_path, requests=requests, progress=on_progress)

    assert seen == [
        (0, 2, "xiaohongshu", 1, 3, "正在合成第 1/3 张…"),
        (1, 2, "album_spread", 1, 3, "正在合成第 1/3 张…"),
    ]


def test_batch_passes_per_item_fields_and_common_kwargs(tmp_path: Path) -> None:
    received: list[dict] = []

    def fake_export(trip_dir, *, platform, **kwargs):
        received.append({"platform": platform, **kwargs})
        return _fake_result(platform)

    requests = [
        BatchExportRequest(
            platform="xiaohongshu", slide_count=6, pad_mode=None, segment_mode="auto",
            copy_display="full",
        ),
        BatchExportRequest(
            platform="wechat_moments", slide_count=None, pad_mode=None,
            segment_mode="auto", copy_display="photos",
        ),
    ]
    with patch("travelogue.export.longshot_batch.export_trip_longshot", side_effect=fake_export):
        export_trip_longshot_batch(
            tmp_path, requests=requests, common={"scale": 3, "fmt": "jpeg", "include_appendix": True}
        )

    assert received[0]["slide_count"] == 6
    assert received[0]["scale"] == 3
    assert received[0]["fmt"] == "jpeg"
    assert received[0]["include_appendix"] is True
    assert received[1]["copy_display"] == "photos"
