# ADR-002 · 智能排版 V2 与现有 pipeline 融合

| 属性 | 内容 |
|------|------|
| **状态** | 已采纳 |
| **日期** | 2026-05-26 |
| **决策者** | 项目负责人 |
| **影响范围** | Agent 1.5 组屏、curate、config、schema、测试 |
| **关联文档** | [智能排版 V2](../智能排版V2.md) |

---

## 背景

1. 现有 `screen_planner.plan_screens_for_chapter` + `build_chapters_from_buckets` 已在线上 trip（linzhi / mao / maomi）验收，行为稳定。  
2. V2 PRD 提出 beam search、多信号评分、叙事弧、降级护栏与反馈回路，若整段替换现有组屏，回归成本高、风险大。  
3. 需要在不破坏默认行为的前提下，逐步引入 V2 能力并可通过配置开关与黄金样本验证等价性。

---

## 决策

### D1 · 定位：补强 + 包裹，非完全替代

| 项 | 决定 |
|----|------|
| **保留** | `run_curate`、`build_chapters_from_buckets`、`attach_screens_to_chapters`、`render` 主路径 |
| **候选生成** | 现有 `plan_screens_for_chapter` 作为 **候选生成器**，不删改其核心规则 |
| **外层搜索** | 新建 `layout_search.replan_chapters_with_beam`，仅在 `layout.scoring.enabled=true` 时包裹调用 |
| **默认行为** | `layout.scoring.enabled: false` → 与 ADR 采纳前 **100% 等价** |

**理由**：最小 diff、可灰度、失败时可一键回退 legacy。

---

### D2 · 配置与 schema 增量

| 项 | 决定 |
|----|------|
| **config** | `layout.scoring.*`（enabled、weights、beam_width、max_screens_per_chapter） |
| **config** | `layout.feedback.*`（enabled、log_path） |
| **config** | `curate.arc_mode: legacy \| v2_five_beat`（默认 legacy） |
| **trip.json** | 可选 `curation.layoutDecisionLog`、`curation.layoutMetrics`（P0 占位写入） |
| **开关默认** | 全部新能力 **关闭** |

---

### D3 · 降级护栏（degradation guard）

当以下任一成立时，**强制走 legacy**，即使 `scoring.enabled=true`：

| 条件 | 阈值（可配置） |
|------|----------------|
| 可排版照片数 | `< layout.scoring.min_layout_eligible`（默认 3） |
| 横竖比种类 | `< 2` 且无 mosaic 候选 |
| 用户已 lock structure | `pipeline.status >= structure_locked` 且未 `--force-relayout` |

写入 `curation.degradationReason` 供调试。

---

### D4 · 灰度四阶段

| 阶段 | 内容 | 退出条件 |
|------|------|----------|
| **0** | ADR + 黄金样本 + P0 骨架（本 ADR） | pytest 绿 |
| **1** | `scoring.enabled` 仅 `aspect_match=1.0`，验证与 legacy 等价 | 黄金 diff=0 ✅ |
| **2** | 开启 beam + 多信号权重；主观盲评 ≥ baseline | 客观对比已跑通；盲评待填 |
| **3a** | 自适应叙事弧、beam 护栏、亮度/主题 run、feedback 去噪 | pytest 绿 ✅ |
| **3b** | dominantTone + meanLuma ingest、ΔE spread | ingest + backfill ✅ |
| **3b+** | salientBox（人脸）、focal 贴边约束、mosaic/no_mosaic 候选 | 骨架 ✅ |
| **3c** | 群体 g1 反馈、LightGBM 离线调权 | 待 sign-off |

---

### D5 · 测试策略

| 项 | 决定 |
|----|------|
| **黄金样本** | `tests/_golden/` 冻结 mini trip 的 screen pattern 序列 |
| **等价断言** | legacy ≡ scoring(aspect_only)；enabled 全权重时允许 diff 但需记录 |
| **不依赖** | 完整 linzhi/maomi 资产入库（体积过大）；合成 mini fixture 代表 portrait-heavy / mixed |

---

## 后果

### 正面

- 默认用户零感知；开发可按阶段打开 V2。  
- 决策可审计（decision_log、metrics）。  
- 与现有 mobile / web dual render 兼容。

### 负面 / 代价

- 双路径维护成本（legacy + search 包裹）直至阶段 3 稳定。  
- schema 字段增多，需文档与 validate 容忍可选字段。

---

## 未决（P1+）

- CLIP / VLM 语义分接入 ingest tags  
- 同一人跨图聚类（当前仅 hasFace + focalPoint）  
- G1 编辑距离自动调权（`feedback.py` 占位）
