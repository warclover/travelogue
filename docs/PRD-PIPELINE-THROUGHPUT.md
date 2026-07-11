# Travelogue · 管线吞吐加速 PRD（Pipeline Throughput）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue（核心管线 + Studio） |
| **文档版本** | **v0.3.0-THROUGHPUT** |
| **状态** | **Approved · 分闸实施（Phase A 可 Kickoff）** |
| **代号** | 「吞吐加速」— 不砍流程 · 先能力后默认 · 正确性优先于刷分 |
| **评审纪要** | [pipeline-throughput-prd-review-2026-07-11.md](./acceptance-records/pipeline-throughput-prd-review-2026-07-11.md) |
| **前置条件** | Phase 7 主线已合入；`TripService.update` + `meta.revision` CAS 已落地；`trip.pipeline.timings` 可观测 |
| **交付形态** | 在 **不删除、不跳过任何既有管线阶段** 的前提下，缩短全量生成 wall-clock；建立相对 P7 的吞吐 KPI（门槛/stretch 双轨）与 NR-PT 等价回归；**功能合入与默认开启分闸** |
| **关联文档** | [PRD-PHASE7.md](./PRD-PHASE7.md) · [TECH-ARCHITECTURE.md](./TECH-ARCHITECTURE.md) §17 / §17.7 · [adr/008-trip-storage-boundaries.md](./adr/008-trip-storage-boundaries.md) §9 · [PRD-PHASE22-storage-platform.md](./PRD-PHASE22-storage-platform.md) · [PRD-ARCH-OPTIMIZATION.md](./PRD-ARCH-OPTIMIZATION.md) |
| **实施清单** | [IMPLEMENTATION-PIPELINE-THROUGHPUT.md](./IMPLEMENTATION-PIPELINE-THROUGHPUT.md) |
| **更新日期** | 2026-07-11 |

> **定位说明**
>
> - Phase 7 解决了 CLIP 批量化、ingest∥embed、layout 签名短路、cache ABI。
> - 本 PRD 解决 P7 之后仍主导 wall-clock 的两类 **结构性串行**：① ingest **逐张** decode/WebP；② narrate **逐章** LLM。
> - **硬约束**：阶段集合与顺序不变；只改阶段内部执行方式与跨阶段重叠。
> - 与 Phase 22「增量 skip」正交：P22 跳过未脏阶段；本 PRD 把 **必须全跑** 跑得更快。P22 **不计入** G-PT-01。
> - **项目定性**：本项是 **数据正确性 + 写安全加固** 项目，附带性能收益；**不是**「性能周末」或降质换速运动。
> - **v0.2**：四方评审闭合（两阶段协议、NR 分层、KPI 双轨、D-PT-11…16）。
> - **v0.3**：吸收开发风险评审与项目总监批复——分闸 Go、Phase A/B/C、产品可感知验收、风险红线、生成体验组合对齐。

---

## 0. 文档说明

### 0.1 为何现在做

Studio 经验估算（`travelogue/web/studio_stages.py`）仍为：50 张约 3–5 分钟、100 张约 5–8 分钟、200 张约 8–15 分钟；LLM narrate 单独约 30–60 秒。P7 吃掉 CLIP/微优化红利后，剩余 gap 主要来自未并行的 CPU 阶段与未并发的 LLM 阶段。

### 0.2 范围承诺

| 承诺 | 说明 |
|------|------|
| **阶段不删减** | 不移除 ingest / clustering / curate / narrate / render / export；不默认关闭 vision / 去重 / cull |
| **语义可守护** | 固定 seed + NR-PT profile 下，产物满足 §9 |
| **可开关可回滚** | 独立 config flag；失败 fail-open；**功能合入 ≠ 默认开启** |
| **可度量** | 合并前附 before/after；写入 `docs/acceptance-records/pipeline-throughput-perf-eval.json` |

### 0.3 与相邻 PRD 的边界

