# Travelogue · 双图编辑拼版 PRD（screen-editorial-2land）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | v0.1.0 |
| **状态** | Draft · 待评审 |
| **模板 ID** | `screen-editorial-2land`（主版）· `screen-editorial-2land-mirror`（镜像变体，P1） |
| **文档类型** | Web 端 LTE composite 模板 + 屏内文案槽 PRD |
| **前置条件** | Phase 16 LTE 稳定；`layout_engine=screens`；`inline-edit` / `copy-toggle` 已上线 |
| **关联文档** | [web端模板.prd](./web端模板.prd)、[PRD-PHASE16-layout-template-engine.md](./PRD-PHASE16-layout-template-engine.md)、[PRD-COPY-OPTIMIZATION.md](./PRD-COPY-OPTIMIZATION.md)、[PRD-PHASE21-mosaic-density-budget.md](./PRD-PHASE21-mosaic-density-budget.md)、[PRD-EXPERIENCE-附录C-Folio版式.md](./PRD-EXPERIENCE-附录C-Folio版式.md)、[RENDER-CONTRACT.md](./RENDER-CONTRACT.md) |
| **设计参考** | 产品 mockup（2026-06 · 左上/右下文本框 + 右上大图 + 左下小图 · Z 字动线） |
| **更新日期** | 2026-06-20 |

> **定位**
>
> - 在 **16:9 Web 舞台**上，用 **2 张横图（一大一小）+ 2 处屏内文案区** 组成一屏「杂志对开感」拼版。
> - 两照片槽 **displayAspect 均为 16:9**；4:3 / 3:2 等常规横图通过槽内 `cover` / `contain` 适配，**不在 ingest 阶段统一裁切**。
> - 文案遵循 [PRD-COPY-OPTIMIZATION.md](./PRD-COPY-OPTIMIZATION.md) 铁律：**短、可藏、可改、图主文辅**；纯照片模式下文案区 collapse，fallback 为无字双图 stack。

---

## 1. 背景与问题

### 1.1 用户诉求

Web 端游记在「一屏一展示」前提下，常见组合为：

| 场景 | 现有 pattern | 缺口 |
|------|--------------|------|
| 2 张横图连排 | `screen-landscape-2`（竖向 stack，槽 AR≈3.56） | 无主次、无文案位，像相册条 |
| 1 图 + 长文案 | `screen-spread`（Folio full 块） | 仅 1 图；与 `layout-screen` 栅格体系分离 |
| 5–6 张 hero 拼图 | `screen-mosaic-5/6-main-*` | 信息密度高，不适合「两张精选 + 一句感受」 |

用户 mockup 表达的需求：

1. **一屏 2 槽**，均面向 **16:9 横图**（兼容纳 **4:3**）。
2. **一大一小**：主图占视觉主导，辅图补充细节或氛围。
3. **留白处文本框**：用户可写短文案，形成 **Z 字阅读动线**（标题感 → 主图 → 辅图 → 收束句）。

### 1.2 用户可感知问题

| ID | 问题 | 用户体感 |
|----|------|----------|
| **E2L-P-01** | 双横图只能等分 stack | 「两张好图摆在一起，像手机相册截图」 |
| **E2L-P-02** | 文案与照片分块（spread） | 「字和图片不在同一屏，杂志感断裂」 |
| **E2L-P-03** | 多槽拼图过密 | 「只想放两张图加一句话，却被排成六宫格」 |
| **E2L-P-04** | 纯照片模式未考虑 | 「关掉文案后留下空框，像缺了一块」 |

### 1.3 与现有体系的关系

