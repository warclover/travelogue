# Travelogue · Phase 7 验收标准

> **单轨入口建议**：[ACCEPTANCE.md](./ACCEPTANCE.md)

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-PHASE7.md](./PRD-PHASE7.md) v0.7.0 |
| **关联实施** | [IMPLEMENTATION-PHASE7.md](./IMPLEMENTATION-PHASE7.md) |
| **前置验收** | [ACCEPTANCE-PHASE6.md](./ACCEPTANCE-PHASE6.md) L0 通过 |
| **代号** | P7-Perf · 极速管线 |
| **更新日期** | 2026-05-30 |

---

## 1. 验收环境

### 1.1 通用

- Windows 10/11 · Chrome/Edge 90+
- `pip install -e ".[dev,vision]"`（CLIP 路径验收须 vision extra）
- 启动：`python -m travelogue studio` 或 `start-studio.bat`
- CLIP 权重 **已缓存**（首次下载不计入性能 AC）

### 1.2 设备档位（须登记到 perf-eval）

| 档位 | 参考硬件 | 用途 |
|------|----------|------|
| **S1** | 4C CPU · 16GB · 无独显 | 下限 SLO |
| **S2** | 8C CPU · 16–32GB | **主验收档**（AC-P7-01/02） |
| **S3** | GPU/NPU 可用 | CLIP 加速参考 |

### 1.3 Benchmark 输入

- **固定 commit** + **config 快照**（`docs/config-phase7.example.yaml`）
- 相册集：
  - **B7-REAL-***：≥3 套真实脱敏相册，每套 50–250 张（含 GPS + 混合场景）
  - **B7-FIX-***：CI fixture（`tests/fixtures/clustering/*`）用于 NR 与 1k proxy
- P6 基线数据：同机同集 · 写入 `phase7-perf-eval.json` 的 `baseline.p6` 段

---

## 2. 验收分层与门禁

| 层级 | 含义 | 必达 |
|------|------|------|
| **L0** | 性能 KPI | AC-P7-01/02/03/05/10 |
| **L1** | 质量等价（NR-P7） | AC-P7-04/06/09/11 |
| **L2** | 可观测与回滚 | AC-P7-07/08 |
| **L3** | 稳定性增强 | AC-P7-12 + G0→G3（§8） |

> 发布前必须 **L0+L1+L2** 全部通过。L3 为灰度运营门禁。

---

## 3. 核心验收项（AC-P7）

| ID | 验收项 | 验收方法 | 通过条件 | 状态 |
|----|--------|----------|----------|------|
| **AC-P7-01** | Studio 端到端加速 | S2 · 250 张 · vision on · 冷 embed cache · 5 次取 p50/p95 | `studio_e2e_250` 相对 P6 **−30%**；`studio_e2e_250_p95` 相对 P6 **−25%** 且 `p95 <= p50 * 1.6` | ☐ |
| **AC-P7-02** | Ingest + CLIP 分项加速 | 分阶段 benchmark（同机 5 次） | ingest **−25%**；clip embed **−40%**；`clip_embed_time_250_p95` 相对 P6 **−30%** 且 `p95 <= p50 * 1.8` | ☐ |
| **AC-P7-03** | 增量 embed 加速 | 同 trip 追加 10% 照片 re-import | embed 阶段 **−60%** vs 同集全量 | ☐ |
| **AC-P7-04** | NR-P7 质量等价 | `phase7_equivalence_check.py` + CI | 固定 fixture hash **100%**；真实脱敏集 hash ≥95%；subjectClass batch=逐张 **100%** | ☐ |
| **AC-P7-05** | 内存与 fixture 代理 | 1k fixture + tracemalloc | `pipeline_time_1k` ≤ P6+5%；`peak_memory_1k` 退化 <10% | ☐ |
| **AC-P7-06** | 确定性 | deterministic config 双跑 | 固定 fixture cluster + curate hash **100%**；真实脱敏集 ≥95% | ☐ |
| **AC-P7-07** | 分阶段 telemetry | 检查 trip + benchmark JSON | `pipeline.timings` / `embedStats` / `ingestStats.elapsedMs` 齐全 | ☐ |
| **AC-P7-08** | 可回滚 | 逐项关闭 P7 flags 双跑 | 与 P6 行为一致（NR 100%） | ☐ |
| **AC-P7-09** | Phase 6 质量不退化 | 同 benchmark 集 | `cluster_noise_ratio` ≤ P6+2pp；`event_boundary_f1` ≥ P6；`layout_repeat_streak` ≤ P6 | ☐ |
| **AC-P7-10** | Auto batch 收敛与不劣化 | S1/S2/S3 分档对比 | 自动 batch 耗时不劣于固定默认（95% 样本）且无新增 OOM | ☐ |
| **AC-P7-11** | cache ABI 失配自动重建 | 修改 `cache_abi_version` / config 指纹后重跑 | 自动失效重建成功，NR-P7 通过 | ☐ |
| **AC-P7-12** | 故障注入恢复能力 | 在 cache 写入阶段中断后恢复 | 无半写 trip/cache；可恢复并继续导入 | ☐ |

