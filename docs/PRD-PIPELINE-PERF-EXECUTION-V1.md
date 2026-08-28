# Travelogue · 流水线提速 V1 执行链收口（PRD）

| 属性 | 内容 |
|---|---|
| 文档编号 | PPX-PRD-001 |
| 版本 | v0.1.0 |
| 状态 | Draft · 待评审 |
| 优先级 | P0 |
| 主题代号 | Pipeline Perf Execution（PPX）— 兑现已设计的并行，而不是另开优化专项 |
| DOC-STATUS | proposed；审核通过前不写入 DOC-STATUS |
| 负责人建议 | Backend 1 · QA 1 · 架构复核 |
| 目标版本 | 下一次 Studio 导入体验收敛版本 |
| 关联文档 | [PRD-PIPELINE-PERF-V1.md](./PRD-PIPELINE-PERF-V1.md)（上游合同，不废止）· [IMPLEMENTATION-PIPELINE-PERF-V1.md](./IMPLEMENTATION-PIPELINE-PERF-V1.md) · [ACCEPTANCE-PIPELINE-PERF-V1.md](./ACCEPTANCE-PIPELINE-PERF-V1.md) · [PRD-PIPELINE-THROUGHPUT.md](./PRD-PIPELINE-THROUGHPUT.md) · [PRD-DESKTOP-INSTALLER-V1.md](./PRD-DESKTOP-INSTALLER-V1.md)（`freeze_support`）· [PRD-DUAL-PIPELINE-ISOLATION-V1.md](./PRD-DUAL-PIPELINE-ISOLATION-V1.md) |
| 实施清单 | [IMPLEMENTATION-PIPELINE-PERF-EXECUTION-V1.md](./IMPLEMENTATION-PIPELINE-PERF-EXECUTION-V1.md) |
| 验收 | [ACCEPTANCE-PIPELINE-PERF-EXECUTION-V1.md](./ACCEPTANCE-PIPELINE-PERF-EXECUTION-V1.md) |
| W0 基线 | [acceptance-records/ppx-w0-baseline-2026-08-28.md](./acceptance-records/ppx-w0-baseline-2026-08-28.md) |
| 复议 | 2026-08-28 架构与算法复议（工作区 canvas `travelogue-perf-architect-algorithm-advice-2026-08-28`）；**以本文为实施合同** |
| 真实实现锚点 | `travelogue/web/studio_subprocess.py` · `travelogue/media/ingest.py` · `travelogue/media/ingest_parallel.py` · `travelogue/media/derivatives.py` · `travelogue/orchestrator/run.py` |
| 更新日期 | 2026-08-28 |

> 一句话目标：当 `pipeline.parallel_ingest=true` 时，Studio 真导入路径必须真正并行；高清物化必须按资产并行且不改坏 trip；失败对用户可回退、对遥测和 CI 不可静默。

---

## 0. 定位与边界

本 PRD **不是** Pipeline Perf V2，也不废止 V1。

V1 已交付并合入：延迟物化、`derivedPlan` 合同、扫描 peek、worker 内信号、timings 吸收、长边档位表。这些合同继续有效。

V1 在 2026-07-19 把 R1.1 根因写成「`flush_timings` 整表覆盖抹掉 `ingestWorkers`」。吸收键修好了证据链。2026-08-24 至 08-28 的 5 个完成相册全部是 `ingestWorkers=1` 且 `ingestParallelFallback=1`，证明 **Studio 执行链仍未兑现并行**。

本波只收口「已设计、已标完成、实际未生效」的执行链。

| 仍以 V1 为准 | 本波新冻结 |
|---|---|
| E-A / E-B 等价性分级（D1） | 进程树与取消回收合同 |
| `srcset` 只登记已落盘文件（D2） | 结构化并行结果 + 滑窗合并 |
| 物化不进公开状态机（D3） | 物化禁止后台线程改 trip |
| NIMA 只重叠不换源（D4） | 共享 RAM 预算（长边表不够） |
| 导出同步物化（D6） | 性能门禁按分辨率分档 |
| 绝对时长不进 CI（MF-06） | WebP 不用文件 hash 做等价 |

### 0.1 非目标

