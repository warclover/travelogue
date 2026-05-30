# Travelogue · Phase 6 实施清单

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-PHASE6.md](./PRD-PHASE6.md) v0.6.2 |
| **关联子 PRD** | [PRD-PHASE6-ART-OPTIMIZATION.md](./PRD-PHASE6-ART-OPTIMIZATION.md) v0.1.0 |
| **周执行计划** | [phase6-week1-execution-plan.md](./reports/phase6-week1-execution-plan.md) |
| **代号** | P6-Stability · 智排稳态 |
| **更新日期** | 2026-05-30 |

> **状态图例**：☑ 已落地 · ◑ 部分 · ☐ 未开始  
> **优先级**：P0（稳定性必做） > P1（质量提升） > P2（联合优化）

---

## 里程碑总览

| 里程碑 | 主题 | 对应 PRD | 完成标志 | 状态 |
|--------|------|----------|----------|------|
| **M24** | 波次 1：聚类与分段核心升级 | §6.1 §6.2 §6.5 | AC-P6-01/02/03 基线通过 | ◑ |
| **M25** | 波次 2：封面与排版约束增强 | §6.3 §6.4 | AC-P6-04/05 通过 | ◑ |
| **M26** | 波次 3：联合优化与灰度放量 | §6.6 §14 | AC-P6-06/07/08 + G3 稳定 | ◑ |
| **M25-ART** | 艺术卷轴专项（子 PRD） | ART-A~E | ART-AC-01~05 达成 4/5 | ◑ |

---

## M24-A · 聚类升级（P6-A*）

| 任务 ID | PRD | 任务 | 文件/模块 | 状态 |
|---------|-----|------|-----------|------|
| M24-A-01 | P6-A1 | `scene_clusters` 默认切换 HDBSCAN | `travelogue/curation/scene_clusters.py` | ☑ |
| M24-A-02 | P6-A2 | 输出 cluster 置信度字段 | `travelogue/curation/scene_clusters.py` · `schemas/trip.schema.json` | ☑ |
| M24-A-03 | P6-A3 | 增加 DBSCAN 回退开关 | `config.yaml.example` · `travelogue/config.py` | ☑ |
| M24-A-04 | D-P6-01 | 默认策略文档化（含回退条件） | `docs/TECH-ARCHITECTURE.md` | ☑ |

---

## M24-B · 时间事件自适应（P6-B*）

| 任务 ID | PRD | 任务 | 文件/模块 | 状态 |
|---------|-----|------|-----------|------|
| M24-B-01 | P6-B1 | 新增 `gap_hours=auto` 阈值算法 | `travelogue/curation/geo_events.py` | ☑ |
| M24-B-02 | P6-B2 | 阈值异常 fail-open 回退 | 同上 | ☑ |
| M24-B-03 | P6-B3 | 事件边界评估脚本 | `scripts/phase6_event_boundary_eval.py` | ☑ |
| M24-B-04 | G-P6-02 | 写入 `thresholdHours` 到 trip | `travelogue/curation/clustering.py` | ☑ |

---

## M24-C · Heuristic 向量语义化（P6-E*）

| 任务 ID | PRD | 任务 | 文件/模块 | 状态 |
|---------|-----|------|-----------|------|
| M24-C-01 | P6-E1 | `tone_hash` → H/S 连续特征 | `travelogue/vision/clip_encoder.py` | ☑ |
| M24-C-02 | P6-E2 | `subject_hash` → one-hot/有序编码 | 同上 | ☑ |
| M24-C-03 | P6-E3 | 无 CLIP 场景回归测试 | `tests/test_phase6_heuristic_vector.py` | ☑ |

---

## M24-D · 指标基线与观测（PRD §4 §18）