---

## 4. 质量等价验收（NR-P7）

### 4.1 等价范围（必须一致）

| 路径 | 字段 / 结构 |
|------|-------------|
| Curate | `curation.chapters[].screens`（patternId + slot assetId 序） |
| Cover | `curation.coverByLayout` |
| Clustering | `asset.sceneClusterId`、`asset.subjectClass`、`curation.clustering.segments` |
| Layout search | replan 后屏序（scoring enabled 时） |

### 4.2 允许漂移（documented）

| 字段 | 容差 |
|------|------|
| `quality.meanLuma` | ±0.02 |
| `dominantTone` | ±1 RGB step |
| `pipeline.timings` / `embedStats` | 新增字段 |
| WebP 文件体积 | 不阻断；监控 zip 上限 |

### 4.3 双门槛判定

| 数据集类型 | 门槛 |
|-----------|------|
| 固定 fixture（固定 seed + 固定 config） | `curate_hash_rate=1.0` 且 `cluster_hash_rate=1.0` |
| 真实脱敏集 | `curate_hash_rate>=0.95` 且 `cluster_hash_rate>=0.95` |

### 4.4 NR-P7 自动化

```powershell
python scripts/phase7_equivalence_check.py --write
python -m pytest tests/test_phase7_equivalence.py tests/test_phase7_clip_batch.py -q
python -m pytest tests/test_layout_golden.py -q
```

**通过条件**：exit code 0；双门槛满足 §4.3；`subject_class_agreement` = 1.0。

---

## 5. 验收用例

### TC-P7-01 CLIP Batch 等价

| 项 | 规格 |
|----|------|
| 输入 | ≥50 张真实照片 trip_dir；`vision.batch_size=16` vs `0` |
| 步骤 | 同 seed 双跑 embed；对比 vectors cosine + subjectClass |
| 期望 | subjectClass **100%** 一致；向量余弦距 < 1e-5 |

### TC-P7-02 Ingest 微优化不退化

| 项 | 规格 |
|----|------|
| 输入 | 固定 100 张相册；P6 ingest config vs P7 ingest config |
| 步骤 | 对比 faceCount、focalPoint、dedupe 结果 |
| 期望 | 人脸检测结果一致；dedupe 计数一致；luma/tone 在 §4.2 容差内 |

### TC-P7-03 端到端 Studio 250 张

| 项 | 规格 |
|----|------|
| 输入 | S2 · vision auto/on · 250 张混合相册 |
| 步骤 | Studio 导入 → 预览可用；记录 wall-clock |
| 期望 | 相对 P6 基线 −30%；progress 间隔 ≤20s |

### TC-P7-04A 增量导入（append）10%

| 项 | 规格 |
|----|------|
| 输入 | 已有 trip 225 张 + 追加 25 张 force re-ingest |
| 步骤 | 对比全量 re-import 的 embed 耗时 |
| 期望 | incremental embed **−60%** |

### TC-P7-04B 增量导入（delete）10%

| 项 | 规格 |
|----|------|
| 输入 | 已有 trip 250 张，删除 25 张后 re-import |
| 步骤 | 对比全量 re-import 的 embed 耗时 + NR |
| 期望 | incremental embed **−60%**；NR 通过 |

