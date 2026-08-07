"""EOI · AC-EOI-02 端到端目录内容断言（PRD-EXPORT-OUTPUT-ISOLATION-V1.md）。

七席评审回写 BLK-EOI-04：不能只测"文件写到了某路径"这种单元级断言，需要一条可执行
断言校验"「导出文件」子目录文件列表 = 产物 ∪ {longshot-current.json}，且不含任意
.js/.css/.html/trip.json"——这正是用户原始反馈（打开导出文件夹混着工程文件）的
根因所在，也是本 PRD 的核心验收点。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.unit.export.test_photo_grid_pack import _seed_kept_photos
from travelogue.export.collage_pack import export_collage_pack
from travelogue.export.longshot import (
    EXPORT_OUTPUT_DIRNAME,
    LONGSHOT_CURRENT_NAME,
    write_longshot_current,
)
from travelogue.export.photo_grid_pack import export_photo_grid_pack
from travelogue.services.trip_factory import create_trip

pytestmark = pytest.mark.unit

# 打开导出文件夹本不该看到的工程文件后缀 / 文件名（用户原始反馈的根因）。
_FORBIDDEN_SUFFIXES = (".js", ".css", ".html", ".htm")
_FORBIDDEN_NAMES = {"trip.json", "index.html", "index-longshot.html", "index-mobile.html"}


def test_export_output_dir_contains_only_products_and_manifest(tmp_path: Path) -> None:
    """AC-EOI-02 · 多种导出类型混合后，「导出文件」子目录只有产物 + 权威清单。"""
    trips = tmp_path / "trips"
    create_trip("eoi-e2e", trips, title="端到端隔离验收")
    trip_dir = trips / "eoi-e2e"
    _seed_kept_photos(trip_dir, 6)

    grid_result = export_photo_grid_pack(trip_dir)
    collage_result = export_collage_pack(trip_dir, platform="xiaohongshu")
    write_longshot_current(
        trip_dir,
        batch_id="e2e",
        kind="whole",
        files=[grid_result.outputs[0].path.name],
    )

    export_dir = trip_dir / EXPORT_OUTPUT_DIRNAME
    assert export_dir.is_dir()

    on_disk = {p.name for p in export_dir.iterdir() if p.is_file()}
    expected_products = {p.path.name for p in grid_result.outputs} | {
        p.path.name for p in collage_result.outputs
    }

    # 核心断言：子目录文件列表 == 产物 ∪ {权威清单}，一个不多一个不少。
    assert on_disk == expected_products | {LONGSHOT_CURRENT_NAME}

    for name in on_disk:
        assert name not in _FORBIDDEN_NAMES, f"子目录里混入了工程文件：{name}"
        assert not name.lower().endswith(_FORBIDDEN_SUFFIXES), f"子目录里混入了工程文件：{name}"

    # trip 根目录本身不应因这轮导出新增任何图片产物（D-EOI-05 · 老产物原地不动，
    # 新导出只进子目录——这里断言的是「不再新增」，不是「根目录空」）。
    root_image_files = {
        p.name
        for p in trip_dir.iterdir()
        if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg")
    }
    assert not root_image_files


def test_export_output_dir_survives_legacy_root_files(tmp_path: Path) -> None:
    """AC-EOI-05 · 老游记根目录已有旧产物时，新导出不报错、不迁移、不删除旧产物。"""
    trips = tmp_path / "trips"
    create_trip("eoi-legacy", trips, title="老游记回归")
    trip_dir = trips / "eoi-legacy"
    _seed_kept_photos(trip_dir, 4)

    legacy_png = trip_dir / "老游记回归-album-01.png"
    legacy_png.write_bytes(b"legacy-product-from-before-this-change")
    legacy_mtime = legacy_png.stat().st_mtime

    result = export_photo_grid_pack(trip_dir)
    assert result.outputs

    # 旧产物原地保留，字节和 mtime 都不变（D-EOI-05 · 不处理）。
    assert legacy_png.is_file()
    assert legacy_png.stat().st_mtime == legacy_mtime
    assert legacy_png.read_bytes() == b"legacy-product-from-before-this-change"

    # 新导出只进子目录，不会跑去跟旧产物挤在根目录。
    export_dir = trip_dir / EXPORT_OUTPUT_DIRNAME
    for out in result.outputs:
        assert out.path.parent == export_dir
