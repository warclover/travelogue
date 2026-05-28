"""Folder picker via subprocess (reliable while Studio serves HTTP)."""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import threading
from pathlib import Path

log = logging.getLogger(__name__)
_pick_lock = threading.Lock()


def start_folder_picker_service() -> None:
    """Compatibility no-op; subprocess picker needs no background thread."""


def stop_folder_picker_service() -> None:
    """Compatibility no-op."""


def request_folder(*, title: str = "选择照片文件夹", timeout: float = 600.0) -> Path | None:
    """Spawn a short-lived process so the dialog runs on its main thread."""
    if sys.platform != "win32":
        return None
    with _pick_lock:
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "travelogue.desktop.pick_folder_worker", title],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            log.debug("pick_folder_worker timed out after %.0fs", timeout)
            return None
        except OSError as exc:
            log.debug("pick_folder_worker failed to start: %s", exc)
            return None
    if proc.returncode != 0:
        log.debug(
            "pick_folder_worker exit=%s stderr=%r",
            proc.returncode,
            (proc.stderr or "").strip(),
        )
        return None
    raw = (proc.stdout or "").strip()
    if not raw:
        log.debug("pick_folder_worker returned empty stdout")
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        log.debug("pick_folder_worker invalid JSON: %r", raw[:200])
        return None
    path = data.get("path")
    if not path:
        return None
    return Path(path)
