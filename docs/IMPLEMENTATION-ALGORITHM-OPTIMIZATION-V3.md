# IMPLEMENTATION · 算法与布局管线优化 V3（ALG-V3）

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-ALGORITHM-OPTIMIZATION-V3.md](./PRD-ALGORITHM-OPTIMIZATION-V3.md) **v0.3.0** |
| **验收** | [ACCEPTANCE-ALGORITHM-OPTIMIZATION-V3.md](./ACCEPTANCE-ALGORITHM-OPTIMIZATION-V3.md) |
| **评审** | [acceptance-records/algorithm-v3-prd-review-2026-08-01.md](./acceptance-records/algorithm-v3-prd-review-2026-08-01.md) |
| **Must-green** | [acceptance-records/alg3-must-green-nodeids.txt](./acceptance-records/alg3-must-green-nodeids.txt) |
| **状态** | **W0～W2-A3 已合入** · 债务修复 PR：`feat/alg-v3-debt-ac20-docs-s03`（AC-20 真下降 / 文档勾选 / S03 / 盲评脚手架） |
| **更新日期** | 2026-08-01 |
| **建议分支** | master ← **本债务 PR** → 其后 W2-A4 / OQ-02 / 人评填盲评记录 |

---

## 落地原则

1. **W0 是挡门，不是暖场** — D5（开关清单）+ FE-ALG3-05 + `buildScreenCalls` 埋点不做完，W1a-2 的 C1 必红（PRD §14.1）。  
2. **W1a 拆两个 PR** — W1a-1 只动性能（B2a/B6）；W1a-2 只动合同（C1/Ready/摘要）；禁止混装。  
3. **默认路径不成片** — 直至 W1b；AC-21 / E21-byte-default 守门。  
4. **不平行实现 AAD** — B5 公式 / D4 curate stage 只提接口诉求。  
5. **不碰代码默认成片开关** — scoring / vision / clone 门 / prefer 保持 PRD §5。  
6. **测试隔离** — 临时 `trips_dir`、显式 `AppConfig`；CI 无真实 Key、无绝对毫秒门。

---

## 摸底结论（开工前已知 · 2026-08-01 · 证据见 PRD §14）

| ID | 发现 | 实施含义 |
|----|------|----------|
| **DEV-01** | `iter_bool_paths` 只收 `bool`；`test_bool_counts_match_prd_diagnostic_band` 写死 151/97/54 | **先做 D5**，再加 C1 bool / TriState |
| **DEV-02** | `studio_llm_status` 会 `inject_secrets_into_environ` | Ready 摘要必须走 `probe_llm_ready()` |
| **DEV-03** | `capability=true` 无 Key 行为未定义 | §3.2.1 + AC-06 |
| **DEV-04** | 廉价硬拒已在 `build_screen` 前；B3 已实现；B1 不在默认路径 | W1a-1 只做 **B2a + B6** |
| **DEV-05** | 原 W1a 混装难定位 | 两 PR 串行合入 |
| **DEV-06** | `mosaic_explain` 对 SSG/atom/clone reason 原文外泄 | **W0 Must FE-ALG3-05** |
| — | `algorithm_profile.layout_config_stale` **不读** `algoV3` | 写摘要本身不应假亮 `algorithmStale`；仍须 S03 回归 |

**候选路径实际顺序（B2a 插入点）**：

```text
pattern_disabled → try_order → atom → shot_group_* → near_scene_clone
  → ★ B2a 静态几何预检（可 skip build_screen）
  → build_screen → [hungarian 二次 build] → geometry / main_ar / sidebar / usage_rule
```

---

## 列车总览

| 列车 | 目标 | 估时 | 依赖 |
|------|------|------|------|
| **M0** | ACCEPTANCE + 本清单 + must-green + AC-21 白名单 | ✅ 本文 | — |
| **W0 / M0.5** | D5 · probe · 摘要 schema · explain 人话 · 埋点基线 | 6–8 人日 | M0 |
| **W1a-1 / M1a** | B2a 静态几何预检 · B6 self-heal 限次 · AC-20/21 | 3–5 人日 | W0 埋点基线 |
| **W1a-2 / M1c** | C1 墙钟 · Ready 接线 · algoV3 落盘 · AC-01/02/06/07/22/32 | 3–5 人日 | **W0 D5 合入** |
| **W1b / M1b** | B7 条件 clone · AC-10 · 盲评 | 另 PR | W1a 稳定后 |
| **W2+** | A1/A3/A6 · vision 按 OQ-02 · B5/AAD | 见 PRD | — |

