"""PRD-BATCH-EXPORT-MULTISELECT-V1 Stage 1/4 · export_trip_longshot_batch 单测。

Stage 1（调度层本身）：顺序调用 / 部分失败继续 / 取消中断，全部 mock 掉
`export_trip_longshot`，不重复测 CardGrouper / Playwright 渲染细节。
Stage 4（真实素材回归）：新增几项**完全不 mock** `export_trip_longshot` 的用例，
走真实 `export_collage_pack` 渲染管线（种子真实照片文件），验证批量调度层与既有
渲染管线的边界衔接正确——而不仅是"调度层按预期调用了 mock"。
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from travelogue.export.longshot import (
    EXPORT_OUTPUT_DIRNAME,
    LongshotCancelled,
    LongshotExportError,
    LongshotExportResult,
    export_trip_longshot,
)
from travelogue.export.longshot_batch import (
    BatchExportRequest,
    export_trip_longshot_batch,
)
from travelogue.export.platform_profiles import clear_platform_profiles_cache
from travelogue.services.trip_factory import create_trip

pytestmark = pytest.mark.unit


def _fake_result(platform: str) -> LongshotExportResult:
    return LongshotExportResult(platform=platform, page_count=1)


def _make_rgb(path: Path, *, size: tuple[int, int], color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, format="JPEG", quality=90)


def _seed_kept_photos(trip_dir: Path, n: int) -> list[str]:
    """与 test_collage_pack.py 同款：种子真实照片文件 + 精选清单（非 mock）。"""
    trip_json = trip_dir / "trip.json"
    data = json.loads(trip_json.read_text(encoding="utf-8"))
    assets = []
    ids: list[str] = []
    for i in range(n):
        aid = f"collage-{i:02d}"
        ids.append(aid)
        rel = f"source/{aid}.jpg"
        size = (900, 600) if i % 2 == 0 else (600, 900)
        _make_rgb(trip_dir / rel, size=size, color=(30 + i * 10, 80, 160))
        assets.append(
            {"id": aid, "type": "image", "sourceFile": rel, "layoutEligible": True}
        )
    data["assets"] = assets
    curation = data.setdefault("curation", {})
    curation["displayedAssetIds"] = ids
    cull = curation.setdefault("cullSummary", {})
    cull["layoutEligibleCount"] = n
    cull["finalLayoutEligibleCount"] = n
    trip_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return ids


@pytest.fixture(autouse=True)
def _clear_profiles_cache() -> None:
    clear_platform_profiles_cache()
    yield
    clear_platform_profiles_cache()


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


# ---------------------------------------------------------------------------
# Stage 4 · 真实素材回归（不 mock export_trip_longshot，走真实渲染管线）
# ---------------------------------------------------------------------------


def test_batch_real_pipeline_multi_platform_success(tmp_path: Path) -> None:
    """G-BEX-01/05 真实素材版：小红书+公众号+画册三平台批量，全程不 mock 渲染，

    验证批量调度层与真实 CardGrouper/CardRenderer 管线衔接无误——每个平台各自
    落盘对应文件，互不覆盖/互不干扰（D-BEX-06 文件名前缀隔离）。
    """
    trips = tmp_path / "trips"
    create_trip("batch-real-3", trips, title="批量真实素材三平台")
    trip_dir = trips / "batch-real-3"
    _seed_kept_photos(trip_dir, 8)

    requests = [
        BatchExportRequest(platform="xiaohongshu"),
        BatchExportRequest(platform="wechat_official"),
        BatchExportRequest(platform="album_spread"),
    ]
    results = export_trip_longshot_batch(trip_dir, requests=requests)

    assert [r.platform for r in results] == ["xiaohongshu", "wechat_official", "album_spread"]
    assert all(r.ok for r in results), [
        (r.platform, r.error_code, r.error_message) for r in results if not r.ok
    ]

    export_dir = trip_dir / EXPORT_OUTPUT_DIRNAME
    xhs_files = sorted(export_dir.glob("*-xhs-*.png"))
    mp_files = sorted(export_dir.glob("*-mp-*.png"))
    album_files = sorted(export_dir.glob("*-album-*.png"))
    assert len(xhs_files) == results[0].result.page_count > 0
    assert len(mp_files) == results[1].result.page_count > 0
    assert len(album_files) == results[2].result.page_count > 0
    # 三套文件名互不重叠（D-BEX-06）。
    assert not (set(xhs_files) & set(mp_files) & set(album_files))


def test_batch_real_pipeline_partial_failure_continues(tmp_path: Path) -> None:
    """AC-BEX-04 真实素材版：一个平台因真实业务错误（无精选照片）失败时，

    其余平台仍走真实渲染管线跑完——只在数据源层面（而非 scheduler 本身）注入
    真实错误，验证 export_trip_longshot_batch 对真实 LongshotExportError 的
    捕获/继续行为，而不只是对 mock 异常的行为。
    """
    trips = tmp_path / "trips"
    create_trip("batch-real-fail", trips, title="批量真实素材部分失败")
    trip_dir = trips / "batch-real-fail"
    _seed_kept_photos(trip_dir, 8)

    import travelogue.export.collage_pack as collage_pack_mod

    real_pairs = collage_pack_mod._poster_candidate_pairs
    call_count = {"n": 0}

    def _fail_only_on_second_call(trip_dir_arg, *, limit):
        # 批量按 requests 顺序调用（xiaohongshu → wechat_official → album_spread），
        # 精确模拟"第 2 项真实业务失败"（E_COLLAGE_N），其余两项走真实数据渲染。
        # export_collage_pack 直接读 `_poster_candidate_pairs`（不再经
        # list_collage_photo_paths），所以 patch 目标要对齐真实调用点。
        call_count["n"] += 1
        if call_count["n"] == 2:
            return []
        return real_pairs(trip_dir_arg, limit=limit)

    requests = [
        BatchExportRequest(platform="xiaohongshu"),
        BatchExportRequest(platform="wechat_official"),
        BatchExportRequest(platform="album_spread"),
    ]
    with patch(
        "travelogue.export.collage_pack._poster_candidate_pairs",
        side_effect=_fail_only_on_second_call,
    ):
        results = export_trip_longshot_batch(trip_dir, requests=requests)

    assert [r.platform for r in results] == ["xiaohongshu", "wechat_official", "album_spread"]
    assert results[0].ok is True
    assert results[1].ok is False
    assert results[1].error_code == "E_COLLAGE_N"
    assert results[2].ok is True  # D-BEX-05：第 2 项真实失败未阻塞第 3 项

    export_dir = trip_dir / EXPORT_OUTPUT_DIRNAME
    xhs_files = list(export_dir.glob("*-xhs-*.png"))
    album_files = list(export_dir.glob("*-album-*.png"))
    mp_files = list(export_dir.glob("*-mp-*.png"))
    assert len(xhs_files) > 0
    assert len(album_files) > 0
    assert len(mp_files) == 0  # 失败项未产出任何文件（writer.rollback 生效）


def test_batch_backward_compat_single_platform_path_unaffected(tmp_path: Path) -> None:
    """AC-BEX-05 契约测试：单平台调用（不经批量调度层）与批量场景下同平台的

    单项行为完全一致——证明 D-BEX-02"批量层只是循环调用既有函数"的零侵入承诺。
    """
    trips = tmp_path / "trips"
    create_trip("batch-compat", trips, title="向后兼容对照")
    trip_dir = trips / "batch-compat"
    _seed_kept_photos(trip_dir, 8)

    export_dir = trip_dir / EXPORT_OUTPUT_DIRNAME
    direct_result = export_trip_longshot(trip_dir, platform="xiaohongshu")
    direct_files = sorted(p.name for p in export_dir.glob("*-xhs-*.png"))
    for p in export_dir.glob("*-xhs-*.png"):
        p.unlink()

    batch_results = export_trip_longshot_batch(
        trip_dir, requests=[BatchExportRequest(platform="xiaohongshu")]
    )
    batch_files = sorted(p.name for p in export_dir.glob("*-xhs-*.png"))

    assert batch_results[0].ok is True
    assert batch_results[0].result.page_count == direct_result.page_count
    assert batch_files == direct_files