### TC-P7-04C 增量导入（replace）10%

| 项 | 规格 |
|----|------|
| 输入 | 已有 trip 250 张，替换 25 张（同场景新文件）后 re-import |
| 步骤 | 对比全量 re-import 的 embed 耗时 + NR |
| 期望 | incremental embed **−60%**；NR 通过 |

### TC-P7-05 并行写入事务不变式

| 项 | 规格 |
|----|------|
| 输入 | `pipeline.parallel_embed=true` · 200 张 |
| 步骤 | 在 embed/manifest 写入点注入中断（kill process）后重启导入 |
| 期望 | cache 可恢复；无半写 trip；`subjectClass` 仅批末提交 |

### TC-P7-06 回滚演练

| 项 | 规格 |
|----|------|
| 输入 | P7 全量 fast-path on |
| 步骤 | 按 PRD §13.3 关闭 5 项 config；执行 `scripts/phase7_verify_rollback.py`；重跑 NR-P7 |
| 期望 | 与 P6 产出 hash 一致 |

### TC-P7-07 并行 embed 无 corrupt cache

| 项 | 规格 |
|----|------|
| 输入 | `pipeline.parallel_embed=true` · 200 张 |
| 步骤 | 导入 3 次；校验 `.cluster-cache` |
| 期望 | 无 `E_CLUSTER_CACHE_CORRUPT`；embed 完整 |

### TC-P7-08 Auto batch 跨设备验证

| 项 | 规格 |
|----|------|
| 输入 | S1/S2/S3 各 1 组样本（≥3 套 trip） |
| 步骤 | 固定默认 batch 与 `batch_auto_tune=true` 对比 |
| 期望 | 95% 样本不劣化；无新增 OOM；记录推荐 batch |

### TC-P7-09 cache ABI 失配重建

| 项 | 规格 |
|----|------|
| 输入 | 已存在 `.cluster-cache` 的 trip |
| 步骤 | 提升 `cache_abi_version` 或变更指纹字段后重跑 |
| 期望 | 触发重建；重建后 NR-P7 通过 |

---

## 6. 设备 SLO 验收（PRD §14）

| 指标 | S1 | S2 | S3 |
|------|----|----|-----|
| 250 张 P3-Full 端到端 | <12 min | **<4 min** | <2.5 min |
| 250 张 ingest only | <4 min | **<2 min** | <2 min |
| 250 张 CLIP cold embed | <8 min | **<2.5 min** | <45 s |
| 峰值内存 250 张 | <12 GB | **<16 GB** | <20 GB |

> S2 为主签字档；S1/S3 为参考，不通过时须 documented 降级策略（如 `batch_size=8`）。

---

## 7. 自动化与脚本

```powershell
# 一键门禁（推荐）
python scripts/phase7_gate_run.py --write --strict
# 仅读取记录文件做门禁判定（CI 快速路径）
python scripts/phase7_gate_run.py --from-record --strict

# 性能 benchmark（分阶段）
python scripts/phase7_pipeline_perf.py
python scripts/phase7_pipeline_perf.py --write

# NR-P7 等价
python scripts/phase7_equivalence_check.py
python scripts/phase7_equivalence_check.py --write
python scripts/phase7_verify_rollback.py

# Phase 6 质量守护（不退化）
python scripts/phase6_benchmark_run.py
python scripts/phase6_event_boundary_eval.py

# CI 套件
python -m pytest tests/test_phase7_equivalence.py tests/test_phase7_clip_batch.py tests/test_phase7_ingest_micro.py tests/test_phase7_rollback_flags.py -q
```

---

## 8. 灰度验收（G0–G3）

| 阶段 | 启用范围 | 验收项 | 通过条件 |
|------|----------|--------|----------|
| **G0** | 离线 | AC-P7-01~07 + NR-P7 | 全绿 |
| **G1** | 内测 10% | 仅 P7-A + P7-B flags | AC-P7-09 无退化；无 OOM 事故 |
| **G2** | 内测 50% | + P7-C 并行/预热 + P7-G1/G3 | AC-P7-01/03/10/11 达标 |
| **G3** | 全量 | P0+P1 默认 on | 7 天无 P0；`studio_e2e_250` 无 >15% 退化；AC-P7-12 通过 |

