# Travelogue · 模板使用说明驱动排版优化 PRD（Usage Rules · Layout Optimization）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | v0.2.0 |
| **状态** | Draft · 评审修订稿（v0.1.0 三方有条件通过） |
| **特性代号** | URO（Usage Rules Optimization，使用说明规则优化） |
| **文档类型** | 基于已落地 `usage` 文档的排版算法增强 PRD（Phase 18 **WS-2 / BQP IG-2** 子项） |
| **前置条件** | 26 个 LTE 模板已含 `usage` 区块（commit `0c9510f`）；Phase 16 MCS 稳定；Phase 18 **WS-0 盲评 harness** 可用或同步建设 |
| **关联文档** | [PRD-TEMPLATE-SEMANTIC-LAYER.md](./PRD-TEMPLATE-SEMANTIC-LAYER.md)（愿景与全栈语义层，**本 PRD 为其排版效果子集**）、[ROADMAP-PHASE18-BOOK-QUALITY.md](./ROADMAP-PHASE18-BOOK-QUALITY.md)、[LAYOUT-SCORING.md](./LAYOUT-SCORING.md)、[DESIGN-PHASE16-layout-template-engine.md](./DESIGN-PHASE16-layout-template-engine.md)、[P17-LSE-处置建议.md](./P17-LSE-处置建议.md) |
| **更新日期** | 2026-07-04 |

> **定位**
>
> - **输入**：26 个 LTE 模板 YAML 中的 `usage`（summary / whenToUse / whenNotToUse / siblings），及从中抽取的少量结构化 `usage.signals`。
> - **输出**：MCS / screen_planner 在**几何硬约束之后**、**打分选优之前**，按使用说明执行**确定性规则**（以排除为主、tie-break 为辅），改善内容–版式错配与易混模板误选。
> - **铁律**：① `layout.usage_rules.enabled=false` 时排版输出与 baseline **逐屏一致**；② 规则**不得**突破 LTE 几何护栏；③ **`enabled=true` 的发布门禁是盲评（AC-URO-BLIND）**，不是 fixture 单测或 proxy 分数；④ **不**在 LSE 策略包内新增软乘子权重（LSE 冻结路线 A）；⑤ **legacy / self-heal / replan 不得绕过 usage filter**。
> - **与 [PRD-TEMPLATE-SEMANTIC-LAYER.md](./PRD-TEMPLATE-SEMANTIC-LAYER.md) 的分工**：TSL PRD 描述语义层全栈愿景（词表、管理台、LLM）；**本 PRD 只交付「用 usage 提升排版效果」的最短可验证路径**；TSL 软打分路径 **冻结**，待 URO IG-2 盲评证明后再扩展。

---

## 0. 评审决策（D1～D8 · 已采纳）

v0.1.0 经算法 / 开发 / 产品三方评审，**有条件通过**。下列决策已写入本版 PRD，作为实施权威依据：

| # | 决策项 | 结论 |
|---|--------|------|
| **D1** | URO 首次 `enabled=true` 挂在哪个 IG？ | **BQP IG-2（18.2 版式包）**，不与 WS-1 subset 同批 |
| **D2** | 盲评 Gate 命名 | **`AC-URO-BLIND`**（≥55% vs off）；**不用** BQP 路线图中的 IG-1（IG-1 = 选片） |
| **D3** | UR-02/05 与 BQ-202 | **共用** `ScreenLayoutPlannerState` breath/dense 模块，不维护第二套计数器 |
| **D4** | `usage.signals` vs TSL `semantics` | **单 schema**：URO 只读 `usage.signals` 子集；TSL 扩展时不得另起字段名 |
| **D5** | 未达 55% 能否 merge | **W0 基础设施（`enabled=false`）可 merge**；**`enabled=true` 未过 AC-URO-BLIND 不得 merge** |
| **D6** | TSL LSE semantic_weight | **冻结**，等 URO 盲评结果 |
| **D7** | 55% 是否分 trip 类型 | **aggregate Gate + 分类型诊断**（分类型 **非** Gate） |
| **D8** | UR-07 P0 是否必做 | **否**，并入 **P1 UT-01** |

---

## 1. 背景与问题

### 1.1 已完成（基线）

| 项 | 状态 |
|----|------|
| 26 个 LTE 模板 `usage` 四段式说明 | ✅ 已落地 |
| `layout_template.schema.json` · `usage` 字段 | ✅ |
| `validator.py` · V-P16-U01～03 | ✅ |
| `scripts/gen_usage_skeleton.py` · `check_usage_consistency.py` | ✅ |
| 运行时排版算法消费 `usage` | ❌ **未接入** |

因此：**文档价值已沉淀，用户可感知的排版提升仍为 0**，直到本 PRD 落地。