- 不另立「性能优化 V2」专项，不改 MCS / beam / cull 阈值 / 模板数量。
- 不引入 GPU、不更换编码库（libvips Park）。
- 不把 `pipeline.parallel_ingest` 产品默认改为 `true`。默认值保持现状（`PipelineConfig` 默认 `false`）；本波只保证 **flag 为 true 时真的并行**。
- 不把 ProcessPool 上提进 Studio HTTP 主进程。
- 本期不实施长图 / 拼图 / 三表面去重（M2 只冻结设计，见 §8）。
- 不新增公开 pipeline 状态，不改 `stages_order`。
- 不在共享模块里加 `is_portfolio` / edition 分支（DPI：ingest / derivatives / orchestrator 未登记，新标记会触发棘轮）。

---

## 1. 问题与证据

### 1.1 真实时间花在哪

来源：工作区 `trips/*/trip.json`，2026-08-24 至 2026-08-28 的 5 个 `rendered/exported` 运行，按阶段耗时加权。明细见 W0 基线。

| 阶段 | 占比 |
|---|---|
| ingest | 51.0% |
| 高清物化 | 34.5% |
| curate | 8.6% |
| render | 3.3% |
| embed | 2.5% |
| cluster | 0.1% |

ingest + 物化合计 **85.5%**。5/5 运行 `workers=1 / fallback=1`。

### 1.2 根因（本波定稿，取代 V1 §10 风险 1 的关闭结论）

| ID | 问题 | 证据 |
|---|---|---|
| **P-PPX-01** | Studio 导入进程是 daemon，内部无法再开 ProcessPool | `ImportSubprocess` 显式 `daemon=True`（`studio_subprocess.py`）。Windows/spawn 下 daemon 进程不能创建子进程。 |
| **P-PPX-02** | 并行失败被吞成串行，用户看见成功 | `run_parallel_ingest_loop` 启动异常返回 `False`；`ingest.py` 设 `fallback=true` 后走串行。无 `reason`。 |
| **P-PPX-03** | 现有 Windows spawn 测试假绿 | `tests/integration/test_pt_ingest_windows_spawn.py` 直接调 `ingest_into_trip`，断言 `workers >= 1`，允许 fail-open。不经过 `ImportSubprocess.start()`。 |
| **P-PPX-04** | 高清物化只是后台串行 | `ensure_derivatives_for_trip` 逐资产 for 循环；`DerivativeMaterializer` 单 daemon 线程。stub narrate 几乎无重叠收益。 |
| **P-PPX-05** | 物化线程就地改 trip | 后台 `ensure_derivatives_for_trip(trip)` 与主线程 narrate / lock_copy 并发写同一 dict。render 前又 `save` → `load` → 再同步物化一次。 |
| **P-PPX-06** | 内存护栏空转 | `resolve_parallel_ingest_plan` 支持 `median_long_edge_px`，`ingest_into_trip` 未传。未知分辨率走 10 workers。扫描已有 `peek_image_meta`（无像素解码）。 |
| **P-PPX-07** | 有序合并等齐才 commit | `as_completed` 收齐全部 `WorkerResult` 后再按序号重放。首次进度 = 最后一张完成；峰值内存 = 全批次结果。 |
| **P-PPX-08** | V1 杀伤测试合同被现网测试架空 | V1 AC-PPF-01 要求 Studio ≥12 张 `ingestWorkers≥2`。合入时以单测 + 遥测吸收替代，未覆盖 daemon 嵌套。 |

7 月同机 4-worker 探针是 **1.47×（降 32%）**，8-worker 是 **2.13×（降 53%）**，不是「4-worker 降 60%」。延迟物化之后 ingest 不再编 2400/3200，剩余加速比不会自动变好。高分相册长边护栏会把 workers 压到 4。

---

## 2. 目标与成功指标

### 2.1 目标

| ID | 目标 |
|---|---|
| **G-PPX-01** | `parallel_ingest=true` 且照片数 ≥ `min_photos` 时，经 `ImportSubprocess.start()` 的 Studio 导入 `ingestWorkers>1` 且 `fallback=0` |
| **G-PPX-02** | 并行失败必须带 `ingestParallelFallbackReason`；用户路径可 fail-open 串行，CI / 狗粮杀伤测试把 fallback 当失败 |
| **G-PPX-03** | 取消导入后无孤儿 worker、无残留 `.ingest-partial` / 物化临时目录 |
| **G-PPX-04** | 高清物化按资产并行；worker 不改 trip；主进程按资产顺序合并 `srcset` / `derivedPlan` 后一次持久化 |
| **G-PPX-05** | 扫描 peek 的长边中位数进入 worker 规划；RAM 预算与长边档位同时生效；未知分辨率不得按 10 workers 起步 |
| **G-PPX-06** | 选片、章节、screens、srcset 宽度集合、像素尺寸、quality 与现状严格等价（E-A） |

