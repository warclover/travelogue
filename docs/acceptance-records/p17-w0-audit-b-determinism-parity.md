# P17 W0 审计 B — 确定性 vs Parity 跑法

| 属性 | 内容 |
|------|------|
| **审计 ID** | P17-W0-B |
| **日期** | 2026-06-07 |
| **分支** | `feature/phase17-lse` |
| **状态** | 待评审 |
| **配套** | PRD §4.9、AC-P17-01；IMPLEMENTATION-PHASE17 §2 审计 B |

---

## 1. 结论摘要

| 问题 | 结论 |
|------|------|
| 现网默认路径是否非确定？ | **否**（`layout.scoring.enabled=false` 时 beam 不跑，`search_budget` 不注入） |
| `search_budget` 挂钟是否改变默认 trip 产出？ | **否**（实测 `timeout=∞` vs `1ms` screens 完全一致） |
| beam 开闸路径是否非确定？ | **是**（`scoring.enabled=true` 时挂钟截断改变 screens[]） |
| parity 基线应如何冻结？ | **受控环境逻辑等价**（见 §4 runbook）；默认路径以 MCS+stages 为准，不含 wall-clock |
| 是否需回写 PRD/AC？ | **建议微调** AC-P17-01 补充「默认路径 vs beam 路径」分层说明（§6） |

---

## 2. 代码核证：`search_budget` 作用域

### 2.1 挂钟门控实现

`travelogue/curation/search_budget.py` 中 `SearchBudget._check_timeout()` 在以下入口改变行为：

- `can_generate()` — 候选生成阶段即可能 `timed_out=True`
- `can_evaluate()` / `trip_evaluations_remaining()` — 评估阶段截断
- `note_generation()` / `note_evaluation()` — 每次操作后复检挂钟

**关键**：`timed_out=True` 后 `replan_day_buckets_beam` 走 `legacy_only` 分支，产出与完整 beam 不同。

### 2.2 调用链（仅 beam 路径）

```
run_curate (curate.py:905/936)
  → compose_trip / maybe_replan_chapters (layout_search.py:59)
      若 scoring_enabled=False → 直接 return，不建 SearchBudget
      若 scoring_enabled=True  → SearchBudget(search_timeout_ms=layout_cfg.scoring.search_timeout_ms)
  → replan_day_buckets_beam (mosaic/search.py)
      → generate_day_bucket_candidates (layout_candidates.py, budget.can_generate)
      → beam 评估循环 (budget.can_evaluate)
```

**MCS 窗级选版（`mosaic/compose.py` → `score_candidate`）不使用 `SearchBudget`**。现网主路径 `attach_screens` → `ChapterScreenPlanner` → mosaic hook 与此无关。

### 2.3 现网默认配置

| 配置项 | 默认值（`config/layout.py` + `config.yaml.example`） | 默认路径是否消费 |
|--------|------------------------------------------------------|------------------|
| `layout.scoring.enabled` | `false` | 否 — `maybe_replan_chapters` 第 59 行早退 |
| `layout.scoring.search_timeout_ms` | `2000` | 仅 `enabled=true` 时 |
| `layout.scoring.max_evaluations_per_trip` | `500` | 仅 `enabled=true` 时（确定性上限，已实现） |
| `mosaic.enabled` | `true` | 是 — MCS 窗级打分 |

---

## 3. 实证验证（W0 探针）

**脚本**：`scripts/p17_w0_search_budget_parity_probe.py`（临时，W1 后迁入 `layout_engine/cli.py audit` 或删除）

### 3.1 golden-mixed-scenes（18 张）

| 路径 | timeout ∞ vs 1ms | screenCount | layoutSearchBudget |
|------|------------------|-------------|-------------------|
| 默认 `scoring.enabled=false` | **相同** ✓ | 8 | `{}`（空，beam 未跑） |
| beam `scoring.enabled=true` | **不同** ✗ | 8 vs 3 | `timedOut: false` vs `timedOut: true` |

### 3.2 demo-2025（120 张）

| 路径 | timeout ∞ vs 1ms | screenCount | 备注 |
|------|------------------|-------------|------|
| 默认 `scoring.enabled=false` | **相同** ✓ | 52 | 现网 P16 末态代表 |
| beam `scoring.enabled=true` | **不同** ✗ | 52 vs 27 | 挂钟在首 bucket 即 `timedOut`，退 legacy_segment |

复现命令：

```powershell
cd c:\Users\xiafe\Projects\travelogue
python scripts/p17_w0_search_budget_parity_probe.py --fixture golden-mixed-scenes
python scripts/p17_w0_search_budget_parity_probe.py trips/demo-2025
```

---

## 4. 受控 Parity Runbook（可执行 · AC-P17-01）

### 4.1 环境变量与进程约束

```powershell
$env:PYTHONHASHSEED = "0"
$env:PYTHONUTF8 = "1"
# 单线程：pytest/curate 默认单进程；并行 CI 须禁 xdist 或 pin workers=1
```

