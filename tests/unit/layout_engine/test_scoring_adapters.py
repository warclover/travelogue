"""Regression: layout_engine scoring adapters must delegate, not self-recurse."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from travelogue.layout_engine.scoring.aesthetic import aesthetic_overall
from travelogue.layout_engine.scoring.hero import effective_hero_score


def _sample_asset() -> dict:
    return {
        "id": "asset-001",
        "tags": ["landscape"],
        "quality": {"sharpness": 0.8},
    }


def test_effective_hero_score_adapter_returns_float_without_recursion() -> None:
    score = effective_hero_score(_sample_asset(), median_sharp=0.5)
    assert isinstance(score, float)
    assert score >= 0.0


def test_aesthetic_overall_adapter_returns_optional_float_without_recursion() -> None:
    value = aesthetic_overall(_sample_asset())
    assert value is None or isinstance(value, float)


def test_layout_engine_mosaic_metrics_imports() -> None:
    import travelogue.layout_engine.mosaic.metrics as metrics

    counts = metrics.summarize_screen_patterns(
        [{"screens": [{"patternId": "screen-portrait-2"}]}]
    )
    assert counts == {"screen-portrait-2": 1}


@pytest.mark.parametrize(
    "rel",
    [
        "travelogue/layout_engine/scoring/hero.py",
        "travelogue/layout_engine/scoring/aesthetic.py",
    ],
)
def test_scoring_adapters_do_not_import_themselves(rel: str) -> None:
    root = Path(__file__).resolve().parents[3]
    path = root / rel
    module = path.stem
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module != f"travelogue.layout_engine.scoring.{module}":
            continue
        for alias in node.names:
            assert alias.name != module, f"{rel} must not import {alias.name} from itself"
