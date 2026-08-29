# PPX W1 · Windows 取消抽检 + 基准机 · 2026-08-28

| 属性 | 内容 |
|---|---|
| **对应 PRD** | [PRD-PIPELINE-PERF-EXECUTION-V1.md](../PRD-PIPELINE-PERF-EXECUTION-V1.md) |
| **验收清单** | [ACCEPTANCE-PIPELINE-PERF-EXECUTION-V1.md](../ACCEPTANCE-PIPELINE-PERF-EXECUTION-V1.md) |
| **W0 对照** | [ppx-w0-baseline-2026-08-28.md](./ppx-w0-baseline-2026-08-28.md) |
| **状态** | **AC-PPX-03 / 08 / 10 本机通过** · 未做 3×cold + 3×warm，未跑完整 narrate/render |
| **日期** | 2026-08-28 |
| **原始 JSON** | [ppx-w1-cancel.json](./ppx-w1-cancel.json) · [ppx-w1-oom36.json](./ppx-w1-oom36.json) · [ppx-w1-bench.json](./ppx-w1-bench.json) |
| **复现脚本** | `python scripts/ppx_windows_accept.py` |

---

## 1. 机器与 K7

| 项 | 值 |
|---|---|
| CPU | Intel Core Ultra 5 125H · 18 逻辑核 |
| RAM | 31.5 GB |
| OS | Windows 10 (win32 10.0.26200) |
| Defender 实时防护 | **开** |
| `config.yaml` `parallel_ingest` | **true**（workers=0 auto，min_photos=12）· 未改仓库默认 |
| frozen onedir | 否 · 源码树 |

---

## 2. AC-PPX-03 取消抽检

经 `ImportSubprocess.start()` 导入 16 张合成 JPEG（`parallel_ingest=true`，workers=2），池起来后 `cancel()`。

| 项 | 结果 |
|---|---|
| 导入 PID | 45168 |
| 取消后导入进程仍活着 | 否 |
| 取消后新增孤儿 python | **无** |
| `.ingest-partial` / `.materialize-partial` | **无** |
| 结论 | **通过** |

---

## 3. AC-PPX-08 36MP

4 张合成 7360×4912 JPEG，规划 `workers=10`。

| 项 | 结果 |
|---|---|
| 入库 | 4 |
| `ingestWorkers` / requested | 3 / 3 |
| 降额 | **是** · `memory_cap_ram` |
| 长边中位 | 7360 |
| fallback | false |
| 残留 partial | 无 |
| OOM | 无 |
| 结论 | **通过** |

纯色夹具解码仍按 36MP 计 RAM，所以降额来自 RAM 预算而不是长边表（长边表本应 ≤4）。无孤儿、无 OOM，满足本条。

---

## 4. AC-PPX-10 分档性能

同机、同相册源文件（`D:\Photos\…`）。每档 **1 次 cold**：串行 workers=1 对照并行（高分钉 4w，中分钉 8w）。只测 **ingest + 物化**（W0 可归因 85.5%）。物化只选前 32 张，避免 121/134 全量高清把墙钟拉去比门槛。关 vision / 人脸 / 美学，因此 **绝对秒数不可直接对拍 W0**；门槛看同脚本串并行加速比。

| 相册 | 张 | 档 / w | 长边中位 | ingest 串→并 | 加速 | 物化 串→并 | 加速 | I+M 降幅 |
|---|---:|---|---:|---|---:|---|---:|---:|
| demo-49551086fe 华农油菜花 | 31 | 高分 4 | 6504 | 58.9→19.0 s | **3.10×** | 34.4→6.8 s | **5.06×** | 72% |
| demo-65db8fd377 凯哥拍摄精选4 | 57 | 高分 4 | 5366 | 79.4→22.8 s | **3.48×** | 22.0→5.1 s | **4.31×** | 73% |
| demo-81d3442e92 珠海东澳岛 | 121 | 高分 4 | 5648 | 190.7→54.8 s | **3.48×** | 29.3→6.0 s | **4.88×** | 72% |
| demo-e52494839a 斯里兰卡风光 | 134 | 中分 8 | 4430 | 190.2→38.2 s | **4.98×** | 25.9→5.7 s | **4.54×** | 80% |

门槛：

| 档 | ingest | 物化 | 121/134 E2E |
|---|---|---|---|
| 高分 4w | ≥1.4× · **过** | ≥2.2× · **过** | ≥30%。用本脚本串行 I+M + W0 的 curate/render 作「其余阶段」：121 约 271 s→112 s（**59%**） |
| 中分 8w | ≥1.8× · **过** | ≥2.5× · **过** | ≥35%。同上估 134 约 270 s→98 s（**64%**） |

并行物化自动工人数落到 9（CPU/2 与 RAM），高于钉死的 ingest 4/8。这是物化加速偏高的原因之一，记录在案，不把它写成对外 4-worker 承诺。

未做：3×cold / 3×warm 中位；完整 narrate/render；与 W0 绝对秒对齐（W0 开了人脸等）。

---

## 5. 结论

| ID | 结论 |
|---|---|
| **AC-PPX-03** | **通过** |
| **AC-PPX-08** | **通过** |
| **AC-PPX-10** | **通过（1×cold · I+M 切片）** |

实现签字：2026-08-28 本机抽检。QA / 架构口头 Go：2026-08-29（合入后补签 K6）。三句：M1 关闭；M2 不开工；仓库 `parallel_ingest` 继续默认 `false`。