| 文档 | 关系 |
|------|------|
| **PRD-PHASE7** | 前置；不重复实现 batch CLIP。W3 仅做预检 warning + 遥测（Studio 默认已开 P7 快路径） |
| **PRD-PHASE22** | W1/W2 **零依赖** P22；W3 可选对接且 **不计入** G-PT-01/02/03 |
| **PRD-ARCH-OPTIMIZATION** | CAS 已落地；本 PRD 依赖其写模型，并扩展并行 persist 压测（AC-ARC-02-parallel） |
| **PRD-COPY / Phase 11** | 只改 LLM 调度；不改 prompt 语义与 `NarrateError` 失败语义 |
| **生成体验组合** | 「首次全量加速」（本 PRD）与「二次增量重跑」（P22）、「早期可预览」（Studio/G1 体验，另项）共同构成等待体感；**KPI 与排期分开**，本 PRD 不冒充解决重跑痛（见 §15） |

### 0.4 项目批复（总监 · 2026-07-11）

| 项 | 批复 |
|----|------|
| **是否实施** | **建议实施（有条件 Go）** |
| **实施方式** | **分闸**：先合入加速能力（默认 off）→ 再独立决策默认开启；先 ingest 正确性 → 后 narrate 并发 |
| **批准预算** | **Phase A ≈ 8–12 人日**（M0 + M1 + merge mutator + 结构 NR + 本机门槛采数）；全量上限 **14–20 人日**（含 M2/M3/M5）；**不预支** M4（P22） |
| **红线** | ① 结构/dedupe 不等价 → 不得默认开；② merge mutator 未完成 → 不得 G1；③ 不得把 P22 / 降 beam / 关 vision 算进「变快」；④ 质量事故优先级 **高于** 速度收益 |
| **管理原则** | 批准的是 **能力**，慎批 **默认**；达不到 stretch 可上线能力，**达不到「不变差」则停** |

三道独立决策（禁止捆成一个 Go）：

| 决策 | 建议 |
|------|------|
| 合入加速能力（flag 默认 off） | **Go（Phase A/B）** |
| Studio 默认 `parallel_ingest=true` | **有条件 Go（G1）**：结构 NR + merge 压测 + Windows 烟测 + 门槛 KPI |
| 默认 `narrate_concurrency≥2` | **更晚（G2）**：限流与文案稳定性验证后 |

---

## 1. 背景与问题陈述

### 1.1 管线阶段与耗时画像

| 阶段 | 代码锚点 | P7 后剩余形态 |
|------|----------|---------------|
| **ingest** | `media/ingest.py` · `_process_one_ingest_photo` · 逐张 for | CPU/I/O 密集，仍顺序 |
| **clustering** | `curation/clustering.py` · `vision/parallel_embed.py` | 可与 ingest 重叠；cache 命中后常非瓶颈 |
| **curate** | `curation/curate.py` | SearchBudget 可控 |
| **narrate** | `services/llm_narrate.py` · 逐章 for | 网络串行，章数↑线性变慢 |
| **render / export** | `render/engine.py` · `export/packager.py` | 通常非主瓶颈 |

计时：`trip.pipeline.timings`（含本 PRD 增补字段，见 §8.2）。

### 1.2 断裂点

| ID | 断裂 | 本 PRD 目标 |
|----|------|-------------|
| **PT-A** | Ingest 逐张串行 | ProcessPool 并行 decode/特征/WebP；主进程有序 dedupe + 单写者 |
| **PT-B** | Narrate 逐章串行 | meta 先行；章级 semaphore 并发；有序 apply |
| **PT-C** | P7 快路径「以为开了其实没开」 | 预检 warning + 遥测（非「打开默认」） |
| **PT-D** | 重跑重复劳动 | cache 命中加固；可选对接 P22 |
| **PT-E** | 吞吐不可运营 | PT perf-eval + gate；默认开 flag 机器门禁 |

### 1.3 优化原则（硬约束）

