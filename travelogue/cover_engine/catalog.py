"""V6 cover style catalog + V5 legacy aliases (PRD §4 / §3.1).

Art Direction Delta v1.1 (2026-08-02): ten opening styles registered.

2026-08-03: five retired after real-world testing (fit/avoid signals too
weak for precise-composition styles — see cover-engine catalog comments on
each record). Five remain active: veil-footer / folio-overlap / band-cut /
scroll-head / contact-stamp. Retired records stay registered (status=
"retired") so already-generated trips keep rendering unchanged; only the
Studio picker / joint auto-pick stop offering them.
"""

from __future__ import annotations

from travelogue.cover_engine.registry import register_style
from travelogue.cover_engine.types import CoverStyleProfile, CoverStyleRecord

# Fixture paths relative to repo (preview matrix / AC hooks).
_FIXTURE_DEMO = "docs/wireframes/cover-styles-v6-art-direction-v2-wireframe.html"
_FIXTURE_HIFI_LEGACY = "docs/wireframes/cover-styles-v6-hi-fi-adefg.html"

_LEGACY_MAP: dict[str, str] = {
    "card-br": "veil-footer",
    "split-mat": "folio-overlap",
    "magazine-head": "folio-overlap",
}


def legacy_map_table() -> dict[str, str]:
    return dict(_LEGACY_MAP)


