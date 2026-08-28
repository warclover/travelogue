# 流水线提速 V1 执行链 · 实施清单

| 属性 | 内容 |
|---|---|
| **PRD** | [PRD-PIPELINE-PERF-EXECUTION-V1.md](./PRD-PIPELINE-PERF-EXECUTION-V1.md) **v0.1.0** |
| **验收** | [ACCEPTANCE-PIPELINE-PERF-EXECUTION-V1.md](./ACCEPTANCE-PIPELINE-PERF-EXECUTION-V1.md) |
| **W0 基线** | [acceptance-records/ppx-w0-baseline-2026-08-28.md](./acceptance-records/ppx-w0-baseline-2026-08-28.md) |
| **上游** | [PRD-PIPELINE-PERF-V1.md](./PRD-PIPELINE-PERF-V1.md) · [IMPLEMENTATION-PIPELINE-PERF-V1.md](./IMPLEMENTATION-PIPELINE-PERF-V1.md) |
| **状态图例** | ☑ 已落地 · ◑ 部分 · ☐ 未开始 |
| **更新日期** | 2026-08-28 |

> **Kickoff**：M0 可在评审通过后立即开工。M1 编码不得在 AC-PPX-01 杀伤测试先红之前开始合入。产品默认 `parallel_ingest` 保持 `false`。

---

## 0. 开工门槛（写第一行产品代码前）

| # | 项 | 状态 | 说明 |
|---|---|---|---|
| K1 | PRD v0.1 入仓 | ☑ | 本文档同期入仓 |
| K2 | W0 基线冻结 | ☑ | 5 个现网 trip + 7 月探针数字 |
| K3 | DPI 所有权 | ☑ | 见 §1；禁止新增强制 edition 分支 |
| K4 | 设计冻结（§2） | ☑ | 进程树 / 取消 / 滑窗 / RAM / 物化合并 |
| K5 | 杀伤测试规格 | ☑ | §4；M0 第一提交按此写红测试 |
| K6 | 评审通过 | ☐ | 架构 + QA 至少口头 Go 再合 M1 |
| K7 | 本机 `parallel_ingest` 现状登记 | ☑ | 本机 `config.yaml` 为 `true` / workers=0；仓库默认仍 `false` |

K6 未过不得把 M1 合入主分支。K1–K5 已在本波文档完成。

---

## 1. 所有权与 DPI

2026-08-28 已跑 `python scripts/lint_dual_pipeline_ownership.py --explain <file>`：

| 文件 | 所有权 | 本波约束 |
|---|---|---|
| `travelogue/web/studio_subprocess.py` | allowlist · shared shell | 可改进程生命周期；不要加 edition 分支 |
| `travelogue/web/studio_jobs.py` | shared Studio | 取消回收导入进程 |
| `travelogue/media/ingest.py` | 未登记 · 共享 | 只传 `medianLongEdgePx`、接结构化结果；**新 dual-pipeline 标记会失败** |
| `travelogue/media/ingest_parallel.py` | 未登记 · 共享 | 滑窗 / RAM / 结构化结果 |
| `travelogue/media/ingest_worker.py` | 未登记 · 共享 | 本波尽量不改 worker 热路径 |
| `travelogue/media/derivatives.py` | 未登记 · 共享 | 并行物化 + 主进程合并 |
| `travelogue/orchestrator/run.py` | 未登记 · 共享 | join 后同步路径空转 |
| `travelogue/domain/pipeline_view.py` | 共享 | absorb 新 timings 键 |
| `travelogue/types/trip_telemetry.py` | 共享 | 新键 |
| `travelogue/export/platform_longshot.py` | 未登记 | **本波不改**（M2） |

夹具：合成 JPEG + 临时 `trips_dir`。禁止从 portfolio 测试读 `phase16-dogfood`，也禁止本波测试读 `editorial_series` 夹具。`trip.render_golden.json` 可克隆做等价，不要当 journal-only。

合入前跑：`pytest -m pipeline_isolation -q`（若本波未碰读者面，预期无新失败）。

---

## 2. 设计规格（M1 开工前冻结）

