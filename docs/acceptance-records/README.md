# 验收记录索引

| 属性 | 内容 |
|------|------|
| **权威入口** | [ACCEPTANCE.md](../ACCEPTANCE.md)（单轨） |
| **更新日期** | 2026-05-30 |

> JSON / Markdown 记录供 Phase 验收签字与脚本写入；**发布闸门以各 Phase ACCEPTANCE 文档为准**。

---

## Phase 7（性能专项 · 开发准备）

| 文件 | 用途 | 命令 / 说明 |
|------|------|-------------|
| [phase7-perf-eval.json](./phase7-perf-eval.json) | AC-P7 分阶段性能 + NR-P7 | `python scripts/phase7_pipeline_perf.py --write` |
| [phase7-rollout-log.json](./phase7-rollout-log.json) | G0-G3 灰度与回滚 | 手动记录 + 发布值班更新 |

---

## Phase 6（开发准备）

| 文件 | 用途 | 命令 / 说明 |
|------|------|-------------|
| [phase6-quality-eval.json](./phase6-quality-eval.json) | AC-P6 / BR-P6 指标记录 | `python scripts/phase6_metrics_baseline.py --summary --write` |
| [phase6-rollout-log.json](./phase6-rollout-log.json) | G0-G3 灰度与回滚日志 | 手动记录 + 发布值班更新 |

---

## Phase 5（当前生产闸门）

| 文件 | 用途 | 命令 / 说明 |
|------|------|-------------|
| [phase5-zero-edit.json](./phase5-zero-edit.json) | UX-P5-80-01 零编辑计时 | 手测填写 |
| [phase5-scroll-qualitative.json](./phase5-scroll-qualitative.json) | UX-P5-SCROLL-01 卷轴定性 | 3–5 人手测 |
| [phase5-layout-sprint.json](./phase5-layout-sprint.json) | P5-QS-01 排版冲刺 | `python scripts/phase5_layout_sprint.py --summary` |
| [phase5-peval.json](./phase5-peval.json) | P5-8.1 排版盲评 | `python scripts/phase5_blind_review.py <tripId>` |
| [phase5-webview-manual.json](./phase5-webview-manual.json) | P5-MP-2 本地 web-view 手测 | 见 [API-MINIAPP.md](../API-MINIAPP.md) §11 |

---

## Phase 4

| 文件 | 用途 |
|------|------|
| [phase4-intent.json](./phase4-intent.json) | P-EVAL · intent 盲评 + 关键词覆盖 |

---

## Phase 3

| 文件 | 用途 |
|------|------|
| [phase3-m12-0-spike.json](./phase3-m12-0-spike.json) | 聚类算法 Spike |
| [phase3-m12-5-cache.json](./phase3-m12-5-cache.json) | 增量 ingest cache |
| [phase3-m13-bench.json](./phase3-m13-bench.json) | P3-Full 性能 |
| [phase3-m13-ig2.json](./phase3-m13-ig2.json) | I-G2 排版质量 |
| [phase3-layout-acceptance.json](./phase3-layout-acceptance.json) | legacy vs beam 客观对比 |
| [phase3-blind-review.json](./phase3-blind-review.json) | Phase 3 盲评包索引 |
| [phase3-weight-experiment.json](./phase3-weight-experiment.json) | 权重实验 |

---

## Phase 2 / Phase 1

| 文件 | 用途 |
|------|------|
| [phase2-layout-compare.json](./phase2-layout-compare.json) | Phase 2 beam 对比 |
| [phase1-layout-equivalence.json](./phase1-layout-equivalence.json) | scoring 等价护栏 |

---

## 真实 trip 手测笔记

| 文件 | trip |
|------|------|
| [linzhi.md](./linzhi.md) | linzhi |
| [mao.md](./mao.md) | mao |
| [maomi.md](./maomi.md) | maomi |
