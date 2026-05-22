"""Regression: workshop-pipeline.ps1 must not pass invalid Typer flags."""

from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "workshop-pipeline.ps1"


def test_workshop_pipeline_no_invalid_publish_flag():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "publish:false" not in text
    assert "publish:true" not in text
    assert "--no-render" in text
    if "Export" in text:
        assert "lock $id copy" in text or "lock `$id copy" in text
        assert "export $id" in text or "export `$id" in text
