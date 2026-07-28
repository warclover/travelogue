# Travelogue · 三竖并列「Editorial Row」排版 PRD

| 属性 | 内容 |
|------|------|
| **文档版本** | v0.3 |
| **状态** | Revised · 可进入 P0（含 §12 开发负责人实施附录） |
| **功能代号** | portrait-row-editorial（方案 B） |
| **前置条件** | `layoutEngine=screens`；现有 `screen-portrait-3` / `person-triple` **保持不变** |
| **关联文档** | [PRD-排版规则优化.md](./PRD-排版规则优化.md)、[LAYOUT-PLANNER.md](./LAYOUT-PLANNER.md)、[screen-portrait-3 slot-aspect](./templates/slot-aspect/screen-portrait-3.md) |
| **实现入口（规划）** | 见 §10 注册表 |
| **验收样本** | `trips/demo-001-2018`、`trips/demo-2025-2` |
| **更新日期** | 2026-06-20 |

> **定位**
>
> 新增 **`screen-portrait-3-editorial`** 模板，以艺术杂志式「肖像行」呈现三竖并列，**不修改**现有 `screen-portrait-3` 与 `person-triple` 契约。产品先 A/B 对比 editorial 与 legacy 效果，再决定是否统一契约（方案 A）。

### 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-06-20 | 初稿；产品拍板 D-01～D-04 |
| v0.2 | 2026-06-20 | 专家评审修订：LTE schema 兼容、节奏 state 注册、移动端拆屏、fit 稳定哈希、脚线 object-position、MCS 共用拦截、分期与 AC 可测化 |
| v0.3 | 2026-06-20 | 开发负责人实施附录 §12：PR 切分、配置优先级、scope 规则、mobile 连带面、probe/CSS 工程约定、beta→ga 指标 |

---

## 1. 已拍板决策（2026-06-20）

| # | 议题 | 决策 |
|---|------|------|
| **D-01** | 主路径 | **方案 B**：新建 `screen-portrait-3-editorial`，legacy 路径零改动 |
| **D-02** | 三图对齐 | **统一行高 + 底对齐脚线**（行高 = 三槽缩放后最大值；槽内 img 贴底） |
| **D-03** | 无人物风景竖拍 fit | **cover 与 contain 均保留**；屏级 **确定性伪随机** 择一（见 §4.4）；**人物行不参与随机** |
| **D-04** | 移动端 | **不做竖版并列**；`layoutEngine=screens` 的 mobile 面在 render 层将三竖屏 **拆成 3× 单竖**（见 §5） |

---

## 2. 设计北极星

> **三竖并列 = 一条 Editorial Portrait Row**：行宽窄于版心、缝大于 legacy triple、行高随最高图、脚线齐；舞台 **视觉 intrinsic**（不写固定 `--screen-aspect`），不强制 9:16。

### 2.1 与 legacy 对照

| 维度 | `screen-portrait-3`（legacy） | `screen-portrait-3-editorial`（新） |
|------|-------------------------------|-------------------------------------|
| 人物三竖 | `layoutHint=person-triple`，contain，gap 8–18px | `layoutHint=portrait-row-editorial`，contain，gap 20–36px |
| 风景三竖 | 无 hint，全宽，gap 3px，cover/contain 按 asset | 同 hint，inset 行宽，屏级随机 cover **或** contain（P2） |
| 舞台 AR | 9:16（LTE）/ intrinsic（CSS overlay） | LTE 占位比 + render **skip_stage_aspect**（§3.1） |
| 对齐 | top center | **统一行高 + 脚线底对齐**（§3.4） |
| 行宽 | person-triple: ~100%−inset；generic: 100% | `min(88%, 960px)` 居中 |
| Web 面 | 三列 `layout-screen` | 三列 `layout-screen`（editorial CSS） |
| Mobile 面 | 仍输出 3 槽 `layout-screen`（无专用 overlay） | render **拆成 3× 单竖屏**（§5） |

---

## 3. 模板规格

### 3.1 LTE YAML（新建）

