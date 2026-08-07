"""PRD-BATCH-EXPORT-MULTISELECT-V1 Stage 1 · handle_longshot `platforms[]` 分支单测。

覆盖 D-BEX-01/02/05 与 AC-BEX-03/04/05：多平台校验、单 Job 语义不变、
单项失败不阻塞其余平台、结果清单契约。
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from tests.studio_test_helpers import MockStudioHandler, wait_for_job
from travelogue.export.longshot import LongshotExportError, LongshotExportResult
from travelogue.services.trip_factory import create_trip
from travelogue.web.studio_handlers.export_handlers import handle_longshot
from travelogue.web.studio_jobs import get_job_store, reset_job_store

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    reset_job_store()


def _fetch(job_id: str) -> dict:
    job = get_job_store().get(job_id)
    assert job is not None
    return job.to_dict()


def test_handle_longshot_batch_rejects_non_dict_item(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    create_trip("demo", trips, title="demo")
    handler = MockStudioHandler(
        trips,
        json_body={
            "tripId": "demo",
            "platforms": ["xiaohongshu"],
            "allowMissingSource": True,
        },
    )
    handle_longshot(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 400
    assert body["error"] == "E_LNG2_INVALID_BATCH_ITEM"


def test_handle_longshot_batch_rejects_missing_platform(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    create_trip("demo", trips, title="demo")
    handler = MockStudioHandler(
        trips,
        json_body={
            "tripId": "demo",
            "platforms": [{"slideCount": 6}],
            "allowMissingSource": True,
        },
    )
    handle_longshot(handler)
    status, body = handler.response
    assert status == 400
    assert body["error"] == "E_LNG2_INVALID_BATCH_ITEM"


def test_handle_longshot_batch_rejects_duplicate_platform(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    create_trip("demo", trips, title="demo")
    handler = MockStudioHandler(
        trips,
        json_body={
            "tripId": "demo",
            "platforms": [{"platform": "xiaohongshu"}, {"platform": "xiaohongshu"}],
            "allowMissingSource": True,
        },
    )
    handle_longshot(handler)
    status, body = handler.response
    assert status == 400
    assert body["error"] == "E_LNG2_DUPLICATE_PLATFORM"


def test_handle_longshot_batch_rejects_invalid_platform_id(tmp_path: Path) -> None:
    """AC-LNG2-05c 同款约束：批量单项非法平台 → 400，不静默丢弃该项。"""
    trips = tmp_path / "trips"
    create_trip("demo", trips, title="demo")
    handler = MockStudioHandler(
        trips,
        json_body={
            "tripId": "demo",
            "platforms": [{"platform": "xiaohongshu"}, {"platform": "not_a_real_platform"}],
            "allowMissingSource": True,
        },
    )
    handle_longshot(handler)
    status, body = handler.response
    assert status == 400
    assert body["error"] in ("E_LNG2_INVALID_PLATFORM", "E_OR_UNKNOWN_PLATFORM")


def test_handle_longshot_batch_rejects_poster_bric_when_flag_off(tmp_path: Path) -> None:
    """AC-DFX-04 同款约束：批量含 poster_bric 且 flag off → 400（禁止半开）。"""
    from travelogue.config.studio import GcsPosterBricConfig

    trips = tmp_path / "trips"
    create_trip("demo", trips, title="demo")
    handler = MockStudioHandler(
        trips,
        json_body={
            "tripId": "demo",
            "platforms": [{"platform": "xiaohongshu"}, {"platform": "poster_bric"}],
            "allowMissingSource": True,
        },
    )
    handler.app_config.studio.gcs_poster_bric = GcsPosterBricConfig(enabled=False)
    handle_longshot(handler)
    status, body = handler.response
    assert status == 400
    assert body["error"] == "E_GCS_POSTER_DISABLED"


def _fake_result(platform: str, n: int = 3) -> LongshotExportResult:
    from travelogue.export.longshot import LongshotOutput

    return LongshotExportResult(
        outputs=[LongshotOutput(path=Path(f"/tmp/{platform}-{i}.png")) for i in range(n)],
        platform=platform,
        profile_label=platform,
        page_count=n,
        user_hint=f"{platform} hint",
    )


def test_handle_longshot_batch_partial_failure_continues_and_reports_items(
    tmp_path: Path,
) -> None:
    """D-BEX-05 / AC-BEX-04 · 一项失败不阻塞其余；结果清单标注每项成败。"""
    trips = tmp_path / "trips"
    create_trip("demo", trips, title="demo")
    trip_dir = trips / "demo"
    # rel_to_trip requires outputs to live under trip_dir.
    order: list[str] = []

    def fake_export(_trip_dir, *, platform, **_kwargs):
        order.append(platform)
        if platform == "wechat_moments":
            raise LongshotExportError("E_LNG_CAPTURE_TOO_LARGE", "画布太大")
        out_path = trip_dir / f"{platform}-01.png"
        out_path.write_bytes(b"fake")
        from travelogue.export.longshot import LongshotOutput

        return LongshotExportResult(
            outputs=[LongshotOutput(path=out_path)],
            platform=platform,
            profile_label=platform,
            page_count=1,
            user_hint=f"{platform} ok",
        )

    handler = MockStudioHandler(
        trips,
        json_body={
            "tripId": "demo",
            "platforms": [
                {"platform": "xiaohongshu"},
                {"platform": "wechat_moments"},
                {"platform": "album_spread"},
            ],
            "allowMissingSource": True,
        },
    )
    with (
        patch(
            "travelogue.web.studio_handlers.export_handlers._ensure_derivatives_for_export",
        ),
        patch(
            "travelogue.export.longshot.playwright_longshot_available", return_value=True
        ),
        patch(
            "travelogue.export.longshot_batch.export_trip_longshot", side_effect=fake_export
        ),
    ):
        handle_longshot(handler)
        assert handler.response is not None
        status, body = handler.response
        assert status == 202
        job_id = body["jobId"]

        job_dict = wait_for_job(lambda: _fetch(job_id), timeout_sec=5)

    assert order == ["xiaohongshu", "wechat_moments", "album_spread"]
    assert job_dict["status"] == "succeeded"
    result = job_dict["result"]
    assert result["batch"] is True
    assert result["succeededCount"] == 2
    assert result["failedCount"] == 1
    items = result["items"]
    assert [i["platform"] for i in items] == ["xiaohongshu", "wechat_moments", "album_spread"]
    assert items[0]["ok"] is True
    assert items[0]["outputs"] == ["xiaohongshu-01.png"]
    assert items[1]["ok"] is False
    assert items[1]["error"] == "E_LNG_CAPTURE_TOO_LARGE"
    assert items[2]["ok"] is True

    # QFX 同款约束：longshot-current.json 反映最后一个成功平台（album_spread）。
    # EOI · 清单落在 EXPORT_OUTPUT_DIRNAME 子目录（与产物同层）而非 trip_dir 根。
    from travelogue.export.longshot import EXPORT_OUTPUT_DIRNAME

    current = (trip_dir / EXPORT_OUTPUT_DIRNAME / "longshot-current.json").read_text(
        encoding="utf-8"
    )
    assert "album_spread-01.png" in current


def test_handle_longshot_single_platform_request_shape_unaffected(tmp_path: Path) -> None:
    """AC-BEX-05 契约测试：不带 `platforms` 字段的既有单平台请求，响应结构里

    不出现任何批量专属字段（`batch`/`items`/`succeededCount`/`failedCount`），
    仍是改动前的扁平结构（`outputs`/`pageCount`/`userHint`/`platform`）——
    证明 D-BEX-02 的"批量分支与单平台路径完全独立"承诺在响应契约层面同样成立。
    """
    trips = tmp_path / "trips"
    create_trip("demo", trips, title="demo")
    trip_dir = trips / "demo"

    def fake_export(_trip_dir, *, platform, **_kwargs):
        out_path = trip_dir / f"{platform}-01.png"
        out_path.write_bytes(b"fake")
        from travelogue.export.longshot import LongshotOutput

        return LongshotExportResult(
            outputs=[LongshotOutput(path=out_path)],
            platform=platform,
            profile_label=platform,
            page_count=1,
            user_hint=f"{platform} ok",
        )

    handler = MockStudioHandler(
        trips,
        json_body={
            "tripId": "demo",
            "platform": "xiaohongshu",
            "allowMissingSource": True,
        },
    )
    with (
        patch(
            "travelogue.web.studio_handlers.export_handlers._ensure_derivatives_for_export",
        ),
        patch(
            "travelogue.export.longshot.playwright_longshot_available", return_value=True
        ),
        patch(
            "travelogue.export.longshot.export_trip_longshot",
            side_effect=fake_export,
        ),
    ):
        handle_longshot(handler)
        assert handler.response is not None
        status, body = handler.response
        assert status == 202
        job_id = body["jobId"]
        job_dict = wait_for_job(lambda: _fetch(job_id), timeout_sec=5)

    assert job_dict["status"] == "succeeded"
    result = job_dict["result"]
    # 批量专属字段一律不出现——不是"为 False/None"，而是键本身不存在。
    for batch_only_key in ("batch", "items", "succeededCount", "failedCount"):
        assert batch_only_key not in result, f"单平台响应不应包含批量字段 {batch_only_key!r}"
    assert result["platform"] == "xiaohongshu"
    assert result["pageCount"] == 1
    assert result["outputs"] == ["xiaohongshu-01.png"]
    assert result["userHint"] == "xiaohongshu ok"


def test_handle_longshot_batch_single_job_lock_shared_with_single_platform(
    tmp_path: Path,
) -> None:
    """AC-BEX-03 · 批量导出仍是一个 Job；Job Store 单锁语义不变（D-BEX-03）。"""
    job = get_job_store().create_longshot_job()
    assert job is not None

    trips = tmp_path / "trips"
    create_trip("demo", trips, title="demo")
    handler = MockStudioHandler(
        trips,
        json_body={
            "tripId": "demo",
            "platforms": [{"platform": "xiaohongshu"}, {"platform": "album_spread"}],
            "allowMissingSource": True,
        },
    )
    handle_longshot(handler)
    status, body = handler.response
    assert status == 409
    assert body["error"] == "E_STUDIO_JOB_BUSY"


def test_handle_longshot_batch_rejects_empty_platforms_array(tmp_path: Path) -> None:
    """显式携带 platforms:[] 必须 400，禁止静默退回单平台默认导出。"""
    trips = tmp_path / "trips"
    create_trip("demo", trips, title="demo")
    handler = MockStudioHandler(
        trips,
        json_body={
            "tripId": "demo",
            "platforms": [],
            "allowMissingSource": True,
        },
    )
    handle_longshot(handler)
    status, body = handler.response
    assert status == 400
    assert body["error"] == "E_LNG2_EMPTY_BATCH"


def test_handle_longshot_batch_rejects_non_list_platforms(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    create_trip("demo", trips, title="demo")
    handler = MockStudioHandler(
        trips,
        json_body={
            "tripId": "demo",
            "platforms": "xiaohongshu",
            "allowMissingSource": True,
        },
    )
    handle_longshot(handler)
    status, body = handler.response
    assert status == 400
    assert body["error"] == "E_LNG2_INVALID_BATCH_ITEM"


def test_handle_longshot_batch_compose_only_ok_without_playwright(
    tmp_path: Path,
) -> None:
    """AC-ECC-05 / PRD-BATCH §2 · 纯 Compose 批量在缺 Playwright 时仍应可提交。"""
    trips = tmp_path / "trips"
    create_trip("demo", trips, title="demo")
    trip_dir = trips / "demo"

    def fake_export(_trip_dir, *, platform, **_kwargs):
        out_path = trip_dir / f"{platform}-01.png"
        out_path.write_bytes(b"fake")
        from travelogue.export.longshot import LongshotOutput

        return LongshotExportResult(
            outputs=[LongshotOutput(path=out_path)],
            platform=platform,
            profile_label=platform,
            page_count=1,
            user_hint=f"{platform} ok",
        )

    handler = MockStudioHandler(
        trips,
        json_body={
            "tripId": "demo",
            "platforms": [
                {"platform": "xiaohongshu"},
                {"platform": "wechat_official"},
                {"platform": "album_spread"},
            ],
            "allowMissingSource": True,
        },
    )

    with (
        patch(
            "travelogue.web.studio_handlers.export_handlers._ensure_derivatives_for_export",
        ),
        patch(
            "travelogue.export.longshot.playwright_longshot_available",
            return_value=False,
        ),
        patch(
            "travelogue.export.longshot_batch.export_trip_longshot",
            side_effect=fake_export,
        ),
    ):
        handle_longshot(handler)
        status, body = handler.response
        assert status == 202, body
        job = wait_for_job(lambda: _fetch(body["jobId"]), timeout_sec=5)
        assert job["status"] == "succeeded"
        assert job["result"]["succeededCount"] == 3


def test_handle_longshot_batch_still_rejects_playwright_platforms_without_browser(
    tmp_path: Path,
) -> None:
    """含 wechat_moments 的批量在缺 Playwright 时仍应整体拒绝（v1 已知简化）。"""
    trips = tmp_path / "trips"
    create_trip("demo", trips, title="demo")
    handler = MockStudioHandler(
        trips,
        json_body={
            "tripId": "demo",
            "platforms": [
                {"platform": "xiaohongshu"},
                {"platform": "wechat_moments"},
            ],
            "allowMissingSource": True,
        },
    )
    with patch(
        "travelogue.export.longshot.playwright_longshot_available",
        return_value=False,
    ):
        handle_longshot(handler)
        status, body = handler.response
        assert status == 400
        assert body["error"] == "E_LNG2_BATCH_CLIENT_FALLBACK_UNSUPPORTED"
        assert "wechat_moments" in body["message"]
        assert "xiaohongshu" not in body["message"]
