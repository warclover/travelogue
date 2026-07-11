# 管线吞吐加速 PRD 评审会纪要

| 属性 | 内容 |
|------|------|
| **会议** | Pipeline Throughput PRD 跨职能评审 |
| **日期** | 2026-07-11 |
| **文档** | [PRD-PIPELINE-THROUGHPUT.md](../PRD-PIPELINE-THROUGHPUT.md) **v0.2.0-THROUGHPUT** |
| **发起人** | 产品 / 工程 |
| **结论** | **有条件通过（Conditional Go）** — 方向立项通过；v0.2 文档已闭合；**M1 编码前须完成 merge mutator 设计评审**；M0 脚本可开工 |
| **纪要版本** | v1.1（文档行动项 A1–A6 已闭合；M0 脚本实现仍 ☐） |

---

## 1. 参会与角色

| 角色 | 代号 | 关注点 |
|------|------|--------|
| **开发工程** | ENG | worker 切分、Windows/Studio 嵌套 spawn、与现有 ingest/narrate 代码冲突、工期 |
| **算法** | ALG | dedupe/人脸/WebP→CLIP/cull 语义、NR-PT 可实现性、KPI 物理上限 |
| **架构** | ARC | 与 ARCH-OPT / P7 / P22 边界、trip 写模型、双路径债务、ADR |
| **测试 / QA** | QA | AC 可测性、基线登记、CI vs dogfood、默认开 flag 门禁 |

---

## 2. 总评汇总

| 角色 | 裁决 | 一句话 |
|------|------|--------|
| **ENG** | 有条件通过 · 开工 No-Go | 瓶颈锚点正确；worker 边界 / dedupe 协议 / D-PT-06 语义未闭合 |
| **ALG** | 有条件 No-Go（默认开启） | D-PT-07「允许 WebP 字节差」与默认 `prefer_web_derivative` 冲突，会污染 CLIP/cull |
| **ARC** | 条件 Go | CAS 已落地；须改 Q-PT-05 为压测硬闸 + merge mutator；删除 DoD 对齐 ARCH-OPT |
| **QA** | Conditional Go | 功能 AC 可测；perf 基线 SOP 与「默认开 flag」机器门禁未写清 |

**合议结论**：

1. **立项通过**：P7 之后剩余结构性串行（ingest 逐张、narrate 逐章）判断正确；「不砍流程、只改执行方式」原则保留。
2. **v0.1.0 不得直接开 M1 编码**；须升版 **v0.2** 关闭下方阻塞项。
3. **可立即启动 M0**：同机基线登记、config flag 骨架、`pipeline-throughput-perf-eval.json` schema、gate `--from-record` 空壳。
4. **默认开启** `parallel_ingest` / `narrate_concurrency≥2` 另设 G1/G2 硬闸，与「功能合入」分离（吸取 P7 `AC-P7-01/02=false` 仍可合入的教训）。

---

## 3. 一致通过项（全票）

| # | 决议 |
|---|------|
| C1 | 阶段集合不删减；禁止用关 clustering / 降 beam / 关 vision 换速度作为 Studio 默认 |
| C2 | W1（并行 ingest）与 W2（章级 LLM 并发）为 P0；W3 不等 P22；P22 skip **不计入** G-PT-01 |
| C3 | Worker **禁止**写 `trip.json`；assetId / burst·phash 终裁留主进程；按输入序合并 |
| C4 | Narrate：meta 串行 → chapters 并发 → **按 chapter index 升序** apply（`lead_seen`） |
| C5 | 失败语义：**保持现行** `NarrateError` 耗尽即整段失败；不在本 PRD 改「单章 skip」 |
| C6 | ARCH-OPT `TripService.update` + `meta.revision` **已落地**，不再「等待 M-A1」 |
| C7 | 实现落点仅 `media/ingest*.py` + `services/llm_narrate.py` + config/timings；`web/` 不得自建 ProcessPool |
| C8 | NR 思想对齐 P7 双门槛；真实 LLM 不比逐字；stub 路径可要求字段 100% |

---

