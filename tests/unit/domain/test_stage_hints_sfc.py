"""Share-Face Closeout W0 · vision_warmup 注入钩与降级文案（AC-SFC-04/05）。"""

from __future__ import annotations

import time

from travelogue.domain.stage_hints import (
    VISION_DOWNGRADE_NOTICE,
    VISION_WARMUP,
    maybe_sleep_vision_warmup_inject,
    stage_hint_text,
)


def test_vision_warmup_copy_is_human() -> None:
    text = stage_hint_text(VISION_WARMUP)
    assert "准备识图" in text
    assert "HF" not in text
    assert "CLIP" not in text
    assert "open_clip" not in text.lower()


def test_vision_downgrade_notice_frozen() -> None:
    assert "识图未启用" in VISION_DOWNGRADE_NOTICE
    assert "时间" in VISION_DOWNGRADE_NOTICE or "张数" in VISION_DOWNGRADE_NOTICE


def test_vision_warmup_delay_inject(monkeypatch) -> None:
    monkeypatch.setenv("TRAVELOGUE_SFC_VISION_WARMUP_DELAY_MS", "50")
    t0 = time.monotonic()
    slept = maybe_sleep_vision_warmup_inject()
    elapsed = time.monotonic() - t0
    assert slept >= 0.04
    assert elapsed >= 0.04


def test_vision_warmup_delay_inject_noop_without_env(monkeypatch) -> None:
    monkeypatch.delenv("TRAVELOGUE_SFC_VISION_WARMUP_DELAY_MS", raising=False)
    assert maybe_sleep_vision_warmup_inject() == 0.0
