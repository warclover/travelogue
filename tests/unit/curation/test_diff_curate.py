"""diff_curate CLI smoke test."""



from __future__ import annotations
from tests._repo_root import repo_root

import sys
from pathlib import Path

ROOT = repo_root(__file__)
sys.path.insert(0, str(ROOT))

from scripts.diff_curate import main


def test_diff_curate_fixture_passes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "diff_curate.py",
            "golden-mixed-scenes",
            "--fixture",
            "--work-dir",
            str(tmp_path / "dc"),
        ],
    )
    assert main() == 0