| 子系统 | 关系 |
|--------|------|
| **LTE（Phase 16）** | 新 composite 模板；使用 **加权轨道** `stage.cols/rows`；`intentionalGaps` 声明文案格 |
| **MCS / screen_planner** | 2 张横图窗口候选；有/无文案信号影响打分 |
| **Phase 21 dense budget** | 本模板 **2 槽**，**不计入** dense collage（≥4 槽）配额 |
| **文案优化 PRD** | 屏内 copy 走 sparse 策略；`copy-display=photos` 时隐藏 |
| **Folio `screen-spread`** | 互补：spread 适合「一图长文」；本 pattern 适合「双图短点缀」 |

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 | 验收口径 |
|----|------|----------|
| **G-E2L-01** | 单屏 **2 照片槽 + 2 文案区**，舞台 **16:9** | 探针截图 + fixture 回归 |
| **G-E2L-02** | 两照片槽 **displayAspect ≈ 1.78**（16:9） | LTE geometry 校验 + slot-aspect 文档 |
| **G-E2L-03** | **4:3 / 3:2** 横图可入槽 | cover 默认；人物槽 auto→contain；金样 4:3 素材 |
| **G-E2L-04** | 主次分明：slot0 主图面积 **≥ 1.8×** slot1 | 视觉验收 + 权重公式 |
| **G-E2L-05** | 文案 **inline 可编辑**，保存 `trip.json` | draft + `inline-edit` E2E |
| **G-E2L-06** | **纯照片模式**无空框 | `copy-display=photos` 探针 0 文案 DOM |
| **G-E2L-07** | 与现有渲染链兼容 | `patternId → gridClass → journal-screens.css` |
| **G-E2L-08** | MCS 可解释选用 | 决策日志含 `patternId` + copy 信号 |

### 2.2 非目标

- 不做拖拽自由排版或用户手动指定单屏 pattern UI（P2）。
- 不在本 PRD 范围扩展 **text-slot** 为 LTE 一等公民 schema（P1 用 gap + render overlay 即可）。
- 不支持竖图混排（竖图仍走 `screen-portrait-*` / `screen-portrait-1-landscape-2`）。
- 不做视频与照片同屏编辑拼版。
- 不替代 `screen-spread` / `screen-plate`；Folio 块保持独立。
- 手机端 9:16 单列 **不** 启用本 pattern（Web / `exportLayout: web` 专用）。

---

## 3. 已拍板决策（评审前建议默认值）

| 项 | 决策 | 说明 |
|----|------|------|
| **pattern 命名** | `screen-editorial-2land` | kind=`composite`；GA 前 status=`experimental` |
| **照片槽数** | 2 | `photoCount.min=max=2`；`mix.landscape=2` |
| **槽位比例** | 两槽均 **16:9** | 靠网格权重实现，非裁切用户原图 |
| **主槽** | index **0** · 右上 · `role: main` | MCS 优先 hero 分最高横图 |
| **辅槽** | index **1** · 左下 · `role: landscape` | 时间邻近 ≤30s 或同 cluster 加分 |
| **网格权重** | `cols: [2, 3]` · `rows: [3, 2]` | 左窄右宽、上高下低 |
| **文案来源 P0** | **用户 inline 编辑** + 可选 AI 预填（sparse） | 不强制 LLM |
| **文案来源 P1** | 可 **seed** 章 `decorLine` / `lead` 首句 | 用户改后锁定 |
| **纯照片 fallback** | collapse gap · 可选降级 `screen-landscape-2` | 由 render 读 `copy-display` |
| **镜像变体** | P1 · `screen-editorial-2land-mirror` | 主图左上、辅图右下 |
| **dense 预算** | **豁免** | 2 槽不计入 Phase 21 dense collage |

---

## 4. 术语

| 术语 | 定义 |
|------|------|
| **Editorial 2-land** | 本 PRD 所指双横图编辑拼版 family |
| **主槽（main）** | slot 0 · 右上 · 面积大 · 承载 hero 横图 |
| **辅槽（tile）** | slot 1 · 左下 · 面积小 · 氛围/细节图 |
| **文案格（copy gap）** | `intentionalGaps` 声明的非照片单元格，渲染为可编辑文本区 |
| **Kicker** | 左上短文案 · 地点/时间/一句标题感 |
| **Body** | 右下收束文案 · 感受/细节 · 略长 |
| **Z 字动线** | 阅读顺序：Kicker → Main → Tile → Body |
| **Collapse 模式** | 纯照片或 copy 为空时，文案格不占视觉占位 |

---

## 5. 版式规格

### 5.1 布局示意（主版 · hero-right）