### 1.2 用户可感知问题（本 PRD 要解决）

| ID | 问题 | 典型误选 | usage 中已有表述 |
|----|------|----------|------------------|
| **URO-P-01** | 无 hero 窗口误选主图引领 mosaic | `mosaic-5-main-hero-plus-4` | whenNotToUse：「无明确主次 → landscape-6」 |
| **URO-P-02** | 竖图主角被塞进混排配角槽 | `mosaic-5-main-portrait-3land` | whenNotToUse：「竖图最强 → portrait-1」 |
| **URO-P-03** | 宽幅风景进偏竖 hero 槽 | `mosaic-5-hero-3-2-plus-4` | whenNotToUse：Plate 63 / 拦腰裁切 |
| **URO-P-04** | dense 屏连续无呼吸 | 连续 landscape-9 / mosaic-6 | whenNotToUse：「章内已 dense 且无缓冲」 |
| **URO-P-05** | 易混模板选错（mosaic-5 族） | hero-plus-4 vs hero-3-2 vs main-portrait | siblings 互引 |
| **URO-P-06** | 选用不可解释 | 全模板 | whenToUse / whenNotToUse 无法进入 log（**运维价值**，不与 win rate 并列对外叙事） |

### 1.3 战略约束（Phase 18 BQP）

| 约束 | 对本 PRD 的含义 |
|------|-----------------|
| LSE 软乘子 dogfood 证伪 | **禁止**把 usage 做成 LSE `semantic_weight` 软加分；规则走 MCS 硬过滤 + 独立 tie-break |
| 盲评是 `enabled=true` 发布门禁 | **AC-URO-BLIND**：8 本 golden trip pairwise ≥55% |
| WS-2 版式 | 本 PRD 归属 **BQP IG-2**（18.2 版式包），可与 BQ-201/202 硬约束并列 |
| 性能 | curate P95 增幅 ≤ +15%（规则为 O(候选数)，可忽略） |
| **最大工程风险** | MCS / **legacy fallback** / P21 rhythm **三套出口不一致** — usage 规则可能被绕过（见 §3.4） |

### 1.4 与 Phase 18 其他 Workstream 的优先级

| 优先级 | 方向 | WS | 与 URO 关系 |
|--------|------|-----|-------------|
| **1** | WS-0 盲评 harness + 8 本 baseline | WS-0 | URO 一切门禁的前置 |
| **2** | subset_planner（选片 −25%～40%） | WS-1 | 提升窗内 hero 对比度，**放大 UR-01 效果** |
| **3** | BQ-201～202 硬约束包 | WS-2 | 与 UR-02/05 **合并实现** |
| **4** | **URO P0-a**（UR-01/02 + legacy 守门） | WS-2 | 本 PRD 首交付 |
| **5** | 3 个设计师 SKU | WS-2 | 规则少选错；SKU 选对更好看 |
| **6** | story_planner + paceRole | WS-3 | 章级节拍；与 URO 互补 |
| **延后** | TSL 词表软匹配、LSE semantic_weight、章级 LLM | — | 等 URO IG-2 盲评证明 |

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 | 验收口径 | 阶段 |
|----|------|----------|------|
| **G-URO-01** | 从 `usage` 抽取 **5～6 条 P0** + **3 条 P1** tie-break 规则 | registry 单测 + 每条规则 ≥1 fixture | P0-a / P1 |
| **G-URO-02** | 规则以**候选排除**为主，在几何校验之后执行 | `generate_window_candidates_with_rejections` 增加 `reason=usage_rule:*` | P0-a |
| **G-URO-03** | `layout.usage_rules.enabled=false` 时输出与 baseline **逐屏一致** | AC-URO-01 回归 | P0-a |
| **G-URO-04** | decision log 记录 `usageRuleHits` / `usageRuleRejects` | trip.json schema 扩展 | P0-a |
| **G-URO-05** | **排版效果**：8 本 golden trip 盲评，on vs off，胜率 **≥ 55%** | **AC-URO-BLIND**（IG-2 Gate） | P0-c |
| **G-URO-06** | **错配率**可度量：`hero_mismatch_rate`、`dense_streak_violation_rate` ↓ **≥ 30%** | `layoutMetrics` 扩展（**诊断，非 Gate**） | P0-c |
| **G-URO-07** | （P1）`usage.signals` 结构化字段 | schema + validator；与 TSL 单 schema | P1 |
| **G-URO-08** | （P2）章级 LLM 回避列表 | 单独 IG；依赖 AC-URO-BLIND | P2 |

### 2.2 非目标