### 2.1 进程树

```
Studio 主进程 (HTTP)
  └── ImportSubprocess  spawn, daemon=False     ← 唯一隔离边界
        └── ProcessPoolExecutor(mp_context=同一 spawn)
              └── ingest_worker / materialize_worker
```

- 池在导入进程内创建，不在 Flask 进程内。
- `ProcessPoolExecutor(mp_context=self._ctx)` 或模块级 `mp.get_context("spawn")`，禁止默认上下文与导入进程不一致。
- 主进程退出：`studio_jobs` / lifecycle 必须 `join` 导入进程；非 daemon 不会随父进程自动消失。

### 2.2 取消协议

超时建议：pool shutdown/join **5s**，导入进程 join **8s**，其后强制终止并枚举直接子进程。

```
cancel Event.set()
  → 停 submit / 协作跳出 merge
  → pool.shutdown(wait=False, cancel_futures=True)
  → pool join ≤5s
  → 导入进程 join ≤8s
  → 仍活着则 terminate 导入进程
  → 枚举并回收其直接子进程（Windows：CreateToolhelp32Snapshot 或已有进程工具；有余力再加 Job Object）
  → rmtree .ingest-partial/<batch> 与物化临时根
```

禁止：只 `self._process.terminate()`。

现有 `ImportSubprocess._cancel` 与 `_import_worker` 对 `E_STUDIO_CANCELLED` 的处理保留，向池下传同一 Event。

### 2.3 结构化结果

```python
@dataclass
class ParallelIngestOutcome:
    ok: bool
    reason: str | None          # §6 原因码
    requested_workers: int
    effective_workers: int
    spawn_ms: float
    first_progress_ms: float | None
```

`ingest.py`：`ok` 才标 `fallback=false`；否则 fail-open 并写 `reason`。不要再 `if not bool: 静默串行`。

### 2.4 滑窗合并（watermark）

```
next_commit = 0
buffer: dict[int, WorkerResult] = {}
submit 全部 jobs（或按 in_flight=workers 限流 submit，推荐限流）
for fut in as_completed:
    buffer[idx] = result
    while next_commit in buffer:
        merge_one_worker_result(buffer.pop(next_commit), processed=next_commit+1)
        if first_progress_ms is None:
            first_progress_ms = now - t0
        next_commit += 1
```

`in_flight` 上限 = `effective_workers`。不要先 `list(as_completed)` 再 for-range。

### 2.5 长边中位数

扫描路径已调用 `peek_image_meta`（`ingest._peek_photo` / `user_tier._scan_one_dir`）。

推荐：`_scan_one_dir` 在已 peek 的宽高上累加 `long_edges`，`scan_stats["medianLongEdgePx"] = median(max(w,h))`。

`ingest_into_trip`：

```python
resolve_parallel_ingest_plan(
    resolved_app,
    photo_count=total_photos,
    median_long_edge_px=scan_stats.get("medianLongEdgePx"),
)
```

增量 pending 路径：对 `photo_tiers` 再 peek 一次头（无像素），写入同一键。

### 2.6 共享 RAM 预算

新函数（建议 `ingest_parallel.py`）：

```
estimate_pixels(median_long_edge) ≈ long * long * 3/4   # 只知长边时按 4:3
per_image_mb = pixels * 4 / 1e6
per_worker_mb = per_image_mb * (1 + widths_in_flight) + 80
usable_mb = max(512, available_ram_mb * 0.45 - 1536)   # 1.5GB 浏览器预留
ram_cap = max(1, floor(usable_mb / per_worker_mb))
workers = min(cpu_cap, long_edge_cap, ram_cap)
```

- ingest：`widths_in_flight=2`（800/1600）
- materialize：`widths_in_flight=2`（2400/3200，同一解码）
- 可用内存：Windows `GlobalMemoryStatusEx`（ctypes），POSIX `os.sysconf`。失败则只走长边表，且 **未知长边上限 6**（改现网 `workers_memory_cap(None)==10`）
- **不新增 psutil**