```text
┌─────────────────────────────────────────────────────────┐
│  16:9 layout-screen 舞台                                 │
│  ┌──────────────┬────────────────────────────────────┐  │
│  │              │                                    │  │
│  │   Kicker     │         Main (slot 0)              │  │
│  │  copy gap    │         16:9 · role: main          │  │
│  │  [1,1,1,1]   │         rect [2,2, 1,1]            │  │
│  │              │                                    │  │
│  ├──────────────┤                                    │  │
│  │              │                                    │  │
│  │ Tile (slot 1)│                                    │  │
│  │ 16:9 · land. │                                    │  │
│  │ [1,1, 2,2]   │                                    │  │
│  ├──────────────┴────────────────────────────────────┤  │
│  │              Body copy gap [2,2, 2,2]              │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘

轨道权重：cols [2, 3] · rows [3, 2]
```

### 5.2 槽位与 gap 几何

| 单元 | type | rect `[c0,c1,r0,r1]` | displayAspect ≈ | 面积占比（舞台） |
|------|------|----------------------|-----------------|------------------|
| Kicker | copy gap | `[1, 1, 1, 1]` | —（文本盒） | 2/5 × 3/5 = **24%** |
| Main | photo slot 0 | `[2, 2, 1, 1]` | **1.7778** | 3/5 × 3/5 = **36%** |
| Tile | photo slot 1 | `[1, 1, 2, 2]` | **1.7778** | 2/5 × 2/5 = **16%** |
| Body | copy gap | `[2, 2, 2, 2]` | —（文本盒） | 3/5 × 2/5 = **24%** |

**主次比**：Main 面积 / Tile 面积 = (3×3)/(2×2) = **2.25**（满足 G-E2L-04 ≥1.8）。

**公式**（LTE §4.6）：

```text
slotWidth  = (Σ col weights in rect) / (Σ all col weights)
slotHeight = (Σ row weights in rect) / (Σ all row weights)
displayAspect = (slotWidth × stageW) / (slotHeight × stageH)   # stage 16:9
```

### 5.3 LTE YAML 权威定义（草案）

```yaml
id: screen-editorial-2land
version: 1
status: experimental
kind: composite
displayName: editorial · 2land · kicker-main-tile-body
description: >
  双横图编辑拼版：右上 main + 左下辅图，两槽均为 16:9；
  左上 kicker、右下 body 为 intentionalGaps 文案格（Z 字动线）。
aesthetic: airy

stage:
  aspect: "16:9"
  cols: [2, 3]
  rows: [3, 2]

photoCount:
  min: 2
  max: 2

mix:
  portrait: 0
  landscape: 2

slots:
  - index: 0
    rect: [2, 2, 1, 1]
    role: main
    fit: auto
    visualWeight: 1.0
  - index: 1
    rect: [1, 1, 2, 2]
    role: landscape
    fit: cover
    visualWeight: 0.55

constraints:
  portrait_forbidden_in_wide_slots: []
  landscape_forbidden_in_tall_slots: []
  intentionalGaps:
    - [1, 1, 1, 1]   # kicker
    - [2, 2, 2, 2]   # body
  mainSlotPolicy:
    slotIndex: 0
    targetDisplayAspect: 1.7778
    eligibleAspectKinds: [landscape]
    forbidKinds: [panorama, tall, portrait, square]
    arLadderTol: 0.08
    preferLadder: [1.7778, 1.5, 1.3333]

copySlots:
  - id: kicker
    gapRect: [1, 1, 1, 1]
    role: kicker
    maxChars: 30
    placeholder: "地点 · 时刻"
  - id: body
    gapRect: [2, 2, 2, 2]
    role: body
    maxChars: 80
    placeholder: "一句感受或细节"

scoring:
  base_weight: 0.92
  tags: [editorial, landscape-pair, airy]
  rhythm:
    max_per_chapter: 2
    diversity_bonus: 0.06

render:
  gridClass: layout-screen__grid--editorial-2land
  cssBundle: journal-screens.css
  fitPolicy: auto_delegate
  copyCollapse: photos_only   # copy-display=photos 时 collapse gaps
```

> **Schema 说明**：`copySlots` 为 **本 PRD 新增 LTE 扩展字段**（P0 可先 hardcode 于模板 + render，P1 写入 `layout_template.schema.json`）。

### 5.4 镜像变体（P1）

| 项 | 主版 | mirror |
|----|------|--------|
| patternId | `screen-editorial-2land` | `screen-editorial-2land-mirror` |
| Main rect | `[2, 2, 1, 1]` | `[1, 1, 1, 1]` |
| Tile rect | `[1, 1, 2, 2]` | `[2, 2, 2, 2]` |
| Kicker gap | `[1, 1, 1, 1]` | `[2, 2, 1, 1]` |
| Body gap | `[2, 2, 2, 2]` | `[1, 1, 2, 2]` |
| cols 权重 | `[2, 3]` | `[3, 2]` |

