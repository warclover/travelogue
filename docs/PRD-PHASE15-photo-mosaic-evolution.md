# Travelogue · Phase 15 产品需求文档（PRD · 拼图模板演进）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | v0.15.1-PHASE15 |
| **状态** | Draft |
| **Phase 15 代号** | 「拼图模板演进」— 从硬匹配到候选打分 |
| **前置条件** | `layout_engine=screens` 稳定；Phase 9/10 已完成基础筛图与 grid 能力 |
| **关联文档** | [PRD-PHASE10-food-grid.md](./PRD-PHASE10-food-grid.md)、[PRD-PHASE13.md](./PRD-PHASE13.md)、[PRD-PHASE15-benchmark.md](./PRD-PHASE15-benchmark.md)、`travelogue/curation/screen_planner.py`、`travelogue/curation/screen_planner_stages.py`、`travelogue/curation/layout_search.py` |
| **更新日期** | 2026-06-04 |

> **定位**
>
> - 当前拼图编排在 `screen_planner_stages.py` 采用“阶段式命中即返回”的硬规则流程。
> - 5 张拼图虽已实现（`screen-mosaic-5-main-portrait-3land`），但触发条件过窄，导致线上几乎不可见。
> - Phase 15 目标是升级为“候选集生成 + 统一打分选择”，在保证稳定性的前提下提升中小张数模板的可见性与审美一致性。

---

## 1. 背景与问题

### 1.1 现状摘要

当前代码中：

1. 通用 pattern 档位集中在 `1/2/3/4/6/9`，5 张是专用特例。
2. 5 张特例受限于多重硬条件（例如全局照片数门槛、横竖比例、时间链）。
3. 流程采用“先命中先返回”，无法在多个可行布局中做质量比较。

### 1.2 用户可感知问题

| ID | 问题 | 用户体感 |
|----|------|----------|
| **P15-P-01** | 5 张拼图几乎不出现 | “系统有很多布局，但经常只看到常见几种” |
| **P15-P-02** | 对同一批素材，布局选择刚性 | “稍微不满足条件就退化成单图/双图” |
| **P15-P-03** | 编排节奏局部最优 | “单屏可能合理，但整章视觉变化不足” |

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 | 说明 |
|----|------|------|
| **G-P15-01** | 提升 5 张模板可见性 | 在真实数据中稳定出现，不再极端稀有 |
| **G-P15-02** | 统一候选打分机制 | 替代关键路径上的硬早停 |
| **G-P15-03** | 保持渲染兼容 | 不破坏现有 `patternId -> gridClass -> CSS` 渲染链 |
| **G-P15-04** | 提升节奏多样性 | 减少模板重复和“过早退化” |
| **G-P15-05** | 可观测可回滚 | 支持灰度、指标观测、快速关闭新策略 |

### 2.2 非目标

- 本 phase 不做端到端机器学习在线服务。
- 不重写 `render/context.py` 与模板引擎架构。
- 不在本 phase 引入用户手动指定单屏布局 UI。
- 不强制替换全部旧规则，仅替换关键瓶颈路径（优先 5 张窗口）。

---

## 3. 设计原则

| ID | 原则 | 说明 |
|----|------|------|
| **P15-PR-01** | 渐进替换 | 先 5 张场景，后扩展到其他张数 |
| **P15-PR-02** | 软约束优先 | 条件尽量转为打分项，而非 hard fail |
| **P15-PR-03** | 可解释决策 | 输出每次命中的候选与分数摘要 |
| **P15-PR-04** | 结果稳定性 | 同输入可复现，避免随机漂移 |
| **P15-PR-05** | 默认安全回退 | 异常或低置信回退现有稳态规则 |

---

## 4. 方案概述

## 4.1 核心升级：两段式决策

将当前“命中即返回”替换为：

1. **候选生成（Generate）**：根据窗口资产生成多个可行 pattern 候选。
2. **候选打分（Score）**：统一评分后选 Top-1（或 Top-K 再经节奏约束）。

## 4.2 首批覆盖范围（P15 必做）

1. 5 张窗口（`len(window)==5`）从单一路径升级为候选族。
2. 保持 `screen-mosaic-5-main-portrait-3land` 兼容，同时新增 4~6 个 5 张 pattern。
3. `try_mosaic_five()` 升级为 `generate_five_candidates()` + `pick_best_candidate()`。

## 4.3 后续扩展（P15+）

- 扩展 7 张、10 张等中间档位。
- 将 3 张混排和 4 张布局纳入统一候选评分。
- 与 `layout_search` 深度融合，实现章节级全局优化。

---

## 5. 功能规格

## 5.1 新增 Pattern（5 张家族）

首版建议至少包含：

1. `screen-mosaic-5-main-portrait-3land`（保留）
2. `screen-mosaic-5-main-landscape-2portrait-2land`
3. `screen-mosaic-5-2portrait-3land-balanced`
4. `screen-mosaic-5-3portrait-2land-balanced`
5. `screen-mosaic-5-main-hero-plus-4`

说明：

- 命名与 `patternId` 可在设计评审后冻结。
- 每个新 pattern 必须对应 `grid_class_for_pattern()` 映射与 CSS。

## 5.2 候选生成器

输入：

- `asset_ids`（窗口内）
- `aspects`
- `assets_map`
- `context`（trip_total、章节位次、近期 pattern 历史）

输出：

