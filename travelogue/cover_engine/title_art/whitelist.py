"""Opening 白名单与 placement preset (PRD §5.4 · D-CAL-10；坐标依据 v0.6 D-CAL-20)。"""

from __future__ import annotations

from dataclasses import dataclass

from travelogue.cover_engine.registry import get_profile


@dataclass(frozen=True)
class PlacementPreset:
    opening_style_id: str
    label: str
    rect: dict[str, float]  # 画布归一化坐标 x/y/w/h
    #: 该风格是否在 rect 覆盖的区域上固定叠加一层与照片内容无关的深色渐罩
    #: （如 ``journal.css`` 里 ``.cover-opening[data-cover-opening="..."]::after``
    #: 的全幅深色渐变）。为真时，§6.1 的自动配色不能只看原始照片 ROI 的亮度
    #: 采样——采样结果是「遮罩前」的颜色，会误判成够亮从而选深墨，实际渲染
    #: 出来的背景早被渐罩压到接近全黑，深墨读不出来（2026-08-07 真实视觉核
    #: 对发现，contact-stamp 首例）。见 ``engine.py`` 里对该字段的消费。
    assume_dark_veil: bool = False


def _registry_rect(style_id: str, region_index: int) -> dict[str, float]:
    """从 Cover Style Registry 的 ``text_safe_regions`` 取一条候选矩形。

    D-CAL-20：``text_safe_regions``（`travelogue/cover_engine/catalog.py`）
    是自动选图环节（`opening/title_safe.py::mark_title_safe`）已经在用的
    权威留白区数据，跟各风格真实渲染坐标高度吻合；这里直接复用，不再在
    本文件里手搓一份可能跟现网版式脱节的数值。
    """
    regions = get_profile(style_id).text_safe_regions
    if region_index >= len(regions):
        raise ValueError(
            f"text_safe_regions[{region_index}] not found for style {style_id!r}; "
            f"registry currently has {len(regions)} region(s)"
        )
    region = regions[region_index]
    return {
        "x": float(region.get("x", 0.0)),
        "y": float(region.get("y", 0.0)),
        "w": float(region.get("w", 0.0)),
        "h": float(region.get("h", 0.0)),
    }


#: 首发 veil-footer；v0.6 追加 band-cut / contact-stamp（D-CAL-20 优先顺位①②：
#: registry text_safe_regions 与真实渲染坐标精确吻合，横版画布友好）。
#: folio-overlap 已注册但默认不在 DEFAULT_ENABLED_STYLES 内（D-CAL-10 · D-CAL-20
#: 优先顺位③，狗粮后再开）。scroll-head 竖排版式与现有横版画布不兼容，暂不
#: 注册（D-CAL-20 优先顺位⑤）。其它 styleId 不注册 → 非白名单，强制不叠加。
WHITELIST: dict[str, PlacementPreset] = {
    "veil-footer": PlacementPreset(
        opening_style_id="veil-footer",
        label="雾带上方留白区",
        # TODO(D-CAL-20 优先顺位④)：该风格 registry 里唯一的 text_safe_regions
        # 是雾带底部——跟现有 hook/trip-meta 面板是同一块区域，跟这里"雾带
        # 上方"的留白语义并非同一件事（面板已被现有文案占用，直接派生会
        # 重新引入 v0.5 视觉验收刚修复的重叠问题）。需要先解决 OQ-CAL-08
        # （面板占位排除 / 接入 mark_title_safe 的 focal 校验）才能改成派生值，
        # 本次不动。
        rect={"x": 0.08, "y": 0.14, "w": 0.84, "h": 0.22},
    ),
    "folio-overlap": PlacementPreset(
        opening_style_id="folio-overlap",
        label="folio 题区约定矩形（registry 候选 #1 · 底部横条，横版画布友好）",
        rect=_registry_rect("folio-overlap", 1),
    ),
    "band-cut": PlacementPreset(
        opening_style_id="band-cut",
        label="切带断带留白区（registry 候选 #0，与真实断带位置精确吻合）",
        rect=_registry_rect("band-cut", 0),
    ),
    "contact-stamp": PlacementPreset(
        opening_style_id="contact-stamp",
        label="日戳左下角文案区（registry 候选 #0，避让右下角 hook/日戳号）",
        rect=_registry_rect("contact-stamp", 0),
        # journal.css 该风格用 .cover-opening[data-cover-opening="contact-stamp"]
        # ::after 在整张封面上叠加一层不透明度约 0.3～0.72 的黑色渐变（且原生
        # <h1> 固定用浅色 #f5f2ec，从不跟随照片亮度）——跟原始照片的实际亮度
        # 无关，此处的原始照片 ROI 采样对这个风格是失真的。
        assume_dark_veil=True,
    ),
}

DEFAULT_ENABLED_STYLES: frozenset[str] = frozenset({"veil-footer", "band-cut", "contact-stamp"})


def is_whitelisted(style_id: str, *, enabled_styles: frozenset[str] | None = None) -> bool:
    allowed = enabled_styles if enabled_styles is not None else DEFAULT_ENABLED_STYLES
    return bool(style_id) and style_id in WHITELIST and style_id in allowed


def placement_preset(style_id: str) -> PlacementPreset | None:
    return WHITELIST.get(style_id)
