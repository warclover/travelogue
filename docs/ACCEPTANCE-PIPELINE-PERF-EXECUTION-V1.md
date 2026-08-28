# 流水线提速 V1 执行链 · 验收清单

| 属性 | 内容 |
|---|---|
| **对应 PRD** | [PRD-PIPELINE-PERF-EXECUTION-V1.md](./PRD-PIPELINE-PERF-EXECUTION-V1.md) **v0.1.0** |
| **实施清单** | [IMPLEMENTATION-PIPELINE-PERF-EXECUTION-V1.md](./IMPLEMENTATION-PIPELINE-PERF-EXECUTION-V1.md) |
| **W0 基线** | [acceptance-records/ppx-w0-baseline-2026-08-28.md](./acceptance-records/ppx-w0-baseline-2026-08-28.md) |
| **状态** | **本机抽检通过** · 已合入 [#72](https://github.com/warclover/travelogue/pull/72) · 记录见 [ppx-w1-windows-bench-2026-08-28.md](./acceptance-records/ppx-w1-windows-bench-2026-08-28.md) |
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
| **M1** 进程契约 / 滑窗 / RAM / 并行物化 | ☑ | ☑ AC-PPX-01～11 本机有证据；08/10 为 1×cold I+M 切片 |
| **M2** 长图 / 拼图 | 不开工 | 设计已冻结于 PRD §8 |

---

## 2. AC 对照

| ID | 结论 | 证据 |
|---|---|---|
| **AC-PPX-01** 真子进程并行 | ☑ 自动化绿 | `tests/integration/studio/test_import_subprocess_parallel.py` |
| **AC-PPX-02** 失败有 reason | ☑ 自动化绿 | `test_ppx_execution.py` · pool_start_failed |
| **AC-PPX-03** 取消无孤儿 / 无临时目录 | ☑ 本机通过 | W1 记录 · ImportSubprocess.cancel 后无孤儿 / 无 partial |
| **AC-PPX-04** 长边中位数入规划 | ☑ 自动化绿 | `test_parallel_ingest_workers.py` · 7360 → ≤4 |
| **AC-PPX-05** 未知边 ≤6 + RAM 降额 | ☑ 自动化绿 | `None→6` + `workers_ram_cap` mock |
| **AC-PPX-06** 滑窗 firstProgressMs | ☑ 自动化绿 | `test_parallel_ingest_writes_first_progress_ms` |
| **AC-PPX-07** 物化不改 worker 侧 trip | ☑ 自动化绿 | `test_materialize_worker_does_not_mutate_trip` |
| **AC-PPX-08** 36MP 无 OOM | ☑ 本机通过 | 4×7360 合成 · 降额 `memory_cap_ram` · workers=3 |
| **AC-PPX-09** E-A 等价（无 hash 门） | ☑ 脚本无 hash 门 | `pipeline_perf_equivalence_check.py` |
| **AC-PPX-10** 分档性能（人工） | ☑ 1×cold I+M 过门槛 | 高分 4w ingest 3.1–3.5× · 中分 8w 4.98×；见 W1 记录 |
| **AC-PPX-11** 同步物化齐档空转 | ☑ 自动化绿 | `test_sync_materialize_is_noop_when_already_ready` |
| **AC-PPX-12** spawn smoke 不再假绿 | ☑ | `test_pt_ingest_windows_spawn.py` |

---

## 3. 基准机记录（AC-PPX-10）

| 项 | 填写 |
|---|---|
| 机器指纹 | Ultra 5 125H · 31.5 GB · Win10 · Defender 开 |
| 相册 | 31 / 57 / 121 / 134；中位 6504 / 5366 / 5648 / 4430 |
| 档 | 高分 4w / 中分 8w |
| cold/warm | **1×cold**（未跑 3+3） |
| ingest 加速比 | 高分 3.10–3.48× · 中分 4.98× |
| materialize 加速比 | 高分 4.31–5.06× · 中分 4.54×（物化自动到 9w） |
| E2E 降幅 | I+M 72–80%；加上 W0 其余阶段估 121≈59% · 134≈64% |
| 对照 W0 | 绝对秒不可对拍（本轮关人脸/美学）；加速比看同脚本串并行 |

高分档门槛：ingest ≥1.4× · 物化 ≥2.2× · 121/134 E2E 中位 ≥30%。  
中分档门槛：ingest ≥1.8× · 物化 ≥2.5× · E2E ≥35%。

---

## 4. 签字

| 角色 | 结论 | 日期 |
|---|---|---|
| 实现 | ☑ 本机抽检 | 2026-08-28 |
| QA | ☐ | |
| 架构 | ☐ | |
| 产品（仅当要改 `parallel_ingest` 默认 true） | 本波不需要 | — |