- `list[ScreenCandidate]`

`ScreenCandidate` 建议字段：

- `patternId`
- `orderedAssetIds`
- `slots`
- `featureSummary`（比例、时间链、人物占比等）
- `hardValid`（仅保留结构不可行的硬约束）

## 5.3 打分器（统一）

建议评分函数：

`score = Σ(w_i * f_i) - penalties`

首版评分特征：

1. `f_time_cohesion`：时间接近度（软约束）
2. `f_aspect_fit`：横竖匹配度
3. `f_main_quality`：主图质量（可复用 hero score）
4. `f_subject_cohesion`：主体一致性
5. `f_pattern_novelty`：与最近模板重复惩罚
6. `f_chapter_rhythm`：章节节奏匹配

硬约束仅保留：

- slot 数量一致
- 必要角色位可填充
- 数据完整性合法

## 5.4 规则软化（关键）

将以下条件由 hard fail 改为 soft score：

1. `trip_total >= 35`（改为权重项）
2. 时间链严格连续（超窗改惩罚）
3. 单一横竖比例要求（允许次优模板）

## 5.5 可观测输出

每次窗口决策写入 `layoutDecisionLog`（或现有决策日志扩展）：

- `windowSize`
- `candidatesCount`
- `winnerPatternId`
- `winnerScore`
- `top3Scores`
- `top3Patterns`
- `winnerReasonCodes`
- `fallbackUsed`
- `fallbackReason`
- `routerVersion` / `scorerVersion`

---

## 6. 配置与开关

新增配置建议：

```yaml
layout:
  mosaic_v2:
    enabled: true
    scope:
      five_photo_window: true
    scorer_version: "p15-s1"
    min_candidate_score: 0.35
    fallback_to_legacy: true
    weights:
      time_cohesion: 0.20
      aspect_fit: 0.25
      main_quality: 0.25
      subject_cohesion: 0.15
      pattern_novelty: 0.10
      chapter_rhythm: 0.05
```

要求：

1. 开关默认可回退到 legacy 路径。
2. 权重修改需有版本号，便于回放。

---

## 7. 指标与验收

## 7.1 观测指标

- `layout.mosaic5.exposure_rate`
- `layout.mosaic5.win_score_p50/p90`
- `layout.pattern.repeat_rate`
- `layout.mosaic_v2.fallback_rate`
- `layout.mosaic_v2.low_score_fallback_rate`
- `layout.render.error_rate`

## 7.2 验收标准（AC）

| ID | 验收条件 |
|----|----------|
| **AC-P15-01** | 5 张窗口支持候选集 + 打分，不再单一路径硬匹配 |
| **AC-P15-02** | 至少新增 4 个 5 张 pattern，且渲染链完整可用 |
| **AC-P15-03** | 在 fixture 与真实回放中，5 张模板出现率显著高于基线 |
| **AC-P15-04** | 打分决策可回放，含候选与 winner 分数 |
| **AC-P15-05** | 异常场景可自动回退 legacy，不影响导出链路 |
| **AC-P15-06** | 无明显回归：渲染失败率与基线持平或更优 |
| **AC-P15-07** | 每次 5 张窗口决策记录 top3 候选（`patternId+score`）与 winner `reasonCodes` |
| **AC-P15-08** | 当 winner 分数低于阈值时，自动回退 legacy 并记录 `fallbackReason=low_score` |

---

## 8. 实施计划（建议三阶段）

| 阶段 | 周期 | 内容 | 输出 |
|------|------|------|------|
| **P15-W1** | 1 周 | 5 张新 pattern + CSS + 候选数据结构 | 可生成候选并渲染 |
| **P15-W2** | 1 周 | 打分器接入 + 开关 + 决策日志 | 可灰度运行与观测 |
| **P15-W3** | 1 周 | 参数调优 + 回放评估 + 默认开启评审 | 形成稳定默认策略 |

---

## 9. 测试计划

### 9.1 单元测试

- 候选生成：不同横竖组合输出合理候选。
- 打分稳定：同输入同版本输出一致 winner。
- 软约束验证：时间超窗仍可出候选但分数降低。

### 9.2 集成测试

- `plan_screens_for_chapter()` 在 `len==5` 场景走新路径。
- `grid_class_for_pattern()` 与样式映射覆盖新增 pattern。
- fallback 开关关闭时行为回归 legacy。

### 9.3 回归测试

- 对现有 golden trip 跑 A/B：对比 `pattern 分布`、`重复率`、`渲染错误率`。
- 重点检查人物密集、风景密集、混合场景三类样本。

---

## 10. 风险与缓解

| 风险 | 影响 | 缓解策略 |
|------|------|----------|
| 打分权重不佳 | 布局质量波动 | 版本化权重 + 灰度 + 回放评估 |
| 模板过多导致不稳定 | 视觉风格跳跃 | 节奏惩罚 + 章节级重复抑制 |
| 新 pattern 样式问题 | 渲染错位 | pattern 与 CSS 成对验收 |
| 线上行为不可解释 | 排障困难 | 决策日志与 scorerVersion 强制落盘 |

---

## 11. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.15.1 | 2026-06-04 | 增补可观测与验收硬条款：top3 候选日志、winner reasonCodes、低分回退原因与对应指标 |
| v0.15.0 | 2026-06-04 | 初稿：定义拼图模板从硬匹配升级为候选打分方案，先覆盖 5 张窗口 |