## 4. 阻塞项（B）— v0.2 必须关闭后方可 M1

### B1 · Ingest 两阶段协议未写清（ENG + ALG）

**问题**：`_build_asset_entry` 将人脸、WebP、geocode、aesthetic 绑在一条链；§5.1「可进 worker」列表与 Q-PT-02 未形成可实施的数据流。

**决议（写入 §5.1）**：

```text
Worker：decode → 特征（含 Haar/focal）→ 可选写 provisional WebP（临时路径）
主进程：按输入序重放 burst/phash 状态机 → 分配最终 assetId → rename/提交 Blob
       → geocode（仅主进程）→ on_asset_added/offer → 批量 persist
       → finalize：aesthetic ML / photo_cull
```

### B2 · Dedupe 有序重放必须成硬 AC（ENG + ALG）

合并必须按输入序重放与串行相同的 `last_burst` / `dhash_refs` / `_next_asset_id` 状态机；禁止 worker 自行 upsert。AC-PT-03 升格为 NR 一等公民（保留集 + 胜者 assetId + `burstGroupId`）。

### B3 · 「先 WebP 再 dedupe」孤儿清理契约（ENG）

现行是先 dedupe 再写盘。并行若提前写衍生图，须补：临时路径约定、丢弃时删除、kill/resume 无半残文件。扩展 AC-PT-04。

### B4 · Geocode 禁止进 ProcessPool（ENG）

`geocode.py` 节流锁仅进程内有效；多进程会打穿 Nominatim。§5.1 显式排除。

### B5 · D-PT-07 与默认 web-derivative 矛盾（ALG · 最大算法阻塞）

phash 基于 decode 原图（不受 WebP 字节影响），但默认 `prefer_web_derivative=true` 时 CLIP/cull 读 WebP → 字节差可间接漂 `subjectClass` / `layoutEligible` / 章节结构。

**决议**：改写 D-PT-07 / NR-PT：

| 层 | 判据 |
|----|------|
| L-struct | assetId、dedupe、burst、cull 排除集、chapter/screen/cover — fixed **100%** |
| L-embed | NR 默认 profile：`prefer_web_derivative=false`（或源图路径）下 subjectClass/cluster **100%**；默认 web 路径仅 real≥95% 或告警 |
| L-bytes | WebP/JPEG 字节 — **不比** |
| L-narrate | stub 100%；真 LLM → VR-N* + 机器可读 signoff |

### B6 · D-PT-06 与现行 NarrateError 自相矛盾（ENG）

删掉「单章失败不拖死整 trip」表述；与 Q-PT-04 / C5 对齐为整段失败。

### B7 · 「共享 backoff」不存在，须新设计（ENG + QA）

`llm/client.py` 重试为单次调用独立退避。AC-PT-09 需可观测字段（`narrateProviderBackoffCount` 等），不能写「复用现有」。

### B8 · persist mutator 全量覆盖 + 并行写频（ARC）

`on_persist` 须改为 **增量 merge**（只合并 assets/ingest 统计/checkpoint），禁止整 trip 覆盖。G1 前扩展 AC-ARC-02（并行 persist × import 子进程 × HTTP PATCH）。改不完则 **默认 `parallel_ingest=false`**。

### B9 · Perf 基线 SOP + 默认开 flag 机器门禁（QA）

规格化：谁、何机、何 config、`repeats≥3` 中位数、`deviceFingerprint`、禁止静默覆盖 baseline。  
「未达 KPI 不得默认开」→ `pipeline_throughput_gate.py --check-default-on` + `lint_pt_default_flags.py`；与功能合入分离。

### B10 · parallel_embed 时序契约（ALG + ARC）

主进程按输入序 **每合并一张即 `offer`**；禁止整批末尾才 offer；worker 内禁止 CLIP。升为 **D-PT-12**。

---

## 5. 重要项（I）— 应进 v0.2，不阻塞 M0

