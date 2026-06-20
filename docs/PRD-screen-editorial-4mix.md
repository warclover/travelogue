# Travelogue · 四图横竖交错拼图 PRD（screen-editorial-4mix）

| 属性 | 内容 |
|------|------|
| **文档版本** | v0.2 |
| **状态** | Approved · 待 P0 Kickoff（[评审会纪要](./acceptance-records/editorial-4mix-prd-review-2026-06-20.md) 2026-06-20） |
| **功能代号** | editorial-4mix（方案 B · 新建模板） |
| **模板 ID** | `screen-editorial-4mix` |
| **前置条件** | `layoutEngine=screens`；Phase 16 LTE 稳定；`inline-edit` / `copy-toggle` 已上线 |
| **关联文档** | [PRD-portrait-row-editorial.md](./PRD-portrait-row-editorial.md)、[PRD-screen-editorial-2land.md](./PRD-screen-editorial-2land.md)、[LAYOUT-PLANNER.md](./LAYOUT-PLANNER.md) |
| **设计参考** | 产品 mockup（2026-06 · 2×2 横竖棋盘 · 黑白杂志拼贴） |
| **更新日期** | 2026-06-20 |

> **定位**
>
> 新增 **`screen-editorial-4mix`**：一屏 **4 张照片槽**（2 横 + 2 竖）按 **棋盘格** 交错排列，**同行内行等高**（竖图高度 = 横图高度；顶齐 + 脚线齐）；**2 张横图各约占舞台面积 25%**；并 **预留 2land 式文案区**（Kicker + Body，`copy-display=photos` 时可 collapse）。  
> **不修改** 现有 `screen-landscape-2` / `screen-portrait-2` / mosaic 家族契约。

---

## 1. 已拍板决策（2026-06-20 · 产品确认）

| # | 议题 | 决策 |
|---|------|------|
| **D-01** | 主路径 | **方案 B**：新建 `screen-editorial-4mix`，legacy 模板零改动 |
| **D-02** | 照片位置 | **固定棋盘**：左上/右下 = 横图；右上/左下 = 竖图 |
| **D-03** | 行内对齐 | **行等高 + 顶齐 + 脚线齐**（竖槽 stretch 至行高；img `object-position: bottom center`，槽内 flex 脚线贴底） |
| **D-04** | 横图面积 | 每张横图 **display 面积 ≈ 舞台 25% ±3%**（非宽度 25%，指槽位在 16:9 舞台中的面积占比） |
| **D-05** | 文案 | **4 照片槽 + 2land 式文案区**（Kicker + Body）；非「仅 4 图满屏」 |
| **D-06** | 试点 | 默认 **关闭**（与 portrait-row-editorial 一致）；`trip.export` / allowlist 控制 |
| **D-07** | Mobile | Web 专用 pattern；mobile 面 **拆成 4× 单槽屏**（顺序 TL→TR→BL→BR）· P1 |
| **D-08** | 文案渲染 P0 | **Overlay 条带**（照片块外缘）；P1 扩 `rows: [1,3,2,1]` + `intentionalGaps` |
| **D-09** | 25% 量测口径 | **槽 bbox 面积**（非 img 可见像素）；AC-4M-03 量 `.layout-slot` |
| **D-10** | vs mosaic-4 | **editorial-4mix 优先**（enabled + 2L+2P 窗口）；`denseBudgetExempt: true` |
| **D-11** | 同章 rhythm | **editorial composite ≤1/章**（2land 与 4mix **互斥**） |
| **D-12** | 镜像变体 | **P2** · `screen-editorial-4mix-mirror`；P0–P1 不做 |

---

## 2. 设计北极星

> **四图棋盘 = 杂志拼贴页**：横竖交错、同行等高、横图克制（各约 1/4 屏），竖图补位；Z 字动线：**Kicker → 上行 → 下行 → Body**。

### 2.1 布局示意（照片 + 文案）

