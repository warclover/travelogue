"""Folder picker via subprocess (reliable while Studio serves HTTP)."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path

from travelogue.paths import is_frozen

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


def _picker_command(title: str, *, out_path: Path | None) -> list[str]:
    """Build argv for the folder-picker worker.

    Frozen builds must not rely on ``python -m`` (ADR-018 D5). Windowed exe
    also often breaks stdout pipes, so frozen mode always uses ``--out``.
    """
    if is_frozen():
        cmd = [sys.executable, "--pick-folder-worker"]
        if out_path is not None:
            cmd.append(f"--out={out_path}")
        cmd.append(title)
        return cmd
    cmd = [sys.executable, "-m", "travelogue.desktop.pick_folder_worker"]
    if out_path is not None:
        cmd.append(f"--out={out_path}")
    cmd.append(title)
    return cmd


def _parse_worker_payload(raw: str) -> dict | None:
    """Parse worker JSON; tolerate native libs that print warnings to stdout."""
    text = (raw or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    # Prefer the last JSON object line (worker payload is one object).
    for line in reversed(text.splitlines()):
        line = line.strip()
        if not (line.startswith("{") and line.endswith("}")):
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
    start = text.rfind("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
        if isinstance(data, dict):
            return data
    return None


def request_folder(*, title: str = "选择照片文件夹", timeout: float = 600.0) -> FolderPickResult:
    """Spawn a short-lived process so the dialog runs on its main thread."""
    if sys.platform != "win32":
        return FolderPickResult(error="unsupported_platform")
    with _pick_lock:
        out_file: Path | None = None
        proc: subprocess.CompletedProcess[str] | None = None
        try:
            # Always use --out: worker imports can print native warnings to
            # stdout (e.g. "[WARNING] Ignore caches…"), which breaks JSON parse
            # when the parent only reads pipes.
            fd, name = tempfile.mkstemp(prefix="travelogue-pick-", suffix=".json")
            os.close(fd)
            out_file = Path(name)
            # Force UTF-8 decode: worker writes UTF-8 JSON (ensure_ascii=False),
            # but Windows default codepage (e.g. cp936) would mangle non-ASCII paths.
            proc = subprocess.run(
                _picker_command(title, out_path=out_file),
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
            if out_file is not None:
                out_file.unlink(missing_ok=True)
            return FolderPickResult(error="picker_timeout")
        except OSError as exc:
            log.warning("pick_folder_worker failed to start: %s", exc)
            if out_file is not None:
                out_file.unlink(missing_ok=True)
            return FolderPickResult(error=str(exc))

        raw = ""
        try:
            if out_file is not None and out_file.is_file():
                raw = out_file.read_text(encoding="utf-8").strip()
        except OSError as exc:
            log.warning("pick_folder_worker out file read failed: %s", exc)
        finally:
            if out_file is not None:
                try:
                    out_file.unlink(missing_ok=True)
                except OSError:
                    pass
        if not raw and proc is not None:
            raw = (proc.stdout or "").strip()

        if proc is not None and proc.returncode != 0 and not raw:
            err = (proc.stderr or proc.stdout or "").strip()
            log.warning("pick_folder_worker exit=%s stderr=%r", proc.returncode, err)
            return FolderPickResult(error=err or f"picker_exit_{proc.returncode}")
        if not raw:
            log.warning("pick_folder_worker returned empty stdout")
            return FolderPickResult(error="picker_empty_response")
        data = _parse_worker_payload(raw)
        if data is None:
            log.warning("pick_folder_worker invalid JSON: %r", raw[:200])
            return FolderPickResult(error="picker_invalid_response")
        path = data.get("path")
        if data.get("error"):
            return FolderPickResult(error=str(data["error"]))
        if not path:
            return FolderPickResult(cancelled=True)
        return FolderPickResult(path=Path(path))
