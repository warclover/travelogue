# Travelogue · 流水线提速 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | **v0.2** |
| **状态** | **有条件通过（Conditional Go）** · 评审 Must-Fix 已回写 · 可开 IMPLEMENTATION / M1 |
| **主题代号** | 「流水线提速 V1（Pipeline Perf）」— 并行修复 · 派生图分层 · 重复解码消除 · 计算重叠 |
| **调研来源** | 2026-07-19 首席架构师性能研究（13 个真实 trip `pipeline.timings` 埋点 + `scripts/perf_probe_ingest.py` / `scripts/perf_probe_pipeline.py` 实测，样本相册 `D:\Photos\仙本那精选全集2`） |
| **评审纪要** | [acceptance-records/pipeline-perf-v1-review-2026-07-19.md](./acceptance-records/pipeline-perf-v1-review-2026-07-19.md) |
| **关联文档** | [ARCH-OPT-P2-BACKLOG.md](./ARCH-OPT-P2-BACKLOG.md) · [config-pipeline-throughput.example.yaml](./config-pipeline-throughput.example.yaml) · [acceptance-records/tpc-local-dogfood-GUIDE.md](./acceptance-records/tpc-local-dogfood-GUIDE.md) |
| **验收** | 本文 §9；落地后补 `ACCEPTANCE-PIPELINE-PERF-V1.md` |
| **实施清单** | [IMPLEMENTATION-PIPELINE-PERF-V1.md](./IMPLEMENTATION-PIPELINE-PERF-V1.md) |
| **更新日期** | 2026-07-19 |

> **定位**
>
> 2026-07-19 性能研究确认：**游记生成端到端时间的 85%–91% 花在 ingest 阶段，ingest 内部约 79% 花在 WebP 多尺寸编码**；LLM、模板路由、排版搜索、HTML 渲染均不构成瓶颈。250 张相册当前约需 27 分钟，狗粮体验不可接受。
>
> 本 PRD 是一次**纯性能优化**，铁律是「**产物质量零退化**」：
>
> 1. **并行修好用满** — 已有的并行 ingest 机制在 Studio 实际导入中未生效（P0 bug）；修复并按机器核数放宽 worker 上限。
> 2. **不做白工** — 被 cull 淘汰、未进章节的照片不再编码 2400/3200 大图；派生图按「预览先行、成品补齐」分层生成。
> 3. **每张照片只解码一次** — 消除扫描阶段、并行 merge 尾巴中的重复全解码。
> 4. **计算重叠** — NIMA 美学推理与 ingest 重叠执行，curate 不再串行等待。
>
> 目标：250 张相册端到端 **27 min → ≤5 min**，首屏预览 **≤2.5 min**；最终游记产物（选片、文案、排版、图片分辨率与画质）与优化前**完全一致**（重构类改动）或**受控且经狗粮复核**（参数类改动，见 §0.2 等价性分级）。

> **v0.2 评审回写摘要（2026-07-19 Conditional Go）**
>
> - D1：质量红线做**等价性分级**——E-A（重构类）严格等价 = CI 门禁；E-B（参数类）阈值门槛 + 差异报告 + 狗粮复核 + 独立 flag
> - D2：**废除** srcset `pending` 标记；srcset 只登记已落盘文件，计划档位入 asset 级 `derivedPlan`，物化后增量回写
> - D3：`materialize_derivatives` **不进公开状态机**；lock_structure 后作为后台步骤**与 narrate 并行**，render 前 join
> - D4：NIMA 预热 V1 **只重叠不换源**（输入与现状 bit 级一致）；换输入源 Park V2
> - D5：并行 worker 内存降额公式（按 `nativeWidth` 中位数）**升格为 V1 落地**
> - D6：R5.1 导出门控拍板**同步物化案**（入口永远可点，缺档触发物化 + 现有进度条），不置灰
> - MF-01～10 已回写进 §0 / §4 / §9

---

## 0. 评审导读与质量红线

### 0.1 D1–D6（已拍板 · 2026-07-19）

