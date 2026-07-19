# Travelogue · 流水线提速 V1 实施任务清单

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-PIPELINE-PERF-V1.md](./PRD-PIPELINE-PERF-V1.md) **v0.2** |
| **评审** | [acceptance-records/pipeline-perf-v1-review-2026-07-19.md](./acceptance-records/pipeline-perf-v1-review-2026-07-19.md) |
| **验收** | 落地后补 `ACCEPTANCE-PIPELINE-PERF-V1.md`（对照 PRD §9） |
| **状态** | **M1 ☑ · M2 ☑ · M3 ☑**（核心路径已落地；07b 狗粮签字后置） |
| **更新** | 2026-07-19 |
| **分支** | `feat/pipeline-perf-v1` |

---

## 落地原则

1. **质量分级**：E-A 严格等价（CI）；E-B 阈值 + 差异报告 + 狗粮复核 + 独立 flag。  
2. **srcset 合同**：只登记已落盘文件；计划档位走 `derivedPlan`（D2）。  
3. **不扩公开状态机**：materialize 不进 `stages_order`（D3）。  
4. **M1 可独立合入**：出口含 R1.1 根因报告 + AC-PPF-01～04。  
5. **测试隔离**：临时 `trips_dir`、显式 `AppConfig`；CI 不跑绝对时长（MF-06）。

---

## 摸底结论（开工前已知 · 2026-07-19）

| 发现 | 含义 |
|------|------|
| `ingest_into_trip` 会把 `ingestWorkers` / `ingestParallelFallback` 写入 `trip.pipeline.timings` | 写入侧正常（`ingest.py` ~1394） |
| `run_trip.flush_timings` → `set_pipeline_timings(trip, pipeline_timings)` **整表覆盖**；本地 `pipeline_timings` 在 stage 开始前拷贝，**不吸收** ingest 新写的 PT 键 | **P-PPF-01 主因（已修）**：并行可能已生效，但遥测被抹掉 → AC-PPF-01 假红 / 研究误判「未并行」 |
| `studio_pipeline._flush_pipeline_timings` 同类覆盖 | 已同步 `absorb_pipeline_timing_keys` |
| `config.yaml` 已 `parallel_ingest: true`；`config.demo.yaml` 无 pipeline 段（默认 `parallel_ingest=false`） | demo CLI 路径另论；Studio 走 `config.yaml` 时应开并行 |
| 本机探针：串行 6.4 s/张 · par4 4.4 · par8 3.0（24 张扫描 / 16 入库） | M1 放宽 workers + 修遥测即可验证收益 |

**R1.1 根因报告（定稿 · 2026-07-19）**：非「Studio 未加载 parallel_ingest」，而是 orchestrator / studio 在 flush timings 时用本地字典**整表覆盖** trip 上已写的 PT 键，导致 `ingestWorkers` 消失。修复：`absorb_pipeline_timing_keys`（`domain/pipeline_view.py`）在 `set_pipeline_timings` 前合并缺失键。验证：`tests/unit/orchestrator/test_pipeline_timings_absorb.py`。

---

## 里程碑总览

| 里程碑 | 目标 | 估时 |
|--------|------|------|
| **M1** | 并行遥测修复 + worker/内存护栏 + 人脸/webp E-B flag | 1.5～2.5 人日 |
| **M2** | 派生图分层 + 去重解码 + NIMA 重叠 | 3～5 人日 |
| **M3** | 预览先行（渐进产出） | 1.5～2 人日 |

---

## M1 · 止血

### 文档

| ID | 任务 | 状态 |
|----|------|------|
| DOC-PPF-01 | PRD v0.2 + 评审纪要 + 本清单 | ☑ |
| DOC-PPF-02 | R1.1 根因报告写入本清单「摸底结论」+ ACCEPTANCE | ☑ 根因已写入摸底；ACCEPTANCE 合入时补签字 |

### 后端 · 并行与配置