| 桩点 | 做法 | 目的 |
|------|------|------|
| 挂钟 | `search_timeout_ms=2_147_483_647`（或 W1 后 `SearchBudget` 增加 `disable_wall_clock=True` 测试桩） | 消除 wall-clock 截断 |
| 评估上限 | 保留 `max_evaluations_per_trip=500`（确定性预算） | 与现网默认一致 |
| 时钟 | `unittest.mock.patch` 固定 `travelogue.util.datetime_.utc_now_iso`（decision log 时间戳比对时剥离） | 日志字段稳定 |
| 随机 | `mosaic.deterministic_strict=true`（默认） | beam tie-break 字典序 |
| 配置 | `layout.scoring.enabled=false`（P16 末态 parity 基线） | 对齐现网默认产出链 |

### 4.2 Golden Trip 集合（W1 冻结前）

| Trip | 角色 | 规模 | 状态 |
|------|------|------|------|
| `golden-mixed-scenes` | fixture · 混排 | 18 张 | ✅ 已有 |
| `trips/demo-2025` | 真实 · 中等 | 120 张 | ✅ 已有 |
| `trips/demo-151e7b488c` | 真实 · 小集 | ~5 章 PNG | ✅ 已有 |
| 人像竖图 golden | §10.3 要求 | — | ❌ W1 前待补 ≥2 |
| 风景横图 golden | §10.3 要求 | — | ❌ W1 前待补 ≥2 |

### 4.3 比对口径

**纳入比对**（screens 逻辑等价）：

```json
[
  {
    "patternId": "screen-portrait-3",
    "slots": [{"slot": 0, "assetId": "asset-001"}, ...]
  }
]
```

**排除比对**（可观测 / 非确定元数据）：

- `trip.curation.layoutDecisionLog` / `mosaicDecisionLog` 全文
- `layoutSearchBudget.elapsedMs`
- `startedAt` / `at` 时间戳
- `weightsHash`（W1 前尚未写入）

### 4.4 Parity 断言矩阵

| 场景 | `enabled` | CAP | 预期 |
|------|-----------|-----|------|
| P16 末态基线 | `false` | 无 | 受控环境 screens = 当前 master 快照 |
| W1 纯收敛 | `true` | 全关 | screens = P16 末态（adapter 仅收束参数） |
| W3b 算法 | `true` | CAP-02/03/04 逐个 | 相对 W3a 有指标增益，非 parity 等价 |
| Studio 实验 | `scoring.enabled=true` | — | **不纳入** P16 末态 parity；须单独受控基线 |

### 4.5 CI 集成草案（W1）

```powershell
# 伪命令 · W1 落地为 pytest marker @controlled_parity
python -m pytest tests/test_p17_controlled_parity.py -m controlled_parity --maxfail=1
```

前置改造（W1 任务，非 W0）：

1. `SearchBudget`：`search_timeout_ms` 仅写 telemetry，**不改变** `can_generate`/`can_evaluate`（PRD §4.9）
2. 或 parity CI 显式传 `search_timeout_ms=MAX` + `scoring.enabled=false`（当前即可跑通默认路径）

---

## 5. 去 Wall-Clock 回归面评估

### 5.1 必改文件

| 文件 | 改动 | 风险 |
|------|------|------|
| `travelogue/curation/search_budget.py` | 挂钟仅 telemetry；截断改 `max_evaluations` | 高 — 行为变更 |
| `travelogue/curation/layout_search.py` | `meta.skipReason` 语义：`search_timeout` → 仅告警 | 中 |
| `travelogue/curation/curate.py:1074` | 用户可见提示文案调整 | 低 |

### 5.2 受影响测试

| 测试文件 | 关联点 | 改造策略 |
|----------|--------|----------|
| `tests/test_search_budget.py::test_budget_times_out` | 断言 `timed_out` 改变 `can_evaluate` | **删除或改写**为「telemetry-only 告警」 |
| `tests/test_mosaic_budget.py` | `max_evaluations_per_trip=1` 截断 | 保留 — 测确定性预算 |
| `tests/test_layout_golden.py` | 默认 `scoring.enabled=false` | **不受影响** |
| `tests/test_layout_candidates.py` | `budget.can_generate` | 改后须用 `max_evaluations` 替代 timeout 测早停 |
| `scripts/phase3_*` | 显式 `search_timeout_ms=5000/8000` | 改为超大值或新桩；脚本非 CI 门禁 |

### 5.3 不受影响的现网路径

- MCS `pick_best_window` / `score_candidate`
- `ChapterScreenPlanner` stage 流水线
- `layout.scoring.enabled=false` 时的全部 golden 布局测试

---

## 6. PRD/AC 回写建议

| 文档 | 建议 |
|------|------|
| **AC-P17-01** | 补充脚注：「P16 末态 parity 默认指 `layout.scoring.enabled=false` 路径；Studio 实验开闸（`enabled=true`）的 beam 挂钟非确定性不纳入 Core parity，须受控 runbook 单独基线」 |
| **PRD §4.9** | 已正确；无需改 |
| **PRD §13.1 草案** | `planning.stages.mosaic.min_trip_photos: 20` 与代码 `MIN_TRIP_PHOTOS_FOR_MOSAIC=35` 不一致 → W1 迁入时以**代码 35** 为权威（审计 A 已记） |
| **IMPLEMENTATION §2** | 本审计完成后可将 runbook §4 升格为 W1 CI 模板 |

---

## 7. 签收

| 角色 | 签名 | 日期 |
|------|------|------|
| 开发负责人 | （待评审） | |
| 算法 | （待评审） | |
| QA | （待评审） | |