| 决策 | 拍板结论 |
|------|----------|
| **D1 等价性分级** | E-A（重构类：R1.1/R1.2/R2.1/R2.2/R3.1/R3.2/R4.1）：产物与决策**严格等价**，golden trip 双跑 = CI 门禁。E-B（参数类：R1.3/R1.4/R2.3）：不承诺零差异，走 §0.2 阈值门槛 + golden trip **差异报告** + 狗粮复核签字 + 独立 flag 可单独回退 |
| **D2 派生图清单合同** | `srcset` 只登记**已落盘**文件（`_missing_derivative_paths` 不变量沿用）；计划档位写 asset 级 `derivedPlan`（含目标宽度与状态）；物化完成后增量回写 srcset。渲染/导出只读 srcset，天然 fail-closed |
| **D3 materialize 执行位置** | 不新增公开 pipeline 状态（`STAGE_MIN_STATUS` / `stages_order` 对 Studio/CLI 的合同不变）；lock_structure 后以后台步骤启动，与 narrate（网络等待）并行，render 前 join + 齐档校验 |
| **D4 NIMA 预热范围** | V1 只做「计算重叠」：预热线程输入与现状**完全一致**（原图路径 + `_ML_INPUT_SIDE=512`），分数 bit 级一致、contentSig 缓存键不变；「输入源换派生图」Park V2。预热线程设 torch 线程配额，避免与并行 ingest 池争核 |
| **D5 内存护栏** | V1 实现 worker 降额：按相册 `nativeWidth` 中位数估算单 worker 峰值内存，超预算自动降 worker 数并写遥测（不再只写文档） |
| **D6 导出门控（R5.1）** | 拍板**同步物化案**：预览先行期导出入口不置灰不禁用；点击后缺档触发同步物化，复用现有导出进度条。用户视角永远「点了就出」 |

### 0.2 质量红线与等价性分级（MF-01）

任何优化项合入前必须证明所属等级的不变量成立，否则不予合入：

**E-A 级（重构类 · 严格等价 · CI 门禁）**——适用 R1.1 / R1.2 / R2.1 / R2.2 / R3.1 / R3.2 / R4.1：

| # | 不变量 | 验证手段 |
|---|--------|----------|
| **Q1** | 选片结果不变：cull 保留集合、章节结构、mosaic/pattern 决策、封面/高光选择逐字段一致 | golden trip 双跑 + `screens[]` 指纹断言（AC-PPF-07a） |
| **Q2** | 最终产物包含完整 srcset（800/1600/2400/3200），文件分辨率与 `webp_quality` 参数不变 | 导出后文件清单 + 尺寸断言 |
| **Q4** | 文案不变：narrate brief、LLM 调用参数、缓存键不受本 PRD 影响 | brief hash 对比 |
| **Q5** | 失败语义不变：并行失败继续 fail-open 回退串行；延迟生成失败不产出缺图的导出物 | pytest 注入故障 |

**E-B 级（参数类 · 受控差异 · 人工门禁）**——适用 R1.3 / R1.4 / R2.3，每项独立 flag、可单独回退：

| # | 门槛 | 验证手段 |
|---|------|----------|
| **Q3** | 画质：新旧产物 SSIM ≥ 0.99（同尺寸对比，含高频纹理样张） | shadow-diff 脚本（沿用 TPC W1 模式） |
| **Q6** | 信号漂移受控：人脸检出差异 ≤2%、focal 偏移 ≤0.02（归一化）；产物体积增幅 ≤12% | 对比脚本（AC-PPF-03/04） |
| **Q7** | 决策差异可解释：golden trip 双跑输出**差异报告**（哪些照片选择/裁切变了、为什么）；狗粮走查签字后方可改默认值 | 差异报告 + 验收记录（AC-PPF-07b） |

**允许的可见差异**（明示豁免）：`webp_method` 调整导致的文件体积变化（预算 ≤ +12%）；派生图生成时间点后移（产物内容不变）。

### 0.3 派生图清单合同（MF-02 · D2）

| 场景 | 行为 |
|------|------|
| ingest 完成 | asset `srcset` = [800, 1600]（已落盘）；`derivedPlan` = 计划全档位 + 各档状态 |
| materialize 完成 | 入选资产 srcset 增量回写至全 4 档；`derivedPlan` 状态更新；落选资产 `derivedPlan` 标记 `skipped` |
| refine 换片 | 换入资产按需物化（单张同步 ≤3 s；>3 张转后台队列 + 徽标，MF-09） |
| 渲染 / 导出 | 只读 srcset；所需档位缺失 → 先同步物化再继续（fail-closed，Q5）；**禁止**引用不存在的文件 |
| schema | `derivedPlan` 为新增可选字段，进 `schemas/`；srcset 条目结构**不变** |

### 0.4 materialize 执行位置（MF-03 · D3）

```
ingest → clustering → curate → layout → lock_structure ─┬─ narrate（网络）
                                                         └─ materialize（CPU · 后台）
                                              render（join + 齐档校验）→ export
```

