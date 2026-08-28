# 流水线提速 V1 执行链 · 验收清单

| 属性 | 内容 |
|---|---|
| **对应 PRD** | [PRD-PIPELINE-PERF-EXECUTION-V1.md](./PRD-PIPELINE-PERF-EXECUTION-V1.md) **v0.1.0** |
| **实施清单** | [IMPLEMENTATION-PIPELINE-PERF-EXECUTION-V1.md](./IMPLEMENTATION-PIPELINE-PERF-EXECUTION-V1.md) |
| **W0 基线** | [acceptance-records/ppx-w0-baseline-2026-08-28.md](./acceptance-records/ppx-w0-baseline-2026-08-28.md) |
| **状态** | **编码完成** · AC-PPX-08/10 待基准机 · 未合入主分支 |
| **日期** | 2026-08-28 |

> **验收原则**
>
> 1. 并行可达必须经 `ImportSubprocess.start()`，不得用直接 `ingest_into_trip` 替代。  
> 2. E-A 严格等价；WebP 不用全量文件 hash。  
> 3. 绝对时长仅基准机记录，不进 CI。  
> 4. 取消回收与并行可达同级。  
> 5. 性能按高分 4w / 中分 8w 分档，禁止单一乐观门禁。

---

## 1. 里程碑

| 里程碑 | 编码 | 验收 |
|---|---|---|
| **M0** 埋点骨架 + 杀伤测试先红 + W0 | ☑ | ☑ QA-PPX-01/02 已绿；AC-PPX-12 断言已收紧 |
| **M1** 进程契约 / 滑窗 / RAM / 并行物化 | ☑ 编码完成 · 待基准机 | ☑ AC-PPX-01～07、09、11 有自动化；☐ AC-PPX-08/10 基准机 |
| **M2** 长图 / 拼图 | 不开工 | 设计已冻结于 PRD §8 |

---

## 2. AC 对照

| ID | 结论 | 证据 |
|---|---|---|
| **AC-PPX-01** 真子进程并行 | ☑ 自动化绿 | `tests/integration/studio/test_import_subprocess_parallel.py` |
| **AC-PPX-02** 失败有 reason | ☑ 自动化绿 | `test_ppx_execution.py` · pool_start_failed |
| **AC-PPX-03** 取消无孤儿 / 无临时目录 | ◑ 自动化覆盖临时目录；Windows 进程树抽检仍待基准机 | `test_cancel_cleans_ingest_partial` + `cancel()` 未 start 安全 |
| **AC-PPX-04** 长边中位数入规划 | ☑ 自动化绿 | `test_parallel_ingest_workers.py` · 7360 → ≤4 |
| **AC-PPX-05** 未知边 ≤6 + RAM 降额 | ☑ 自动化绿 | `None→6` + `workers_ram_cap` mock |
| **AC-PPX-06** 滑窗 firstProgressMs | ☑ 自动化绿 | `test_parallel_ingest_writes_first_progress_ms` |
| **AC-PPX-07** 物化不改 worker 侧 trip | ☑ 自动化绿 | `test_materialize_worker_does_not_mutate_trip` |
| **AC-PPX-08** 36MP 无 OOM | ☐ | 基准机 / 故障夹具 |
| **AC-PPX-09** E-A 等价（无 hash 门） | ☑ 脚本无 hash 门 | `pipeline_perf_equivalence_check.py` |
| **AC-PPX-10** 分档性能（人工） | ☐ | 基准机 |
| **AC-PPX-11** 同步物化齐档空转 | ☑ 自动化绿 | `test_sync_materialize_is_noop_when_already_ready` |
| **AC-PPX-12** spawn smoke 不再假绿 | ☑ | `test_pt_ingest_windows_spawn.py` |

---

## 3. 基准机记录（AC-PPX-10）

| 项 | 填写 |
|---|---|
| 机器指纹 | CPU / RAM / OS / 实时防护是否开 |
| 相册 | 31 / 57 / 121 / 134 张；长边中位 |
| 档 | 高分 4w / 中分 8w |
| cold/warm | 各 3 次中位 |
| ingest 加速比 | |
| materialize 加速比 | |
| E2E 降幅 | |
| 对照 W0 | 见基线文档绝对秒数 |

高分档门槛：ingest ≥1.4× · 物化 ≥2.2× · 121/134 E2E 中位 ≥30%。  
中分档门槛：ingest ≥1.8× · 物化 ≥2.5× · E2E ≥35%。

---

## 4. 签字

| 角色 | 结论 | 日期 |
|---|---|---|
| 实现 | ☐ | |
| QA | ☐ | |
| 架构 | ☐ | |
| 产品（仅当要改 `parallel_ingest` 默认 true） | 本波不需要 | — |