1. **流程完整优先**：禁止用关阶段/降 beam 换速度作为 Studio 默认。
2. **效果等价优先**：NR-PT 分层守护（§9）。
3. **Fail-open**：并行异常 → 串行慢路径；不写半残 trip。
4. **单写者持久化**：Worker 只产 Blob/中间结果；Document 仅主进程经 `TripService.update`（增量 merge）。
5. **可开关、可回滚**；删除 DoD 对齐 ARCH-OPT §3.3（D-PT-13）。
6. **不测的不算**；**未达门槛 KPI 不得默认开 flag**（功能路径可合入）。
7. **正确性优先于刷分**：并行化按「数据正确性变更」管理（算法夹具、CAS 压测、NR 与功能同权）；禁止先并行、后补测试。
8. **能力与默认分闸**：合入加速路径 ≠ 产品默认开启（吸取 P7 perf AC 可红着合代码的教训）。

---

## 2. 目标与非目标

### 2.1 产品目标（KPI 双轨 + 可感知验收）

| ID | 目标 | 门槛（默认开硬闸） | Stretch |
|----|------|-------------------|---------|
| **G-PT-01** | e2e wall-clock | 100 张 **−18%**；250 张 **−22%**（相对本机 P7 快路径基线） | −25% / −30% |
| **G-PT-02** | ingestMs | 100/250 张 **−25%** vs 同机串行 | −35% |
| **G-PT-03** | narrateMs | ≥6 章真实 LLM cache miss **−30%**（concurrency=2 起量）；限流地板 **−20%**（须 `backoffCount≥1`） | −40% @c=3 |
| **G-PT-04** | 阶段集合不变 | telemetry 含 ingest→cluster→curate→narrate→render | — |
| **G-PT-05** | 质量零退化 | NR-PT 全项通过 | — |
| **G-PT-06** | 确定性 | fixed fixture 结构 100%；真实 trip ≥95% | — |
| **G-PT-07** | 可观测 | timings 增补 §8.2 字段 | — |
| **G-PT-08** | P7 快路径可观测 | import 前可 warning「性能配置未对齐」 | — |
| **G-PT-09** | 故障可恢复 | resume / 无半写入；孤儿 WebP 可清理 | — |
| **G-PT-10** | narrate cache 重跑 | 同 brief hit ≥95%，`narrateMs` **−80%** | — |
| **G-PT-11** | 可感知等待改善 | 100 张 dogfood：墙钟相对现状有 **可感知缩短**；进度单调不回跳；用户不认为「少做了某步」 | — |
| **G-PT-12** | 同册无「咦变了」 | 同相册 flag on/off：选图/章节结构无主观「版式变了」；结构 NR + 人工抽检签字入库 | **高于** stretch：不过则停默认开 |

内存：S2 峰值 RSS 退化 **≤+30%**（250 张）；S1 `workers=2` 单列记录。

**解释权**：ms 门槛服务工程放量；**G-PT-12 否决权高于 G-PT-01 stretch**。达不到 stretch 可保留能力（默认 off）；达不到 G-PT-05/12 则回滚或保持默认 off。

### 2.2 非目标

- 不删除或默认跳过任一管线阶段。
- 不降低 beam / SearchBudget / 关 vision 换速度（demo 除外）。
- 不改隐私模型；不强制云端推理。
- 不在本 PRD 重做 P22 / 不改 `NarrateError` 语义为单章 skip。
- 不以 streaming 首 token 计入 G-PT-01。
- 不以 stub provider 作为正式加速手段。
- **不**在吞吐窗口内大重构整个 ingest（只允许两阶段拆分所需的最小切开）。
- **不**引入第三套生产并行模型（ThreadPool 仅 benchmark）。
- **不**把「早期可预览 / G1 草稿体验」算作本 PRD 交付（见 §15，另项排期）。
- **不**用本 PRD 的 e2e 数字冒充「改一字重跑变快」（属 P22）。

---

## 3. 已拍板决策（D-PT）

