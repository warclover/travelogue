"""Phase 23 · inline moment EXIF on layout-screen."""

from __future__ import annotations

from dataclasses import replace

from travelogue.config import AppConfig
from travelogue.config.moment import MomentConfig
from travelogue.render.engine import render_html
from travelogue.render.moment_exif import format_moment_exif_line


def _moment_cfg(**kwargs) -> AppConfig:
    moment = MomentConfig(**kwargs)
    return replace(AppConfig(), curate=replace(AppConfig().curate, moment=moment))


def _moment_trip() -> dict:
    return {
        "tripId": "moment-render",
        "title": "最佳时刻",
        "meta": {"title": "最佳时刻", "place": "林芝"},
        "coverAssetId": "cover",
        "momentAssetId": "moment",
        "exportLayout": "web",
        "layoutEngine": "screens",
        "assets": [
            {
                "id": "cover",
                "type": "image",
                "layoutEligible": True,
                "width": 1600,
                "height": 900,
                "paths": {"w800": "assets/cover-w800.webp", "w1600": "assets/cover-w1600.webp"},
            },
            {
                "id": "moment",
                "type": "image",
                "layoutEligible": True,
                "width": 2048,
                "height": 1365,
                "takenAt": "2024-06-14T07:15:00+08:00",
                "place": {"city": "林芝"},
                "exif": {
                    "model": "iPhone 15 Pro",
                    "focalLengthMm": 24,
                    "aperture": 1.8,
                    "shutter": "1/200",
                    "iso": 64,
                },
                "paths": {"w800": "assets/moment-w800.webp", "w1600": "assets/moment-w1600.webp"},
            },
            {
                "id": "closing",
                "type": "image",
                "layoutEligible": True,
                "width": 2048,
                "height": 1365,
                "paths": {"w800": "assets/closing-w800.webp", "w1600": "assets/closing-w1600.webp"},
            },
        ],
        "chapters": [
            {
                "id": "ch-01",
                "title": "第一章",
                "screens": [
                    {"slots": [{"assetId": "cover"}]},
                    {"role": "moment", "patternId": "screen-landscape-1", "slots": [{"assetId": "moment"}]},
                    {"slots": [{"assetId": "closing"}]},
                ],
            }
        ],
        "curation": {
            "momentPoolIds": ["moment"],
            "momentSecondaryIds": [],
            "momentPoolSize": 1,
        },
        "epilogue": "尾声一句",
    }


def test_format_moment_exif_line() -> None:
    trip = _moment_trip()
    asset = next(a for a in trip["assets"] if a["id"] == "moment")
    line = format_moment_exif_line(asset)
    assert line
    assert "林芝" in line


def test_web_render_inline_moment_exif_bar() -> None:
    trip = _moment_trip()
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="default_hybrid",
    )
    assert 'data-block="moment-screen"' not in html
    assert 'data-role="moment"' in html
    assert "moment-exif-bar" in html
    assert "决定性瞬间" in html
    assert "layout-screen__moment-label" in html
    assert "林芝" in html
    assert html.count("moment-exif-bar") == 1
    moment_pos = html.index('data-role="moment"')
    closing_pos = html.index('data-block="cover-closing"')
    assert moment_pos < closing_pos


def _pool_moment_trip() -> dict:
    def asset(aid: str, *, place: str, model: str) -> dict:
        return {
            "id": aid,
            "type": "image",
            "layoutEligible": True,
            "width": 2048,
            "height": 1365,
            "takenAt": "2024-06-14T07:15:00+08:00",
            "place": {"city": place},
            "exif": {
                "model": model,
                "focalLengthMm": 24,
                "aperture": 1.8,
                "shutter": "1/200",
                "iso": 64,
            },
            "paths": {"w800": f"assets/{aid}-w800.webp", "w1600": f"assets/{aid}-w1600.webp"},
        }

    return {
        "tripId": "pool-moment-render",
        "title": "高光池",
        "meta": {"title": "高光池", "place": "林芝"},
        "coverAssetId": "cover",
        "momentAssetId": "sig",
        "exportLayout": "web",
        "layoutEngine": "screens",
        "assets": [
            {
                "id": "cover",
                "type": "image",
                "layoutEligible": True,
                "width": 1600,
                "height": 900,
                "paths": {"w800": "assets/cover-w800.webp", "w1600": "assets/cover-w1600.webp"},
            },
            asset("sig", place="林芝", model="iPhone 15 Pro"),
            asset("peak2", place="波密", model="Sony A7C"),
            {
                "id": "closing",
                "type": "image",
                "layoutEligible": True,
                "width": 2048,
                "height": 1365,
                "paths": {"w800": "assets/closing-w800.webp", "w1600": "assets/closing-w1600.webp"},
            },
        ],
        "chapters": [
            {
                "id": "ch-01",
                "title": "第一章",
                "curation": {"assetIds": ["cover", "sig", "peak2"]},
                "screens": [
                    {"slots": [{"assetId": "cover"}]},
                    {
                        "patternId": "screen-landscape-2",
                        "slots": [{"assetId": "sig"}, {"assetId": "peak2"}],
                    },
                ],
            },
            {
                "id": "ch-02",
                "title": "第二章",
                "screens": [{"slots": [{"assetId": "closing"}]}],
            },
        ],
        "curation": {
            "momentPoolIds": ["sig", "peak2"],
            "momentSecondaryIds": ["peak2"],
            "momentPoolSize": 2,
        },
        "epilogue": "尾声一句",
    }