MCS 在章内 **交替** 选用主版/mirror，避免全书同一对角线。

---

## 6. 照片适配策略

### 6.1 长宽比

| 素材类型 | AspectKind | 入槽策略 |
|----------|------------|----------|
| 16:9 | landscape | 理想；main 槽优先 |
| 4:3 · 3:2 | landscape | `cover` 默认；主槽 `auto` 可 contain |
| 全景 ≥2:1 | panorama | **禁止** main；可入 tile 需 sign-off |
| 竖图 | portrait | **禁止**（模板 mix 不匹配） |
| 方图 | square | **禁止** |

### 6.2 fit 策略

| 槽 | 默认 fit | auto 规则 |
|----|----------|-----------|
| main (0) | auto | 人物 → contain + `--screen-tone`；风景 → cover |
| tile (1) | cover | 辅图允许略裁 |

### 6.3 focalPoint

沿用现有 `layout-slot__img` + `--focal-x/y`；main 槽 cover 裁切时优先保留 focal。

---

## 7. 文案规格

### 7.1 产品原则（继承 COPY PRD）

1. **短**：Kicker ≤30 字 · Body ≤80 字；AI 预填合计建议 ≤40 字。
2. **可藏**：`copy-display=photos` → 文案格 collapse，照片格扩展占满（见 §8.3）。
3. **可改**：draft 下 `contenteditable` + `inline-edit` patch。
4. **图主文辅**：空文案允许发布；不强制 AI 生成。

### 7.2 文案角色

| 字段 | 位置 | 用途 | 字数 | 排版 |
|------|------|------|------|------|
| `copy.kicker` | 左上 | 地点、日期、短标题 | ≤30 | 左对齐 · sans · 略小 |
| `copy.body` | 右下 | 感受、细节、收束 | ≤80 | 左对齐 · serif 可选 · 2–3 行 clamp |

### 7.3 数据模型（`layoutScreen` 扩展）

在 `schemas/trip.schema.json` · `layoutScreen` 增加可选字段：

```json
{
  "screenId": "ch01-s03",
  "patternId": "screen-editorial-2land",
  "copy": {
    "kicker": "林芝 · 清晨",
    "body": "云开了半面，湖像刚醒。"
  },
  "copyMeta": {
    "kickerSource": "user",
    "bodySource": "ai_sparse"
  },
  "slots": [ ... ]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `copy.kicker` | string | 否 | 空则 UI 占位或 collapse |
| `copy.body` | string | 否 | 空则 UI 占位或 collapse |
| `copyMeta.*Source` | `user \| ai_sparse \| chapter_seed \| empty` | 否 | 可观测；不影响渲染 |

**inline-edit path**（draft）：

```text
chapters.{chapterId}.screens.{screenId}.copy.kicker
chapters.{chapterId}.screens.{screenId}.copy.body
```

Guardrail：沿用 `apply_copy_patches` 白名单；禁止 patch `slots` 与 `patternId` 同批混写。

### 7.4 AI 预填（P1 · 可选）

| 条件 | 行为 |
|------|------|
| 用户已编辑 | **不覆盖** |
| `copy-scope=sparse` 且章有 `decorLine` | kicker ← decorLine；body 留空或 LLM 1 句 |
| fact 不足 | **skip**，两字段皆空 |
| 纯照片 trip | 不调用 narrate |

---

## 8. 渲染契约

### 8.1 DOM 结构（`layout-screen.hbs` 扩展）

在 `layout-screen__grid` 内，照片槽之外插入 **copy 单元**：

```html
<div class="layout-screen__grid layout-screen__grid--editorial-2land">
  <div class="layout-copy layout-copy--kicker" data-copy-slot="kicker" data-editable data-edit-path="...">
    {{copy.kicker}}
  </div>
  <figure class="layout-slot" data-slot="0" data-role="main">...</figure>
  <figure class="layout-slot" data-slot="1" data-role="landscape">...</figure>
  <div class="layout-copy layout-copy--body" data-copy-slot="body" data-editable data-edit-path="...">
    {{copy.body}}
  </div>
