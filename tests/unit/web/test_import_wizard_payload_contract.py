"""DS-03 · Wizard import payload 字段契约 snapshot（Sheet 退役后冻结键集）。"""

from __future__ import annotations

from pathlib import Path

from tests.unit.web.fixtures.import_wizard_payload_contract import (
    ALLOWED_KEYS,
    FINE_CRAFT_REQUIRED_KEYS,
    OPTIONAL_KEYS,
    QUICK_SHARE_REQUIRED_KEYS,
)

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
    assert "function buildWizardPayload" in wizard
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
    assert 'v2-wizard-template-mode' in run
    assert 'v2-template-mode' not in run or 'v2-wizard-template-mode' in run
    assert 'form.append("place", "旅途")' not in run
    assert "placeUserSet" in run
    assert "dateRangeStart" in run or "dateRange" in run


def test_m3_preview_four_states_copy_frozen() -> None:
    """AC-QH-04 · 清点四态文案冻结。"""
    wizard = _WIZARD_JS.read_text(encoding="utf-8")
    assert "正在清点照片…" in wizard
    assert "照片较多，制作时将自动清点" in wizard
    assert "未能清点照片，可更换文件夹或直接开始" in wizard
    assert "已清点 " in wizard
    assert '_previewState === "failed"' in wizard or '_previewState = "failed"' in wizard
    assert '_previewState === "degraded"' in wizard or '_previewState = "degraded"' in wizard
    assert "PREVIEW_TIMEOUT_MS" in wizard


def test_m3_cancel_confirm_copy() -> None:
    """AC-QH-05 · 取消确认人话。"""
    run = _RUN_JS.read_text(encoding="utf-8")
    assert "取消后将删除未完成的草稿" in run
    assert "已清理未完成草稿" in run