- **不**重复建设 TSL PRD 中的管理台 13 API / 4 Tab（编辑仍走 git + YAML）。
- **不**做 ingest 标签 → 词表 → suitedContent 软匹配（P2+；与 URO 正交）。
- **不**修改模板几何、不新增模板 SKU（仅改变**选用**）。
- **不**保证 mobile legacy `items[]` 引擎（首期仅 `layoutEngine=screens` Web）。
- **不**用 golden proxy（layoutMetrics 代理分）作为 **`enabled=true` 合并依据**。
- **首 PR（P0-a）不承诺** AC-URO-BLIND ≥55%。

---

## 3. 总体方案

### 3.1 设计原则

```text
usage 自然语言（人读）
        ↓ 人工 + 脚本维护
usage.signals（机读，P1 起 · 与 TSL 单 schema）
        ↓
Usage Rule Registry（P0-a：Python 常量；P1：registry.yaml）
        ↓
WindowContext（hero 分差、P21 dense 状态、章位…）
        ↓
filter_candidates()  → 排除 + 记录 reason
        ↓  （legacy / self-heal / replan 同一入口）
既有 scorer.pick_best_window()  → 不变或 tie-break
        ↓
mosaicDecisionLog.usageRuleHits
```

**优先级（已拍板 · 见 §3.5）**：

```text
几何硬约束（LTE slot_geometry / mainSlotPolicy）
  > usage 硬排除（UR-xx）
  > P21/BQ-202 rhythm 硬过滤（can_emit_pattern · 上提为硬排除，见 §3.5）
  > scorer 软分（既有 LSE · 不含 usage 乘子）
  > usage tie-break（UT-xx · P1）
```

### 3.2 架构图

```mermaid
flowchart TB
  subgraph INPUT [输入]
    USAGE[LTE YAML usage + signals]
    WIN[窗口特征 heroGap / mix / tags]
    CTX[P21 ScreenLayoutPlannerState]
  end

  subgraph ENGINE [Usage Rules Engine · 新增]
    REG[usage_rules/registry · P0 Python 常量]
    EVAL[evaluate_reject(templateId, ctx) → bool]
    LEG[legacy_guard · 同一 evaluate_reject]
  end

  subgraph MCS [既有 MCS]
    GEO[geometry + mainSlot 硬过滤]
    CAND[generate_window_candidates]
    SCORE[score_candidate · pick_best_window]
  end

  subgraph OUT [输出]
    SCR[screens[]]
    LOG[mosaicDecisionLog + usageRuleRejects]
    MET[layoutMetrics 错配率]
  end

  USAGE --> REG
  WIN --> EVAL
  CTX --> EVAL
  GEO --> CAND
  CAND --> EVAL
  EVAL -->|reject| LOG
  EVAL -->|allow| SCORE
  SCORE -->|no_candidates| LEG
  LEG -->|guard reject| LOG
  LEG -->|allow| SCR
  SCORE --> SCR
  SCORE --> LOG
  LOG --> MET
```

### 3.3 与现有模块的落点

| 模块 | 文件 | 改动 |
|------|------|------|
| 规则注册表 | `travelogue/curation/usage_rules/registry.py`（P0-a） | **新增**；P1 可迁 `registry.yaml` |
| 规则求值 | `travelogue/curation/usage_rules/evaluator.py` | **新增** |
| 窗口上下文 | `travelogue/curation/usage_rules/context.py` | **新增** |
| density 统一 | `travelogue/curation/usage_rules/density.py` | **新增** `classify_screen_density()` |
| MCS 候选 | `curation/mosaic/candidates.py` | 过滤钩子 + rejected reason |
| Legacy 守门 | `curation/mosaic/legacy.py` · `compose.py` | **必须**过 `evaluate_reject` |
| MCS 选优 | `curation/mosaic/compose.py` | tie-break 偏置（P1） |
| 非 mosaic 屏 | `curation/screen_planner_stages.py` | UR-04 等价逻辑（P0-b） |
| 配置 | `travelogue/config/layout.py` | `UsageRulesConfig` |
| 指标 | `curation/curate.py` · layoutMetrics | 错配率 |
| Schema | `schemas/trip.schema.json` | log 字段（`mosaicDecisionLogEntry` 须扩展） |

### 3.4 Legacy 守门（阻塞项 · P0-a 必做）

**问题**：`compose.py` 在 `no_candidates` 时走 `legacy.py`；后者对 5 图窗 **硬编码** `screen-mosaic-5-main-portrait-3land`，不经过 usage filter，会直接触发 URO-P-02。

**要求**：

1. `build_legacy_screen()` 在返回 screen 前，对拟 emit 的 `patternId` 调用 **`evaluate_reject(pattern_id, ctx)`**；若 reject → 返回 `None` 或改选下一 legacy 候选。
2. `self-heal` / `replan` 路径在重新 pick 后 **再次** 跑 usage filter。
3. **AC-URO-09**：legacy 路径 **不得** emit 会被当前 enabled UR-xx reject 的 pattern。