</div>
```

Grid 区域命名（CSS grid-area）：

| area | 内容 |
|------|------|
| `kicker` | 文案 |
| `main` | slot 0 |
| `tile` | slot 1 |
| `body` | 文案 |

### 8.2 样式要点

| Token / 规则 | 值 |
|--------------|-----|
| gap 背景 | `var(--screen-tone)` 或 `--folio-paper`（folio on） |
| kicker 字号 | `clamp(0.75rem, 1.2vw, 0.95rem)` · mono 可选 |
| body 字号 | `clamp(0.9rem, 1.5vw, 1.1rem)` · line-height 1.45 |
| 最大行数 | kicker 2 行 · body 3 行 · `line-clamp` + 溢出省略 |
| 空态 draft | 虚线框 + placeholder |
| 空态 publish | 无占位框（collapse 或透明） |

### 8.3 纯照片模式（collapse）

当 `html[data-copy-display="photos"]`：

1. `.layout-copy` **不渲染**或 `display: none`。
2. 网格 **重排**为双图占满（P0 最小实现：两图保持原 rect，gap 区域留 `--screen-tone` 色带；P1：动态改为 `screen-landscape-2` 等价 stack）。

**P0 验收**：无「文本框」字样、无虚线空框。

### 8.4 与 `screen-spread` 差异

| 项 | screen-spread | screen-editorial-2land |
|----|---------------|------------------------|
| 照片数 | 1 | 2 |
| 结构 | 独立 `data-block` | `layout-screen` 栅格内 |
| 文案长度 | 可较长 + pull quote | 极短 kicker + body |
| Folio | full 档 | web screens 通用 |
| MCS 窗宽 | 不参与 | **2** |

---

## 9. 策展与选用（MCS / screen_planner）

### 9.1 触发条件

| 条件 | 要求 |
|------|------|
| 窗宽 | `len(window) == 2` |
| 构图 | 2× `landscape`（含 4:3 归入 landscape） |
| 引擎 | `layout_engine=screens` · Web export |
| 禁用 | longshot · mobile layout |

### 9.2 候选与打分

**纳入候选**当：

- `screen_slots_geometry_ok` 通过；
- main 槽资产通过 `mainSlotPolicy`（R-MAIN-AR-01 子集）；
- 非连续第二屏 editorial-2land（ rhythm `max_per_chapter: 2`）。

**加分项**：

| 特征 | 权重方向 |
|------|----------|
| main hero_score 高 | + |
| 两图 `takenAt` 差 ≤30s | + |
| 同 semantic cluster | + |
| 章内已有 decorLine / 用户 voice | +（倾向选用，便于填 kicker） |
| 前一屏为 dense collage | +（呼吸） |

**减分项**：

| 特征 | 权重方向 |
|------|----------|
| 两图 hero_score 接近 | −（难分主次 → 降级 `screen-landscape-2`） |
| 章内已有 2 屏 editorial-2land | −（达上限 hard reject） |
| 无 copy 信号且 `layoutDensity=hero_first` | − |

### 9.3 与 `screen-landscape-2` 关系

| 场景 | 选用 |
|------|------|
| 2 横图 · 无文案 · hero_first | `screen-landscape-2` |
| 2 横图 · 有 decorLine/voice · balanced | **优先** `screen-editorial-2land` |
| 2 横图 · 用户已填 screen.copy | **强制** editorial（若几何 OK） |

---

## 10. 生命周期与发布

### 10.1 LTE 注册

| 阶段 | status | MCS | 说明 |
|------|--------|-----|------|
| W0 | experimental | 否 | YAML + validator + probe |
| W1 | beta | rollout 10% | 内部 dogfood |
| W2 | ga | 全量 | 过 admission + 人工 sign-off |

### 10.2 Admission 检查

- [ ] `python -m travelogue.layout_templates.cli validate`
- [ ] `export --sync-journal` CSS 生成
- [ ] probe 截图 vs baseline
- [ ] `trip.schema.json` 增加 `patternId` enum
- [ ] fixture：`tests/_golden/editorial-2land/`

### 10.3 Feature flag

```yaml
# travelogue/layout_templates/lte_policy.yaml（建议）
overrides:
  enable_editorial_2land: false   # beta 前默认关