### 2.2 成功指标（分档，禁止单一乐观门禁）

绝对毫秒只做本机基准。CI 只跑调用次数、并发状态、产物等价。

| 档 | 适用 | ingest | 物化 | 端到端中位（相对本波 W0 同机） |
|---|---|---|---|---|
| **高分 4w** | 中位长边 ≥7000px，或 RAM 预算压到 4 | ≥1.4× 串行 | ≥2.2× 串行 | ≥30% |
| **中分 8w** | 中位长边 ≤3500px 且 RAM 允许 8 | ≥1.8× 串行 | ≥2.5× 串行 | ≥35% |
| **只修 daemon、合并仍等齐** | 不可接受 | — | — | 估测约 22%，本波出口必须超过此档 |

样本冻结：31 / 57 / 121 / 134 张四档；每档 cold/warm 各 3 次。W0 已登记 5 个现网 trip 的绝对秒数，只作对照，不作 CI 红灯。

---

## 3. 拍板决策

| 决策 | 结论 |
|---|---|
| **D-PPX-01 立项性质** | V1 执行链收口。标题与排期不得写成新优化专项。 |
| **D-PPX-02 进程树** | 保留 `ImportSubprocess` 作为导入隔离边界。改为非 daemon。它是唯一的 ProcessPool 主人。禁止把池上提进 Flask 主进程。池必须使用与导入进程相同的 `spawn` 上下文。 |
| **D-PPX-03 取消** | 协议：cooperative Event → `pool.shutdown(wait=False, cancel_futures=True)` → join 超时 → 再终止导入进程，并枚举/回收其直接子进程。禁止只 `terminate()` 父进程。Windows 优先 Job Object；若本波不加新依赖，至少用进程枚举回收孙子。 |
| **D-PPX-04 失败语义** | 用户路径保持 fail-open 串行（V1 Q5）。遥测必须有 reason。Studio 狗粮 hint 可附原因码，终端用户不打扰。CI 杀伤测试与「并行可达」门禁把 fallback 当失败。 |
| **D-PPX-05 结构化结果** | `run_parallel_ingest_loop` 不得只返回 `bool`。返回成功 / 失败原因 / requestedWorkers / effectiveWorkers / spawnMs / firstProgressMs。 |
| **D-PPX-06 滑窗合并** | watermark：完成即入缓冲，连续序号立刻 commit。在飞任务上限 = workers。禁止收齐全部结果再重放。 |
| **D-PPX-07 长边来源** | 使用扫描阶段已有的 `peek_image_meta`（无像素解码）。`scan_stats` 写 `medianLongEdgePx`，传入 `resolve_parallel_ingest_plan`。禁止为护栏再全量解码。 |
| **D-PPX-08 RAM 预算** | 抽共享函数，ingest 与 materialize 复用。`workers = min(cpu_cap, long_edge_cap, ram_cap)`。浏览器预留 1.5GB。检测失败时未知分辨率上限从 10 降为 **6**。不新增 `psutil` 依赖（ctypes / `os.sysconf`）。 |
| **D-PPX-09 物化并行** | 按资产并行，不按宽度并行。worker 解码一次，写缺失的 2400/3200 到临时文件并返回元数据。主进程合并。禁止线程或子进程改 trip dict。 |
| **D-PPX-10 等价门** | E-A 锁选片集合、章节、screens、srcset 宽度集合、像素尺寸、`webp_quality`。WebP **禁止**全量文件 hash。体积走带宽；画质用抽样 SSIM / phash。 |
| **D-PPX-11 默认 flag** | 本波不改 `parallel_ingest` 产品默认。吞吐示例与本机狗粮可继续显式打开。默认改 true 必须另过评审，且本波 AC-PPX-01 / 03 / 08 全绿。 |
| **D-PPX-12 M2** | 长图 / 拼图 / 批量导出只批准技术方案（§8），本波不开工。 |
| **D-PPX-13 池复用** | ingest 与 materialize 若落在同一导入进程生命周期内，优先复用同一池或保持池热，避免各开一次 Windows spawn 冷启动把 4-worker 红利吃掉。 |

