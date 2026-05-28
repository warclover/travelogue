"""Subprocess entry: pick a folder on the process main thread (stdout JSON)."""

from __future__ import annotations

import json
import sys

from travelogue.desktop.folder_dialog import pick_folder


def _configure_utf8_stdio() -> None:
    """Force UTF-8 on stdout/stderr so non-ASCII paths survive on Windows."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8")
            except (OSError, ValueError):
                pass


def main() -> None:
    _configure_utf8_stdio()
    title = sys.argv[1] if len(sys.argv) > 1 else "选择照片文件夹"
    try:
        chosen = pick_folder(title=title)
        payload = {"path": str(chosen.resolve()) if chosen else None}
    except Exception as exc:
        payload = {"path": None, "error": str(exc)}
        sys.stdout.write(json.dumps(payload, ensure_ascii=False))
        sys.stdout.flush()
        raise SystemExit(1) from exc
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