---

## W0 · 合同与观测（挡门）

### 文档 / 基线

| ID | 任务 | 建议位置 | 状态 |
|----|------|----------|------|
| DOC-ALG3-01 | PRD v0.3.0 + 评审纪要 DEV 回写 | `docs/PRD-…` · `acceptance-records/…` | ☑ |
| DOC-ALG3-02 | ACCEPTANCE（含 AC-21 白名单）+ 本清单 + must-green | 本目录 | ☑ |
| DOC-ALG3-03 | 冻结 `alg3-build-screen-calls-baseline.json` | `docs/acceptance-records/` | ☑ 2026-08-01 · W0=9（+probe） |
| DOC-ALG3-04 | example `decor_line_llm_enabled: false`（对齐代码） | `config.yaml.example` | ☑ |
| DOC-ALG3-05 | FE-ALG3-05 人话终稿（可微调 ACCEPTANCE §8） | ACCEPTANCE §8 | ☑ |

### 后端 · D5 开关清单（挡门）

| ID | 任务 | 建议位置 | 状态 |
|----|------|----------|------|
| BE-ALG3-D5-01 | `iter_flag_paths`：bool + TriState 双收集；`tristate_flags` 进 recipe | `orchestrator/happy_path_recipe.py` | ☑ |
| BE-ALG3-D5-02 | `tier_for_*` / Research·Danger 对 TriState 键语义（默认须 `false` 或 ready-only `auto`） | 同上 | ☑ |
| BE-ALG3-D5-03 | 更新 `csc-w0-baseline-happy-path-recipe.json` + 三计数断言（AC-32） | `docs/acceptance-records/` · `test_happy_path_recipe.py` | ☑ 重签 170/108/62 + tristate=5；解释：基线相对 AppConfig 漂移已久，本波一并重签 |
| QA-ALG3-D5-01 | 单测：把某 Research bool 暂标为 TriState 时键不从清单消失（可用临时 fixture） | `tests/unit/orchestrator/` | ☑ |

### 后端 · Ready 只读探测

| ID | 任务 | 建议位置 | 状态 |
|----|------|----------|------|
| BE-ALG3-R01 | 新增 `probe_llm_ready()`：只读解析，**不** `inject_secrets_into_environ` | `web/studio_narrate.py` | ☑ |
| BE-ALG3-R02 | `studio_llm_status` 保持现状；与 probe **共用底层、互不调用** | 同上 | ☑ |
| BE-ALG3-R03 | `capability_allows` 按 PRD §3.2.1 返回 `(allowed, degrade\|None)` | `config/_common.py` | ☑ |
| QA-ALG3-R01 | AC-07：environ 快照 + 无网络 | `tests/unit/web/test_alg3_llm_ready.py` | ☑ |

### 后端 · 摘要与埋点

| ID | 任务 | 建议位置 | 状态 |
|----|------|----------|------|
| BE-ALG3-M01 | `curation.algoV3` schema（PRD §7.1）；含 `buildScreenCalls` | `curation/algo_v3_summary.py` · curate finalize | ☑ |
| BE-ALG3-M02 | MCS 路径递增 `buildScreenCalls`（每次真实调用 `build_screen`） | `builders.py` ContextVar | ☑ |
| BE-ALG3-M03 | `clusterNoiseRatio` / rejectFunnelTop 聚合（可先 Top 原因计数） | `algo_v3_summary.py` | ☑ |
| QA-ALG3-M01 | AC-30：无 Key / SSG empty 两场景键齐全且值分化 | `test_alg3_algo_v3_summary.py` | ☑ `test_ac30_no_key_vs_ssg_empty_values_diverge` |
| QA-ALG3-M02 | AC-31：实验旗默认关与 recipe 一致 | happy_path / 现有危险旗测 | ☑ |

### FE / 文案

| ID | 任务 | 建议位置 | 状态 |
|----|------|----------|------|
| FE-ALG3-05-01 | 补全 `_REJECT_LABELS`（ACCEPTANCE §8 八键 + 既有） | `curation/mosaic_explain.py` | ☑ |
| QA-ALG3-FE01 | 单测：对各 reason 断言 details 含中文且不含裸 reason 键 | `tests/unit/curation/test_mosaic_explain.py` | ☑ |

**W0 出口**：AC-30/31/32/07 绿；FE-ALG3-05 绿；`buildScreenCalls` 基线 JSON 已冻结；**不成片**。

