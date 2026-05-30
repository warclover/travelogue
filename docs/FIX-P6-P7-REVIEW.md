# P6/P7 评审修复任务清单

> 依据 CTO 评审 + 首席开发负责人 Wave 0–3 路线图执行。状态截至本地 pytest 通过。

## Wave 0 — 灰度语义（阻塞 G1 对齐）

| ID | 任务 | 状态 |
|---|---|---|
| W0-1 | `phase6_in_rollout_cohort` 文档澄清：`stage=off` = 无分桶、全员 P6 | ✅ |
| W0-2 | 空 `trip_id` fail-closed → `False` | ✅ |
| W0-3 | `config.yaml.example` 注释与实现对齐 | ✅ |
| W0-4 | 契约测试 `test_phase6_in_rollout_cohort_off_means_full_p6` | ✅ |

## Wave 1 — 阻塞 G1 放量

| ID | 任务 | 状态 |
|---|---|---|
| C-P6-02 | CLIP batch 混维：缺失文件时整 batch 走 heuristic | ✅ |
| C-P6-03 | geo orphan 段距离公式修正 | ✅ |
| C-P6-04 | longshot 连续 pattern：回溯 + 保留 `must` 种子 | ✅ |

## Wave 2 — P7 稳定性

| ID | 任务 | 状态 |
|---|---|---|
| C-P7-01 | `_auto_tune_batch_size` 持 `_infer_lock` | ✅ |
| C-P7-02 | prefetch 快照 `prefer_web` / `preprocess` | ✅ |
| C-P7-03 | `parallel_embed` 分块 + `_all_offered` 增量 cache 合并 | ✅ |
| W6 | `Image.open` context manager | ✅ |
| W11 | Haar cascade `threading.Lock` | ✅ |

## Wave 3 — G2 前正确性

| ID | 任务 | 状态 |
|---|---|---|
| W1 | DBSCAN fallback → noise labels | ✅ |
| W2 | `deterministic` 参数文档化 + `_` 绑定 | ✅ |
| W3 | `p75==0` 双峰自适应 | ✅ |
| W4+W5 | `scene_subsegments` coalesce cluster/尾部逻辑 | ✅ |
| W10 | `layout_search` 约束回退 warning | ✅ |

## 测试加固

| ID | 任务 | 状态 |
|---|---|---|
| T-rollout | `test_phase6_in_rollout_cohort_off_means_full_p6` | ✅ |
| T-geo | orphan 距离 + 自适应 p75 测试 | ✅ |
| T-parallel | `prepare_scene_embeddings` spy 分块断言 | ✅ |
| T-clip | `test_clip_batch_no_heuristic_dim_mix` | ✅ |

## Backlog Wave 4（已完成）

| ID | 任务 | 状态 |
|---|---|---|
| W7 | OOM 用 `_oom_cap` 会话级降级，不污染 `_tuned_batch_size` | ✅ |
| T4 | `test_longshot_mmr_off_vs_on_diversity` | ✅ |
| T5 | `test_phase7_clip_concurrent.py` prefetch + 双线程 | ✅ |
| T1 | `test_embed_stats_recorded_clip` 字段断言 | ✅ |
| T3 | `test_ac_p7_07_*` / `test_ac_p7_08_rollback_patch_*` | ✅ |

## Backlog Wave 5（已完成）

| ID | 任务 | 状态 |
|---|---|---|
| R1 | `render/screen_tone.py` 共享 tone 工具 | ✅ |
| R2 | `VoiceSourceContext` / `VoiceRenderContext` | ✅ |
| R3 | `StudioHandlerProtocol` + handlers 标注 | ✅ |
| R4 | `studio_dispatch_PATCH` + `serve.do_PATCH` 统一 | ✅ |
| R5 | import job watch 用 `threading.Event` | ✅ |
| W8 | per-trip `_cache_write_lock_for` | ✅ |
| W9 | `np.asarray(..., dtype=str)` + 无 pickle 读取（legacy 回退） | ✅ |
