# PPX W0 基线 · 2026-08-28

| 属性 | 内容 |
|---|---|
| **对应 PRD** | [PRD-PIPELINE-PERF-EXECUTION-V1.md](../PRD-PIPELINE-PERF-EXECUTION-V1.md) |
| **性质** | 实施前冻结的对照数字。绝对秒数不作 CI 红灯。 |
| **采集** | 只读 `trips/*/trip.json` timings；未跑会改写 trip 的作业 |
| **日期** | 2026-08-28 |

---

## 1. 现网完成运行（串行回退）

来源：2026-08-24 至 2026-08-28 的 5 个 rendered/exported 相册。全部 `ingestWorkers=1`，`ingestParallelFallback=1`。

| Trip | 资产数 | ingest(s) | 物化(s) | curate(s) | render(s) | workers / 状态 |
|---|---:|---:|---:|---:|---:|---|
| demo-49551086fe | 31 | 74.3 | 60.9 | 11.9 | 5.9 | 1 / 回退 |
| demo-65db8fd377 | 57 | 117.1 | 75.2 | 21.5 | 14.2 | 1 / 回退 |
| demo-d21946c6a9 | 31 | 114.9 | 57.2 | 26.6 | 16.3 | 1 / 回退 |
| demo-81d3442e92 | 121 | 266.1 | 186.3 | 40.4 | 11.0 | 1 / 回退 |
| demo-e52494839a | 134 | 295.5 | 207.9 | 45.6 | 8.3 | 1 / 回退 |

按阶段耗时加权占比（可归因阶段）：

| 阶段 | 占比 |
|---|---|
| ingest | 51.0% |
| 高清物化 | 34.5% |
| curate | 8.6% |
| render | 3.3% |
| embed | 2.5% |
| cluster | 0.1% |

ingest + 物化 = **85.5%**。

M1 对照样本冻结为 **31 / 57 / 121 / 134** 四档。两枚 31 张保留，避免只拿较快的那次当基线。

---

## 2. 2026-07-19 同机并行探针（仍有效）

来源：[PRD-PIPELINE-PERF-V1.md](../PRD-PIPELINE-PERF-V1.md) §1.3。24 张扫描 / 16 张入库。

| 模式 | 总耗时 | 加速比 | 降幅 |
|---|---|---|---|
| 串行 | 102.7 s | 1× | — |
| 4 workers | 69.6 s | **1.47×** | 32% |
| 8 workers | 48.2 s | **2.13×** | 53% |

另一组 per-photo：串行 6.4 s · par4 4.4 s · par8 3.0 s。

**本波禁止把「4-worker 降 60%」写进门禁或对外承诺。** 60% 更接近 8-worker。高分相册护栏会落在 4-worker 档。

---

## 3. Amdahl 估测（只作规划，不作承诺）

假设其余阶段 14.5% 不动：

| 场景 | ingest | 物化 | 估测 E2E 降幅 |
|---|---|---|---|
| 乐观 8w / 物化 3.5× | 2.1× | 3.5× | ~51% |
| 现实 4w 高分 / 物化 2.5× | 1.47× | 2.5× | ~37% |
| 只修 daemon、合并仍等齐 | ~1.3× | ~1.5× | ~22% |

M1 出口必须超过「只修 daemon」档。分档门槛见 PRD §2.2。

---

## 4. 现网测试缺口（摸底，勿再探）

| 测试 | 缺口 |
|---|---|
| `tests/integration/test_pt_ingest_windows_spawn.py` | 直接 `ingest_into_trip`；`workers >= 1` 允许 fail-open |
| `tests/unit/orchestrator/test_pipeline_timings_absorb.py` | 只证明遥测不被抹掉，不证明并行发生 |
| `tests/unit/web/test_studio_subprocess.py` | 覆盖事件与取消，不断言 `daemon is False`，不 `start()` 真导入 |
| `tests/unit/media/test_parallel_ingest_workers.py` | 规划函数单测；`median=None → 10` 与本波未知边上限定 6 冲突，M1 须改断言 |

---

## 5. 代码锚点（2026-08-28）

| 现象 | 位置 |
|---|---|
| daemon=True | `travelogue/web/studio_subprocess.py` · `ImportSubprocess.__init__` |
| 池启动失败返回 False | `travelogue/media/ingest_parallel.py` · `run_parallel_ingest_loop` |
| 静默 fallback | `travelogue/media/ingest.py` · 并行 `ok` 分支 |
| 规划未传长边 | 同上 · `resolve_parallel_ingest_plan(..., photo_count=)` |
| 物化串行 + 线程改 trip | `travelogue/media/derivatives.py` · `ensure_derivatives_for_trip` / `DerivativeMaterializer` |
| 同步物化双工 | `travelogue/orchestrator/run.py` · render 前 join + `ensure_derivatives_for_trip` |
| peek 已存在 | `travelogue/media/image_ops.py` · `peek_image_meta` |

---

## 6. 本机开工时补登（实施者填）

| 项 | 值 |
|---|---|
| 机器 | |
| `config.yaml` 的 `parallel_ingest` | |
| 是否 frozen onedir | |
| Defender 实时防护 | |