---

## W1a-1 · 性能（零合同变更）

| ID | 任务 | 建议位置 | 状态 |
|----|------|----------|------|
| BE-ALG3-B2A-01 | `pattern_geometry_precheck(pattern_id, ordered_ids, aspects) -> bool\|None` | `layout_engine/mosaic/slot_geometry.py` | ☑ |
| BE-ALG3-B2A-02 | 在 `near_scene_clone` 之后、`build_screen` 之前调用；`False` → reject `geometry_invalid` + detail `static_precheck`；`None` → 建 screen | `candidates.py` | ☑ |
| BE-ALG3-B2A-03 | **MSA 开启时一律 `None`**（`effective_slot_adaptation_enabled`） | 同上 | ☑ |
| BE-ALG3-B6-01 | self-heal 限次 / 限 SKU（`self_heal_max_rescore` / `self_heal_max_drop_attempts`） | `selfheal.py` · `config/mosaic.py` | ☑ |
| QA-ALG3-20 | AC-20：固定语料(+mismatch probe) `buildScreenCalls` **严格 <** 基线 | `test_alg3_ac20_ac21.py` + baseline JSON | ☑ W0=9 → B2a=8 |
| QA-ALG3-21 | AC-21：§2.1 投影 vs `alg3-ac21-layout-baseline.json` | `test_alg3_ac20_ac21.py` | ☑ |
| DOC-ALG3-06 | 冻结 AC-21 版式基线 JSON | `acceptance-records/` | ☑ 2026-08-01 |

**本 PR 已批准例外**：B6 新增 `self_heal_max_rescore` / `self_heal_max_drop_attempts`（默认 8 / 1）——与「零新配置键」字面冲突，以限次自愈为目的保留。  
**仍禁止**：改 Ready/墙钟接线、改成片意图、无说明改 CSC 三计数。  
**退出**：AC-20/21 绿；must-green 全绿。

---

## W1a-2 · 合同（默认路径零行为变化）

| ID | 任务 | 建议位置 | 状态 |
|----|------|----------|------|
| BE-ALG3-C1-01 | `layout.scoring.wall_clock_limits_output`（名以 PR 为准）进 `LayoutScoringConfig` + loader | `config/layout.py` | ☑ 默认 true |
| BE-ALG3-C1-02 | `layout_search` / `compose_trip` / `curate` 贯通传入 `SearchBudget` | `layout_search.py` · `trip.py` · `curate.py` | ☑ |
| BE-ALG3-C1-03 | scoring 开时默认硬截断 `true`；scoring 关时行为与今日一致 | 配置默认 | ☑ |
| BE-ALG3-LLM-01 | `llm.capability` TriState 默认 `auto`；接 `probe_llm_ready` | `config` · narrate | ☑ |
| BE-ALG3-LLM-02 | 收敛 `resolve_studio_narrate_provider`：`prefer ∧ ready ∧ may_call` 否则 stub | `studio_narrate.py` | ☑ |
| BE-ALG3-LLM-03 | prefer/capability **不进**用户 PATCH 白名单 | `config_handlers` / loader | ☑ 本就不在白名单；测锁死 |
| BE-ALG3-M04 | 每趟写入完整 `algoV3`（含 llm 段） | curate | ☑ 含 preferLlmWhenReady |
| QA-ALG3-01/02/06 | AC-01/02/06 | `test_alg3_w1a2_contracts.py` | ☑ |
| QA-ALG3-22 | AC-22 cohort + **默认路径投影不变** | `test_alg3_ac22_wall_clock.py` | ☑ |
| QA-ALG3-32 | C1 新 bool → 同 PR 更新 CSC（X09 解释增量） | happy_path 测 · CSC JSON | ☑ 172/109/63 |
| FE-ALG3-01/02/04 | 回归：无解冻、无新设置控件 | 手动 / 现有 NAS 测 + PATCH 测 | ☑ 契约测 |

**退出**：AC-01/02/04/05a/06/07/22/30/32 绿；默认配置 AC-21 投影与合入前一致。

**AC-32 / X09 增量说明（W1a-2）**：新增 `layout.scoring.wall_clock_limits_output`（default **true**）与 `llm.prefer_llm_when_ready`（default **false**）→ CSC 三计数 **172 / 109 / 63**（相对 W0 的 170/108/62）。W1b 再 +`near_scene_clone_gate.conditional` → **173 / 110 / 63**。

---

## W1b · 条件 clone 硬门（成片可变）