现有单测 `test_workers_memory_cap_by_long_edge` 的 `None → 10` **必须改成 6**，并补 RAM mock 用例。

### 2.7 物化并行

```
主进程: 收集缺档资产列表（只读 trip）
worker: (asset_id, source_path, widths, focal, tmp_dir) 
        → 解码一次 → 写临时 WebP → 返回 {asset_id, widths, rel_paths, out_w, out_h}
主进程: 按 assets[] 原序把文件移到 assets/，合并 srcset / derivedPlan / displayFile
        一次 save
```

禁止：worker 持有 trip dict；`DerivativeMaterializer` 线程内 `ensure_derivatives_for_trip(trip)`。

`DerivativeMaterializer.start` 可仍用线程做「调度」，但线程只跑池+收元数据到 `self._pending`，join 后主线程合并。更干净：start 只启动池，join 在主线程合并。

orchestrator `run.py` 现顺序：join → save → load → `ensure_derivatives_for_trip`。齐档时后者必须 `widths_written=0`（AC-PPX-11）。

### 2.8 等价

沿用 `scripts/pipeline_perf_equivalence_check.py`。**删除或不要新增**「并行物化文件 hash 一致」断言。比较：宽度集合、像素、quality 参数、抽样 phash。

---

## 3. 里程碑任务

### M0 · 基线与杀伤测试

| ID | 任务 | 位置 | 状态 |
|---|---|---|---|
| DOC-PPX-01 | PRD / IMPLEMENTATION / ACCEPTANCE / W0 | `docs/` | ☑ |
| BE-PPX-01 | timings TypedDict 增键（可先声明后写入） | `types/trip_telemetry.py` | ☑ |
| QA-PPX-01 | `ImportSubprocess` `daemon is False` 单测 | `tests/unit/web/test_studio_subprocess.py` | ☑ |
| QA-PPX-02 | `ImportSubprocess.start()` 并行杀伤测试（先红） | 新 `tests/integration/studio/test_import_subprocess_parallel.py` | ☑ 已绿 |
| QA-PPX-03 | 收紧 `test_pt_ingest_windows_spawn`：fail-open 不再算并行成功 | `tests/integration/test_pt_ingest_windows_spawn.py` | ☑ |

### M1 · 执行链

| ID | 任务 | 位置 | 状态 |
|---|---|---|---|
| BE-PPX-02 | 非 daemon + 退出 join | `studio_subprocess.py` · `studio_jobs.py` | ☑ |
| BE-PPX-03 | 取消协议 + 临时目录清理 | 同上 + `ingest_parallel.py` | ☑ |
| BE-PPX-04 | `ParallelIngestOutcome` + ingest 接线 | `ingest_parallel.py` · `ingest.py` | ☑ |
| BE-PPX-05 | watermark 滑窗 | `ingest_parallel.py` | ☑ |
| BE-PPX-06 | `medianLongEdgePx` 出扫描、入规划 | `user_tier.py` / `ingest.py` | ☑ |
| BE-PPX-07 | RAM 预算 + 未知边上限 6 | `ingest_parallel.py` · 改既有单测 | ☑ |
| BE-PPX-08 | 并行物化 + 主进程合并 | `derivatives.py` · `orchestrator/run.py` | ☑ 主进程合并；orchestrator 同步路径复用 ensure 空转 |
| BE-PPX-09 | 埋点写入（reason / spawn / firstProgress / RSS） | ingest / derivatives | ☑ |
| QA-PPX-04 | AC-PPX-02～07、11 单测 | `tests/unit/media/` · `tests/unit/web/` | ☑ |
| QA-PPX-05 | 等价脚本确认无 hash 门 | `scripts/pipeline_perf_equivalence_check.py` | ☑ 脚本无 hashlib / 文件 hash 门 |
| QA-PPX-06 | 基准机 31/57/121/134 · 高分/中分分档 | 验收记录 | ☑ [ppx-w1-windows-bench-2026-08-28](./acceptance-records/ppx-w1-windows-bench-2026-08-28.md) |

**M1 出口**：QA-PPX-02 绿；AC-PPX-01/03/09 绿；AC-PPX-10 有记录。