不新增公开 pipeline 状态；Studio/CLI 看到的 stages 合同不变。CLI 非渐进模式下 materialize 在 narrate 前同步执行（行为等价，只是不重叠）。

---

## 1. 背景与证据

### 1.1 埋点数据（13 个真实 trip · `pipeline.timings`）

| Trip | 照片数 | ingestMs | curateMs | renderMs | totalMs | ingest 占比 |
|------|--------|----------|----------|----------|---------|-------------|
| demo-1d4f92d534 | 250 | 24.5 min | 2.1 min | 10.8 s | 26.8 min | **91%** |
| demo-815dc906d3 | 249 | 27.3 min | 2.6 min | 19.2 s | 30.2 min | **90%** |
| demo-2025 | 121 | 12.9 min | 1.1 min | 15.4 s | 14.3 min | **90%** |
| demo-1b67b06546 | 35 | 6.4 min | 29.9 s | 12.3 s | 7.1 min | **90%** |

`clusterMs≈2ms`、`embedMs=0`（clustering 关）、`narrateMs≈13ms`（缓存/stub 命中）——LLM 与聚类当前不是瓶颈。

### 1.2 微基准（单张 8MP JPG · 串行路径 · 本机 18 逻辑核）

| 步骤 | 实测耗时 | 代码位置 |
|------|----------|----------|
| WebP 4 档编码（method=4） | **2.4–3.4 s** | `travelogue/media/image_ops.py` · `export_webp_variants` |
| 同 4 档 method=0 | 0.8–1.3 s（≈2.7× 快） | 同上 |
| 人脸检测（原图全分辨率，`face_detect_max_edge=0`） | 0.15–0.92 s | `travelogue/media/subject_detect.py` |
| 人脸检测（降采样 1024px） | 0.06–0.15 s（3–6× 快） | 同上（P7-B4 已支持，默认未启用） |
| 解码 | 0.08–0.17 s | `image_ops.load_image_normalized` |
| 锐度 / dhash / 色彩 | 各 <0.05 s | — |

### 1.3 端到端 ingest 对比（24 张扫描 · 16 张入库 · 同一相册）

| 模式 | 总耗时 | webp 分项 | 加速比 |
|------|--------|-----------|--------|
| 串行 | 102.7 s | 78.8 s（**79%**） | 1× |
| 并行 4 workers | 69.6 s | — | 1.5× |
| 并行 8 workers | 48.2 s | — | 2.1× |

并行加速比受三段串行拖累：扫描全解码（前置）、主进程 merge 重解码（尾巴）、Windows spawn 冷启动。

### 1.4 关键事实：Studio 实际导入未走并行

`config.yaml` 已设 `pipeline.parallel_ingest: true`（workers=4），但 2026-07-19 当天生成的 trip（如 demo-1b67b06546，10.9 s/张）`timings` 中**没有 `ingestWorkers` 字段**。按 `travelogue/media/ingest.py:1397` 的写入逻辑，只要运行时配置的 `parallel_ingest` 为真该字段必然写入——即 Studio 导入子进程实际读到的配置未开并行（疑似 demo 配置分支或 `studio_subprocess._import_worker` 的配置解析路径）。

---

## 2. 问题陈述（P-PPF-*）

| ID | 问题 | 严重度 | 证据 |
|----|------|--------|------|
| **P-PPF-01** | Studio 实际导入未启用并行 ingest，配置形同虚设 | **P0** | §1.4；timings 无 `ingestWorkers` |
| **P-PPF-02** | WebP 4 档全量编码占串行 ingest 79%；被 cull 淘汰/未入章节照片的 2400/3200 是纯白工 | **P0** | §1.2/§1.3；`export_webp_variants` 对每张照片无差别编码 4 档 |
| **P-PPF-03** | 人脸检测在原图全分辨率跑 Haar（`face_detect_max_edge=0` 默认） | **P1** | §1.2；7360px 照片单张最高 0.92 s |
| **P-PPF-04** | 扫描阶段对全部照片做完整像素解码，只为取尺寸+拍摄时间 | **P1** | `ingest.py` · `scan_image_paths` / `user_tier.scan_tiered_image_paths` 调 `_load_photo`（含 `exif_transpose`）；250 张 ≈ 30–60 s 串行 |
| **P-PPF-05** | 并行模式每张照片解码 3 次；美学信号/mediaClass 在主进程 merge 时串行重算 | **P1** | `ingest_parallel.py:268-306` · `_build_entry_from_worker_result` 重新 `Image.open` |
| **P-PPF-06** | NIMA（pyiqa/torch-CPU）美学推理在 curate 内串行执行，250 张 ≈ 2 min | **P1** | `curate.py` · `_stage_aesthetic_align` → `apply_aesthetic_ml_calibration`；本机 torch 2.12 CPU 版 |
| **P-PPF-07** | worker 自动上限 `min(4, cpu-1)` 过保守（本机 18 逻辑核） | **P2** | `ingest_parallel.py` · `resolve_parallel_ingest_plan` |
| **P-PPF-08** | 无渐进产出：用户必须等全链路完成才能看到任何结果，感知时间=全部时间 | **P2** | Studio 导入流程；预览只需 800px 派生图即可渲染 |

