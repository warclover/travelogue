"""PFM ISO-02 / AC-PFM-18 · xhs / album 卡序不读作品集 patternId。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from travelogue.export.collage_pack import collage_plan_fingerprint, export_collage_pack
from travelogue.services.trip_factory import create_trip

pytestmark = [pytest.mark.unit, pytest.mark.pipeline_isolation]


def _make_rgb(path: Path, *, size: tuple[int, int] = (800, 600), color=(40, 120, 200)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, format="JPEG", quality=90)


def _seed_kept_photos(trip_dir: Path, n: int) -> None:
    trip_json = trip_dir / "trip.json"
    data = json.loads(trip_json.read_text(encoding="utf-8"))
    assets = []
    ids: list[str] = []
    for i in range(n):
        aid = f"iso02-{i:02d}"
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
    data["layoutEngine"] = "screens"
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


def _stamp_portfolio_page_screens(trip_dir: Path) -> None:
    trip_json = trip_dir / "trip.json"
    data = json.loads(trip_json.read_text(encoding="utf-8"))
    ids = (data.get("curation") or {}).get("displayedAssetIds") or []
    data["studio"] = {
        "edition": "portfolio",
        "portfolio": {"seriesId": "magazine-16-standard", "pageCount": 16},
    }
    data["chapters"] = [
        {
            "id": "ch-01",
            "screens": [
                {
                    "screenId": "ch-01-sc-01",
                    "patternId": "page-6-grid-land",
                    "slots": [{"assetId": aid, "slot": i, "fit": "cover"} for i, aid in enumerate(ids[:6])],
                }
            ],
        }
    ]
    trip_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _capture_fingerprint(monkeypatch: pytest.MonkeyPatch, attr: str) -> list[tuple]:
    import travelogue.export.collage_pack as pack

    captured: list[tuple] = []
    orig = getattr(pack, attr)

    def _wrap(*args: object, **kwargs: object):
        plans = orig(*args, **kwargs)
        captured.append(collage_plan_fingerprint(plans))
        blob = str(args) + str(kwargs)
        assert "patternId" not in blob
        assert "page-6-grid-land" not in blob
        return plans

    monkeypatch.setattr(pack, attr, _wrap)
    return captured


def test_iso02_xhs_card_sequence_ignores_edition_and_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    journal = _new_trip(tmp_path, "iso02-xhs-j")
    captured = _capture_fingerprint(monkeypatch, "plan_cards_for_feed")
    export_collage_pack(journal, platform="xiaohongshu")
    trip_json = journal / "trip.json"
    data = json.loads(trip_json.read_text(encoding="utf-8"))
    data["studio"] = {"edition": "journal", "portfolio": {"seriesId": "noise"}}
    trip_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    export_collage_pack(journal, platform="xiaohongshu")
    assert len(captured) == 2
    assert captured[0] == captured[1]


def test_iso02_album_card_sequence_ignores_edition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    journal = _new_trip(tmp_path, "iso02-album-j")
    captured = _capture_fingerprint(monkeypatch, "plan_cards")
    export_collage_pack(journal, platform="album_spread")
    trip_json = journal / "trip.json"
    data = json.loads(trip_json.read_text(encoding="utf-8"))
    data["studio"] = {"edition": "journal"}
    trip_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    export_collage_pack(journal, platform="album_spread")
    assert captured[0] == captured[1]


def test_ac_pfm_18_portfolio_xhs_plan_does_not_read_pattern_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """BE-PFM-14 · 作品集 trip 导出 xhs，planner 入参不含 screens[].patternId。"""
    journal = _new_trip(tmp_path, "iso02-xhs-base")
    portfolio = _new_trip(tmp_path, "iso02-xhs-pf")
    _stamp_portfolio_page_screens(portfolio)
    captured = _capture_fingerprint(monkeypatch, "plan_cards_for_feed")
    export_collage_pack(journal, platform="xiaohongshu")
    export_collage_pack(portfolio, platform="xiaohongshu")
    assert captured[0] == captured[1]


def test_iso04_portfolio_wechat_does_not_flatten_page_geometry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ISO-04 · 作品集显式微信群走 kept 池，不拍 5 槽以上 page-* flatten。"""
    from travelogue.export.longshot import export_trip_longshot
    from travelogue.export.portfolio_wechat import list_portfolio_wechat_photo_paths

    portfolio = _new_trip(tmp_path, "iso04-wechat-pf")
    _stamp_portfolio_page_screens(portfolio)
    (portfolio / "index-longshot.html").write_text(
        '<div class="screen page-6-grid-land" data-pattern-id="page-6-grid-land"></div>',
        encoding="utf-8",
    )

    def _forbid_branch_a(*_a, **_k):
        raise AssertionError("ISO-04 must not capture page-* longshot HTML")

    monkeypatch.setattr(
        "travelogue.export.longshot._resolve_longshot_url", _forbid_branch_a
    )
    paths = list_portfolio_wechat_photo_paths(portfolio)
    assert paths
    result = export_trip_longshot(portfolio, platform="wechat_chat")
    assert result.outputs
    name = result.outputs[0].path.name
    assert "长图" in name
    assert "portfolio" not in name
    assert result.capture_method == "kept_stack"
    img = Image.open(result.outputs[0].path)
    assert img.size[0] == 1080
