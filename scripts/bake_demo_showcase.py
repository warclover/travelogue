"""Bake demo-showcase WebPs from trips/demo-album (homepage Bento samples)."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TRIP = ROOT / "trips" / "demo-album"
OUT = ROOT / "templates" / "studio" / "assets" / "demo-showcase"
TITLE = "斯里兰卡见闻录"


def _load_trip() -> dict:
    return json.loads((TRIP / "trip.json").read_text(encoding="utf-8"))


def _asset_path(trip: dict, asset_id: str) -> Path:
    assets = {a["id"]: a for a in trip.get("assets") or []}
    a = assets[asset_id]
    rel = str(a.get("displayFile") or "").replace("\\", "/")
    if not rel:
        raise KeyError(asset_id)
    return TRIP / rel


def _open_rgb(path: Path) -> Image.Image:
    im = Image.open(path)
    if im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    elif im.mode == "L":
        im = im.convert("RGB")
    return im


def _cover_crop(im: Image.Image, tw: int, th: int) -> Image.Image:
    """Center-crop to target aspect, then resize."""
    sw, sh = im.size
    target = tw / th
    src = sw / sh
    if src > target:
        nw = int(sh * target)
        left = (sw - nw) // 2
        im = im.crop((left, 0, left + nw, sh))
    else:
        nh = int(sw / target)
        top = (sh - nh) // 2
        im = im.crop((0, top, sw, top + nh))
    return im.resize((tw, th), Image.Resampling.LANCZOS)


def _save_webp(im: Image.Image, path: Path, *, quality: int = 78) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, format="WEBP", quality=quality, method=4)


def _pick_ids(trip: dict) -> dict[str, str]:
    cover = str(trip.get("coverAssetId") or "")
    chapters = trip.get("chapters") or []
    heroes: list[str] = []
    for ch in chapters:
        hid = (ch.get("curation") or {}).get("heroAssetId") or ch.get("heroAssetId")
        if hid:
            heroes.append(str(hid))
    assets = [a for a in trip.get("assets") or [] if a.get("type", "image") == "image"]
    landscapes = [
        str(a["id"])
        for a in assets
        if a.get("aspectKind") in ("landscape", "panorama")
    ]
    portraits = [
        str(a["id"])
        for a in assets
        if a.get("aspectKind") in ("portrait", "tall")
    ]

    def uniq(seq: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for x in seq:
            if x and x not in seen:
                seen.add(x)
                out.append(x)
        return out

    land = uniq([cover] + heroes + landscapes)
    port = uniq(portraits + land)

    while len(land) < 5:
        land.append(land[-1] if land else cover)
    while len(port) < 5:
        port.append(port[-1] if port else cover)

    return {
        "cover": land[0],
        "ch01": land[1],
        "ch02": land[2],
        "ch03": land[3],
        "epilogue": land[4],
        "longshot": port[:6],
    }


def main() -> None:
    trip = _load_trip()
    picks = _pick_ids(trip)
    scroll = OUT / "scroll"

    # Phone longshot · stacked 9:16 frames (cap 4 for size budget)
    frames: list[Image.Image] = []
    for aid in picks["longshot"][:4]:
        frames.append(_cover_crop(_open_rgb(_asset_path(trip, aid)), 432, 768))
    long_h = sum(f.height for f in frames)
    longshot = Image.new("RGB", (432, long_h), (10, 10, 10))
    y = 0
    for f in frames:
        longshot.paste(f, (0, y))
        y += f.height
    _save_webp(longshot, OUT / "longshot.webp", quality=68)

    # Web carousel · 16:9 (slightly smaller for ≤800KB pack)
    web_specs = [
        ("cover", picks["cover"], scroll / "cover.webp", 960, 540),
        ("ch01", picks["ch01"], scroll / "ch01.webp", 960, 540),
        ("ch02", picks["ch02"], scroll / "ch02.webp", 960, 540),
        ("ch03", picks["ch03"], scroll / "ch03.webp", 960, 540),
        ("epilogue", picks["epilogue"], scroll / "epilogue.webp", 960, 540),
    ]
    for _name, aid, dest, w, h in web_specs:
        im = _cover_crop(_open_rgb(_asset_path(trip, aid)), w, h)
        _save_webp(im, dest, quality=72)

    # Background · reuse cover 16:9 (homepage veil)
    bg = _cover_crop(_open_rgb(_asset_path(trip, picks["cover"])), 960, 540)
    _save_webp(bg, OUT / "background.webp", quality=70)

    photo_count = sum(
        1 for a in trip.get("assets") or [] if a.get("type", "image") == "image"
    )
    chapter_count = len(trip.get("chapters") or [])
    manifest = {
        "version": "2026.07.28-sri-lanka-bake",
        "title": TITLE,
        "meta": {
            "photoCount": photo_count,
            "chapterCount": chapter_count,
            "subtitle": f"{photo_count} PHOTOS · DEMO",
        },
        "assets": {
            "background": "background.webp",
            "longshot": "longshot.webp",
        },
        "longshotPages": [
            {
                "id": "longshot",
                "label": "微信长图",
                "url": "longshot.webp",
                "scrollPreview": True,
            }
        ],
        "pages": [
            {"id": "cover", "role": "cover", "label": "封面", "webp": "scroll/cover.webp"},
            {
                "id": "ch01",
                "role": "chapter",
                "label": "第一章",
                "chapterIndex": 1,
                "webp": "scroll/ch01.webp",
            },
            {
                "id": "ch02",
                "role": "chapter",
                "label": "第二章",
                "chapterIndex": 2,
                "webp": "scroll/ch02.webp",
            },
            {
                "id": "ch03",
                "role": "chapter",
                "label": "第三章",
                "chapterIndex": 3,
                "webp": "scroll/ch03.webp",
            },
            {
                "id": "epilogue",
                "role": "epilogue",
                "label": "尾声",
                "webp": "scroll/epilogue.webp",
            },
        ],
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    total = sum(p.stat().st_size for p in OUT.rglob("*.webp"))
    print(f"baked {TITLE} · {photo_count} photos · showcase={total/1024:.0f}KB")
    for p in sorted(OUT.rglob("*.webp")):
        im = Image.open(p)
        print(f"  {p.relative_to(OUT)} {im.size} {p.stat().st_size/1024:.1f}KB")


if __name__ == "__main__":
    main()
