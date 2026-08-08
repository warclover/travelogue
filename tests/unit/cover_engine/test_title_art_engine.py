"""Unit tests · title_art engine orchestrator (PRD §5/§6/§8 · D-CAL-16)."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from PIL import Image

from travelogue.cover_engine.title_art import engine as engine_mod
from travelogue.cover_engine.title_art.engine import mark_title_art_stale, resolve_title_art
from travelogue.cover_engine.title_art.route_c import RouteCFailure
from travelogue.cover_engine.title_art.whitelist import FALLBACK_PRESETS, placement_preset

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _force_glyph_coverage(monkeypatch):
    """字形覆盖检查依赖真实系统字体；测试环境不保证可用，直接锁定为已覆盖，
    该逻辑本身已在 test_title_art_fonts.py 独立验证。"""
    monkeypatch.setattr(engine_mod, "glyphs_covered", lambda *_a, **_k: True)


def _no_asset_path(_asset):
    return None


def _write_png_recorder():
    written: list[bytes] = []

    def _write(data: bytes) -> str:
        written.append(data)
        return f"trip-derived/title-art/fake-{len(written)}.png"

    return _write, written


def test_non_whitelisted_style_is_fail_open() -> None:
    trip = {"meta": {"title": "拾光", "coverOpeningStyle": "type-monument"}}
    write_png, written = _write_png_recorder()
    result = resolve_title_art(
        trip, resolve_asset_path=_no_asset_path, write_png=write_png
    )
    assert result is None
    assert trip["meta"]["titleArt"]["enabled"] is False
    assert written == []


def test_empty_title_is_fail_open() -> None:
    trip = {"meta": {"title": "  ", "coverOpeningStyle": "veil-footer"}}
    write_png, _ = _write_png_recorder()
    result = resolve_title_art(trip, resolve_asset_path=_no_asset_path, write_png=write_png)
    assert result is None
    assert trip["meta"]["titleArt"]["enabled"] is False


def test_glyph_not_covered_is_fail_open(monkeypatch) -> None:
    monkeypatch.setattr(engine_mod, "glyphs_covered", lambda *_a, **_k: False)
    trip = {"meta": {"title": "拾光", "coverOpeningStyle": "veil-footer"}}
    write_png, _ = _write_png_recorder()
    result = resolve_title_art(trip, resolve_asset_path=_no_asset_path, write_png=write_png)
    assert result is None
    assert trip["meta"]["titleArt"]["enabled"] is False


def test_route_b_happy_path_writes_meta_and_png() -> None:
    trip = {"meta": {"title": "拾光", "coverOpeningStyle": "veil-footer"}}
    write_png, written = _write_png_recorder()
    result = resolve_title_art(trip, resolve_asset_path=_no_asset_path, write_png=write_png)
    assert result is not None
    assert result.engine == "clean-pipeline-v1"
    assert result.enabled is True
    assert result.fallback_from is None
    assert len(written) == 1
    meta_dict = trip["meta"]["titleArt"]
    assert meta_dict["enabled"] is True
    assert meta_dict["engine"] == "clean-pipeline-v1"
    assert meta_dict["assetPath"] == result.asset_path
    assert "fallbackFrom" not in meta_dict


def test_existing_non_stale_result_skips_recompute_without_force() -> None:
    trip = {
        "meta": {
            "title": "拾光",
            "coverOpeningStyle": "veil-footer",
            "titleArt": {"version": 1, "enabled": True, "stale": False, "assetPath": "x.png"},
        }
    }
    write_png, written = _write_png_recorder()
    result = resolve_title_art(trip, resolve_asset_path=_no_asset_path, write_png=write_png)
    assert result is None
    assert written == []
    assert trip["meta"]["titleArt"]["assetPath"] == "x.png"  # 未被覆盖


def test_stale_result_recomputes_even_without_force() -> None:
    trip = {
        "meta": {
            "title": "拾光",
            "coverOpeningStyle": "veil-footer",
            "titleArt": {"version": 1, "enabled": True, "stale": True, "assetPath": "old.png"},
        }
    }
    write_png, written = _write_png_recorder()
    result = resolve_title_art(trip, resolve_asset_path=_no_asset_path, write_png=write_png)
    assert result is not None
    assert len(written) == 1
    assert trip["meta"]["titleArt"]["assetPath"] != "old.png"


def test_force_recomputes_even_when_not_stale() -> None:
    trip = {
        "meta": {
            "title": "拾光",
            "coverOpeningStyle": "veil-footer",
            "titleArt": {"version": 1, "enabled": True, "stale": False, "assetPath": "old.png"},
        }
    }
    write_png, written = _write_png_recorder()
    result = resolve_title_art(
        trip, resolve_asset_path=_no_asset_path, write_png=write_png, force=True
    )
    assert result is not None
    assert len(written) == 1


def test_mark_title_art_stale_flips_flag() -> None:
    trip = {"meta": {"titleArt": {"enabled": True, "stale": False}}}
    mark_title_art_stale(trip)
    assert trip["meta"]["titleArt"]["stale"] is True


def test_mark_title_art_stale_noop_when_no_title_art() -> None:
    trip = {"meta": {}}
    mark_title_art_stale(trip)  # 不应抛异常
    assert "titleArt" not in trip["meta"]


@dataclass(frozen=True)
class _FakeStyle:
    style_id: str = "cascade-seal"


@dataclass(frozen=True)
class _FakeRawResult:
    image: Image.Image
    style: _FakeStyle = _FakeStyle()
    model: str = "wanx2.1-t2i-plus"
    actual_prompt: str = "毛笔字·拾光"


def test_route_c_success_path_marks_engine_and_ocr_verified() -> None:
    trip = {"meta": {"title": "拾光", "coverOpeningStyle": "veil-footer"}}
    write_png, written = _write_png_recorder()

    def _fake_generate_raw(style_id, *, title, subtitle=None, **_kw):
        return _FakeRawResult(image=Image.new("RGB", (32, 32), (255, 255, 255)))

    def _fake_ocr_verify(_img, _expected, **_kw):
        return True

    result = resolve_title_art(
        trip,
        resolve_asset_path=_no_asset_path,
        write_png=write_png,
        route_c_enabled=True,
        generate_raw=_fake_generate_raw,
        ocr_verify=_fake_ocr_verify,
    )
    assert result is not None
    assert result.engine == "diffusion-fixed-prompt-v1"
    assert result.ocr_verified is True
    assert result.fallback_from is None
    assert len(written) == 1
    assert trip["meta"]["titleArt"]["engine"] == "diffusion-fixed-prompt-v1"
    assert trip["meta"]["titleArt"]["ocrVerified"] is True


def test_route_c_generation_failure_falls_back_to_route_b() -> None:
    trip = {"meta": {"title": "拾光", "coverOpeningStyle": "veil-footer"}}
    write_png, written = _write_png_recorder()

    def _fake_generate_raw(*_a, **_kw):
        raise RouteCFailure("E_CAL_C_TIMEOUT")

    result = resolve_title_art(
        trip,
        resolve_asset_path=_no_asset_path,
        write_png=write_png,
        route_c_enabled=True,
        generate_raw=_fake_generate_raw,
    )
    assert result is not None
    assert result.engine == "clean-pipeline-v1"
    assert result.fallback_from == "diffusion-fixed-prompt-v1"
    assert len(written) == 1  # 只落一次盘（路线 B 的产物），不留半成品文件
    assert trip["meta"]["titleArt"]["fallbackFrom"] == "diffusion-fixed-prompt-v1"


def test_contact_stamp_dark_veil_forces_white_ink_despite_bright_photo(tmp_path) -> None:
    # 2026-08-07 真实视觉核对：contact-stamp 全幅深色渐罩会把「原始照片很亮」
    # 误判成「背景够亮，选深墨」，实际渲染深墨读不出来。用一张纯白照片模拟
    # 「原始 ROI 很亮」，断言 assume_dark_veil 生效后必然选回白色墨迹。
    photo_path = tmp_path / "bright.png"
    Image.new("RGB", (800, 600), (245, 245, 245)).save(photo_path)
    trip = {
        "meta": {"title": "拾光", "coverOpeningStyle": "contact-stamp"},
        "coverAssetId": "asset-1",
        "assets": [{"id": "asset-1"}],
    }
    write_png, written = _write_png_recorder()

    def _resolve_asset_path(_asset):
        return photo_path

    result = resolve_title_art(
        trip, resolve_asset_path=_resolve_asset_path, write_png=write_png
    )
    assert result is not None
    assert len(written) == 1
    assert result.main_color == "#ffffff"
    assert any("固定深色渐罩" in line for line in result.explain)


def test_focal_conflict_with_placement_rect_fails_open_to_html_title() -> None:
    # D-CAL-20 优先顺位④/OQ-CAL-08：veil-footer 只有单一固定候选框（雾带上
    # 方），没有备选位置——镜头焦点正好落在这个框内时，宁可回退纯 HTML 标
    # 题，也不要硬贴一个大概率压脸的艺术字贴纸。
    trip = {
        "meta": {"title": "拾光", "coverOpeningStyle": "veil-footer"},
        "coverAssetId": "asset-1",
        "assets": [{"id": "asset-1", "focalPoint": {"x": 0.5, "y": 0.25}}],
    }
    write_png, written = _write_png_recorder()

    result = resolve_title_art(
        trip, resolve_asset_path=_no_asset_path, write_png=write_png
    )
    assert result is None
    assert written == []
    meta_dict = trip["meta"]["titleArt"]
    assert meta_dict["enabled"] is False
    assert meta_dict["reason"] == "focal_conflict:veil-footer"


def test_focal_outside_placement_rect_still_renders_normally() -> None:
    trip = {
        "meta": {"title": "拾光", "coverOpeningStyle": "veil-footer"},
        "coverAssetId": "asset-1",
        "assets": [{"id": "asset-1", "focalPoint": {"x": 0.5, "y": 0.8}}],
    }
    write_png, written = _write_png_recorder()

    result = resolve_title_art(
        trip, resolve_asset_path=_no_asset_path, write_png=write_png
    )
    assert result is not None
    assert len(written) == 1
    assert trip["meta"]["titleArt"]["enabled"] is True


def test_contact_stamp_archive_check_true_for_realistic_minimal_trip() -> None:
    # 实测发现（D-CAL-20 优先顺位⑤落地时）：format_trip_meta 的天数兜底
    # （"N 天"）几乎总是非空，导致这个占用判定在现网几乎总是 True——备选
    # 候选设计上正确，但真实触发窗口很窄，这里留痕说明，避免误以为它会
    # 经常生效。
    trip = {"meta": {"title": "拾光", "coverOpeningStyle": "contact-stamp"}}
    assert engine_mod._contact_stamp_hook_or_archive_present(trip, {}) is True


def test_contact_stamp_falls_back_to_secondary_when_primary_focal_conflicts(
    monkeypatch,
) -> None:
    # D-CAL-20 优先顺位⑤：主候选（左块）跟镜头焦点冲突时，若备选候选（右块）
    # 未被占用，应换到备选而不是整体 fail-open。真实 trip 里备选几乎总被
    # archive strip 占用（见上一条测试），这里直接把占用判定打成"未占用"
    # 来构造这个场景，专门验证多候选切换机制本身。
    monkeypatch.setattr(engine_mod, "_contact_stamp_hook_or_archive_present", lambda *_a: False)

    primary_rect = placement_preset("contact-stamp").rect
    focal_x = primary_rect["x"] + primary_rect["w"] / 2
    focal_y = primary_rect["y"] + primary_rect["h"] / 2
    trip = {
        "meta": {"title": "拾光", "coverOpeningStyle": "contact-stamp"},
        "coverAssetId": "asset-1",
        "assets": [{"id": "asset-1", "focalPoint": {"x": focal_x, "y": focal_y}}],
    }
    write_png, written = _write_png_recorder()

    result = resolve_title_art(trip, resolve_asset_path=_no_asset_path, write_png=write_png)

    assert result is not None
    assert len(written) == 1
    assert trip["meta"]["titleArt"]["enabled"] is True


def test_contact_stamp_uses_secondary_candidate_box_when_primary_conflicts(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(engine_mod, "_contact_stamp_hook_or_archive_present", lambda *_a: False)

    photo_path = tmp_path / "photo.png"
    Image.new("RGB", (1000, 1000), (200, 200, 200)).save(photo_path)

    primary_rect = placement_preset("contact-stamp").rect
    focal_x = primary_rect["x"] + primary_rect["w"] / 2
    focal_y = primary_rect["y"] + primary_rect["h"] / 2
    trip = {
        "meta": {"title": "拾光", "coverOpeningStyle": "contact-stamp"},
        "coverAssetId": "asset-1",
        "assets": [{"id": "asset-1", "focalPoint": {"x": focal_x, "y": focal_y}}],
    }
    write_png, written = _write_png_recorder()

    def _resolve_asset_path(_asset):
        return photo_path

    result = resolve_title_art(
        trip, resolve_asset_path=_resolve_asset_path, write_png=write_png
    )

    assert result is not None
    assert len(written) == 1
    fallback_rect = FALLBACK_PRESETS["contact-stamp"][0].rect
    expected_x = round(fallback_rect["x"] + fallback_rect["w"] / 2, 4)
    expected_y = round(fallback_rect["y"] + fallback_rect["h"] / 2, 4)
    assert abs(result.position["x"] - expected_x) < 0.01
    assert abs(result.position["y"] - expected_y) < 0.01
    # 备选候选跟主候选一样带 assume_dark_veil，即便原图偏亮也应强制选白墨。
    assert result.main_color == "#ffffff"


def test_contact_stamp_fails_open_when_primary_conflicts_and_fallback_occupied() -> None:
    # 默认（未 monkeypatch）情况下备选几乎总被判定占用，主候选又跟焦点冲突
    # 时应整体 fail-open，不硬贴。
    primary_rect = placement_preset("contact-stamp").rect
    focal_x = primary_rect["x"] + primary_rect["w"] / 2
    focal_y = primary_rect["y"] + primary_rect["h"] / 2
    trip = {
        "meta": {"title": "拾光", "coverOpeningStyle": "contact-stamp"},
        "coverAssetId": "asset-1",
        "assets": [{"id": "asset-1", "focalPoint": {"x": focal_x, "y": focal_y}}],
    }
    write_png, written = _write_png_recorder()

    result = resolve_title_art(trip, resolve_asset_path=_no_asset_path, write_png=write_png)

    assert result is None
    assert written == []
    assert trip["meta"]["titleArt"]["enabled"] is False
    assert trip["meta"]["titleArt"]["reason"] == "focal_conflict:contact-stamp"


def test_folio_place_present_true_when_place_distinct_from_title() -> None:
    # OQ-CAL-09 收尾：地点跟标题不同名时 .cover-opening__place 会渲染，占用
    # 纸面栏顶部——须跟 assemble.py 用同一套 resolve_show_cover_place 判定。
    trip = {
        "meta": {"title": "毕业照精选", "places": ["呼伦贝尔草原"]},
        "intent": {"placesUserSet": True},
    }
    assert engine_mod._folio_place_present(trip, {}) is True


def test_folio_place_present_false_when_place_duplicates_title() -> None:
    trip = {"meta": {"title": "呼伦贝尔"}}
    assert engine_mod._folio_place_present(trip, {}) is False


def test_folio_overlap_ignores_focal_conflict_for_paper_bg_candidate() -> None:
    # 主候选 assume_paper_bg=True：矩形对应的不是照片内容（那块区域压根不
    # 显示 .cover-hero 照片），镜头焦点落在同名照片坐标里跟视觉上"压脸"是
    # 两件事——focal_conflict 不该淘汰这个候选。
    primary_rect = placement_preset("folio-overlap").rect
    focal_x = primary_rect["x"] + primary_rect["w"] / 2
    focal_y = primary_rect["y"] + primary_rect["h"] / 2
    trip = {
        "meta": {"title": "呼伦贝尔", "coverOpeningStyle": "folio-overlap"},
        "coverAssetId": "asset-1",
        "assets": [{"id": "asset-1", "focalPoint": {"x": focal_x, "y": focal_y}}],
    }
    write_png, written = _write_png_recorder()

    result = resolve_title_art(trip, resolve_asset_path=_no_asset_path, write_png=write_png)

    assert result is not None
    assert len(written) == 1
    assert trip["meta"]["titleArt"]["enabled"] is True


def test_folio_overlap_forces_paper_color_regardless_of_bright_or_dark_photo(
    tmp_path,
) -> None:
    # assume_paper_bg：候选压在跟照片无关的固定纸面色块上，自动配色须忽略
    # 原图像素采样，改用纸色（--cover-folio-paper #f4f1ea，近白）固定估计，
    # 对比度算法应回到深墨 #1a1a1a，不管原图本身是纯黑还是纯白。
    photo_path = tmp_path / "photo.png"
    Image.new("RGB", (1000, 1000), (10, 10, 10)).save(photo_path)  # 原图本身很暗
    trip = {
        "meta": {"title": "呼伦贝尔", "coverOpeningStyle": "folio-overlap"},
        "coverAssetId": "asset-1",
        "assets": [{"id": "asset-1"}],
    }
    write_png, written = _write_png_recorder()

    def _resolve_asset_path(_asset):
        return photo_path

    result = resolve_title_art(trip, resolve_asset_path=_resolve_asset_path, write_png=write_png)

    assert result is not None
    assert len(written) == 1
    assert result.main_color == "#1a1a1a"
    assert any("纸面底色区" in line for line in result.explain)


def test_folio_overlap_uses_full_column_fallback_when_place_absent(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(engine_mod, "_folio_place_present", lambda *_a: False)
    photo_path = tmp_path / "photo.png"
    Image.new("RGB", (1000, 1000), (200, 200, 200)).save(photo_path)
    trip = {
        "meta": {"title": "呼伦贝尔", "coverOpeningStyle": "folio-overlap"},
        "coverAssetId": "asset-1",
        "assets": [{"id": "asset-1"}],
    }
    write_png, written = _write_png_recorder()

    def _resolve_asset_path(_asset):
        return photo_path

    result = resolve_title_art(trip, resolve_asset_path=_resolve_asset_path, write_png=write_png)

    assert result is not None
    assert len(written) == 1
    fallback_rect = FALLBACK_PRESETS["folio-overlap"][0].rect
    expected_x = round(fallback_rect["x"] + fallback_rect["w"] / 2, 4)
    expected_y = round(fallback_rect["y"] + fallback_rect["h"] / 2, 4)
    assert abs(result.position["x"] - expected_x) < 0.01
    assert abs(result.position["y"] - expected_y) < 0.01


def test_folio_overlap_uses_narrow_primary_when_place_present(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(engine_mod, "_folio_place_present", lambda *_a: True)
    photo_path = tmp_path / "photo.png"
    Image.new("RGB", (1000, 1000), (200, 200, 200)).save(photo_path)
    trip = {
        "meta": {"title": "呼伦贝尔", "coverOpeningStyle": "folio-overlap"},
        "coverAssetId": "asset-1",
        "assets": [{"id": "asset-1"}],
    }
    write_png, written = _write_png_recorder()

    def _resolve_asset_path(_asset):
        return photo_path

    result = resolve_title_art(trip, resolve_asset_path=_resolve_asset_path, write_png=write_png)

    assert result is not None
    assert len(written) == 1
    primary_rect = placement_preset("folio-overlap").rect
    expected_x = round(primary_rect["x"] + primary_rect["w"] / 2, 4)
    expected_y = round(primary_rect["y"] + primary_rect["h"] / 2, 4)
    assert abs(result.position["x"] - expected_x) < 0.01
    assert abs(result.position["y"] - expected_y) < 0.01


def test_route_c_ocr_mismatch_falls_back_to_route_b() -> None:
    trip = {"meta": {"title": "拾光", "coverOpeningStyle": "veil-footer"}}
    write_png, written = _write_png_recorder()

    def _fake_generate_raw(style_id, *, title, subtitle=None, **_kw):
        return _FakeRawResult(image=Image.new("RGB", (32, 32), (255, 255, 255)))

    def _fake_ocr_verify(_img, _expected, **_kw):
        return False

    result = resolve_title_art(
        trip,
        resolve_asset_path=_no_asset_path,
        write_png=write_png,
        route_c_enabled=True,
        generate_raw=_fake_generate_raw,
        ocr_verify=_fake_ocr_verify,
    )
    assert result is not None
    assert result.engine == "clean-pipeline-v1"
    assert result.fallback_from == "diffusion-fixed-prompt-v1"
    assert len(written) == 1