```text
┌─────────────────────────────────────────────────────────────┐
│  layout-screen（视觉 intrinsic · skip_stage_aspect）           │
│  ┌ Kicker copy gap ─────────────────────────────────────┐   │
│  │  地点 · 时刻 · 短句                                    │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────── row 1 (权重 3/5 高) ─────────────────┐   │
│  │ ┌─────────────┐ gap ┌──────────┐                      │   │
│  │ │ Land · TL   │     │ Port · TR│  ← 同行等高 H₁       │   │
│  │ │ ≈25% 面积   │     │ 高度=H₁  │                      │   │
│  │ └─────────────┘     └──────────┘                      │   │
│  └───────────────────────────────────────────────────────┘   │
│  ┌──────────────── row 2 (权重 2/5 高) ─────────────────┐   │
│  │ ┌──────────┐ gap ┌─────────────┐                      │   │
│  │ │ Port · BL│     │ Land · BR   │  ← 同行等高 H₂       │   │
│  │ │ 高度=H₂  │     │ ≈25% 面积   │                      │   │
│  │ └──────────┘     └─────────────┘                      │   │
│  └───────────────────────────────────────────────────────┘   │
│  ┌ Body copy gap ──────────────────────────────────────┐   │
│  │  一句感受或细节 · 收束                                  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**阅读动线（Z 字）**：Kicker → 横 TL → 竖 TR → 竖 BL → 横 BR → Body。

### 2.2 与 portrait-row-editorial / 2land 对照

| 维度 | 三竖 editorial | 2land | **4mix（本 PRD）** |
|------|----------------|-------|-------------------|
| 照片数 | 3 竖 | 2 横 | **2 横 + 2 竖** |
| 排列 | 单行 3 列 | 加权网格 + 文案 | **2 行棋盘交错** |
| 行高 | 三列统一 | 槽位固定 AR | **同行 L/P 等高** |
| 横图面积 | — | main 36% / tile 16% | **各横槽 ≈25%** |
| 文案 | 无 | Kicker + Body | **同 2land** |
| 舞台 | intrinsic | 16:9 | **intrinsic（render）** |

---

## 3. 几何与面积约束

### 3.1 轨道权重（LTE · 权威）

采用与 2land 相同的 **cols `[2, 3]` · rows `[3, 2]`** 权重系，使单个 1×1 单元面积可预测：

| 单元 | rect `[c0,c1,r0,r1]` | 类型 | 面积占比（16:9 舞台） |
|------|------------------------|------|------------------------|
| Kicker | `[1, 1, 0, 0]` * | copy gap | 2/5 × 1/5 = **4%**（整行顶栏 · 见 §3.3） |
| **Land TL** | `[1, 1, 1, 1]` | photo slot 0 | 2/5 × 3/5 = **24%** ≈ 25% |
| **Port TR** | `[2, 2, 1, 1]` | photo slot 1 | 3/5 × 3/5 = 36%（槽面积大；竖图按 AR 占宽） |
| **Port BL** | `[1, 1, 2, 2]` | photo slot 2 | 2/5 × 2/5 = **16%** |
| **Land BR** | `[2, 2, 2, 2]` | photo slot 3 | 3/5 × 2/5 = **24%** ≈ 25% |
| Body | `[1, 2, 3, 3]` * | copy gap | 见 §3.3 |

\* **v0.1 文案行**：Kicker / Body 暂占 **独立横条行**（`rows` 扩展为 `[1, 3, 2, 1]` 或 render overlay）；P0 可先 **CSS overlay 浮于照片块外缘**，P1 写入 `intentionalGaps` 正式 rect。面积公式仍按 §3.2 校验 **照片槽**。

### 3.2 行等高（D-03 · 核心）

对 **照片区** 内两行（不含 Kicker/Body 条）：

1. **Row 1**（`r=1`）：Land TL + Port TR 共享行高 **H₁ = 3/(3+2) × 照片区高度**。
2. **Row 2**（`r=2`）：Port BL + Land BR 共享行高 **H₂ = 2/(3+2) × 照片区高度**。
3. **H₁ ≠ H₂** 为预期（与参考图一致：上行略高）。

**槽内规则（render/CSS · 与三竖 editorial 同族）：**

```css
/* 同行照片槽 stretch；竖槽 flex 脚线 */
.layout-slot { display: flex; flex-direction: column; justify-content: flex-end; min-height: 100%; }
.layout-slot__img { object-position: bottom center; /* 脚线 */ }
/* 行 grid: align-items: stretch; grid-template-rows: auto auto; */
```

**顶齐 + 脚线齐**：行高由本行 **横图槽**（目标 25% 面积反推宽度）与 **竖图 native AR** 共同约束；竖图 `height` 贴满槽高（contain/cover 策略见 §6），槽顶 = 行顶、img 底 = 槽底 = 行脚线。

### 3.3 文案区（D-05 · 2land  parity）

| copy slot | 角色 | 约束 | collapse |
|-----------|------|------|----------|
| **Kicker** | 左上短句 | `maxChars: 30`；`inline-edit` | `copy-display=photos` 时隐藏 |
| **Body** | 右下收束 | `maxChars: 80` | 同上 |

- 文案 **不占用照片槽 rect**；渲染为照片块 **上方/下方/外侧** 条带（P0 overlay），或扩展 LTE `rows`（P1）。
- 空文案 + 纯照片模式：collapse 后 **仅显示 4 图棋盘**（与参考 mockup 一致）。

---

## 4. LTE YAML（草案）

```yaml
id: screen-editorial-4mix
version: 1
status: experimental
kind: composite
displayName: editorial · 4mix · chess-2L2P
description: >
  四图横竖棋盘：TL/BR 横图（各≈25% 舞台面积），TR/BL 竖图（同行等高）；
  Kicker/Body 文案区（2land 同族）；视觉 intrinsic render。
