"""PyInstaller entry point: Travelogue Studio exe."""

from __future__ import annotations

import logging
import sys
from pathlib import Path


def _setup_early_file_logging() -> Path | None:
    """Attach a file logger as early as possible (windowed builds have no console).

    M-INS-0a: always log next to the exe under ``logs/``. M-INS-0b will route
    install-mode logs to LocalAppData while keeping portable ``./logs/``.
    """
    frozen = bool(getattr(sys, "frozen", False))
    if frozen:
        base = Path(sys.executable).resolve().parent
    else:
        # Dev runs via ``python -m travelogue.desktop.launcher`` — keep optional file log
        # under cwd so windowed-path debugging still has a place to look.
        base = Path.cwd()

    log_dir = base / "logs"
    try:
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

        logging.getLogger(__name__).info(
            "Travelogue Studio starting (frozen=%s) log=%s", frozen, log_path
        )
        return log_path
    except OSError as exc:
        # Last resort: cannot create log dir (read-only media). Continue without file log.
        try:
            sys.stderr.write(f"studio log setup failed: {exc}\n")
        except Exception:
            pass
        return None


def main() -> None:
    _setup_early_file_logging()
    # Desktop / packaged Studio: allow local folder-picker albums by default.
    # Operators can still set TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM=0 to lock down.
    from travelogue.web.studio_handlers.import_handlers import ensure_studio_trust_local_album

    ensure_studio_trust_local_album()
    if len(sys.argv) == 1:
        sys.argv.append("studio")
    from travelogue.cli import app

    app()


if __name__ == "__main__":
    main()
