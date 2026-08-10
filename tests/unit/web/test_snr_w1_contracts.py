"""Share Narrative Readiness · W1 源码契约（AC-SNR-01/03/05）。"""

from __future__ import annotations

from pathlib import Path

from travelogue.domain.share_face_copy import is_unsafe_share_copy, sanitize_share_copy
from travelogue.render.context import alt_text
from travelogue.render.moment_exif import format_moment_exif_line
from travelogue.web.studio_entry import build_entry

ROOT = Path(__file__).resolve().parents[3]
STUDIO = ROOT / "templates" / "studio"


def test_snr_w1_entry_includes_narrative_posture() -> None:
    entry = build_entry(
        {"meta": {}, "chapters": []},
        "demo",
        ai_surface_enabled=False,
        llm_ready=False,
    )
    assert entry["narrativePosture"] == "photo_led"

    ready = build_entry(
        {"meta": {"hook": "湖风里的一天", "title": "周末"}, "chapters": []},
        "demo",
        ai_surface_enabled=True,
        llm_ready=True,
    )
    assert ready["narrativePosture"] == "narrative_ready"

    upgrade = build_entry(
        {"meta": {}, "chapters": [{"lead": ""}]},
        "demo",
        ai_surface_enabled=True,
        llm_ready=True,
    )
    assert upgrade["narrativePosture"] == "upgrade_ready"


def test_snr_w1_bans_travel_photo_caption_and_alt() -> None:
    from travelogue.domain.share_face_copy import resolve_visible_caption

    assert is_unsafe_share_copy("旅行照片", kind="caption")
    assert is_unsafe_share_copy("旅行照片", kind="alt")
    assert sanitize_share_copy("旅行照片", kind="caption") == ""
    # SNR · 空 caption 时 alt 回退中性「照片」，仍禁「旅行照片」
    assert "旅行照片" not in alt_text(None, {}, "题名")
    assert resolve_visible_caption("旅行照片", kind="caption") == ""
    assert resolve_visible_caption("旅行照片", kind="alt", asset={}) == "照片"


def test_snr_w1_year_outlier_uses_wangnian_copy() -> None:
    line = format_moment_exif_line(
        {
            "takenAt": "2015-07-08T15:00:00",
            "place": {"city": "珞珈山"},
        },
        trip_primary_year=2024,
    )
    assert line is not None
    assert "2015" not in line
    assert "往年" in line
    assert "下午" in line


def test_snr_w1_posture_bar_mounted_and_copy() -> None:
    js = (STUDIO / "preview-toolbar" / "narrative-posture.js").read_text(encoding="utf-8")
    css = (STUDIO / "preview-toolbar" / "narrative-posture.css").read_text(
        encoding="utf-8"
    )
    agg = (STUDIO / "preview-toolbar.css").read_text(encoding="utf-8")
    init = (STUDIO / "preview-toolbar" / "init-v3.js").read_text(encoding="utf-8")
    assert "mountNarrativePostureBar" in js
    assert "纯照片成册" in js
    assert "可生成杂志感文案" in js
    assert "生成杂志感文案" in js
    assert 'focus: "narrate"' in js
    assert "narrative-posture.css" in agg
    assert "mountNarrativePostureBar" in init
    assert "preview-toolbar__posture-bar" in css
