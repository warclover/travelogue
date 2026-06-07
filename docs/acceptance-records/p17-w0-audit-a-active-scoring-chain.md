# P17 W0 审计 A — 现网真实活跃打分链

| 属性 | 内容 |
|------|------|
| **审计 ID** | P17-W0-A |
| **日期** | 2026-06-07 |
| **分支** | `feature/phase17-lse` |
| **状态** | 待评审 |
| **配套** | PRD §7.2、AC-P17-02；IMPLEMENTATION-PHASE17 §2 审计 A |

---

## 1. 结论摘要

| 问题 | 结论 |
|------|------|
| `layout.scoring` 是否生效？ | **默认不生效**（`enabled=false`）；beam replan 整条链休眠 |
| 默认 trip 真正跑的打分链？ | **MCS 乘性链**（`mosaic/scorer.score_candidate`）+ **layout 加性 base**（`score_screen_plan` 读 `mosaic.weights`） |
| 节奏/配额权威？ | **`ScreenLayoutPlannerState`** 硬编码分档 + `layout_density.py` 密度调整 |
| Strategy Pack 真值来源？ | **`MosaicConfig` 默认 + `config.yaml.example`**，非 `layout.scoring.weights` |
| PRD §13.1 草案数值偏差？ | `min_trip_photos` 草案写 20，**代码 35**；`tone_*` 权重草案有值但现网 mosaic weights **无此项**（W3b 新增） |

---

## 2. 调用链 Trace（默认 trip · `layout.scoring.enabled=false`）

```
run_curate
  ├─ build_chapters_from_buckets
  │    └─ attach_screens_day_buckets / attach_screens_to_chapters
  │         └─ plan_screens_for_chapter → ChapterScreenPlanner.plan()
  │              ├─ stages: hero / mosaic / mixed / landscape / portrait / flush / tall
  │              └─ mosaic hook (try_mosaic_window / try_mosaic_five_mcs)
  │                   └─ compose.pick_best_window
  │                        └─ score_candidate (乘性惩罚 + score_screen_plan 加性 base)
  │                             weights ← MosaicConfig.weights
  │                             penalties ← MosaicConfig.penalties
  │                        └─ apply_candidate_diversity ← mcs_diversity_config()
  │              └─ layout_state: ScreenLayoutPlannerState (九宫配额 / consecutive ban)
  │
  └─ compose_trip / maybe_replan_chapters
       └─ scoring_enabled=False → 【跳过】return chapters unchanged
```

**休眠链**（仅 `layout.scoring.enabled=true` 或 Studio 实验开闸）：

```
maybe_replan_chapters
  └─ replan_day_buckets_beam
       └─ score_screen_plan (layout 加性 · PHASE6/PHASE3B 预设权重)
       └─ SearchBudget (挂钟 + max_evaluations)
```

---

## 3. 活跃参数权威值

### 3.1 `layout.scoring`（默认路径：死代码）

| 字段 | 代码默认 | `config.yaml.example` | 活跃？ | 说明 |
|------|----------|----------------------|--------|------|
| `enabled` | `false` | `false` | **否** | 控制 beam 开闸 |
| `beam_width` | `3` | `3` | 仅 enabled=true | → `search.beam_width` |
| `search_timeout_ms` | `2000` | `2000` | 仅 enabled=true | → `search.search_timeout_ms`（W1 改 telemetry-only） |
| `max_evaluations_per_trip` | `500` | `500` | 仅 enabled=true | → `search.max_evaluations_per_trip` |
| `max_candidates_per_bucket` | `12` | `12` | 仅 enabled=true | → `search`（beam 候选上限） |
| `max_evaluations_per_segment` | `0` | `0` | 仅 enabled=true | 0=不限 per-segment |
| `allow_burst_split` | `false` | `false` | 仅 enabled=true | |
| `subject_run_tolerance` | `1` | `1` | **部分** | beam + `compute_layout_metrics` |
| `skip_duplicate_signatures` | `true` | `true` | 仅 enabled=true | |
| `incremental` | `false` | — | 仅 enabled=true | |
| `min_layout_eligible` | `3` | `3` | **是** | `assess_degradation` |
| `min_aspect_kinds` | `1` | `1` | **是** | `assess_degradation` |
| `max_screens_per_chapter` | `12` | `12` | 仅 enabled=true | |
| `weights.*` | **全 0** | **全 0** | **否** | enabled=true 时走 `resolve_scoring_weights` 预设 fallback |