| ID | 决策 | 结论 |
|----|------|------|
| **D-PT-01** | Ingest 并行模型 | 生产路径 **仅 ProcessPool**；`workers=1` 或 `<min_photos` → 现行串行。ThreadPool **只许** benchmark A/B。Studio 子进程内嵌套 spawn：提高 `min_photos` 或降 workers |
| **D-PT-02** | 合并写 | Worker **禁写** trip.json、**禁分配最终 assetId**；主进程按输入序（`sourcePath`/既有排序键）重放 dedupe 状态机后再 `_next_asset_id` |
| **D-PT-03** | persist | `persist_every_n` 默认 8；mutator = **增量 merge**（assets / ingest 统计 / checkpoint）；禁止整 trip 覆盖。checkpoint 频率可与 persist 解耦 |
| **D-PT-04** | Narrate 并发 | meta 串行 → chapters semaphore 并发；默认 S2 **concurrency=2**（dogfood 稳定后再 3）；S1=2；可配 1–8 |
| **D-PT-05** | 应用顺序 | 并发取回后按 **chapter index 升序** apply；禁止完成即 apply |
| **D-PT-06** | 失败语义 | **保持现行**：章级重试耗尽 → `NarrateError` **整段失败**。不引入「单章 skip」 |
| **D-PT-07** | 等价性分层 | 见 §9：L-struct 100%；L-embed 在 NR profile（`prefer_web_derivative=false` 或源图）100%；L-bytes 不比；真 LLM 不比逐字 |
| **D-PT-08** | 与 P7 | 新 flag 叠加；关新 flag = P7 行为面 |
| **D-PT-09** | 与 P22 | W3 不等 P22；P22 不计入 G-PT-* |
| **D-PT-10** | 放量 | G0 等价 → G1 默认 ingest 并行 → G2 默认 narrate 并发；各有独立机器门禁 |
| **D-PT-11** | 写安全硬闸 | CAS 已是前提。G1 前必须：merge mutator + AC-ARC-02-parallel 绿。否则默认 `parallel_ingest=false` |
| **D-PT-12** | parallel_embed | 主进程按输入序 **每合并一张即 `offer`**；worker 内禁止 CLIP |
| **D-PT-13** | 删除 DoD | 对齐 ARCH-OPT §3.3：默认开满 4 周 + 周更双跑 diff 空 + 无回切 + 用户 config 零 legacy；暂停须先回单路径 |
| **D-PT-14** | Worker 职责 | **人脸+focal 强制进 worker**；CV aesthetic signals 可进；**geocode / pyiqa·cull / assetId 仅主进程** |
| **D-PT-15** | 共享限流 | 新建跨调用共享 backoff（非「复用」现有单次 sleep）；可观测 `narrateProviderBackoffCount` |
| **D-PT-16** | 实现落点 | 并行入口仅 `media/ingest.py` + `media/ingest_worker.py` + `services/llm_narrate.py`；`web/` 不得出现 `ProcessPoolExecutor` |
| **D-PT-17** | 分阶段交付 | **Phase A**（立即批）：M0+M1+merge mutator+结构 NR+本机门槛采数。**Phase B**：M2 narrate 并发+共享 backoff。**Phase C**：G1/G2 默认开、M3 预检、M5 门禁常驻；M4/P22 可选且不计入 G-PT |
| **D-PT-18** | 双闸成功标准 | 闸 1「与串行行为等价」（G-PT-05/12）不过 → 禁止默认开；闸 2「足够快」（门槛 KPI）不过 → **允许**合能力、保持默认 off，继续优化或接受 stretch 未达 |
| **D-PT-19** | 组合排期 | 若与 Import Wizard / 预览体验抢人力：优先保证 **merge mutator**（即使并行延后也值得）；M0 可并行；**默认开启与 narrate 默认并发可错峰** |

---

## 4. 核心指标体系

### 4.1 端到端与分阶段

| 指标 | 基线 | 门槛 | Stretch |
|------|------|------|---------|
| `studio_e2e_100` / `_250` | 本机 P7 快路径 | −18% / −22% | −25% / −30% |
| `ingest_time_100` / `_250` | `parallel_ingest=false` | −25% | −35% |
| `narrate_time_ge6` | concurrency=1 · cache miss | −30%（限流 −20%） | −40% @c=3 |
| `narrate_cache_hit_rerun` | — | hit≥95% · −80% ms | — |
| `peak_memory_250` | P7 串行 | S2 ≤+30% RSS | — |
| `stage_coverage` | P7 | 相等 | — |

