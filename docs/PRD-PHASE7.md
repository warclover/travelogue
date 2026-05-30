# Travelogue · Phase 7 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | v0.7.0-PHASE7 |
| **状态** | Draft · 开发准入（管线性能专项） |
| **Phase 7 代号** | 「极速管线」— 缩短等待 · 效果等价 · 可度量回归 |
| **前置条件** | [PRD-PHASE6.md](./PRD-PHASE6.md) G0 离线 AC 通过；Phase 6 质量指标（聚类/分段/排版）基线已登记 |
| **交付形态** | 在不改变 Phase 6 算法输出与能力边界前提下，显著缩短 Studio 导入→预览 wall-clock；建立性能 KPI 与质量等价回归闸门 |
| **关联文档** | [PRD-PHASE6.md](./PRD-PHASE6.md)、[PRD-PHASE6-ART-OPTIMIZATION.md](./PRD-PHASE6-ART-OPTIMIZATION.md)、[ACCEPTANCE-PHASE6.md](./ACCEPTANCE-PHASE6.md)、[PRD-PHASE3.md](./PRD-PHASE3.md) §1.5、[TECH-ARCHITECTURE.md](./TECH-ARCHITECTURE.md)、[MEDIA-PIPELINE.md](./MEDIA-PIPELINE.md)、[智能排版V2.md](./智能排版V2.md) §8、[adr/007-native-clustering.md](./adr/007-native-clustering.md) |
| **更新日期** | 2026-05-30 |

> **定位说明**
>
> - Phase 6 解决 **「好不好」**（聚类稳态、叙事分段、排版质量可测）；Phase 7 解决 **「等多久」**（ingest / CLIP / curate 的工程耗时）。
> - 本 Phase **不新增** 用户可见算法能力；所有优化须满足 **NR-P7 质量等价**（§12）。
> - Phase 6 PRD §20.3 已将「性能专项」列为 P7 候选输入；本文为其正式规格化。

---

## 1. 背景与问题陈述

### 1.1 Phase 6 之后的新瓶颈

Phase 6 在 fixture 基准上已证明 HDBSCAN 等升级 **可同时改善质量与聚类耗时**（`pipeline_time_1k` 相对 P5 −17%）。但 **真实用户路径**（Studio 选文件夹 → 预览）的 wall-clock 仍由下列环节主导：

| 阶段 | 典型占比（250 张 · vision 开启） | 根因（代码现状） |
|------|----------------------------------|------------------|
| **Ingest** | 40–55% | 逐张解码；Haar 分类器重复加载；3 档 WebP `method=6`；luma/tone 多次缩略图 |
| **CLIP + 聚类** | 25–40% | `_embed_clip` 逐张 `batch=1`；每 trip 新建 `ClipEncoder` 冷启动 |
| **Curate / Beam** | 5–15% | 多 variant 重复 `plan_screens_for_chapter` + 全量 `score_screen_plan` |
| **Render** | 5–10% | HTML 生成（本 Phase 仅做必要并行，不重写渲染） |

用户主路径（Phase 5 · ~80% 分享者）期望：**选文件夹 → 几分钟内看到可分享成品**（G-P2-01 / Phase 3 §1.5）。P3-Full CPU 路径 soft 上限为 400 张 **≤8 分钟（模型已缓存）**；当前实现距该承诺仍有明显 gap，且 **二次导入**（增量照片）未充分利用已有 embedding cache。

### 1.2 Phase 7 要解决的断裂点

| 断裂 | 现状（Phase 6） | Phase 7 目标 |
|------|-----------------|--------------|
| **断裂 A · CLIP 吞吐** | 逐张推理，GPU/CPU 利用率低 | 批量 encode + I/O 预取；会话内模型单例 |
| **断裂 B · Ingest CPU 浪费** | 人脸检测重复加载 cascade；色彩指标重复 resize | 单例 + 共享缩略图；WebP 编码档位优化 |
| **断裂 C · 流水线串行** | ingest 完 → 再 clustering → 再 curate | ingest ∥ 增量 embed（可选波次） |
| **断裂 D · Layout 重复劳动** | 相同 plan 签名仍重复评分；全量 deepcopy | 签名短路 + 增量评分（等价变换） |
| **断裂 E · 性能不可运营** | 仅有 fixture 代理指标 | 分阶段耗时 telemetry + 设备档位 SLO |
| **断裂 F · 冷启动体验** | 首次 CLIP 权重下载阻塞 curate 阶段 | 选文件夹后异步预热 |