---

## 4. 需求

### 4.1 M0 · 可观测性与杀伤测试（不改产物）

#### R-PPX-01 分段埋点

在既有 `pipeline.timings` / ingest stats 上增加（类型进 `trip_telemetry.py`，经 `absorb_pipeline_timing_keys` 保留）：

| 键 | 含义 |
|---|---|
| `ingestParallelFallbackReason` | 空或原因码，见 §6 |
| `ingestWorkersRequested` / `ingestWorkers` | 规划值 / 生效值 |
| `ingestPoolSpawnMs` / `ingestFirstProgressMs` | 池启动、首次 commit 进度 |
| `ingestMedianLongEdgePx` / `ingestWorkersDownscaled` | 护栏输入与是否降额 |
| `materializeWorkers` / `materializeAssets` | 物化并发与资产数 |
| `materializeDecodeMs` / `materializeEncodeMs` | 可加总的分段 |
| `peakRssMb` | 导入进程峰值 RSS（能取则取） |

CI 不跑绝对时长。相对回归只报警。

#### R-PPX-02 杀伤测试（M0 出口，先红后绿）

必须新增、且不得被现有 spawn smoke 替代：

1. **单元合同**：`ImportSubprocess` 创建的进程 `daemon is False`；`cancel()` 在未 start 时安全。
2. **集成杀伤**：经 `ImportSubprocess.start()` 导入 ≥12 张（可用合成 JPEG），`parallel_ingest=true`，断言 `ingestWorkers>1` 且 `fallback=0`。Windows 必跑；其他 OS 同样有效。
3. **现网测试降级**：`test_pt_ingest_process_pool_spawn_smoke` 不得再把 `workers>=1` 或 fail-open 写成成功。保留「不崩溃」断言，并行可达改由本条负责。

无 2 即视为 V1 假关重演。M1 编码不得在 2 变绿之前合入。

### 4.2 M1 · 兑现并行

#### R-PPX-03 进程契约

- `ImportSubprocess`：`daemon=False`；`mp.get_context("spawn")`。
- 导入进程退出前必须 join 池。
- Studio 主进程退出时必须 join / 回收导入进程（非 daemon 后不再随父进程自动死）。
- frozen onedir 继续走已有 `freeze_support()`（`travelogue/__main__.py` · `desktop/launcher.py`）。本波加一条 onedir 备注到验收，不重做安装器。

#### R-PPX-04 取消与孤儿

- 把已有 `_cancel` Event 传入并行 ingest / 物化循环，协作停提交。
- 实现 D-PPX-03。超时阈值写入 IMPLEMENTATION（建议 pool join 5s，导入进程 join 8s）。
- 临时目录 `.ingest-partial/<batch>` 与物化临时根必须在 cancel / 失败路径删除。
- 断点恢复不重复 `assetId`，不留下半成品 srcset 条目（V1 D2）。

#### R-PPX-05 结构化结果 + 滑窗

- 实现 D-PPX-05 / D-PPX-06。
- `firstProgressMs` 必须在第一张连续序号 commit 时打点，不得等全批次。
- 进度回调与今日串行路径同一套 `on_progress` / Studio stage hint，不新增文案面。

#### R-PPX-06 护栏传参 + 共享 RAM 预算

- 实现 D-PPX-07 / D-PPX-08。
- 长边档位表保留：≥7000→4，≥5000→6，≥3500→8，否则 10，再与 RAM 取 min。
- 36MP 故障样本：自动降额，无 OOM，无孤儿。
- 降额原因码写入遥测：`memory_cap_long_edge` / `memory_cap_ram` / `memory_cap_unknown_edge`。

#### R-PPX-07 并行物化

- 实现 D-PPX-09。
- 入选资产缺档才进池；已齐档幂等跳过（现 `missing_planned_widths`）。
- `DerivativeMaterializer.join` 只回收元数据；主线程合并后 `save`。orchestrator 同步 `ensure_derivatives_for_trip` 在后台已齐档时必须空转（`widths_written=0`）。
- refine 换片、导出同步物化仍走 V1 D6 / MF-09 / MF-10，可复用同一有界池。