### 4.2 设备档位

| 档位 | parallel_ingest | narrate_concurrency |
|------|-----------------|---------------------|
| S1 | workers=2 | 2 |
| S2 | `min(4, cpu-1)` | 2（起量）→ 3（G2 后） |
| S3 | `min(8, cpu-1)` | 4 |

---

## 5. W1 · 并行 Ingest（PT-A · P0）

### 5.1 两阶段协议（评审 B1 闭合）

```text
主进程：扫描 / 分层 / checkpoint 过滤 / RAW 前置拦截
    → ProcessPool：每张 decode + Haar/focal + 局部色彩/锐度/phash 输入特征
                 + 可选 provisional WebP（临时目录，非最终 asset-NNN）
    → 主进程按输入序收集 Result
    → 重放 burst/phash 状态机（与串行同一套 last_burst / dhash_refs）
    → 分配最终 assetId；commit/rename Blob；丢弃则删除临时衍生图
    → geocode（仅主进程 / cache）
    → on_asset_added → ParallelEmbedCoordinator.offer（每张）
    → 每 persist_every_n：TripService.update 增量 merge
    → finalize：aesthetic ML / photo_cull（主进程）
```

**Worker 允许**：`media.*` 图像路径、只读 IngestConfig 快照、写指定 temp/预分配路径 Blob。  
**Worker 禁止**：`services.trip`、`web`、`orchestrator`、`curation` cull/ML、`vision` 重模型、geocode 网络请求、最终 assetId。

### 5.2 配置键

```yaml
pipeline:
  parallel_ingest: false         # G0/G1 前默认 false；达标后改 true
  parallel_ingest_workers: 0     # 0 = auto
  parallel_ingest_min_photos: 12 # Studio 嵌套 spawn 可另提高
  persist_every_n: 8
```

### 5.3 验收（AC-PT-INGEST）

| ID | 验收项 |
|----|--------|
| **AC-PT-01** | `parallel_ingest=false` ≡ 现行路径（结构/回归） |
| **AC-PT-02** | 门槛：100 张 ingestMs ≥−25% vs 同机串行（stretch −35%） |
| **AC-PT-03** | 保留 assetId 集、dedupe 胜者、`burstGroupId`、`takenAt` 序稳定 |
| **AC-PT-04** | kill worker + resume：无损坏/半残 WebP、无重复 assetId、孤儿可清理 |
| **AC-PT-05** | Studio 进度单调（completed count）；stage 序号模型不变 |
| **AC-PT-11** | geocode 仅主进程；多 worker 不打穿 Nominatim |
| **AC-PT-12** | 每合并一张即 offer；`prefer_web=false` NR profile 下 subjectClass 与串行一致 |

### 5.4 风险

| 风险 | 缓解 |
|------|------|
| Windows / Studio 嵌套 spawn | `min_photos`；workers 上限；nightly Windows 烟测阻塞 G1 |
| 人脸 cascade 多进程内存 | S1 workers=2；RSS 门槛 |
| CAS 竞争 | merge mutator + `persist_every_n` |
| WebP 字节差 | NR 用源图 profile；不比 L-bytes |

---

## 6. W2 · 章节 LLM 并发（PT-B · P0）

### 6.1 方案

```text
1. meta 串行
2. 收集需生成的 chapter briefs（跳过 cache hit）
3. ThreadPool + 共享 semaphore + 共享 backoff 并发 chat
4. 按 chapter index 升序 _apply_chapter_payload（lead_seen）
5. 重试耗尽 → NarrateError 整段失败（与现行一致）
```

### 6.2 配置键

```yaml
llm:
  narrate_concurrency: 1         # G2 前默认 1；起量默认 2
  narrate_concurrency_backoff: true
```

### 6.3 验收（AC-PT-NARRATE）

