# 编排差异矩阵（M-B2 · S1 · PRD §5.1.1）

> **语义基准 = Studio 现行产物**（PRD §5.1.1）。统一编排（M-B3）须使 `run_trip` + `StudioProfile` 对齐 Studio，而非让 Studio 向旧 CLI 退化。

**对照面**：`travelogue/web/studio_pipeline.py::run_studio_pipeline` vs `travelogue/orchestrator/run.py::run_trip`  
**最后核对**：2026-07-08 · 分支 `arch/optimization-ws1`

## 图例

| 类别 | 含义 | M-B3 处置 |
|------|------|-----------|
| **Studio 特化** | 仅 Studio 需要的行为 | 吸收进 `StudioProfile` / `StudioHooks` / 阶段机 |
| **漂移** | CLI/orchestrator 与 Studio 产物不一致 | **以 Studio 为准**修正 `run_trip` |
| **telemetry** | 可观测性字段，等价检查可剔除 | 保留；`arch_equivalence_check` 规范化 profile 剔除 |
| **M-B3 边界** | 仍留在 Studio 壳层、不进阶段机 | M-B3 前不改 `studio_pipeline` 调用路径 |

## 差异表

| # | 差异项 | Studio | run_trip（M-B2 前） | 类别 | 处置 / 状态 |
|---|--------|--------|---------------------|------|-------------|
| 1 | **clustering 一等 stage** | curate 前显式 `run_clustering_layer` | 无 clustering stage | **漂移** | M-B2 S2：`clustering` stage + `StudioProfile.run_clustering` |
| 2 | **trip 创建 + intent** | `create_trip` + plan/intent/date_range/template | 假定 trip.json 已存在 | Studio 特化 | 留 Studio 壳；M-B3 仍由 Studio 创建 trip 再 `run_trip(from_stage=…)` |
| 3 | **ingest 参数组** | featured/material dir、resume、on_persist、parallel embed | 仅 `from_dir` + `dedupe` + `generate_crops=False` | **漂移** | M-B2 S2：`IngestProfile` 透传；默认 CLI 行为不变 |
| 4 | **ingest 子进度** | `on_progress` / `on_cull_hint` + photo_cull hint | 无回调 | Studio 特化 | `IngestProfile.on_progress/on_cull_hint` + hooks |
| 5 | **keep_near_duplicates** | trip intent 驱动 ingest dedupe 关闭 | 未接 intent | **漂移** | 已在 `ingest_into_trip` 读 trip；Studio intent 写入仍由 Studio 负责 |
| 6 | **editorial intent hints** | curate 前 `apply_editorial_intent_hints` | 无 | **漂移** | M-B2 S2：`StudioProfile.apply_editorial_hints` |
| 7 | **export_layout** | curate 用 `"auto"` | 默认 `"mobile"` | **漂移** | M-B2 S2：`StudioProfile.export_layout`（studio=`auto`） |
| 8 | **细粒度 timings** | ingest/cluster/embed/curate/render/totalMs 增量 flush | 部分 stage 仅 ingest/curate/… | Studio 特化 | M-B2 S2：`flush_timings` + `StudioHooks.on_timing` |
| 9 | **G1 confirm 分支** | g1_pending 时 draft render 后早退 | 无 | Studio 特化 | **M-B3 边界**；不进 `run_trip` 全链 |
| 10 | **preview jpg** | render 后 `render_preview_jpg` | 无 | Studio 特化 | **M-B3 边界** 或 post-hook |
| 11 | **telemetry finalize** | `_finalize_pipeline_result` 写 studio telemetry | 无 | telemetry | 留 Studio；等价检查剔除 |
| 12 | **per-trip LSE rollout** | ingest 前 `_resolve_per_trip_lse_rollout` | 无 | Studio 特化 | 留 Studio 或 config scope；M-B3 前不变 |
| 13 | **分阶段 run_trip** | lock_structure→copy 与 render 分两次 `run_trip` | 单次连续链 | Studio 特化 | M-B3 可合并为一次 `run_trip(until=rendered)` + profile |
| 14 | **vision preload** | folder pick 后 preload CLIP | 无 | Studio 特化 | 留 Studio 壳 |
| 15 | **ingest tier / intent.folders** | post-ingest `apply_intent(folders.featuredDetected)` | 无 | Studio 特化 | 留 Studio 或迁入 profile 后处理 hook |
| 16 | **cluster 用户提示** | `cluster_result.user_notice` 进结果 | 无 | telemetry | hooks hint；等价检查忽略 |
| 17 | **validate 默认** | Studio 多 stage `validate=False` | CLI 默认 True | Studio 特化 | `StudioProfile` 或 M-B3 传参 |

## Go/No-Go 结论（S1）

| 检查项 | 结论 |
|--------|------|
| G1/LSE rollout 级深度分歧 | **无超预期**：G1 早退与 LSE rollout 可保留 Studio 壳，不阻塞阶段机扩展 |
| clustering 语义 | **必须修**：属 PRD 明示漂移；M-B2 S2 已加 stage |
| ingest 参数 | **可吸收**：IngestProfile 已建模；M-B3 切换时逐项对齐 |
| 建议 | **Go（有条件）**：完成 M-B2 S2 单测 + fixture 等价验证后，可进入 M-B3；**仍须 G-WIP-01** 才能改 `studio_pipeline.py` |

## M-B2 S2 交付对照

| 交付物 | 路径 | 状态 |
|--------|------|------|
| StudioProfile | `travelogue/orchestrator/studio_profile.py` | done |
| StudioHooks 扩展 | `travelogue/orchestrator/studio_hooks.py` | done（`on_timing`） |
| clustering stage | `travelogue/orchestrator/run.py` | done |
| studio_pipeline 切换 | — | **M-B3**（G-WIP-01） |

## 验收命令（M-B2 S2）

```bash
python -m pytest tests/test_orchestrator_studio_profile.py tests/test_pipeline_run.py -q
python scripts/lint_trip_pipeline_mutations.py
```

M-B3 等价门禁见 PRD AC-ARC-06v2（legacy Studio vs unified，再 unified vs CLI）。