```python
# legacy.py · 守门伪代码
screen = _build_legacy_candidate(...)
if screen and usage_rules.enabled:
    pid = screen.get("patternId") or screen.get("templateId")
    if evaluate_reject(pid, ctx):
        return None  # 或尝试下一 legacy 分支
return screen
```

### 3.5 Rhythm 硬过滤决策（阻塞项 · 与 BQ-202 对齐）

**问题**：今日 `can_emit_pattern=false` 在 `score_candidate` 里是 **0.5 软乘子**，与 PRD「usage 硬排除 > rhythm 配额」矛盾。

**拍板（D3 延伸）**：

- UR-02 / UR-05 **不**维护独立 `chapter_dense_count` / `screens_since_breath`。
- 改为调用 **`ScreenLayoutPlannerState.can_use_dense_collage()`** / **`last_was_dense_collage`**（BQ-202 同一模块）。
- BQ-202 落地时，将 rhythm 违规从软乘子 **上提为硬过滤**（与 usage 同级，在 `pick_best_window` 之前）。
- usage 规则 log reason 前缀：`usage_rule:UR-02` 或 `rhythm:bq202`（实现层可合并，PRD 层语义一致）。

### 3.6 空候选策略（阻塞项）

**禁止** reject 到 0 候选后 silent fallback。顺序写死：

```text
1. 若 reject 后 candidates 为空 → 撤销「最弱 reject」规则（按 rule priority 逆序），直到非空
2. 仍为空 → 缩窗（减小 window size，MCS 既有重试）
3. 仍为空 → legacy（须过 §3.4 legacy 守门）
4. legacy 仍 None → skip 窗口 + warn log
```

**禁止**：直接 emit 会被 UR-xx reject 的 pattern（含 legacy 硬编码路径）。

### 3.7 统一 density 分类

PRD v0.1 自定义 dense 枚举与代码 `is_dense_collage_pattern()` 双轨。**统一**为单一函数：

```python
# travelogue/curation/usage_rules/density.py

def classify_screen_density(pattern_id: str) -> Literal["airy", "balanced", "dense"]:
    """
    权威定义 · 全项目复用：
    - dense: is_dense_collage_pattern(pattern_id) 或 mosaic-*-hero-* / mosaic-*-main-*
    - airy: slots ≤ 2 或 landscape-1 / portrait-1 / editorial（非 composite）
    - balanced: 其余
    """
```

UR-02/05、layoutMetrics、`hero_mismatch` 脚本 **只** 引用此函数 + P21 state，不得另写 pattern 集合。

---

## 4. 规则规格（权威清单）

规则 ID 与模板 `usage.whenNotToUse` **逐条可追溯**（维护时同 PR 修改）。

### 4.1 P0 规则表（6 条 · 硬排除）

| 规则 ID | 适用模板 | 条件（WindowContext + P21 state） | 动作 | usage 出处 | 交付 |
|---------|----------|-----------------------------------|------|------------|------|
| **UR-01** | `screen-mosaic-5-main-hero-plus-4`, `screen-mosaic-6-main-hero-plus-5` | `main_eligible_hero_score_gap < 0.15` | **reject** | main-hero whenNotToUse §1 | **P0-a** |
| **UR-02** | 同上 + 其他 hero-led dense 模板 | `not layout_state.can_use_dense_collage(pattern_id)` 或 `layout_state.last_was_dense_collage`（**复用 BQ-202**） | **reject** | main-hero whenNotToUse §2 | **P0-a** |
| **UR-03** | `screen-mosaic-5-hero-3-2-plus-4` | 与现有 `slot_geometry` / `landscape_forbidden_tall` **守卫聚合**；仅当几何 guard 已 pass 且仍违反 usage 意图时 reject | **reject**（别名 + 统一 reason） | hero-3-2 whenNotToUse §1 | **P0-b** |
| **UR-04** | `screen-mosaic-5-main-portrait-3land` | 窗口内竖图 `hero_score == max(window)` 且竖图仅 1 张 | **reject** | main-portrait whenNotToUse §1 | **P0-b** |
| **UR-05** | `screen-landscape-9`, `screen-portrait-9` | **`layout_state.can_use_dense_collage(pattern_id)` == false**（与 UR-02 同一 P21 入口，不独立计数） | **reject** | portrait/landscape-9 whenNotToUse §2 | **P0-b** |
| **UR-06** | `screen-editorial-4mix` | 章内 `editorial_count >= rhythm.max_per_chapter` | **reject** | editorial rhythm | **P0-b** |

**P0 删除 / 延后**：