### 1.3 优化原则（硬约束）

1. **效果等价优先**：优化不得改变 curate 输出、聚类标签、subjectClass、屏序与 cover 选择（在固定 seed + 固定 config 下）。
2. **Fail-open**：任一新 fast-path 失败时回退现有慢路径，不阻塞主流程。
3. **可开关、可回滚**：每项优化独立 config flag，默认在 G0 验证后逐步打开。
4. **不测的不算**：每项 P0 优化须有 before/after benchmark 与 NR-P7 回归用例。

---

## 2. 目标与非目标

### 2.1 产品目标

| ID | 目标 | 衡量方式 |
|----|------|----------|
| **G-P7-01** | Studio 导入 wall-clock 显著下降 | 250 张 P3-Full · S2 设备：端到端 **−30%**（相对 P6 基线） |
| **G-P7-02** | Ingest 阶段加速 | 250 张 ingest **−25%**（同硬件 · 同 dedupe 配置） |
| **G-P7-03** | CLIP 路径加速 | 250 张 CLIP embed（cache miss 全量）**−40%** |
| **G-P7-04** | 增量导入体验 | 变更 ≤10% 照片时 clustering **−60%**（相对全量 embed） |
| **G-P7-05** | 质量零退化 | NR-P7 全项通过（§12） |
| **G-P7-06** | 确定性保持 | `clustering.deterministic=true` 下双跑 hash **≥95%** 一致 |
| **G-P7-07** | 可观测 | pipeline 输出分阶段 `elapsedMs`（ingest / embed / cluster / curate / render） |
| **G-P7-08** | 冷启动可感知优化 | 首次 CLIP 权重准备移出 curate 关键路径（预热或并行） |
| **G-P7-09** | 自适应吞吐稳定 | S1/S2/S3 自动 batch 收敛，不低于固定默认（同场景） |
| **G-P7-10** | 缓存一致性增强 | cache ABI 不匹配时自动失效重建，且通过 NR-P7 |
| **G-P7-11** | 并行故障可恢复 | 强制中断/异常写入后可恢复，无半写入 trip/cache |

### 2.2 非目标

- **不** 降低 beam_width、减少 layout variant 数量或放宽 `SearchBudget` 以换速度（会直接改变排版结果）。
- **不** 在 `vision.enabled=true` 时默认改用 heuristic 向量替代 CLIP（仅优化 CLIP 执行方式）。
- **不** 减少 WebP 宽度档位或默认 JPEG 质量（影响渲染清晰度）。
- **不** 移除 burst/phash 去重逻辑。
- **不** 引入云端推理或改变「照片不出本机」隐私模型。
- **不** 在本 Phase 强制完成 ONNX 迁移（列为 P2 可选 Spike；须单独过确定性验收）。
- **不** 重写 Phase 5/6 双路径渲染骨架或模板契约。

---

## 3. 已拍板决策（D-P7）

| ID | 决策 | 结论 | 说明 |
|----|------|------|------|
| **D-P7-01** | CLIP 推理模式 | **批量化 + 单例** 为 P0；逐张路径保留为 fallback | batch size 可配置，默认 16 |
| **D-P7-02** | CLIP 输入分辨率 | **优先 web derivative（800px）** | 原图路径保留为 fallback；embedding 余弦距离漂移须在阈值内 |
| **D-P7-03** | Ingest 色彩指标 | **共享 32×32 缩略图** 计算 luma + tone | sharpness 仍独立路径 |
| **D-P7-04** | WebP 编码 | **`method=4`** 为默认（可配置） | quality 不变 |
| **D-P7-05** | Haar 人脸检测 | **Classifier 进程内单例** | 检测逻辑不变 |
| **D-P7-06** | ingest ∥ embed | **W2 启用**；W1 不阻塞 | 需保证 subjectClass 原子写入 |
| **D-P7-07** | Layout 优化策略 | **等价变换**（短路 + 增量评分） | 禁止改变搜索语义 |
| **D-P7-08** | ONNX | **P2 可选** | 须过 G-P7-06 + NR-P7；不默认启用 |
| **D-P7-09** | 性能回归闸门 | **先性能、后放量** | 任一项 P0 优化合并须附 benchmark 记录 |
| **D-P7-10** | Batch 选择策略 | **自适应探测优先** | 启动小样本探测；失败回落固定默认 |
| **D-P7-11** | 缓存兼容策略 | **引入 Cache ABI Version** | `algo/model/config` 指纹变化即失效重建 |
| **D-P7-12** | 确定性验收模式 | **固定集强确定性** | 固定 fixture 要求 100% 一致 |

