"""Generate P17 layout golden fixtures (portrait ×2, landscape ×2)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "clustering"


def _segment_assets(
    prefix: str,
    *,
    portrait: bool,
    city: str,
    day: int,
    lat: float,
    lon: float,
    subject: str,
) -> list[dict]:
    assets: list[dict] = []
    for i in range(6):
        w, h = (900, 1600) if portrait else (2000, 1200)
        assets.append(
            {
                "id": f"{prefix}{chr(ord('a') + i)}",
                "type": "image",
                "takenAt": f"2025-06-{day:02d}T{9 + i}:00:00Z",
                "geo": {"lat": round(lat + i * 0.001, 4), "lon": round(lon + i * 0.001, 4)},
                "place": {"city": city},
                "width": w,
                "height": h,
                "sharpness": round(0.58 + i * 0.02, 2),
                "meanLuma": round(0.5 + i * 0.02, 2),
                "dominantTone": "warm" if portrait else "cool",
                "subjectBucket": subject,
            }
        )
    return assets


def _write_fixture(
    trip_id: str,
    *,
    description: str,
    segments: list[dict],
    portrait: bool,
) -> None:
    root = FIXTURES / trip_id
    root.mkdir(parents=True, exist_ok=True)
    all_assets: list[dict] = []
    golden_segments: list[dict] = []
    for seg in segments:
        assets = _segment_assets(
            seg["prefix"],
            portrait=portrait,
            city=seg["city"],
            day=seg["day"],
            lat=seg["lat"],
            lon=seg["lon"],
            subject=seg["subject"],
        )
        all_assets.extend(assets)
        golden_segments.append(
            {
                "id": seg["evt_id"],
                "name": seg["city"],
                "startDate": f"2025-06-{seg['day']:02d}",
                "endDate": f"2025-06-{seg['day']:02d}",
                "location": seg["city"],
                "assetIds": [a["id"] for a in assets],
            }
        )
    manifest = {"description": description, "assets": all_assets}
    (root / "assets-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (root / "segments-golden.json").write_text(
        json.dumps(golden_segments, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    readme = f"""# {trip_id}

{description}

- **类别**：{"人像竖图" if portrait else "风景横图"}
- **资产数**：{len(all_assets)}
- **用途**：P17 受控 parity / golden probe（§10.3）
"""
    (root / "README.md").write_text(readme, encoding="utf-8")
    print(f"wrote {trip_id} ({len(all_assets)} assets)")


def main() -> int:
    portrait_specs = [
        (
            "golden-portrait-family",
            "CI golden · 家庭人像竖图（3 日 × 6P）",
            [
                {"prefix": "f1", "city": "上海", "day": 1, "lat": 31.23, "lon": 121.47, "subject": "portrait", "evt_id": "evt-sh-family-d1"},
                {"prefix": "f2", "city": "杭州", "day": 3, "lat": 30.25, "lon": 120.17, "subject": "portrait", "evt_id": "evt-hz-family-d3"},
                {"prefix": "f3", "city": "苏州", "day": 5, "lat": 31.30, "lon": 120.62, "subject": "portrait", "evt_id": "evt-sz-family-d5"},
            ],
        ),
        (
            "golden-portrait-travel",
            "CI golden · 旅行自拍竖图（3 日 × 6P）",
            [
                {"prefix": "t1", "city": "成都", "day": 2, "lat": 30.57, "lon": 104.07, "subject": "person", "evt_id": "evt-cd-travel-d2"},
                {"prefix": "t2", "city": "丽江", "day": 4, "lat": 26.86, "lon": 100.23, "subject": "person", "evt_id": "evt-lj-travel-d4"},
                {"prefix": "t3", "city": "大理", "day": 6, "lat": 25.59, "lon": 100.23, "subject": "person", "evt_id": "evt-dl-travel-d6"},
            ],
        ),
    ]
    landscape_specs = [
        (
            "golden-landscape-coast",
            "CI golden · 海岸风景横图（3 日 × 6L）",
            [
                {"prefix": "c1", "city": "三亚", "day": 7, "lat": 18.25, "lon": 109.51, "subject": "landscape", "evt_id": "evt-sy-coast-d7"},
                {"prefix": "c2", "city": "厦门", "day": 9, "lat": 24.48, "lon": 118.09, "subject": "landscape", "evt_id": "evt-xm-coast-d9"},
                {"prefix": "c3", "city": "青岛", "day": 11, "lat": 36.07, "lon": 120.38, "subject": "landscape", "evt_id": "evt-qd-coast-d11"},
            ],
        ),
        (
            "golden-landscape-mountain",
            "CI golden · 山地风景横图（3 日 × 6L）",
            [
                {"prefix": "m1", "city": "林芝", "day": 8, "lat": 29.65, "lon": 94.36, "subject": "scenery", "evt_id": "evt-lz-mountain-d8"},
                {"prefix": "m2", "city": "稻城", "day": 10, "lat": 29.04, "lon": 100.30, "subject": "scenery", "evt_id": "evt-dc-mountain-d10"},
                {"prefix": "m3", "city": "喀纳斯", "day": 12, "lat": 48.70, "lon": 87.00, "subject": "scenery", "evt_id": "evt-kns-mountain-d12"},
            ],
        ),
    ]
    for trip_id, desc, segs in portrait_specs:
        _write_fixture(trip_id, description=desc, segments=segs, portrait=True)
    for trip_id, desc, segs in landscape_specs:
        _write_fixture(trip_id, description=desc, segments=segs, portrait=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