def bootstrap_catalog() -> None:
    """Register V6 ten active styles (+ retired legacy aliases). Idempotent via register overwrite."""
    styles = (
        CoverStyleRecord(
            id="veil-footer",
            label="雾底题签",
            studio_label="沉浸题签",
            status="active",
            sort_order=10,
            studio_blurb="适合主体偏上、下半可暗的大场面；暮光雾底，像电影开场。",
            preview_fixtures=(_FIXTURE_DEMO, _FIXTURE_HIFI_LEGACY),
            profile=CoverStyleProfile(
                prefer={"focal_y_max": 0.55, "mood": "cinematic"},
                avoid={"subject_bottom": True, "high_luma_lower": True},
                text_safe_regions=[{"x": 0.0, "y": 0.55, "w": 0.58, "h": 0.45}],
                title_max_lines=2,
            ),
            legacy_aliases=("card-br",),
        ),
        CoverStyleRecord(
            id="folio-overlap",
            label="对页叠印",
            status="active",
            sort_order=20,
            studio_blurb="适合右侧有景、左侧可留白；书名会骑缝切开压进画面。",
            preview_fixtures=(_FIXTURE_DEMO, _FIXTURE_HIFI_LEGACY),
            profile=CoverStyleProfile(
                prefer={"right_weighted": True},
                avoid={"subject_left_30": True},
                text_safe_regions=[
                    {"x": 0.0, "y": 0.0, "w": 0.33, "h": 1.0},
                    {"x": 0.0, "y": 0.58, "w": 0.7, "h": 0.2},
                ],
                title_max_lines=2,
            ),
            legacy_aliases=("split-mat", "magazine-head"),
        ),
        CoverStyleRecord(
            id="band-cut",
            label="切带题名",
            status="active",
            sort_order=30,
            studio_blurb="适合风景与天际线清楚的照片；断带标签偏下，人物勿落在切线附近。",
            preview_fixtures=(_FIXTURE_DEMO, _FIXTURE_HIFI_LEGACY),
            profile=CoverStyleProfile(
                prefer={"horizon": True, "upper_scene": True},
                avoid={"band_safe_zone": [0.58, 0.70]},
                text_safe_regions=[{"x": 0.0, "y": 0.60, "w": 0.55, "h": 0.14}],
                title_max_lines=2,
            ),
        ),
        CoverStyleRecord(
            id="cameo-aperture",
            label="圆窗肖像",
            # 2026-08-03 实测下线：对焦人脸/主体精度要求高，命中率不稳，先退场
            # 不再可分配；已生成的 trip 仍按原样渲染（resolve_style_id 对
            # retired 保持不变）。
            status="retired",
            sort_order=40,
            studio_blurb="适合主体清晰、可落在焦点圆窗内的人像或地标；圆外会虚化。",
            preview_fixtures=(_FIXTURE_DEMO, _FIXTURE_HIFI_LEGACY),
            profile=CoverStyleProfile(
                prefer={"center_subject": True},
                avoid={"edge_subject": True, "ultra_wide": True},
                text_safe_regions=[{"x": 0.72, "y": 0.25, "w": 0.22, "h": 0.5}],
                title_max_lines=2,
            ),
        ),
        CoverStyleRecord(
            id="type-monument",
            label="巨字碑",
            studio_label="海报巨字",
            # 2026-08-03 实测下线：效果不理想，先退场（同 cameo-aperture 备注）。
            status="retired",
            sort_order=50,
            studio_blurb="适合氛围感强、可压暗的底图；书名宜短，字会镂空透出照片。",
            preview_fixtures=(_FIXTURE_DEMO, _FIXTURE_HIFI_LEGACY),
            profile=CoverStyleProfile(
                prefer={"texture_mood": True, "short_title": True},
                avoid={"face_must_read": True, "very_light_bg": True},
                text_safe_regions=[{"x": 0.05, "y": 0.2, "w": 0.9, "h": 0.6}],
                title_max_lines=3,
            ),
        ),
        # —— Art Direction · 扩池五款（与 A/D/E/F/G 一并联合选型 / 哈希分配）——
        CoverStyleRecord(
            id="scroll-head",
            label="卷首竖题",
            status="active",
            sort_order=60,
            studio_blurb="天地留白与竖排书名，偏中式卷首气质。",
            preview_fixtures=(_FIXTURE_DEMO,),
            profile=CoverStyleProfile(
                prefer={"upper_scene": True},
                avoid={"subject_bottom": True, "edge_subject": True},
                text_safe_regions=[{"x": 0.78, "y": 0.08, "w": 0.2, "h": 0.72}],
                title_max_lines=1,
            ),
        ),
        CoverStyleRecord(
            id="portal-arch",
            label="天窗",
            # 2026-08-03 实测下线：拱形取景对准纵深巷道/山径的难度太大，先退场。
            status="retired",
            sort_order=70,
            studio_blurb="拱形取景如推开门；适合有纵深的巷道或山径。",
            preview_fixtures=(_FIXTURE_DEMO,),
            profile=CoverStyleProfile(
                prefer={"center_subject": True},
                avoid={"edge_subject": True, "ultra_wide": True},
                text_safe_regions=[{"x": 0.1, "y": 0.0, "w": 0.8, "h": 0.19}],
                title_max_lines=1,
            ),
        ),
        CoverStyleRecord(
            id="horizon-split",
            label="地平线",
            # 2026-08-03 实测下线：效果不理想，先退场（同 cameo-aperture 备注）。
            status="retired",
            sort_order=80,
            studio_blurb="上图下纸，留白承载长标题；适合有天际线的风景。",
            preview_fixtures=(_FIXTURE_DEMO,),
            profile=CoverStyleProfile(
                prefer={"horizon": True},
                avoid={"subject_bottom": True},
                text_safe_regions=[{"x": 0.0, "y": 0.57, "w": 1.0, "h": 0.43}],
                title_max_lines=2,
            ),
        ),
        CoverStyleRecord(
            id="contact-stamp",
            label="日戳档案",
            status="active",
            sort_order=90,
            studio_blurb="纪实档案气质：裁切十字、日戳与卷号参数。",
            preview_fixtures=(_FIXTURE_DEMO,),
            profile=CoverStyleProfile(
                prefer={"texture_mood": True},
                avoid={"edge_subject": True, "face_must_read": True},
                text_safe_regions=[
                    {"x": 0.0, "y": 0.72, "w": 0.55, "h": 0.28},
                    {"x": 0.62, "y": 0.72, "w": 0.38, "h": 0.28},
                ],
                title_max_lines=1,
            ),
        ),
        CoverStyleRecord(
            id="diptych-seam",
            label="双联断字",
            # 2026-08-03 实测下线：效果不理想，先退场（同 cameo-aperture 备注）。
            status="retired",
            sort_order=100,
            studio_blurb="一景一人跨缝断字；有人物副图时更完整，缺省时右栏同源裁切。",
            preview_fixtures=(_FIXTURE_DEMO,),
            profile=CoverStyleProfile(
                prefer={"pair_scene_person": True},
                avoid={"edge_subject": True},
                text_safe_regions=[{"x": 0.0, "y": 0.72, "w": 1.0, "h": 0.28}],
                title_max_lines=1,
            ),
        ),
    )
    for rec in styles:
        register_style(rec)
