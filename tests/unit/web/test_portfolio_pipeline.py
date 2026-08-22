"""PFM W0 · import reject, schema isolation, homepage default-hidden entry."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.studio_test_helpers import MockStudioHandler
from travelogue.config import AppConfig, PortfolioPipelineConfig
from travelogue.config.edition import E_PORTFOLIO_UNAVAILABLE
from travelogue.config.runtime import config_override
from travelogue.web.studio_handlers.import_handlers import handle_import
from travelogue.web.studio_jobs import reset_job_store

pytestmark = [pytest.mark.unit, pytest.mark.pipeline_isolation]

_REPO = Path(__file__).resolve().parents[3]
_STUDIO = _REPO / "templates" / "studio"
_SCHEMA = _REPO / "schemas" / "trip.schema.json"


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    reset_job_store()


def _enabled_cfg() -> AppConfig:
    base = AppConfig()
    return replace(
        base,
        studio=replace(
            base.studio,
            portfolio_pipeline=PortfolioPipelineConfig(enabled=True),
        ),
    )


def test_import_portfolio_rejected_when_flag_off(tmp_path: Path) -> None:
    album = tmp_path / "album"
    album.mkdir()
    (album / "a.jpg").write_bytes(b"x")
    handler = MockStudioHandler(
        tmp_path / "trips",
        json_body={"albumPath": str(album), "edition": "portfolio", "forceStub": True},
    )
    with config_override(AppConfig()):
        handle_import(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 409
    assert body["error"] == E_PORTFOLIO_UNAVAILABLE
    assert "作品集" in body["message"]


def test_import_journal_omits_edition_and_proceeds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM", "1")
    album = tmp_path / "album"
    album.mkdir()
    (album / "a.jpg").write_bytes(b"x")
    handler = MockStudioHandler(
        tmp_path / "trips",
        json_body={"albumPath": str(album), "title": "奈良", "force": True, "forceStub": True},
    )
    with patch("travelogue.web.studio_handlers.import_handlers.run_import_job_subprocess") as run_job:
        with patch(
            "travelogue.web.studio_handlers.import_handlers.assert_album_importable",
            return_value="album",
        ):
            handle_import(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 202, body
    payload = run_job.call_args.args[1]
    assert payload.get("edition") in (None, "", "journal")


def test_import_portfolio_accepted_when_flag_on(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM", "1")
    album = tmp_path / "album"
    album.mkdir()
    (album / "a.jpg").write_bytes(b"x")
    handler = MockStudioHandler(
        tmp_path / "trips",
        json_body={
            "albumPath": str(album),
            "edition": "portfolio",
            "title": "奈良作品集",
            "force": True,
            "forceStub": True,
        },
    )
    with config_override(_enabled_cfg()):
        with patch("travelogue.web.studio_handlers.import_handlers.run_import_job_subprocess") as run_job:
            with patch(
                "travelogue.web.studio_handlers.import_handlers.assert_album_importable",
                return_value="album",
            ):
                handle_import(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 202, body
    payload = run_job.call_args.args[1]
    assert payload["edition"] == "portfolio"


def test_layout_engine_enum_has_no_third_value() -> None:
    schema = json.loads(_SCHEMA.read_text(encoding="utf-8"))
    enum = schema["properties"]["layoutEngine"]["enum"]
    assert enum == ["legacy", "screens"]
    studio = schema["$defs"]["tripStudio"]["properties"]
    assert studio["edition"]["enum"] == ["journal", "portfolio"]
    assert "folio" not in studio["edition"]["enum"]


def test_iso07_repo_has_no_third_layout_engine_value() -> None:
    """AC-PFM-27 · 全库检索无第三个 layoutEngine 字面量。"""
    import re

    allowed = {"legacy", "screens"}
    rx = re.compile(r"""layoutEngine(?:Version)?["']?\s*[:=]\s*["']([^"']+)["']""")
    roots = (_REPO / "travelogue", _REPO / "schemas", _REPO / "config")
    hits: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".py", ".json", ".yaml", ".yml"}:
                continue
            if path.name.endswith(".pyc"):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for match in rx.finditer(text):
                val = match.group(1)
                if "Version" in match.group(0):
                    continue
                if val not in allowed:
                    hits.append(f"{path.relative_to(_REPO)}: {val}")
    assert hits == []


