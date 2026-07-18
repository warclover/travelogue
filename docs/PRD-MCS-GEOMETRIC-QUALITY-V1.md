# Travelogue · MCS 屏内几何质量与标定闭环 V1（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | **v0.2.1** |
| **状态** | **Conditional Go · Ready for Kickoff W0** · **W1 前须消化 BLK-09～14** |
| **特性代号** | **MGQ**（MCS Geometric Quality） |
| **文档类型** | 版式观感专项优化 PRD（现网 MCS 轨 · 非 LSE 上量） |
| **触发来源** | 开源对标 [kclemson/gridwiggle](https://github.com/kclemson/gridwiggle) 深度分析；与 [观感提升-业内调研.md](./观感提升-业内调研.md) / [观感提升路线图.md](./观感提升路线图.md) 对齐 |
| **前置条件** | Phase 16 LTE 默认路径稳定；Phase 15 MCS `pick_best_window` 为现网权威；`replan_screen(alt_topk)` 可用；URO / BQP 盲评 harness 可用或可同步复用 |
| **纲领上位** | [PRD-LAYOUT-QUALITY-STACK-V1.md](./PRD-LAYOUT-QUALITY-STACK-V1.md)（**LQS** · 统摄 MSR/MGQ/GCS 跨主题合同与排期） |
| **关联文档** | [观感提升-业内调研.md](./观感提升-业内调研.md) · [观感提升路线图.md](./观感提升路线图.md) · [ROADMAP-PHASE18-BOOK-QUALITY.md](./ROADMAP-PHASE18-BOOK-QUALITY.md) · [PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md](./PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md) · [PRD-PHASE18-layout-effect-improvement.md](./PRD-PHASE18-layout-effect-improvement.md) · [PRD-PHASE16-layout-template-engine.md](./PRD-PHASE16-layout-template-engine.md) · [P17-LSE-处置建议.md](./P17-LSE-处置建议.md) · [acceptance-records/p17-w0-audit-a-active-scoring-chain.md](./acceptance-records/p17-w0-audit-a-active-scoring-chain.md) · [PRD-MCS-SIGNATURE-ROUTING-V1.md](./PRD-MCS-SIGNATURE-ROUTING-V1.md) · [PRD-GENERATIVE-COLLAGE-SURFACES-V1.md](./PRD-GENERATIVE-COLLAGE-SURFACES-V1.md) |
| **评审纪要** | [第一轮·推荐案结案](./acceptance-records/mcs-geometric-quality-v1-review-2026-07-18.md) · [**第二轮·专家评审（权威）**](./acceptance-records/mcs-geometric-quality-v1-expert-review-2026-07-18.md) |
| **验收配套** | 本文 §9（**W1 merge 前**须拆 `ACCEPTANCE-MCS-GEOMETRIC-QUALITY-V1.md` · BLK-08/14） |
| **实施清单** | Kickoff W0 时补 `IMPLEMENTATION-MCS-GEOMETRIC-QUALITY-V1.md` |
| **更新日期** | 2026-07-18 |

> **定位**
>
> gridwiggle 证明：在「固定拓扑 + 照片填槽 + 软罚选优」范式下，**声明式 hero 准入、屏内几何软罚、人工标注→调权闭环**能显著提升单页拼贴观感。  
> Travelogue 已具备同类骨架（LTE YAML + MCS soft utility + `alt_topk` replan），但缺三块：**真正的屏内几何维度、模板准入 DSL、可产品化的 pairwise 标定台**。  
> 本 PRD **不**引入连续分区 solver、**不**替换 LTE SKU、**不**解冻 LSE 软乘子上量；只在 **现网 MCS** 上补齐「可解释的屏内几何质量」与「可复现的调参回路」。

---

## 0. 评审决策（D-MGQ · 已冻结）

| # | 决策项 | 冻结结论 |
|---|--------|----------|
| **D-MGQ-01** | 落点轨 | 全部新维度与权重挂 **`MosaicConfig`（现网 MCS）**；**禁止**默认写进 `layout.scoring` / LSE 策略包 |
| **D-MGQ-02** | 几何策略 | **固定 SKU + 准入 DSL**；**禁止** runtime 动态改 slot `rect` / hero-area 连续搜索 |
| **D-MGQ-03** | 命名隔离 | 保留 `hero_separation` = 跨屏 hero 复用；**新增** `hero_prominence` / `hero_coverage` / `cell_area_balance` |
| **D-MGQ-04** | 硬 vs 软 | P0：硬化 **UR-01 类准入**（消费 URO）+ reject 看板；P1：屏内几何 soft；**硬拒绝不得被 soft 绕过** |
| **D-MGQ-05** | 标定形态 | Studio **pairwise（alt_topk）** + 分层用例；**禁止**默认 shuffle / 四角镜像 |
| **D-MGQ-06** | 发布门禁 | `enabled=false` 可先 merge；**默认开启**须过 **AC-MGQ-BLIND**（≥55%） |
| **D-MGQ-07** | 与 URO | MGQ **消费** URO，不另起 usage 引擎；几何 soft 与 UR 硬过滤分层 |
| **D-MGQ-08** | 裁切 | **不**引入 DETR/Transformers.js；可加强 `focalPoint` / face_crop / retention |

| OQ | 冻结结论 |
|----|----------|
| **OQ-MGQ-01** | 评分台为 **V1·W2 必做**（对内/dogfood 开关） |
| **OQ-MGQ-02** | W1a 顺序 = **先 BLK-10（堵绕过）→ 再 UR-01 dogfood + `constraints.eligibility` DSL** |
| **OQ-MGQ-03** | `photoCountScale` 超带 → **硬拒绝**（非仅诊断） |
| **OQ-MGQ-04** | **可 Kickoff W0**（开关骨架 · 命名清理 · 落点审计） |

**总案一句话**：抄 gridwiggle 的 **约束声明 + 屏内几何软罚 + 标注闭环**；落点 **MCS**；保持 **固定 LTE 几何 + trip.json 确定性**。

### 0.1 v0.1.0 → v0.2.0 变更摘要（评审合入）

| 来源 | 合入要点 |
|------|----------|
| **BLK-01** | 落点写死 MCS；新增 **AC-MGQ-11**（`layout.scoring.enabled` 默认 false） |
| **BLK-02** | UR-01 / `usage_rules` 归属 **URO**；MGQ W1a 只消费；见 §1.4 / §4.3.0 |
| **BLK-03** | eligibility SSOT = **`constraints.eligibility`**（不塞完整 DSL 进 `usage.signals`） |
| **BLK-04** | soft 阈值冻结：ceiling **0.50**、prominence_min_ratio **1.35**、cv_start **0.35**；无 main 跳过 |
| **BLK-05** | legacy / self-heal / replan **不得绕过**硬过滤；新增 **AC-MGQ-12** |
| **BLK-06** | 评分 sidecar **独立** `runs/layout-rating.jsonl` |
| **BLK-07** | 盲评与 BQP/URO **共用 trip 集 + harness**；Gate 码 **AC-MGQ-BLIND 独立** |
| **BLK-08** | W0 可以本文 §9 为挡门；**W1 merge 前**必须拆 ACCEPTANCE + IMPLEMENTATION |
| **OQ / Should** | CV 作 `cell_area_balance` 主特征；评分台线框 W2 再补；对内开关 |

### 0.2 v0.2.0 → v0.2.1 变更摘要（专家评审合入）

来源：[专家评审纪要](./acceptance-records/mcs-geometric-quality-v1-expert-review-2026-07-18.md)（算法 · 架构 · 开发 · 测试 · 用户体验）。

| 来源 | 合入要点 |
|------|----------|
| **BLK-09** | 面积 = `col_frac × row_frac`（复用 `geometry.slot_display_aspect` 口径）；禁止按 rect 格数计数 |
| **BLK-10** | 修复 `selfheal.drop_worst_asset` / `replan_screen(legacy)` 硬过滤绕过；**先于** UR-01 dogfood 与新 soft |
| **BLK-11** | 未声明 `eligibility` ≡ 不参与硬拒绝；schema PR 同批全量 validate + registry cache |
| **BLK-12** | eligibility 接在 URO 之后；**不进** `USAGE_RULE_UNDO_ORDER` |
| **BLK-13** | decision log 存 raw 几何特征，与 penalty 分栏 |
| **BLK-14** | AC/盲评可判定字面；coverage 用 `>`；评分台「不改本书」；P-05/P-06 移出用户问题表 |
| **OQ-02 微调** | 顺序：BLK-10 → UR-01 dogfood + eligibility DSL |

---

## 1. 背景与问题

### 1.1 对标结论（gridwiggle → Travelogue）

| gridwiggle 能力 | Travelogue 现状 | 本 PRD 态度 |
|-----------------|-----------------|-------------|
| Hero 分离 + 模板注册表筛选 | LTE `mainSlotPolicy` / UR-01（默认 **关**） | **加强 `constraints.eligibility`**，不重写拓扑 |
| 几何采样（canvas AR × hero fraction） | 几何预置 YAML，无 hero 面积搜索 | **不抄**连续采样；改为 **photoCountScale + 舒适带声明** |
| Row-packing / Topology 分解 | 固定 slots | **不抄** |
| Soft penalties（prominence / coverage / uniformity / uncovered） | 有 slot AR / narrow tiles / dense_without_hero；**无**面积 prominence / cell CV | **抄维度到 MCS penalties** |
| `/layout-rating` 调参台 | probe / golden / feedback sidecar（默认关） | **产品化 pairwise 面板**（V1·W2） |
| shuffle / 镜像四角 | `deterministic_strict=true` | **明确禁止**进默认路径 |
| DETR 主体裁切 | Haar face → `focalPoint` | **不抄 DETR**；可选加强 retention |

### 1.2 现网权威链路（不可误映射）

```text
run_curate
  → ChapterScreenPlanner（多 stage / 节奏状态机）
      → mosaic.compose.pick_best_window
           → generate_window_candidates
                → usage_rules（URO · UR-01…）          ← 硬过滤
                → constraints.eligibility（MGQ DSL）   ← 硬过滤
           → mosaic.scorer.score_candidate
                base = 加性 weights（含 hero_separation=跨屏复用）
                utility = soft × Π(1 − w·p)             ← 现网权威 + MGQ 几何罚
           → MMR/DPP + self-heal / legacy fallback      ← 仍须经硬过滤（BLK-05）
  → layout.scoring beam（默认 enabled=false）← 非本 PRD 主战场（BLK-01）
```

审计真值见：`acceptance-records/p17-w0-audit-a-active-scoring-chain.md`。

### 1.3 用户可感知问题（本 PRD 要解决）

| ID | 问题 | 典型表现 | 根因分层 |
|----|------|----------|----------|
| **MGQ-P-01** | Hero 屏「有主槽、不够突出」 | 主图与侧栏面积接近，视觉无锚点 | 缺 `hero_prominence` |
| **MGQ-P-02** | Hero 过大挤死配图 | 主槽视觉霸屏，内容区碎片化 | 缺 `hero_coverage` + photoCountScale 硬拒绝 |
| **MGQ-P-03** | 同屏小图大小悬殊 | 一格过大、其余碎屑感 | 缺 `cell_area_balance`（≠ `gravity_balance`） |
| **MGQ-P-04** | 无明确 hero 仍进 extreme hero 页型 | 任意选片撑满主轴 | UR-01 / `heroDominance` 未生效 |

> **研发可维护性（非用户可感知 · BLK-14）**：调权靠直觉 → W2 评分台；`hero_separation` 语义串线 → W0 命名锁（AC-MGQ-02）。二者不进用户问题表。

### 1.4 与相邻工作的边界（BLK-02 冻结）

| 主题 | 解决什么 | 本文是否改动 | 所有权 |
|------|----------|--------------|--------|
| **URO** | `usage` / `usage_rules` / UR-01 硬过滤与 tie-break | **不改引擎**；W1a **消费** UR-01 dogfood | **URO 业主** |
| **MGQ eligibility** | `constraints.eligibility` 声明式页型准入 | **本 PRD 交付** | **MGQ** |
| BQP / Phase 18 | 设计师 SKU、硬约束包、盲评 harness | Gate **复用 harness + 代表 trip**；Gate 码独立（BLK-07） | BQP |
| LSE / P17 | 章级策略包、软乘子 | **冻结**：不默认开启、不新增 LSE 权重 | — |
| P21 density | dense / breath | **不改** | — |
| 选片 subset / DPP 上移 | 「选什么照片」 | **非目标** | 观感路线图 P1 |
| `layout-feedback.jsonl` | G1/编辑 pairwise | **不扩展**；评分用独立 sidecar（BLK-06） | Refine / feedback |

**对外一句话**：URO 负责「按使用说明少选错」；MGQ 负责「屏内几何更稳 + 可标定」；二者共用硬过滤管道，不造第二套 usage 引擎。

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 | 验收口径 | 阶段 |
|----|------|----------|------|
| **G-MGQ-01** | 澄清评分语义：`hero_separation` ≠ prominence | 配置注释 + 单测命名 | W0 |
| **G-MGQ-02** | LTE 增加 **`constraints.eligibility`** DSL | schema + validator + ≥3 模板样例 | W0–W1 |
| **G-MGQ-03** | MCS 新增三 soft：`hero_prominence` / `hero_coverage` / `cell_area_balance` | `MosaicConfig` + score breakdown | W1 |
| **G-MGQ-04** | 消费 URO：UR-01 dogfood 可开；reject 可聚合 | reject taxonomy 看板 | W1a |
| **G-MGQ-05** | Studio 布局评分：`alt_topk` pairwise + 标签 | `layout-rating.jsonl` | W2 |
| **G-MGQ-06** | 分层用例集 30–50 screen | 覆盖矩阵 | W2 |
| **G-MGQ-07** | 默认开启前盲评胜率 **≥ 55%** | **AC-MGQ-BLIND** | W3 |
| **G-MGQ-08** | 诊断指标可报表 | `layoutMetrics`（**非 Gate**） | W1–W3 |

### 2.2 非目标

| # | 排除项 | 理由 |
|---|--------|------|
| OUT-01 | 连续 hero-area / canvas-AR 采样 solver | 破坏固定 SKU + solidify + 复现 |
| OUT-02 | Row-packing 重排 slot 几何 | 同上 |
| OUT-03 | 默认路径 shuffle / 四角镜像 | 与 `deterministic_strict` 冲突 |
| OUT-04 | DETR / Transformers.js | D-MGQ-08 |
| OUT-05 | 用单屏 F-ratio 优化整本叙事 | 章级节奏另轨 |
| OUT-06 | LSE `layout.scoring` 默认开启或新乘子上量 | dogfood 已证伪 · BLK-01 |
| OUT-07 | 替换 LTE 模板体系 / 大改 pattern 几何 | 只加准入与打分 |
| OUT-08 | 选片 DPP 上移、subset_planner 主交付 | 独立 PRD |
| OUT-09 | 绝对分 1–10 作为主标注 | pairwise 更稳 |
| OUT-10 | 另起第二套 `usage_rules` 引擎 | BLK-02 / D-MGQ-07 |
| OUT-11 | 扩展 `layout-feedback.jsonl` 承载布局评分 | BLK-06 |

---

## 3. 设计原则

### 3.1 铁律

1. **`mosaic.geometric_quality.enabled=false` 时**：排版输出与 baseline **逐屏一致**（patternId + asset 序 + 固化几何）。
2. **不得**在评分路径 runtime 改写 LTE slot `rect`；几何变更必须走模板 YAML → solidify。
3. **硬过滤先于 soft utility**：顺序为 geometry → **URO `usage_rules`** → **MGQ `constraints.eligibility`** → soft score。
4. **legacy / self-heal / replan 不得绕过**已启用的硬规则（BLK-05 · AC-MGQ-12）。
5. **默认开启**的发布门禁是 **AC-MGQ-BLIND**，不是 golden proxy 微涨。
6. **屏内几何**与**屏间叙事**分账：本 PRD 主交付前者；`hero_separation` / rhythm / burst / density 保持现语义。
7. **新维度只进 `MosaicConfig`**；禁止默认同步进 LSE 策略包（BLK-01 · AC-MGQ-11）。

### 3.2 两层评分账本

```text
┌─────────────────────────────────────────────────────────┐
│ 屏内几何（MGQ 主交付）                                    │
│  hero_prominence · hero_coverage · cell_area_balance     │
│  （既有）hero_slot_aspect · hero_narrow_tiles · …        │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ 屏间叙事（保留现网 · 本 PRD 不重定义）                    │
│  hero_separation（跨屏复用）· gravity_balance             │
│  dense/breath 配额 · burst/duplicate_density · collage   │
└─────────────────────────────────────────────────────────┘
```

### 3.3 与 gridwiggle 惩罚项的映射

| gridwiggle | Travelogue 落点 | 类型 | 阶段 |
|------------|-----------------|------|------|
| prominencePenalty | `geometric_quality.penalties.hero_prominence` | soft | W1 |
| coveragePenalty | `geometric_quality.penalties.hero_coverage` | soft | W1 |
| contentUniformity / scoreCellBalance | `geometric_quality.penalties.cell_area_balance`（**CV 主特征**） | soft | W1 |
| arPenalty | `constraints.eligibility.canvasAr` + main AR ladder | 硬/软分层 | W0–W1 |
| uncoveredPenalty | **P2 可选** | 延后 | P2 |
| F-ratio 基础分 | **不**做基础分；不进默认 `cell_area_balance`（可选内部实验） | — | — |

---

## 4. 总体方案

### 4.1 架构增量

```text
LTE YAML
  └─ constraints.eligibility（MGQ SSOT · BLK-03）
        heroDominance: extreme | moderate
        canvasAr: [min, max]
        heroAreaBand: [min, max]
        photoCountScale: { referenceCount, maxHeroAreaAtRef, floorFactorAt50 }

MCS candidates
  └─ hard: geometry → usage_rules(URO) → eligibility(MGQ) → reject+reason
  └─ soft: score_candidate + geometric_quality penalties
  └─ pick: deterministic top
  └─ fallback / self-heal / replan: 仍经硬过滤（BLK-05）

Studio Layout Rating（W2）
  └─ fix window → alt_topk → pairwise + tags
  └─ sidecar: trips/<id>/runs/layout-rating.jsonl（BLK-06）
  └─ offline: 权重建议 → 人工 PR 合入
```

### 4.2 W0 · 契约与命名清理（可 Kickoff）

| 交付 | 说明 |
|------|------|
| 语义锁 | `hero_separation` 注释/文档/单测统一为「章内/跨屏是否复用 chapter hero」 |
| 配置骨架 | `MosaicConfig.geometric_quality`（`enabled=false`）进 fail-loud |
| 落点审计 | 脚本或单测确认活跃链 = MCS；**AC-MGQ-11** |
| 文档 | 本 PRD 为 SSOT；IMPLEMENTATION 任务卡可与 W0 同开 |

### 4.3 W1 · 准入 DSL + 屏内几何 soft

#### 4.3.0 与 URO 的执行合同（BLK-02 · BLK-10 · BLK-12）

| 项 | 合同 |
|----|------|
| `layout.usage_rules` 开关与 UR-01 实现 | **URO PRD / 代码业主** |
| MGQ W1a 顺序 | **① 先修 BLK-10 绕过** → ② 打开/依赖 UR-01 dogfood → ③ 上线 eligibility 求值器 |
| MGQ 自有硬过滤 | 仅 **`constraints.eligibility` 求值器**（reason 前缀 `eligibility:*`） |
| 插入点 | `generate_window_candidates_with_rejections` 内，URO `evaluate_reject` **之后**（BLK-12） |
| 空候选 | eligibility reject **不参与** `USAGE_RULE_UNDO_ORDER`；枯竭走缩窗/legacy，不撤销 eligibility（BLK-12） |
| reject 看板 | 可联合展示 `usage_rule:*` 与 `eligibility:*` |
| decision log | 复用 `usageRuleRejects`（reason 前缀区分）**或**新增 `eligibilityRejects`——IMPLEMENTATION 二选一写死 |

**BLK-10（现网绕过 · 必须先修）**：

| 路径 | 问题 | 要求 |
|------|------|------|
| `selfheal.try_self_heal_pick` → `drop_worst_asset` | 重调 `generate_window_candidates` **未传 `window_ctx`** → 跳过硬过滤 | 重建 `WindowContext`，走 `generate_window_candidates_with_rejections` |
| `replan_screen(strategy="legacy")` | 直接 `build_legacy_screen`，无 `evaluate_reject` | 结果强制过硬过滤，**或** MGQ/URO harness 与评分台 **禁止** 调用 legacy 策略 |

#### 4.3.1 准入 DSL（`constraints.eligibility` · BLK-11）

```yaml
# LTE 模板示例 · SSOT 挂载点
constraints:
  eligibility:
    heroDominance: moderate   # extreme | moderate
    canvasAr: [0.5, 2.25]
    heroAreaBand: [0.15, 0.40]
    photoCountScale:
      referenceCount: 20
      maxHeroAreaAtRef: 0.40
      floorFactorAt50: 0.55
```

行为（冻结）：

- **未声明 `constraints.eligibility`**：等价于不参与 MGQ 硬拒绝（不设 extreme/面积带/photoCountScale 上限）（BLK-11）。
- **extreme**：仅当窗口存在明确 hero 信号（userTier/featured、chapter hero、或 UR-01 gap ≥ 阈值）才允许该模板进入候选。
- **moderate**：自动选片默认路径可用；禁止「arbitrary hero 撑满整轴」类 extreme 页型。
- **photoCountScale**：按照片数收紧 hero 面积上限；**超出带硬拒绝**（OQ-MGQ-03），走 `candidates` `_reject` 管道（`eligibility:*`），**不**走 penalty=0.95 双轨，**不**改 slot rect。
- **不**把完整 DSL 写入 `usage.signals`（BLK-03）。
- schema 变更 PR 必须同批：全量模板 validate + `registry.cache.json` 重建（BLK-11）。

#### 4.3.2 Soft penalties（阈值冻结 · BLK-04 · BLK-09）

均走 `combine_utility`：`utility *= (1 - w * p)`，`p ∈ [0,1]`。

| 维度 | 特征 | 阈值（冻结） | 方向 |
|------|------|--------------|------|
| `hero_prominence` | `heroArea / max(contentCellAreas)` | **min_ratio = 1.35**；低于则 p↑ | 主图不够跳 |
| `hero_coverage` | `heroArea / canvasArea` | **ceiling = 0.50**；**仅当 `>` 时** p↑（非 `>=`） | 主图过大 |
| `cell_area_balance` | content 槽面积 **CV** | **cv_start = 0.35**；超过则 p↑ | 小图悬殊 |

**面积口径（BLK-09 · 一字面）**：

> 槽面积占比 = 复用 `travelogue/layout_templates/geometry.py::slot_display_aspect` 的 **`col_frac × row_frac`**（按 `layoutGeometry.cols/rows` 权重折算）。**禁止**按 `slot.rect` 跨越的网格格数直接计数。单测临界样本必须含 `screen-mosaic-5-hero-3-2-plus-4`。

实现注意：

- **无 `main` role**：`hero_prominence` / `hero_coverage` **跳过**（p=0）。
- **content 槽 n&lt;3**：`cell_area_balance` 跳过或衰减（避免小样本 CV 噪声）。
- **不读** 槽位 `visualWeight`（设计师主观权重 ≠ 几何面积）。
- 默认权重建议：`hero_prominence=0.20`、`hero_coverage=0.20`、`cell_area_balance=0.15`（各 ≤ 0.25）。
- `cell_area_balance` **不以 F-ratio 为默认公式**。
- raw 特征写入 log（BLK-13）：`heroProminenceRatio` / `heroCoverageRatio` / `cellAreaCv`。

#### 4.3.3 诊断指标（非 Gate）

| 指标 | 含义 |
|------|------|
| `hero_prominence_p50` | 含 main 屏 prominence 中位 |
| `hero_coverage_p90` | hero 面积占比高分位 |
| `cell_area_cv_p90` | 内容槽面积 CV 高分位 |
| `eligibility_reject_rate` | 按 `eligibility:*` 聚合 |
| `hero_mismatch_rate` | 与 URO 诊断可共用 |

### 4.4 W2 · 布局评分工作台

#### 4.4.1 产品流程

```text
真实 trip 导出 screen 窗口（固定 assetIds）
  → current + alt_topk 次优（无则跳过）
  → 选胜者 + 标签
       tags: hero-not-prominent | hero-too-big | cells-uneven
             | wasted-space | wrong-template-family | ok
  → 写入 runs/layout-rating.jsonl
  → 离线汇总 → 人工 PR 调 mosaic.geometric_quality / eligibility
```

#### 4.4.2 分层用例集（30–50）

| 层 | 覆盖 |
|----|------|
| photoCount | ≤8 / 9–20 / 21–50（每档 ≥3 例 · BLK-14） |
| hero 信号 | 明确 / 模糊 / 无（每档 ≥3） |
| 主图朝向 | 横 / 竖 / 方（每档 ≥3） |
| 窗口类型 | burst / 风景均质 / 人物混排（每档 ≥3） |
| trip 规模 | 小册 / 标准 / 厚册（每档 ≥3） |
| 几何轨道 | **均匀网格 / 加权轨道**（每档 ≥3 · 专家评审） |

#### 4.4.3 Sidecar 合同（BLK-06）

| 机制 | 合同 |
|------|------|
| 路径 | `{trip_dir}/runs/layout-rating.jsonl` |
| 与 `layout-feedback.jsonl` | **分轨**；禁止用 editType 硬塞布局评分 |
| 候选源 | 仅 `replan_screen` / `score_window_candidates` 的 `alt_topk` |
| 曝光 | **内部/dogfood 开关**；不对全体终端用户默认曝光 |
| 线框 | **W2 再补**；不挡 W0 |

### 4.5 W3 · 标定合入与默认开启（BLK-07）

1. 冻结一版 penalties / DSL 阈值；是否 bump algorithm lock 由算法负责人裁定。  
2. **AC-MGQ-BLIND**：与 BQP/URO **共用代表 trip 集 + 盲评 harness**；Gate 码独立；on vs off；≥3 评审；胜率 **≥55%**。  
3. 未达标则保持 `enabled=false`；基础设施可留在 master。  
4. **AC-MGQ-BLIND 与 AC-URO-BLIND 可同场执行，但分别计票、分别发布。**

---

## 5. 里程碑与工作包

| 里程碑 | 内容 | 预估 | Go | No-Go |
|--------|------|------|----|-------|
| **W0** | 命名清理；`geometric_quality` 开关骨架；AC-MGQ-11 CI；IMPLEMENTATION 任务卡 | **1–1.5d** | 默认 off；落点=MCS 可证 | 争议「是否改 LSE」仍开 scorer |
| **W1a** | **BLK-10 修复** → eligibility + 消费 UR-01 + reject 聚合 | 含于 W1 | AC-MGQ-03/05/12（分路径） | 另起 usage 引擎；绕过未修就开 dogfood |
| **W1b** | 三 soft + 面积 helper（BLK-09）+ raw 特征（BLK-13）+ 触发率基线 | **W1 合计 1.5–2w** | AC-MGQ-01～06、13～15 | runtime 改 rect；按格数算面积 |
| **W2** | 评分台 + 30–50 用例 + 线框 | 1–1.5w | AC-MGQ-07～10 | shuffle 候选；扩展 layout-feedback |
| **W3** | 盲评 + 默认开启决策 | 3–5d | **AC-MGQ-BLIND ≥55%** 或保持 off | proxy 充当发布依据 |

**拆文节奏（BLK-08）**：W0 可以本文 §9 为工程挡门；**任何 W1 代码合入 master 前**必须存在：

- `IMPLEMENTATION-MCS-GEOMETRIC-QUALITY-V1.md`
- `ACCEPTANCE-MCS-GEOMETRIC-QUALITY-V1.md`

---

## 6. 配置与数据契约

### 6.1 配置（冻结草案）

```yaml
mosaic:
  geometric_quality:
    enabled: false
    hero_coverage_ceiling: 0.50
    hero_prominence_min_ratio: 1.35
    cell_area_cv_start: 0.35
    penalties:
      hero_prominence: 0.20
      hero_coverage: 0.20
      cell_area_balance: 0.15

# URO 业主 · MGQ 消费（勿在 MGQ 另起平行开关语义）
layout:
  usage_rules:
    enabled: false
    hero_gap_threshold: 0.15
```

### 6.2 `layout-rating.jsonl`

```json
{
  "schemaVersion": 1,
  "tripId": "…",
  "screenId": "…",
  "assetIds": ["a1", "a2", "a3", "a4", "a5", "a6"],
  "left": { "patternId": "screen-mosaic-5-main-hero-plus-4", "source": "current" },
  "right": { "patternId": "screen-mosaic-6-landscape", "source": "alt_topk", "rank": 2 },
  "winner": "left",
  "tags": ["hero-not-prominent"],
  "reviewer": "dogfood",
  "emittedAt": "2026-07-18T12:00:00Z"
}
```

### 6.3 确定性

- 评分台候选必须来自同一 `score_window_candidates` 排序；遵循 `deterministic_strict`。  
- **禁止**生产 curate 路径随机镜像。  
- 同一输入 + 同一 config → 同 `trip.json` screens。

---

## 7. Studio UX（W2 最小可用）

### 7.1 入口（UX 冻结）

- **优先独立 debug 路由**（类 `/layout-rating`）；桌面 Studio ≥1024。  
- **不推荐**挂进精修「这页」与 ★/拼图同区（易被当成换版式）。若必须挂「这页」，须有「仅供内部研究」横幅，且不得复用「更新版面」语汇。

### 7.2 一屏一任务

- 左：当前成稿；右：`alt_topk` 次优（无则跳过）。  
- 选更好者 + 可选 1～2 标签。  
- 预览接口复用无副作用的 `_pick_alt_topk`，**禁止**误用会 mutate chapters 的 `replan_screen`。  
- **不做**拖拽改槽；**不做**绝对 1–10 主路径。

### 7.3 文案原则（BLK-14）

- 对内工具语气可工程化。  
- **固定句（须出现在评分台 UI）**：「你的选择只用于后续调参研究，**不会改变你当前这本书的任何一页**。」  
- 不承诺「评分后立即改权重」。  
- 标签：`wasted-space` 若展示须标注「暂未接入调权」或 W2 首发不放；`wrong-template-family` 视为准入漏洞信号而非常规调参。

---

## 8. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 屏内变好、章级更碎 | 观感回退 | 盲评看整本；监控 dense streak / hero 复用 |
| soft 与 UR 重复惩罚 | 候选枯竭 → fallback | 分层 reason；权重保守；fallback 仍经硬过滤（AC-MGQ-12） |
| 命名串线 | 调错权 | W0 语义锁（AC-MGQ-02） |
| 样本偏科 | 过拟合 | 分层用例矩阵 |
| 与 URO 重复建设 | 双引擎 | BLK-02 所有权表 |
| 误挂 LSE | 默认路径零感知 | AC-MGQ-11 |

---

## 9. 验收标准

### 9.1 工程验收

| ID | 条款 |
|----|------|
| **AC-MGQ-01** | `geometric_quality.enabled=false` 时，固定 fixture 与 baseline 逐屏一致 |
| **AC-MGQ-02** | 可执行断言：面积分布变而 `hero_separation` 不变；仅 `hero_asset_ids` 重叠态变化时才变；禁止把该权写进 `geometric_quality.penalties` |
| **AC-MGQ-03** | ≥3 个具名 hero 模板带齐 `constraints.eligibility`；publish 模式 validator `block` |
| **AC-MGQ-04** | breakdown 钉死 key，且含 BLK-13 raw 特征字段（非仅 penalty） |
| **AC-MGQ-05** | fixture：heroScore/featured 持平窗 → `heroDominance=extreme` 拒、`moderate` 放行；reason 含 `eligibility:*` 或 `usage_rule:UR-01` |
| **AC-MGQ-06** | 按 BLK-09 面积口径，coverage **`>` 0.50** → `hero_coverage` 惩罚上升；临界样本含 `hero-3-2-plus-4` |
| **AC-MGQ-07** | 可生成 current vs alt 对并写入 `layout-rating.jsonl`；UI 含「不改本书」固定句 |
| **AC-MGQ-08** | 用例集 ≥30；§4.4.2 每轴每档 **≥3** 例（CI 校验 manifest） |
| **AC-MGQ-09** | curate P95 增幅 ≤ +10%（脚本/环境口径与 URO 对齐，或挪 W3） |
| **AC-MGQ-10** | 默认管线无 DETR/新重模型；建议自动化依赖扫描 |
| **AC-MGQ-11** | 默认 `layout.scoring.enabled is false`；MGQ 字段仅 `MosaicConfig` 路径（CI 静态遍历） |
| **AC-MGQ-12** | **分路径**：① self-heal 三分支（含 `drop_worst_asset`）；② `replan_screen(legacy)` 或已禁用；③ legacy append——均不得 emit 已被 `usage_rule:*`/`eligibility:*` 拒绝的 pattern（BLK-10） |
| **AC-MGQ-13** | 无 `main` role：`hero_prominence`/`hero_coverage` p=0 |
| **AC-MGQ-14** | prominence &lt; **1.35** → prominence 罚↑；content CV &gt; **0.35** → balance 罚↑（面积口径 BLK-09） |
| **AC-MGQ-15** | `photoCountScale` 超带 → `_reject(eligibility:*)`，且不经 UNDO 撤销（BLK-12 / OQ-03） |

### 9.2 产品门禁（默认开启前）

| ID | 条款 |
|----|------|
| **AC-MGQ-BLIND** | 复用 `URO_GOLDEN_TRIP_IDS`（先统一文档「8/9 本」口径）；两臂**只翻** `geometric_quality`，`usage_rules` 同态；≥3 评审；胜率 ≥55%（平局计分规则写进 ACCEPTANCE）；Gate 码独立；声明 veto/脚本扩展方式（BLK-07/14） |
| **AC-MGQ-DIAG** | `layoutMetrics` 关键字段非空可生成；含三罚项触发覆盖率；**不**以 proxy 单独作为 merge 依据 |

### 9.3 主题 Go / No-Go

| 里程碑 | Go | No-Go |
|--------|-----|-------|
| W0 | D-MGQ 已冻结；开关默认 off；AC-MGQ-02/11 | 未决落点仍改 scorer |
| W1 | AC-MGQ-01～06、12～15；BLK-09～13 已落地；ACCEPTANCE+IMPLEMENTATION 已存在 | runtime 改几何；绕过未修；按格数算面积 |
| W2 | AC-MGQ-07～10；独立路由评分台 +「不改本书」文案 | shuffle；挂「这页」无隔离；写入 layout-feedback |
| W3 默认开 | AC-MGQ-BLIND + 触发率故事可讲 | 仅有单元测试绿 |

---

## 10. 实施顺序建议

| 顺序 | 包 | 依赖 | 备注 |
|------|----|------|------|
| 1 | W0 合同 + 命名 + 开关 + CI 落点断言 | 无 | **可立即 Kickoff** |
| 2 | 拆 IMPLEMENTATION（可与 W0 同开） | — | BLK-08 |
| 3 | **W1a-0 修 BLK-10 绕过** | — | **先于 dogfood** |
| 4 | W1a eligibility + 消费 UR-01 | URO + BLK-10 | OQ-MGQ-02 |
| 5 | 拆 ACCEPTANCE（含盲评合同 · BLK-14） | — | W1 merge 前必达 |
| 6 | W1b 三 soft + 面积 helper + raw 特征 + 触发率基线 | W1a | BLK-09/13 |
| 7 | W2 评分台（独立路由）+ 用例 + 线框 | `_pick_alt_topk` | 对内开关 |
| 8 | W3 盲评与默认开启决策 | W1+W2 | 未过 Gate 则保持 off |

---

## 11. 成功画像

1. **有明确主图时**，hero 页主槽「跳得出来」但不霸屏；  
2. **无明确主次时**，更少误进 extreme hero 页型；  
3. **同屏小图**不至于一块过大、其余碎屑；  
4. 调权时能打开评分台看到 **标签分布 → 权重建议**。

若只能完成一项：优先 **W1a（eligibility + 消费 UR-01）**。

---

## 12. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-07-18 | 初稿；待跨职能评审拍板 D-MGQ-01～08 |
| v0.1.0+ | 2026-07-18 | 开评审纪要会前稿 |
| v0.2.0 | 2026-07-18 | 第一轮推荐案结案：消化 BLK-01～08 |
| **v0.2.1** | **2026-07-18** | **专家五席评审**：消化 **BLK-09～14**；面积口径 / 硬过滤绕过 / eligibility 接线 / AC 可判定字面；仍可 Kickoff W0 |
