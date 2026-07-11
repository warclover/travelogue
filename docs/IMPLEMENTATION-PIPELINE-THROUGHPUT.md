# Travelogue · 管线吞吐加速实施清单

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-PIPELINE-THROUGHPUT.md](./PRD-PIPELINE-THROUGHPUT.md) **v0.3.0** |
| **评审纪要** | [pipeline-throughput-prd-review-2026-07-11.md](./acceptance-records/pipeline-throughput-prd-review-2026-07-11.md) |
| **关联架构** | [TECH-ARCHITECTURE.md](./TECH-ARCHITECTURE.md) §17.7 · [adr/008](./adr/008-trip-storage-boundaries.md) §9 |
| **代号** | PT-Throughput |
| **状态图例** | ☑ 已落地 · ◑ 部分 · ☐ 未开始 |
| **更新日期** | 2026-07-11 |

> **Kickoff 约束（PRD v0.3）**：**Phase A**（M0+M1+merge mutator+结构 NR）可立即开工，预算 8–12 人日，**产品默认 flag 保持 off**。M1 须完成本清单 §2 设计评审。Phase B/C 与 G1/G2 默认开见 PRD §0.4 / §10 / §14。  
> **优先级**：P0（Phase A）> P0（Phase B）> P1（Phase C 预检）> P2（M4 P22）

---

## 1. 里程碑总览

| 里程碑 | 主题 | 完成标志 | 预估 | 状态 |
|--------|------|----------|------|------|
| **M0** | 基线 + flag 骨架 + record schema + gate 空壳 | config 键可加载；perf-eval/signoff 模板入仓；`gate --from-record --require-schema-only` | 1–1.5d | ☐ |
| **M1** | 并行 ingest | AC-PT-01…05/11/12；merge mutator；结构 NR | 7–11d | ☐ |
| **M2** | narrate 并发 | AC-PT-06…10；共享 backoff | 3.5–5d | ☐ |
| **M3** | 预检 warning + timings 字段 | G-PT-07/08 | 0.5–1d | ☐ |
| **M4** |（可选）P22 skip 对接 | 不计入 G-PT-* | 2–3d | ☐ |
| **M5** | gate→CI + 默认开钩子 | lint_pt_default_flags；`--check-default-on` | 1–1.5d | ☐ |

**合计（不含 M4）**：约 **14–20 人日**（测试约占 35–40%）。其中 **Phase A 锁定 8–12 人日**（PRD D-PT-17）。

---

## 2. 设计规格（M1 开工前冻结）

### 2.1 Ingest 两阶段时序

```mermaid
sequenceDiagram
  participant Main as 主进程 ingest.py
  participant Pool as ProcessPool ingest_worker
  participant Trip as TripService.update
  participant Emb as ParallelEmbedCoordinator

  Main->>Main: scan / tier / checkpoint filter / RAW gate
  loop 每张（可批量 submit）
    Main->>Pool: decode+face+features+provisional WebP(temp)
    Pool-->>Main: WorkerResult(pickle-safe)
  end
  loop 按输入序
    Main->>Main: replay burst/phash state machine
    alt 保留
      Main->>Main: assign assetId; commit/rename Blob
      Main->>Main: geocode (main only)
      Main->>Emb: on_asset_added / offer
    else 丢弃
      Main->>Main: delete provisional files
    end
    opt 每 persist_every_n
      Main->>Trip: merge mutator (assets+stats+checkpoint)
    end
  end
  Main->>Main: finalize aesthetic ML / photo_cull
```

### 2.2 Worker 契约

| 项 | 规格 |
|----|------|
| 模块 | 新建 `travelogue/media/ingest_worker.py`（顶层可 pickle 纯函数） |
| 入参 | 路径、只读 config 快照、temp 目录、可选预分配 provisional id |
| 出参 | `WorkerResult` dataclass：dhash、sharpness、subject/focal、色彩、exif 摘要、provisional 路径列表、error |
| 禁止 import | `services` / `web` / `orchestrator` / `curation` / `vision`（重模型） |
| import-linter | 建议：`ingest_worker` 不得依赖第 4 层以上 |

### 2.3 Merge mutator（D-PT-03 / D-PT-11）

