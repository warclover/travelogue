"""Near-scene clone penalty · avoids fake sliced mosaics on prefers_burst:false."""

from __future__ import annotations

import pytest

from travelogue.layout_engine.mosaic.scorer import (
    _near_scene_clone_penalty,
    _template_prefers_burst,
)


@pytest.mark.unit
def test_rail_and_weighted_prefer_burst_false() -> None:
    assert _template_prefers_burst("screen-mosaic-4-1l3p-rail") is False
    assert _template_prefers_burst("screen-mosaic-4-2l2p-weighted") is False
    assert _template_prefers_burst("screen-mosaic-5-main-portrait-3land") is False


@pytest.mark.unit
def test_candidates_hard_reject_near_scene_on_weighted() -> None:
    from travelogue.config import get_config
    from travelogue.layout_engine.mosaic.candidates import (
        generate_window_candidates_with_rejections,
    )

    assets = {
        "a0": {
            "id": "a0",
            "takenAt": "2025-04-20T22:00:00Z",
            "tags": ["person", "face"],
            "width": 1600,
            "height": 900,
        },
        "a1": {
            "id": "a1",
            "takenAt": "2025-04-20T22:01:00Z",
            "tags": ["person", "face"],
            "width": 900,
            "height": 1600,
        },
        "a2": {
            "id": "a2",
            "takenAt": "2025-04-20T22:02:00Z",
            "tags": ["person", "face"],
            "width": 900,
            "height": 1600,
        },
        "a3": {
            "id": "a3",
            "takenAt": "2025-04-20T22:03:00Z",
            "tags": ["person", "face"],
            "width": 1600,
            "height": 900,
        },
    }
    aspects = {
        "a0": "landscape",
        "a1": "portrait",
        "a2": "portrait",
        "a3": "landscape",
    }
    cfg = get_config().mosaic
    res = generate_window_candidates_with_rejections(
        list(assets), aspects, assets, cfg=cfg
    )
    assert not any(
        c.pattern_id == "screen-mosaic-4-2l2p-weighted" for c in res.candidates
    )
    assert any(
        r.get("templateId") == "screen-mosaic-4-2l2p-weighted"
        and r.get("reason") == "near_scene_clone"
        for r in res.rejected
    )


@pytest.mark.unit
def test_near_scene_person_burst_penalized_on_weighted() -> None:
    assets = {
        f"a{i}": {
            "id": f"a{i}",
            "takenAt": f"2025-04-20T22:0{i}:00Z",
            "tags": ["person", "face"],
        }
        for i in range(4)
    }
    # span ≈ 3 minutes, all people → high penalty
    pen = _near_scene_clone_penalty(
        "screen-mosaic-4-2l2p-weighted",
        list(assets),
        assets,
    )
    assert pen >= 0.85


@pytest.mark.unit
def test_near_scene_12min_person_walk_rejected_on_rail() -> None:
    """demo-2025 rail used 12-min same-outfit walk → fake 切条拼图."""
    assets = {
        "a0": {"id": "a0", "takenAt": "2025-04-20T22:13:40Z", "tags": ["person", "face"]},
        "a1": {"id": "a1", "takenAt": "2025-04-20T22:17:25Z", "tags": ["person", "face"]},
        "a2": {"id": "a2", "takenAt": "2025-04-20T22:21:05Z", "tags": ["person", "face"]},
        "a3": {"id": "a3", "takenAt": "2025-04-20T22:25:17Z", "tags": ["person", "face"]},
    }
    pen = _near_scene_clone_penalty(
        "screen-mosaic-4-1l3p-rail",
        list(assets),
        assets,
    )
    assert pen >= 0.75


@pytest.mark.unit
def test_prefers_burst_true_skips_near_scene_penalty() -> None:
    assets = {
        f"a{i}": {
            "id": f"a{i}",
            "takenAt": f"2025-04-20T22:0{i}:00Z",
            "tags": ["person"],
        }
        for i in range(4)
    }
    pen = _near_scene_clone_penalty(
        "screen-mosaic-4-hero-70-sidebar",
        list(assets),
        assets,
    )
    assert pen == 0.0


@pytest.mark.unit
def test_rail_v2_stacked_geometry_in_yaml() -> None:
    from travelogue.layout_templates.registry import get_engine

    tpl = get_engine().get("screen-mosaic-4-1l3p-rail")
    assert list(tpl.stage.cols) == [5, 1]
    assert list(tpl.stage.rows) == [1, 1, 1]
    main = tpl.slots[0]
    assert main.role == "landscape"
    assert list(main.rect) == [1, 1, 1, 3]
