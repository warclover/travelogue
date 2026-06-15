#!/usr/bin/env python3
"""Build HetangYuese woff2 subsets for cover trip titles.

Source (first match):
  1. --source path
  2. templates/studio/assets/fonts/hetangyuese-source.ttf
  3. npm package @fontpkg/hetangyuese (auto-downloaded to a temp dir)

Output:
  templates/visual-journal/assets/fonts/hetangyuese.woff2
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "templates" / "studio" / "assets" / "fonts" / "hetangyuese-source.ttf"
OUT_DIR = ROOT / "templates" / "visual-journal" / "assets" / "fonts"
OUT_FILE = OUT_DIR / "hetangyuese.woff2"
NPM_FONT_PACKAGE = "@fontpkg/hetangyuese"

# Studio H1 + common trip-title / place-name characters (PRD title ≤20 chars).
DEFAULT_CHARS = (
    "每一个瞬间，都值得再次相遇"
    "0123456789"
    " ·—－-"
    "林芝东澳岛京都鸭川旅行游记春夏秋冬天地南北"
    "省市县区镇村河湖海山林岛礁湾港城路街巷"
    "甲乙丙丁子丑寅卯辰巳午未申酉戌亥"
    "的二三四五六七八九十百千万"
    "纪行记游散步行摄风光人文记忆"
)


def _collect_chars(extra: str) -> str:
    seen: set[str] = set()
    ordered: list[str] = []
    for ch in DEFAULT_CHARS + extra:
        if ch not in seen:
            seen.add(ch)
            ordered.append(ch)
    return "".join(ordered)


def _resolve_source_ttf(explicit: Path | None) -> Path:
    if explicit and explicit.is_file():
        return explicit
    if DEFAULT_SOURCE.is_file():
        return DEFAULT_SOURCE
    tmp = Path(tempfile.mkdtemp(prefix="hetangyuese-npm-"))
    try:
        subprocess.run(
            ["npm", "pack", NPM_FONT_PACKAGE],
            cwd=tmp,
            check=True,
            capture_output=True,
        )
        archive = next(tmp.glob("fontpkg-hetangyuese-*.tgz"))
        extract_dir = tmp / "pkg"
        extract_dir.mkdir()
        subprocess.run(
            ["tar", "-xzf", str(archive), "-C", str(extract_dir)],
            check=True,
        )
        package_dir = extract_dir / "package"
        ttf = next(package_dir.glob("*.ttf"), None)
        if ttf is None:
            raise FileNotFoundError(f"no .ttf in {NPM_FONT_PACKAGE}")
        dest = DEFAULT_SOURCE
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ttf, dest)
        print("Cached source TTF →", dest)
        return dest
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help=f"Full hetangyuese TTF (default: {DEFAULT_SOURCE} or npm)",
    )
    parser.add_argument(
        "--extra-chars",
        default="",
        help="Additional Unicode characters to include in the subset",
    )
    args = parser.parse_args()

    try:
        source = _resolve_source_ttf(args.source)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(
            f"E_FONT: could not resolve hetangyuese TTF ({exc})\n"
            f"Install Node/npm or place TTF at {DEFAULT_SOURCE}",
            file=sys.stderr,
        )
        return 1

    text = _collect_chars(args.extra_chars)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "fontTools.subset",
        str(source),
        f"--output-file={OUT_FILE}",
        f"--text={text}",
        "--flavor=woff2",
        "--layout-features=*",
        "--glyph-names",
        "--symbol-cmap",
        "--legacy-cmap",
        "--notdef-glyph",
        "--notdef-outline",
        "--recommended-glyphs",
        "--name-IDs=*",
        "--name-legacy",
        "--name-languages=*",
    ]
    print("Subsetting", len(text), "unique chars →", OUT_FILE)
    subprocess.run(cmd, check=True)
    print("OK", OUT_FILE, f"({OUT_FILE.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