aesthetic: airy

stage:
  aspect: "16:9"      # LTE/probe 占位；render skip_stage_aspect
  cols: [2, 3]
  rows: [3, 2]

photoCount:
  min: 4
  max: 4

mix:
  portrait: 2
  landscape: 2

slots:
  - index: 0
    rect: [1, 1, 1, 1]
    role: landscape
    fit: auto
    slotHint: land-tl
  - index: 1
    rect: [2, 2, 1, 1]
    role: portrait
    fit: auto
    slotHint: port-tr
  - index: 2
    rect: [1, 1, 2, 2]
    role: portrait
    fit: auto
    slotHint: port-bl
  - index: 3
    rect: [2, 2, 2, 2]
    role: landscape
    fit: auto
    slotHint: land-br

constraints:
  portrait_forbidden_in_wide_slots: []
  landscape_forbidden_in_tall_slots: []
  intentionalGaps: []   # P1: kicker/body rects
  slotOrderPolicy: chess-2L2P   # planner 须重排为 TL-L, TR-P, BL-P, BR-L

copySlots:
  - id: kicker
    role: kicker
    maxChars: 30
    placeholder: "地点 · 时刻"
  - id: body
    role: body
    maxChars: 80
    placeholder: "一句感受或细节"

scoring:
  base_weight: 0.88
  tags: [editorial, mixed-4, chess, airy]
  rhythm:
    max_per_chapter: 1

render:
  gridClass: layout-screen__grid--editorial-4mix
  cssBundle: journal-screens.css
  fitPolicy: row_matched
  layoutHint: editorial-4mix
  copyCollapse: photos_only
  presentation: editorial-4mix
```

---

## 5. Render 契约

| 字段 | 值 |
|------|-----|
| `data-pattern` | `screen-editorial-4mix` |
| `data-layout-hint` | `editorial-4mix` |
| `--screen-aspect` | **不写**（`skip_stage_aspect=True`） |
| 横图槽 CSS 变量 | 可选 `--editorial-4mix-land-area-target: 0.25` |
| 行 CSS 变量 | `--editorial-4mix-row1-fr: 3; --editorial-4mix-row2-fr: 2` |

**双文件同步**：`journal-screens.css` + `journal-screens-overlays.css`（同 portrait-row-editorial §12.6）。

---

## 6. 照片 fit 策略

| 槽 | 默认 fit | 说明 |
|----|----------|------|
| Land TL / BR | `cover`（人物 `contain`） | 填满 ≈25% 面积槽 |
| Port TR / BL | `contain`（人物）/ `cover`（纯风景 · P2 可随机） | 同行等高，不裁脸 |

人物检测：`asset_has_person` → 竖/横槽均 **contain + 脚线**。

---

## 7. Curate / Planner

### 7.1 窗口条件

- 连续或同 burst **2 landscape + 2 portrait**（顺序任意）。
- Planner **重排**为固定 chess：`[L, P, P, L]`（TL, TR, BL, BR）。
- 横图优先 **sharpness/hero** 分最高者占 TL 或 BR（默认 TL=稍宽行）。

### 7.2 启用方式（试点）

```yaml
layout:
  editorial_4mix:
    enabled: false
    trip_allowlist: []
