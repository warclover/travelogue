#!/usr/bin/env python3
"""Dogfood A/B: legacy p2l2 vs screen-editorial-4mix (PRD PR-6)."""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
from pathlib import Path

from travelogue.layout_engine.editorial.four_mix import (
    LAYOUT_HINT_EDITORIAL_4MIX,
    PATTERN_EDITORIAL_4MIX,
)
from travelogue.paths import FIXTURES_DIR
from travelogue.render.compare_editorial_4mix import compare_editorial_4mix
from travelogue.render.dual_layout_regression import prepare_trip_web_screens
from travelogue.render.golden_regression import load_golden_trip

_GOLDEN_FIXTURE = FIXTURES_DIR / "trip.render_golden.json"
_DEMO_ASSETS = Path(__file__).resolve().parents[1] / "templates" / "visual-journal" / "assets"
_PLACEHOLDER_COLORS = (
    (196, 214, 232),
    (214, 196, 176),
    (176, 196, 176),
    (196, 176, 196),
    (176, 188, 214),
    (214, 204, 176),
    (188, 176, 214),
    (176, 214, 204),
)


def _placeholder_size(rel: str) -> tuple[int, int]:
    name = Path(rel).name.lower()
    if "w1600" in name or "1600" in name:
        return (1600, 1067)
    if "w800" in name or "800" in name:
        return (800, 533)
    if "poster" in name:
        return (1280, 720)
    if "scroll" in name:
        return (900, 1400)
    if "umbrella" in name or "station" in name:
        return (1200, 800)
    return (960, 640)


