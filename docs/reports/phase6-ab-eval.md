# Phase 6 · A/B 评测报告

| 属性 | 内容 |
|------|------|
| **阶段** | P6-Stability |
| **关联 PRD** | [PRD-PHASE6.md](../PRD-PHASE6.md) |
| **关联验收** | [ACCEPTANCE-PHASE6.md](../ACCEPTANCE-PHASE6.md) |
| **机器记录** | [phase6-quality-eval.json](../acceptance-records/phase6-quality-eval.json) |
| **灰度日志** | [phase6-rollout-log.json](../acceptance-records/phase6-rollout-log.json) |
| **数据集版本** | `benchmark-p6-v0.2-ci-fixtures` |
| **评测日期** | 2026-05-30 |

---

## 1. 评测范围与方法

### 1.1 对比组

| 组别 | 定义 | 说明 |
|------|------|------|
| **A (baseline)** | Phase 5 默认策略 | DBSCAN + fixed gap + 无 P6 布局/封面因子 |
| **B (candidate)** | Phase 6 新策略 | HDBSCAN + adaptive gap + MMR/约束 + 封面三分法 |

### 1.2 固定条件

- CI fixture 套件 `benchmark-p6-v0.2-ci-fixtures`
- commit `8ccb53a04bf6e9b11fabe54964a15e3f6f64f5f9`
- heuristic 向量聚类（无 trip 图片时）

---

## 2. 客观指标对比

| 指标 | A (P5) | B (P6) | 变化 | 是否达标 |
|------|--------|--------|------|----------|
| `cluster_noise_ratio` | 0.2609 | 0.1304 | −50% | ☑ |
| `event_boundary_f1` | 0.50 | 1.00 | +100% | ☑ |
| `layout_repeat_streak` | 12 | 2 | −83% | ☑ |
| `pipeline_time_1k` | 0.342s | 0.283s | −17% | ☑ |
| `peak_memory_1k` | 8.16 MB | 7.89 MB | −3% | ☑ |

---

## 3. 主观评测（封面与排版）

### 3.1 封面盲评

| 项 | 值 |
|----|----|
| 模式 | scoring_proxy（待人工复核） |
| 样本相册数 | 6 |
| P6 胜率 | **100%**（5/5 有效相册，scoring proxy） |
| 结论（阈值 ≥60%） | ☑ proxy 通过 |

人工记录模板：[phase6-cover-blind-review.json](../acceptance-records/phase6-cover-blind-review.json)

---

## 4. 业务指标观测（灰度期 · 待填）

| 指标 | 基线（P5） | 灰度期（P6） | 变化 | 是否达标 |
|------|------------|--------------|------|----------|
| 导出成功率 | 待填 | 待填 | 待填 | 待填 |
| 二次使用率 | 待填 | 待填 | 待填 | 待填 |
| 7 日复访率 | 待填 | 待填 | 待填 | 待填 |
| 分享转化率 | 待填 | 待填 | 待填 | 待填 |

---

## 5. 结论与建议

- **G0**：fixture 自动化 AC 全绿；封面盲评为 scoring proxy，发布前须人工盲评复核。
- **G1**：可进入 10% 灰度准备（见 [phase6-g1-rollout-checklist.md](phase6-g1-rollout-checklist.md)）。
- **风险**：真实 trip 数据集覆盖仍不足，灰度期须持续监控 BR 与导出成功率。

---

## 6. 变更记录

| 日期 | 说明 |
|------|------|
| 2026-05-30 | 模板创建 |
| 2026-05-30 | 填入 v0.2 fixture benchmark 结果 |