| 任务 ID | PRD | 任务 | 文件/模块 | 状态 |
|---------|-----|------|-----------|------|
| M24-D-01 | G-P6-01~05 | 指标采集脚本（质量/性能） | `scripts/phase6_metrics_baseline.py` | ☑ |
| M24-D-02 | §18.1 | 最小指标输出到 records | `docs/acceptance-records/phase6-quality-eval.json` · `scripts/phase6_benchmark_run.py` | ☑ |
| M24-D-03 | §18.2 | 告警阈值配置化 | `travelogue/config.py` | ☑ |

---

## M25-A · 封面评分增强（P6-C*）

| 任务 ID | PRD | 任务 | 文件/模块 | 状态 |
|---------|-----|------|-----------|------|
| M25-A-01 | P6-C1 | 构图规则分（主体位置/三分法） | `travelogue/curation/curate_scoring.py` | ☑ |
| M25-A-02 | P6-C2 | 色彩丰富度因子 | `travelogue/media/color_metrics.py` | ☑ |
| M25-A-03 | P6-C3 | 封面 explain 可读输出 | `travelogue/curation/curate_scoring.py` · `curate.py` | ☑ |
| M25-A-04 | G-P6-03 | 盲评脚本与记录模板 | `scripts/phase6_cover_blind_review.py` | ☑ |

---

## M25-B · 布局节奏与多样性（P6-D*）

| 任务 ID | PRD | 任务 | 文件/模块 | 状态 |
|---------|-----|------|-----------|------|
| M25-B-01 | P6-D1 | `gravity_balance` 评分维度接入 | `travelogue/curation/layout_scoring.py` | ☑ |
| M25-B-02 | P6-D2 | longshot MMR 多样性选屏 | `travelogue/curation/longshot_filter.py` | ☑ |
| M25-B-03 | P6-D3 | 连续模板硬约束（rule gate） | `travelogue/curation/layout_constraints.py` | ☑ |
| M25-B-04 | G-P6-04 | 节奏相关指标计算 | `scripts/phase6_layout_rhythm_eval.py` | ☑ |

---

## M25-C · 艺术卷轴专项映射（ART-*）

| 任务 ID | 子 PRD | 任务 | 映射主任务 | 文件/模块 | 状态 |
|---------|--------|------|------------|-----------|------|
| M25-C-01 | ART-A1/A2 | Geo×Scene 子分段 + 断点 explain | M26-A-01 | `travelogue/curation/scene_subsegments.py` · `chapter_explain.py` | ☑ |
| M25-C-02 | ART-B1/B2/B3 | 全局节奏：重心分 + 连续模板约束 + hero/grid 交替 | M25-B-01/03 | `layout_scoring.py` · `layout_constraints.py` | ☑ |
| M25-C-03 | ART-C1/C2/C3 | 封面/章首审美 + explain | M25-A-01/02/03 | `curate_scoring.py` · `chapter_explain.py` | ☑ |
| M25-C-04 | ART-D1/D2 | MMR 多样性与去同质化 | M25-B-02 | `longshot_filter.py` | ☑ |
| M25-C-05 | ART-E1/E2 | 呼吸屏“叙事弧驱动”插入与突兀度优化 | M26-A-01 | `breath_pauses.py` · `curate.py` | ☑ |

---

## M26-A · 联合优化试点（P6-F*）

| 任务 ID | PRD | 任务 | 文件/模块 | 状态 |
|---------|-----|------|-----------|------|
| M26-A-01 | P6-F1 | Geo 段内 Scene-aware 子分段 | `travelogue/curation/scene_subsegments.py` · `clustering.py` | ☑ |
| M26-A-02 | P6-F2 | 增量重聚类三档策略 | `travelogue/vision/cache.py` | ☑ |
| M26-A-03 | P6-F3 | 灰度与回滚策略文档联动 | `phase6_rollout.py` · `scripts/phase6_apply_p5_rollback.py` | ☑ |

---

## M26-B · 合规与治理（PRD §15 §16 §19 §20）