---

## 4. 核心指标体系（KPI）

### 4.1 端到端性能指标

| 指标 | 定义 | 基线 | Phase 7 目标 |
|------|------|------|--------------|
| `studio_e2e_250` | Studio 250 张 · vision on · S2 · 冷 cache 端到端 | P6 实测登记 | **−30%** |
| `studio_e2e_250_p95` | 同上，95 分位端到端耗时 | P6 实测 | **−25%** 且 `p95 <= p50 * 1.6` |
| `ingest_time_250` | ingest 阶段耗时 | P6 实测 | **−25%** |
| `clip_embed_time_250` | 全量 CLIP embed（无 cache） | P6 实测 | **−40%** |
| `clip_embed_time_250_p95` | 同上，95 分位耗时 | P6 实测 | **−30%** 且 `p95 <= p50 * 1.8` |
| `clip_embed_time_incr_10pct` | 10% 照片变更 · incremental | P6 实测 | **−60%** |
| `curate_beam_time_250` | layout beam replan 耗时 | P6 实测 | **−30%** |
| `pipeline_time_1k` | 1000 张代理总耗时（fixture） | P6 基线 | **不劣于 P6**（允许 ±5% 测量噪声） |
| `peak_memory_1k` | 峰值内存 | P6 基线 | **退化 <10%** |
| `auto_batch_win_rate` | 自动 batch 不劣于固定默认的样本占比 | 无 | **≥95%** |
| `cache_rebuild_success_rate` | ABI 失效重建成功率 | 无 | **100%**（固定测试集） |

### 4.2 质量守护指标（不得退化）

| 指标 | 定义 | 阈值 |
|------|------|------|
| `cluster_noise_ratio` | 噪声样本占比 | ≤ P6 基线 + 2pp |
| `event_boundary_f1` | 事件边界 F1 | ≥ P6 基线 |
| `layout_repeat_streak` | 同模板连续长度 | ≤ P6 基线 |
| `nr_p7_curate_hash_fixed` | 固定 fixture（固定 seed/config）curate hash 一致率 | **100%** |
| `nr_p7_cluster_hash_fixed` | 固定 fixture（固定 seed/config）cluster hash 一致率 | **100%** |
| `nr_p7_curate_hash_real` | 真实脱敏集 curate hash 一致率 | ≥ 95% |
| `nr_p7_cluster_hash_real` | 真实脱敏集 cluster hash 一致率 | ≥ 95% |
| `subject_class_agreement` | CLIP batch  vs 逐张 subjectClass 一致率 | **100%**（同模型同输入） |
| `rollback_recovery_success` | 中断后恢复成功率（cache + trip） | **100%**（故障注入测试） |

### 4.3 体验指标

| 指标 | 定义 | 目标 |
|------|------|------|
| `stage_hint_gap_sec` | 相邻 progress 更新最大间隔 | **≤20s** |
| `clip_cold_start_in_curate` | curate 阶段内首次 CLIP 加载占比 | **<10%** wall-clock（预热后） |

---

## 5. 实施波次（路线图）

```mermaid
flowchart LR
  W1[波次1: Ingest + CLIP P0] --> W2[波次2: 流水线并行 + 预热]
  W2 --> W3[波次3: Layout 等价加速 + 可选 ONNX]
```

| 波次 | 周期建议 | 主题 | 完成标志 |
|------|----------|------|----------|
| **W1** | 1–2 周 | CLIP batch/单例 · ingest 微优化 · 分阶段 telemetry | G-P7-02/03/07 + NR-P7 基线 |
| **W2** | 1–2 周 | ingest∥embed · CLIP 预热 · web derivative 优先 | G-P7-01/04/08 |
| **W3** | 1 周 | layout 增量评分/短路 · ONNX spike（可选） | G-P7-05/06 全绿 |

---

## 6. 模块需求规格（可拆任务）

每项格式：**ID · 模块 · 动作 · 优先级 · 验收**