**文件：** `travelogue/layout_templates/templates/screen-portrait-3-editorial.yaml`

> **schema 约束（v0.2 修正）**  
> 现网 `layout_template.schema.json` 要求 `stage.aspect` 匹配 `^\d+:\d+$`，**不接受** `intrinsic`。  
> YAML 使用 **占位舞台比**；真实呈现由 render `skip_stage_aspect` + CSS overlay 实现 **视觉 intrinsic**。

```yaml
id: screen-portrait-3-editorial
version: 1
status: beta          # 试点；稳定后升 ga
kind: primitive
displayName: portrait · 3 · editorial
description: 杂志式三竖并列行（视觉 intrinsic · 脚线对齐 · 不替换 screen-portrait-3）
stage:
  aspect: "16:9"      # LTE/probe 占位；render 不写 --screen-aspect
  grid: [3, 1]
photoCount: { min: 3, max: 3 }
mix: { portrait: 3, landscape: 0 }
slots:
  - { index: 0, role: portrait, fit: auto }
  - { index: 1, role: portrait, fit: auto }
  - { index: 2, role: portrait, fit: auto }
constraints:
  portrait_forbidden_in_wide_slots: []
  landscape_forbidden_in_tall_slots: []
  intentionalGaps: []
scoring:
  base_weight: 0.85   # MCS 路径生效；screen_planner 硬 emit 时不依赖此项
  tags: [portrait-row, editorial]
render:
  gridClass: layout-screen__grid--3col
  cssBundle: journal-screens.css
  fitPolicy: editorial_row
  presentation: portrait-row-editorial
```

**slot displayAspect：** 不写死 0.1875。probe 基线按 **行宽三等分 + 样本竖图 native AR** 重拍；**contain 与 cover 各一套**（P3）。

**后续可选（非 P0）：** 扩展 LTE schema 支持 `aspect: intrinsic`，再迁移 YAML；不阻塞首版。

### 3.2 Render 契约

| 字段 | 值 |
|------|-----|
| `data-pattern` | `screen-portrait-3-editorial` |
| `data-layout-hint` | `portrait-row-editorial` |
| `--screen-aspect` | **不写**（`skip_stage_aspect=True`） |
| 槽 background | `transparent` |
| 屏级 `--screen-tone` | 纸面/中性场（行外留白） |
| cover 行（P2） | 可选 `--editorial-row-ar`（§3.5） |

**`context.py` 改动：**

- `skip_stage_aspect` 加入 `screen-portrait-3-editorial`（与 `screen-portrait-2/3` 同级）。
- `layout_hint` 透传 `portrait-row-editorial`。
- mobile 拆屏逻辑见 §5（在 `build_layout_screen` 上游或 chapter 组装层）。

**Blurred fill（O-03 已关闭）：**

- **不启用**。将 `portrait-row-editorial` 显式登记进 `blur_fill._INTRINSIC_CONTAIN_HINTS`（或等价 pattern 白名单），**禁止**依赖 `n_slots > 1` 的隐式副作用。

### 3.3 CSS Token（web / auto / screens · 非 mobile）

```css
html[data-layout-engine="screens"] {
  --portrait-row-editorial-width: min(88%, 960px);
  --portrait-row-editorial-inset: clamp(24px, 4vw, 48px);
  --portrait-row-editorial-gap: clamp(20px, 2.5vw, 36px);
  --portrait-row-editorial-padding-y: clamp(16px, 3vh, 48px);
}
```

**选择器：** 仅匹配 `data-pattern="screen-portrait-3-editorial"`，**不得**污染 legacy `screen-portrait-3` / `person-triple`。

### 3.4 布局规则与脚线对齐（D-02）

**Grid / 行高：**

1. `.layout-screen`：`aspect-ratio: unset`；`display: flex`；`justify-content: center`；`padding: var(--portrait-row-editorial-padding-y) var(--portrait-row-editorial-inset)`。
2. `.layout-screen__grid--3col`：`width: var(--portrait-row-editorial-width)`；`gap: var(--portrait-row-editorial-gap)`；`grid-template-rows: auto`（与 person-triple 一致，**不用** `1fr`）；`align-items: stretch`。
3. `.layout-slot`：`display: flex`；`flex-direction: column`；`justify-content: flex-end`；`min-height: 100%`；`background: transparent`。

