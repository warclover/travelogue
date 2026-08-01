"""ALG-V3 W1a-2 · Ready / MayCall / Import contract gates (AC-01/02/05a/06)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from travelogue.config import AppConfig
from travelogue.config.loader import patch_config_file
from travelogue.config.misc import LlmConfig, NarrativeConfig
from travelogue.config.studio import StudioConfig
from travelogue.llm.ready import (
    resolve_llm_may_call,
    resolve_llm_ready_summary,
)
from travelogue.services.llm_decor_line import should_call_llm_decor
from travelogue.web.studio_narrate import resolve_studio_narrate_provider


def test_ac01_no_key_import_stays_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-01: 无 Key → ready=false · usedOnImport=false · import provider=stub."""
    monkeypatch.setattr(
        "travelogue.llm.ready.probe_llm_ready",
        lambda *, cfg=None: False,
    )
    outbound = {"n": 0}

    def _chat(*_a, **_k):
        outbound["n"] += 1
        raise AssertionError("must not call LLM")

    monkeypatch.setattr("travelogue.llm.client.chat_completion", _chat)
    cfg = AppConfig(llm=LlmConfig(provider="deepseek", capability="auto"))
    summary = resolve_llm_ready_summary(cfg=cfg)
    assert summary["ready"] is False
    assert summary["usedOnImport"] is False
    assert summary["mayCall"] is False
    assert resolve_studio_narrate_provider(cfg=cfg) == "stub"
    assert outbound["n"] == 0


def test_ac02_ready_with_key_prefer_false_no_import_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-02: 有 Key + prefer=false → ready=true · usedOnImport=false · mayCall=false."""
    monkeypatch.setattr(
        "travelogue.llm.ready.probe_llm_ready",
        lambda *, cfg=None: True,
    )
    monkeypatch.setattr(
        "travelogue.llm.ready.resolve_llm_may_call",
        lambda *, cfg=None: False,
    )
    cfg = AppConfig(
        llm=LlmConfig(
            provider="deepseek",
            capability="auto",
            prefer_llm_when_ready=False,
        )
    )
    summary = resolve_llm_ready_summary(cfg=cfg)
    assert summary["ready"] is True
    assert summary["mayCall"] is False
    assert summary["usedOnImport"] is False
    assert summary["preferLlmWhenReady"] is False
    assert resolve_studio_narrate_provider(cfg=cfg) == "stub"


def test_ac06_capability_true_no_key_writes_llm_no_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "travelogue.llm.ready.probe_llm_ready",
        lambda *, cfg=None: False,
    )
    cfg = AppConfig(llm=LlmConfig(capability="true"))
    summary = resolve_llm_ready_summary(cfg=cfg)
    assert summary["ready"] is False
    assert summary["degradeReason"] == "llm_no_key"
    # auto 无凭证不写 llm_no_key
    auto = resolve_llm_ready_summary(
        cfg=AppConfig(llm=LlmConfig(capability="auto"))
    )
    assert "degradeReason" not in auto


def test_ac05a_decor_may_call_false_skips(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "travelogue.llm.ready.resolve_llm_may_call",
        lambda *, cfg=None: False,
    )
    cfg = AppConfig(
        narrative=NarrativeConfig(decor_line_llm_enabled=True, decor_line_voice_first=False),
        studio=StudioConfig(ai_surface_enabled=False),
    )
    chapter = {
        "id": "ch-01",
        "memoryAnchors": ["雨很大"],
        "facts": ["雨很大", "回酒店"],
    }
    trip = {"chapters": [chapter], "assets": []}
    assert should_call_llm_decor(chapter, trip, cfg=cfg) is False


def test_prefer_and_may_call_allows_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "travelogue.web.studio_narrate.probe_llm_ready",
        lambda *, cfg=None: True,
    )
    monkeypatch.setattr(
        "travelogue.web.studio_narrate.resolve_llm_may_call",
        lambda *, cfg=None: True,
    )
    monkeypatch.setattr(
        "travelogue.web.studio_narrate.resolve_ready_provider",
        lambda *, cfg=None: "deepseek",
    )
    monkeypatch.setattr(
        "travelogue.llm.ready.probe_llm_ready",
        lambda *, cfg=None: True,
    )
    monkeypatch.setattr(
        "travelogue.llm.ready.resolve_llm_may_call",
        lambda *, cfg=None: True,
    )
    cfg = AppConfig(
        llm=LlmConfig(
            provider="deepseek",
            prefer_llm_when_ready=True,
            capability="auto",
        )
    )
    assert resolve_studio_narrate_provider(cfg=cfg) == "deepseek"
    summary = resolve_llm_ready_summary(cfg=cfg)
    assert summary["usedOnImport"] is True
    assert summary["mayCall"] is True


def test_fe_alg3_04_prefer_capability_not_in_user_patch(tmp_path: Path) -> None:
    """FE-ALG3-04: prefer / capability 不进用户开放 PATCH 白名单。"""
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        "trips_dir: ./trips\nllm:\n  provider: stub\n  capability: auto\n"
        "  prefer_llm_when_ready: false\n",
        encoding="utf-8",
    )
    patch_config_file(
        cfg_path,
        {
            "llm": {
                "capability": "true",
                "prefer_llm_when_ready": True,
                "preferLlmWhenReady": True,
            },
            "layout": {"scoring": {"enabled": True, "wall_clock_limits_output": False}},
        },
    )
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    assert raw["llm"]["capability"] == "auto"
    assert raw["llm"]["prefer_llm_when_ready"] is False
    # scoring.enabled is whitelisted; wall_clock is not
    assert raw["layout"]["scoring"]["enabled"] is True
    assert "wall_clock_limits_output" not in raw["layout"]["scoring"]


def test_may_call_follows_ai_surface(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TRAVELOGUE_AI_SURFACE", raising=False)
    assert resolve_llm_may_call(cfg=AppConfig()) is False
    assert (
        resolve_llm_may_call(cfg=AppConfig(studio=StudioConfig(ai_surface_enabled=True)))
        is True
    )