### 6.1 模块 A · CLIP 推理加速

| ID | 动作 | P | 验收 |
|----|------|---|------|
| **P7-A1** | `_embed_clip` 改为 batch inference（可配置 `vision.batch_size`） | P0 | 250 张 embed −40%；subjectClass 100% 一致 |
| **P7-A2** | `ClipEncoder` 进程级单例（Studio 会话复用） | P0 | 同会话第 2 trip 无模型重载；内存不泄漏 |
| **P7-A3** | I/O 预取：后台线程 decode 下一 batch | P1 | CPU/GPU 流水线重叠可观测 |
| **P7-A4** | 优先读取 `assets/web` 800px WebP；原图 fallback | P1 | embedding 余弦距均值 < 0.02 vs 原图路径 |
| **P7-A5** | batch 失败时逐张 fallback + 日志 | P0 | 不阻塞 clustering；decision_log 可追溯 |
| **P7-A6** | 增量 embed 仅对 `plan.new_ids` 跑 batch | P0 | 10% 变更场景达 G-P7-04 |

**涉及文件**：`travelogue/vision/clip_encoder.py`、`travelogue/vision/cache.py`、`travelogue/curation/clustering.py`

### 6.2 模块 B · Ingest 微优化

| ID | 动作 | P | 验收 |
|----|------|---|------|
| **P7-B1** | OpenCV Haar `CascadeClassifier` 模块级 lazy 单例 | P0 | 250 张 ingest −5% 以上；检测结果不变 |
| **P7-B2** | 共享 32×32 缩略图计算 `meanLuma` + `dominantTone` | P0 | 字段数值漂移在 documented tolerance 内；layout 评分 regression 通过 |
| **P7-B3** | WebP `method=4` 为默认（`ingest.webp_method` 可配置） | P0 | encode −30%；文件体积增幅 <15% |
| **P7-B4** | 人脸检测前可选缩放到长边 640（`ingest.face_detect_max_edge`） | P2 | focal/salient 误差 <5%；默认 off 直至 A/B 通过 |
| **P7-B5** | ingest 分阶段计时写入 `ingestStats.elapsedMs` | P1 | Studio telemetry 可读取 |

**涉及文件**：`travelogue/media/subject_detect.py`、`travelogue/media/ingest.py`、`travelogue/media/image_ops.py`、`travelogue/media/color_metrics.py`

### 6.3 模块 C · 流水线并行与预热

| ID | 动作 | P | 验收 |
|----|------|---|------|
| **P7-C1** | ingest 每 N 张（默认 32）触发后台 incremental embed | P1 | wall-clock ≈ max(ingest, embed)；无半写入 subjectClass |
| **P7-C2** | Studio 选文件夹后异步 CLIP 模型 preload | P1 | G-P7-08；失败 silent skip |
| **P7-C3** | clustering 与 curate 间只 merge cache + HDBSCAN（embed 已完成） | P1 | 增量场景 clustering 耗时 −50% |
| **P7-C4** | 并发安全：embedding cache 写入串行化 | P0 | 无 corrupt cache；F-CLU-CACHE-05 仍成立 |
| **P7-C5** | 写入事务不变式：tmp+rename、manifest/version 单调递增、subjectClass 批末一次性提交 | P0 | 任意中断不出现半写 trip 与损坏 cache |

**涉及文件**：`travelogue/web/studio_pipeline.py`、`travelogue/vision/cache.py`、`travelogue/curation/clustering.py`

### 6.4 模块 D · Layout Beam 等价加速

| ID | 动作 | P | 验收 |
|----|------|---|------|
| **P7-D1** | candidate 与 legacy 签名相同时跳过 `score_screen_plan` | P1 | NR-P7 curate hash 100% |
| **P7-D2** | 增量评分：维护 beam 累计分 + 滑动窗口 cross-screen 项 | P2 | 与全量评分 diff < 1e-6；beam 结果一致 |
| **P7-D3** | `deepcopy(chapters)` 改为写时复制或局部 copy | P2 | 内存峰值 −10%；输出一致 |
| **P7-D4** | `SearchBudget` 评估计数修正（生成 vs 评分分离） | P1 | telemetry 准确；行为不变 |

**涉及文件**：`travelogue/curation/layout_search.py`、`travelogue/curation/layout_candidates.py`、`travelogue/curation/layout_scoring.py`

