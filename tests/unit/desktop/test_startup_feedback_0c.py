"""Unit tests for windowed startup failure UX (T-0c-09)."""

from __future__ import annotations

from pathlib import Path

from travelogue.desktop.startup_feedback import format_startup_failure_message


def test_format_includes_log_path(tmp_path: Path) -> None:
    log = tmp_path / "logs" / "studio.log"
    text = format_startup_failure_message(detail="无法绑定端口", log_path=log)
    assert "无法绑定端口" in text
    assert str(log) in text
    assert "反馈" in text


def test_format_without_log() -> None:
    text = format_startup_failure_message(detail="boom", log_path=None)
    assert "boom" in text
    assert "未能写入日志" in text
