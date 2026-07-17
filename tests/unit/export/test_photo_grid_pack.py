"""AC-OR-09 / 09b / 11b · photo_grid_pack（真九宫格 Writer）."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from travelogue.export.longshot import LongshotExportError, export_trip_longshot
from travelogue.export.output_recipe.resolve import ambiguous_intent_options, resolve_output_recipe
from travelogue.export.photo_grid_pack import (
    compose_1x1_contain,
    export_photo_grid_pack,
    list_kept_photo_paths,
)
from travelogue.services.trip_factory import create_trip

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[3]
STUDIO = ROOT / "templates" / "studio"


def _make_rgb(path: Path, *, size: tuple[int, int] = (800, 600), color=(40, 120, 200)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, format="JPEG", quality=90)


def _seed_kept_photos(trip_dir: Path, n: int) -> list[str]:
    """Write n kept images + trip.json assets / displayedAssetIds."""
    trip_json = trip_dir / "trip.json"
    data = json.loads(trip_json.read_text(encoding="utf-8"))
    assets = []
    ids: list[str] = []
    for i in range(n):
        aid = f"grid-{i:02d}"
        ids.append(aid)
        rel = f"source/{aid}.jpg"
        # alternate landscape / portrait
        size = (900, 600) if i % 2 == 0 else (600, 900)
        _make_rgb(trip_dir / rel, size=size, color=(30 + i * 10, 80, 160))
        assets.append(
            {
                "id": aid,
                "type": "image",
                "sourceFile": rel,
                "layoutEligible": True,
            }
        )
    data["assets"] = assets
    curation = data.setdefault("curation", {})
    curation["displayedAssetIds"] = ids
    cull = curation.setdefault("cullSummary", {})
    cull["layoutEligibleCount"] = n
    cull["finalLayoutEligibleCount"] = n
    trip_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return ids


def test_ac_or_09_kept_n6_no_padding(tmp_path: Path) -> None:
    """kept_n=6 → 恰好 6 张产物，无空白灌水."""
    trips = tmp_path / "trips"
    create_trip("grid-6", trips, title="九宫格六张")
    trip_dir = trips / "grid-6"
    _seed_kept_photos(trip_dir, 6)

    paths = list_kept_photo_paths(trip_dir)
    assert len(paths) == 6

    result = export_photo_grid_pack(trip_dir)
    assert result.platform == "moments_grid"
    assert result.page_count == 6
    assert len(result.outputs) == 6
    assert result.capture_method == "photo_grid"
    assert "九宫格" in (result.publish_guide or "")
    # 无灌水文件
    finals = list(trip_dir.glob("*-moments-grid-*.png"))
    assert len(finals) == 6
    assert not list(trip_dir.glob("*.part"))
    # 1:1 像素
    for out in result.outputs:
        with Image.open(out.path) as im:
            assert im.size[0] == im.size[1]


def test_ac_or_09b_filename_and_rollback(tmp_path: Path) -> None:
    """文件名 *-moments-grid-*；异常后无 .part 残留."""
    trips = tmp_path / "trips"
    create_trip("grid-rb", trips, title="回滚测")
    trip_dir = trips / "grid-rb"
    _seed_kept_photos(trip_dir, 3)

    result = export_photo_grid_pack(trip_dir)
    for item in result.outputs:
        assert "-moments-grid-" in item.path.name
        assert item.path.suffix == ".png"

    # 模拟中途失败 → rollback 清 .part
    with patch(
        "travelogue.export.photo_grid_pack.compose_1x1_contain",
        side_effect=[b"\x89PNG\r\n\x1a\n" + b"x" * 64, RuntimeError("boom")],
    ):
        with pytest.raises(LongshotExportError) as ei:
            export_photo_grid_pack(trip_dir)
    assert getattr(ei.value, "code", None) == "E_OR_GRID_FAILED"
    assert not list(trip_dir.glob("*.part"))


def test_ac_or_09_route_via_export_trip_longshot(tmp_path: Path) -> None:
    """分支 D：moments_grid 不得落入 platform_longshot."""
    trips = tmp_path / "trips"
    create_trip("grid-route", trips, title="路由")
    trip_dir = trips / "grid-route"
    _seed_kept_photos(trip_dir, 4)

    with patch("travelogue.export.platform_longshot.export_platform_longshot") as mock_b:
        result = export_trip_longshot(trip_dir, platform="moments_grid")
    mock_b.assert_not_called()
    assert result.platform == "moments_grid"
    assert result.page_count == 4
    assert result.capture_method == "photo_grid"


def test_compose_1x1_contain_square() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "wide.jpg"
        _make_rgb(p, size=(1200, 400))
        data = compose_1x1_contain(p, size=540)
        with Image.open(__import__("io").BytesIO(data)) as im:
            assert im.size == (540, 540)


def test_ac_or_11b_ui_grid_bound_only_to_moments_grid() -> None:
    """「九宫格」可点映射仅 moments_grid；scroll 仍无九宫格可点映射."""
    opts_b = ambiguous_intent_options(phase="B", kept_n=12)
    intents = [o["intent"] for o in opts_b]
    assert intents == ["chat_longshot", "moments_grid", "moments_scroll"]
    grid_opt = next(o for o in opts_b if o["intent"] == "moments_grid")
    assert "九宫格" in grid_opt["label"]
    scroll_opt = next(o for o in opts_b if o["intent"] == "moments_scroll")
    assert "九宫格" not in scroll_opt["label"]

    # Phase A 卡仍无九宫格（回归）
    opts_a = ambiguous_intent_options(phase="A")
    assert {o["intent"] for o in opts_a} == {"chat_longshot", "moments_scroll"}

    grid = resolve_output_recipe(kept_n=12, enabled=True, intent="moments_grid")
    assert grid.platform == "moments_grid"
    assert grid.engine == "photo_grid"

    scroll = resolve_output_recipe(kept_n=12, enabled=True, intent="moments_scroll")
    assert scroll.platform == "wechat_moments"
    assert "九宫格" not in scroll.product_label
    assert "九宫格" not in scroll.cta_label

    recipe_js = (STUDIO / "js" / "output-recipe.js").read_text(encoding="utf-8")
    recipe_logic = (STUDIO / "js" / "output-recipe-logic.js").read_text(encoding="utf-8")
    assert 'intent: "moments_grid"' in recipe_js
    assert "朋友圈 · 九宫格" in recipe_js
    assert "即将推出" not in recipe_js
    assert (
        'moments_grid: "moments_grid"' in recipe_js
        or "moments_grid: 'moments_grid'" in recipe_js
        or 'moments_grid: "moments_grid"' in recipe_logic
    )

    client = (STUDIO / "js" / "longshot-client.js").read_text(encoding="utf-8")
    assert 'platform === "moments_grid"' in client
    assert "九宫格已就绪" in client
    # scroll 成功态仍诚实声明不是九宫格
    assert "这不是九宫格" in client

    panel = (STUDIO / "js" / "longshot-export-panel.js").read_text(encoding="utf-8")
    assert 'id: "moments_grid"' in panel
    assert 'data-studio-longshot-platform="' in panel
    # 导出设置 · 方案 A：2×2 平台卡（禁止 4 项单行 pill）
    assert "preview-toolbar__export-platform-grid" in panel
    assert "preview-toolbar__export-platform-card" in panel
    assert 'title: "朋友圈"' in panel
    assert 'subtitle: "长图连读"' in panel
    assert 'subtitle: "九宫格 1:1"' in panel
    # wechat_moments CTA 不得冒充九宫格
    assert 'cta: "导出朋友圈 · 长图连读"' in panel
    assert 'cta: "导出朋友圈 · 九宫格"' in panel