### 6.5 模块 E · 性能基准与可观测性

| ID | 动作 | P | 验收 |
|----|------|---|------|
| **P7-E1** | `scripts/phase7_pipeline_perf.py` 分阶段 benchmark | P0 | 输出 ingest/embed/cluster/curate/render |
| **P7-E2** | `docs/acceptance-records/phase7-perf-eval.json` 记录格式 | P0 | 固定 commit + config + 设备档 |
| **P7-E3** | NR-P7 回归套件：`tests/test_phase7_equivalence.py` | P0 | CI 必跑；失败阻塞 merge |
| **P7-E4** | Studio progress 接入分阶段耗时（L2 可选展示） | P2 | L1 无新增复杂 UI |

**涉及文件**：`scripts/phase7_*.py`、`docs/acceptance-records/`、`tests/test_phase7_equivalence.py`

### 6.6 模块 F · ONNX 可选 Spike（P2）

| ID | 动作 | P | 验收 |
|----|------|---|------|
| **P7-F1** | PyTorch vs ONNX 250 张耗时与 embedding 对齐报告 | P2 | 文档化；不默认启用 |
| **P7-F2** | 确定性双跑（ONNX INT8） | P2 | ≥95% hash；否则 No-Go |
| **P7-F3** | License BOM 更新 | P2 | 无 L2 组件进入默认链 |

**关联**：Phase 3 OQ-P3-03 · `docs/spikes/clustering-algorithm-matrix.md` §4.2

### 6.7 模块 G · 稳定性与自适应增强（P0/P1）

| ID | 动作 | P | 验收 |
|----|------|---|------|
| **P7-G1** | 启动自适应 batch 探测（小样本）并落盘推荐值 | P0 | `auto_batch_win_rate` ≥95%，无新增 OOM |
| **P7-G2** | 增加 `deterministic_strict`（固定 seed/排序/线程） | P0 | 固定 fixture hash 100% |
| **P7-G3** | cache ABI version：`algoVersion/modelVersion/configFingerprint` | P0 | ABI 变化触发重建，NR-P7 通过 |
| **P7-G4** | 双文件提交协议：`embeddings.tmp + manifest.tmp` 原子切换 | P0 | 故障注入后无 corrupt cache |
| **P7-G5** | 动态退化保护：慢批次/内存压力自动降 batch 与关闭预取 | P1 | 长尾耗时降低，p95 不恶化 |
| **P7-G6** | 增量场景拆分验收（append/delete/replace） | P1 | 三类场景均达 AC-P7-03 |

---

## 7. 数据与配置变更

### 7.1 配置项新增（建议）

| 配置键 | 默认值 | 说明 |
|--------|--------|------|
| `vision.batch_size` | `16` | CLIP image encode batch size；`0` = 逐张 fallback |
| `vision.prefer_web_derivative` | `true` | 优先 800px WebP 作为 CLIP 输入 |
| `vision.session_singleton` | `true` | Studio 进程内复用 ClipEncoder |
| `vision.preload_on_folder_pick` | `true` | 选文件夹后异步预热 |
| `ingest.webp_method` | `4` | Pillow WEBP method（1–6） |
| `ingest.shared_color_thumb_px` | `32` | luma + tone 共享缩略图边长 |
| `ingest.face_detect_max_edge` | `0` | `0` = 不缩放；`640` = 检测前缩放 |
| `pipeline.parallel_embed` | `false` | W2 启用 ingest ∥ embed |
| `pipeline.parallel_embed_chunk` | `32` | 每批触发 embed 的照片数 |
| `layout_scoring.incremental` | `false` | 增量评分（W3） |
| `layout_scoring.skip_duplicate_signatures` | `true` | 签名相同跳过评分 |
| `vision.batch_auto_tune` | `true` | 启动小样本自动 batch 探测 |
| `vision.batch_auto_tune_samples` | `8` | 探测样本数 |
| `clustering.cache_abi_version` | `"v1"` | cache ABI 版本号 |
| `clustering.cache_config_fingerprint` | `auto` | 关键 config 指纹 |
| `clustering.deterministic_strict` | `false` | 固定集验收时启用强确定性模式 |
| `vision.dynamic_backoff` | `true` | OOM/慢批次自动降级保护 |

### 7.2 输出字段新增（建议）