### M2 · 不开工

§8 设计已写在 PRD。任务不建。

---

## 4. 杀伤测试规格（M0 第一提交）

### 4.1 单元 · daemon 合同

```python
def test_import_subprocess_is_not_daemon(tmp_path):
    handle = ImportSubprocess(_base_payload(tmp_path))
    assert handle._process.daemon is False
```

今日必红（`daemon=True`）。

### 4.2 集成 · 必须 `start()`

- 合成 ≥12 张 JPEG（小图即可，测的是进程树不是编码）。
- payload 走真实 `_import_worker` 路径，或最小 `run_studio_pipeline` 但 **进程必须由 `ImportSubprocess.start()` 拉起**。
- 子进程内 `AppConfig(pipeline=PipelineConfig(parallel_ingest=True, parallel_ingest_min_photos=12, parallel_ingest_workers=2))`。
- 断言 trip `pipeline.timings.ingestWorkers > 1` 且 `ingestParallelFallback == 0`。
- mark：`integration`；Windows 与 POSIX 都跑。超时给足 spawn（建议 120s）。

不允许：在测试进程里直接 `ingest_into_trip` 来满足本条。

### 4.3 现网 spawn smoke

`test_pt_ingest_process_pool_spawn_smoke` 保留「不崩溃、有资产」。若存在 `ingestParallelFallback`，不得再 `assert workers >= 1` 当作并行证明。并行证明只认 4.2。

---

## 5. 回归必须保持绿

| 测试 | 为什么 |
|---|---|
| `tests/unit/media/test_parallel_ingest_workers.py` | 改 `None→6` 后更新断言，其余档位表不变 |
| `tests/unit/orchestrator/test_pipeline_timings_absorb.py` | 新键也必须能被吸收 |
| `tests/unit/web/test_studio_subprocess.py` | 取消 / 错误码 |
| `tests/unit/media/test_derivatives_deferred.py` 及 ondemand / mf09 / mf10 | 延迟物化合同 |
| `scripts/pipeline_perf_equivalence_check.py` | E-A |
| `tests/unit/media/test_source_resolve_storage.py` AC-MRS-02b | 并行 + 不复制源文件 |

---

## 6. 已知坑（实施时必读）

1. **V1 已假关一次**。任何「直接调 `ingest_into_trip` 且 workers≥1」的测试都不能关闭 AC-PPX-01。
2. **`absorb_pipeline_timing_keys` 只补缺失键**。同一次 flush 若本地 dict 已有 `ingestWorkers=0` 仍会盖掉。写入侧用明确值，不要先写 0 再并行。
3. **`config.demo.yaml` 无 pipeline 段**，默认 `parallel_ingest=false`。杀伤测试必须显式注入 AppConfig，不能依赖仓库默认。
4. **frozen spawn** 已有 `freeze_support`。若杀伤在源码绿、onedir 红，记 ACCEPTANCE 后置，不阻塞源码合入，但必须开 issue。
5. **Pillow WebP 非比特稳定**。不要用文件 hash 当绿。
6. **Windows Defender** 可能串行化刚写入的 WebP，放大 I/O。基准机记录是否实时防护开启。
7. **物化双工**：join 后 `save/load` 再 `ensure_derivatives_for_trip`。若只把文件写在内存 trip 未落盘，同步路径会重做或看到缺档。
8. **不要用 `psutil`**。脚本里有，运行时不要新增依赖。
9. **DPI**：ingest / derivatives / orchestrator 未登记，加 `is_portfolio` 会棘轮红。

---

## 7. 建议提交切分

1. `test(ppx): fail ImportSubprocess daemon and spawn parallel kill test`
2. `fix(ppx): non-daemon import process and cancel reaps children`
3. `fix(ppx): structured parallel ingest with watermark merge`
4. `fix(ppx): pass scan median and shared RAM worker budget`
5. `fix(ppx): parallel materialize with main-process srcset merge`
6. `chore(ppx): timings keys and tighten windows spawn smoke`

每笔必须自带对应测试。禁止把 2–5 揉进一个「性能大提交」。
