# Travelogue · Phase 12 实施任务清单

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-PHASE12.md](./PRD-PHASE12.md) v0.12.1 |
| **里程碑** | M40 · 静默自治选片增强 |
| **状态** | In Progress |
| **更新** | 2026-06-03 |

---

## 波次总览

| 波次 | 目标 | 出口 |
|------|------|------|
| **M40-W1** | 分支化评分骨架 + 人像轻量信号 + 组内择优统一 | 可在 CPU-only 跑通且回退稳定 |
| **M40-W2** | 11 类 L1 映射 + `category_coherence` 评分上线 | 编排评分可观测，回归通过 |
| **M40-W3（可选）** | 候选模型试点与参数校准 | 输出对比报告，不阻塞主线 |

---

## M40-W1 · 核心落地（P0）

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| M40-1a | 新增分支路由参数与默认值（face_ratio 阈值、Top-K/threshold） | `travelogue/config.py` `config.yaml.example` | ◑ |
| M40-1b | `photo_cull` 增加 portrait/landscape/gray 分流与统一打分入口 | `travelogue/curation/photo_cull.py` | ☑ |
| M40-1c | 人像轻量信号接入（face_ratio、face sharpness、曝光） | `travelogue/media/ingest.py` `travelogue/curation/photo_cull.py` | ☑ |
| M40-1d | 统一组内择优与 deterministic tie-break 链 | `travelogue/curation/photo_cull.py` | ☑ |
| M40-1e | L1/L2/L3 回退分级打点（telemetry 字段） | `travelogue/curation/photo_cull.py` `travelogue/web/studio_telemetry.py` `travelogue/types/trip_telemetry.py` | ◑ |
| M40-1f | CPU-only 时延采样与预算守护（P50/P95） | `travelogue/media/ingest.py` `travelogue/curation/photo_cull.py` | ◑ |
| M40-1g | 单测：分流、灰区仲裁、组内择优、回退语义 | `tests/test_photo_cull.py` `tests/test_photo_cull_ml.py` | ◑ |

---

## M40-W2 · 语义与编排评分（P0）

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| M40-2a | 11 类 L1 映射规则（由 `subjectClass + tags` 产出 `semanticTag.category`） | `travelogue/curation/subject_tagging.py` | ☑ |
| M40-2b | 必要时补充 CLIP prompt/标签映射（保持可回退） | `travelogue/vision/clip_encoder.py` | ☐ |
| M40-2c | 引入 `category_coherence` 评分项与权重配置 | `travelogue/curation/layout_scoring.py` `travelogue/config.py` | ☑ |
| M40-2d | 将 coherence 纳入 chapter explain/metrics 可观测项 | `travelogue/curation/chapter_explain.py` `travelogue/curation/layout_metrics.py` | ◑ |
| M40-2e | 回归：food grid、subject bridge、layout search 不回退 | `tests/test_food_grid.py` `tests/test_subject_tagging_bridge.py` `tests/test_layout_search.py` | ◑ |
| M40-2f | 验证 GPU 可用场景时延预算并记录 | `scripts/`（新增 phase12 验证脚本） | ☐ |

---

## M40-W3 · 试点（不阻塞）

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| M40-3a | 候选人像模型试点（CR-FIQA / DN-PIQA 二选一） | `travelogue/curation/photo_cull_ml.py`（试验分支） | ☐ |
| M40-3b | 候选风光模型离线对照（AestheticSigLIP vs `topiq_nr`） | `scripts/phase12_model_benchmark.py` | ☐ |
| M40-3c | 输出模型对照报告（准确率/时延/回退率） | `docs/reports/phase12-model-benchmark.md` | ☐ |
| M40-3d | 参数校准并冻结默认值（一周冻结窗口） | `config.yaml.example` `docs/PRD-PHASE12.md` | ☐ |

---

## 文件映射（主路径）

| 模块 | 关键改动 |
|------|----------|
| `photo_cull.py` | 分支化评分总线、阈值+Top-K顺序、组内择优、回退分级 |
| `ingest.py` | 透传人像轻量信号、时延采样 |
| `subject_tagging.py` | 11 类 L1 映射与回退 |
| `layout_scoring.py` | `category_coherence` 评分维度 |
| `config.py` | 新增参数与默认值、权重治理 |
| `studio_telemetry.py` | L1/L2/L3 回退率与分支覆盖率打点 |

---

## 已落地观测字段（截至 2026-06-03）

- `trip.curation.cullSummary`
  - `mlFallbackRateL1`
  - `branchFallbackRateL2`
  - `branchFallbackByReasonL2`
  - `failOpenRateL3`
  - `branchPortraitRatio` / `branchLandscapeRatio` / `branchGrayRatio`
  - `cpuMs`
- `ingest_stats`
  - `cull_l1_ml_fallback_rate`
  - `cull_l2_branch_fallback_rate`
  - `cull_l3_fail_open_rate`
  - `cull_l2_<reason>`（如 `cull_l2_gray_zone`）
- 验收记录链路
  - `scripts/phase9_golden_cull_signoff.py` 已写出 L1/L2/L3 与分支比率
  - `scripts/phase9_eval_baseline.py` 已聚合 `l1_ml_fallback_rate` / `l2_branch_fallback_rate` / `l2_branch_fallback_by_reason` / `l3_fail_open_rate`
  - `docs/acceptance-records/phase9-eval-baseline.json` 已按新 schema 重生成

---

## 测试与验收清单（建议命令）

```bash
pytest tests/test_photo_cull.py tests/test_photo_cull_ml.py -v
pytest tests/test_subject_tagging_bridge.py tests/test_food_grid.py -v
pytest tests/test_layout_scoring.py tests/test_layout_search.py -v
pytest tests/test_curate.py -v --timeout=120
python -m travelogue demo verify
```

可选新增脚本：

```bash
python scripts/phase12_eval_baseline.py --write docs/acceptance-records/phase12-eval-baseline.json
python scripts/phase12_latency_profile.py --write docs/acceptance-records/phase12-latency.json
```

发布闸门模板：

- [`reports/phase12-1-release-gate-checklist.md`](./reports/phase12-1-release-gate-checklist.md)

---

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| 人像信号噪声导致误杀 | 低权重 + 灰区保留 + 组内择优 |
| 语义映射抖动影响 coherence | 低置信回退 `general` + 权重保守 |
| 时延超预算 | 优先降低模型调用比例，保留稳定性 |
| 个人开发者维护压力 | W1/W2 先闭环，W3 全部可选 |

---

## 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.12.0 | 2026-06-03 | 初稿：按 PRD-PHASE12 v0.12.1 拆分 M40-W1/W2/W3 可执行任务 |
| v0.12.1 | 2026-06-03 | W1/W2 部分完成：分支评分、L1/L2/L3 指标、`category_coherence`、验收汇总字段已落地 |