---

## 3. 目标与非目标

### 3.1 产品目标

1. **250 张相册端到端 ≤5 min**（当前 ~27 min），100 张 ≤2.5 min。
2. **首屏预览 ≤2.5 min**（P-PPF-08，M3 范围）。
3. **质量零退化**：E-A 项满足 §0.2 严格等价（Q1/Q2/Q4/Q5）；E-B 项满足阈值门槛（Q3/Q6/Q7）并经狗粮复核签字。
4. **机制可观测**：并行是否生效、派生图延迟队列积压、NIMA 重叠命中率均有埋点，回归可在 CI 中自动发现。

### 3.2 非目标

- 不改选片/排版/文案算法本身（beam 宽度、评分权重、cull 阈值一律不动）。
- 不引入 GPU 依赖；不更换图像编码库（如 libvips）——列为 V2 候选。
- 不动 Playwright 长图导出链路（浏览器池已有 warm 机制，另行立项）。
- 不做 CLIP/clustering 优化（当前默认关闭，embedMs=0）。
- 不改 `webp_quality`、srcset 档位定义等**产物合同**。

### 3.3 成功指标

| 指标 | 现状 | 目标 |
|------|------|------|
| 250 张端到端 totalMs | ~27 min | **≤5 min** |
| Studio 导入 `ingestWorkers` 埋点出现率 | 0% | 100%（≥`parallel_ingest_min_photos` 时） |
| 单张平均 ingest 耗时（8MP 类相册） | 5.9–10.9 s | ≤1.2 s（摊薄） |
| curate 内 NIMA 串行等待 | ~2 min/250 张 | ≤15 s（重叠+缓存命中） |
| golden trip `screens[]` 指纹一致率 | — | 100% |

---

## 4. 需求详述

### WS1 · 并行修复与低风险配置（P0）

#### R1.1 修复 Studio 并行失效（P-PPF-01 · MF-07）

- **先写失败复现测试**（Studio 导入 ≥12 张，断言 `ingest_stats` 含 `ingestWorkers`），再修根因；**根因报告为 M1 出口物**。
- 排查链路：`studio_subprocess._import_worker` 配置加载 → `resolve_studio_config` → `run_studio_pipeline` 的 `app_config_scope(cfg)` → `ingest_into_trip` 的 `resolved_app.pipeline.parallel_ingest`，定位哪一环丢失 `pipeline` 段。
- 覆盖 demo 导入分支：若走 `config.demo.yaml`（无 `pipeline` 段）需继承项目 `config.yaml` 的 pipeline 配置或在 demo 配置中显式补齐。
- **防回归**：ingest 完成时若 `parallel_ingest=true` 但未并行执行且照片数 ≥ `parallel_ingest_min_photos`，`ingest_stats` 必须写 `ingestParallelFallback=true` 及 fallback 原因码；Studio 遥测上报。

#### R1.2 worker 数放宽 + 内存护栏（P-PPF-07 · MF-05 · D5）

- `resolve_parallel_ingest_plan` 自动模式（`workers=0`）改为 `max(2, min(cpu//2, 10))`；显式配置仍以用户值为准。
- **内存降额（V1 落地，评审升格）**：按相册 `nativeWidth` 中位数估算单 worker 峰值内存（≈ 原图解码 + 最大变体，36MP 约 300–400 MB），超出预算（默认可用内存的 50%）自动降 worker 数，并写 `ingestWorkersDownscaled` 遥测与原因码。
- `config.yaml.example` 与 `docs/config-pipeline-throughput.example.yaml` 同步更新推荐值与内存预算说明。

#### R1.3 人脸检测降采样默认值（P-PPF-03 · E-B 级 · MF-08）