```

```json
"export": { "editorial4Mix": true }
```

优先级：`trip.export.editorial4Mix` > allowlist > global `enabled`。

### 7.3 与 MCS

- 4 槽 composite；**不计入** Phase 21 dense collage（≥4 槽）配额误判——显式 `denseBudgetExempt: true`。
- 与 `screen-editorial-2land` 同章 **互斥**（rhythm：`max_per_chapter: 1` editorial composite）。

---

## 8. 验收标准

| ID | 标准 | 阶段 |
|----|------|------|
| AC-4M-01 | 开关关闭时 legacy golden **零 diff** | P1 |
| AC-4M-02 | 开启后 demo ≥1 屏 `data-pattern="screen-editorial-4mix"` | P1 |
| AC-4M-03 | Land TL / BR 槽 **display 面积 22–28%** 舞台（@1440） | P0 |
| AC-4M-04 | Row1：TL 横与 TR 竖 **顶/底 bbox 偏差 ≤2px** | P0 |
| AC-4M-05 | Row2：BL 竖与 BR 横 **顶/底 bbox 偏差 ≤2px** | P0 |
| AC-4M-06 | Kicker/Body 可 inline 编辑；`copy-display=photos` collapse | P1 |
| AC-4M-07 | 无固定 9:16 tone 信箱；intrinsic 舞台 | P0 |
| AC-4M-08 | mobile 拆 4× 单槽，顺序不变 | P1 |
| AC-4M-09 | probe baseline PNG 入库 | P3 |
| AC-4M-10 | `copy-display=photos` 时无可见 Kicker/Body DOM（非透明占位） | P1 |
| AC-4M-11 | mobile 无整块 4mix grid；拆 4× 单槽，顺序 TL→TR→BL→BR | P1 |
| AC-4M-12 | longshot 面不出现四连 mobile 展开 | P1 |

---

## 9. 分期交付

| 阶段 | 内容 | PR |
|------|------|-----|
| **P0** | LTE YAML + CSS 棋盘 + 行等高 + skip_stage_aspect + AC-4M-03/04/05/07 | PR-1 |
| **P1a** | 注册表 + config + planner/MCS + rhythm + AC-4M-01/02 | PR-2 |
| **P1b** | copy overlay + inline-edit + AC-4M-06/10 | PR-3 |
| **P1c** | mobile 拆 4× 单槽 + AC-4M-08/11/12 | PR-4 |
| **P2** | 风景竖槽 cover 随机（可选）+ MCS 微调 | PR-5 |
| **P3** | probe + dogfood 对比页 + G-4M-01 blind review | PR-6 |

**P0 不含**：planner 自动替换（可手动 `patternId` 验 CSS）。

---

## 10. 开放项（已闭合 · 2026-06-20 评审会）

| ID | 问题 | 决议 | 状态 |
|----|------|------|------|
| O-4M-01 | Kicker/Body grid 行 vs overlay | P0 overlay；P1 `rows [1,3,2,1]` | ✅ → D-08 |
| O-4M-02 | 25% 槽 vs img | **槽面积** | ✅ → D-09 |
| O-4M-03 | 镜像变体 | P2 · `screen-editorial-4mix-mirror` | ✅ → D-12 |
| O-4M-04 | vs mosaic-4 | editorial-4mix 优先 | ✅ → D-10 |

---

## 11. 附录 · 工程注册表（摘要）

实现时须显式登记（不可假设自动继承）：

- `schemas/trip.schema.json` · `patternId` + `layoutHint: editorial-4mix`
- `screen_layout_state.py` · rhythm / orientation（计入 mixed 屏，非 triple streak）
- `render_binding.py` · `gridClass: layout-screen__grid--editorial-4mix`
- `context.py` · `skip_stage_aspect` + copy slot render
- `journal-screens.css` / `overlays.css` · 双文件
- `tests/test_editorial_4mix.py` · 面积 + 行 bbox golden

---

## 12. 开发负责人实施附录（v0.2 · 评审会并入）

> 来源：[editorial-4mix-prd-review-2026-06-20.md](./acceptance-records/editorial-4mix-prd-review-2026-06-20.md)

### 12.1 PR 切分（强制）

| PR | 阶段 | 内容 | 关键 AC |
|----|------|------|---------|
| **PR-1** | P0 | LTE YAML + CSS + render hint + blur + skip_stage_aspect | AC-4M-03/04/05/07 |
| **PR-2** | P1a | 注册表 + config + `_maybe_editorial_4mix` + rhythm + MCS | AC-4M-01/02 |
| **PR-3** | P1b | copy overlay + inline-edit + collapse | AC-4M-06/10 |
| **PR-4** | P1c | mobile 4× 拆屏 + folio/longshot 连带 | AC-4M-08/11/12 |
| **PR-5** | P2 | 风景竖 cover 随机 | — |
| **PR-6** | P3 | probe + dogfood 对比页 | AC-4M-09；G-4M-01 |

P0 **刻意不上** planner；P2 **刻意不做** mirror 变体。

### 12.2 配置读取（单一入口）

**优先级（高 → 低）：**

1. `trip.export.editorial4Mix`（bool）
2. `trip_id ∈ layout.editorial_4mix.trip_allowlist`
3. `layout.editorial_4mix.enabled`（默认 `false`）

```text
is_editorial_4mix_enabled(trip, cfg) -> bool
maybe_editorial_4mix(pattern_id, asset_ids, assets_map, trip, cfg)
    -> tuple[pattern_id, layout_hint | None]