def test_flag_on_journal_import_stays_journal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-PFM-02 · 开旗但不选作品集：导入仍走游记，不写 edition。"""
    monkeypatch.setenv("TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM", "1")
    album = tmp_path / "album"
    album.mkdir()
    (album / "a.jpg").write_bytes(b"x")
    handler = MockStudioHandler(
        tmp_path / "trips",
        json_body={"albumPath": str(album), "title": "奈良", "force": True, "forceStub": True},
    )
    with config_override(_enabled_cfg()):
        with patch("travelogue.web.studio_handlers.import_handlers.run_import_job_subprocess") as run_job:
            with patch(
                "travelogue.web.studio_handlers.import_handlers.assert_album_importable",
                return_value="album",
            ):
                handle_import(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 202, body
    payload = run_job.call_args.args[1]
    assert payload.get("edition") in (None, "", "journal")


def test_journal_chrome_unchanged_when_flag_exists() -> None:
    """AC-PFM-02 · 游记 Dock 仍「导出长图」；作品集主钮不进 init-v3 默认串。"""
    html = (_STUDIO / "studio-home-v2.html").read_text(encoding="utf-8")
    toolbar = (_STUDIO / "preview-toolbar" / "init-v3.js").read_text(encoding="utf-8")
    lvp = (_STUDIO / "preview-toolbar" / "features.js").read_text(encoding="utf-8")
    logic = (_STUDIO / "js" / "portfolio-export-logic.js").read_text(encoding="utf-8")
    assert "开始制作我的画册" in html
    assert "导出长图" in toolbar
    assert "导出作品集" not in toolbar
    assert "导出作品集" in logic
    assert "成册风格" in lvp
    assert "杂志成册（推荐）" in lvp
    assert "成册类型" in lvp
    assert "data-page-count" in lvp
    assert "改用游记（全收）" in (
        _STUDIO / "js" / "portfolio-export-logic.js"
    ).read_text(encoding="utf-8")
    assert "v2-wizard-page-count" not in html
    sheet = (_STUDIO / "preview-toolbar-v3-sheet.js").read_text(encoding="utf-8")
    assert "成册类型" in sheet
    assert 'data-book-zone="edition-type"' in sheet
    assert 'data-book-zone="layout-vibe"' in sheet
    assert "hooks.isPortfolio" in sheet
    shelf = (_STUDIO / "homepage-v2" / "shelf.js").read_text(encoding="utf-8")
    menu = (_STUDIO / "homepage-v2" / "shelf-menu.js").read_text(encoding="utf-8")
    assert "shelfEditionLine" in shelf
    assert "改为游记重排" in menu
    assert "做一本作品集" in html
    assert "开始制作我的画册" in html
    constants = (_STUDIO / "js" / "constants.js").read_text(encoding="utf-8")
    assert 'narrate: "正在生成画册文案…"' in constants
    import_logic = (_STUDIO / "homepage-v2" / "import-run-logic.js").read_text(
        encoding="utf-8"
    )
    assert 'JOURNAL_IMPORT_TITLE = "正在生成你的影像画册…"' in import_logic
    assert "配文 · 排版" in import_logic


def test_portfolio_wait_copy_avoids_writing_phrases() -> None:
    """AC-PFM-33 · 作品集等待态 / 成功面不含「文案 / 正在写」；游记 STAGE_LABELS 不动。"""
    import_logic = (_STUDIO / "homepage-v2" / "import-run-logic.js").read_text(
        encoding="utf-8"
    )
    import_run = (_STUDIO / "homepage-v2" / "import-run.js").read_text(encoding="utf-8")
    wait_copy = (_STUDIO / "homepage-v2" / "wait-tips-copy.js").read_text(
        encoding="utf-8"
    )
    wait_ctrl = (_STUDIO / "homepage-v2" / "wait-tips.js").read_text(encoding="utf-8")
    success = (_STUDIO / "js" / "portfolio-export-logic.js").read_text(encoding="utf-8")
    constants = (_STUDIO / "js" / "constants.js").read_text(encoding="utf-8")
    assert 'PORTFOLIO_IMPORT_TITLE = "正在按杂志页编排…"' in import_logic
    assert "自动分章 · 按页编排 · 可离开稍后回来" in import_logic
    assert "isCopyWritingPhrase" in import_logic
    assert "/文案|正在写/" in import_logic
    assert "resolveImportStageCopy(job, _importEdition)" in import_run
    assert "edition: _importEdition" in import_run
    assert "normalizeImportEdition(opts.edition)" in import_run
    assert "normalizeImportEdition(pending && pending.edition)" in import_run
    assert "waitTipsCardsForEdition" in wait_copy
    assert 'title: "分章排版，交给它"' in wait_copy
    assert "分章配文排版，交给它" in wait_copy
    assert "杂志" not in wait_copy
    assert "edition: _edition" in wait_ctrl
    assert "作品集已导出" in success
    assert "打开这一本" in success
    assert "正在写" not in success
    assert "正在生成画册文案" not in success
    assert 'narrate: "正在生成画册文案…"' in constants


def test_portfolio_flag_off_banner_and_bc_hidden() -> None:
    """AC-PFM-07 · 关旗隐藏 B/C；存量作品集横幅可改回游记。"""
    edition = (_STUDIO / "js" / "portfolio-edition-logic.js").read_text(encoding="utf-8")
    dock = (_STUDIO / "preview-toolbar" / "dock.js").read_text(encoding="utf-8")
    wizard = (_STUDIO / "homepage-v2" / "import-wizard-logic.js").read_text(
        encoding="utf-8"
    )
    features = (_STUDIO / "preview-toolbar" / "features.js").read_text(encoding="utf-8")
    assert "作品集编排暂时关闭 · 这一本仍可翻阅" in edition
    assert "改为游记重排" in edition
    assert "shouldShowPortfolioFlagOffBanner" in edition
    assert "shouldShowHomepagePortfolioEntry" in wizard
    assert "pipe.enabled && pipe.homepageEntry" in wizard
    assert "syncPortfolioFlagOffBanner" in dock
    assert "shouldMountEditionType" in features
    assert "edition / PFM / page-*" not in (
        "作品集编排暂时关闭 · 这一本仍可翻阅改为游记重排"
    )


def test_portfolio_narrow_gate_keeps_refine_export_on_desktop() -> None:
    """AC-PFM-24 · 作品集窄屏仍提示电脑精修/导出；游记字面仍在。"""
    logic = (_STUDIO / "preview-toolbar" / "narrow-gate-logic.js").read_text(
        encoding="utf-8"
    )
    gate = (_STUDIO / "preview-toolbar" / "narrow-gate.js").read_text(encoding="utf-8")
    init = (_STUDIO / "preview-toolbar" / "init-v3.js").read_text(encoding="utf-8")
    assert "手机可阅读分享页；精修与导出请在电脑浏览器打开本地址。" in logic
    assert "手机可翻阅这一本；精修与导出请在电脑浏览器打开本地址。" in logic
    assert "resolvePreviewNarrowGateCopy" in gate
    assert "refreshPreviewNarrowGate" in gate
    assert "refreshPreviewNarrowGate" in init
    assert "edition / PFM / page-*" not in (
        "手机可翻阅这一本；精修与导出请在电脑浏览器打开本地址。"
    )


def test_edition_radiogroup_keyboard_and_confirm_trap() -> None:
    """FE-PFM-15 · AC-PFM-13 · 身份 radiogroup + 确认走 studioModal 焦点陷阱。"""
    html = (_STUDIO / "studio-home-v2.html").read_text(encoding="utf-8")
    wizard = (_STUDIO / "homepage-v2" / "import-wizard.js").read_text(encoding="utf-8")
    features = (_STUDIO / "preview-toolbar" / "features.js").read_text(encoding="utf-8")
    modal = (_STUDIO / "studio-modal.js").read_text(encoding="utf-8")
    assert 'role="radiogroup"' in html
    assert 'id="v2-wizard-edition-journal"' in html
    assert 'aria-checked="true"' in html
    assert 'tabindex="0"' in html
    assert 'tabindex="-1"' in html
    assert "onEditionKeydown" in wizard
    assert "nextRadioId" in wizard
    assert 'role="radiogroup"' in features
    assert 'setAttribute("role", "radio")' in features
    assert "isRadioNavKey" in features
    assert "function trapFocus" in modal
    assert 'e.key === "Escape"' in modal
    assert "previousFocus" in modal
    assert "studioModal" in wizard
    assert "toolbarConfirm" in features


def test_config_exposes_derived_min_kept(tmp_path: Path) -> None:
    """D-PFM-29 · GET /config 投影系列库最小 photo_span，不写死 12。"""
    from travelogue.web.studio_handlers.config_handlers import handle_config

    handler = MockStudioHandler(tmp_path / "trips")
    handler.command = "GET"
    handle_config(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 200
    pipe = (body.get("studio") or {}).get("portfolioPipeline") or {}
    assert pipe.get("minKept") == 27
    assert pipe.get("pageCountChips") == [8, 12, 16, 20, 28]
    assert pipe.get("pageCountChipDetails")[0] == {"pages": 8, "capacity": 27}
    wizard = (_STUDIO / "homepage-v2" / "import-wizard.js").read_text(encoding="utf-8")
    assert "requestLowPhotoContinue" in wizard
    assert "lowPhotoContinueConfirm" in wizard


def test_homepage_portfolio_entry_exists_but_hidden_by_default() -> None:
    html = (_STUDIO / "studio-home-v2.html").read_text(encoding="utf-8")
    assert 'id="v2-cta-portfolio"' in html
    assert "做一本作品集" in html
    assert 'id="v2-cta-portfolio" hidden' in html or 'hidden>做一本作品集' in html
    assert "开始制作我的画册" in html
    edition = html[html.index('id="v2-wizard-edition"') : html.index('id="v2-wizard-edition"') + 80]
    assert "hidden" in edition
    assert "v2-wizard-page-count" not in html
    constants = (_STUDIO / "js" / "constants.js").read_text(encoding="utf-8")
    assert "E_PORTFOLIO_UNAVAILABLE" in constants


def test_shelf_list_exposes_portfolio_edition_and_page_count(tmp_path: Path) -> None:
    from travelogue.web.studio_trips import list_studio_trips

    trips_dir = tmp_path / "trips"
    pf = trips_dir / "nara"
    journal = trips_dir / "kyoto"
    pf.mkdir(parents=True)
    journal.mkdir()
    (pf / "trip.json").write_text(
        json.dumps(
            {
                "meta": {"title": "奈良"},
                "assets": [{"id": "a", "type": "image"}],
                "studio": {
                    "edition": "portfolio",
                    "portfolio": {"pageCount": 16},
                },
            }
        ),
        encoding="utf-8",
    )
    (journal / "trip.json").write_text(
        json.dumps({"meta": {"title": "京都"}, "assets": []}),
        encoding="utf-8",
    )
    rows = {row["tripId"]: row for row in list_studio_trips(trips_dir)}
    assert rows["nara"]["edition"] == "portfolio"
    assert rows["nara"]["pageCount"] == 16
    assert "edition" not in rows["kyoto"]
    assert "pageCount" not in rows["kyoto"]


def test_shelf_and_entry_share_overflow_chrome(tmp_path: Path) -> None:
    from travelogue.web.studio_entry import build_entry, edition_chrome
    from travelogue.web.studio_trips import list_studio_trips

    trips_dir = tmp_path / "trips"
    pf = trips_dir / "nara"
    pf.mkdir(parents=True)
    trip = {
        "meta": {"title": "奈良"},
        "assets": [{"id": "a", "type": "image"}],
        "studio": {
            "edition": "portfolio",
            "portfolio": {
                "pageCount": 16,
                "photosPlaced": 96,
                "photosKept": 180,
                "overflow": {"count": 84},
            },
        },
        "chapters": [],
    }
    (pf / "trip.json").write_text(json.dumps(trip), encoding="utf-8")
    chrome = edition_chrome(trip)
    entry = build_entry(trip, "nara")
    rows = {row["tripId"]: row for row in list_studio_trips(trips_dir)}
    assert chrome["overflowLine"] == "本册收录 96 / 180 张"
    assert entry["overflowLine"] == chrome["overflowLine"]
    assert rows["nara"]["overflowLine"] == chrome["overflowLine"]
    assert entry["dockCta"] == chrome["dockCta"]
    assert entry["layoutVibeVisible"] is False