- `trip.pipeline.timings`：`{ ingestMs, embedMs, clusterMs, curateMs, renderMs, totalMs }`
- `trip.ingestStats.elapsedMs`：ingest 细分（decode / webp / faces / dedupe）
- `trip.curation.clustering.embedStats`：`{ mode, batchSize, source, elapsedMs, cacheHitRatio }`

### 7.3 Schema 影响

- 上述字段为 **optional**；旧 trip 无字段时 validator 仅 WARN。
- 确定性回归以 **curate 产出 + clustering 字段** 为主 hash 输入（见 NR-P7 §12.2）。

---

## 8. 验收标准（AC-P7）

| ID | 通过条件 |
|----|----------|
| **AC-P7-01** | S2 · 250 张 · vision on：`studio_e2e_250` 相对 P6 **−30%** |
| **AC-P7-02** | `ingest_time_250` **−25%**；`clip_embed_time_250` **−40%**；对应 P95 指标满足 §4.1 |
| **AC-P7-03** | 10% 增量变更：`clip_embed_time_incr_10pct` **−60%** |
| **AC-P7-04** | NR-P7 全项通过（固定 fixture=100%；真实脱敏集≥95%，见 §12） |
| **AC-P7-05** | `pipeline_time_1k` 不劣于 P6 基线 +5%；`peak_memory_1k` 退化 <10% |
| **AC-P7-06** | `clustering.deterministic=true`：固定 fixture 双跑 hash **100%**，真实脱敏集 ≥95% |
| **AC-P7-07** | 分阶段 `pipeline.timings` 可在 benchmark 记录与 Studio 日志读取 |
| **AC-P7-08** | 所有 P0 优化可独立 config 关闭并回退至 P6 行为 |
| **AC-P7-09** | Phase 6 质量 KPI（`cluster_noise_ratio`、`event_boundary_f1`、`layout_repeat_streak`）不退化 |
| **AC-P7-10** | Auto batch 在 S1/S2/S3 收敛且不劣于固定默认（同场景） |
| **AC-P7-11** | cache ABI 不匹配时自动失效重建且通过 NR-P7 |
| **AC-P7-12** | 故障注入（中断/断写）后可恢复，无半写入 trip/cache |

---

## 9. 目标用户与场景

### 9.1 Persona

| Persona | Phase 7 价值 |
|---------|--------------|
| **分享者（~80%）** | 更短等待 → 更接近「选文件夹 → 几分钟出稿」 |
| **进阶用户（~20%）** | 增量加片后 re-import 更快；L2 可看分阶段耗时 |
| **维护者 / QA** | 可复现 benchmark + NR-P7 CI |

### 9.2 User Stories

| ID | 作为… | 我想要… | 以便… |
|----|--------|---------|--------|
| **US-P7-01** | 分享者 | 导入 200+ 张时 **明显更快** 看到预览 | 不中途放弃 |
| **US-P7-02** | 分享者 | 追加少量照片后 **不用等全量 CLIP** | 快速刷新游记 |
| **US-P7-03** | 分享者 | 等待时 **progress 持续更新** | 知道程序仍在工作 |
| **US-P7-04** | 维护者 | 一键跑 **性能 + 等价** 回归 | 合入前有信心 |
| **US-P7-05** | 维护者 | 关闭单项 fast-path 做 A/B | 定位性能回归 |

### 9.3 耗时预期（修订 · 在 Phase 3 §1.5 基础上）

**前提**：模型已缓存 · S2 设备 · Phase 7 W2 完成

| 档位 | 照片数 | Phase 6 参考 | Phase 7 目标 |
|------|--------|--------------|--------------|
| **P3-Lite** | 250 | ingest+geo ≤ ~2 min | **≤ ~1.5 min** |
| **P3-Full** | 250 | ingest+clip ≤ ~6–8 min | **≤ ~4 min** |
| **P3-Full** | 400 | CPU soft ≤ 8 min | **≤ ~5 min** |
| **增量** | +25 张（10%） | ≈ 全量 embed | **≤ 全量 40% 时间** |

**首次 CLIP 下载**仍不计入 G-P7-01；预热仅减少 **加载进内存** 在 curate 内的占比。

---

## 10. 风险与依赖

