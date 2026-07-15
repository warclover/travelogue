"""Windows single-instance mutex + instance state file (ADR-018 D4)."""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from travelogue.paths import is_frozen, user_data_dir

_log = logging.getLogger(__name__)

MUTEX_NAME = "Local\\TravelogueStudio"
STATE_FILENAME = "studio-instance.json"

# Win32 constants
_ERROR_ALREADY_EXISTS = 183
_WAIT_OBJECT_0 = 0
_WAIT_TIMEOUT = 258
_INFINITE = 0xFFFFFFFF


@dataclass
class InstanceState:
    pid: int
    port: int
    url: str
    host: str
    started_at: float

    def to_dict(self) -> dict:
        return {
            "pid": self.pid,
            "port": self.port,
            "url": self.url,
            "host": self.host,
            "startedAt": self.started_at,
        }

    @classmethod
    def from_dict(cls, raw: dict) -> InstanceState | None:
        try:
            return cls(
                pid=int(raw["pid"]),
                port=int(raw["port"]),
                url=str(raw["url"]),
                host=str(raw.get("host") or "127.0.0.1"),
                started_at=float(raw.get("startedAt") or 0),
            )
        except (KeyError, TypeError, ValueError):
            return None


@dataclass
class SingleInstanceHandle:
    owned: bool
    mutex_handle: int | None = None
    state_path: Path | None = None


def instance_state_path() -> Path:
    return user_data_dir() / STATE_FILENAME


def read_instance_state() -> InstanceState | None:
    path = instance_state_path()
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    return InstanceState.from_dict(raw)


def write_instance_state(state: InstanceState) -> Path:
    path = instance_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def clear_instance_state() -> None:
    path = instance_state_path()
    try:
        path.unlink(missing_ok=True)
    except OSError:
        _log.debug("failed to clear instance state", exc_info=True)


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(  # type: ignore[attr-defined]
            PROCESS_QUERY_LIMITED_INFORMATION, False, pid
        )
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)  # type: ignore[attr-defined]
            return True
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def try_acquire_single_instance() -> SingleInstanceHandle:
    """Acquire the desktop single-instance mutex when frozen on Windows.

    Non-frozen / non-Windows: always ``owned=True`` (no mutex).
    """
    state_path = instance_state_path()
    if not (is_frozen() and sys.platform == "win32"):
        return SingleInstanceHandle(owned=True, state_path=state_path)

    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
    kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if not handle:
        _log.warning("CreateMutexW failed; continuing without single-instance guard")
        return SingleInstanceHandle(owned=True, state_path=state_path)

    already = ctypes.GetLastError() == _ERROR_ALREADY_EXISTS
    if already:
        # Another process holds it — do not keep a duplicate handle that would
        # also own the mutex after the other exits.
        kernel32.CloseHandle(handle)
        return SingleInstanceHandle(owned=False, mutex_handle=None, state_path=state_path)

    return SingleInstanceHandle(owned=True, mutex_handle=int(handle), state_path=state_path)


def release_single_instance(handle: SingleInstanceHandle | None) -> None:
    if handle is None:
        return
    clear_instance_state()
    if handle.mutex_handle and sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.kernel32.CloseHandle(handle.mutex_handle)  # type: ignore[attr-defined]
        except Exception:
            _log.debug("CloseHandle mutex failed", exc_info=True)


def open_existing_instance_or_stale() -> InstanceState | None:
    """Return live instance state, or clear stale state and return None."""
    state = read_instance_state()
    if state is None:
        return None
    if _pid_alive(state.pid):
        return state
    clear_instance_state()
    return None


def record_running_instance(*, host: str, port: int) -> InstanceState:
    state = InstanceState(
        pid=os.getpid(),
        port=port,
        url=f"http://{host}:{port}/",
        host=host,
        started_at=time.time(),
    )
    write_instance_state(state)
    return state
