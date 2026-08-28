# 流水线提速 V1 · 验收清单

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-PIPELINE-PERF-V1.md](./PRD-PIPELINE-PERF-V1.md) **v0.2** |
| **评审纪要** | [pipeline-perf-v1-review-2026-07-19.md](./acceptance-records/pipeline-perf-v1-review-2026-07-19.md) |
| **实施清单** | [IMPLEMENTATION-PIPELINE-PERF-V1.md](./IMPLEMENTATION-PIPELINE-PERF-V1.md) |
| **对比数据** | [pipeline-perf-v1-compare-latest.json](./acceptance-records/pipeline-perf-v1-compare-latest.json) |
| **状态** | **合入 master（人工放行）** · 2026-08-28 起执行链验收改走 [ACCEPTANCE-PIPELINE-PERF-EXECUTION-V1.md](./ACCEPTANCE-PIPELINE-PERF-EXECUTION-V1.md) |
| **日期** | 2026-07-19 |
| **分支** | `feat/pipeline-perf-v1` |

> **验收原则**
>
> 1. E-A（重构类）走严格等价；E-B（`face_detect_max_edge` / `webp_method`）允许受控漂移，须狗粮签字后方可锁默认。  
> 2. 绝对时长仅基准机记录，不作为远程 CI 红灯（MF-06）。  
> 3. `srcset` 只登记已落盘文件；物化不扩公开 pipeline 状态机。

---

## 1. 里程碑

| 里程碑 | 编码 | 验收 |
|--------|------|------|
| **M1** timings / workers / E-B 默认 | ✅ | ✅ AC-PPF-01～04 单测；E-B 默认锁死见 §3 |
| **M2** 延迟物化 / scan peek / worker 信号 / NIMA warm / MF-09·10 | ✅ | ✅ 07a 脚本就绪；07b 见 §3；AC-08/09/10 后置 |
| **M3** 预览先行两态 + 导出同步物化 | ✅ | ✅ 狗粮走查通过；AC-11/12 基准机后置 |

---

## 2. 关键 AC

| ID | 结论 | 证据 |
|----|------|------|
| **AC-PPF-01～04** | Pass | 单元测试 + M1 探针 |
| **AC-PPF-05～06** | Pass（工程） | 延迟物化 / fail-closed 单测（含 MF-10 三负例） |
| **AC-PPF-07a** | Pass（脚本就绪） | `scripts/pipeline_perf_equivalence_check.py` · workflow 步骤已加（本轮未跑远程 CI） |
| **AC-PPF-07b** | **Pass · 人工签字** | 产品狗粮「基本正常」· 2026-07-19；E-B 默认保留可回退 flag |
| **E2E 提速** | 记录 | 同机相册 48 张上限：baseline **111.8s** → candidate **68.8s**（**1.62× / −38.5%**）；详见 compare JSON |

---

## 3. AC-PPF-07b · E-B 狗粮签字

| 项 | 内容 |
|----|------|
| **环境** | Windows · Studio `http://127.0.0.1:8766` · 本机 config（`parallel_ingest` 等按需） |
| **走查结论** | 预览/书架两态、换片补图、导出完整性基本正常；E-B 选片轻微差异可接受 |
| **产品签字** | **通过** · 2026-07-19（实现者自测 + 产品确认「基本正常」） |
| **默认锁定** | `face_detect_max_edge=1024` · `webp_method=2` · `deferred_derivatives=true`；回退见 config 注释 |
| **仍默认关** | `parallel_ingest=false` · `aesthetic.warm_learned_on_ingest=false` · `webp_pyramid=false` |

---

## 4. 后置（不挡合入）

| ID | 说明 |
|----|------|
| AC-PPF-08 | exif_transpose spy |
| AC-PPF-09 | 串/并字段旁路双跑 |
| AC-PPF-10 | NIMA warm 命中率 |
| AC-PPF-11 / 12 | 基准机 Playwright + 绝对时长 |

---

## 5. 合入说明

- 远程 GitHub Actions **本轮跳过**（额度用尽）；不以 CI 红/灰为合并阻塞。  
- 工作区本地 `qa-*.png`、`config/output_recipe_*.yaml` **不纳入**本主题提交。