**Img / object-position（v0.2 修正）：**

| fit | 规则 |
|-----|------|
| **contain**（人物行 + 风景 contain 行） | `width: 100%`；`height: auto`；`max-height: var(--portrait-stage-vh)`；`object-fit: contain`；**`object-position: bottom center`**（脚线对齐；**不用** focal y） |
| **cover**（风景 cover 行 · P2） | 槽设 `aspect-ratio: var(--editorial-row-ar)`；img `width/height: 100%`；`object-fit: cover`；**`object-position: bottom center`** |

> Editorial row 的 focal point **不参与**竖向对齐；focal 保留给 `screen-portrait-1` / full-frame 等单槽场景。

### 3.5 Cover 行几何（P2 · 随风景随机 fit 一并交付）

Render 在屏级 cover 模式下计算并写入：

```text
--editorial-row-ar: W / H_max
```

其中 `H_max` = 三图在列宽 `W = (rowWidth − 2×gap) / 3` 下，按各自 native AR 缩放后的 **最大展示高度**。

单测：给定三张固定 AR 的 fixture，断言 CSS 变量与 probe 截图槽等高。

---

## 4. Curate / Planner

### 4.1 启用方式（试点）

**默认不替换** `screen-portrait-3`。配置：

```yaml
# config.yaml
layout:
  editorial_portrait_row:
    enabled: false          # O-01 默认 false
    replace_patterns:
      - screen-portrait-3
    scope: all              # all | scenery | person（语义见 §12.3）
    trip_allowlist: []      # 全局 allowlist；与 trip 级 override 配合见 §12.2
```

**配置优先级（v0.3 · §12.2）：**

```text
trip.export.editorialPortraitRow  >  trip_id ∈ trip_allowlist  >  layout.editorial_portrait_row.enabled
```

实现收敛为单一入口：`is_editorial_portrait_row_enabled(trip, cfg)`；planner 与 MCS **不得**各自读 config。

**统一拦截函数（v0.2 新增 · O-02 已关闭）：**

```text
_maybe_editorial_portrait_row(pattern_id, asset_ids, assets_map, config) → pattern_id, layoutHint
```

| 调用点 | 必须接入 |
|--------|----------|
| `screen_planner._plan_portrait_triple_row` | ✅ |
| `screen_planner._emit_person_portrait_screens` | ✅ |
| `mosaic/builders.py`（MCS unified → portrait-3 窗口） | ✅ |

命中条件：`enabled` + `pattern_id ∈ replace_patterns` + `scope` 匹配（人物/风景/全部）。

输出：`patternId = screen-portrait-3-editorial`，`layoutHint = portrait-row-editorial`。

**节奏 state 等价（§10.2）：** 与 `screen-portrait-3` 同等计入 `portrait_triple`（竖版三列连续 R-02 豁免；与 `six` 相邻仍禁）——须改代码，**非** regex 自动继承。

### 4.2 人物 vs 风景 fit

| 类型 | fit | 随机 |
|------|-----|------|
| 含人物（任一槽 `asset_has_person`） | 三槽均为 **contain** | **不参与** §4.4 |
| 纯风景竖拍 | 屏级 **cover 或 contain** | §4.4（**P2** 交付） |

### 4.3 Fit 决策时机

`_fits_for_screen` / slot fit 须在 **`screenId` 已赋值之后** 计算（`screen_planner_attach` / `assign_screen_id` 之后），或在稳定键可用时调用 §4.4。

**禁止**在 `_make_screen(..., screen_id="")` 当次同步调用随机 fit（`screen_id` 常为空）。

### 4.4 风景 fit 确定性伪随机（D-03 · P2）

**目标：** 同 trip 内 cover / contain 行均出现；**跨进程、重跑 curate/render 结果稳定**。

