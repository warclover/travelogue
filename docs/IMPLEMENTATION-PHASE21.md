# Travelogue · Phase 21 实施任务清单（拼图密度预算）

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-PHASE21-mosaic-density-budget.md](./PRD-PHASE21-mosaic-density-budget.md) v0.21.0 |
| **分支** | `phase21/mosaic-density-budget` |
| **状态** | ☑ 完成 |
| **更新** | 2026-06-11 |

---

## 波次总览

| 波次 | 目标 | 出口 |
|------|------|------|
| **P21-W0** | 文档 + 分支 | PRD / IMPLEMENTATION 冻结 |
| **P21-W1** | 状态机 + 配额函数 | `ScreenLayoutPlannerState` dense 字段 |
| **P21-W2** | hook 顺序 + MCS 过滤 | `try_mosaic_window` / `runtime` |
| **P21-W3** | max_mosaic_slots 接线 + config 默认 | `lte_adapter` / `config.yaml.example` |
| **P21-W4** | scorer 软惩罚 + 单测 | `test_mosaic_density_budget.py` |

---

## P21-W1 · Dense collage 配额

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| P21-1a | `dense_collage_limits_for_trip` | `screen_layout_state.py` | ☑ |
| P21-1b | `is_dense_collage_pattern` / slot 判定 | `screen_layout_state.py` | ☑ |
| P21-1c | `ScreenLayoutPlannerState` 增 `dense_*` 字段 | `screen_layout_state.py` | ☑ |
| P21-1d | `can_emit_pattern` / `note_screen` dense 逻辑 | `screen_layout_state.py` | ☑ |
| P21-1e | `LayoutDensityParams.adjust_dense_collage_limits` | `layout_density.py` | ☑ |
| P21-1f | `MosaicDensityBudgetConfig` dataclass | `config/mosaic.py` | ☑ |

---

## P21-W2 · Hook 与 runtime

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| P21-2a | `can_use_dense_collage_window(size)` | `screen_layout_state.py` | ☑ |
| P21-2b | balanced 窗宽顺序 5→4→6 | `mosaic/hook.py` | ☑ |
| P21-2c | hook 跳过超配额窗宽 | `mosaic/hook.py` | ☑ |
| P21-2d | `effective_mosaic_window_sizes` 过滤 max_slots | `mosaic/runtime.py` | ☑ |
| P21-2e | `ordered_mosaic_window_sizes()` helper | `mosaic/runtime.py` | ☑ |

---

## P21-W3 · 配置与 LTE

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| P21-3a | `max_mosaic_slots` 默认 6 | `config/layout.py` | ☑ |
| P21-3b | `mosaic_pattern_disabled` 槽位硬顶 | `mosaic/lte_adapter.py` | ☑ |
| P21-3c | 默认 `enabled_window_sizes: [4,5,6]` | `config/mosaic.py`, `config.yaml.example` | ☑ |
| P21-3d | `density_budget` YAML 段 | `config.yaml.example` | ☑ |

---

## P21-W4 · Scorer + 测试

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| P21-4a | `flat_nine_grid` / `dense_without_hero` 惩罚 | `mosaic/scorer.py` | ☑ |
| P21-4b | `tests/test_mosaic_density_budget.py` | 配额 / 相邻 / 顺序 | ☑ |
| P21-4c | 回归 `test_screen_layout_planner` 相关用例 | — | ☑ |

**验收命令**：

```powershell
python -m pytest tests/test_mosaic_density_budget.py tests/test_layout_rhythm_rules.py -q
```

---

## 迁移说明

- 默认行为变更：MCS 不再尝试 8/9 窗（仍可通过 config 打开）。
- Golden 若漂移：运行 `phase15_mosaic_eval.py` 对比 dense 屏占比后再决定是否更新 fixture。