| ID | 验收项 |
|----|--------|
| **AC-PT-06** | concurrency=1 ≡ 现行（含 cache key） |
| **AC-PT-07** | 门槛 −30%（限流 −20% 且 record 含 backoffCount≥1） |
| **AC-PT-08** | 并发不影响 cache hit；命中不重复 HTTP |
| **AC-PT-09** | 429 注入：共享 backoff 可观测；可降级串行或按策略失败；不未捕获崩溃 |
| **AC-PT-10** | lead_seen / 去重与串行一致（stub；故意乱序完成） |

---

## 7. W3 · 快路径可观测与增量（PT-C / PT-D · P1）

| 动作 | 说明 |
|------|------|
| 预检 warning | vision 开但 `parallel_embed=false` 等 → warning，不阻断 |
| 遥测 | 记录实际 workers / concurrency / cache hits |
| Cache 文档 | 勿无谓 `force_recluster`；UI「重新生成」才 `regenerate` |
| P22 | 可选；不阻塞 W1/W2；不计入 G-PT-* |

---

## 8. W4 · 观测、基准与门禁（PT-E）

### 8.1 产物

| 产物 | 用途 |
|------|------|
| `scripts/pipeline_throughput_benchmark.py` | 采数；`--register-baseline` |
| `scripts/pipeline_throughput_equivalence_check.py` | **活 diff**（非仅读预填 rate） |
| `scripts/pipeline_throughput_gate.py` | `--from-record` / `--check-default-on` |
| `scripts/lint_pt_default_flags.py` | 默认加速态 ↔ signoff 耦合 |
| `docs/acceptance-records/pipeline-throughput-perf-eval.json` | 机器可读评测 |
| `docs/acceptance-records/pipeline-throughput-real-trip-signoff.json` | L4 |
| `docs/acceptance-records/pipeline-throughput-default-flag-signoff.json` | 默认开专用 |
| `docs/config-pipeline-throughput.example.yaml` | 冻结 benchmark config |
| `docs/reports/pipeline-throughput-baseline.md` | 人读基线 |

### 8.2 Timings 增补

| 字段 | 含义 |
|------|------|
| `ingestWorkers` | 实际 worker 数 |
| `ingestParallelFallback` | 是否回退串行 |
| `narrateConcurrency` | 实际并发 |
| `narrateCacheHits` / `narrateCacheMisses` | 章级 cache |
| `narrateProviderBackoffCount` | 共享限流次数 |

### 8.3 基线登记 SOP

1. 冻结 `docs/config-pipeline-throughput.example.yaml`（P7 快路径 + PT flags off = baseline）。
2. `benchmark.py --register-baseline --photos 100,250 --tier S2 --repeats 3` → 写 `baseline` + `deviceFingerprint`。
3. 同机同 commit 跑 candidate（flags on）→ 自动算门槛/stretch。
4. `gate.py --write --strict`。
5. 换机重登须 `--replace-baseline` + 理由；禁止静默覆盖。

CI **不**重跑大相册；只跑 `gate --from-record --strict`。改产品默认值时跑 `--check-default-on`（block merge）。

---

## 9. 质量等价门禁（NR-PT）

| 层 | 手段 | 判据 |
|----|------|------|
| **L-struct** | fixed：parallel on/off | assetId、dedupe 胜者、burstGroupId、cull 排除集、chapter/screen/cover **100%** |
| **L-embed** | NR profile：`prefer_web_derivative=false`（或源图） | subjectClass / cluster **100%**；默认 web 路径 real≥95% 或告警 |
| **L-bytes** | — | WebP/JPEG **不比** |
| **L-narrate** | stub 1 vs N | 字段 **100%**；真 LLM → VR-N* + signoff JSON |
| L1 pytest | PR 强制 | 全绿 |
| L4/L5 | dogfood + record | 禁口头确认 |

算法最小矩阵：PT-A1 Burst、PT-A2 Phash、PT-A3 Face→focal、PT-A4 Cull、PT-N1 lead_seen（放量前 +A5 embed 重叠、+N2 VR-N04）。详见 IMPLEMENTATION。

---

## 10. 里程碑、分阶段与放量

### 10.1 Phase 划分（总监批复 · D-PT-17）