| 原 ID | 处置 |
|-------|------|
| **UR-07** | **移 P1**，并入 **UT-01**（prefer landscape-6，非 reject） |
| **UR-08** | **移 P1**；P0 用 patternId 硬编码集合，P1 读 `usage.signals.needsHero` |

**hero_score_gap 定义（修订 · 对齐 mainSlotPolicy）**：

```python
# 在 main-eligible landscape 子集上算（对齐 main_eligibility / mainSlotPolicy）
eligible = [effective_hero_score(a) for a in window if main_slot_eligible(a)]
if len(eligible) <= 1:
    main_eligible_hero_score_gap = float("inf")
else:
    eligible.sort(reverse=True)
    main_eligible_hero_score_gap = eligible[0] - eligible[1]
```

WindowContext 字段名：**`main_eligible_hero_score_gap`**（废弃 v0.1 的 `hero_score_gap` 歧义命名）。

### 4.2 P1 tie-break 规则（4 条 · 不 exclude）

| 规则 ID | 条件 | 动作 | 来源 |
|---------|------|------|------|
| **UT-01** | UR-01 边缘（0.15 ≤ gap < 0.22）且 `mosaic-5-main-hero-plus-4` vs `landscape-6` 同分；**或** UR-01 已 reject hero 模板后仅剩 landscape-6 | +0.05 偏向 `landscape-6` | 原 UR-07 + UT-01 合并 |
| **UT-02** | 窗口 3 图、1P+2L 且竖图 hero 最高 | +0.05 偏向 `portrait-1-landscape-2` over mosaic | P1 |
| **UT-03** | 3 竖 run、Web export | +0.05 偏向 `portrait-3-editorial` over `portrait-3` | P1 |
| **UT-04** | family `mosaic-5-*` 且 `usage.signals.needsHero == strong` 且 UR-01 触发 | +0.03 偏向非 hero  siblings（读 signals） | 原 UR-08 软化 |

tie-break 增量 **≤ 0.05**，且仅在 `score_delta < 0.03` 时生效。

### 4.3 规则与模板 usage 的同步契约

| 变更类型 | 要求 |
|----------|------|
| 修改 `whenNotToUse` 语义 | 同 PR 更新 registry 对应规则 |
| 新增 GA 模板 | `usage` 必填 + 评估是否注册 UR/UT |
| 规则 ID 废弃 | registry 标记 `deprecated` + 保留 1 版本 |

CI：`scripts/check_usage_rules_sync.py`（**P1**）扫描 registry 引用的 `ruleIds` 与模板 `usage.ruleIds` 一致。

---

## 5. 数据模型

### 5.1 `usage.signals` 扩展（P1 · 与 TSL 单 schema）

在既有 `usage` 下增加机器可读字段（**不替代** whenToUse prose）。**字段名与 TSL PRD §5 对齐**，URO 只读下列子集：

```yaml
usage:
  summary: ...
  whenToUse: |
    - ...
  whenNotToUse: |
    - ...
  signals:
    needsHero: strong       # none | weak | strong
    density: dense          # airy | balanced | dense · 与 classify_screen_density 一致
    mixRole: hero-led       # equal | hero-led | portrait-accent | editorial
  ruleIds:                  # 可选
    - UR-01
    - UR-02
  siblings: [...]
```

P0-a 规则 **硬编码 patternId 集合**；P1 改为读 `signals.*`。

### 5.2 WindowContext（求值输入）

```python
@dataclass(frozen=True)
class WindowContext:
    window_asset_ids: tuple[str, ...]
    aspects: dict[str, AspectKind]
    assets_map: dict[str, dict]
    main_eligible_hero_score_gap: float      # 修订：main-eligible 子集
    main_eligible_hero_scores: tuple[float, ...]  # 调试 / log
    window_top_hero_asset_id: str | None
    portrait_hero_is_max: bool
    layout_state: ScreenLayoutPlannerState   # 修订：直接引用 P21 state
    chapter_editorial_count: int
    chapter_index: int
    chapter_count: int
    trip_total_photos: int
```

由 `ChapterPlanContext` + 已生成 `screens[]` 前缀在 `try_mosaic_window` / `screen_planner` 入口构建。**不**额外 LLM 调用。废弃 v0.1 独立字段 `prev_screen_density` / `chapter_dense_count` / `screens_since_breath`（改读 `layout_state`）。

### 5.3 decision log 扩展

`mosaicDecisionLog[]` 条目追加（**须同步修改** `schemas/trip.schema.json` · `mosaicDecisionLogEntry`，当前 `additionalProperties: false`）：

