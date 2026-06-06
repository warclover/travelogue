# Travelogue · Phase 7 实施清单

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-PHASE7.md](./PRD-PHASE7.md) v0.7.0 |
| **关联验收** | [ACCEPTANCE-PHASE7.md](./ACCEPTANCE-PHASE7.md) |
| **前置 Phase** | [IMPLEMENTATION-PHASE6.md](./IMPLEMENTATION-PHASE6.md) · G0 通过 |
| **代号** | P7-Perf · 极速管线 |
| **更新日期** | 2026-05-30 |

> **状态图例**：☑ 已落地 · ◑ 部分 · ☐ 未开始  
> **优先级**：P0（性能必做 + NR 闸门） > P1（并行/预热） > P2（layout 增量 · ONNX spike）

---

## 里程碑总览

| 里程碑 | 主题 | 对应 PRD | 完成标志 | 状态 |
|--------|------|----------|----------|------|
| **M27** | 波次 1：CLIP batch + Ingest 微优化 + Telemetry | §6.1 §6.2 §6.5 | AC-P7-02/07 + NR-P7 基线 CI | ☑ |
| **M28** | 波次 2：流水线并行 + CLIP 预热 + 稳定性增强 | §6.3 §6.7 | AC-P7-01/03/08/10/11 | ☑ |
| **M29** | 波次 3：Layout 等价加速 + 放量 | §6.4 §13 | AC-P7-04~06/09/12 + G1 就绪 | ☑ |
| **M29-OPT** | 可选 Spike：ONNX | §6.6 | 报告完成；不阻塞 G3 | ☐ |

---

## M27-A · CLIP 推理加速（P7-A*）

| 任务 ID | PRD | 任务 | 文件/模块 | 状态 |
|---------|-----|------|-----------|------|
| M27-A-01 | P7-A1 | `_embed_clip` batch inference + `vision.batch_size` | `travelogue/vision/clip_encoder.py` · `config.py` | ☑ |
| M27-A-02 | P7-A2 | `ClipEncoder` 进程级单例 + `vision.session_singleton` | `clip_encoder.py` · `clustering.py` | ☑ |
| M27-A-03 | P7-A5 | batch OOM/异常 → 逐张 fallback + decision_log | `clip_encoder.py` | ☑ |
| M27-A-04 | P7-A6 | 增量 embed 对 `plan.new_ids` 走 batch | `vision/cache.py` | ☑ |
| M27-A-05 | D-P7-01 | batch vs 逐张 subjectClass 一致 pytest | `tests/test_phase7_clip_batch.py` | ☑ |
| M27-A-06 | P7-A3 | I/O 预取（decode 下一 batch 线程） | `clip_encoder.py` | ☑ |
| M27-A-07 | P7-A4 | 优先 web 800px WebP + 余弦距门禁 | `clip_encoder.py` · `_resolve_asset_path` | ☑ |

---

## M27-B · Ingest 微优化（P7-B*）

| 任务 ID | PRD | 任务 | 文件/模块 | 状态 |
|---------|-----|------|-----------|------|
| M27-B-01 | P7-B1 | Haar `CascadeClassifier` lazy 单例 | `travelogue/media/subject_detect.py` | ☑ |
| M27-B-02 | P7-B2 | 共享缩略图 `meanLuma` + `dominantTone` | `color_metrics.py` · `ingest.py` | ☑ |
| M27-B-03 | P7-B3 | WebP `method=4` 默认 + `ingest.webp_method` | `image_ops.py` · `config.py` · `config.yaml.example` | ☑ |
| M27-B-04 | P7-B5 | `ingestStats.elapsedMs` 分阶段计时 | `ingest.py` | ☑ |
| M27-B-05 | NR-P7 | ingest 人脸/色彩 golden 回归 | `tests/test_phase7_ingest_micro.py` | ☑ |

---

## M27-C · 性能基准与 NR 闸门（P7-E*）

| 任务 ID | PRD | 任务 | 文件/模块 | 状态 |
|---------|-----|------|-----------|------|
| M27-C-01 | P7-E1 | 分阶段 benchmark 脚本 | `scripts/phase7_pipeline_perf.py` · `scripts/phase7_benchmark_run.py` | ☑ |
| M27-C-02 | P7-E2 | perf eval 记录 schema + 模板 | `docs/acceptance-records/phase7-perf-eval.json` | ☑ |
| M27-C-03 | P7-E3 | NR-P7 CI 套件 | `tests/test_phase7_equivalence.py` | ☑ |
| M27-C-04 | P7-E3 | 离线等价检查 CLI | `scripts/phase7_equivalence_check.py` | ☑ |
| M27-C-05 | G-P7-07 | `trip.pipeline.timings` 写入 | `studio_pipeline.py` · `orchestrator/run.py` | ☑ |
| M27-C-06 | §4.1 | P6 基线登记（同机同 config） | `docs/reports/phase7-perf-baseline.md` · `scripts/phase7_benchmark_run.py` · `scripts/phase7_nr_collect.py` | ☑ |
| M27-C-07 | §7.2 | `embedStats` 写入 clustering 层 | `clustering.py` | ☑ |
| M27-C-08 | §4.1 | p95 指标采集与写入（e2e/clip） | `scripts/phase7_pipeline_perf.py` · `phase7-perf-eval.json` | ☑ |
| M27-C-09 | §12 | NR 双门槛输出（fixed=100%，real>=95%） | `scripts/phase7_equivalence_check.py` | ☑ |
| M27-C-10 | §8 | 一键门禁编排（perf + NR） | `scripts/phase7_gate_run.py` | ☑ |