def test_web_render_pool_exif_bars_and_role_split() -> None:
    trip = _pool_moment_trip()
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="default_hybrid",
    )
    assert html.count("moment-exif-bar") == 2
    assert html.count('data-role="moment"') == 1
    assert html.count('data-role="peak"') == 1
    assert "林芝" in html
    assert "波密" in html
    # BE-FST-04 · 读者面不含相机 Model
    assert "Sony A7C" not in html
    assert "iPhone" not in html
    assert html.count("layout-screen__moment-label") == 1
    assert "决定性瞬间" in html


def test_performance_profile_keeps_pool_solo_without_exif() -> None:
    trip = _pool_moment_trip()
    html = render_html(
        trip,
        export_mode="share",
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="performance",
    )
    assert "moment-exif-bar" not in html
    assert html.count('data-role="moment"') == 1
    assert html.count('data-role="peak"') == 1
    assert 'data-asset-ids="sig,peak2"' not in html
    assert 'data-asset-ids="sig"' in html
    assert 'data-asset-ids="peak2"' in html


def test_pool_exif_false_only_signature_gets_exif() -> None:
    trip = _pool_moment_trip()
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="default_hybrid",
        cfg=_moment_cfg(pool_exif=False),
    )
    assert html.count("moment-exif-bar") == 1
    assert "林芝" in html
    assert "Sony A7C" not in html
    assert html.count('data-role="peak"') == 1


def test_pool_solo_false_only_signature_solo() -> None:
    trip = _pool_moment_trip()
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="default_hybrid",
        cfg=_moment_cfg(pool_solo=False),
    )
    assert 'data-asset-ids="sig,peak2"' not in html
    assert html.count('data-role="moment"') == 1
    assert html.count('data-role="peak"') == 0
    assert 'data-asset-ids="sig"' in html


def test_no_exif_pool_asset_still_solo_without_bar() -> None:
    trip = _pool_moment_trip()
    for asset in trip["assets"]:
        if asset["id"] == "peak2":
            asset.pop("exif", None)
            asset.pop("place", None)
            asset.pop("takenAt", None)
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="default_hybrid",
    )
    assert html.count("moment-exif-bar") == 1
    assert html.count('data-role="peak"') == 1
    assert 'data-asset-ids="peak2"' in html


def test_five_pool_members_all_solo_with_exif() -> None:
    def asset(aid: str) -> dict:
        return {
            "id": aid,
            "type": "image",
            "layoutEligible": True,
            "width": 1600,
            "height": 900,
            "place": {"city": "林芝"},
            "exif": {
                "model": f"Cam-{aid}",
                "focalLengthMm": 35,
                "aperture": 2.8,
                "shutter": "1/250",
                "iso": 100,
            },
            "paths": {"w800": f"assets/{aid}-w800.webp"},
        }

    pool = [f"p{i}" for i in range(1, 6)]
    trip = {
        "tripId": "pool-five",
        "title": "五张池",
        "meta": {"title": "五张池"},
        "coverAssetId": "cover",
        "momentAssetId": "p1",
        "exportLayout": "web",
        "layoutEngine": "screens",
        "assets": [
            {
                "id": "cover",
                "type": "image",
                "layoutEligible": True,
                "width": 1600,
                "height": 900,
                "paths": {"w800": "assets/cover-w800.webp"},
            },
            *[asset(aid) for aid in pool],
            {
                "id": "closing",
                "type": "image",
                "layoutEligible": True,
                "width": 1600,
                "height": 900,
                "paths": {"w800": "assets/closing-w800.webp"},
            },
        ],
        "chapters": [
            {
                "id": "ch-01",
                "curation": {"assetIds": pool},
                "screens": [
                    {
                        "patternId": "screen-landscape-5",
                        "slots": [{"assetId": aid} for aid in pool],
                    }
                ],
            },
            {"id": "ch-02", "screens": [{"slots": [{"assetId": "closing"}]}]},
        ],
        "curation": {
            "momentPoolIds": pool,
            "momentSecondaryIds": pool[1:],
            "momentPoolSize": 5,
        },
        "epilogue": "end",
    }
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="reader_immersive",
    )
    assert html.count("moment-exif-bar") == 5
    assert html.count('data-role="moment"') == 1
    assert html.count('data-role="peak"') == 4
    assert "screen-landscape-5" not in html


def test_signature_label_disabled_hides_moment_role_and_label() -> None:
    trip = _moment_trip()
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="default_hybrid",
        cfg=_moment_cfg(signature_label=False),
    )
    assert 'data-role="moment"' not in html
    assert "layout-screen__moment-label" not in html
    assert "moment-exif-bar" in html


def test_english_locale_moment_label() -> None:
    trip = _moment_trip()
    trip["meta"]["locale"] = "en-US"
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="default_hybrid",
    )
    assert "Moment" in html
    assert "决定性瞬间" not in html
    assert html.count("layout-screen__moment-label") == 1


def test_skipped_moment_has_no_exif_bar() -> None:
    trip = _moment_trip()
    trip["curation"]["momentSkipped"] = "small_trip"
    trip.pop("momentAssetId", None)
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="default_hybrid",
    )
    assert "moment-exif-bar" not in html