```json
{
  "screenId": "ch-02-sc-03",
  "patternId": "screen-landscape-6",
  "usageRuleRejects": [
    { "ruleId": "UR-01", "templateId": "screen-mosaic-5-main-hero-plus-4", "detail": "main_eligible_gap=0.09" }
  ],
  "usageRuleHits": [
    { "ruleId": "UT-01", "action": "prefer", "templateId": "screen-landscape-6" }
  ]
}
```

`layoutMetrics` 追加：

```json
{
  "usageRules": {
    "enabled": true,
    "rejectCount": 12,
    "heroMismatchScreens": 0,
    "denseStreakViolations": 1
  }
}
```

---

## 6. 配置与开关

```yaml
# config.yaml
layout:
  usage_rules:
    enabled: false              # 默认关 · AC-URO-01（runtime 默认 true 见 layout.py · 2026-07-05）
    hero_gap_threshold: 0.15    # UR-01
    hero_gap_prefer_threshold: 0.22  # UT-01 上界
    tiebreak_enabled: false     # P1 · UT-01～04
    log_rejections: true
    disabled_rules: []          # AC-URO-02 · 单条禁用
```

### 6.1 配置开关矩阵（AC-URO-01 baseline 定义）

| `usage_rules.enabled` | `mosaic.enabled` | `tiebreak_enabled` | 期望行为 |
|----------------------|------------------|-------------------|----------|
| `false` | `true` | `*` | **与当前 production baseline 逐屏一致**（AC-URO-01 权威行） |
| `false` | `false` | `*` | 同上（无 mosaic 路径） |
| `true` | `true` | `false` | UR 硬排除生效；无 UT tie-break |
| `true` | `true` | `true` | UR + UT 全生效 |
| `true` | `false` | `*` | UR 作用于 screen_planner 路径；legacy 仍须守门 |

**AC-URO-01 测试配置**：`usage_rules.enabled=false` + `mosaic.enabled=true` + `tiebreak_enabled=false`，与 `_golden/` 或 `layout_snapshot` baseline 逐屏 diff。

**不**写入 LSE 策略包 `layout_engine/strategies/default.yaml`。

---

## 7. 算法流程

### 7.1 MCS 窗口路径

```text
try_mosaic_window(ctx, start)
  → slice window asset_ids
  → build WindowContext（含 layout_state）
  → generate_window_candidates_with_rejections(...)
       for each pattern in registry:
         if geometry_ok and main_ok:
           if usage_rules.enabled and evaluate_reject(pattern, ctx):
             rejected.append({ reason: "usage_rule:UR-xx" })
             continue
           → build candidate
       if candidates empty → §3.6 空候选策略
  → pick_best_window(candidates)
  → append usageRuleHits to log
```

### 7.2 Legacy / self-heal 路径

```text
pick_best_window → no_candidates
  → build_legacy_screen(...)           # legacy.py
  → evaluate_reject(patternId, ctx)    # §3.4 守门
  → if reject: None → 下一分支或 §3.6

self_heal / replan:
  → 重 pick 后再次 evaluate_reject
```

### 7.3 screen_planner 非 mosaic 路径（P0-b）

接入 **UR-04** 等价逻辑：在 `mixed` / portrait carry 阶段，若检测到「单竖 hero + 横 run 可组 mosaic-5-main-portrait」，改 prefer `portrait-1` 或 `portrait-1-landscape-2`。

### 7.4 性能

- 每窗口每模板 O(1) 规则求值；规则数 ≤ 20。
- 无网络、无 LLM。
- 预期 curate 耗时 +< 1%。

---

## 8. 效果评估体系

### 8.1 发布门禁

| 阶段 | 门槛 | 方法 | merge 策略（D5） |
|------|------|------|------------------|
| **P0-a 基础设施** | AC-URO-01/02/03 + legacy 守门 | CI fixture（2～3 本）+ 单测 | **`enabled=false` 可 merge** |
| **AC-URO-BLIND**（IG-2 · `enabled=true`） | 8 本 golden trip pairwise **≥ 55%** vs off | Phase 18 blind harness | **未达标不得 merge `enabled=true`** |
| **P1 tie-break** | AC-URO-BLIND **≥ 60%**（`tiebreak_enabled=true`） | 同上 | IG-2 子 Gate |
| **Program 北极星** | **≥ 65%** | BQP 路线图 | 非单特性 Gate |

> **命名说明**：BQP 路线图 **IG-1 = 选片（subset）**；URO 盲评 Gate 统一称 **`AC-URO-BLIND`**，挂载 **IG-2（18.2 版式包）**，避免与 IG-1 混淆。

**盲评协议（AC-URO-04 扩展）**：

