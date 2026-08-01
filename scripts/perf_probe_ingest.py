"""One-off perf probe: per-step ingest cost on real photos (research only)."""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from travelogue.media.color_metrics import color_metrics_from_thumb
from travelogue.media.image_ops import (
    export_webp_variants,
    load_image_normalized,
    save_jpeg_without_exif,
)
from travelogue.media.phash import dhash_hex
from travelogue.media.sharpness import sharpness_score, sharpness_score_v2
from travelogue.media.subject_detect import analyze_subject


def probe(photo: Path, out_dir: Path) -> dict:
    t = {}

    t0 = time.perf_counter()
    loaded = load_image_normalized(photo)
    img = loaded.image
    t["decode"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    _ = sharpness_score(img)
    t["sharpness_v1"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    _ = dhash_hex(img)
    t["dhash"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    subj = analyze_subject(img, min_face_size=48, face_detect_max_edge=0, enabled=True)
    t["faces_fullres"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    _ = analyze_subject(img, min_face_size=48, face_detect_max_edge=1024, enabled=True)
    t["faces_1024"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    _ = sharpness_score_v2(img, roi=subj.salient_box if subj.salient_box else None)
    t["sharpness_v2"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    _ = color_metrics_from_thumb(img, thumb_px=32)
    t["color"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    export_webp_variants(
        img, out_dir, "probe",
        widths=(800, 1600, 2400, 3200), quality=82, webp_method=4,
        generate_crops=False, focal=(0.5, 0.45),
    )
    t["webp_4x_m4"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    export_webp_variants(
        img, out_dir, "probe2",
        widths=(800, 1600, 2400, 3200), quality=82, webp_method=0,
        generate_crops=False, focal=(0.5, 0.45),
    )
    t["webp_4x_m0"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    save_jpeg_without_exif(img, out_dir / "probe.jpg")
    t["jpeg_copy_q92_opt"] = time.perf_counter() - t0

    t["size"] = f"{img.width}x{img.height}"
    return t


def main() -> None:
    album = Path(sys.argv[1])
    photos = sorted(album.glob("*.JPG"))[:3] or sorted(album.glob("*.jpg"))[:3]
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        for p in photos:
            r = probe(p, out)
            print(p.name, json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}))


if __name__ == "__main__":
    main()
