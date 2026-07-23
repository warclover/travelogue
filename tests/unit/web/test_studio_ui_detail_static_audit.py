"""Unit smoke for Studio UI detail static audit."""

from __future__ import annotations

from scripts.studio_ui_detail_static_audit import main, run_audit
from tests.e2e.ui_detail_runtime_helpers import semantic_color_count


def test_static_audit_no_modal_chrome_dual_standard() -> None:
    report = run_audit(wave="modal")
    conflicts = [
        f
        for f in report["findings"]
        if f["id"] == "D-UID-01" and "studio__" in str(f.get("selector", ""))
    ]
    assert conflicts == [], conflicts


def test_static_audit_preview_chrome_no_bare_legacy_hex() -> None:
    report = run_audit(wave="preview-chrome")
    bare = [f for f in report["findings"] if f["id"] == "D-UID-09"]
    assert bare == [], bare
    assert report["summary"]["P1"] == 0


def test_static_audit_wait_tips_no_rainbow_tones() -> None:
    report = run_audit(wave="wait-tips")
    rainbow = [f for f in report["findings"] if f["id"] == "D-UID-10"]
    assert rainbow == [], rainbow


def test_static_audit_cap_narrow_lightbox_no_forest_drift() -> None:
    report = run_audit(wave="cap-narrow-lightbox")
    drift = [f for f in report["findings"] if f["id"] == "D-UID-11"]
    assert drift == [], drift
    assert report["summary"]["P0"] == 0


def test_static_audit_bench_wizard_carousel_no_slate_cyan() -> None:
    report = run_audit(wave="bench-wizard-carousel")
    drift = [f for f in report["findings"] if f["id"] == "D-UID-12"]
    assert drift == [], drift
    assert report["summary"]["P0"] == 0


def test_static_audit_home_tokens_no_sky_default_or_hardcode() -> None:
    report = run_audit(wave="home-tokens")
    drift = [f for f in report["findings"] if f["id"] == "D-UID-13"]
    assert drift == [], drift
    assert report["summary"]["P0"] == 0


def test_static_audit_shelf_dev_loading_no_cyan_shimmer() -> None:
    report = run_audit(wave="shelf-dev-loading")
    drift = [f for f in report["findings"] if f["id"] == "D-UID-14"]
    assert drift == [], drift
    assert report["summary"]["P0"] == 0


def test_static_audit_overlay_toast_no_mint_forest() -> None:
    report = run_audit(wave="overlay-toast")
    drift = [f for f in report["findings"] if f["id"] == "D-UID-15"]
    assert drift == [], drift
    assert report["summary"]["P0"] == 0


def test_static_audit_wizard_help_closeout_clean() -> None:
    report = run_audit(wave="wizard-help-closeout")
    drift = [f for f in report["findings"] if f["id"] == "D-UID-16"]
    assert drift == [], drift
    assert report["summary"]["P0"] == 0


def test_static_audit_all_waves_no_p0_p1() -> None:
    report = run_audit(wave="all")
    assert report["summary"]["P0"] == 0
    assert report["summary"]["P1"] == 0, [
        f for f in report["findings"] if f["severity"] == "P1"
    ]


def test_static_audit_settings_sheet_no_mint_hardcode() -> None:
    report = run_audit(wave="settings-sheet")
    mint = [
        f
        for f in report["findings"]
        if f["id"] == "D-UID-08" and "薄荷" in str(f.get("detail", ""))
    ]
    assert mint == [], mint


def test_static_audit_strict_fails_on_p1(monkeypatch, tmp_path) -> None:
    """--strict 须在 P1>0 时非零退出（不再只拦 P0）。"""
    fake = {
        "summary": {"findings": 1, "P0": 0, "P1": 1, "P2": 0},
        "findings": [
            {
                "id": "D-UID-08",
                "severity": "P1",
                "selector": "x",
                "detail": "probe",
                "files": [],
            }
        ],
    }
    monkeypatch.setattr(
        "scripts.studio_ui_detail_static_audit.run_audit",
        lambda **_kwargs: fake,
    )
    assert main(["--wave", "all", "--strict"]) == 1


def test_settings_sheet_token_unrelated_selector_fails_ac20(tmp_path, monkeypatch) -> None:
    """AC-QFX-20 · token 仅在无关选择器 → 审计失败。"""
    from scripts import studio_ui_detail_static_audit as audit

    unrelated = tmp_path / "bento.css"
    unrelated.write_text(
        ".unrelated-foo { color: var(--studio-panel-ink, #14110d); }\n",
        encoding="utf-8",
    )
    sheet = tmp_path / "sheet.css"
    sheet.write_text(".preview-sheet { color: #546e7a; }\n", encoding="utf-8")
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    # Point module-level paths used inside audit_settings_sheet via Path joins — call helper directly
    assert audit._root_blocks_use_studio_panel_ink(
        unrelated.read_text(encoding="utf-8"),
        (".v2-settings-popover",),
    ) is False
    assert audit._root_blocks_use_studio_panel_ink(
        ".v2-settings-popover { --v2-set-ink: var(--studio-panel-ink, #000); }\n",
        (".v2-settings-popover",),
    ) is True


def test_bare_strict_defaults_wave_to_all(monkeypatch) -> None:
    """AC-QFX-08/19 · bare --strict ⇒ wave=all。"""
    seen: dict = {}

    def _fake(**kwargs):
        seen.update(kwargs)
        return {
            "summary": {"findings": 0, "P0": 0, "P1": 0, "P2": 0},
            "findings": [],
        }

    monkeypatch.setattr(
        "scripts.studio_ui_detail_static_audit.run_audit",
        _fake,
    )
    assert main(["--strict"]) == 0
    assert seen.get("wave") == "all"


def test_default_without_strict_stays_modal(monkeypatch) -> None:
    seen: dict = {}

    def _fake(**kwargs):
        seen.update(kwargs)
        return {
            "summary": {"findings": 0, "P0": 0, "P1": 0, "P2": 0},
            "findings": [],
        }

    monkeypatch.setattr(
        "scripts.studio_ui_detail_static_audit.run_audit",
        _fake,
    )
    assert main([]) == 0
    assert seen.get("wave") == "modal"


def test_semantic_color_count_collapses_alpha_variants() -> None:
    colors = [
        "rgb(245, 240, 232)",
        "rgba(245, 240, 232, 0.78)",
        "rgba(245, 240, 232, 0.58)",
        "rgba(255, 255, 255, 0.62)",
        "rgba(255, 255, 255, 0.48)",
        "rgb(26, 21, 16)",
    ]
    assert semantic_color_count(colors) == 3