def _write_placeholder_image(path: Path, *, label: str) -> None:
    from PIL import Image, ImageDraw, ImageFont

    width, height = _placeholder_size(path.as_posix())
    color = _PLACEHOLDER_COLORS[hash(label) % len(_PLACEHOLDER_COLORS)]
    img = Image.new("RGB", (width, height), color)
    draw = ImageDraw.Draw(img)
    text = label.replace("assets/demo/", "").replace("-", " ")
    try:
        font = ImageFont.truetype("arial.ttf", size=max(28, width // 28))
    except OSError:
        font = ImageFont.load_default()
    draw.rectangle((0, 0, width - 1, height - 1), outline=(64, 64, 64), width=4)
    draw.text((24, 24), text, fill=(32, 32, 32), font=font)
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix == ".webp":
        img.save(path, "WEBP", quality=82)
    elif suffix in {".jpg", ".jpeg"}:
        img.save(path, "JPEG", quality=85)
    else:
        img.save(path, "PNG")


def _inject_4mix_demo_screen(trip: dict) -> dict:
    """Insert one editorial-4mix screen after the first chapter screen."""
    out = copy.deepcopy(trip)
    screen_4mix = {
        "screenId": "ch-4mix-demo",
        "patternId": PATTERN_EDITORIAL_4MIX,
        "layoutHint": LAYOUT_HINT_EDITORIAL_4MIX,
        "layoutGeometry": {"gridClass": "layout-screen__grid--editorial-4mix"},
        "copy": {
            "kicker": "京都 · 雨后",
            "body": "站台边的风，把霓虹拉得很长。",
        },
        "slots": [
            {"assetId": "asset-001", "slot": 0, "fit": "cover", "role": "landscape"},
            {"assetId": "asset-002", "slot": 1, "fit": "contain", "role": "portrait"},
            {"assetId": "scroll-1", "slot": 2, "fit": "contain", "role": "portrait"},
            {"assetId": "scroll-2", "slot": 3, "fit": "cover", "role": "landscape"},
        ],
    }
    dims = {
        "asset-001": (1600, 900),
        "asset-002": (900, 1600),
        "scroll-1": (800, 1400),
        "scroll-2": (1400, 800),
    }
    for asset in out.get("assets") or []:
        aid = asset.get("id")
        if aid in dims:
            w, h = dims[aid]
            asset["nativeWidth"] = w
            asset["nativeHeight"] = h
            asset["width"] = w
            asset["height"] = h
            asset["layoutEligible"] = True

    for ch in out.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        screens = list(ch.get("screens") or [])
        if not screens:
            continue
        ch["screens"] = [screens[0], screen_4mix, *screens[1:]]
        break
    else:
        out.setdefault("chapters", []).append(
            {
                "id": "ch-4mix",
                "index": 99,
                "title": "4mix",
                "items": [],
                "screens": [screen_4mix],
            }
        )
    out.setdefault("export", {})["editorial4Mix"] = True
    return out


def _stub_asset_files(trip: dict, ws: Path) -> None:
    refs: set[str] = set()
    for asset in trip.get("assets") or []:
        for key in ("displayFile", "sourceFile", "posterFile"):
            if asset.get(key):
                refs.add(str(asset[key]))
        for entry in asset.get("srcset") or []:
            if entry.get("file"):
                refs.add(str(entry["file"]))
        voice = asset.get("voice") or {}
        if voice.get("audioFile"):
            refs.add(str(voice["audioFile"]))
    for rel in sorted(refs):
        path = ws / rel
        if rel.endswith((".webp", ".jpg", ".jpeg", ".png")):
            _write_placeholder_image(path, label=rel)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"")


def _copy_demo_assets(ws: Path) -> None:
    if _DEMO_ASSETS.is_dir() and any(_DEMO_ASSETS.iterdir()):
        shutil.copytree(_DEMO_ASSETS, ws / "assets", dirs_exist_ok=True)
    (ws / "assets" / "demo").mkdir(parents=True, exist_ok=True)
    for name in ("placeholder.m4a", "video.mp4"):
        path = ws / "assets" / "demo" / name
        if not path.is_file():
            path.write_bytes(b"")


def prepare_golden_4mix_demo(out_dir: Path) -> Path:
    """Build 雨后京都 screens trip with one injected 4mix screen."""
    if not _GOLDEN_FIXTURE.is_file():
        raise FileNotFoundError(f"golden fixture missing: {_GOLDEN_FIXTURE}")
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    trip = _inject_4mix_demo_screen(prepare_trip_web_screens(load_golden_trip()))
    trip["meta"]["title"] = "雨后京都 · 4mix A/B"
    trip_file = out_dir / "trip.json"
    trip_file.write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    _copy_demo_assets(out_dir)
    _stub_asset_files(trip, out_dir)
    return trip_file


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render index-editorial-4mix-compare.html (legacy p2l2 vs editorial 4mix)"
    )
    parser.add_argument(
        "trip",
        type=Path,
        nargs="?",
        default=None,
        help="trip.json or trip directory (omit with --golden-demo)",
    )
    parser.add_argument(
        "--golden-demo",
        action="store_true",
        help="build demo workspace from schemas/fixtures/trip.render_golden.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="output directory (default: <trip>/editorial-4mix-compare or trips/demo-editorial-4mix-compare)",
    )
    args = parser.parse_args()

    if args.golden_demo:
        demo_root = Path("trips/demo-editorial-4mix-compare")
        trip_path = prepare_golden_4mix_demo(demo_root)
        compare_dir = args.out or (demo_root / "compare")
    else:
        if args.trip is None:
            print("E_TRIP_REQUIRED: pass trip path or --golden-demo", file=sys.stderr)
            return 1
        trip_path = args.trip
        if trip_path.is_dir():
            trip_path = trip_path / "trip.json"
        if not trip_path.is_file():
            print(f"E_TRIP_NOT_FOUND {trip_path}", file=sys.stderr)
            return 1
        compare_dir = args.out or (trip_path.parent / "editorial-4mix-compare")

    result = compare_editorial_4mix(trip_path, out_dir=compare_dir)
    print(f"OK wrapper   {result.wrapper_html}")
    print(f"OK legacy    {result.legacy_panel}")
    print(f"OK editorial {result.editorial_panel}")
    print(f"URI          {result.wrapper_html.resolve().as_uri()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