```python
import hashlib

def editorial_row_fit_mode(
    *,
    trip_id: str,
    screen_id: str,
    asset_ids: tuple[str, ...],
) -> Literal["cover", "contain"]:
    key = f"{trip_id}:{screen_id}:{','.join(sorted(asset_ids))}"
    digest = hashlib.sha256(key.encode()).hexdigest()
    return "cover" if int(digest[:8], 16) % 2 == 0 else "contain"
```

- 屏级统一 fit：三槽同值。
- **禁止**使用 Python 内置 `hash()`（受 `PYTHONHASHSEED` 影响）。
- 单测：同输入 N 次一致；100+ 样本分布约 40–60%（不强制精确 50/50）。

---

## 5. 移动端（D-04 · P1 必做）

### 5.1 问题陈述（v0.2 修正）

v0.1 误认为 legacy `plan_chapter_items(mobile)` 已覆盖 screens trip。实际：

- `layoutEngine=screens` 的 `index-mobile.html` 仍走 `useScreensEngine`，输出 **3 槽 `layout-screen`**（`chapter.hbs`）。
- portrait overlay 普遍带 `:not([data-layout="mobile"])`，mobile 三列 **无** editorial / person-triple 样式。

**D-04 不能在 mobile 上呈现三竖并列。**

### 5.2 方案（推荐 · 写死）

**Render 层拆屏：** 当 `export_layout == "mobile"` 且 `patternId ∈ { screen-portrait-3, screen-portrait-3-editorial }` 时，将一屏 **展开为 3 个** `screen-portrait-1` layout-screen（槽序不变，各槽 retain 原 fit 策略；人物仍为 contain）。

| 项 | 说明 |
|----|------|
| 插入点 | `chapters.py` 组装 `screens_out` 前，或 dedicated `expand_portrait_triple_for_mobile(screens)` |
| 触发条件 | `export_layout == "mobile"` **且** `not is_longshot_surface`（§12.4） |
| legacy 同步 | **`screen-portrait-3` 与 editorial 共用**拆屏逻辑（mobile 行为一致） |
| folio plate | **仅第一槽**继承 `is_plate` / plate meta；#2/#3 为普通 `screen-portrait-1`（§12.4） |
| trip.json | **不改** `screens[]` 存储；仅 HTML render 展开 |
| items stub | 可选同步：`items_from_screens` 对三竖屏写 3× `media-card`（schema 一致） |

### 5.3 验收（替代 v0.1 AC-ED-08）

| ID | 标准 |
|----|------|
| AC-ED-08a | mobile HTML 中 **无** `data-pattern="screen-portrait-3-editorial"` 且子 grid 为 3col 的块 |
| AC-ED-08b | 原三竖屏 assets 以 **3 个连续** `screen-portrait-1`（或等价单槽屏）出现，顺序不变 |
| AC-ED-08c | 单测 `test_mobile_screens_engine_portrait_triple_expands_to_singles` |
| AC-ED-08d | longshot 面无「双次展开」（§12.4） |
| AC-ED-08e | folio plate 仅出现在拆屏第一槽（§12.4） |

---

## 6. 验收标准

| ID | 标准 | 阶段 |
|----|------|------|
| AC-ED-01 | 开关 **关闭** 时 legacy golden（web）零 diff | P1 |
| AC-ED-02 | 开关 **开启**：demo 样本 ≥1 屏 `data-pattern="screen-portrait-3-editorial"` | P1 |
| AC-ED-03 | @1440：行宽 ≤ 88% 版心；gap ≥ 20px | P0 |
| AC-ED-04 | 脚线对齐：三槽 img 底边距 row 底 **≤ 2px**（probe 或 Playwright bbox） | P0 |
| AC-ED-05 | 人物屏三槽 `layout-slot__img--contain`，无脸裁切（人工 spot） | P0 |
| AC-ED-06 | 纯风景 trip：可见 cover 行与 contain 行各 ≥1 | P2 |
| AC-ED-07 | 无固定 9:16 上下大块 tone 信箱 | P0 |
| AC-ED-08 | 见 §5.3 + §12.4（含 AC-ED-08d/e） | P1 |
| AC-ED-09 | probe baseline：`screen-portrait-3-editorial-contain.png` 入库 | P3 |
| AC-ED-10 | `screen-portrait-3-editorial` 连续两屏时 planner **拒绝**第三连三列（R-02） | P1 |
| AC-ED-11 | `portrait-row-editorial` + contain **无** `layout-slot--blurred-fill` | P0 |

