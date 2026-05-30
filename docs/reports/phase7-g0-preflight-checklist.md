# Phase 7 · G0 离线预检清单

| 属性 | 内容 |
|------|------|
| **阶段** | G0（离线 benchmark + NR-P7） |
| **关联 PRD** | [PRD-PHASE7.md](../PRD-PHASE7.md) §13.1 |
| **关联验收** | [ACCEPTANCE-PHASE7.md](../ACCEPTANCE-PHASE7.md) |
| **更新日期** | 2026-05-30 |

---

## 1. 环境准备

| # | 项 | 通过 |
|---|-----|------|
| 1 | Phase 6 L0 验收已通过 | ☐ |
| 2 | CLIP 权重已缓存（非首次下载场景） | ☐ |
| 3 | 设备档位已登记（S1/S2/S3） | ☐ |
| 4 | `docs/config-phase7.example.yaml` 快照已固定 | ☐ |
| 5 | P6 基线已写入 `phase7-perf-eval.json` · `baseline` | ☐ |

---

## 2. 自动化 AC

| # | 命令 / 检查 | 通过 |
|---|-------------|------|
| 1 | `python scripts/phase7_pipeline_perf.py` | ☐ |
| 2 | AC-P7-01/02/03 数值达标（含 p95 门槛） | ☐ |
| 3 | AC-P7-05 fixture 代理通过 | ☐ |
| 4 | `python scripts/phase7_equivalence_check.py` | ☐ |
| 5 | AC-P7-04/06 NR-P7 双门槛通过（fixed=100%，real>=95%） | ☐ |
| 6 | AC-P7-10 Auto batch 在 S1/S2/S3 不劣化 | ☐ |
| 7 | AC-P7-11 cache ABI 失配自动重建通过 | ☐ |
| 8 | AC-P7-12 故障注入恢复通过 | ☐ |
| 9 | `pytest tests/test_phase7_* tests/test_layout_golden.py -q` | ☐ |
| 10 | AC-P7-09 Phase 6 质量 KPI 无退化 | ☐ |

---

## 3. 回滚演练

| # | 项 | 通过 |
|---|-----|------|
| 1 | `vision.batch_size=0` 回退验证 | ☐ |
| 2 | `ingest.webp_method=6` 回退验证 | ☐ |
| 3 | `pipeline.parallel_embed=false` | ☐ |
| 4 | 全 flag off 与 P6 hash 一致（AC-P7-08） | ☐ |
| 5 | 运行 `python scripts/phase7_verify_rollback.py` 通过 | ☐ |

---

## 4. 文档与记录

| # | 文件 | 通过 |
|---|------|------|
| 1 | `phase7-perf-eval.json` 已填 | ☐ |
| 2 | `phase7-perf-baseline.md` P6 vs P7 对比 | ☐ |
| 3 | IMPLEMENTATION-PHASE7 里程碑状态更新 | ☐ |

---

## 5. G0 结论

| 结论 | 签字 | 日期 |
|------|------|------|
| ☐ 通过，可进入 G1（仅 P7-A + P7-B） |  |  |
| ☐ 有条件通过（列豁免项） |  |  |
| ☐ 不通过 |  |  |

**豁免项（如有）**：

---

## 6. 变更记录

| 日期 | 说明 |
|------|------|
| 2026-05-30 | 初稿 |
