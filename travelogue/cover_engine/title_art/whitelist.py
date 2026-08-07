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
    #: D-CAL-20 优先顺位⑤：该候选是否有「条件性占用风险」——即某些 trip 下
    #: 会被本风格自身的可选 UI 元素（hook/档案条等）实际占用，另一些 trip
    #: 下则完全空置、可以安全使用。非空时取值是 engine.py
    #: ``_CONDITIONAL_OCCUPANT_CHECKS`` 里注册的检查函数名；``placement_presets``
    #: 只返回候选定义，真正"这次这个 trip 是否被占用"的判定延后到 engine.py
    #: （需要 trip/cover_asset 数据，whitelist.py 保持零 I/O、纯数据表）。
    conditional_occupant: str | None = None


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
#:
#: 2026-08-07 开放前 CSS 暗坑排查（呼应 contact-stamp assume_dark_veil 那次教训，
#: 见 W2 验收记录 §4）：逐个风格翻了 journal.css 找类似"渐罩/filter 让实际渲染
#: 亮度跟原图采样不一致"的坑——
#:   - veil-footer 的 ::before 暖色 mix-blend-mode:screen 渐罩：z-index 与本贴纸
#:     相同但是伪元素，绘制顺序在真实子元素（贴纸 <img>）之前，不会遮住贴纸；
#:     且最高不透明度仅 0.30，非阻断项。
#:   - band-cut/contact-stamp/folio-overlap 等风格共用的左下角暖色
#:     mix-blend-mode:soft-light 渐罩（.cover-opening:not([data-cover-opening=
#:     "veil-footer"])::before）：同理绘制顺序在贴纸之下，且 soft-light+低不透明度
#:     只是轻微暖调，band-cut 真机视觉核对已验证不影响可读性。
#:   - contact-stamp 的强黑渐罩已在上面用 assume_dark_veil 修复。
#:   - folio-overlap 发现真正的阻断项，见下方 TODO/OQ-CAL-09，暂不开放。
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
    # TODO(OQ-CAL-09 · D-CAL-20 优先顺位③ 开放前排查，2026-08-07)：folio-overlap
    # 两条 text_safe_regions 都不能直接拿来贴纯色艺术字 PNG——
    #   候选 #0（左侧纸列 x:0~0.33,全高）：视觉上被 .cover-opening__place
    #   （地点标签，vertical-rl 竖排）常驻占用，贴上去会重叠。
    #   候选 #1（本行选用，y:0.58~0.78,x:0~0.7）：横跨"纸面栏(0~0.33，纯色
    #   #f4f1ea 米纸)→骑缝渐变(0.33~0.7，.cover-hero::after 90deg 黑渐变
    #   0.46→0.16，且被竖向 mask 限制在 y:0.22~0.74)→原图"三种背景。原生
    #   <h1> 用两份 content:attr(data-title) 叠加不同 clip-path + 配色
    #   （纸面侧深墨 #141312 / 照片侧浅色 #fcfaf6+投影）实现"书名骑缝切开
    #   压进画面"的双色断字效果（studio_blurb 原话）——这是 folio-overlap
    #   的核心设计语言，单一纯色 PNG 贴纸做不出来，套用会在某一侧读不出。
    # 结论：先别急着照抄 band-cut/contact-stamp 的"直接派生+开白名单"流程；
    # 需要专门方案（如收窄矩形只落在纯纸面栏内并挪开 __place，或做双色
    # 渐变贴纸）才能开放，见 PRD OQ-CAL-09。当前 rect 仍占位为候选 #1，
    # 该风格本就不在 DEFAULT_ENABLED_STYLES 内，无现网影响。
    "folio-overlap": PlacementPreset(
        opening_style_id="folio-overlap",
        label="folio 题区候选 #1（占位，尚不可直接开放，见上方 TODO/OQ-CAL-09）",
        rect=_registry_rect("folio-overlap", 1),
    ),
    "band-cut": PlacementPreset(
        opening_style_id="band-cut",
        label="切带断带留白区（registry 候选 #0，与真实断带位置精确吻合）",
        rect=_registry_rect("band-cut", 0),
    ),
    "contact-stamp": PlacementPreset(
        opening_style_id="contact-stamp",
        label="日戳左下角文案区（registry 候选 #0 · 主候选，跟 sr-only <h1> 同一位置）",
        rect=_registry_rect("contact-stamp", 0),
        # journal.css 该风格用 .cover-opening[data-cover-opening="contact-stamp"]
        # ::after 在整张封面上叠加一层不透明度约 0.3～0.72 的黑色渐变（且原生
        # <h1> 固定用浅色 #f5f2ec，从不跟随照片亮度）——跟原始照片的实际亮度
        # 无关，此处的原始照片 ROI 采样对这个风格是失真的。
        assume_dark_veil=True,
    ),
}

#: D-CAL-20 优先顺位⑤：已知安全、但只在特定 trip 条件下才不冲突的备选候选
#: （见各条目上的注释）。主候选（``WHITELIST``）永远排在 ``placement_presets``
#: 返回列表的第一位——只有主候选被 focal 冲突或占用检查淘汰时才会用到这里；
#: 多数风格目前没有已验证安全的备选，留空。
FALLBACK_PRESETS: dict[str, list[PlacementPreset]] = {
    "contact-stamp": [
        PlacementPreset(
            opening_style_id="contact-stamp",
            label=(
                "日戳右下角备选（registry 候选 #1）——仅当该 trip 没有 hook 文案"
                "且没有档案条文案时才安全，两者任一存在都会被这个矩形正好压住"
            ),
            rect=_registry_rect("contact-stamp", 1),
            assume_dark_veil=True,
            conditional_occupant="contact_stamp_hook_or_archive",
        ),
    ],
}

DEFAULT_ENABLED_STYLES: frozenset[str] = frozenset({"veil-footer", "band-cut", "contact-stamp"})


def is_whitelisted(style_id: str, *, enabled_styles: frozenset[str] | None = None) -> bool:
    allowed = enabled_styles if enabled_styles is not None else DEFAULT_ENABLED_STYLES
    return bool(style_id) and style_id in WHITELIST and style_id in allowed


def placement_preset(style_id: str) -> PlacementPreset | None:
    return WHITELIST.get(style_id)


def placement_presets(style_id: str) -> list[PlacementPreset]:
    """主候选 + 已知安全的备选候选（D-CAL-20 优先顺位⑤），主候选永远在前。

    ``engine.py`` 负责在此基础上做两层过滤：① 备选候选若带
    ``conditional_occupant``，先按该 trip 的实际内容判定是否被占用；②
    对剩余候选做 focal 冲突淘汰。淘汰后仍有 ≥2 个候选存活时，才真正交给
    ``placement.best_placement`` 打分择优——单个风格今天大多仍只有 1 个
    已验证安全的候选，这种情况下打分是形式化的（只有一个选项），跟 v0.6.1
    之前"固定绑死一个矩形"在行为上完全等价，不引入额外随机性。
    """
    primary = WHITELIST.get(style_id)
    if primary is None:
        return []
    return [primary, *FALLBACK_PRESETS.get(style_id, [])]