| ID | 任务 | 建议位置 | 状态 |
|----|------|----------|------|
| BE-PPF-01 | `flush_timings` 合并已有 `trip.pipeline.timings` 键，禁止抹掉 `ingestWorkers` / `ingestParallelFallback` | `orchestrator/run.py` · `studio_pipeline._flush_pipeline_timings` · `absorb_pipeline_timing_keys` | ☑ |
| BE-PPF-02 | 复现测试：flush 后保留 `ingestWorkers` | `tests/unit/orchestrator/test_pipeline_timings_absorb.py` | ☑ |
| BE-PPF-03 | `resolve_parallel_ingest_plan`：`workers=0` → `max(2, min(cpu//2, 10))` + long-edge 内存降额 | `media/ingest_parallel.py` · `test_parallel_ingest_workers.py` | ☑ |
| BE-PPF-04 | `face_detect_max_edge` 默认 1024 + 独立 flag（E-B，可回退） | `config/ingest.py` · config 示例 | ☑ |
| BE-PPF-05 | `webp_method` 默认 2 + 独立 flag（E-B） | `config/ingest.py` · config 示例 | ☑ |
| DOC-PPF-03 | 更新 `config.yaml.example` / throughput 示例说明 | `config.yaml.example` · `docs/config-pipeline-throughput.example.yaml` | ☑ |

### 测试 · M1 门禁

| ID | 任务 | 状态 |
|----|------|------|
| QA-PPF-01 | pytest：timings 合并不丢 PT 键（AC-PPF-01） | ☑ |
| QA-PPF-02 | pytest：worker 自动解析 + 降额（AC-PPF-02） | ☑ |
| QA-PPF-03 | 默认值单测 + 回退路径（AC-PPF-03/04 完整狗粮签字后置） | ☑ `test_ingest_perf_defaults.py` · 探针 `scripts/perf_probe_ingest.py` |

**M1 出口**：BE-PPF-01～05 绿；AC-PPF-01～02 过；根因报告定稿；R1.3/R1.4 新默认已合入（E-B：`face_detect_max_edge: 0` / `webp_method: 4` 可单独回退；07b 狗粮签字后锁死）。

---

## M2 · 结构性（待 M1 后）

| ID | 任务 | 状态 |
|----|------|------|
| BE-PPF-10 | `derivedPlan` schema + ingest 只产 800/1600 | ☑ `schemas/trip.schema.json` · `webp_ingest_widths` · `deferred_derivatives` |
| BE-PPF-11 | `media/derivatives.py` 物化；lock_structure 后后台线程与 narrate 重叠；render 前 join + sync ensure | ☑ |
| BE-PPF-12 | 金字塔缩放 flag 默认关 | ☑ `webp_pyramid=False` · `export_webp_variants(pyramid=…)` |
| BE-PPF-13 | 扫描免像素解码（orientation 交换） | ☑ `peek_image_meta` · `scan_image_paths` / tiered |
| BE-PPF-14 | 美学信号 / mediaClass 入 worker | ☑ `WorkerResult.media_class` / `aesthetic_signals`；merge 不再重开图 |
| BE-PPF-15 | NIMA 重叠预热 + torch 线程配额（只重叠不换源） | ☑ `aesthetic_warm.AestheticWarmCoordinator`；`warm_learned_on_ingest` |
| QA-PPF-10 | AC-PPF-05～10 · 07a CI · 07b 报告 · MF-10 三负例 | ◐ `test_derivatives_deferred` · `test_scan_peek_meta` · `test_webp_pyramid_flag` · `test_aesthetic_warm`；07a/07b/MF-10 后置 |

---

## M3 · 渐进产出

| ID | 任务 | 状态 |
|----|------|------|
| FE-PPF-01 | 两态进度 + 书架/预览一致 | ☑ `layout_preview_ready` / `export_ready` hints · shelf 角标 · `derivativesStatus` |
| BE-PPF-20 | 导出同步物化（D6，不置灰） | ☑ `ensure_derivatives_before_export` · zip/longshot 前同步 |
| QA-PPF-20 | AC-PPF-11 / 基准机 AC-PPF-12 | ☐ 基准机 Playwright 后置 |

---

## 变更记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-07-19 | 初稿 · 摸底：timings 覆盖抹掉 ingestWorkers · M1 任务拆解 |
| v0.2 | 2026-07-19 | M2 收尾：R3 扫描/worker 信号 · R4 NIMA 重叠 · R2.3 金字塔 flag · M3 两态进度与导出同步物化 |