| 风险 | 影响 | 缓解 |
|------|------|------|
| CLIP batch 导致 OOM | 大 batch GPU/CPU 内存峰值 | 可配置 batch_size；OOM 自动 halve batch fallback |
| web derivative embedding 漂移 | 聚类边界微变 | P7-A4 余弦距门禁；超阈值回退原图 |
| ingest∥embed 竞态 | cache corrupt / 半写入 subjectClass | P7-C4 串行写；atomic commit（沿用 batch 末写入） |
| 共享缩略图 luma/tone 微差 | layout 连续性评分微变 | NR-P7 layout golden；tolerance 文档化 |
| WebP method 体积增大 | zip 变大 | 监控 `export.max_zip_mb`；method 可配置回 6 |
| 增量评分实现错误 | beam 选屏变化 | P7-D2 仅 W3；全量评分 fallback；双跑 diff |
| Windows 上线程/GIL | 并行收益低于预期 | I/O 用线程；CPU 密集用 batch 而非多进程（W1） |
| ONNX 确定性失败 | 无法替换 PyTorch | 保持 PyTorch 默认；ONNX 仅实验 |
| Auto batch 误判 | 吞吐波动或 OOM | `batch_auto_tune` 探测 + 上限保护 + 动态降级 |
| cache ABI 误配置 | 频繁全量重算或缓存污染 | ABI/version 指纹自动校验 + 可观测日志 |
| 强确定性与性能冲突 | 验收模式偏慢 | 仅固定集/CI 开启 `deterministic_strict` |

**依赖**：

- Phase 6 embedding cache（F-CLU-CACHE）已落地 — P7 增量路径依赖其正确性。
- Phase 3 `clustering.deterministic` 约束 — P7 不得破坏。
- 黄金样本 / fixture 套件扩展至 **含真实 CLIP** 子集（至少 3 套 ≥50 张）。

---

## 11. 交付物清单

- `docs/PRD-PHASE7.md`（本文件）
- `docs/IMPLEMENTATION-PHASE7.md`（任务拆解与进度跟踪）
- `docs/ACCEPTANCE-PHASE7.md`（验收与签字清单）
- `docs/acceptance-records/phase7-perf-eval.json`（性能评估记录）
- `docs/reports/phase7-perf-baseline.md`（P6 vs P7 对比报告）
- `scripts/phase7_pipeline_perf.py`（分阶段 benchmark）
- `scripts/phase7_equivalence_check.py`（NR-P7 离线检查）
- `tests/test_phase7_equivalence.py`（CI 回归）

---

## 12. 质量等价回归（NR-P7）

> Phase 7 的性能优化 **以 NR-P7 为发布硬闸门**；仅性能提升但 NR 失败 **不得** 放量。

### 12.1 等价范围

| 范围 | 必须一致 |
|------|----------|
| `curation.chapters` 屏序与 patternId | ✓ |
| `curation.coverByLayout` | ✓ |
| `asset.sceneClusterId` / `subjectClass` | ✓（deterministic 模式） |
| `curation.clustering.segments` | ✓ |
| `layout_scoring` 启用时的 replan 结果 | ✓ |

### 12.2 回归方法

1. **固定输入**：≥5 套 benchmark trip（含 golden + 真实相册脱敏）；固定 `config.yaml` 快照；固定 commit。
2. **双跑**：P6 行为（全部 P7 fast-path **off**） vs P7 行为（全部 P7 fast-path **on**）。
3. **Hash（双门槛）**：对 §12.1 字段 canonical JSON → SHA256；
   - 固定 fixture（固定 seed + 固定 config）：一致率 **100%**；
   - 真实脱敏集：一致率 ≥95%（允许 documented 浮点 tolerance 字段除外）。
4. **CLIP subjectClass**：同图 batch vs 逐张 **100%** 一致（独立 pytest）。
5. **Layout**：`tests/test_layout_golden.py` 全绿；beam decision log variant 分布一致。

### 12.3 允许漂移字段（documented）

| 字段 | 允许原因 |
|------|----------|
| `quality.meanLuma` | 共享缩略图算法 ±0.02 |
| `dominantTone` | 16→32 缩略图合并 ±1 RGB step |
| `pipeline.timings` / `embedStats` | 新增 telemetry |
| 文件体积 / `contentSig` | WebP method 变化 |

---

## 13. 灰度发布与回滚 Runbook

### 13.1 灰度阶段