| Phase | 内容 | 预算 | 默认 flag |
|-------|------|------|-----------|
| **A（立即）** | M0 门禁骨架；M1 并行 ingest（正确性优先）；merge mutator；结构 NR；本机门槛采数 | **8–12 人日** | 仍 **off** |
| **B（随后）** | M2 narrate 并发 + 共享 backoff；stub NR；429 注入 | 含于 14–20 上限 | concurrency 仍 **1** |
| **C（放量）** | M3 预检；M5 CI 钩子；**G1/G2 默认开**（各过独立门禁） | 含于上限 | 分闸打开 |
| **可选** | M4 P22 对接 | 另计；**不进** G-PT-* | — |

```text
Phase A 能力合入（默认 off）
  → Phase B 能力合入（默认 off）
  → G0 记录齐全
  → G1 默认 parallel_ingest（门槛 KPI + NR + AC-ARC-02-parallel + Windows + G-PT-12）
  → G2 默认 narrate_concurrency≥2（门槛 KPI + stub NR + 429 + 文案抽检）
```

| 里程碑 | 内容 | 预估 | Phase |
|--------|------|------|-------|
| **M0** | 基线 + schema + flag 骨架 + gate 空壳 | 1–1.5d | A |
| **M1** | 并行 ingest + AC-PT-01…05/11/12 + merge mutator | **7–11d** | A |
| **M2** | narrate 并发 + 共享 backoff + AC-06…10 | 3.5–5d | B |
| **M3** | 预检 warning + timings 字段 | 0.5–1d | C |
| **M4** |（可选）P22 | 2–3d | 可选 |
| **M5** | gate 入 CI；默认开钩子 | 1–1.5d | C |
| **合计** | 不含 M4 | **约 14–20 人日**（A 优先锁定 8–12） |

### 10.2 回滚

| Flag | 回滚动作 |
|------|----------|
| `pipeline.parallel_ingest: false` | 立即回到逐张 ingest |
| `llm.narrate_concurrency: 1` | 立即回到逐章 LLM |
| 全回滚 | 上述两项关闭 = P7 行为面 |

删除 DoD：见 D-PT-13 / ARCH-OPT §3.3。

---

## 11. 实施任务草表

见 [IMPLEMENTATION-PIPELINE-THROUGHPUT.md](./IMPLEMENTATION-PIPELINE-THROUGHPUT.md)。Phase A 开工前须完成 IMPLEMENTATION §2（两阶段协议 / merge mutator）设计评审。

---

## 12. 验收清单

### 12.1 产品

- [ ] 完整生成仍含导入、聚类、编排、文案、渲染；用户不认为「少做了某步」（G-PT-04/11）
- [ ] 100 张 dogfood 达 G-PT-01 **门槛**或 record 记载例外；**G-PT-12 抽检通过**方可将默认开列入议程
- [ ] 关闭新 flag 回到 P7，无需改相册
- [ ] 进度单调；无「黑盒无阶段」回退

### 12.2 工程

- [ ] AC-PT-01…12 按门禁级别通过
- [ ] NR-PT L-struct/L-embed（NR profile）/L-narrate stub 绿
- [ ] 无绕过 `TripService.update` 的直写；mutator 为增量 merge
- [ ] `web/` 无 ProcessPoolExecutor
- [ ] 默认开 flag 经 `--check-default-on`（与功能合入分离）
- [ ] Phase A 结束时：能力可开、**产品默认仍 off**（除非已单独过 G1）

---

## 13. 已闭合的原开放问题

| 原 ID | 闭合为 |
|-------|--------|
| Q-PT-01 | D-PT-01 |
| Q-PT-02 | D-PT-14 |
| Q-PT-03 | D-PT-04 |
| Q-PT-04 | D-PT-06 |
| Q-PT-05 | D-PT-11 |
| Q-PT-06 | D-PT-09 |

残留跟踪项见 IMPLEMENTATION「开放实现细节」。

---

## 14. 风险登记与红线（RAID 摘要）

> 完整技术论据见评审纪要与开发风险讨论；本节为 **产品/工程共同红线**，实施中不得静默降级。