---

## M28-A · 流水线并行与预热（P7-C*）

| 任务 ID | PRD | 任务 | 文件/模块 | 状态 |
|---------|-----|------|-----------|------|
| M28-A-01 | P7-C4 | embedding cache 写入锁 / 串行化 | `vision/cache.py` | ☑ |
| M28-A-02 | P7-C1 | ingest 每 N 张触发后台 embed | `studio_pipeline.py` · `ingest.py` hook | ☑ |
| M28-A-03 | P7-C2 | 选文件夹后 CLIP preload 线程 | `studio_pipeline.py` · `web/studio_stages.py` | ☑ |
| M28-A-04 | P7-C3 | clustering 阶段 skip 已完成 embed | `clustering.py` | ☑ |
| M28-A-05 | G-P7-08 | preload 失败 silent + stageHint | `studio_pipeline.py` | ☑ |
| M28-A-06 | — | 并行路径集成测试（无 corrupt cache） | `tests/test_phase7_parallel_embed.py` | ☑ |
| M28-A-07 | P7-C5 | 写入事务不变式（tmp+rename + manifest version + 批末提交） | `vision/cache.py` · `clustering.py` | ☑ |

---

## M28-B · 稳定性与自适应增强（P7-G*）

| 任务 ID | PRD | 任务 | 文件/模块 | 状态 |
|---------|-----|------|-----------|------|
| M28-B-01 | P7-G1 | Auto batch 探测（样本探测 + 设备回落） | `clip_encoder.py` · `config.py` | ☑ |
| M28-B-02 | P7-G2 | `deterministic_strict` 强确定性模式 | `clustering.py` · `layout_search.py` | ☑ |
| M28-B-03 | P7-G3 | cache ABI version 与 config 指纹校验 | `vision/cache.py` | ☑ |
| M28-B-04 | P7-G4 | 双文件提交协议（embeddings/manifest 原子切换） | `vision/cache.py` | ☑ |
| M28-B-05 | P7-G5 | 动态退化保护（慢批次/OOM 自动降级） | `clip_encoder.py` · `studio_pipeline.py` | ☑ |
| M28-B-06 | P7-G6 | append/delete/replace 三场景增量测试 | `tests/test_phase7_incremental_modes.py` | ☑ |

---

## M29-A · Layout Beam 等价加速（P7-D*）

| 任务 ID | PRD | 任务 | 文件/模块 | 状态 |
|---------|-----|------|-----------|------|
| M29-A-01 | P7-D1 | 签名相同跳过 `score_screen_plan` | `layout_search.py` | ☑ |
| M29-A-02 | P7-D4 | SearchBudget 生成 vs 评分离账 | `layout_candidates.py` · `search_budget.py` | ☑ |
| M29-A-03 | P7-D2 | 增量评分（config 默认 off） | `layout_scoring.py` · `layout_search.py` | ☑ |
| M29-A-04 | P7-D3 | 局部 copy 替代全量 `deepcopy(chapters)` | `layout_search.py` | ☑ |
| M29-A-05 | NR-P7 | layout golden 双跑一致 | `tests/test_layout_golden.py` 扩展 | ☑ |

---

## M29-B · 灰度、回滚与文档（PRD §11 §13）

| 任务 ID | PRD | 任务 | 文件/模块 | 状态 |
|---------|-----|------|-----------|------|
| M29-B-01 | §13 | P7 fast-path config 示例 | `docs/config-phase7.example.yaml` | ☑ |
| M29-B-02 | §13 | rollout / rollback 日志模板 | `docs/acceptance-records/phase7-rollout-log.json` | ☑ |
| M29-B-03 | §13 | G0→G1 预检清单 | `docs/reports/phase7-g0-preflight-checklist.md` | ☑ |
| M29-B-04 | AC-P7-08 | 逐项关闭 fast-path 回退测试 | `tests/test_phase7_rollback_flags.py` | ☑ |
| M29-B-05 | §14 | TECH-ARCHITECTURE 性能章节更新 | `docs/TECH-ARCHITECTURE.md` | ☑ |
| M29-B-06 | §13.3 | 一键回滚校验脚本 | `scripts/phase7_verify_rollback.py` | ☑ |

---

## M29-OPT · ONNX Spike（P7-F* · 可选）

| 任务 ID | PRD | 任务 | 文件/模块 | 状态 |
|---------|-----|------|-----------|------|
| M29-OPT-01 | P7-F1 | PyTorch vs ONNX 250 张 benchmark 报告 | `docs/reports/phase7-onnx-spike.md` | ☐ |
| M29-OPT-02 | P7-F2 | ONNX 确定性双跑 | `scripts/phase7_onnx_compare.py` | ☐ |
| M29-OPT-03 | P7-F3 | License BOM 增量条目 | `docs/reports/phase6-license-bom.md` | ☐ |

