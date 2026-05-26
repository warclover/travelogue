"""Backfill contentSig and color metrics without deprecation noise."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _load_backfill_module():
    path = ROOT / "scripts" / "backfill_content_sig.py"
    spec = importlib.util.spec_from_file_location("backfill_content_sig", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_backfill_content_sig_writes_signatures(tmp_path: Path) -> None:
    mod = _load_backfill_module()
    trip_dir = tmp_path / "trips" / "sig-trip"
    source_dir = trip_dir / "source"
    source_dir.mkdir(parents=True)
    img_path = source_dir / "asset-001.jpg"
    Image.new("RGB", (800, 600), (40, 80, 120)).save(img_path, quality=95)
    trip = {
        "tripId": "sig-trip",
        "assets": [
            {
                "id": "asset-001",
                "type": "image",
                "sourceFile": "source/asset-001.jpg",
            }
        ],
    }
    trip_path = trip_dir / "trip.json"
    trip_path.write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")

    result = mod.backfill_trip(trip_path)
    assert result["updated"] == 1
    saved = json.loads(trip_path.read_text(encoding="utf-8"))
    sig = saved["assets"][0].get("contentSig")
    assert sig
    assert ":" in sig
    from travelogue.media.ingest import content_signature

    assert sig == content_signature(img_path)


def test_color_metrics_no_getdata_deprecation() -> None:
    import warnings

    from travelogue.media.color_metrics import dominant_tone_hex, mean_luma

    img = Image.new("RGB", (64, 64), (100, 120, 140))
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        luma = mean_luma(img)
        tone = dominant_tone_hex(img)
    assert not any("getdata" in str(w.message).lower() for w in record)
    assert 0.0 <= luma <= 1.0
    assert tone.startswith("#")
