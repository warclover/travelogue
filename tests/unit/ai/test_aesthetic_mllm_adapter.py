"""ACP W1b · aesthetic_mllm_adapter has no curation imports."""

from __future__ import annotations

import ast
from pathlib import Path

from travelogue.ai.agents import aesthetic_mllm_adapter as adapter
from travelogue.ai.budget import clear_budgets
from travelogue.ai.telemetry import clear_ops_summary
from travelogue.config import AestheticMllmConfig
from travelogue.config.app import AppConfig
from travelogue.config.runtime import app_config_scope


def setup_function() -> None:
    clear_budgets()
    clear_ops_summary()


def test_adapter_module_does_not_import_curation() -> None:
    path = Path(adapter.__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("travelogue.curation"), node.module
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("travelogue.curation"), alias.name


def test_score_disabled_returns_none(tmp_path) -> None:
    asset = {"id": "a1", "displayFile": "missing.jpg"}
    with app_config_scope(AppConfig()):
        out = adapter.score_image_with_mllm(
            asset,
            trip_dir=tmp_path,
            purpose="cover",
            cfg=AestheticMllmConfig(enabled=False),
        )
    assert out is None


def test_mllm_cache_key_prefers_content_sig() -> None:
    key = adapter.mllm_cache_key(
        {"contentSig": "abc", "id": "a1"},
        model="qwen-vl-max",
        rubric="universal",
    )
    assert "sig:abc" in key
