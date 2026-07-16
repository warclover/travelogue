"""AAD-22 aesthetic purpose_overall read-path smoke."""

from __future__ import annotations

import ast
from pathlib import Path


def test_purpose_overall_callable() -> None:
    from travelogue.curation.aesthetic_score import purpose_overall

    assert callable(purpose_overall)


def test_hotspots_reference_purpose_overall() -> None:
    """Cover / hero / moment / solo hotspots should call purpose_overall (lint allowlist)."""
    root = Path(__file__).resolve().parents[3] / "travelogue" / "curation"
    targets = (
        "curate_scoring.py",
        "moment_scoring.py",
        "cover_scoring_v2.py",
    )
    missing: list[str] = []
    for name in targets:
        path = root / name
        if not path.is_file():
            missing.append(f"missing-file:{name}")
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {
            n.id
            for n in ast.walk(tree)
            if isinstance(n, ast.Name)
        } | {
            n.attr
            for n in ast.walk(tree)
            if isinstance(n, ast.Attribute)
        }
        if "purpose_overall" not in names:
            missing.append(name)
    assert not missing, f"hotspots missing purpose_overall: {missing}"
