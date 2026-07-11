"""lint_pt_default_flags smoke."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.lint_pt_default_flags import check_defaults


def test_lint_passes_with_conservative_defaults(tmp_path: Path) -> None:
    signoff = tmp_path / "signoff.json"
    signoff.write_text(
        json.dumps(
            {
                "status": "pending",
                "flags": {
                    "pipeline.parallel_ingest": False,
                    "llm.narrate_concurrency": 1,
                },
            }
        ),
        encoding="utf-8",
    )
    rc, summary = check_defaults(signoff=signoff)
    assert rc == 0
    assert summary["overallPassed"] is True
    assert summary["acceleratedDefaults"] is False


def test_lint_repo_signoff_pending_ok_while_defaults_off() -> None:
    root = Path(__file__).resolve().parents[3]
    signoff = root / "docs" / "acceptance-records" / "pipeline-throughput-default-flag-signoff.json"
    rc, summary = check_defaults(signoff=signoff)
    assert rc == 0
    assert summary["parallel_ingest_default"] is False
    assert summary["narrate_concurrency_default"] == 1
