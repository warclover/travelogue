"""Resolve repository root from any test module path."""

from __future__ import annotations

from pathlib import Path

_TESTS = Path(__file__).resolve().parent


def repo_root(from_file: str | Path | None = None) -> Path:
    """Return repo root for a test file under ``tests/`` (any depth)."""
    if from_file is None:
        return _TESTS.parent
    path = Path(from_file).resolve()
    rel = path.relative_to(_TESTS)
    return path.parents[len(rel.parts)]
