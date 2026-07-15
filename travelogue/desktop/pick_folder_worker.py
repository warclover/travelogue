"""Subprocess entry: pick a folder on the process main thread (stdout JSON or --out file)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

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


def _parse_args(argv: list[str]) -> tuple[str, Path | None]:
    """Return (title, optional out_path). Supports ``--out=PATH`` / ``--out PATH``."""
    title = "选择照片文件夹"
    out_path: Path | None = None
    positional: list[str] = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg.startswith("--out="):
            out_path = Path(arg.split("=", 1)[1])
        elif arg == "--out" and i + 1 < len(argv):
            i += 1
            out_path = Path(argv[i])
        elif arg.startswith("-"):
            # Ignore unknown flags so launcher wrappers stay forward-compatible.
            pass
        else:
            positional.append(arg)
        i += 1
    if positional:
        title = positional[0]
    return title, out_path


def main(argv: list[str] | None = None) -> None:
    _configure_utf8_stdio()
    title, out_path = _parse_args(list(argv if argv is not None else sys.argv[1:]))
    try:
        chosen = pick_folder(title=title)
        payload = {"path": str(chosen.resolve()) if chosen else None}
        exit_code = 0
    except Exception as exc:
        payload = {"path": None, "error": str(exc)}
        exit_code = 1

    text = json.dumps(payload, ensure_ascii=False)
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
    else:
        sys.stdout.write(text)
        sys.stdout.flush()
    if exit_code:
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
