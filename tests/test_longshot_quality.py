"""Long-shot quality helpers (mirror longshot.js)."""

from __future__ import annotations

import re
from pathlib import Path


def pick_best_src_for_capture(srcset: str, required_width: int = 428) -> str | None:
    entries: list[tuple[int, str]] = []
    for part in srcset.split(","):
        chunk = part.strip()
        if not chunk:
            continue
        match = re.match(r"^(\S+)\s+(\d+)w$", chunk)
        if match:
            entries.append((int(match.group(2)), match.group(1)))
            continue
        entries.append((0, chunk.split()[0]))
    entries.sort(key=lambda x: x[0])
    if not entries:
        return None
    for w, url in entries:
        if w >= required_width:
            return url
    return entries[-1][1]


def pick_highest_src_from_srcset(srcset: str) -> str | None:
    return pick_best_src_for_capture(srcset, 99999)


def test_pick_highest_src_from_srcset() -> None:
    srcset = (
        "assets/a-w800.webp 800w, "
        "assets/a-w1600.webp 1600w, "
        "assets/a-w2400.webp 2400w"
    )
    assert pick_highest_src_from_srcset(srcset) == "assets/a-w2400.webp"


def test_pick_best_src_for_capture_meets_required_width() -> None:
    srcset = "assets/a-w800.webp 800w, assets/a-w1600.webp 1600w"
    assert pick_best_src_for_capture(srcset, 780) == "assets/a-w800.webp"
    assert pick_best_src_for_capture(srcset, 1170) == "assets/a-w1600.webp"


def test_longshot_js_exports_quality_constants() -> None:
    js = (Path(__file__).resolve().parents[1] / "templates" / "visual-journal" / "longshot.js").read_text(
        encoding="utf-8"
    )
    assert "DESKTOP_CAPTURE_SCALE = 3" in js
    assert "CAPTURE_WIDTH = 428" in js
    assert "MOBILE_CAPTURE_SCALE = 2" in js
    assert "LARGE_TRIP_IMAGES = 45" in js
    assert "SINGLE_PAGE_MAX_IMAGES = 30" in js
    assert "captureLongShotByChapter" in js
    assert "JPEG_QUALITY = 0.96" in js
    assert "getUserSelectedScale" in js
    toolbar = (
        Path(__file__).resolve().parents[1]
        / "templates"
        / "visual-journal"
        / "partials"
        / "longshot-toolbar.hbs"
    ).read_text(encoding="utf-8")
    assert "data-longshot-scale-option" not in toolbar
    assert "openExportPanel" in js
