"""Folder picker via subprocess (reliable while Studio serves HTTP)."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)
_pick_lock = threading.Lock()


@dataclass
class FolderPickResult:
    path: Path | None = None
    cancelled: bool = False
    error: str | None = None


def start_folder_picker_service() -> None:
    """Compatibility no-op; subprocess picker needs no background thread."""


def stop_folder_picker_service() -> None:
    """Compatibility no-op."""


def request_folder(*, title: str = "选择照片文件夹", timeout: float = 600.0) -> FolderPickResult:
    """Spawn a short-lived process so the dialog runs on its main thread."""
    if sys.platform != "win32":
        return FolderPickResult(error="unsupported_platform")
    with _pick_lock:
        try:
            # Force UTF-8 decode: worker writes UTF-8 JSON (ensure_ascii=False),
            # but Windows default codepage (e.g. cp936) would mangle non-ASCII paths.
            proc = subprocess.run(
                [sys.executable, "-m", "travelogue.desktop.pick_folder_worker", title],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
        except subprocess.TimeoutExpired:
            log.warning("pick_folder_worker timed out after %.0fs", timeout)
            return FolderPickResult(error="picker_timeout")
        except OSError as exc:
            log.warning("pick_folder_worker failed to start: %s", exc)
            return FolderPickResult(error=str(exc))
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        log.warning("pick_folder_worker exit=%s stderr=%r", proc.returncode, err)
        return FolderPickResult(error=err or f"picker_exit_{proc.returncode}")
    raw = (proc.stdout or "").strip()
    if not raw:
        log.warning("pick_folder_worker returned empty stdout")
        return FolderPickResult(error="picker_empty_response")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        log.warning("pick_folder_worker invalid JSON: %r", raw[:200])
        return FolderPickResult(error="picker_invalid_response")
    path = data.get("path")
    if data.get("error"):
        return FolderPickResult(error=str(data["error"]))
    if not path:
        return FolderPickResult(cancelled=True)
    return FolderPickResult(path=Path(path))
