# Travelogue · Phase 15 验收标准

> **单轨入口**：[ACCEPTANCE.md](./ACCEPTANCE.md)  
> **PRD**：[PRD-PHASE15-photo-mosaic-evolution.md](./PRD-PHASE15-photo-mosaic-evolution.md) v0.15.1  
> **实施**：[IMPLEMENTATION-PHASE15.md](./IMPLEMENTATION-PHASE15.md)  
> **更新** | 2026-06-04

---

## 1. 功能验收（AC-P15）

| ID | 描述 | 自动化 | 通过 |
|----|------|--------|------|
| **AC-P15-01** | 5 窗候选 + 打分 | `test_mosaic_candidates.py` · `test_mosaic_integration.py` | ☑ |
| **AC-P15-02** | ≥4 新 5 张 pattern + 渲染链 | `test_mosaic_render_patterns.py` | ☑ |
| **AC-P15-03** | 5 张出现率高于基线 | `phase15_mosaic_eval.py` · `test_golden_layouts` A/B | ☑ |
| **AC-P15-04** | 可回放决策 | `test_mosaic_compose_deterministic.py` · `mosaicDecisionLog` | ☑ |
| **AC-P15-05** | 异常回退 legacy | `test_mosaic_fallback.py` · `test_mosaic_legacy_parity.py` | ☑ |
| **AC-P15-06** | 渲染无回归 | `test_mosaic_render_patterns.py`（CSS 类存在） | ☑ |
| **AC-P15-07** | top3 + reasonCodes | `test_mosaic_decision_log_contract.py` | ☑ |
| **AC-P15-08** | 低分 `fallbackReason=low_score` | `test_mosaic_fallback.py` | ☑ |

---

## 2. S2/S3 补充

| 项 | 自动化 | 通过 |
|----|--------|------|
| 3/4/6 golden | `test_golden_mosaic_unified.py` | ☑ |
| 自愈收紧 | `test_mosaic_self_heal.py` | ☑ |
| `compose_trip` | `test_mosaic_compose_trip.py` | ☑ |
| beam 在 `mosaic/search.py` | `test_layout_search.py` · `test_mosaic_budget.py` | ☑ |

---

## 3. 命令

```bash
python scripts/phase15_acceptance_bundle.py
```

或分步见 [PHASE15-ROLLOUT.md](./PHASE15-ROLLOUT.md)。

```bash
pytest tests/ -k mosaic -q
python scripts/phase15_mosaic_eval.py --write docs/acceptance-records/phase15-mosaic-eval.json
python scripts/phase15_unified_gate.py
```

---

## 4. 多场景回放（§9.3）

```bash
python scripts/phase15_replay_scenarios.py --write docs/acceptance-records/phase15-replay-scenarios.json
```

| 场景 | 说明 |
|------|------|
| `mosaic5_eligible` | 8×5 竖横混合 · mosaic5 曝光 |
| `portrait_heavy` | 竖图为主 |
| `mixed_aspects` | 横竖混合 · 4 窗 `screen-portrait-2-landscape-2`（MCS 100%） |
| `portrait_grid8` | 8 竖 · grid-8 |
| `landscape_nine` | 9 横 · 九宫格 |

## 5. 完整 curate 回放

```bash
python scripts/phase15_curate_replay.py golden-mixed-scenes --fixture \
  --write docs/acceptance-records/phase15-curate-replay.json
python scripts/phase15_curate_replay.py mao maomi linzhi   # 需 trips/{id}/trip.json
```

CI：`tests/test_phase15_curate_replay.py`（`golden-mixed-scenes` · P3-Full · mosaic off/on 屏型与指标不退化）。

## 6. PRD §7 补充指标

| 指标 | 自动化 |
|------|--------|
| `layout.pattern.repeat_rate` | `test_mosaic_coverage_metrics.py` · `layoutMetrics` |
| `layout.eligible_to_screen_coverage` | `mosaic/coverage.py` · curate 写入 |
| `layout.mosaic_v2.drop_rate` | 有 `mosaicDroppedAssetIds` 时写入 |

## 7. 仍待 / 有用户后再做

| 项 | 说明 |
|----|------|
| 真实 trip 相册（mao/maomi 等）端到端 curate 回放 | 本地 `trips/` 存在时运行 §5 第二条命令 |
| 在线 `layout.render.error_rate` 与渲染引擎聚合 | curate 已写 `template-metrics.jsonl` |
| mobile MCS | P15+ |
| 灰度 / `unified_mode` 在线自动回滚 | **无用户期跳过**；默认全开见 [PHASE15-ROLLOUT.md](./PHASE15-ROLLOUT.md) |
| Studio 接 `replan_screen` | `mosaic/replan.py` ☑ · `PATCH …/screens/{id}/replan` ☑ · `test_mosaic_replan.py` · `test_studio_handlers_replan.py` |
