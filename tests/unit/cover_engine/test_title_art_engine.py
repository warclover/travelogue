"""Unit tests · title_art engine orchestrator (PRD §5/§6/§8 · D-CAL-16)."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from PIL import Image

from travelogue.cover_engine.title_art import engine as engine_mod
from travelogue.cover_engine.title_art.engine import mark_title_art_stale, resolve_title_art
from travelogue.cover_engine.title_art.route_c import RouteCFailure

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