---

## 7. 分期交付（PR 映射见 §12.1）

| 阶段 | 内容 | 依赖 | 推荐 PR |
|------|------|------|---------|
| **P0** | LTE YAML（占位 aspect）+ editorial CSS（**contain / 人物**）+ render hint / skip_stage_aspect + blur hint 登记 + AC-ED-03/04/05/07/11 | 无 | PR-1 |
| **P1** | §10 注册表 + config 开关 + `_maybe_editorial_portrait_row`（planner **+ MCS**）+ mobile 拆屏 + rhythm 等价单测 + AC-ED-01/02/08/10 | P0 | PR-2 + PR-3 |
| **P2** | 风景 fit 确定性随机 + cover 行 `--editorial-row-ar` + AC-ED-06 | P1 | PR-4 |
| **P3** | probe baseline（contain + cover）+ demo dogfood 并排对比页 + §12.7 决策评审 | P2 | PR-5 |

**P0 刻意不包含：** planner 开关、风景 cover 随机、MCS 拦截（可用手动 trip.json 挂 `patternId` 验 CSS）。

**明确不做（本 PRD）：**

- 方案 A 统一契约（合并 person-triple / generic portrait-3）
- 方案 C 不等宽三竖（weighted columns）
- Reader profile 隐藏 folio plate meta（另开 PRD）
- 修改 legacy web gap / inset / 对齐
- LTE schema 扩展 `intrinsic`（可选后续）

---

## 8. 开放项

| ID | 问题 | v0.2 决议 |
|----|------|-----------|
| O-01 | 试点默认开还是关？ | **`enabled: false`**；`trip_allowlist` 供 dogfood |
| O-02 | MCS 是否参与？ | **是** — 与 planner 共用 `_maybe_editorial_portrait_row` |
| O-03 | contain 风景 blur？ | **否** — hint 显式登记，见 §3.2 |
| O-04 | mobile 拆屏是否作用于 legacy `screen-portrait-3`？ | **是** — 统一 mobile 竖单体验 |

---

## 9. 附录 A · CSS 脚线备忘

```css
.layout-screen[data-pattern="screen-portrait-3-editorial"] .layout-screen__grid--3col {
  grid-template-rows: auto;
  align-items: stretch;
}
.layout-screen[data-pattern="screen-portrait-3-editorial"] .layout-slot {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  min-height: 100%;
}
.layout-screen[data-pattern="screen-portrait-3-editorial"] .layout-slot__img--contain,
.layout-screen[data-pattern="screen-portrait-3-editorial"] .layout-slot__img--cover {
  object-position: bottom center;
}
```

---

## 10. 附录 B · 工程注册表（P1 必改清单）

实现 editorial 时，以下触点须 **显式登记** `screen-portrait-3-editorial`，不可假设与 `screen-portrait-3` 自动等价。

### 10.1 Schema & 类型

| 文件 | 改动 |
|------|------|
| `schemas/trip.schema.json` | `screens[].patternId` enum 增加 `screen-portrait-3-editorial` |
| `travelogue/render/context_types.py` | 若有 pattern 字面量联合，同步 |

### 10.2 节奏 state（`screen_layout_state.py`）

| 符号 | 改动 |
|------|------|
| `is_triple_row_pattern()` | 显式包含 `screen-portrait-3-editorial`（regex `screen-portrait-(\d+)` **不匹配** `-editorial` 后缀） |
| `PORTRAIT_ORIENTATION_PATTERNS` | 加入 editorial |
| `can_emit_pattern` / R-02 | 验证 AC-ED-10 |

### 10.3 Grid class & legacy bridge

