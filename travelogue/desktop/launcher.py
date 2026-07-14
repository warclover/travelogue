"""PyInstaller entry point: Travelogue Studio exe."""

from __future__ import annotations

import logging
import multiprocessing
import sys
from pathlib import Path


def _dispatch_pick_folder_worker() -> bool:
    """Handle ``--pick-folder-worker`` before Typer / file-log stdout redirect."""
    if len(sys.argv) < 2 or sys.argv[1] != "--pick-folder-worker":
        return False
    from travelogue.desktop.pick_folder_worker import main as worker_main

    worker_main(sys.argv[2:])
    return True


def _setup_early_file_logging() -> Path | None:
    """Attach a file logger as early as possible (windowed builds have no console)."""
    from travelogue.paths import is_frozen, logs_dir

    frozen = is_frozen()
    try:
        if frozen:
            from travelogue.paths import ensure_user_data_layout

            ensure_user_data_layout()
            log_dir = logs_dir()
        else:
            log_dir = Path.cwd() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "studio.log"
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        root = logging.getLogger()
        # Root defaults to WARNING; force INFO so startup breadcrumbs are kept.
        root.setLevel(logging.INFO)
        handler.setLevel(logging.INFO)
        already = any(
            isinstance(h, logging.FileHandler)
            and Path(getattr(h, "baseFilename", "")).resolve() == log_path.resolve()
            for h in root.handlers
        )
        if not already:
            root.addHandler(handler)

        if frozen:
            # Capture print / uncaught library stdout in windowed mode.
            class _StreamToLogger:
                def __init__(self, logger: logging.Logger, level: int) -> None:
                    self._logger = logger
                    self._level = level
                    self._buf = ""

                def write(self, message: str) -> int:
                    self._buf += message
                    while "\n" in self._buf:
                        line, self._buf = self._buf.split("\n", 1)
                        line = line.rstrip("\r")
                        if line:
                            self._logger.log(self._level, line)
                    return len(message)

                def flush(self) -> None:
                    if self._buf.strip():
                        self._logger.log(self._level, self._buf.rstrip())
                        self._buf = ""

                def isatty(self) -> bool:
                    return False

            sys.stdout = _StreamToLogger(logging.getLogger("stdout"), logging.INFO)  # type: ignore[assignment]
            sys.stderr = _StreamToLogger(logging.getLogger("stderr"), logging.ERROR)  # type: ignore[assignment]

        from travelogue.paths import is_portable_mode, user_data_dir

        logging.getLogger(__name__).info(
            "Travelogue Studio starting (frozen=%s portable=%s user_data=%s log=%s)",
            frozen,
            is_portable_mode() if frozen else False,
            user_data_dir() if frozen else Path.cwd(),
            log_path,
        )
        return log_path
    except OSError as exc:
        try:
            sys.stderr.write(f"studio log setup failed: {exc}\n")
        except Exception:
            pass
        return None


def main() -> None:
    multiprocessing.freeze_support()
    if _dispatch_pick_folder_worker():
        return
    log_path = _setup_early_file_logging()
    # Desktop / packaged Studio: allow local folder-picker albums by default.
    # Operators can still set TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM=0 to lock down.
    from travelogue.web.studio_handlers.import_handlers import ensure_studio_trust_local_album

    ensure_studio_trust_local_album()
    if len(sys.argv) == 1:
        sys.argv.append("studio")
    from travelogue.cli import app
    from travelogue.desktop.startup_feedback import show_startup_failure
    from travelogue.paths import is_frozen

    try:
        app()
    except SystemExit as exc:
        code = exc.code
        if code in (None, 0):
            raise
        detail = code if isinstance(code, str) else f"进程退出码 {code}"
        if is_frozen():
            show_startup_failure(detail=str(detail), log_path=log_path)
        raise
    except Exception as exc:
        logging.getLogger(__name__).exception("Studio startup failed")
        if is_frozen():
            show_startup_failure(detail=str(exc), log_path=log_path)
        raise


if __name__ == "__main__":
    main()