- 每本 trip ≥3 名评审，盲法 A/B 顺序随机。
- **分维度评分**（版式匹配、呼吸感、hero 主次）——用于诊断，**不**替代 aggregate 55% Gate。
- **per-trip 归因表**：每本 trip 单独 win/loss/tie，aggregate Gate + 分类型诊断（D7）。
- **Studio trip 回归**：linzhi 等已知问题 trip **一票否决**（单 trip 盲评 loss 须书面归因）。

### 8.2 诊断指标（非门禁，必报）

| 指标 | 定义 | baseline 对比 |
|------|------|---------------|
| `hero_mismatch_rate` | 选用 hero 模板但 UR-01 会 reject 的屏占比 | ↓ ≥ 30% |
| `dense_streak_violation_rate` | 连续两屏 dense 且无 breath 占比 | ↓ ≥ 30% |
| `pattern_exposure_entropy` | 章内 pattern 分布熵 | 不下降 |
| `usage_rule_reject_rate` | 被拒绝候选数 / 总候选数 | 监控调参 |

> **注意**：错配率 ↓30% 与 AC-URO-BLIND ≥55% **可并行但不互相保证**；代理指标改善 ≠ 盲评 win。

### 8.3 回归安全

| ID | 要求 | 阶段 |
|----|------|------|
| **AC-URO-01** | `usage_rules.enabled=false` → screens 序列与 baseline **完全一致**（见 §6.1 矩阵） | P0-a |
| **AC-URO-02** | 单条规则可 `disabled_rules: [UR-01]` 禁用 | P0-a |
| **AC-URO-03** | 每条 UR-xx 有 unit test + ≥1 `_golden/usage_rules/` fixture | P0-a/b |
| **AC-URO-09** | legacy / self-heal **不得** emit 会被 UR-xx reject 的 pattern | P0-a |

---

## 9. 前端与可观测性

### 9.1 P0-a（最小）

- 无新 UI 阻断发布。
- `trip.json` · `curation.mosaicDecisionLog` 含 `usageRuleRejects`（JSON 可 jq）。

### 9.2 P1（Studio 只读）

| 位置 | 内容 |
|------|------|
| templates-admin · 模板详情 | 折叠展示 `usage` + 绑定的 `ruleIds` |
| 决策日志 | 展开 `usageRuleRejects` / `usageRuleHits` |
| curate metrics | `layoutMetrics.usageRules.rejectCount` |

**不做** usage 在线编辑（仍 git）。

---

## 10. 实施路线

| 阶段 | 周期 | 交付 | merge 条件 |
|------|------|------|------------|
| **P0-a · 基础设施 + 核心 2 规则** | 5～7d | `usage_rules/` 包 · WindowContext · config · **UR-01/UR-02** · legacy 守门 · log schema · AC-URO-01/02/03/09 · CI 2～3 fixture | `enabled=false` **可 merge** |
| **P0-b · 剩余 P0 规则** | 5d | UR-03～UR-06 · screen_planner UR-04 · 空候选策略 · `_golden/usage_rules/` | `enabled=false` 可 merge |
| **P0-c · 评估** | 4d + WS-0 | 8 本 trip off/on 盲评 · 错配率脚本 · **AC-URO-BLIND 报告** | **`enabled=true` 须过 Gate** |
| **P1 · signals + tie-break** | 5d | `usage.signals` schema · UT-01～04 · check_usage_rules_sync | IG-2 子 Gate ≥60% |
| **P1 · Studio 只读** | 3d | admin 展示 usage + rule hits | 随 P1 |
| **P2（可选）** | 评审后 | 章级 LLM 回避 · 见 TSL PRD §6.2 | 独立 IG |

**首 PR 范围（强制）**：**仅 P0-a** — 约 400～700 LOC；**不**一次交付 UR-01～UR-08 全量；**不**绑 AC-URO-BLIND merge。

**工程 backlog（P0-a 后）**：

1. main-eligible 预览层（与 `main_eligibility.py` 对齐）
2. window size 重试与 usage filter 联动
3. BQ-202 rhythm 硬过滤上提（与 UR-02/05 合并 PR）

---

## 11. 验收标准

| ID | 级别 | 描述 |
|----|------|------|
| **AC-URO-01** | P0-a | usage_rules off 时 screens 与 baseline 一致（§6.1 矩阵） |
| **AC-URO-02** | P0-a | UR-01 触发时 main-hero 出现在 rejected；选用非 hero 模板 |
| **AC-URO-03** | P0-a | mosaicDecisionLog 含 usageRuleRejects |
| **AC-URO-04** | P0-c | **AC-URO-BLIND**：8 本 golden ≥55%；含 per-trip 表 + 分维度诊断 + Studio trip 回归 |
| **AC-URO-05** | P0-c | hero_mismatch_rate ↓ ≥30%（诊断，非 merge 替代 AC-URO-BLIND） |
| **AC-URO-06** | P1 | tiebreak 独立开关；on 时 AC-URO-BLIND ≥60% |
| **AC-URO-07** | P1 | `usage.signals` validator 通过 |
| **AC-URO-08** | P1 | templates-admin 只读展示 rule hits |
| **AC-URO-09** | P0-a | legacy / self-heal 不过 usage filter 不得 emit |

