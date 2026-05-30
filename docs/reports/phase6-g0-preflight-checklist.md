# Phase 6 · G0 预检清单（CI Fixture Suite）

| 属性 | 内容 |
|------|------|
| **阶段** | P6-Stability · G0 离线评测 |
| **关联 PRD** | [PRD-PHASE6.md](../PRD-PHASE6.md) §14 |
| **更新日期** | 2026-05-30 |
| **执行脚本** | `scripts/phase6_benchmark_run.py --write` |

---

## 1. 环境与数据

| # | 检查项 | 期望 | 状态 |
|---|--------|------|------|
| 1 | Python ≥ 3.11 | 通过 | ☑ |
| 2 | `vision` extra（sklearn/numpy） | 可 import | ☑ |
| 3 | CI clustering fixtures 齐全 | 4 套 golden | ☑ |
| 4 | 布局 rhythm fixture | `schemas/fixtures/trip.linzhi_screens.json` | ☑ |
| 5 | 验收记录可写 | `docs/acceptance-records/` | ☑ |

---

## 2. 自动化 AC（G0 必需）

| AC | 检查 | 命令 / 来源 | 状态 |
|----|------|-------------|------|
| AC-P6-01 | HDBSCAN 四套 fixture 稳定跑通 | `phase6_benchmark_run.py` | ☑ |
| AC-P6-02 | 聚类噪声 DBSCAN→HDBSCAN 对比 | `golden-cluster-noise` | ☑ 50% 降幅 |
| AC-P6-03 | 事件边界 F1 proxy 提升 ≥10% | `golden-gap-edge` + 加权套件 | ☑ 100% lift |
| AC-P6-04 | 封面盲评 winrate ≥60% | `phase6_cover_blind_review.py --score-proxy` | ☑ proxy 100%（5 相册，待人工复核） |
| AC-P6-05 | layout repeat streak 降幅 | 合成高重复 + linzhi fixture | ☑ 83% 降幅 |
| AC-P6-06 | 1k 管线耗时/内存回归 | `phase6_pipeline_perf.py` | ☑ 无回归 |
| AC-P6-07 | P5 回滚 drill | `phase6_apply_p5_rollback.py --dry-run` | ☑ |
| AC-P6-08 | License BOM 完整 | `phase6-license-bom.md` | ☑ |

---

## 3. 记录与门禁

| # | 产出 | 路径 | 状态 |
|---|------|------|------|
| 1 | 质量 KPI 记录 | `docs/acceptance-records/phase6-quality-eval.json` | ☑ |
| 2 | 灰度日志首条 | `docs/acceptance-records/phase6-rollout-log.json` | ☑ |
| 3 | Benchmark 台账 | `docs/reports/phase6-benchmark-catalog.md` | ☑ |
| 4 | Rollup l0/l1 | quality-eval `rollup` | 见 JSON |

---

## 4. G0 结论

- **fixture 自动化**：G0 自动化 AC 已通过；封面为 scoring proxy，发布签字前须人工盲评。
- **G1**：`rollout-log` 状态 `ready_for_10pct`，见 G1 检查单。

---

## 5. 签字（模板）

| 角色 | 负责人 | 结论 | 日期 |
|------|--------|------|------|
| 算法 | 待填 | 通过 / 有条件通过 | 待填 |
| 工程 | 待填 | 通过 / 有条件通过 | 待填 |
| QA | 待填 | 通过 / 有条件通过 | 待填 |
