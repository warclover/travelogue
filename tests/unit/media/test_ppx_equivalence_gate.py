"""PRD-PIPELINE-PERF-EXECUTION-V1 · QA-PPX-05 / D-PPX-10."""

from __future__ import annotations

from pathlib import Path


def test_equivalence_script_has_no_webp_hash_gate() -> None:
    """QA-PPX-05 · D-PPX-10 forbids full-file WebP hash equality."""
    text = Path("scripts/pipeline_perf_equivalence_check.py").read_text(encoding="utf-8")
    assert "hashlib" not in text
    assert "file_hash" not in text