- `IngestConfig.face_detect_max_edge` 默认 `0 → 1024`（机制已存在，P7-B4）。
- **独立 flag、可单独回退**；改默认值前须满足 §0.2 Q6/Q7：≥3 个真实相册对比 `faceCount` / `focalPoint` / `salientBox`，人脸检出差异 ≤2% 且 focal 偏移 ≤0.02，**并出具 golden trip 差异报告 + 狗粮走查签字**（信号漂移会经锐度 ROI → 美学分 → cull 分传导，不承诺零决策差异）。
- 差异超限则保持可配置、默认不变，并在 §10 记录。

#### R1.4 webp_method 调优（P-PPF-02 部分 · E-B 级）

- 默认 `webp_method: 4 → 2`；实测编码提速 ~2–3×，同 `quality=82` 下视觉一致。**独立 flag、可单独回退**。
- 体积预算：产物总体积增幅 ≤12%（超限则仅对非 display 档降 method，display 档保留 4）。
- Q3 shadow-diff 验证 SSIM ≥0.99（含高频纹理样张：树叶 / 织物 / 文字）。

### WS2 · 派生图分层生成（P0 · 结构性最大收益）

#### R2.1 ingest 只产预览档（P-PPF-02 · MF-02 · D2）

- ingest 阶段 `export_webp_variants` 仅生成 **800/1600** 两档。
- **契约（§0.3）**：`srcset` 只登记已落盘文件；计划档位写 asset 级 `derivedPlan`（新增可选 schema 字段），物化完成后增量回写 srcset。**禁止** srcset 出现指向不存在文件的条目。
- `displayFile` 指向已生成的最大档（1600），保证 refine/预览页立即可用。

#### R2.2 成品档延迟物化（P-PPF-02 · MF-03/09/10 · D3）

- 新增物化模块 `materialize_derivatives`：只为**进入章节/封面/高光的资产**补齐 2400/3200，走并行池。
- **执行位置（§0.4）**：不进公开状态机；lock_structure 后以后台步骤启动，与 narrate 并行，render 前 join + 齐档校验。CLI 非渐进模式下同步执行。
- 被 cull 淘汰与未入选资产**永不**生成大图。
- **refine 换片（MF-09）**：换入未物化照片单张同步补齐（预算 ≤3 s）；一次换入 >3 张转后台队列 + 「正在准备 N 张高清图」徽标，禁止按钮长 loading 假死。
- **fail-closed（MF-10）**：render/export 前校验所需档位齐全（复用 `_missing_derivative_paths` 模式），缺档则先物化再继续，禁止产出缺图导出物（Q5）。故障注入负例：删档后导出 / 物化中途 kill / 换片并发导出。
- 增量重排（layout-only replan）时只物化新增资产，已物化档位幂等跳过。

#### R2.3 金字塔缩放（P-PPF-02 · E-B 级）

- 变体生成顺序改为从大到小逐级 resize（原图→3200→2400→1600→800），替代每档从原图 LANCZOS。
- **flag 默认关**（评审拍板）：出具 ≥3 相册 SSIM 报告（含高频纹理样张）且 SSIM ≥0.99 后方可默认开；不达标则保持关闭，不阻塞 M2 出口（独立开关，与 R2.1/R2.2 解耦合入）。

### WS3 · 消除重复解码（P1)

#### R3.1 扫描免像素解码（P-PPF-04）

- `scan_image_paths` / `scan_tiered_image_paths` 改为仅 `Image.open`（不触发像素载入）读取 `size` + EXIF 时间，不再调用 `exif_transpose` / `convert`。
- 注意 EXIF orientation：宽高判定（`min_dimension_ok`）需按 orientation tag 交换 w/h 后再判。
- 打不开/损坏文件的容错语义保持不变（计入 `skipped_open`）。

#### R3.2 美学信号与 mediaClass 移入 worker（P-PPF-05）

- `compute_aesthetic_signals`（纯 PIL）与 `classify_media_class` 在 `ingest_worker.process_ingest_photo_worker` 内完成，随 `WorkerResult` 回传（均为 pickle-safe dict）。
- 主进程 `_build_entry_from_worker_result` 不再重新打开图片；aesthetic contentSig 缓存的读写仍在主进程（避免 worker 并发写缓存文件）。
- 串行路径行为不变（同函数、同结果，仅执行位置不同）。

### WS4 · NIMA 计算重叠（P1）

#### R4.1 学习分预热与 ingest 重叠（P-PPF-06 · MF-04 · D4）

