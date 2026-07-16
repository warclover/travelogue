"""Regular album imports must not surface demo-album failure codes."""

from __future__ import annotations

import pytest

from travelogue.demo.build import DemoError
from travelogue.media.ingest import IngestError
from travelogue.web.studio_pipeline import _raise_demo_from_ingest


@pytest.mark.parametrize(
    "code,detail",
    [
        ("E_INGEST_TOO_FEW", "need at least 4 assets in trip after ingest (have 1)"),
        ("E_INGEST_EMPTY", "no photos found"),
    ],
)
def test_studio_ingest_too_few_keeps_ingest_code(code: str, detail: str) -> None:
    with pytest.raises(DemoError) as excinfo:
        _raise_demo_from_ingest(IngestError(code, detail))
    assert excinfo.value.code == code
    assert "E_DEMO_TOO_FEW" not in excinfo.value.code


def test_studio_ingest_raw_still_rewrites_message() -> None:
    with pytest.raises(DemoError) as excinfo:
        _raise_demo_from_ingest(IngestError("E_INGEST_RAW_UNSUPPORTED", "raw"))
    assert excinfo.value.code == "E_INGEST_RAW_UNSUPPORTED"
    assert "RAW" in str(excinfo.value) or "raw" in str(excinfo.value).lower()


def test_ingest_too_few_failure_hint_is_not_demo_copy() -> None:
    from pathlib import Path

    errors = (
        Path(__file__).resolve().parents[3]
        / "templates"
        / "studio"
        / "js"
        / "errors.js"
    ).read_text(encoding="utf-8")
    # Demo path keeps its own hint; regular ingest must not reuse that wording.
    assert "E_INGEST_TOO_FEW:" in errors
    ingest_line = next(
        line for line in errors.splitlines() if "E_INGEST_TOO_FEW:" in line
    )
    demo_line = next(line for line in errors.splitlines() if "E_DEMO_TOO_FEW:" in line)
    assert "示例相册" not in ingest_line
    assert "智能挑选" in ingest_line
    assert "示例相册" in demo_line