| 阶段 | 范围 | 门槛 |
|------|------|------|
| **G0** | 离线 benchmark + NR-P7 CI | AC-P7-01~06 |
| **G1** | 内测 10% · 仅 P7-A + P7-B | 无质量 KPI 退化 |
| **G2** | 内测 50% · 含 P7-C 并行 | G-P7-01 达标 |
| **G3** | 全量默认开启 P0+P1 | 7 天无 perf/quality 告警 |

### 13.2 回滚触发

- NR-P7 CI 失败。
- `cluster_noise_ratio` 或 `event_boundary_f1` 相对 P6 退化超 §4.2 阈值。
- OOM 或 cache corrupt 率上升。

### 13.3 回滚步骤

1. `vision.batch_size=0`（逐张 fallback）。
2. `pipeline.parallel_embed=false`。
3. `vision.prefer_web_derivative=false`。
4. `ingest.webp_method=6`（恢复 P6 编码）。
5. `layout_scoring.incremental=false`。
6. 运行一键校验（建议脚本：`scripts/phase7_verify_rollback.py`）确认与 P6 行为等价。
7. 记录 `phase7-rollout-log.json` 事故条目。

---

## 14. 设备分层 SLO（修订）

在 Phase 6 §17 基础上，Phase 7 完成后 **目标**：

| 指标 | S1（4C/16GB） | S2（8C/16–32GB） | S3（GPU） |
|------|---------------|------------------|-----------|
| 250 张 · P3-Full 端到端 | **<12 min** | **<4 min** | **<2.5 min** |
| 250 张 · ingest only | **<4 min** | **<2 min** | **<2 min** |
| 250 张 · CLIP embed（cold cache） | **<8 min** | **<2.5 min** | **<45 s** |
| 峰值内存（250 张） | **<12 GB** | **<16 GB** | **<20 GB** |

---

## 15. 可观测性与告警

### 15.1 新增观测字段

- `pipeline.timings.*`
- `embedStats.cacheHitRatio`
- `embedStats.batchSize`
- `ingestStats.elapsedMs.*`

### 15.2 告警阈值

| 指标 | 阈值 | 动作 |
|------|------|------|
| `studio_e2e_250` | 相对 P7 基线退化 >15% | 冻结 G2+ |
| `nr_p7_curate_hash_fixed` | <100% | 阻塞发布 |
| `nr_p7_curate_hash_real` | <95% | 阻塞发布 |
| OOM rate | >1% trips | halve batch / 回滚 parallel_embed |

---

## 16. 组织协作模型（RACI）

| 工作项 | 产品 | 算法 | 工程 | QA |
|--------|------|------|------|-----|
| PRD 与优先级 | **A/R** | C | C | C |
| CLIP batch/单例 | C | **A/R** | R | C |
| Ingest 优化 | I | C | **A/R** | C |
| 流水线并行 | C | C | **A/R** | C |
| NR-P7 回归套件 | C | R | R | **A/R** |
| Benchmark 与放量 | C | R | **R** | C |

---

## 17. 开放问题

| ID | 问题 | v0.7.0 决议 |
|----|------|-------------|
| **OQ-P7-01** | ingest 多进程是否纳入 P7 | **否** → Future；W1–W2 仅 batch + 线程 I/O |
| **OQ-P7-02** | 默认 batch_size 16 是否适配 S1 | G0 实测；OOM 则默认 8 |
| **OQ-P7-03** | web derivative CLIP 是否默认开启 | **是**（D-P7-02）；余弦距门禁 |
| **OQ-P7-04** | layout 增量评分是否 P7 必达 | **P2**；W3 完成；可延期至 P7.1 |
| **OQ-P7-05** | ONNX 默认路径 | **否**；Spike only（P7-F*） |
| **OQ-P7-06** | 是否降低 `vision.auto_min_photos` 门槛换覆盖 | **否**；性能优化不改变 auto 策略 |
| **OQ-P7-07** | Auto batch 默认是否全量启用 | **是**，但保留 `batch_auto_tune=false` 回退 |
| **OQ-P7-08** | `deterministic_strict` 是否默认开启 | **否**；仅 CI/G0 验收启用 |

---

## 18. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.7.0-PHASE7** | 2026-05-30 | 初稿：ingest/CLIP/流水线/layout 四大性能主线；NR-P7 等价闸门；KPI/SLO/灰度/回滚 |