| ID | 项 | 决议 |
|----|----|------|
| **I1** | PT-C「P7 未强制落地」夸大 | Studio/`PipelineConfig` 默认已开 `parallel_embed` 等；W3 降级为「预检 warning + 遥测」 |
| **I2** | KPI 双轨 | 门槛 / stretch 分离（见 §6）；门槛未达可合功能，不可默认开 |
| **I3** | 工期上修 | **14–20 人日**（不含 M4）；含 Windows Studio 嵌套硬化取 16–22 |
| **I4** | 删除 DoD | 逐字对齐 ARCH-OPT §3.3（周更双跑、用户 config 清零、暂停须回单路径） |
| **I5** | `persist_every_n` vs 现行 tick=5 | 明确 checkpoint 频率与 CAS persist 是否解耦 |
| **I6** | 进度计数口径 | 并行时 `on_progress` = completed count，保证单调 |
| **I7** | AGENT-ARCH 文档漂移 | 「run_trip 不含 clustering」已过时；本 PRD 引用勿当现状 |
| **I8** | ADR | **不**新开大 ADR；补丁 ADR-008「Ingest 并行写边界」+ TECH-ARCH §17.7 |

---

## 6. KPI 修订建议（ALG + QA · 合议采纳）

| 指标 | v0.1.0 | v0.2 建议 |
|------|--------|-----------|
| ingest −35% | 硬目标 | **门槛 −25%** / stretch −35% |
| e2e 100 −25% | 硬目标 | **门槛 −18%** / stretch −25% |
| e2e 250 −30% | 硬目标 | **门槛 −22%** / stretch −30% |
| narrate −40% @c=3 | 硬目标 | **门槛 −30%** / 限流地板 −20%（须 `backoffCount≥1`） |
| narrate cache −80% | 保持 | 保持 |
| 内存 +25% | 保持 | S2 ≤+30% RSS；S1 workers=2 单列 |

---

## 7. 开放问题拍板（升入 §3 已拍板决策）

| ID | 合议决议 | 备注 |
|----|----------|------|
| **Q-PT-01** | **生产路径 ProcessPool**；`<min_photos` 或 `workers=1` → 串行。ThreadPool **仅** benchmark A/B，不进默认 runtime。Studio 子进程内另加：`min_photos` 提高或显式检测嵌套 spawn 降 workers | ENG 曾主张先 ThreadPool MVP；ARC 反对第三套生产路径。折中：正确性用串行对照测；生产只保留 ProcessPool+串行两态 |
| **Q-PT-02** | **人脸（+focal）强制进 worker**；CV aesthetic signals 可进；**pyiqa / cull / geocode / assetId 主进程** | 覆盖 ALG 硬要求 |
| **Q-PT-03** | **S2 默认 concurrency=2 起量**；dogfood 稳定后再 3。S1=2 | 兼顾 ENG 限流顾虑与原倾向 |
| **Q-PT-04** | **保持 NarrateError 整段失败** | 闭合；改 D-PT-06 |
| **Q-PT-05** | → **D-PT-11**：CAS 已是前提；G1 硬闸 = AC-ARC-02-parallel + merge mutator | 闭合 |
| **Q-PT-06** | **不等 P22** | 维持 |

新增：

| ID | 决议 |
|----|------|
| **D-PT-11** | 见上 Q-PT-05 |
| **D-PT-12** | 与 `parallel_embed`：主进程有序 `offer`；worker 禁 embed |
| **D-PT-13** | 删除 DoD = ARCH-OPT §3.3 模板 |

---

## 8. 测试与放量门禁（QA 合议）

| 层 | CI | 说明 |
|----|-----|------|
| L1 unit | PR 强制 | 合并序、concurrency=1 等价、429 注入、config |
| L2/L3 结构+stub | push integration / validate 强制 | 活 diff（勿只扩展 P7 记录计算器） |
| L4 真 LLM | 不跑 API；强制 `…-real-trip-signoff.json` schema | 禁口头确认 |
| L5 perf | 不跑 100/250；强制 record + **默认开 flag 专用 gate** | Windows spawn：nightly，**阻塞 G1** |

建议脚本：`pipeline_throughput_benchmark.py` / `equivalence_check.py` / `gate.py` / `lint_pt_default_flags.py`。

