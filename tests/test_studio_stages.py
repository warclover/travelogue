"""Studio stage hints YAML (F-STU-14) and LLM narrate API (F-NAR-P2-03)."""

from __future__ import annotations

from travelogue.web.studio_stages import all_stage_hints, ingest_stage_hint, stage_hint


def test_stage_hint_from_yaml() -> None:
    assert stage_hint("curate") == "约 30 秒"
    assert stage_hint("longshot") == "约 20–40 秒"
    assert stage_hint("llm_narrate") == "约 30–60 秒"


def test_ingest_stage_hint_tiers_yaml() -> None:
    assert ingest_stage_hint(40) == "约 30 秒"
    assert ingest_stage_hint(80) == "约 1 分钟"
    assert ingest_stage_hint(200) == "约 2 分钟"


def test_all_stage_hints_includes_llm() -> None:
    hints = all_stage_hints()
    assert "llm_narrate" in hints
    assert hints["narrate"] == "约 10 秒"


def test_studio_llm_status_stub() -> None:
    from travelogue.config import AppConfig
    from travelogue.web.studio_narrate import studio_llm_status

    cfg = AppConfig()
    cfg.llm.provider = "stub"
    status = studio_llm_status(cfg=cfg)
    assert status["llmAvailable"] is False
    assert status["llmProvider"] == "stub"