```python
# 伪代码 — on_persist / 阶段末
def merge_ingest_partial(disk_trip: dict, *, memory_assets_delta, stats, checkpoint) -> None:
    """禁止 disk_trip.clear(); disk_trip.update(full_memory_trip)。
    只合并 ingest 拥有的字段，保留 HTTP 侧 intent/copy 等并发写入。"""
    # upsert assets by assetId / sourcePath
    # merge pipeline.ingestStats / checkpoint
    # bump_revision=False（pipeline 中间态，对齐 ADR-008 §6）
```

**AC-ARC-02-parallel 大纲**（架构+QA，M1 前补全用例）：

| 步骤 | 动作 | 期望 |
|------|------|------|
| 1 | 启动 import 子进程，`parallel_ingest=true`，`persist_every_n=2` | 进行中 |
| 2 | HTTP PATCH intent / save-copy 交错 | 409 可重试或成功合并 |
| 3 | import 结束后 load trip | intent 补丁仍在；assets 完整；无静默丢失 |
| 4 | 对照 `parallel_ingest=false` 同相册结构 hash | L-struct 一致 |

### 2.4 Narrate 并发调度

```text
meta (serial) → gather briefs → ThreadPool(sem=N) + shared_backoff
  → results dict[ch_idx]
  → for ch_idx in sorted: apply + lead_seen
  → exhausted retries → NarrateError (整段)
```

共享 backoff：模块级锁 + 下次允许请求的 monotonic 时间戳；429/502/503 更新之；写入 `narrateProviderBackoffCount`。

### 2.5 NR-PT profile

规范化（对齐 P7 思想，新建活 diff 脚本）：

- `clustering.deterministic_strict=true`
- `pipeline.parallel_embed`：结构对比时可 false；embed 专项按 D-PT-12
- **L-embed 强制**：`vision.prefer_web_derivative=false`（或源图路径）
- 剔除：timings、runs 时间戳、WebP 字节、真实 LLM 正文

---

## 3. M0 · 基线与骨架（P0）

| 任务 ID | 任务 | 文件/模块 | 状态 |
|---------|------|-----------|------|
| PT-M0-01 | 同机登记说明 + baseline.md 模板 | `docs/reports/pipeline-throughput-baseline.md` | ☐ |
| PT-M0-02 | `PipelineConfig` / `LlmConfig` 新键 + loader + example | `config/misc.py` · `config-pipeline-throughput.example.yaml` | ☐ |
| PT-M0-03 | perf-eval / signoff JSON 模板 | `docs/acceptance-records/pipeline-throughput-*.json` | ◑ 模板已入仓 |
| PT-M0-04 | `pipeline_throughput_gate.py` 空壳：`--from-record --require-schema-only` | `scripts/` | ☐ |
| PT-M0-05 | benchmark 脚本骨架：`--register-baseline` 接口 | `scripts/pipeline_throughput_benchmark.py` | ☐ |

---

## 4. M1 · 并行 Ingest（P0）

| 任务 ID | 任务 | 文件/模块 | 状态 |
|---------|------|-----------|------|
| PT-M1-01 | `ingest_worker.py` + `WorkerResult` | `media/ingest_worker.py` | ☐ |
| PT-M1-02 | 主进程调度 ProcessPool；`<min_photos` / `workers=1` 短路串行 | `media/ingest.py` | ☐ |
| PT-M1-03 | 有序 dedupe 重放；最终 assetId；孤儿清理 | `ingest.py` | ☐ |
| PT-M1-04 | geocode 仅主进程断言 | `ingest.py` · 单测 | ☐ |
| PT-M1-05 | merge mutator 替换全量覆盖 persist | `studio_pipeline.py` / ingest hooks · `trip.py` 约定 | ☐ |
| PT-M1-06 | 每合并一张 `on_asset_added` → offer | `orchestrator/run.py` 契约保持 | ☐ |
| PT-M1-07 | resume / kill 恢复 + 半残 WebP | 测试 | ☐ |
| PT-M1-08 | Windows spawn 烟测 | `tests/integration/test_pt_ingest_windows_spawn.py` · nightly | ☐ |
| PT-M1-09 | 结构等价 + serial parity | `tests/integration/test_pt_ingest_*.py` | ☐ |
| PT-M1-10 | AC-ARC-02-parallel 集成测 | `tests/integration/test_pt_persist_cas_parallel.py` | ☐ |

### 4.1 算法验收夹具（最小）