```

---

## 11. 验收标准

| ID | 级别 | 描述 |
|----|------|------|
| **AC-E2L-01** | P0 | 16:9 舞台 · 探针两槽 displayAspect ∈ [1.70, 1.85] |
| **AC-E2L-02** | P0 | Main 面积 / Tile 面积 ≥ 1.8 |
| **AC-E2L-03** | P0 | 4:3 素材 main cover 无 focal 丢失（人工 5 例） |
| **AC-E2L-04** | P0 | draft inline-edit 保存 `copy.kicker/body` 到 trip.json |
| **AC-E2L-05** | P0 | `copy-display=photos` 无文案 DOM / 无空框 |
| **AC-E2L-06** | P0 | 竖图窗口 **不** 命中本 pattern |
| **AC-E2L-07** | P1 | 章内 ≤2 屏 editorial；第 3 屏 reject |
| **AC-E2L-08** | P1 | mirror 变体交替出现（同章主版+mirror ≤2） |
| **AC-E2L-09** | P1 | AI sparse 预填不覆盖 user 编辑 |
| **AC-E2L-10** | P2 | Studio 决策日志展示选用原因 |

---

## 12. 实施路线

| 阶段 | 交付 | 模块 |
|------|------|------|
| **W0 · 几何** | YAML + css_gen + probe baseline | `layout_templates/` · `journal-screens.css` |
| **W0 · 渲染** | hbs copy 单元 + CSS | `layout-screen.hbs` · `journal-screens.css` |
| **W1 · 数据** | `trip.schema` · context 映射 | `schemas/` · `render/context.py` |
| **W1 · 编辑** | inline-edit path + guardrail | `inline-edit.js` · `apply_copy_patches` |
| **W1 · MCS** | 2 窗候选 + scoring | `screen_planner` · `layout_scoring` |
| **W2 · 文案** | AI sparse seed（可选） | `llm_narrate` · decorLine 桥接 |
| **W2 · 镜像** | mirror YAML + 节奏 | LTE · MCS |

**建议实施文档**：`IMPLEMENTATION-screen-editorial-2land.md`（W0 启动时创建）。

---

## 13. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| gap 文案非 LTE 原生 | schema 漂移 | P0 render hardcode；P1 正式 `copySlots` |
| 小图槽过小 | 辅图看不清 | 权重下限 cols 左列 ≥2/5；用户可 swap 主辅（P2） |
| 空文案像缺块 | 发布态丑 | collapse + tone 填色 |
| 与 landscape-2 抢窗 | 行为不确定 | 明确 copy 信号优先级（§9.3） |
| 长文案溢出 | 破版 | maxChars + line-clamp + 保存校验 |

---

## 14. 开放问题（评审待定）

| # | 问题 | 选项 |
|---|------|------|
| Q1 | P0 collapse 是 **hide copy** 还是 **重排为 landscape-2**？ | A hide · B 重排（推荐 P1） |
| Q2 | Body 是否支持 **pull quote** 样式？ | P2 再议 |
| Q3 | 是否允许 **仅填 kicker** 单文案格？ | 推荐允许；空 body collapse |
| Q4 | mirror 变体是否 **GA 同步**？ | 建议 P1 独立 status |
| Q5 | `copySlots` 是否进入 **LTE schema 正式字段**？ | W1 评审冻结 |

---

## 15. 附录

### 15.1 Mockup 对照

| Mockup 区域 | PRD 映射 |
|-------------|----------|
| 左上「文本框」 | `copy.kicker` · gap `[1,1,1,1]` |
| 右上大渐变块 | Main photo slot 0 |
| 左下绿色块 | Tile photo slot 1 |
| 右下「文本框」 | `copy.body` · gap `[2,2,2,2]` |

### 15.2 关联 pattern 速查

| patternId | 槽位 | 文案 | 适用 |
|-----------|------|------|------|
| `screen-landscape-2` | 2 横 · stack | 无 | 纯图连拍 |
| `screen-spread` | 1 | 长文案 | Folio full |
| `screen-plate` | 1 hero | 框外 caption | featured |
| **`screen-editorial-2land`** | **2 横 · 主次** | **屏内短 copy** | **双精选 + 点缀** |

### 15.3 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-06-20 | 初稿：几何、文案、MCS、渲染、验收 |