| 文件 | 改动 |
|------|------|
| `travelogue/curation/screen_planner.py` | `PATTERN_GRID_CLASS` 映射 |
| `travelogue/curation/mosaic/_legacy_generated.py` | `MOSAIC_3_PATTERN_IDS` **不**加入 editorial（非 MCS 3-slot 家族）；仅 grid_class 若需 |
| `travelogue/layout_engine/render_binding.py` | `grid_class_for_pattern` |
| `travelogue/layout_templates/lte_policy.yaml` | 文档注释；quota 是否计 beta primitive |

### 10.4 Render & blur

| 文件 | 改动 |
|------|------|
| `travelogue/render/context.py` | `skip_stage_aspect`、hint 透传 |
| `travelogue/render/blur_fill.py` | `_INTRINSIC_CONTAIN_HINTS` += `portrait-row-editorial` |
| `travelogue/render/chapters.py` | mobile 拆屏（§5.2） |

### 10.5 Curate

| 文件 | 改动 |
|------|------|
| `travelogue/curation/screen_planner.py` | `_maybe_editorial_portrait_row` |
| `travelogue/curation/mosaic/builders.py` | MCS portrait-3 窗口调用同上 |
| `travelogue/curation/screen_planner.py` | `_fits_for_screen` 分支（P2） |

### 10.6 CSS & probe

| 文件 | 改动 |
|------|------|
| `templates/visual-journal/journal-screens.css` | editorial overlay（§3.3–3.4）；**与 overlays 双文件同步**（§12.6） |
| `templates/visual-journal/journal-screens-overlays.css` | 同上 |
| `docs/templates/slot-aspect/screen-portrait-3-editorial.md` | 自动生成或手写；probe ≠ web 说明（§12.5） |
| `travelogue/layout_templates/probes/baselines/` | `screen-portrait-3-editorial-contain.png`（**P3 前 skip/xfail**，§12.5） |

### 10.7 测试（最低集）

| 测试 | 覆盖 |
|------|------|
| `test_editorial_row_fit_stable_hash` | §4.4 跨进程一致 |
| `test_triple_pattern_includes_editorial` | §10.2 R-02 |
| `test_mobile_screens_engine_portrait_triple_expands_to_singles` | §5.3 |
| `test_blur_fill_skips_portrait_row_editorial` | §3.2 |
| `test_legacy_golden_unchanged_when_editorial_disabled` | AC-ED-01 |
| `test_editorial_scope_*`（3 例） | §12.3 |
| `test_mobile_longshot_skips_triple_expand` | AC-ED-08d |
| `test_mobile_triple_expand_plate_on_first_slot_only` | AC-ED-08e |

---

## 11. 附录 C · v0.1 → v0.2 对照（评审吸收）

| 评审项 | v0.1 | v0.2 |
|--------|------|------|
| LTE `aspect: intrinsic` | YAML 直接写 | 占位 `16:9` + skip_stage_aspect |
| 节奏 triple streak | 「等价」一笔带过 | §10.2 显式函数清单 + AC-ED-10 |
| Mobile | 「已满足」 | §5 render 拆屏 P1 必做 |
| fit 随机 | `hash()` | `hashlib.sha256` + screenId 时机 |
| object-position | focal x/y | **bottom center**（脚线） |
| cover 行 | P0 含糊 | 推迟 **P2** + `--editorial-row-ar` |
| MCS 路径 | 仅 planner | 共用 `_maybe_editorial_portrait_row` |
| grid-template-rows | `1fr` | **`auto`** |
| blur | 隐含 n_slots | hint **显式登记** |

---

## 12. 附录 D · 开发负责人实施附录（v0.3）

> 本节为 **实施与 PR 编排** 约束，不改变 §1 产品拍板；与 §7 分期、§10 注册表配合使用。

### 12.1 PR 切分策略（强制）

**禁止**单 PR 合并 P0 + P1 + mobile 拆屏 + P2。推荐三分法：