- 在 ingest 期间以**后台线程**批量跑 NIMA（torch 推理释放 GIL，可与 WebP 编码进程并存）：资产入库即入队，批大小沿用 `_ML_BATCH_SIZE=16`。
- **V1 只重叠、不换源（评审拍板）**：预热线程输入与现状完全一致（原图路径 + `_ML_INPUT_SIDE=512`），分数 bit 级一致、contentSig 缓存键不变——本项因此归 E-A 级严格等价。「输入源换派生图」**Park V2**。
- **资源治理**：预热线程设 torch 线程配额（`torch.set_num_threads`），避免与并行 ingest 池争核；配额与 worker 数联动（如 `max(1, cpu - workers - 1)` 上限 4）。
- 结果写入既有 contentSig 缓存（`phase9_aesthetic.json`），curate 的 `_stage_aesthetic_align` 命中缓存后不再现场推理。
- 配置开关：`aesthetic.warm_learned_on_ingest` 语义扩展为「重叠预热」；关闭时行为与现状一致。

### WS5 · 渐进产出（P2）

#### R5.1 预览先行（P-PPF-08 · D6）

- G1 确认/首屏预览仅依赖 800/1600 档 + 已完成的 curate 结构；`materialize_derivatives` 与 narrate 在预览可见后后台补齐。
- Studio 进度语义：预览就绪即报「可查看」，成品补齐后报「导出就绪」；书架卡片状态区分两态，且与预览页水印/徽标**一致**，禁止「预览可见但书架仍显示处理中」的分叉。
- **导出门控（评审拍板 D6）**：导出入口在预览先行期**不置灰不禁用**；点击后缺档触发同步物化，复用现有导出进度条（与 R2.2 fail-closed 同一机制）。与 [PRD-M14-shelf-save-longshot] 的导出就绪判定对齐。
- 阶段文案并入 `stage_hints.py` 体系，不新增文案面。
- **范围控制**：本项只做 Studio 主导入路径；CLI 保持一次跑全（`--progressive` 可选，Should-Fix）。

---

## 5. 交互与文案规格

本 PRD 主体为后端性能工作，UI 触点仅限 WS5 与降级提示：

| 场景 | 规格 |
|------|------|
| 预览先行（R5.1） | 进度阶段文案：「照片处理中…」→「版面已就绪，可先预览」→「高清图与导出准备完成」；并入 `stage_hints.py`，书架两态与预览页徽标一致 |
| 并行降级（R1.1） | 不打扰用户；仅遥测记录 fallback 原因。狗粮模式（内部）可在导入完成 hint 附「本次未并行（原因码）」 |
| 手动换片补图（R2.2 · MF-09） | 单张：按钮短暂 loading（≤3 s 预算），无额外弹窗；一次 >3 张：后台队列 + 「正在准备 N 张高清图」徽标，禁止长 loading 假死 |
| 导出前补图（R2.2 fail-closed · D6） | 导出入口**永不置灰**；缺档触发同步物化，复用现有导出进度条，不新增文案面 |

文案总则沿用项目惯例：无内部词、无假状态、不可感知的优化不做提示。

---

## 6. 技术实现要点

| 工作流 | 落点 | 备注 |
|--------|------|------|
| R1.1 并行修复 | `travelogue/web/studio_subprocess.py` · `studio_config.py` · `studio_pipeline.run_studio_pipeline` | MF-07：先写复现测试再修；根因报告 = M1 出口物 |
| R1.2 worker 上限 + 内存降额 | `travelogue/media/ingest_parallel.py` · `resolve_parallel_ingest_plan` | MF-05：降额公式 V1 落地 + `ingestWorkersDownscaled` 遥测 |
| R1.3 人脸降采样 | `travelogue/config/ingest.py` 默认值 + 独立 flag | 机制已在 `subject_detect._downscale_for_detect`；E-B 流程（MF-08） |
| R1.4 webp_method | `travelogue/config/ingest.py` + shadow-diff 脚本 + 独立 flag | 体积预算断言；E-B 流程 |
| R2.1/R2.2 分层派生 | `image_ops.export_webp_variants` 加 `widths` 子集调用 · 新模块 `travelogue/media/derivatives.py`（物化队列+幂等） · `derivedPlan` 进 `schemas/` | **不进** `stages_order`；lock_structure 后后台启动、render 前 join（D3）；`_missing_derivative_paths` 语义升级为「按需物化」而非报错 |
| R2.3 金字塔 | `image_ops.export_webp_variants` | 独立 flag **默认关**，SSIM 报告后再开 |
| R3.1 扫描 | `media/ingest.py:scan_image_paths` · `media/user_tier.py:scan_tiered_image_paths` | orientation 交换宽高 |
| R3.2 worker 内信号 | `media/ingest_worker.py` · `ingest_parallel._build_entry_from_worker_result` | WorkerResult 增字段，保持 pickle-safe |
| R4.1 NIMA 重叠 | `curation/photo_cull_ml.py` · 新 `curation/aesthetic_warm.py`（线程协调，参考 `vision/parallel_embed.ParallelEmbedCoordinator`） | 单例 metric、线程安全缓存写、torch 线程配额（MF-04） |
| R5.1 渐进 | `web/studio_pipeline.py` 切片顺序 · 书架状态 | M3；导出同步物化（D6） |
| QA | golden trip 双跑（等价性）· shadow-diff（SSIM）· pytest 故障注入 · Playwright 导入计时 | 新增 `scripts/perf_probe_*.py` 纳入回归基准（固定相册 + 机器指纹入验收记录） |