**`resolve_scoring_weights` 预设**（`layout.scoring.enabled=true` 且 weights 全 0 时）：

- `enable_gravity_balance=true`（默认 curate）→ `PHASE6_WEIGHTS`
- 否则有 `dominantTone` → `PHASE3B_WEIGHTS`；无则 `PHASE3_WEIGHTS`

→ **迁入 Strategy Pack 时**：`scoring_profiles.default.weights` 应对齐 **MosaicConfig.weights**（现网生效），另建 `scoring_profiles.beam` 存 PHASE6 预设供实验轨。

### 3.2 `mosaic.*`（默认路径：活跃）

来源：`travelogue/config/mosaic.py` 默认 ≡ `config.yaml.example` mosaic 块。

| 字段 | 权威值 | Strategy Pack 目标 | 活跃 |
|------|--------|-------------------|------|
| `enabled` | `true` | capabilities（MCS 总开关） | **是** |
| `scorer_version` | `"p15-s2"` | `algorithm_version` 引用 | **是** |
| `deterministic_strict` | `true` | `search` / MCS 标志 | **是** |
| `min_candidate_score` | `0.35` | `search.min_candidate_score` | **是** |
| `enabled_window_sizes` | `[3,4,5,6,8,9]` | `planning.stages.mosaic.enabled_window_sizes` | **是** |
| `unified_mode` | `true` | MCS 行为（非 YAML 草案字段） | **是** |
| `fallback_to_legacy` | `true` | `self_heal` 邻域 | **是** |
| `self_heal.enabled` | `true` | `self_heal.enabled` | **是** |
| `self_heal.allow_drop` | `false` | `self_heal.allow_drop` | **是** |
| `candidate_top_k` | `4` | MCS 内部 | **是** |
| `log_level` | `"window"` | telemetry | **是** |
| `hero_weighted_geometry_guard` | `true` | feature 开关（非 example 显式，代码默认 true） | **是** |

**weights（加性 base · `score_screen_plan`）**：

| 因子 | 值 | 活跃 |
|------|-----|------|
| `aspect_match` | 0.20 | **是** |
| `sharpness` | 0.15 | **是** |
| `temporal_coherence` | 0.15 | **是** |
| `hero_separation` | 0.10 | **是** |
| `subject_run` | 0.10 | **是** |
| `layout_rhythm` | 0.10 | **是** |
| `diversity` | 0.10 | **是** |
| `category_coherence` | 0.10 | **是** |
| `cohort_coherence` | 0.0 | 仅 cohort.enabled | 条件 |
| `tone_continuity` | — | **否**（未在 mosaic weights；W3b CAP-04） |
| `luminance_continuity` | — | **否** |

**penalties（乘性 · `score_candidate`）**：

| 因子 | MosaicConfig 默认 | example 显式 | 活跃 |
|------|-------------------|--------------|------|
| `face_crop` | 0.30 | 0.30 | **是** |
| `main_quality` | 0.25 | 0.25 | **是** |
| `duplicate_density` | 0.20 | 0.20 | **是** |
| `hero_narrow_tiles` | 0.35 | （缺省继承默认） | **是** |
| `hero_slot_aspect` | 0.40 | （缺省继承默认） | **是** |
| `flat_six_grid` | 0.35 | （缺省继承默认） | **是** |
| `salient_crop` | — | — | **否**（W3b CAP-02 新增） |

