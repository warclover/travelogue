"""AC-TPC-07 · poster_bric Writer（单屏海报，非九宫格）."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from travelogue.config.studio import GcsPosterBricConfig
from travelogue.export.bric_compose import bric_compose
from travelogue.export.longshot import LongshotExportError, export_trip_longshot
from travelogue.export.output_recipe.resolve import ambiguous_intent_options, resolve_output_recipe
from travelogue.export.poster_bric_pack import (
    compose_poster_png,
    export_poster_bric_pack,
    list_poster_photo_paths,
)
from travelogue.services.trip_factory import create_trip

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[3]
STUDIO = ROOT / "templates" / "studio"


def _make_rgb(path: Path, *, size: tuple[int, int] = (800, 600), color=(40, 120, 200)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, format="JPEG", quality=90)


def _seed_kept_photos(
    trip_dir: Path,
    n: int,
    *,
    collage_ids: frozenset[str] | None = None,
    chapters: list[dict] | None = None,
) -> list[str]:
    trip_json = trip_dir / "trip.json"
    data = json.loads(trip_json.read_text(encoding="utf-8"))
    assets = []
    ids: list[str] = []
    collage_ids = collage_ids or frozenset()
    for i in range(n):
        aid = f"poster-{i:02d}"
        ids.append(aid)
        rel = f"source/{aid}.jpg"
        size = (900, 600) if i % 2 == 0 else (600, 900)
        _make_rgb(trip_dir / rel, size=size, color=(30 + i * 10, 80, 160))
        entry = {
            "id": aid,
            "type": "image",
            "sourceFile": rel,
            "layoutEligible": True,
        }
        if aid in collage_ids:
            entry["mediaClass"] = "collage"
        assets.append(entry)
    data["assets"] = assets
    curation = data.setdefault("curation", {})
    curation["displayedAssetIds"] = ids
    cull = curation.setdefault("cullSummary", {})
    cull["layoutEligibleCount"] = n
    cull["finalLayoutEligibleCount"] = n
    if chapters is not None:
        data["chapters"] = chapters
    trip_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return ids


def _cfg_on():
    from dataclasses import replace

    from travelogue.config import get_config

    base = get_config()
    return replace(
        base,
        studio=replace(
            base.studio,
            gcs_poster_bric=GcsPosterBricConfig(enabled=True),
        ),
    )


def test_bric_compose_no_overlap_gutter() -> None:
    sizes = [(900.0, 600.0), (600.0, 900.0), (800.0, 800.0), (1200.0, 700.0)]
    fitted, positions, canvas = bric_compose(sizes, width=1080, border=16, spacing=8)
    assert len(fitted) == 4
    assert canvas[0] == 1080.0
    # Axis-aligned boxes must not overlap
    boxes = []
    for (w, h), (x, y) in zip(fitted, positions, strict=True):
        boxes.append((x, y, x + w, y + h))
    for i, a in enumerate(boxes):
        for j, b in enumerate(boxes):
            if i >= j:
                continue
            ax0, ay0, ax1, ay1 = a
            bx0, by0, bx1, by1 = b
            overlap_x = min(ax1, bx1) - max(ax0, bx0)
            overlap_y = min(ay1, by1) - max(ay0, by0)
            assert overlap_x <= 0 or overlap_y <= 0


def test_ac_tpc_07_export_n4_no_screens_mutation(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    create_trip("poster-4", trips, title="单屏海报四张")
    trip_dir = trips / "poster-4"
    chapters = [
        {
            "id": "ch1",
            "screens": [
                {"id": "s1", "patternId": "legacy-fixture", "assetIds": ["poster-00"]},
            ],
        }
    ]
    _seed_kept_photos(trip_dir, 4, chapters=chapters)
    before = json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
    screens_before = json.dumps(before["chapters"][0]["screens"], sort_keys=True)

    result = export_poster_bric_pack(trip_dir, cfg=_cfg_on())
    assert result.platform == "poster_bric"
    assert result.page_count == 1
    assert result.capture_method == "poster_bric"
    assert "九宫格" not in (result.user_hint or "")
    assert "九宫格" not in (result.publish_guide or "")
    assert result.profile_label == "单张海报"

    finals = list(trip_dir.glob("*-poster.png"))
    assert len(finals) == 1
    with Image.open(finals[0]) as im:
        assert im.size == (1080, 1440)

    after = json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
    screens_after = json.dumps(after["chapters"][0]["screens"], sort_keys=True)
    assert screens_before == screens_after
    assert (trip_dir / "runs" / "gcs-poster-bric.json").is_file()


def test_poster_bric_ignores_jpeg_fmt(tmp_path: Path) -> None:
    """BE-DFX-21 · poster always PNG even when job asks for jpeg."""
    trips = tmp_path / "trips"
    create_trip("poster-jpeg", trips, title="海报强制PNG")
    trip_dir = trips / "poster-jpeg"
    _seed_kept_photos(trip_dir, 4)
    result = export_poster_bric_pack(trip_dir, cfg=_cfg_on(), fmt="jpeg")
    assert result.output_format == "png"
    assert list(trip_dir.glob("*-poster.jpg")) == []
    finals = list(trip_dir.glob("*-poster.png"))
    assert len(finals) == 1
    assert finals[0].read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_ac_tpc_07_reject_zero_photos(tmp_path: Path) -> None:
    """PRD-EXPORT-CARD-COMPOSE-V1 §5.2 · card-1-full-frame 让 1 张精选照片
    也是合法海报，新地板是 0（无照片）才拒绝，不再是旧的 MIN_N=3。"""
    trips = tmp_path / "trips"
    create_trip("poster-0", trips, title="零张拒")
    trip_dir = trips / "poster-0"
    _seed_kept_photos(trip_dir, 0)
    with pytest.raises(LongshotExportError) as ei:
        export_poster_bric_pack(trip_dir, cfg=_cfg_on())
    assert getattr(ei.value, "code", None) == "E_GCS_POSTER_N"


def test_ac_tpc_07_single_photo_uses_full_frame(tmp_path: Path) -> None:
    """新地板：仅 1–2 张精选照片时改用 card-1-full-frame 单图满版，不再拒绝。"""
    trips = tmp_path / "trips"
    create_trip("poster-2", trips, title="两张不拒")
    trip_dir = trips / "poster-2"
    _seed_kept_photos(trip_dir, 2)
    result = export_poster_bric_pack(trip_dir, cfg=_cfg_on())
    assert result.platform == "poster_bric"
    assert result.page_count == 1
    finals = list(trip_dir.glob("*-poster.png"))
    assert len(finals) == 1
    with Image.open(finals[0]) as im:
        assert im.size == (1080, 1440)


def test_ac_tpc_07_exclude_collage(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    create_trip("poster-collage", trips, title="拼贴排除")
    trip_dir = trips / "poster-collage"
    ids = _seed_kept_photos(trip_dir, 4, collage_ids=frozenset({"poster-01"}))
    paths = list_poster_photo_paths(trip_dir)
    assert len(paths) == 3
    assert all("poster-01" not in str(p) for p in paths)
    assert len(ids) == 4


def test_ac_tpc_07_flag_default_off(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    create_trip("poster-off", trips, title="默认关")
    trip_dir = trips / "poster-off"
    _seed_kept_photos(trip_dir, 4)
    # 隔离本机 dogfood config.yaml（可能已打开 gcs_poster_bric）
    with patch(
        "travelogue.export.poster_bric_pack.gcs_poster_bric_enabled",
        return_value=False,
    ):
        with pytest.raises(LongshotExportError) as ei:
            export_poster_bric_pack(trip_dir)
    assert getattr(ei.value, "code", None) == "E_GCS_POSTER_DISABLED"


def test_ac_tpc_07_route_via_export_trip_longshot(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    create_trip("poster-route", trips, title="路由")
    trip_dir = trips / "poster-route"
    _seed_kept_photos(trip_dir, 5)

    with patch("travelogue.export.platform_longshot.export_platform_longshot") as mock_b:
        with patch(
            "travelogue.export.poster_bric_pack.gcs_poster_bric_enabled",
            return_value=True,
        ):
            result = export_trip_longshot(trip_dir, platform="poster_bric")
    mock_b.assert_not_called()
    assert result.platform == "poster_bric"
    assert result.page_count == 1


def test_ac_tpc_07_recipe_no_jiugongge_wording() -> None:
    recipe = resolve_output_recipe(kept_n=6, enabled=True, intent="poster_bric")
    assert recipe.engine == "poster_bric"
    assert recipe.platform == "poster_bric"
    assert "九宫格" not in recipe.product_label
    assert "九宫格" not in recipe.cta_label
    # Ambiguous Phase B card must not include poster_bric
    opts = ambiguous_intent_options(phase="B", kept_n=12)
    assert "poster_bric" not in {o["intent"] for o in opts}


def test_compose_poster_png_bytes(tmp_path: Path) -> None:
    paths = []
    for i in range(3):
        p = tmp_path / f"p{i}.jpg"
        _make_rgb(p, size=(800, 600) if i % 2 == 0 else (500, 900))
        paths.append(p)
    data, diag = compose_poster_png(paths)
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert diag["exportSurface"] == "poster_bric"
    # pool_size=3 < 4 → falls back to the single full-frame template (§5.2).
    assert diag["template"] == "card-1-full-frame"
    assert diag["n"] == 1
    assert diag["canvas"] == [1080, 1440]
    with Image.open(__import__("io").BytesIO(data)) as im:
        assert im.size == (1080, 1440)


def test_compose_poster_png_empty_raises() -> None:
    with pytest.raises(LongshotExportError) as ei:
        compose_poster_png([])
    assert getattr(ei.value, "code", None) == "E_GCS_POSTER_N"


def test_ui_copy_no_jiugongge_for_poster() -> None:
    panel = (STUDIO / "js" / "longshot-export-panel.js").read_text(encoding="utf-8")
    assert 'id: "poster_bric"' in panel
    assert "3:4" in panel
    assert "A4" not in panel  # PRD-EXPORT-CARD-COMPOSE-V1 · poster_bric 已改 3:4
    assert "九宫格" not in panel.split("poster_bric:")[1].split("xiaohongshu:")[0]
    assert 'id: "moments_grid"' not in panel