| PR | 阶段 | 内容 | 合并门槛 |
|----|------|------|----------|
| **PR-1** | P0 | LTE YAML + editorial CSS（contain/人物）+ render hint / `skip_stage_aspect` + blur hint 登记 | 手工改 `trip.json` 的 `patternId` 可验 AC-ED-03/04/05/07/11 |
| **PR-2** | P1a | §10 注册表 + config + `is_editorial_portrait_row_enabled` + `_maybe_editorial_portrait_row`（planner + MCS）+ rhythm 单测 | AC-ED-01/02/10；`enabled: false` golden 零 diff |
| **PR-3** | P1b | mobile 拆屏（§5.2 + §12.4） | AC-ED-08；**单独 review**（行为面大于 editorial 视觉） |
| **PR-4** | P2 | 风景 fit 随机 + `--editorial-row-ar` + cover CSS | AC-ED-06；**不得**与 PR-2 捆绑 |
| **PR-5** | P3 | probe baseline + dogfood 对比页 | AC-ED-09；§12.7 决策评审 |

P0 **刻意不上** planner 开关；P2 **刻意不做** legacy web CSS 改动。

### 12.2 配置读取（单一入口）

**优先级（高 → 低）：**

1. `trip.export.editorialPortraitRow`（bool，trip 级显式 override）
2. `trip_id ∈ layout.editorial_portrait_row.trip_allowlist`
3. `layout.editorial_portrait_row.enabled`（全局默认 `false`）

**API 约定：**

```text
is_editorial_portrait_row_enabled(trip, cfg) -> bool
maybe_editorial_portrait_row(pattern_id, asset_ids, assets_map, trip, cfg)
    -> tuple[pattern_id, layout_hint | None]
```

`_maybe_editorial_portrait_row` 仅在 `is_*` 为 true 且 `pattern_id ∈ replace_patterns` 时替换；否则原样返回。

### 12.3 `scope` 替换规则（v0.3 补全）

在 `enabled`（含 §12.2 优先级）为 true 的前提下：

| scope | 替换条件 |
|-------|----------|
| `person` | 三槽 **均为** person（`asset_has_person`） |
| `scenery` | 三槽 **均无** person |
| `all` | 任意合法 `screen-portrait-3` 三竖窗口 |

**混合三竖**（有人物 + 风景）：仅 `scope=all` 时可替换；`person` / `scenery` **均不替换**。

**单测（PR-2 必含）：**

- `test_editorial_scope_person_requires_all_person`
- `test_editorial_scope_scenery_requires_no_person`
- `test_editorial_scope_all_allows_mixed`

### 12.4 Mobile 拆屏连带规则

除 §5.2 外，实现须满足：

| 连带 | 规则 |
|------|------|
| **longshot** | `is_longshot_surface` 时 **不拆屏**（已有 flatten 路径） |
| **folio lite plate** | 拆后 **slot 0** 继承原屏 `is_plate` / plate meta；slot 1/2 否 |
| **screenplay** | mobile 拆屏后，原一屏计 **3** 个 layout-screen step（文档化；不改 trip.json） |
| **breath-pause** | 拆屏不改变 breath 在原 `screens[]` 序中的锚点；单测断言 breath 索引 |
| **global_screen_index** | 拆屏后递增 +2（接受；telemetry 注明「mobile triple expand」） |

**AC 补充：**

| ID | 标准 |
|----|------|
| AC-ED-08d | longshot 面不出现「双次展开」 |
| AC-ED-08e | folio plate 仅出现在拆屏第一槽 |

### 12.5 LTE probe 与占位 aspect（工程约定）

YAML 占位 `16:9` 与 web render（skip stage aspect + intrinsic CSS）** intentionally 不一致**。

| 阶段 | 要求 |
|------|------|
| P0–P2 | `screen-portrait-3-editorial` **不**跑 probe 截图 golden；CI 使用 skip 或 `@pytest.mark.xfail(reason="P3 baseline")` |
| P3 | 重拍 baseline 前，在 slot-aspect doc 顶部注明 **「probe 参考态 ≠ web render 态」** |
| P3 | baseline 分 **`…-contain.png`** 与 **`…-cover.png`** 两套 |

