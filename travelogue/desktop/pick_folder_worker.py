"""Subprocess entry: pick a folder on the process main thread (stdout JSON)."""

from __future__ import annotations

import json
import sys

from travelogue.desktop.folder_dialog import pick_folder


def main() -> None:
    title = sys.argv[1] if len(sys.argv) > 1 else "选择照片文件夹"
    chosen = pick_folder(title=title)
    payload = {"path": str(chosen.resolve()) if chosen else None}
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
