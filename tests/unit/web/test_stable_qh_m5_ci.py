"""Stable-QH M5 · CI 卫生契约（flake markers · unit 禁隐式 NIMA）。"""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_TOOLBAR = _ROOT / "tests" / "unit" / "web" / "test_preview_toolbar_v3.py"
_M20I = _ROOT / "tests" / "unit" / "web" / "test_studio_m20i_drill.py"
_ROLLBACK = _ROOT / "tests" / "unit" / "web" / "test_studio_rollback_drill.py"
_GATE = _ROOT / "docs" / "QUALITY-GATE.md"
_ACCEPT = _ROOT / "docs" / "acceptance-records" / "stable-qh-2026-07-15.md"
_CONFTEST = _ROOT / "tests" / "conftest.py"


def _func_block(src: str, func_name: str) -> str:
    needle = f"def {func_name}("
    idx = src.find(needle)
    assert idx >= 0, f"missing {func_name}"
    start = idx
    pos = idx
    while True:
        prev_nl = src.rfind("\n", 0, pos)
        if prev_nl < 0:
            start = 0
            break
        line = src[prev_nl + 1 : pos]
        stripped = line.strip()
        if stripped.startswith("@"):
            start = prev_nl + 1
            pos = prev_nl
            continue
        if not stripped:
            pos = prev_nl
            continue
        break
    end = src.find("\ndef ", idx + 1)
    if end < 0:
        end = len(src)
    return src[start:end]


def test_m5_01_f03_f04_have_playwright_serial() -> None:
    src = _TOOLBAR.read_text(encoding="utf-8")
    for name in (
        "test_v4_preview_toolbar_playwright_smoke",
        "test_v3_mobile_keeps_bottom_sheet",
    ):
        block = _func_block(src, name)
        assert "@pytest.mark.e2e" in block, name
        assert "@pytest.mark.playwright_serial" in block, name


def test_m5_01_f15_f16_module_serial() -> None:
    for path in (_M20I, _ROLLBACK):
        text = path.read_text(encoding="utf-8")
        assert "playwright_serial" in text
        assert "pytest.mark.e2e" in text


def test_m5_02_unit_stubs_pyiqa_by_default() -> None:
    """Autouse fixture must stub pyiqa in unit; this test is unit → expect False."""
    from travelogue.curation.photo_cull_ml import pyiqa_available

    assert pyiqa_available() is False
    conf = _CONFTEST.read_text(encoding="utf-8")
    assert "_forbid_implicit_nima_torch_in_unit" in conf


def test_m5_03_quality_gate_has_stable_qh_section() -> None:
    text = _GATE.read_text(encoding="utf-8")
    assert "稳定期质量硬化" in text
    assert "pytest tests/ -q --fast" in text
    assert "playwright_serial" in text
    assert "禁隐式 NIMA" in text


def test_m5_04_acceptance_record_exists() -> None:
    assert _ACCEPT.is_file()
    text = _ACCEPT.read_text(encoding="utf-8")
    assert "M5" in text
    assert "fix/stable-quality-hardening-v1" in text
