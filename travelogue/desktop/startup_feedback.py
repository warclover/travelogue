"""Windowed startup failure UX (T-0c-09 / F-INS-FIRST-04).

When console=False, users never see stderr. Surface a MessageBox (Windows)
or stderr line (dev) that points at the log file and feedback SOP.
"""

from __future__ import annotations

import sys
from pathlib import Path


def format_startup_failure_message(
    *,
    detail: str,
    log_path: Path | None,
) -> str:
    detail_s = (detail or "").strip() or "未知错误"
    # Keep MessageBox readable; full traceback stays in the log.
    if len(detail_s) > 400:
        detail_s = detail_s[:397] + "..."
    lines = [
        "Travelogue Studio 无法完成启动。",
        "",
        detail_s,
        "",
    ]
    if log_path is not None:
        lines.append(f"日志文件：{log_path}")
        lines.append("反馈问题时请附上该日志（发送前请确认不含隐私内容）。")
    else:
        lines.append("未能写入日志文件；请检查磁盘权限后重试。")
    lines.append("")
    lines.append("反馈入口见邀请说明 / 使用说明中的唯一反馈渠道。")
    return "\n".join(lines)


def show_startup_failure(*, detail: str, log_path: Path | None) -> None:
    """Show a blocking failure dialog on Windows; otherwise print to stderr."""
    text = format_startup_failure_message(detail=detail, log_path=log_path)
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(  # type: ignore[attr-defined]
                0,
                text,
                "Travelogue Studio",
                0x00000010,  # MB_ICONERROR
            )
            return
        except Exception:
            pass
    try:
        sys.stderr.write(text + "\n")
        sys.stderr.flush()
    except Exception:
        pass
