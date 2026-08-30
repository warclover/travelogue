"""DS-03 · Wizard import payload 字段契约 snapshot（Sheet 退役后冻结键集）。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from tests.studio_test_helpers import MockStudioHandler
from tests.unit.web.fixtures.import_wizard_payload_contract import (
    ALLOWED_KEYS,
    FINE_CRAFT_REQUIRED_KEYS,
    OPTIONAL_KEYS,
    QUICK_SHARE_REQUIRED_KEYS,
)
from travelogue.web.studio_handlers.import_handlers import handle_import
from travelogue.web.studio_jobs import get_job_store, reset_job_store

_ROOT = Path(__file__).resolve().parents[3]
_WIZARD_JS = _ROOT / "templates" / "studio" / "homepage-v2" / "import-wizard.js"
_RUN_JS = _ROOT / "templates" / "studio" / "homepage-v2" / "import-run.js"


def test_ds_03_quick_share_required_keys_frozen() -> None:
    assert "albumPath" in QUICK_SHARE_REQUIRED_KEYS
    assert "photoCullEnabled" in QUICK_SHARE_REQUIRED_KEYS
    assert "layoutDensity" not in QUICK_SHARE_REQUIRED_KEYS
    assert QUICK_SHARE_REQUIRED_KEYS <= ALLOWED_KEYS


def test_ds_03_fine_craft_requires_layout_density() -> None:
    assert FINE_CRAFT_REQUIRED_KEYS - QUICK_SHARE_REQUIRED_KEYS == frozenset({"layoutDensity"})
    assert FINE_CRAFT_REQUIRED_KEYS <= ALLOWED_KEYS


def test_ds_03_optional_keys_disjoint_from_required() -> None:
    assert not (OPTIONAL_KEYS & QUICK_SHARE_REQUIRED_KEYS)
    assert OPTIONAL_KEYS <= ALLOWED_KEYS


def test_ds_03_source_still_assigns_contract_keys() -> None:
    """防回归：JS 仍写入契约字段名（非运行时；e2e 负责真实 POST body）。"""
    wizard = _WIZARD_JS.read_text(encoding="utf-8")
    run = _RUN_JS.read_text(encoding="utf-8")
    logic = (_RUN_JS.parent / "import-run-logic.js").read_text(encoding="utf-8")
    assert "function buildWizardPayload" in wizard
    # SFH W1 · payload 组装下沉 logic；壳层仍 export buildImportPayload
    assert "function buildImportPayloadFields" in logic  # ASH-CONTRACT
    assert "buildImportPayloadFields" in run
    assert "function buildImportPayload" in run
    for key in (
        "photoCullEnabled",
        "keepNearDuplicates",
        "layoutDensity",
        "eligibleCount",
        "dateRange",
        "userNotes",
        "travelNotes",
        "featuredDir",
        "materialDir",
        "planText",
        "edition",
    ):
        assert key in wizard, f"missing key assignment surface: {key}"


def test_m3_upload_aligns_with_wizard_fields() -> None:
    """AC-QH-03 · 上传旁路与 Wizard 字段对齐（源码契约）。"""
    wizard = _WIZARD_JS.read_text(encoding="utf-8")
    run = _RUN_JS.read_text(encoding="utf-8")
    assert "function startUploadFromWizard" in wizard
    assert "validateFineFields()" in wizard
    assert "uploadOpts.layoutDensity" in wizard or "layoutDensity: readLayoutDensity()" in wizard
    assert "template_mode:" in wizard or "template_mode =" in wizard
    assert 'placeUserSet:' in wizard or "placeUserSet:" in wizard
    assert "titleUserSet" in wizard
    assert 'v2-wizard-template-mode' in run
    assert 'v2-template-mode' not in run or 'v2-wizard-template-mode' in run
    assert 'form.append("place", "旅途")' not in run
    assert "placeUserSet" in run
    assert "titleUserSet" in run
    assert "dateRangeStart" in run or "dateRange" in run


def test_m3_preview_four_states_copy_frozen() -> None:
    """AC-QH-04 · 清点四态走 logic 输出，不再冻源码字面量位置。"""
    wizard = _WIZARD_JS.read_text(encoding="utf-8")
    logic = (_WIZARD_JS.parent / "import-wizard-logic.js").read_text(encoding="utf-8")
    assert "正在清点照片…" in wizard
    assert "照片较多，制作时将自动清点" in wizard
    assert "wizardFailedVerifyLine" in wizard
    assert "classifyAlbumPreviewFailure" in wizard
    assert "未能清点照片，请更换文件夹" in logic
    assert "未能清点照片，可更换文件夹或仍要开始" in logic
    assert "function wizardPhotoSummaryLine" in logic
    assert "文件夹有 " in logic
    assert '_previewState === "failed"' in wizard or '_previewState = "failed"' in wizard
    assert '_previewState === "degraded"' in wizard or '_previewState = "degraded"' in wizard
    assert "PREVIEW_TIMEOUT_MS" in wizard
    assert "canStartAfterPreview" in wizard


def test_m3_cancel_confirm_copy() -> None:
    """AC-QH-05 · 取消确认人话。"""
    run = _RUN_JS.read_text(encoding="utf-8")
    assert "取消后将删除未完成的草稿" in run
    assert "已清理未完成草稿" in run


def test_ac_qh_03b_fine_craft_result_fields_reach_worker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-QH-03b · 精细旁路：标题/地点/手动模板进入 worker（成册结果前置）。

    成册落盘结果由 dogfood UX-QH-02 覆盖；本测锁定 handler→worker 契约。
    """
    monkeypatch.setenv("TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM", "1")
    reset_job_store()
    album = tmp_path / "album-qh03b"
    album.mkdir()
    (album / "a.jpg").write_bytes(b"x")
    handler = MockStudioHandler(
        tmp_path / "trips",
        json_body={
            "albumPath": str(album),
            "title": "AC精细标题",
            "place": "奈良",
            "placeUserSet": True,
            "mode": "fine_craft",
            "template_mode": "manual",
            "template_id": "visual-journal",
            "layoutDensity": "hero_first",
            "userNotes": "ac-qh-03b",
            "force": True,
            "forceStub": True,
        },
    )
    with patch("travelogue.web.studio_handlers.import_handlers.run_import_job_subprocess") as run_job:
        with patch(
            "travelogue.web.studio_handlers.import_handlers.assert_album_importable",
            return_value="album-qh03b",
        ):
            handle_import(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 202, body
    payload = run_job.call_args.args[1]
    assert payload["title"] == "AC精细标题"
    assert payload["place"] == "奈良"
    assert payload["placeUserSet"] is True
    assert payload["mode"] == "fine_craft"
    assert payload["template_mode"] == "manual"
    assert payload["template_id"] == "visual-journal"
    assert payload["layoutDensity"] == "hero_first"
    assert payload["userNotes"] == "ac-qh-03b"
    stored = get_job_store().get(body["jobId"])
    assert stored is not None
    assert stored.trip_id


def test_title_user_set_preserves_dotted_title(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """BE-SR-05 · 用户手改标题含点号时不得再 humanize。"""
    monkeypatch.setenv("TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM", "1")
    reset_job_store()
    album = tmp_path / "album-title-user"
    album.mkdir()
    (album / "a.jpg").write_bytes(b"x")
    handler = MockStudioHandler(
        tmp_path / "trips",
        json_body={
            "albumPath": str(album),
            "title": "Day1.出发",
            "titleUserSet": True,
            "place": "旅途",
            "placeUserSet": False,
            "mode": "quick_share",
            "force": True,
            "forceStub": True,
        },
    )
    with patch("travelogue.web.studio_handlers.import_handlers.run_import_job_subprocess") as run_job:
        with patch(
            "travelogue.web.studio_handlers.import_handlers.assert_album_importable",
            return_value="album-title-user",
        ):
            handle_import(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 202, body
    payload = run_job.call_args.args[1]
    assert payload["title"] == "Day1.出发"


def test_default_title_still_humanized_when_not_user_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM", "1")
    reset_job_store()
    album = tmp_path / "album-title-default"
    album.mkdir()
    (album / "a.jpg").write_bytes(b"x")
    handler = MockStudioHandler(
        tmp_path / "trips",
        json_body={
            "albumPath": str(album),
            "title": "linzhi_a1b2c3d4e5f6",
            "titleUserSet": False,
            "place": "旅途",
            "mode": "quick_share",
            "force": True,
            "forceStub": True,
        },
    )
    with patch("travelogue.web.studio_handlers.import_handlers.run_import_job_subprocess") as run_job:
        with patch(
            "travelogue.web.studio_handlers.import_handlers.assert_album_importable",
            return_value="album-title-default",
        ):
            handle_import(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 202, body
    payload = run_job.call_args.args[1]
    assert payload["title"] == "linzhi"
