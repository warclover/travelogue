"""ACP W1a · title_art_adapter wraps callables without importing cover_engine."""

from __future__ import annotations

import pytest

from travelogue.ai.agents.title_art_adapter import (
    AcpSkipRouteC,
    call_generate_raw,
    call_ocr_verify,
)
from travelogue.ai.budget import clear_budgets
from travelogue.ai.telemetry import clear_ops_summary, ops_summary
from travelogue.config.ai_capability import AiCapabilityConfig
from travelogue.config.app import AppConfig
from travelogue.config.misc import LlmConfig
from travelogue.config.runtime import app_config_scope
from travelogue.config.studio import StudioConfig


def setup_function() -> None:
    clear_budgets()
    clear_ops_summary()


def test_call_generate_raw_passthrough_when_acp_off() -> None:
    calls: list[tuple] = []

    def fake_generate(style: str, *, title: str, **kwargs):
        calls.append((style, title, kwargs))
        return {"image": "ok"}

    with app_config_scope(AppConfig()):
        out = call_generate_raw(
            fake_generate,
            "style-a",
            title="拾光",
            model="wanx2.1-t2i-plus",
            trip={"tripId": "t1"},
            telemetry_model="wanx",
        )
    assert out == {"image": "ok"}
    assert calls == [("style-a", "拾光", {"model": "wanx2.1-t2i-plus"})]
    assert ops_summary()["title_art_route_c"]["calls"] == 1


def test_call_generate_raw_gate_blocks_when_acp_on() -> None:
    def boom(*_a, **_k):
        raise AssertionError("must not call underlying generate")

    cfg = AppConfig(
        ai_capability=AiCapabilityConfig(enabled=True),
        studio=StudioConfig(ai_surface_enabled=False),
        llm=LlmConfig(provider="stub"),
    )
    with app_config_scope(cfg):
        with pytest.raises(AcpSkipRouteC) as ei:
            call_generate_raw(boom, "s", title="x", trip={"tripId": "t1"})
    assert ei.value.reason == "surface_off"


def test_call_ocr_verify_passthrough() -> None:
    def fake_ocr(img, expected: str) -> bool:
        return expected == "拾光"

    with app_config_scope(AppConfig()):
        assert call_ocr_verify(fake_ocr, object(), "拾光") is True
        assert call_ocr_verify(fake_ocr, object(), "否") is False