---

## 建议执行顺序（3 周）

### Week 1（W1 · P0 核心）

```
M27-C-06          # 先登记 P6 基线（同机）
M27-B-01/02/03    # ingest 快赢
M27-A-01/02/03    # CLIP batch + 单例
M27-A-05          # subjectClass 一致测试
M27-C-01/03/04    # benchmark + NR CI 骨架
M27-C-08/09       # p95 与 NR 双门槛
```

**Week 1 出口**：`phase7_pipeline_perf.py` 可跑；NR-P7 CI 绿；ingest/clip 分项有 −15% 以上信号。

### Week 2（W2 · 并行 + 增量）

```
M27-A-04/06/07    # 增量 batch + web derivative + 预取
M27-B-04/05
M27-C-02/05/07    # timings + records
M28-A-01~07       # 并行 embed + preload + 事务不变式
M28-B-01/02/03    # auto-batch + strict deterministic + ABI
```

**Week 2 出口**：AC-P7-01/03 达标或差距 documented；parallel_embed 集成测试绿。

### Week 3（W3 · Layout + 放量准备）

```
M29-A-01/02/05    # layout 短路 + budget 修正
M29-A-03/04       # 可选：增量评分 / copy 优化
M29-B-01~06
M28-B-04/05/06    # 原子提交 + 动态退化 + 增量三模式
M29-OPT-*         # 并行 spike，不阻塞
```

**Week 3 出口**：AC-P7-04~12 全绿；G0 预检清单签字。

---

## 配置落地清单

| 配置键 | 默认（P7） | P6 回退值 | 任务 |
|--------|------------|-----------|------|
| `vision.batch_size` | `16` | `0` | M27-A-01 |
| `vision.session_singleton` | `true` | `false` | M27-A-02 |
| `vision.prefer_web_derivative` | `true` | `false` | M27-A-07 |
| `vision.preload_on_folder_pick` | `true` | `false` | M28-A-03 |
| `ingest.webp_method` | `4` | `6` | M27-B-03 |
| `ingest.shared_color_thumb_px` | `32` | — | M27-B-02 |
| `pipeline.parallel_embed` | `true`（G2 已放量） | `false` | M28-A-02 |
| `layout_scoring.skip_duplicate_signatures` | `true` | `false` | M29-A-01 |
| `layout_scoring.incremental` | `false` | `false` | M29-A-03 |
| `vision.batch_auto_tune` | `true` | `false` | M28-B-01 |
| `vision.batch_auto_tune_samples` | `8` | — | M28-B-01 |
| `clustering.cache_abi_version` | `"v1"` | — | M28-B-03 |
| `clustering.cache_config_fingerprint` | `auto` | — | M28-B-03 |
| `clustering.deterministic_strict` | `false` | `false` | M28-B-02 |
| `vision.dynamic_backoff` | `true` | `false` | M28-B-05 |

---

## 发布闸门（实现视角）

| 类别 | 必达项 |
|------|--------|
| **性能** | AC-P7-01/02/03 |
| **等价** | AC-P7-04/06 + NR-P7 双门槛（fixed=100%，real>=95%） |
| **内存/代理** | AC-P7-05 |
| **可观测** | AC-P7-07 |
| **可回滚** | AC-P7-08 |
| **质量不退化** | AC-P7-09（Phase 6 KPI） |
| **稳定性增强** | AC-P7-10/11/12 |
| **放量** | G0 全绿 → G1（仅 A+B）→ G2（含 C）→ G3 |

> **硬规则**：NR-P7 失败 **禁止** 合并 P0 fast-path 默认值变更。

---

## 配套记录文件

| 文件 | 用途 |
|------|------|
| `docs/acceptance-records/phase7-perf-eval.json` | 分阶段性能评测结果 |
| `docs/acceptance-records/phase7-rollout-log.json` | 灰度与回滚日志 |
| `docs/reports/phase7-perf-baseline.md` | P6 vs P7 对比报告 |
| `docs/reports/phase7-g0-preflight-checklist.md` | G0 离线预检 |
| `docs/config-phase7.example.yaml` | P7 推荐 config 快照 |
| `scripts/phase7_benchmark_run.py` | 分阶段 timed benchmark（ingest/embed/cluster/curate + 增量场景） |
| `scripts/phase7_nr_collect.py` | fixture NR 指标自动采集 → perf-eval |
| `scripts/phase7_pipeline_perf.py` | 分阶段 benchmark |
| `scripts/phase7_equivalence_check.py` | NR-P7 离线检查 |
| `scripts/phase7_gate_run.py` | 一键门禁（benchmark + NR + pytest + perf + equivalence） |

---

## 变更记录

| 日期 | 说明 |
|------|------|
| 2026-05-30 | 初稿：M27–M29 对齐 PRD v0.7.0；3 周执行顺序与发布闸门 |