**依赖顺序**：R1.1 独立可先行；R2.2 依赖 R2.1；R4.1 与 R2.1 无强依赖（输入用原图，D4）；R5.1 依赖 R2.2。

---

## 7. 里程碑

| 里程碑 | 范围 | 出口 |
|--------|------|------|
| **M1（止血 · 修复+配置）** | R1.1 · R1.2 · R1.3 · R1.4 | AC-PPF-01～04 + **R1.1 根因报告**（MF-07）；250 张端到端 ≤12 min（基准机手动验收）；R1.3/R1.4 各自独立 flag 合入；可独立合入 |
| **M2（结构性 · 分层与去重）** | R2.1 · R2.2 · R2.3 · R3.1 · R3.2 · R4.1 | AC-PPF-05～10 + 07a CI 绿 + 07b 差异报告签字；250 张端到端 ≤5 min（基准机）；R2.3 flag 默认关不阻塞出口 |
| **M3（体验 · 渐进产出）** | R5.1 | AC-PPF-11 + 书架/预览两态一致性走查；首屏预览 ≤2.5 min |

每个里程碑合入前跑一次 §9 的性能基准与质量等价性双跑；E-B 项（R1.3/R1.4/R2.3）验证不达标可单项回退，不阻塞里程碑。

---

## 8. 遥测

- `pipeline.timings` 增补：`materializeMs`、`nimaWarmHits` / `nimaWarmMisses`、`scanMs`（扫描从 ingestMs 中拆出显示，Should-Fix）
- `ingestParallelFallback` + 原因码（期望长期为 0）；`ingestWorkersDownscaled` + 原因码（MF-05）
- `derivativesDeferredCount` / `derivativesOnDemandCount`（refine 换片触发的按需物化次数）
- `previewReadyMs`（M3：导入开始到预览可见）
- **相对回归护栏（MF-06）**：per-photo ingest ms 分位数入遥测，超阈值报警（非 CI 红灯）
- 复用 `~/.travelogue/telemetry` JSONL 通道，不新增采集面

---

## 9. 验收标准（AC-PPF-*）

