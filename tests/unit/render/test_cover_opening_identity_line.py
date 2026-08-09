"""装帧身份线前封回声（D-SFI-13 扩容 / D-CAL-26，2026-08-09）。

复用已有的 ``works_brand`` 署名三态，往全部 10 款封面风格追加第三处渲染位
（原仅 ``cover-closing__brand`` + ``longshot-boundary-footer__brand`` 两处）。
首批 4 款（band-cut/veil-footer/contact-stamp/folio-overlap）与扩展的 6 款
（cameo-aperture/type-monument/scroll-head/portal-arch/horizon-split/
diptych-seam）均已用真实渲染截图逐个核对（见决策记录 §5、§8），产品负责人
拍板默认开启。
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import travelogue.render.assemble as assemble_module
from travelogue.paths import ROOT, TEMPLATE_VISUAL_JOURNAL
from travelogue.render.assemble import build_render_context

FIXTURE = ROOT / "schemas" / "fixtures" / "trip.render_golden.json"
DEMO_ASSETS = TEMPLATE_VISUAL_JOURNAL / "assets"


@pytest.fixture
def trip_workspace(tmp_path: Path) -> Path:
    import shutil

    trip = json.loads(FIXTURE.read_text(encoding="utf-8"))
    ws = tmp_path / "trips" / "render-golden-demo"
    ws.mkdir(parents=True)
    shutil.copytree(DEMO_ASSETS, ws / "assets")
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    return ws, trip


@pytest.mark.parametrize(
    "style_id",
    [
        "band-cut",
        "veil-footer",
        "contact-stamp",
        "folio-overlap",
        "cameo-aperture",
        "type-monument",
        "scroll-head",
        "portal-arch",
        "horizon-split",
        "diptych-seam",
    ],
)
def test_show_cover_opening_brand_defaults_on_for_whitelisted_styles(
    trip_workspace, style_id: str
) -> None:
    """全部 10 款已核对风格默认显示（showWorksBrand 默认 True → Travelogue）。"""
    ws, trip = trip_workspace
    trip = copy.deepcopy(trip)
    trip.setdefault("meta", {})["coverOpeningStyle"] = style_id
    ctx = build_render_context(trip, export_mode="draft", trip_root=ws)
    assert ctx["showCoverOpeningBrand"] is True
    assert ctx["worksBrandLine"] == "Travelogue"


def test_show_cover_opening_brand_off_for_style_outside_allowlist(
    trip_workspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """不在白名单里的风格 id 不显示，避免盲开出 bug——10 款已全部核对完，
    这里用一个不存在的假 style id 撑住回归防线（真实风格目前无人在白名单
    外）。"""
    ws, trip = trip_workspace
    trip = copy.deepcopy(trip)
    trip.setdefault("meta", {})["coverOpeningStyle"] = "band-cut"
    monkeypatch.setattr(assemble_module, "_COVER_OPENING_BRAND_STYLES", ("some-other-style",))
    ctx = build_render_context(trip, export_mode="draft", trip_root=ws)
    assert ctx["showCoverOpeningBrand"] is False


def test_show_cover_opening_brand_respects_hidden_mode(trip_workspace) -> None:
    """署名三态选「不显示」时，即便风格在白名单里也不渲染前封回声。"""
    ws, trip = trip_workspace
    trip = copy.deepcopy(trip)
    trip.setdefault("meta", {})["coverOpeningStyle"] = "band-cut"
    trip["meta"]["worksBrandMode"] = "hidden"
    ctx = build_render_context(trip, export_mode="draft", trip_root=ws)
    assert ctx["showCoverOpeningBrand"] is False


def test_show_cover_opening_brand_respects_custom_text(trip_workspace) -> None:
    """自定义署名文案（≤14 字）也会出现在前封回声，跟封底/长图脚同源。"""
    ws, trip = trip_workspace
    trip = copy.deepcopy(trip)
    trip.setdefault("meta", {})["coverOpeningStyle"] = "veil-footer"
    trip["meta"]["worksBrandMode"] = "custom"
    trip["meta"]["worksBrandText"] = "阿舟的旅途"
    ctx = build_render_context(trip, export_mode="draft", trip_root=ws)
    assert ctx["showCoverOpeningBrand"] is True
    assert ctx["worksBrandLine"] == "阿舟的旅途"


def test_cover_opening_brand_markup_appears_in_html_by_default(trip_workspace) -> None:
    """接线到模板：白名单风格默认就有 .cover-opening__brand，不需要额外开关。"""
    from travelogue.render.engine import render_html

    ws, trip = trip_workspace
    trip = copy.deepcopy(trip)
    trip.setdefault("meta", {})["coverOpeningStyle"] = "band-cut"
    html = render_html(trip, export_mode="draft", trip_root=ws)
    assert 'class="cover-opening__brand"' in html
    assert 'data-block="cover-opening-brand"' in html


def test_cover_opening_brand_markup_absent_outside_allowlist(
    trip_workspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """回归防线：白名单以外的风格永远不出现该标记（哪怕日后误改白名单常量）。"""
    from travelogue.render.engine import render_html

    ws, trip = trip_workspace
    trip = copy.deepcopy(trip)
    trip.setdefault("meta", {})["coverOpeningStyle"] = "band-cut"
    monkeypatch.setattr(assemble_module, "_COVER_OPENING_BRAND_STYLES", ())
    html = render_html(trip, export_mode="draft", trip_root=ws)
    assert "cover-opening__brand" not in html