| ID | 风险 | 级别 | 预防（合同化） |
|----|------|------|----------------|
| **R-01** | Dedupe/assetId 漂移 → 版式「变了」 | P0 | 两阶段+有序重放；PT-A1/A2；AC-PT-03；G-PT-12 |
| **R-02** | WebP 差经 CLIP/cull 间接漂结构 | P0 | NR profile 关 web-derivative；D-PT-07；AC-PT-12 |
| **R-03** | 全量覆盖 persist × 并行写频丢 HTTP 写入 | P0 | 增量 merge；AC-ARC-02-parallel；未完成不得 G1 |
| **R-04** | Studio 嵌套 ProcessPool（Win）慢/孤儿/OOM | P0 | min_photos/workers；cancel shutdown；nightly 阻塞 G1 |
| **R-05** | KPI 未达却默认开或对外宣传 stretch | P1 | 双闸 D-PT-18；`--check-default-on`；signoff JSON |
| **R-06** | LLM 429 + 误改失败语义 | P1 | concurrency 起量 2；共享 backoff；保持 NarrateError 整段失败 |
| **R-07** | 并行削弱 ingest∥embed | P1 | 每张 offer（D-PT-12）；benchmark 兼看 embed |
| **R-08** | 范围膨胀 / 三套并行路径 | P2 | Phase A 冻结范围；仅 ProcessPool+串行；删除 DoD |
| **R-09** | 门禁空转（只有模板无活 diff） | P2 | M0 gate schema；M5 活 diff；禁口头 sign-off |

**红线（违反即停默认开或停合入）**：

1. 结构/dedupe 与串行不等价仍要默认开。  
2. merge mutator 未完成仍要 G1。  
3. 用降 beam / 关 vision / 跳过阶段刷 e2e。  
4. 把 P22 增量收益算进本 PRD G-PT-01。  
5. 在 `web/` 旁路自建进程池，绕过 `run_trip`。

---

## 15. 生成体验组合（路线图对齐 · 非本 PRD 交付）

等待体感由三件事共同决定，**须在路线图上并列，KPI 分开**：

| 杠杆 | 谁负责 | 与本 PRD |
|------|--------|----------|
| **首次全量加速** | 本 PRD（并行 ingest / narrate 并发） | 主交付 |
| **二次增量跳过未脏阶段** | PRD-PHASE22 | 正交；改一字重跑痛优先看 P22，不计入 G-PT-* |
| **早期可预览 / 阶段完成即可见草稿** | Studio / G1 体验（另项） | **非本 PRD 范围**；可与 Phase A 错峰，避免只优化墙钟数字 |

产品叙事建议：对外说「生成更快且结果稳定」；对内验收拆成「全量墙钟 / 重跑墙钟 / 首屏可看」三条，避免单一 e2e 指标绑架优先级。

---

## 16. 附录 A · 推荐 config 快照

见 [config-pipeline-throughput.example.yaml](./config-pipeline-throughput.example.yaml)。

## 附录 B · 证据锚点

| 主题 | 路径 |
|------|------|
| 主管线 | `travelogue/orchestrator/run.py` |
| Studio 导入 | `travelogue/web/studio_pipeline.py` |
| Ingest 串行循环 | `travelogue/media/ingest.py` |
| Narrate 串行循环 | `travelogue/services/llm_narrate.py` |
| CAS | `travelogue/services/trip.py` · `TripService.update` |
| 评审纪要 | `docs/acceptance-records/pipeline-throughput-prd-review-2026-07-11.md` |

## 附录 C · 修订历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-07-10 | 初稿 |
| v0.2.0 | 2026-07-11 | 四方评审闭合：两阶段协议、D-PT-07/NR 分层、失败语义、共享 backoff、KPI 双轨、工期 14–20d、D-PT-11…16 |
| v0.3.0 | 2026-07-11 | 总监批复入文：§0.4 分闸 Go、Phase A/B/C、G-PT-11/12、D-PT-17…19、§14 风险红线、§15 生成体验组合；状态 → Approved · Phase A Kickoff |
