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
    #: OQ-CAL-09 收尾（v0.6.6）：该候选区是否压在跟照片内容完全无关的固定
    #: 背景色块上（如 folio-overlap 左侧纸面栏——那块区域根本不显示照片，
    #: `.cover-hero` 只占据 ``--cover-folio-margin`` 右侧那部分）。为真时
    #: §6.1 自动配色不能对 ``cover_img``（原始照片文件）做 ROI 采样——采样
    #: 出来的像素跟这块区域实际渲染的颜色毫无关系（不是"渐罩前/渐罩后"的
    #: 亮度偏差，是压根不是同一块视觉内容）。engine.py 命中时改用该风格的
    #: 固定背景色（如米纸色）而非采样结果。跟 ``assume_dark_veil`` 是同一
    #: 类问题（ROI 采样对这块区域失真）的另一种成因，故意分成两个字段而非
    #: 合并成一个「背景色覆盖值」——数值不同、成因不同，各自的注释各自能
    #: 独立讲清楚，合并后调用点反而要多一层"这里的覆盖色具体是什么"的追问。
    assume_paper_bg: bool = False
    #: 锚点模式：``center`` 用矩形几何中心；``left`` 贴矩形左侧（呼应原生
    #: 左起标题），CSS 侧配合 ``translate(0,-50%)``。
    anchor: str = "center"
    #: 与该风格原生 ``.cover-opening__title`` 颜色一致的固定墨色；非空时
    #: engine 跳过 ROI 对比度挑色，直接用此色（W3：大小/颜色跟封面样式匹配）。
    native_ink: tuple[int, int, int] | None = None


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
#: registry text_safe_regions 与真实渲染坐标精确吻合，横版画布友好）；v0.6.6
#: 追加 folio-overlap（OQ-CAL-09 收尾：手工纸面栏矩形 + assume_paper_bg，不再
#: 走 registry 派生，见下方该条目注释）。scroll-head 竖排版式与现有横版画布
#: 不兼容，暂不注册。其它 styleId 不注册 → 非白名单，强制不叠加。
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
#:   - folio-overlap 当时发现的真正阻断项已在 v0.6.6 用手工纸面栏矩形 +
#:     assume_paper_bg 收尾（OQ-CAL-09 已关闭），见下方该条目详细注释。
WHITELIST: dict[str, PlacementPreset] = {
    "veil-footer": PlacementPreset(
        opening_style_id="veil-footer",
        label="底部浓黑题签区（对齐 panel 左下原生 <h1>）",
        # 底部约 18%：与 journal.css panel bottom padding + 标题字号同量级。
        # 渲染侧 titleArtInPanel：贴纸进 panel 文档流；此 rect 仍供 focal /
        # 元数据 position 使用。
        rect={"x": 0.04, "y": 0.80, "w": 0.52, "h": 0.18},
        anchor="left",
        native_ink=(0xF5, 0xF3, 0xF0),  # journal.css 默认 title #f5f3f0
    ),
    "folio-overlap": PlacementPreset(
        opening_style_id="folio-overlap",
        label="纸面栏左侧竖排书名位（对齐 writing-mode:vertical-rl）",
        # 窄高条幅：落在 --cover-folio-margin 33% 纸面栏内；y 避开顶部
        # .cover-opening__place 竖排跑题。
        rect={"x": 0.05, "y": 0.16, "w": 0.16, "h": 0.58},
        assume_paper_bg=True,
        anchor="left",
        native_ink=(0x14, 0x13, 0x12),  # #141312
    ),
    "band-cut": PlacementPreset(
        opening_style_id="band-cut",
        label="断带纸签原生标题位（registry 候选 #0 · 对齐 --cover-band-center）",
        rect=_registry_rect("band-cut", 0),
        assume_paper_bg=True,
        anchor="left",
        native_ink=(0x14, 0x13, 0x12),  # #141312
    ),
    "contact-stamp": PlacementPreset(
        opening_style_id="contact-stamp",
        label="日戳左下角原生标题位（registry 候选 #0）",
        # CSS 侧 title-art 已 bottom 钉死对齐原生 h1；此 rect 供 focal / 元数据
        rect=_registry_rect("contact-stamp", 0),
        assume_dark_veil=True,
        anchor="left",
        native_ink=(0xF5, 0xF2, 0xEC),  # #f5f2ec
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
            anchor="left",
            native_ink=(0xF5, 0xF2, 0xEC),
        ),
    ],
    "folio-overlap": [
        PlacementPreset(
            opening_style_id="folio-overlap",
            label=(
                "纸面栏竖排全高备选——仅当该 trip 没有地点标签（.cover-opening__place，"
                "跟主标题不同名才会显示）占用纸面栏顶部时才用，留白更松"
            ),
            rect={"x": 0.05, "y": 0.08, "w": 0.16, "h": 0.78},
            assume_paper_bg=True,
            conditional_occupant="folio_place_present",
            anchor="left",
            native_ink=(0x14, 0x13, 0x12),
        ),
    ],
}

DEFAULT_ENABLED_STYLES: frozenset[str] = frozenset(
    {"veil-footer", "band-cut", "contact-stamp", "folio-overlap"}
)


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