| ID | 任务 | 建议位置 | 状态 |
|----|------|----------|------|
| BE-ALG3-B7-01 | `effective_clone_hard_gate`：ssg 窗无 shotGroup ∨ vision 降级 → 硬门；`conditional` 可关 | `clone_detection.py` · `candidates.py` | ☑ |
| BE-ALG3-B7-02 | VC-01：仅 `is_slice_pattern`（prefers_burst is not True） | `shot_group_gate.is_slice_pattern` | ☑ |
| BE-ALG3-B7-03 | `algoV3.cloneGateEffective` 反映条件生效 | `algo_v3_summary.py` | ☑ |
| QA-ALG3-10 | AC-10：无 SSG 语料 B7 on vs off；↓≥40% 或 funnel 硬可见 | `test_alg3_w1b_clone_gate.py` | ☑ |
| QA-ALG3-32b | `near_scene_clone_gate.conditional` → CSC 重签 | CSC JSON | ☑ 173/110/63 |
| FE-ALG3-S03 | algoV3 不误亮 algorithmStale / longshotStale；书架 CTA 不因 algoV3 强推「更新并导出」 | `test_alg3_w1b_clone_gate.py` · shelf-actions 合同 | ☑ |

**退出**：AC-10 绿；must-green 全绿；盲评问1/3 另开 dogfood（本 PR 不挡码）。

**AC-32 / X09 增量说明（W1b）**：新增 `mosaic.near_scene_clone_gate.conditional`（default **true**）→ CSC **173 / 110 / 63**。

---

## W2 · 上游准确度（分 PR）

> IMPL 原则：W2 按包拆 PR；**首 PR 只做 A1 + AC-11**，默认成片字节不变（`cluster_selection_epsilon=0.0` ≡ 今日 sklearn 默认）。A3/A6/A4/OQ-02 后续另开。

### W2-A1 · HDBSCAN 诚实接线 + AC-11（当前）

| ID | 任务 | 建议位置 | 状态 |
|----|------|----------|------|
| BE-ALG3-A1-01 | 新键 `clustering.scene.cluster_selection_epsilon`（默认 `0.0`）进 HDBSCAN；**禁止**把 `cluster_eps` silent remap | `config/clustering.py` · `scene_clusters.py` · `clustering.py` | ☑ |
| BE-ALG3-A1-02 | cache fingerprint **只含实际消费参数**（hdbscan→selection_epsilon；dbscan→eps） | `vision/cache.py` | ☑ |
| DOC-ALG3-A1-01 | example 注释对齐死旋钮 / 新键 | `config.yaml.example` | ☑ |
| QA-ALG3-11 | AC-11：噪声基线门 + 消费参数改 fingerprint / 死旋钮不改 | `test_alg3_w2_a1_ac11.py` · `alg3-ac11-noise-baseline.json` | ☑ |

**退出**：AC-11 绿；must-green 全绿；默认路径 HDBSCAN 行为与合入前等价（epsilon=0）。

### W2-A6 · look 批量化 encode（当前）

| ID | 任务 | 建议位置 | 状态 |
|----|------|----------|------|
| BE-ALG3-A6-01 | `encode_pil_clip_batch`：stack + 一次 `encode_image`；OOM/失败回退单张 | `vision/look_appearance.py` | ☑ |
| BE-ALG3-A6-02 | `compute_look_vectors_for_assets` 按 `vision.batch_size` 分块；`<=1` 走旧路径 | 同上 | ☑ |
| BE-ALG3-A6-03 | 显式 `get_clip_encoder(app_cfg)`；`run_shot_grouping_layer` 传入 AppConfig | `look_appearance.py` · `shot_grouping.py` | ☑ |
| BE-ALG3-A6-04 | 遥测：`lookElapsedMs` / `lookBatchSize` / `lookBatches` / `lookFallbackSingle` | shotGrouping stats | ☑ |
| QA-ALG3-A6 | 分块次数、顺序、batch_size=1、cache hit、app_cfg 传递 | `test_alg3_w2_a6_look_batch.py` | ☑ |

**退出**：默认 look 分组语义不变；must-green 绿；**不加**默认硬 timeout（fail-open 会改成片）。

### W2-A3 · soft-split 自适应（当前 · 默认关）

