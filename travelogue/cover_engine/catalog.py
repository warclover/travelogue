"""V6 cover style catalog + V5 legacy aliases (PRD §4 / §3.1)."""

from __future__ import annotations

from travelogue.cover_engine.registry import register_style
from travelogue.cover_engine.types import CoverStyleProfile, CoverStyleRecord

# Fixture paths relative to repo (preview matrix / AC hooks).
_FIXTURE_DEMO = "docs/wireframes/cover-styles-v6-hi-fi-adefg.html"

_LEGACY_MAP: dict[str, str] = {
    "card-br": "veil-footer",
    "split-mat": "folio-overlap",
    "magazine-head": "folio-overlap",
}


def legacy_map_table() -> dict[str, str]:
    return dict(_LEGACY_MAP)


def bootstrap_catalog() -> None:
    """Register V6 active styles. Idempotent via register overwrite."""
    styles = (
        CoverStyleRecord(
            id="veil-footer",
            label="雾底题签",
            studio_label="沉浸题签",
            status="active",
            sort_order=10,
            studio_blurb="适合主体偏上、下半可暗的大场面，像电影开场。",
            preview_fixtures=(_FIXTURE_DEMO,),
            profile=CoverStyleProfile(
                prefer={"focal_y_max": 0.55, "mood": "cinematic"},
                avoid={"subject_bottom": True, "high_luma_lower": True},
                text_safe_regions=[{"x": 0.0, "y": 0.52, "w": 0.74, "h": 0.48}],
                title_max_lines=2,
            ),
            legacy_aliases=("card-br",),
        ),
        CoverStyleRecord(
            id="folio-overlap",
            label="对页叠印",
            status="active",
            sort_order=20,
            studio_blurb="适合右侧有景、左侧可留白的照片，标题会压在画面上。",
            preview_fixtures=(_FIXTURE_DEMO,),
            profile=CoverStyleProfile(
                prefer={"right_weighted": True},
                avoid={"subject_left_30": True},
                text_safe_regions=[{"x": 0.0, "y": 0.45, "w": 0.54, "h": 0.55}],
                title_max_lines=2,
            ),
            legacy_aliases=("split-mat", "magazine-head"),
        ),
        CoverStyleRecord(
            id="band-cut",
            label="切带题名",
            status="active",
            sort_order=30,
            studio_blurb="适合风景与有天空分界的照片；题带偏下，人物请勿落在画面下部。",
            preview_fixtures=(_FIXTURE_DEMO,),
            profile=CoverStyleProfile(
                prefer={"horizon": True, "upper_scene": True},
                avoid={"band_safe_zone": [0.66, 0.78]},
                text_safe_regions=[{"x": 0.0, "y": 0.66, "w": 1.0, "h": 0.12}],
                title_max_lines=2,
            ),
        ),
        CoverStyleRecord(
            id="cameo-aperture",
            label="圆窗肖像",
            status="active",
            sort_order=40,
            studio_blurb="适合主体居中、可被圆形裁切的一张。",
            preview_fixtures=(_FIXTURE_DEMO,),
            profile=CoverStyleProfile(
                prefer={"center_subject": True},
                avoid={"edge_subject": True, "ultra_wide": True},
                text_safe_regions=[{"x": 0.2, "y": 0.62, "w": 0.6, "h": 0.3}],
                title_max_lines=2,
            ),
        ),
        CoverStyleRecord(
            id="type-monument",
            label="巨字碑",
            studio_label="海报巨字",
            status="active",
            sort_order=50,
            studio_blurb="适合氛围感强、可压暗的底图；书名宜短。",
            preview_fixtures=(_FIXTURE_DEMO,),
            profile=CoverStyleProfile(
                prefer={"texture_mood": True, "short_title": True},
                avoid={"face_must_read": True, "very_light_bg": True},
                text_safe_regions=[{"x": 0.05, "y": 0.2, "w": 0.7, "h": 0.55}],
                title_max_lines=3,
            ),
        ),
    )
    for rec in styles:
        register_style(rec)