| ID | 夹具意图 | 建议路径 |
|----|----------|----------|
| PT-A1 | 3s 内连拍 5 张清晰度递增 | `tests/fixtures/pt-ingest-burst/` |
| PT-A2 | 近重 2 + 无关 1 | `tests/fixtures/pt-ingest-phash/` |
| PT-A3 | 单人脸大头照 | `tests/fixtures/pt-ingest-face/` |
| PT-A4 | ≥30 张 cull 全局 | 复用既有中型 fixture 或 `pt-ingest-cull/` |
| PT-N1 | ≥6 章 stub 故意重复 lead | 单测构造 trip dict，无需相册 |

---

## 5. M2 · Narrate 并发（P0）

| 任务 ID | 任务 | 文件/模块 | 状态 |
|---------|------|-----------|------|
| PT-M2-01 | semaphore 调度 + 有序 apply | `services/llm_narrate.py` | ☐ |
| PT-M2-02 | 共享 backoff + timings 计数 | `llm/client.py` 或 narrate 层包装 | ☐ |
| PT-M2-03 | concurrency=1 短路 ≡ 旧路径 | 单测 | ☐ |
| PT-M2-04 | lead_seen 乱序完成仍一致 | `tests/unit/llm/test_llm_narrate_lead_seen_order.py` | ☐ |
| PT-M2-05 | 429 注入 AC-PT-09 | `tests/unit/llm/test_llm_narrate_backoff.py` | ☐ |
| PT-M2-06 | cache hit 并发 | `test_llm_narrate_concurrency.py` | ☐ |
| PT-M2-07 | stub 1 vs N 字段等价 | `tests/integration/test_pt_narrate_stub_equiv.py` | ☐ |

---

## 6. M3 · 可观测（P1）

| 任务 ID | 任务 | 状态 |
|---------|------|------|
| PT-M3-01 | import 预检 warning（P7 键未对齐） | ☐ |
| PT-M3-02 | timings 增补字段写入 schema（若需） | ☐ |
| PT-M3-03 | Studio profile 单测 | ☐ |

---

## 7. M4 · P22（P2 · 可选）

| 任务 ID | 任务 | 状态 |
|---------|------|------|
| PT-M4-01 | fingerprint skip 对接；**不**写入 G-PT 计算 | ☐ |

---

## 8. M5 · 门禁与默认开（P0）

| 任务 ID | 任务 | 状态 |
|---------|------|------|
| PT-M5-01 | `equivalence_check.py` 活 diff | ☐ |
| PT-M5-02 | `gate.py` 聚合 pytest + record | ☐ |
| PT-M5-03 | `lint_pt_default_flags.py` | ☐ |
| PT-M5-04 | CI：PR unit；push integration；validate from-record | ☐ |
| PT-M5-05 | `nightly-windows-pt.yml`（阻塞 G1 默认开） | ☐ |
| PT-M5-06 | 默认开 PR：`--check-default-on` block | ☐ |

### 8.1 CI 策略摘要

```text
PR:     PT unit +（可选）gate --require-schema-only
push:   test_pt_* integration
validate: gate --from-record --strict
G1/G2 PR（改 defaults）: --check-default-on block
nightly: Windows spawn
```

注意：若仅改 `docs/acceptance-records/**`，确认 CI paths 不会被 ignore；默认开 PR 须同时改 `travelogue/` 或专用 workflow。

---

## 9. 回滚

| Flag | 动作 |
|------|------|
| `pipeline.parallel_ingest: false` | 逐张 ingest |
| `llm.narrate_concurrency: 1` | 逐章 LLM |
| 全关 | = P7 行为面 |

删除 DoD：见 PRD D-PT-13 / ARCH-OPT §3.3。

---

## 10. 开放实现细节（不阻塞 Kickoff）

| ID | 问题 | 倾向 |
|----|------|------|
| IMP-01 | provisional WebP 用 temp 子目录还是 `.partial/` | temp + commit rename |
| IMP-02 | Studio 内 `min_photos` 是否提高到 24 | dogfood 后定 |
| IMP-03 | 共享 backoff 放 `llm/client.py` 还是 narrate 包装层 | 优先 client 可复用 |
| IMP-04 | checkpoint 是否与 `persist_every_n` 解耦为独立键 | 首版可同频，文档注明 |

---

## 11. 修订历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-07-11 | 初稿 · 对齐 PRD v0.2 评审决议 |
| v0.2 | 2026-07-11 | 对齐 PRD v0.3：Phase A Kickoff 约束与预算 |
