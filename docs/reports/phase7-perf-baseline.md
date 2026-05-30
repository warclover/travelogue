# Phase 7 · 性能基线对比报告（P6 vs P7）

| 属性 | 内容 |
|------|------|
| **阶段** | P7-Perf |
| **关联 PRD** | [PRD-PHASE7.md](../PRD-PHASE7.md) |
| **机器记录** | [phase7-perf-eval.json](../acceptance-records/phase7-perf-eval.json) |
| **数据集版本** | `benchmark-p7-v0.1`（待填） |
| **评测日期** | 2026-05-30 |

---

## 1. 对比条件

| 项 | P6 基线 | P7 候选 |
|----|---------|---------|
| commit | — | — |
| config | Phase 6 默认 | [config-phase7.example.yaml](../config-phase7.example.yaml) |
| 设备档 | S2 | S2 |
| 照片数 | 250 · vision on | 同左 |
| CLIP cache | 冷 / 热（分别记录） | 同左 |

---

## 2. 端到端与分项耗时

| 指标 | P6 (ms) | P7 (ms) | 变化 | 目标 | 达标 |
|------|---------|---------|------|------|------|
| `studio_e2e_250` | — | 11940 | — | −30% | ◑ |
| `studio_e2e_250_p95` | — | — | — | −25%，且 `p95<=p50*1.6` | ☐ |
| `ingest_time_250` | — | 11917 | — | −25% | ◑ |
| `clip_embed_time_250` | — | 2 | — | −40% | ◑ |
| `clip_embed_time_250_p95` | — | — | — | −30%，且 `p95<=p50*1.8` | ☐ |
| `clip_embed_time_incr_10pct` | — | — | — | −60% | ☐ |
| `clip_embed_time_incr_append_10pct` | — | — | — | −60% | ☐ |
| `clip_embed_time_incr_delete_10pct` | — | — | — | −60% | ☐ |
| `clip_embed_time_incr_replace_10pct` | — | — | — | −60% | ☐ |
| `curate_beam_time_250` | — | — | — | −30% | ☐ |
| `pipeline_time_1k` | — | — | — | ≤ P6+5% | ☐ |
| `peak_memory_1k` | — | — | — | < +10% | ☐ |
| `auto_batch_win_rate` | — | — | — | ≥95% | ☐ |
| `cache_rebuild_success_rate` | — | — | — | 100% | ☐ |
| `rollback_recovery_success` | — | 100% | — | 100% | ☑ |

---

## 3. 质量守护（不得退化）

| 指标 | P6 | P7 | 达标 |
|------|----|----|------|
| `cluster_noise_ratio` | — | — | ☐ |
| `event_boundary_f1` | — | — | ☐ |
| `layout_repeat_streak` | — | — | ☐ |
| `nr_p7_curate_hash_fixed` | — | — | ☐ |
| `nr_p7_cluster_hash_fixed` | — | — | ☐ |
| `nr_p7_curate_hash_real` | — | — | ☐ |
| `nr_p7_cluster_hash_real` | — | — | ☐ |

---

## 4. 结论

- **G0**：benchmark 已跑（12 张 × 2 次）
- **风险**：
- **建议**：

---

## 5. 变更记录

| 日期 | 说明 |
|------|------|
| 2026-05-30 | 模板创建 |
