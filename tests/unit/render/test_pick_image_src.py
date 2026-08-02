"""pick_image_src prefers mid-tier srcset over largest displayFile."""

from __future__ import annotations

from travelogue.render.context import compile_srcset, pick_image_sizes, pick_image_src


def test_pick_image_src_prefers_w1600_over_display_w3200() -> None:
    asset = {
        "displayFile": "assets/a-w3200.webp",
        "srcset": [
            {"file": "assets/a-w800.webp", "width": 800},
            {"file": "assets/a-w1600.webp", "width": 1600},
            {"file": "assets/a-w2400.webp", "width": 2400},
            {"file": "assets/a-w3200.webp", "width": 3200},
        ],
    }
    assert pick_image_src(asset, export_layout="web") == "assets/a-w1600.webp"
    assert pick_image_src(asset, export_layout="auto") == "assets/a-w1600.webp"


def test_pick_image_src_falls_back_to_display_without_srcset() -> None:
    asset = {"displayFile": "assets/a-w3200.webp"}
    assert pick_image_src(asset) == "assets/a-w3200.webp"


def test_web_sizes_cap_below_3200() -> None:
    cover = pick_image_sizes("web", "cover")
    screen = pick_image_sizes("web", "screen_full")
    assert "3200px" not in cover
    assert "3200px" not in screen
    assert "2200px" not in cover
    assert "1800px" in cover
    assert "1800px" in screen


def test_compile_srcset_excludes_w3200_to_prevent_retina_oom() -> None:
    """sizes×DPR can still request ≥3200; omit that candidate from HTML srcset."""
    asset = {
        "srcset": [
            {"file": "assets/a-w800.webp", "width": 800},
            {"file": "assets/a-w1600.webp", "width": 1600},
            {"file": "assets/a-w2400.webp", "width": 2400},
            {"file": "assets/a-w3200.webp", "width": 3200},
        ],
    }
    srcset = compile_srcset(asset)
    assert "3200w" not in srcset
    assert "w3200" not in srcset
    assert "2400w" in srcset
    assert "1600w" in srcset
    assert "800w" in srcset
