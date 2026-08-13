"""AEL L0 isolation — AC-AEL-01/02/03/09/17/21/24. Sequence ruler, not PNG hash."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from travelogue.config.album_editorial import album_editorial_lab_from_dict
from travelogue.config.app import AppConfig
from travelogue.export.collage_pack import collage_plan_fingerprint, export_collage_pack
from travelogue.export.longshot import EXPORT_OUTPUT_DIRNAME
from travelogue.services.trip_factory import create_trip

pytestmark = pytest.mark.unit

_REPO = Path(__file__).resolve().parents[3]


def _make_rgb(path: Path, *, size: tuple[int, int] = (800, 600), color=(40, 120, 200)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, format="JPEG", quality=90)


def _seed_kept_photos(trip_dir: Path, n: int) -> None:
    trip_json = trip_dir / "trip.json"
    data = json.loads(trip_json.read_text(encoding="utf-8"))
    assets = []
    ids: list[str] = []
    for i in range(n):
        aid = f"ael-l0-{i:02d}"
        ids.append(aid)
        rel = f"source/{aid}.jpg"
        size = (900, 600) if i % 2 == 0 else (600, 900)
        _make_rgb(trip_dir / rel, size=size, color=(30 + i * 10, 80, 160))
        assets.append(
            {
                "id": aid,
                "type": "image",
                "sourceFile": rel,
                "layoutEligible": True,
            }
        )
    data["assets"] = assets
    curation = data.setdefault("curation", {})
    curation["displayedAssetIds"] = ids
    cull = curation.setdefault("cullSummary", {})
    cull["layoutEligibleCount"] = n
    cull["finalLayoutEligibleCount"] = n
    trip_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _new_trip(tmp_path: Path, name: str, n: int = 8) -> Path:
    trips = tmp_path / "trips"
    create_trip(name, trips, title=name)
    trip_dir = trips / name
    _seed_kept_photos(trip_dir, n)
    return trip_dir


def _ael_cfg(*, enabled: bool, crop: bool = False) -> AppConfig:
    return AppConfig(
        album_editorial_lab=album_editorial_lab_from_dict(
            {"enabled": enabled, "crop": {"enabled": crop}}
        )
    )


def _capture_fingerprint(monkeypatch: pytest.MonkeyPatch, attr: str) -> list[tuple]:
    import travelogue.export.collage_pack as pack

    captured: list[tuple] = []
    orig = getattr(pack, attr)

    def _wrap(*args: object, **kwargs: object):
        plans = orig(*args, **kwargs)
        captured.append(collage_plan_fingerprint(plans))
        return plans

    monkeypatch.setattr(pack, attr, _wrap)
    return captured


def test_album_parent_off_matches_no_cfg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    trip_dir = _new_trip(tmp_path, "ael-off")
    captured = _capture_fingerprint(monkeypatch, "plan_cards")
    export_collage_pack(trip_dir, platform="album_spread")
    export_collage_pack(trip_dir, platform="album_spread", cfg=_ael_cfg(enabled=False))
    assert len(captured) == 2
    assert captured[0] == captured[1]
    assert not (trip_dir / EXPORT_OUTPUT_DIRNAME / "ael.json").exists()


def test_album_parent_on_children_off_same_sequence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    trip_dir = _new_trip(tmp_path, "ael-parent")
    captured = _capture_fingerprint(monkeypatch, "plan_cards")
    export_collage_pack(trip_dir, platform="album_spread")
    export_collage_pack(trip_dir, platform="album_spread", cfg=_ael_cfg(enabled=True))
    assert captured[0] == captured[1]
    diag = json.loads(
        (trip_dir / EXPORT_OUTPUT_DIRNAME / "ael.json").read_text(encoding="utf-8")
    )
    assert diag["aelEnabled"] is True
    assert diag["crop"] is False
    assert diag["roles"] is False
    assert diag["probes"] is False
    assert diag["probeCount"] == 0
    assert diag["templateIds"] == captured[1][0]
    assert diag["slotOrientations"] == captured[1][1]


def test_album_crop_flag_l0_does_not_change_sequence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """L1 not wired: crop.enabled must not change template id / slot orientation."""
    trip_dir = _new_trip(tmp_path, "ael-crop")
    captured = _capture_fingerprint(monkeypatch, "plan_cards")
    export_collage_pack(trip_dir, platform="album_spread")
    export_collage_pack(
        trip_dir, platform="album_spread", cfg=_ael_cfg(enabled=True, crop=True)
    )
    assert captured[0] == captured[1]


def test_xhs_ignores_ael_parent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    trip_dir = _new_trip(tmp_path, "ael-xhs")
    captured = _capture_fingerprint(monkeypatch, "plan_cards_for_feed")
    export_collage_pack(trip_dir, platform="xiaohongshu")
    export_collage_pack(
        trip_dir, platform="xiaohongshu", cfg=_ael_cfg(enabled=True, crop=True)
    )
    assert captured[0] == captured[1]
    assert not (trip_dir / EXPORT_OUTPUT_DIRNAME / "ael.json").exists()


def test_mp_ignores_ael_parent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    trip_dir = _new_trip(tmp_path, "ael-mp")
    captured = _capture_fingerprint(monkeypatch, "plan_cards_for_feed")
    export_collage_pack(trip_dir, platform="wechat_official")
    export_collage_pack(
        trip_dir, platform="wechat_official", cfg=_ael_cfg(enabled=True)
    )
    assert captured[0] == captured[1]


def test_longshot_passes_cfg_into_album_pack(tmp_path: Path) -> None:
    from travelogue.export.longshot import LongshotExportResult, export_trip_longshot

    trip_dir = _new_trip(tmp_path, "ael-longshot")
    sentinel = LongshotExportResult(platform="album_spread", capture_method="collage_pages")
    with patch("travelogue.export.collage_pack.export_collage_pack", return_value=sentinel) as mock_pack:
        result = export_trip_longshot(trip_dir, platform="album_spread")
    assert result is sentinel
    assert mock_pack.called
    assert "cfg" in mock_pack.call_args.kwargs


def test_export_panel_has_no_ael_copy() -> None:
    panel = _REPO / "templates" / "studio" / "js" / "longshot-export-panel.js"
    text = panel.read_text(encoding="utf-8")
    assert "album_editorial" not in text
    assert "album_editorial_lab" not in text
    assert "PROBE_TEMPLATES" not in text


def test_l0_does_not_import_llm_or_enable_msa() -> None:
    import travelogue.export.collage_pack as pack

    src = Path(pack.__file__).read_text(encoding="utf-8")
    assert "travelogue.llm" not in src
    assert "travelogue.ai" not in src
    assert "slot_adaptation" not in src
    assert "layout_engine.mosaic" not in src