**隐式惩罚**（代码硬编码，非 config）：

| 因子 | 逻辑 | 迁入建议 |
|------|------|----------|
| `trip_small` | `trip_photo_total < 35` → pen 0.25；`< 20` → 0.7 | `planning.stages.mosaic.min_trip_photos` + penalty |
| `slot_geometry` | `screen_slots_geometry_ok` fail → 0.95 | L0 算法 |
| `R_RHYTHM_BLOCK` | `layout_state.can_emit_pattern` fail → ×0.5 | rhythm 硬约束 |

### 3.3 `ScreenLayoutPlannerState` 分档（活跃 · 代码常量）

| 逻辑 | 代码位置 | 权威值 |
|------|----------|--------|
| 九宫配额 `nine_grid_limits` | `nine_grid_limits_for_trip()` | ≤50: 0–1；51–100: 2–5；101–200: 4–8；>200: 6–10 |
| 竖八格上限 | `portrait_grid8_max_for_trip()` | ≤50: 0；51–100: 2；101–200: 4；>200: 6 |
| 竖八格门槛 | `PORTRAIT_GRID8_MIN_PHOTOS` | 50 |
| mosaic 阶段门槛 | `MIN_TRIP_PHOTOS_FOR_MOSAIC` | **35**（`screen_planner.py:46`） |
| consecutive ban · 九宫 | `can_use_nine` | `last_kind != "nine"` |
| consecutive ban · 三联/六联 | `can_pick_grid_size(3/6)` | `last_kind not in ("triple","six")` |
| consecutive ban · 竖单 | `can_emit_pattern(portrait_single)` | `last_kind != "portrait_single"` |
| 密度调整 | `LayoutDensityParams.adjust_nine_limits` | hero_first: min×0.25 max×0.6；collage_first: min×1.2 max×1.1 |

→ PRD §13.1 `rhythm.nine_grid_limits` 与代码一致；`consecutive_bans` 需从 `can_emit_pattern` 提炼（见映射表）。

### 3.4 其他活跃布局参数

| 现网路径 | 权威值 | 活跃 | Strategy Pack |
|----------|--------|------|---------------|
| `layout.screen_plan_scope` | `"day"` | **是** | `planning.screen_plan_scope` |
| `layout.mixed_proximity_seconds` | `12.0` | **是** | `planning.mixed_proximity_seconds` |
| `layout.layout_density_enabled` | `true` | **是** | density profile 总开关 |
| `trip.intent.layoutDensity` | 默认 `balanced` | fine_craft 路径 | `density_profiles.*` |
| `layout.template_engine.mcs_integration.scoring.diversity` | `mmr` / `0.65` | **是**（config 覆盖 policy） | `diversity.mode` / `diversity.lambda` |
| `lte_policy.yaml` diversity 回退 | `mmr` / `0.65` | config 未设时 | 同上 |
| `DEFAULT_FEATURED_WEIGHT` | `1.35` | **是**（hero 选片） | 不归 LSE（§4.8 封面链） |
| `curate.enable_food_grid` 等 | curate 配置 | **是** | `planning.stages.enabled` 子集 |

---

## 4. §7.2 完整映射表

