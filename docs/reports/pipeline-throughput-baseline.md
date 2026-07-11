# Pipeline Throughput · 性能基线登记（人读）

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-PIPELINE-THROUGHPUT.md](../PRD-PIPELINE-THROUGHPUT.md) v0.3 |
| **机器可读** | [pipeline-throughput-perf-eval.json](../acceptance-records/pipeline-throughput-perf-eval.json) |
| **Config** | [config-pipeline-throughput.example.yaml](../config-pipeline-throughput.example.yaml) |
| **状态** | **Ingest dogfood 已登记 · e2e/narrate 待补 · 产品默认仍 off** |
| **更新日期** | 2026-07-11 |

## 登记 SOP（摘自 PRD §8.3）

1. 冻结 config（PT flags off = baseline）。
2. `python scripts/pipeline_throughput_benchmark.py --run-microbench --album-dir <相册> --compare-parallel --stages ingest --repeats 2 --workers 4`
3. 同机同 commit 开 flag 跑 candidate（上式已含 A/B）。
4. 写入 [pipeline-throughput-perf-eval.json](../acceptance-records/pipeline-throughput-perf-eval.json)；`gate --from-record --strict` 在 AC 填齐后启用阻断。
5. 换机重登须 `--replace-baseline` + 理由。

## 本机记录（2026-07-11）

| 项 | 值 |
|----|-----|
| 日期 | 2026-07-11 |
| 机器 / 档位 | Windows 11 · S2 · 31.5 GB RAM |
| CPU | Intel64 Family 6 Model 170 |
| commit | `7767a9c`（feat/pipeline-throughput-phase-a） |
| 相册 proxy≈100 | `D:\Photos\凯哥拍摄精选4`（58 张扫描 → 57 保留） |
| 相册 proxy≈250 | `D:\Photos\张智慧精选2`（251 张扫描 → 223 保留） |
| baseline ingest_58 | **315714 ms**（中位，n=2） |
| candidate ingest_58 | **131284 ms**（workers=4） |
| ingest drop_58 | **58.42%**（门槛 −25% / stretch −35% → 双过） |
| baseline ingest_251 | **1245016 ms**（中位，n=2） |
| candidate ingest_251 | **492832 ms**（workers=4） |
| ingest drop_251 | **60.42%**（门槛 −25% / stretch −35% → 双过） |
| baseline pipeline_58（ingest+cluster+curate） | **599037 ms**（中位，n=2） |
| candidate pipeline_58 | **307914 ms**（workers=4） |
| pipeline e2e drop_58 | **48.6%**（相对 G-PT-01 门槛 −18% / stretch −25% → 双过；不含 narrate/render） |
| studio e2e 250 | 待补 |
| narrate ≥6 章 | 待真实 LLM dogfood（AC-PT-07） |
| 备注 | 仅切换 `parallel_ingest`；`narrate_concurrency` 仍为 1；**未**改产品默认 |

## 门槛 vs Stretch

| 指标 | 门槛 | Stretch | 本机 ingest |
|------|------|--------|-------------|
| ingest（≈100 proxy） | −25% | −35% | **−58.4%** ☑ |
| ingest（≈250） | −25% | −35% | **−60.4%** ☑ |
| e2e 100 / 250 | −18% / −22% | −25% / −30% | **−48.6%**（58 张 pipeline）☑ / 250 待补 |
| narrate ≥6 | −30% | −40% | 待补 |

默认开 flag 只认 **门槛** + **G-PT-12**；stretch 用于宣传与 dogfood 目标。