测试约占工期 **35–40%**（约 4–5.5 人日）。

算法验收最小矩阵：PT-A1 Burst、PT-A2 Phash、PT-A3 Face→focal、PT-A4 Cull 全局、PT-N1 lead_seen（放量前加 A5 embed 重叠、N2 VR-N04）。

---

## 9. 工期修正

| 里程碑 | v0.1.0 | 合议修正 |
|--------|--------|----------|
| M0 | 1d | 1–1.5d |
| M1 并行 ingest | 4–6d | **7–11d** |
| M2 narrate 并发 | 3–4d | 3.5–5d |
| M3 配置预检 | 1d | 0.5–1d |
| M5 gate | 1d | 1–1.5d |
| **合计（不含 M4）** | 10–13d | **14–20d** |

---

## 10. 行动项（Action Items）

| ID | 行动 | Owner | 截止 | 状态 |
|----|------|-------|------|------|
| **A1** | PRD 升版 v0.2：关闭 B1–B10，Q-PT 写入 §3，KPI 双轨，工期修正 | 产品+工程 | 评审后 3 个工作日 | ☑ 2026-07-11 → [PRD v0.2](../PRD-PIPELINE-THROUGHPUT.md) |
| **A2** | 撰写 `IMPLEMENTATION-PIPELINE-THROUGHPUT.md`（含两阶段协议时序图、merge mutator 草图） | 工程 | v0.2 后 | ☑ [IMPLEMENTATION](../IMPLEMENTATION-PIPELINE-THROUGHPUT.md) |
| **A3** | ADR-008 补丁半页 + TECH-ARCH §17.7 提纲 | 架构 | 与 A2 并行 | ☑ ADR-008 §9 · TECH-ARCH §17.7 |
| **A4** | M0：baseline 说明 + perf-eval / signoff JSON 模板 + config 示例 | 工程+QA | 可立即 | ☑ 模板/config/baseline.md 已入仓；**脚本实现仍 ☐（PT-M0-04/05）** |
| **A5** | AC-ARC-02-parallel 用例大纲 | 架构+QA | M1 开工前 | ☑ 见 IMPLEMENTATION §2.3 |
| **A6** | 算法 fixture：burst/phash/face 最小集路径列入 IMPLEMENTATION | 算法 | M1 前 | ☑ 见 IMPLEMENTATION §4.1 |

---

## 11. 最终裁决

| 项 | 裁决 |
|----|------|
| **PRD 方向 / 立项** | **通过** |
| **v0.1.0 直接开工 M1** | **No-Go** |
| **升版 v0.2 并关闭 §4 阻塞项后** | **Go（M0 可先行）** |
| **G1 默认开 parallel_ingest** | 另闸：结构 NR + ingest 门槛 KPI + AC-ARC-02-parallel + Windows 烟测 |
| **G2 默认开 narrate 并发** | 另闸：stub NR + narrate 门槛 KPI + 429 注入绿 |

---

## 附录 · 证据锚点（评审核验）

| 主张 | 核验 |
|------|------|
| ingest 逐张串行 | `media/ingest.py` ≈ L1248 `for photo, user_tier in photo_tiers` |
| narrate 逐章串行 | `services/llm_narrate.py` ≈ L471 |
| CAS 已落地 | `services/trip.py` `TripService.update` + `TripConflictError`；`meta.revision` |
| Studio 已 spawn 子进程 | `web/studio_subprocess.py` `mp.get_context("spawn")` |
| geocode 进程内锁 | `media/geocode.py` `_geocode_lock` |
| CLIP 默认吃 WebP | `vision/clip_encoder.py` `prefer_web_derivative` |
| 429 无共享 backoff | `llm/client.py` 单次调用独立 sleep |
| P7 parallel_embed 默认开 | `config/misc.py` / Studio profile |

---

## 修订历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-07-11 | 四方（开发/算法/架构/测试）合议初稿 |
| v1.1 | 2026-07-11 | A1–A6 文档交付勾选；指向 PRD v0.2 / IMPLEMENTATION / ADR-008 §9 / TECH-ARCH §17.7 |