| 任务 ID | PRD | 任务 | 文件/模块 | 状态 |
|---------|-----|------|-----------|------|
| M26-B-01 | §15 | benchmark 数据集版本化清单 | `docs/reports/phase6-benchmark-catalog.md` | ☑ |
| M26-B-02 | §16 | License BOM 台账 | `docs/reports/phase6-license-bom.md` | ☑ |
| M26-B-03 | §19 | RACI 落地到里程碑 owner | 本文件 + 周会模板 | ☑ |
| M26-B-04 | §20 | T+7 / T+30 复盘模板创建 | `docs/reports/phase6-retro-template.md` | ☑ |

---

## 建议执行顺序（4 周）

### Week 1（稳定性优先 · P0）

```
M24-A-01/02/03
M24-B-01/02
M24-C-01/02
M24-D-01
```

### Week 2（评估闭环 · P0/P1）

```
M24-B-03/04
M24-C-03
M24-D-02/03
M25-A-01
```

### Week 3（质量提升 · P1）

```
M25-A-02/03/04
M25-B-01/02/03/04
M25-C-02/03/04
```

### Week 4（灰度放量 · P2）

```
M26-A-01/02/03
M26-B-01/02/03/04
M25-C-01/05
```

---

## 发布闸门（实现视角）

| 类别 | 必达项 |
|------|--------|
| **算法质量** | AC-P6-01~05 |
| **性能稳定** | AC-P6-06 |
| **可回滚性** | AC-P6-07 |
| **合规治理** | AC-P6-08 + License BOM |
| **业务不退化** | BR-P6 至少 2 项改善，且无关键退化 |
| **艺术专项** | ART-AC-01~05 达成至少 4 项，且不破坏 AC-P6 |

---

## 配套记录文件

| 文件 | 用途 |
|------|------|
| `docs/acceptance-records/phase6-quality-eval.json` | 质量/性能评测结果 |
| `docs/acceptance-records/phase6-rollout-log.json` | 灰度与回滚日志 |
| `scripts/phase6_pipeline_perf.py` | AC-P6-06 性能 proxy |
| `scripts/phase6_cover_blind_review.py` | AC-P6-04 封面盲评 |
| `scripts/phase6_rollout_advance.py` | G0→G1 灰度门控 |
| `docs/reports/phase6-g1-rollout-checklist.md` | G1 10% 预检清单 |
| `docs/reports/phase6-benchmark-catalog.md` | Benchmark 数据集台账 |
| `docs/reports/phase6-ab-eval.md` | A/B 评测报告 |
| `docs/reports/phase6-license-bom.md` | 许可与替代台账 |

---

## 变更记录

| 日期 | 说明 |
|------|------|
| 2026-05-30 | 初稿：M24-M26 对齐 PRD v0.6.1，含实施顺序、闸门与治理项 |
| 2026-05-30 | 增补：对齐艺术子 PRD（ART-A~E）任务映射与发布门槛 |
| 2026-05-30 | 新增 Week 1 执行计划文档（M24 到天级拆解） |
| 2026-05-30 | M24-A/B/C 代码落地；29 项单测通过；TECH-ARCHITECTURE §16 文档化 |
| 2026-05-30 | M24-D-03 告警配置；fixture 噪声基线写入；M25-A 封面评分/explain 落地 |
| 2026-05-30 | M25-B 布局节奏：gravity_balance、MMR longshot、连续模板约束、节奏评测脚本 |
| 2026-05-30 | M26 编码完成：scene 子分段、cache prune、叙事弧呼吸屏、P5 回滚脚本；50 项 P6 相关单测通过 |
| 2026-05-30 | G0 benchmark 首轮：`phase6_benchmark_run.py` 写入 quality-eval / rollout-log；台账与 License BOM 填数 |
| 2026-05-30 | v0.2：adaptive gap 修复、gap-edge/cluster-noise fixtures、合成布局/性能 proxy；G0 自动化 AC 全绿（除盲评） |
| 2026-05-30 | AC-P6-04 scoring proxy + 盲评模板；G1 rollout 准备脚本与 A/B 报告填数 |

