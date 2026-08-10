#!/usr/bin/env python3
"""Share Narrative Readiness · W3 扫描闸（AC-SNR-03/04/12）。

扫描 trips 下：
- 读者面 HTML「旅行照片」
- 脏 displayTitle（noise）
- 序号腔章名
- 裸日期章名占比（对照 AC-SNR-04）
- 可选：对 trip.json 跑薄章名 refresh 后的改善对照

用法::

    python scripts/snr_narrative_readiness_scan.py
    python scripts/snr_narrative_readiness_scan.py --trips-dir trips --refresh-titles
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_SURFACES = (
    "index.html",
    "index-mobile.html",
    "index-longshot.html",
    "present.html",
)
_BARE_DATE_RE = re.compile(
    r"^(?:\d{4}年)?\d{1,2}月\d{1,2}日(?:\s*[–\-—~～]\s*(?:\d{4}年)?\d{1,2}(?:月\d{1,2}日?)?)?$"
)
_YEAR_DOT_RE = re.compile(r"(?:19|20)\d{2}\.\d{2}\.\d{2}")
_TRAVEL_PHOTO = "旅行照片"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _is_bare_date_title(title: str) -> bool:
    t = (title or "").strip()
    if not t:
        return False
    # 有时段/地点分隔则不算「仅裸日期」
    if "·" in t or "•" in t:
        return False
    return bool(_BARE_DATE_RE.match(t))


def scan_trip(
    trip_dir: Path,
    *,
    refresh_titles: bool = False,
) -> dict:
    from travelogue.curation.chapter_titles import (
        is_ordinal_face_title,
        refresh_chapter_titles_on_trip,
    )
    from travelogue.domain.title_humanize import (
        is_folder_title_noise,
        resolve_display_title,
    )

    trip_json = trip_dir / "trip.json"
    data = json.loads(trip_json.read_text(encoding="utf-8"))
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    stored_display = str(meta.get("displayTitle") or "").strip()
    resolved = resolve_display_title(meta)

    chapters = [
        ch
        for ch in (data.get("chapters") or [])
        if isinstance(ch, dict) and not (ch.get("curation") or {}).get("isAppendix")
    ]
    titles = [str(ch.get("title") or "").strip() for ch in chapters]
    ordinals = [t for t in titles if is_ordinal_face_title(t)]
    bare = [t for t in titles if _is_bare_date_title(t)]

    refreshed_bare = bare
    if refresh_titles and chapters:
        import copy

        clone = copy.deepcopy(data)
        refresh_chapter_titles_on_trip(clone)
        r_titles = [
            str(ch.get("title") or "").strip()
            for ch in (clone.get("chapters") or [])
            if isinstance(ch, dict) and not (ch.get("curation") or {}).get("isAppendix")
        ]
        refreshed_bare = [t for t in r_titles if _is_bare_date_title(t)]

    alt_hits = 0
    year_dot_hits = 0
    # 行程 meta 日期行可含起止年（非 C3 离群泄漏）；只计高光/图注类上下文
    _exif_ctx = re.compile(
        r'(?:momentExif|moment-exif|exif-line|trip-meta__line--exif)[^<]{0,120}'
        + _YEAR_DOT_RE.pattern,
        re.I,
    )
    for name in _SURFACES:
        path = trip_dir / name
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        alt_hits += text.count(_TRAVEL_PHOTO)
        year_dot_hits += len(_exif_ctx.findall(text))

    return {
        "tripId": trip_dir.name,
        "chapters": len(chapters),
        "bareDateTitles": len(bare),
        "bareDateTitlesAfterRefresh": len(refreshed_bare),
        "ordinalTitles": len(ordinals),
        "dirtyStoredDisplay": bool(
            stored_display and is_folder_title_noise(stored_display)
        ),
        "resolvedDisplayDirty": bool(resolved and is_folder_title_noise(resolved)),
        "altTravelPhoto": alt_hits,
        "yearDotLeakHtml": year_dot_hits,
        "resolvedDisplay": resolved,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SNR W3 narrative readiness scan")
    parser.add_argument("--trips-dir", type=Path, default=_repo_root() / "trips")
    parser.add_argument("--only", type=str, default="")
    parser.add_argument(
        "--refresh-titles",
        action="store_true",
        help="also compute bare-date counts after thin-title refresh",
    )
    parser.add_argument(
        "--fail-on",
        type=str,
        default="alt,ordinal,dirtyResolved",
        help="comma flags: alt,ordinal,dirtyResolved,dirtyStored,bareRatio",
    )
    args = parser.parse_args(argv)

    trips_dir = args.trips_dir.resolve()
    only = {x.strip() for x in args.only.split(",") if x.strip()}
    fail_flags = {x.strip() for x in args.fail_on.split(",") if x.strip()}

    rows: list[dict] = []
    for child in sorted(trips_dir.iterdir()):
        if not child.is_dir() or child.name.startswith((".", "_")):
            continue
        if only and child.name not in only:
            continue
        if not (child / "trip.json").is_file():
            continue
        rows.append(scan_trip(child, refresh_titles=args.refresh_titles))

    total_ch = sum(r["chapters"] for r in rows)
    total_bare = sum(r["bareDateTitles"] for r in rows)
    total_bare_r = sum(r["bareDateTitlesAfterRefresh"] for r in rows)
    total_ord = sum(r["ordinalTitles"] for r in rows)
    total_alt = sum(r["altTravelPhoto"] for r in rows)
    dirty_resolved = [r["tripId"] for r in rows if r["resolvedDisplayDirty"]]
    dirty_stored = [r["tripId"] for r in rows if r["dirtyStoredDisplay"]]
    bare_ratio = (total_bare / total_ch) if total_ch else 0.0
    bare_ratio_r = (total_bare_r / total_ch) if total_ch else 0.0

    print(f"trips={len(rows)} chapters={total_ch}")
    print(f"bare_date_titles={total_bare} ratio={bare_ratio:.1%}")
    if args.refresh_titles:
        print(
            f"bare_date_after_refresh={total_bare_r} ratio={bare_ratio_r:.1%}"
        )
    print(f"ordinal_titles={total_ord}")
    print(f"alt_旅行照片={total_alt}")
    print(f"year_dot_html_hits={sum(r['yearDotLeakHtml'] for r in rows)}")
    print(f"dirty_resolved_display={len(dirty_resolved)} {dirty_resolved[:8]}")
    print(f"dirty_stored_display={len(dirty_stored)} {dirty_stored[:8]}")

    failed = False
    if "alt" in fail_flags and total_alt:
        failed = True
        print("FAIL alt_旅行照片 > 0")
    if "ordinal" in fail_flags and total_ord:
        failed = True
        print("FAIL ordinal_titles > 0")
    if "dirtyResolved" in fail_flags and dirty_resolved:
        failed = True
        print("FAIL resolved displayTitle still dirty")
    if "dirtyStored" in fail_flags and dirty_stored:
        failed = True
        print("FAIL stored displayTitle still dirty")
    if "bareRatio" in fail_flags and bare_ratio_r > 0.30 and total_ch >= 3:
        failed = True
        print("FAIL bare_date ratio after refresh > 30%")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