---

## 12. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 规则过严 → 可用候选为空 | 窗口跳过或降级失败 | §3.6 空候选策略；禁止 silent bad emit |
| legacy 绕过 usage | URO-P-02 持续发生 | §3.4 legacy 守门 + AC-URO-09 |
| hero_gap 阈值敏感 | 盲评不稳定 | IG 报告扫 0.12/0.15/0.18；默认保守 |
| usage 文案与规则漂移 | 文档说谎 | ruleIds 绑定 + check_usage_rules_sync CI |
| UR-05 与 P21 重复 | 双重 reject / 计数不一致 | D3：单一 `can_use_dense_collage` 入口 |
| rhythm 软惩罚 vs usage 硬排除 | 规则被 scorer 覆盖 | §3.5 BQ-202 硬过滤上提 |
| 仅 mosaic 受益 | 整体盲评提升不足 | P0-b screen_planner UR-04 |
| 代理指标达标、盲评未升 | 错误 merge | AC-URO-BLIND 为唯一 `enabled=true` Gate |

---

## 13. 与 PRD-TEMPLATE-SEMANTIC-LAYER 的关系

| TSL PRD 条目 | 本 PRD |
|--------------|--------|
| 全量 semantics 词表 + ingestTagMap | **不做**（P2+ 独立） |
| LSE semantic_weight | **明确不做 · 冻结（D6）** |
| 管理台 13 API | **不做**（P1 只读） |
| LLM 艺术指导 | **P2 可选**，依赖 AC-URO-BLIND |
| usage 文档 | **已完成的输入** |
| **`usage.signals` / `semantics` schema** | **单 schema（D4）**：TSL 扩展时 URO 只读子集，禁止双写字段 |
| decision log 可解释 | **P0-a 做** |
| 盲评门禁 | **P0-c · AC-URO-BLIND** |

---

## 14. 开放问题

| # | 问题 | v0.2 结论 |
|---|------|-----------|
| Q1 | UR-01 hero_gap 0.15 是否按 trip 规模分档？ | 先全局常数；AC-URO-BLIND 报告再定 |
| Q2 | portrait-3（9:16 stage）是否纳入 Web screens 规则？ | P0 仅 log 统计；P1 与 exportLayout 对齐 |
| Q3 | 规则变更是否走 experimental flag 逐条 rollout？ | `disabled_rules[]` 足够 |
| Q4 | 盲评未达 55% 是否允许 merge？ | **W0/P0-a infra 可 merge；`enabled=true` 否（D5）** |
| Q5 | IG 命名与 BQP IG-1 冲突？ | **已解决：AC-URO-BLIND · IG-2（D2）** |
| Q6 | rhythm 软惩罚 vs usage 硬排除？ | **已解决：BQ-202 硬过滤上提（§3.5）** |

---

## 15. 附录

### 15.1 示例：UR-01 求值伪代码

```python
def evaluate_ur01(pattern_id: str, ctx: WindowContext, cfg: UsageRulesConfig) -> bool:
    if pattern_id not in HERO_LED_PATTERNS:
        return False
    if ctx.main_eligible_hero_score_gap >= cfg.hero_gap_threshold:
        return False
    return True
```

### 15.2 示例：UR-02 复用 P21（非独立计数）

```python
def evaluate_ur02(pattern_id: str, ctx: WindowContext, cfg: UsageRulesConfig) -> bool:
    if pattern_id not in HERO_LED_DENSE_PATTERNS:
        return False
    st = ctx.layout_state
    if st is None:
        return False
    if not st.can_use_dense_collage(pattern_id):
        return True  # reject
    if st.last_was_dense_collage:
        return True  # reject · breath
    return False
```

### 15.3 8 本 golden trip（与 BQP 一致）

见 [ROADMAP-PHASE18-BOOK-QUALITY.md](./ROADMAP-PHASE18-BOOK-QUALITY.md) §2.3。

### 15.4 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-07-04 | 初稿：规则清单、架构、盲评门禁、Phase 18 对齐、与 TSL 分工 |
| v0.2.0 | 2026-07-04 | **评审修订**：采纳 D1～D8；AC-URO-BLIND/IG-2 命名；legacy 守门；P21/BQ-202 去重；`classify_screen_density`；main-eligible gap；UR-07→UT-01；P0-a/b/c 分期；配置矩阵；TSL 单 schema；rhythm 硬过滤决策；空候选策略 |
