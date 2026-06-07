#!/usr/bin/env python3
"""Evaluate collage detector against labeled fixtures (PRD §3.4 · 议题F)."""

from __future__ import annotations

import argparse
import json
from io import BytesIO
from pathlib import Path

from PIL import Image

from travelogue.curation.media_classify import classify_media_class, detect_collage_asset

DEFAULT_FIXTURES = Path("docs/acceptance-records/collage-detect-fixtures.json")
DEFAULT_FIXTURES_ROOT = Path("tests/fixtures/collage")


def _build_image(spec: dict) -> Image.Image:
    kind = spec.get("kind")
    if kind == "file":
        rel = str(spec.get("path") or "")
        path = Path(rel)
        if not path.is_file():
            path = DEFAULT_FIXTURES_ROOT / rel
        if not path.is_file():
            raise FileNotFoundError(f"collage fixture file not found: {rel}")
        return Image.open(path).convert("RGB")
    if kind == "exif":
        w, h = 1200, 1200
        img = Image.new("RGB", (w, h), color=(128, 128, 128))
        exif = img.getexif()
        from PIL.ExifTags import Base

        exif[Base.Software] = str(spec.get("software") or "")
        buf = BytesIO()
        img.save(buf, format="JPEG", exif=exif)
        buf.seek(0)
        return Image.open(buf)
    if kind == "grid_collage":
        size = spec.get("size") or [1000, 1000]
        w, h = int(size[0]), int(size[1])
        panels = spec.get("panels")
        img = Image.new("RGB", (w, h), color=(40, 40, 40))
        px = img.load()
        if isinstance(panels, list) and len(panels) >= 2 and panels[0] == 3 and panels[1] == 1:
            third = w // 3
            for x in range(w):
                for y in range(h):
                    if abs(x - third) < 4 or abs(x - 2 * third) < 4:
                        px[x, y] = (240, 240, 240)
                    else:
                        panel = 0 if x < third - 3 else (1 if x < 2 * third - 3 else 2)
                        base = [(180, 120, 90), (90, 140, 180), (140, 180, 90)][panel]
                        px[x, y] = base
            return img
        if isinstance(panels, list) and len(panels) >= 2 and panels[0] == 2 and panels[1] == 1:
            mid = w // 2
            for x in range(w):
                for y in range(h):
                    panel = 0 if x < mid - 3 else 1
                    base = (180, 120, 90) if panel == 0 else (90, 140, 180)
                    if abs(x - mid) < 4:
                        px[x, y] = (240, 240, 240)
                    else:
                        px[x, y] = base
            return img
        for x in range(w):
            for y in range(h):
                panel_x = 0 if x < w // 2 - 5 else 1
                panel_y = 0 if y < h // 2 - 5 else 1
                base = (180, 120, 90) if (panel_x + panel_y) % 2 == 0 else (90, 140, 180)
                if abs(x - w // 2) < 4 or abs(y - h // 2) < 4:
                    px[x, y] = (240, 240, 240)
                else:
                    px[x, y] = base
        return img
    size = spec.get("size") or [1200, 800]
    color = spec.get("color") or [128, 128, 128]
    return Image.new("RGB", (int(size[0]), int(size[1])), color=tuple(color))


def evaluate_fixtures(fixtures_path: Path) -> dict:
    fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))
    rows: list[dict] = []
    tp = fp = tn = fn = 0
    for spec in fixtures:
        img = _build_image(spec)
        path = Path(f"{spec['id']}.jpg")
        detected = detect_collage_asset(path=path, img=img, asset={})
        classified = classify_media_class(path=path, img=img, date_source="exif")
        expect = str(spec.get("expect") or "photo")
        predicted = "collage" if detected or classified == "collage" else "photo"
        ok = predicted == expect
        if expect == "collage" and predicted == "collage":
            tp += 1
        elif expect == "collage" and predicted != "collage":
            fn += 1
        elif expect != "collage" and predicted == "collage":
            fp += 1
        else:
            tn += 1
        rows.append(
            {
                "id": spec["id"],
                "expect": expect,
                "predicted": predicted,
                "detectCollage": detected,
                "mediaClass": classified,
                "ok": ok,
            }
        )
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    return {
        "fixtureCount": len(rows),
        "accuracy": round(sum(1 for r in rows if r["ok"]) / len(rows), 4) if rows else 0.0,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "confusion": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Collage detector fixture eval")
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument("--min-recall", type=float, default=0.5)
    parser.add_argument("--max-fp-rate", type=float, default=0.2)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    report = evaluate_fixtures(args.fixtures)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    fp_rate = report["confusion"]["fp"] / max(1, report["confusion"]["fp"] + report["confusion"]["tn"])
    if args.strict and (report["recall"] < args.min_recall or fp_rate > args.max_fp_rate):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