### 4.3 明确不做（本波）

| 项 | 去向 |
|---|---|
| 长图一次解码 / 避免 recapture | §8 设计，M2 |
| 拼图输入档位选择 + 页并行 | §8 设计，M2 |
| 批量平台 capture signature | §8 设计，M2 |
| 三表面模板缓存 | Park |
| exact-duplicate 提前短路 | 仅当 M1 后遥测证明重复率高 |
| 改 `parallel_ingest` 默认 true | D-PPX-11 |
| MCS / beam / GPU / libvips | 禁止 |

---

## 5. 交互与文案

本波几乎无 UI。沿用 V1 §5 与 [COPY-DICTIONARY-V1](./COPY-DICTIONARY-V1.md)：

| 场景 | 规格 |
|---|---|
| 并行降级 | 终端用户不打扰。狗粮 / 内部 hint 可附「本次未并行（原因码）」 |
| 导入取消 | 复用现有「已取消」语义，不新造词 |
| 物化等待 | 不新增公开阶段。导出缺档仍走现有进度条（V1 D6） |
| 禁词 | 不对用户说 worker、daemon、ProcessPool、srcset、物化 |

---

## 6. 原因码

| 码 | 何时 |
|---|---|
| `pool_daemon_nested` | 历史：daemon 中无法开池（修复后不应再出现；出现即回归） |
| `pool_start_failed` | 池启动异常（含 spawn / frozen） |
| `pool_cancelled` | 用户取消 |
| `below_min_photos` | 照片数 < `parallel_ingest_min_photos`（不算故障，`fallback` 可为 true 但 reason 分开） |
| `workers_eq_one` | 规划后 workers≤1 |
| `flag_off` | `parallel_ingest=false`（不写 fallback，或写但不进杀伤失败集） |
| `memory_cap_long_edge` | 长边降额（降额不是 fallback） |
| `memory_cap_ram` | RAM 降额 |
| `memory_cap_unknown_edge` | 无长边时走保守上限 6 |

`below_min_photos` 与 `flag_off` **不是** AC-PPX-01 失败。`pool_*` 与「本应并行却 workers=1」才是。

---

## 7. 技术落点与依赖顺序

| 需求 | 主落点 | 备注 |
|---|---|---|
| R-PPX-01 | `types/trip_telemetry.py` · `ingest.py` · `derivatives.py` · `pipeline_view.py` | 新键必须能被 absorb，防止再被整表覆盖 |
| R-PPX-02 | `tests/unit/web/test_studio_subprocess.py` · 新 `tests/integration/studio/test_import_subprocess_parallel.py` | 必须 `start()` |
| R-PPX-03/04 | `web/studio_subprocess.py` · `web/studio_jobs.py` | 取消与主进程退出回收 |
| R-PPX-05 | `media/ingest_parallel.py` · `media/ingest.py` | 结构化结果 + watermark |
| R-PPX-06 | `ingest_parallel.py` · `user_tier.py` / `ingest.py` scan_stats | peek 中位数；共享预算函数可放 `ingest_parallel.py` |
| R-PPX-07 | `media/derivatives.py` · `orchestrator/run.py` | 主进程合并；同步路径空转 |

**依赖**：R-PPX-02 测试先红 → R-PPX-03 变绿 → R-PPX-05/06 → R-PPX-07。R-PPX-01 可与 03 并行，但 07 合入前埋点必须能区分串行/并行物化。

**DPI**：`studio_subprocess.py` 属 shared shell。其余目标文件未登记，禁止新增强制 edition 分支。

---

## 8. M2 技术方案（本波只批设计，不开工）

冻结意图，防止 M1 之后散打：

1. **长图**：整幅 canvas 只解码一次；按 ranges 内存裁切；20MB 用未压缩上界或**一次**编码判断；能避免 Playwright recapture 优先于少一次 PNG save。超限降 scale 才允许重拍。
2. **拼图**：先做「所需长边 × 1.25 选 srcset」+ 抽样 SSIM 门；未过门回退 `sourceFile`。页面并行是第二步，2–4 worker，主线程提交顺序。禁止 8K × 多页同时解码。
3. **批量平台**：按 capture signature（页面状态、copyDisplay、scale、format、appendix）分组；同签名只打开一次页面、捕获一次整图。不盲目多开 Playwright 页。