| # | 现配置路径 | Strategy Pack 字段 | 权威值 | 状态 | 备注 |
|---|------------|-------------------|--------|------|------|
| 1 | `layout.scoring.enabled` | （引擎开关，非 pack 内） | `false` | 死代码 | `layout.strategy_engine.enabled` 新键 |
| 2 | `layout.scoring.beam_width` | `search.beam_width` | `3` | 休眠 | beam 专用 profile |
| 3 | `layout.scoring.search_timeout_ms` | `search.search_timeout_ms` | `2000` | 休眠 | W1 改 telemetry-only |
| 4 | `layout.scoring.max_evaluations_per_trip` | `search.max_evaluations_per_trip` | `500` | 休眠 | 确定性预算，保留 |
| 5 | `layout.scoring.max_candidates_per_bucket` | `search.max_candidates_per_bucket` | `12` | 休眠 | |
| 6 | `layout.scoring.weights.*` | `scoring_profiles.beam.weights` | 全 0 → PHASE6 预设 | 死代码 | **勿**与 default profile 混淆 |
| 7 | `mosaic.weights` | `scoring_profiles.default.weights` | 见 §3.2 | **活跃** | parity 核心 |
| 8 | `mosaic.penalties` | `scoring_profiles.default.penalties` | 见 §3.2 | **活跃** | |
| 9 | `mosaic.min_candidate_score` | `search.min_candidate_score` | `0.35` | **活跃** | |
| 10 | `mosaic.enabled_window_sizes` | `planning.stages.mosaic.enabled_window_sizes` | `[3,4,5,6,8,9]` | **活跃** | |
| 11 | `mosaic.self_heal.*` | `self_heal.*` | allow_drop=false | **活跃** | |
| 12 | `layout.screen_plan_scope` | `planning.screen_plan_scope` | `day` | **活跃** | |
| 13 | `layout.mixed_proximity_seconds` | `planning.mixed_proximity_seconds` | `12` | **活跃** | |
| 14 | `layout.template_engine.mcs_integration.scoring.diversity` | `diversity.mode` / `diversity.lambda` | `mmr` / `0.65` | **活跃** | |
| 15 | `ScreenLayoutPlannerState` 九宫分档 | `rhythm.nine_grid_limits[]` | 见 §3.3 | **活跃** | 代码常量 |
| 16 | `ScreenLayoutPlannerState` consecutive | `rhythm.consecutive_bans[]` | 见 §3.3 | **活跃** | 须从代码提炼 |
| 17 | `layout_density` 三档 | `density_profiles.*` | 见 `layout_density.py` | **活跃** | fine_craft |
| 18 | `MIN_TRIP_PHOTOS_FOR_MOSAIC` | `planning.stages.mosaic.min_trip_photos` | **35** | **活跃** | PRD 草案 20 **需修正** |
| 19 | `hero_weighted_geometry_guard` | `features.saliency` 前置 / MCS 标志 | `true` | **活跃** | |
| 20 | `layout.scoring.subject_run_tolerance` | `scoring_profiles` 或 metrics | `1` | 部分 | metrics 用 |

---

## 5. Strategy Pack 默认包修订建议（相对 PRD §13.1）

| PRD 草案 | 审计权威 | 动作 |
|----------|----------|------|
| `min_trip_photos: 20` | `35` | W1 YAML 写 **35**；回写 PRD §13.1 |
| `tone_continuity: 0.08` 等在 default weights | 现网无 | 放 `capabilities.tone_harmony` 默认 off；W3b 再注入 |
| `salient_crop: 0.28` | 现网无 | W3b CAP-02 |
| `scoring_profiles.default.weights` 含 tone | 应对齐 **mosaic.weights** | 删除草案中未生效的 tone 行 |
| `layout.scoring.*` 合并入 pack | 拆 **default**（MCS）与 **beam**（实验） | adapter 按 enabled 择一 |

---

## 6. W1 Parity 验收锚点

`enabled=true` 纯收敛时，adapter 从默认 pack 派生的 kwargs/weights **必须逐一等于**本表「活跃」行：

1. `mosaic.weights` / `penalties` → `scoring_profiles.default`
2. `nine_grid_limits` + `consecutive_bans` → `ScreenLayoutPlannerState` 等价
3. `diversity` → `mcs_diversity_config()` 返回值
4. `mixed_proximity_seconds=12`、`screen_plan_scope=day`
5. `layout.scoring.enabled=false` 时 adapter 仍走 legacy 入口，pack 仅预置不生效

---

## 7. 签收

| 角色 | 签名 | 日期 |
|------|------|------|
| 开发负责人 | （待评审） | |
| 算法 | （待评审） | |
| 运营 | （待评审） | |
