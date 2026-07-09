"""M-C5 · split studio-home-v2.css into partials + @import entry (G-WIP-02)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "templates" / "studio" / "studio-home-v2.css"
OUT_DIR = ROOT / "templates" / "studio" / "homepage-v2" / "css"

SECTIONS: list[tuple[str, int, int | None, str]] = [
    ("tokens.css", 1, 407, "Font + theme tokens + base html/body"),
    ("base.css", 408, 440, "Hidden utility, skip link, offline banner"),
    ("bento.css", 441, 1078, "Bento shell, loading, headline, grid, carousel frame"),
    ("carousel.css", 1079, 1251, "Carousel 16:9"),
    ("phone.css", 1252, 1444, "Phone preview + vertical scroll"),
    ("bench.css", 1445, 2078, "Bench + settings panel portaled styles"),
    ("shelf.css", 2079, 2299, "Web shelf revisit zone"),
    ("theme-classic.css", 2300, 2587, "Theme classic dark fallback"),
    ("import-sheet.css", 2588, 2967, "Import sheet + form controls"),
    ("import-wizard.css", 2968, 3385, "Import Wizard v3 dialog"),
    ("overlays.css", 3386, 3705, "Import scrim, importing, success, failed"),
    ("chrome.css", 3706, 3938, "Lightbox, unsupported, responsive, reduced motion"),
    ("dev-panel.css", 3939, None, "Dev harness panel"),
]

ENTRY_HEADER = """\
/**
 * Travelogue Studio · homepage v2 styles (M-C5 @import aggregate).
 * URL unchanged: /__studio/studio-home-v2.css
 */
"""


def _slice_lines(lines: list[str], start: int, end: int | None) -> list[str]:
    return lines[start - 1 : len(lines) if end is None else end]


def main() -> None:
    if not SRC.is_file():
        raise SystemExit(f"missing {SRC}")
    text = SRC.read_text(encoding="utf-8")
    if text.lstrip().startswith("@import"):
        print("studio-home-v2.css already split")
        return

    lines = text.splitlines(keepends=True)
    if not lines[-1].endswith("\n"):
        lines[-1] += "\n"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rebuilt: list[str] = []

    for name, start, end, desc in SECTIONS:
        chunk_lines = _slice_lines(lines, start, end)
        chunk = "".join(chunk_lines)
        header = f"/* Homepage v2 · {desc} */\n"
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
        f'@import url("homepage-v2/css/{name}");' for name, _, _, _ in SECTIONS
    )
    SRC.write_text(ENTRY_HEADER + imports + "\n", encoding="utf-8")
    print(f"Patched entry {SRC.relative_to(ROOT)} ({len(SECTIONS)} imports)")


if __name__ == "__main__":
    main()