M2 开工前提：M1 AC-PPX-01/03/07/08 绿，且 M0 分段里能看见 capture / slice / encode。

---

## 9. 验收标准（AC-PPX-*）

| ID | 标准 | 验证 | 里程碑 |
|---|---|---|---|
| **AC-PPX-01** | 经 `ImportSubprocess.start()`，≥12 张，`parallel_ingest=true` → `ingestWorkers>1` 且 `fallback=0` | 新集成测试；Windows 必跑 | M0/M1 |
| **AC-PPX-02** | 池启动失败有 reason；不得只返回 False | 单测注入 | M1 |
| **AC-PPX-03** | 取消后无残留 worker / 临时目录；导入进程与直接子进程退出 | 单测 + Windows 手工抽检 | M1 |
| **AC-PPX-04** | `scan_stats.medianLongEdgePx` 传入规划；7360 中位 → workers≤4 | 单测（扩 `test_parallel_ingest_workers.py`） | M1 |
| **AC-PPX-05** | 未知长边 workers≤6；RAM 预算可把 10 压到更低 | 单测 mock 可用内存 | M1 |
| **AC-PPX-06** | 滑窗：第一张完成后 `firstProgressMs` 已写出，不必等全批次 | 单测 fake pool | M1 |
| **AC-PPX-07** | 物化 worker 不改传入 trip；主进程合并后 srcset 宽度集合与串行一致 | 单测 | M1 |
| **AC-PPX-08** | 36MP 样本无 OOM、无孤儿；降额遥测出现 | 基准机 / 故障夹具 | M1 |
| **AC-PPX-09** | E-A：cull 集合、章节、screens、封面、srcset 宽度与尺寸一致；WebP 不用 hash | 沿用 `pipeline_perf_equivalence_check.py` | M1 |
| **AC-PPX-10** | 高分档 ingest ≥1.4×、物化 ≥2.2×、121/134 张 E2E 中位 ≥30%；中分档另记 | 基准机；写入验收记录 | M1 |
| **AC-PPX-11** | orchestrator 后台已齐档时同步物化 `widths_written=0` | 单测 | M1 |
| **AC-PPX-12** | `test_pt_ingest_windows_spawn` 不再把 fail-open 写成并行成功 | 改断言后 CI | M0 |

门禁：AC-PPX-01 / 03 / 09 是合入主分支的硬门。AC-PPX-10 是基准机人工门。绝对时长不进 CI。

---

## 10. 风险

| ID | 风险 | 缓解 |
|---|---|---|
| **R-PPX-R01** | `daemon=False` 后只改一行，取消留下孤儿 | AC-PPX-03 与 01 同级 |
| **R-PPX-R02** | Windows spawn 冷启动吃掉 4-worker 收益 | D-PPX-13；`poolSpawnMs` 可见 |
| **R-PPX-R03** | 修并行后 10 workers × 36MP OOM | D-PPX-08；未知边上限 6 |
| **R-PPX-R04** | WebP hash 门禁卡死合入 | D-PPX-10 |
| **R-PPX-R05** | 再次用「直接调 ingest」测试假绿 | AC-PPX-01 / 12 |
| **R-PPX-R06** | 后台物化与同步路径双工重做或半成品 srcset | AC-PPX-07 / 11 |
| **R-PPX-R07** | 把本波做成 V2 大而全 | D-PPX-01 / 12；M2 不开工 |

---

## 11. 里程碑

| 里程碑 | 范围 | 出口 | 估时 |
|---|---|---|---|
| **M0** | R-PPX-01 埋点骨架 + R-PPX-02 杀伤测试（先红）+ W0 基线入仓 | AC-PPX-12；杀伤测试存在且红在 daemon | 0.5–1 人日 |
| **M1** | R-PPX-03～07 | AC-PPX-01～09、11 绿；AC-PPX-10 基准机记录 | 3–5 人日 |
| **M2** | §8 仅设计 | 本文已冻结；不排期 | 0 |
| **M3** | 三表面缓存 / curate 分段 | Park；M1 后若 121/134 仍慢再立项 | — |

---

## 12. 变更记录

| 版本 | 日期 | 变更 |
|---|---|---|
| v0.1.0 | 2026-08-28 | 初稿。基于 08-28 只读审计与架构/算法复议。重开 V1 R1.1 执行链；冻结 D-PPX-01～13。 |
