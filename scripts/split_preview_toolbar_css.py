"""M-C5 · split preview-toolbar.css into partials + @import entry."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "templates" / "studio" / "preview-toolbar.css"
OUT_DIR = ROOT / "templates" / "studio" / "preview-toolbar"

SECTIONS: list[tuple[str, int, int | None, str]] = [
    ("tokens.css", 1, 18, "Design tokens"),
    ("shell.css", 19, 347, "Base chrome · FAB hide, reader, controls, mode seg"),
    ("longshot.css", 348, 982, "Longshot export · popover, effects, pending, result"),
    ("legacy-bar.css", 983, 1065, "Legacy bar · title, menu, featured"),
    ("drawers.css", 1066, 1461, "Overlay drawers · edit, structure"),
    ("modal-chrome.css", 1462, 1496, "Studio modal preview chrome"),
    ("cohort.css", 1497, 1650, "Cohort seed picker"),
    ("v3-bar.css", 1651, 1906, "Preview toolbar v3 bar"),
    ("dock.css", 1907, 2237, "Preview toolbar v4 icon dock"),
    ("inline-edit.css", 2238, 2288, "Cover title inline edit"),
    ("task-dock.css", 2289, 2392, "Preview task dock"),
    ("sheet.css", 2393, None, "Unified settings sheet"),
]

ENTRY_HEADER = """\
/**
 * Travelogue Studio · preview toolbar styles (M-C5 @import aggregate).
 * URL unchanged: /__studio/preview-toolbar.css
 */
"""


def _slice_lines(lines: list[str], start: int, end: int | None) -> list[str]:
    start_i = start - 1
    end_i = len(lines) if end is None else end
    return lines[start_i:end_i]


def main() -> None:
    if not SRC.is_file():
        raise SystemExit(f"missing {SRC}")

    text = SRC.read_text(encoding="utf-8")
    if text.lstrip().startswith("@import"):
        print("preview-toolbar.css already split")
        return

    lines = text.splitlines(keepends=True)
    if not lines[-1].endswith("\n"):
        lines[-1] += "\n"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rebuilt: list[str] = []

    for name, start, end, desc in SECTIONS:
        chunk_lines = _slice_lines(lines, start, end)
        chunk = "".join(chunk_lines)
        header = f"/* Preview toolbar · {desc} */\n"
        out_path = OUT_DIR / name
        out_path.write_text(header + chunk, encoding="utf-8")
        rebuilt.append(chunk)
        print(f"Wrote {out_path.relative_to(ROOT)} ({len(chunk_lines)} lines)")

    joined = "".join(rebuilt)
    if joined != text:
        raise SystemExit(
            f"split verification failed: rebuilt {len(joined)} chars vs src {len(text)}"
        )

    imports = "\n".join(
        f'@import url("preview-toolbar/{name}");' for name, _, _, _ in SECTIONS
    )
    SRC.write_text(ENTRY_HEADER + imports + "\n", encoding="utf-8")
    print(f"Patched entry {SRC.relative_to(ROOT)} ({len(SECTIONS)} imports)")


if __name__ == "__main__":
    main()