| ID | 任务 | 建议位置 | 状态 |
|----|------|----------|------|
| BE-ALG3-A3-01 | `adaptive_soft_split` 等键；默认 **false**；公式 `clamp(median(gaps_h)*k,[lo,hi])` | `config/shot_grouping.py` | ☑ |
| BE-ALG3-A3-02 | 每簇解析 `resolve_soft_split_hours` → `_soft_split_runs`；flag off ≡ 固定 6h | `curation/shot_grouping.py` | ☑ |
| BE-ALG3-A3-03 | 遥测 `softSplitAdaptive` / `softSplitHoursEffective` | shotGrouping stats | ☑ |
| QA-ALG3-A3 | 夹紧 / fallback / flag off 等价 / 稀疏少切 | `test_alg3_w2_a3_soft_split_adaptive.py` | ☑ |
| QA-ALG3-32c | 新 bool → CSC 重签 **174/110/64**；Research 防火墙 | CSC JSON · `RESEARCH_DEFAULT_FALSE` | ☑ |

**退出**：默认路径 soft-split 与合入前一致；must-green 绿。**不**抬默认 on（成片变更须另 PR + 盲评）。

### W2 后续（提纲 · 未开工）

| 包 | 要点 | 挡门 |
|----|------|------|
| ~~A3~~ | ~~soft-split 自适应~~ | ✅ W2-A3（默认关） |
| ~~A6~~ | ~~look 批量化 encode~~ | ✅ W2-A6 |
| A4 | Atom/soft-split **仅实验旗**；禁 observe floor 自动 widen | AC-12 + X04；旗默认关 |
| OQ-02 | vision cohort / `fine_craft`（先 C） | 产品书面口；禁全局 auto |
| FE-ALG3-S04 | 「场景分析」hint 与 OQ-02 对齐 | 跟 vision 包 |

---

## W1b+（提纲 · 已拆上方）

| 包 | 要点 |
|----|------|
| B7 | ✅ 见上 |
| AC-10 | ✅ 合成语料门测；盲评仍须 dogfood |
| FE-ALG3-S03 | ✅ |
| 禁止 | 用「SSG 已绿」代替 AC-10 |

W2/W3/W4 其余任务见上方 **W2 后续**；W3/W4 另开 IMPL 增补。

---

## 关键代码地图（只读索引）

| 主题 | 路径 |
|------|------|
| 候选 / 硬拒 / build_screen | `layout_engine/mosaic/candidates.py` · `builders.py` |
| 几何纯函数 | `layout_engine/mosaic/slot_geometry.py` |
| 打分跳过 hard_valid | `layout_engine/mosaic/compose.py` |
| self-heal | `layout_engine/mosaic/selfheal.py` |
| SearchBudget | `layout_contract/search_budget.py` · `planner/layout_search.py` |
| 墙钟调用链 | `curation/curate.py` · `mosaic/trip.py` |
| 开关清单 | `orchestrator/happy_path_recipe.py` |
| LLM Ready | `web/studio_narrate.py` · `llm/user_settings.py` |
| explain | `curation/mosaic_explain.py` |
| stale | `curation/algorithm_profile.py` |
| CSC 基线 | `docs/acceptance-records/csc-w0-baseline-happy-path-recipe.json` |
| 场景簇 / A1 | `curation/scene_clusters.py` · `config/clustering.py` · `vision/cache.py` |
| AC-11 噪声基线 | `docs/acceptance-records/alg3-ac11-noise-baseline.json` |

---

## 风险与回滚（实施备忘）

| 风险 | 缓解 | 回滚 |
|------|------|------|
| B2a 预检误杀合法候选 | MSA 开则跳过；AC-21 逐屏；detail 可观测 | 预检 flag off 或直接删调用 |
| C1 改默认截断行为 | 仅 scoring on；默认路径字节/投影对照 | 键默认 false |
| D5 漏迁 TriState | AC-32 + Research 集合断言 | 回滚 recipe API |
| probe 仍写 environ | AC-07 | 去掉摘要调用直至修复 |
| explain 人话过长 | Top3 既有截断合同 | 缩短文案 |

---

## 编码启动顺序（给执行者）

1. ~~`feat/alg-v3-w0`~~ ✅ → ~~w1a1~~ ✅ → ~~w1a2~~ ✅ → ~~w1b~~ ✅（已合 master）。  
2. **当前**：`feat/alg-v3-w2-a3`（soft-split 自适应；**默认关**，默认成片不变）。  
3. 其后：W2-A4 实验旗 / OQ-02 cohort（各另 PR；默认成片变更须投影+盲评）。  
4. W1b 盲评问1/3 仍为独立 dogfood，不挡码。