### 12.6 CSS 双文件同步

editorial overlay 须 **同时**修改：

- `templates/visual-journal/journal-screens.css`
- `templates/visual-journal/journal-screens-overlays.css`

与现网 `person-triple` 流程一致；合并前跑 `tests/test_lte_css_sync.py`。PR-1 checklist 必勾。

### 12.7 Beta → GA / 方案 A 决策指标（P3 前产品确认）

满足 **全部** 方可升 `status: ga` 或启动方案 A 统一契约评估：

| # | 指标 |
|---|------|
| G-ED-01 | dogfood trip（allowlist）≥ **5** 屏 editorial；产品 blind review **≥ 4/5** 屏不劣于 legacy person-triple |
| G-ED-02 | AC-ED-01～11 + §12.3 scope 单测 + §12.4 连带 AC **全绿** |
| G-ED-03 | `enabled: false` 下 `demo-2025-2` layout golden **deep equal** master（连续 2 周或 2 个 release 周期） |
| G-ED-04 | mobile 拆屏（PR-3）已合入且 **无** folio/plate 回归 ticket |

未达标则保持 `beta` + 双轨维护；**禁止** silent 默认 `enabled: true`。

### 12.8 视觉 acceptance note（脚线对齐边界）

P0 dogfood 前与产品口头确认并写入 release note：

- Editorial row 对齐的是 **槽内 `<img>` 元素底边**，非语义地平线。
- **胸像/大头照**：bottom center 可能导致头顶参差 —— **预期行为**，非 bug。
- **大 sky 竖构图**：脚线齐框底，非地面齐 —— **预期行为**。

### 12.9 测试分层（§10.7 之上）

| 层级 | 范围 |
|------|------|
| **单元** | §10.7 五例 + §12.3 scope 三例 + §12.4 longshot 不拆 + breath 锚点 |
| **Golden** | 新增 `_golden/editorial-portrait-row/`：1 章 3 人物竖版；`enabled` on/off 各一份 `expected.layout.json` |
| **Visual** | P0 人工；P3 probe。AC-ED-04 Playwright bbox **仅**测 contain 人物 fixture（Safari flaky 规避） |
| **Regression** | `demo-2025-2` curate + `enabled: false` layout json deep equal |

### 12.10 风险登记

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| §10 注册表漏改 | 中 | R-02 失效 / streak 错误 | PR-2 checklist 逐项 tick §10 |
| mobile 拆屏破坏 folio plate | 中 | 版式/序号错乱 | §12.4 首槽 inherit；AC-ED-08e |
| 双轨 template 长期并存 | 高 | 维护成本 | §12.7 决策日；未达标不升 ga |
| bottom center 与产品预期不符 | 中 | CSS 返工 | §12.8 P0 dogfood |
| probe CI 与 web 不一致 | 中 | 假红 | §12.5 P3 前 skip |

### 12.11 PR Review Checklist（复制到 PR 描述）

**PR-1（P0）**

- [ ] 仅 `data-pattern="screen-portrait-3-editorial"` 选择器，未改 legacy person-triple / portrait-3
- [ ] `journal-screens.css` + `journal-screens-overlays.css` 双文件同步
- [ ] `blur_fill` hint 已登记
- [ ] 手工 trip 验脚线 / gap / 无 blur
- [ ] probe 未误加 baseline（或已 skip）

**PR-2（P1a）**

- [ ] §10.1–10.5 注册表全勾
- [ ] `is_editorial_portrait_row_enabled` 单一入口
- [ ] planner + MCS 均走 `_maybe_editorial_portrait_row`
- [ ] §12.3 scope 单测
- [ ] AC-ED-01 / AC-ED-10
- [ ] `enabled: false` golden 零 diff

**PR-3（P1b）**

- [ ] legacy `screen-portrait-3` 与 editorial 共用拆屏
- [ ] longshot 不拆；plate 仅首槽（AC-ED-08d/e）
- [ ] AC-ED-08a/b/c
- [ ] 与 PR-2 独立可 revert