| ID | 标准 | 验证 |
|----|------|------|
| **AC-PPF-01** | Studio 导入 ≥12 张照片时 `timings.ingestWorkers ≥ 2`；人为破坏配置时 fallback 原因码上报 | pytest + Playwright 导入 + trip.json 断言 |
| **AC-PPF-02** | 18 核机器 `workers=0` 自动解析为 9（`cpu//2`，上限 10）；显式配置优先 | pytest 单测 |
| **AC-PPF-03** | `face_detect_max_edge=1024` 下 ≥3 相册人脸检出差异 ≤2%、focal 偏移 ≤0.02；faces 分项耗时下降 ≥60% | 对比脚本 + `elapsedMs.faces` |
| **AC-PPF-04** | `webp_method=2`：同相册产物 SSIM ≥0.99、总体积增幅 ≤12%、`elapsedMs.webp` 下降 ≥50% | shadow-diff + 体积统计 |
| **AC-PPF-05** | ingest 后仅存在 800/1600 档文件且 srcset 只含已落盘条目（`derivedPlan` 记录计划档位）；curate+materialize 后入选资产四档齐全并回写 srcset、落选资产无 2400/3200 | 文件清单 + trip.json schema 断言 |
| **AC-PPF-06** | 导出物（ZIP/长图/present）中 srcset 引用的全部文件存在且分辨率合同不变；三个负例（MF-10）：人为删档后导出、物化中途 kill 后恢复、refine 换片并发导出——均不产出缺图导出物 | pytest 故障注入 + 导出校验 |
| **AC-PPF-07a** | **E-A 严格等价（CI 门禁）**：仅开启 E-A 项时 golden trip 双跑：cull 集合、章节结构、`screens[]` 指纹、封面选择、NIMA 分数逐字段一致 | 等价性脚本（沿用 `arch_equivalence_check` 模式）· CI |
| **AC-PPF-07b** | **E-B 受控差异（人工门禁）**：开启 E-B 项后 golden trip 双跑输出差异报告（选片/焦点/裁切变更清单 + 原因）；Q6 阈值达标；狗粮走查签字后方可改默认值 | 差异报告 + 验收记录 |
| **AC-PPF-08** | 扫描阶段无像素解码（探针断言 `exif_transpose` 未被调用）；竖拍照片 min-edge 判定仍正确 | pytest（含 orientation=6 样张） |
| **AC-PPF-09** | 并行模式主进程 merge 不再打开图片文件；`WorkerResult` 携带美学信号与 mediaClass，串行/并行结果逐字段一致 | pytest 双模式对比 |
| **AC-PPF-10** | NIMA 预热开启时 curate `_stage_aesthetic_align` 缓存命中率 ≥95%，curate 阶段无批量推理；分数与现状路径 **bit 级一致**（D4：同输入同缓存键）；预热线程 torch 线程数受配额约束 | pytest + timings |
| **AC-PPF-11** | 250 张真实相册：导入开始到预览可见 ≤2.5 min；预览期导出入口可点、缺档触发同步物化 + 进度条（D6）；书架与预览页两态一致 | Playwright 计时 + 状态走查 |
| **AC-PPF-12** | 性能总纲：250 张端到端 ≤5 min（M2 出口），100 张 ≤2.5 min；**基准机手动验收**（固定相册 + 机器指纹入验收记录），CI 不跑绝对时长（MF-06） | `scripts/perf_probe_pipeline.py` 扩展 |

**门禁（MF-01/06）**：AC-PPF-07a（E-A 严格等价）是所有 E-A 项合入的 CI 前置；E-B 项以 AC-PPF-07b 人工门禁放行。CI 只跑等价性、功能断言与相对回归护栏（遥测报警），绝对时长仅在基准机验收。

---

## 10. 风险与开放问题

| # | 项 | 状态 |
|---|-----|------|
| 1 | R1.1 根因未定位（demo 配置分支 vs 子进程配置解析） | **关闭（2026-07-19）**：主因是 `flush_timings` 整表覆盖抹掉 `ingestWorkers`（见 IMPLEMENTATION 摸底）；非配置未加载。已修 `absorb_pipeline_timing_keys` |
| 2 | 延迟物化与 refine 手动换片的竞态（用户换入未物化照片立即导出） | **关闭**：D6 同步物化 + MF-10 三个故障注入负例 |
| 3 | 金字塔缩放画质（逐级 LANCZOS 误差累积） | **关闭**：R2.3 flag 默认关，SSIM 报告后再开，不阻塞 M2 |
| 4 | NIMA 输入源改派生图导致分数漂移 → 影响选片 | **关闭**：D4 拍板 V1 只重叠不换源；换源 Park V2 |
| 5 | 并行 worker 内存峰值（36MP 相册 × 10 workers） | **关闭**：D5 升格为 V1 落地降额公式 + 遥测（MF-05） |
| 6 | `webp_method=2` 体积增幅在移动端分享场景的可接受度 | 预算 ≤12%；超限降级方案见 R1.4；狗粮期收集典型用户反馈 |
| 7 | Q1 严格等价与 R1.3/R1.4 参数变更的矛盾 | **关闭**：D1 等价性分级（E-A/E-B），07a/07b 分门禁 |
| 8 | libvips / GPU 编码等更激进方案 | **Park** → V2 候选，本包不引入新依赖 |
| 9 | Playwright 长图导出提速 | **Park** → 独立立项（浏览器池并行 tab） |
| 10 | NIMA 输入源换派生图（|Δscore|≤0.01 证明） | **Park** → V2 |

---

## 11. 变更记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-07-19 | 初稿 · 基于 2026-07-19 性能研究（真实 trip 埋点 + 微基准 + 串并行对比）· P-PPF-01～08 · WS1–WS5 · 质量红线 Q1–Q5 · AC-PPF-01～12 |
| v0.2 | 2026-07-19 | 评审回写 · D1–D6 拍板（等价性分级 / derivedPlan 合同 / materialize 与 narrate 并行 / NIMA 只重叠不换源 / 内存降额升格 V1 / 导出同步物化）· MF-01～10 · AC-PPF-07 拆分 07a/07b · 绝对时长退出 CI · 链到评审纪要 |