### G0 预检清单

见 [phase7-g0-preflight-checklist.md](./reports/phase7-g0-preflight-checklist.md)。

---

## 9. 失败判定与处置

| 失败条件 | 处置动作 |
|----------|----------|
| 固定 fixture NR <100% 或真实集 NR <95% | **阻塞发布**；定位 fast-path；可单项关闭 |
| AC-P7-09 质量退化 | 冻结 G1+；回滚 web derivative / 共享缩略图 |
| OOM >1% trips | `vision.batch_size` 减半；默认改 8 |
| Auto batch 劣化样本 >5% | 关闭 `batch_auto_tune`，回退固定 batch |
| cache corrupt 上升 | 关闭 `pipeline.parallel_embed` |
| `studio_e2e_250` 退化 >15%（48h） | 回滚 PRD §13.3 全步骤 |
| 仅性能达标、NR 失败 | **不得放量**（D-P7-09） |

---

## 10. 验收记录文件

| 文件 | 用途 |
|------|------|
| `docs/acceptance-records/phase7-perf-eval.json` | 性能结果（含 P6 baseline） |
| `docs/acceptance-records/phase7-rollout-log.json` | 灰度与回滚 |
| `docs/reports/phase7-perf-baseline.md` | P6 vs P7 对比报告 |
| `docs/reports/phase7-onnx-spike.md` | ONNX 可选 spike（不阻塞） |
| `docs/config-phase7.example.yaml` | 验收 config 快照 |
| `docs/reports/phase7-g0-preflight-checklist.md` | G0 预检（含稳定性条款） |

### phase7-perf-eval.json 最小 schema

```json
{
  "schemaVersion": "1",
  "benchmarkId": "benchmark-p7-v0.1",
  "commit": "",
  "deviceTier": "S2",
  "configSnapshot": "docs/config-phase7.example.yaml",
  "baseline": {
    "phase": "P6",
    "studio_e2e_250_ms": null,
    "studio_e2e_250_p95_ms": null,
    "clip_embed_time_250_p95_ms": null
  },
  "candidate": {
    "phase": "P7",
    "studio_e2e_250_ms": null,
    "studio_e2e_250_p95_ms": null,
    "ingest_time_250_ms": null,
    "clip_embed_time_250_ms": null,
    "clip_embed_time_250_p95_ms": null,
    "clip_embed_time_incr_10pct_ms": null,
    "clip_embed_time_incr_append_10pct_ms": null,
    "clip_embed_time_incr_delete_10pct_ms": null,
    "clip_embed_time_incr_replace_10pct_ms": null,
    "pipeline_time_1k_sec": null,
    "peak_memory_1k_mb": null
  },
  "nr_p7": {
    "curate_hash_rate_fixed": null,
    "cluster_hash_rate_fixed": null,
    "curate_hash_rate_real": null,
    "cluster_hash_rate_real": null,
    "subject_class_agreement": null,
    "passed": null
  },
  "ac_p7": {
    "AC-P7-01": null,
    "AC-P7-02": null,
    "AC-P7-03": null,
    "AC-P7-04": null,
    "AC-P7-05": null,
    "AC-P7-06": null,
    "AC-P7-07": null,
    "AC-P7-08": null,
    "AC-P7-09": null,
    "AC-P7-10": null,
    "AC-P7-11": null,
    "AC-P7-12": null
  },
  "recordedAt": ""
}
```

---

## 11. 签字页（发布前）

| 角色 | 负责人 | 结论 | 日期 |
|------|--------|------|------|
| 产品负责人 |  | 通过 / 拒绝 |  |
| 算法负责人 |  | 通过 / 拒绝 |  |
| 工程负责人 |  | 通过 / 拒绝 |  |
| QA 负责人 |  | 通过 / 拒绝 |  |
| 产品总监 |  | G1 放量 / 暂缓 / 回退 |  |

---

## 12. 变更记录

| 日期 | 说明 |
|------|------|
| 2026-05-30 | 初稿：对齐 PRD v0.7.0；AC/NR/TC/SLO/灰度/记录 schema |