```

### 12.3 Planner 窗口与 chess 重排

| 条件 | 行为 |
|------|------|
| 4 槽窗口含 **2 landscape + 2 portrait** | 重排 slot 顺序为 `[L,P,P,L]`（TL, TR, BL, BR） |
| hero 分 | 最高横图 → **TL**（slot 0）；次高 → **BR**（slot 3） |
| enabled=false | 零替换；legacy golden deep equal |

**单测（PR-2 必含）：**

- `test_editorial_4mix_chess_reorder`
- `test_editorial_4mix_prefers_over_mosaic_4_when_enabled`
- `test_editorial_composite_mutex_2land_and_4mix`

### 12.4 Mobile 拆屏连带规则

| 连带 | 规则 |
|------|------|
| **顺序** | TL → TR → BL → BR |
| **longshot** | **不拆屏** |
| **folio plate** | 拆后 **slot 0（TL）** inherit plate meta |
| **breath-pause** | 原 `screens[]` 序锚点不变 |
| **screenplay** | 原一屏计 **4** 个 mobile layout-screen step |

### 12.5 LTE probe 与占位 aspect

YAML 占位 `16:9` 与 web render（skip stage aspect + intrinsic CSS）** intentionally 不一致**。

| 阶段 | 要求 |
|------|------|
| P0–P2 | probe baseline **skip** 或 `@pytest.mark.xfail(reason="P3 baseline")` |
| P3 | 重拍前注明 probe 参考态 ≠ web render 态 |

### 12.6 CSS 双文件同步

须 **同时**修改：

- `templates/visual-journal/journal-screens.css`
- `templates/visual-journal/journal-screens-overlays.css`

合并前跑 `tests/test_lte_css_sync.py`。generic contain 规则须加：

```css
:not([data-pattern="screen-editorial-4mix"])
```

### 12.7 Beta → GA 决策指标（P3 前）

| # | 指标 |
|---|------|
| G-4M-01 | dogfood ≥ **5** 屏 4mix；blind review **≥ 4/5** 不劣于 mosaic-4 / 双竖组合 |
| G-4M-02 | AC-4M-01～12 + §12.3 单测 **全绿** |
| G-4M-03 | `enabled: false` 下 `demo-2025-2` layout golden **deep equal** |
| G-4M-04 | mobile 拆屏（PR-4）合入且无 folio/plate 回归 |

未达标保持 `experimental`；**禁止** silent 默认 `enabled: true`。

### 12.8 视觉 acceptance note

- 行对齐量 **槽 bbox**；竖槽面积 36% 但 contain 后 img 窄条 — **两侧留白为预期**。
- 脚线对齐 **`<img>` 底边**，非语义地平线（同 portrait-row §12.8）。

### 12.9 PR Review Checklist（PR-1）

- [ ] 仅 `data-pattern="screen-editorial-4mix"` 选择器，未改 legacy mosaic/landscape
- [ ] 双 CSS 文件同步
- [ ] `blur_fill` hint 已登记
- [ ] generic contain 已排除 4mix
- [ ] 手工 trip 验行 bbox + 25% 横槽
- [ ] probe 未误加 baseline

---

## 13. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-06-20 | 初稿；确认棋盘位置、行等高脚线、横图≈25% 面积、4 图 + 2land 文案 |
| v0.2 | 2026-06-20 | 评审会通过：闭合 O-4M-01～04；新增 D-08～D-12、AC-4M-10～12、§12 实施附录 |
