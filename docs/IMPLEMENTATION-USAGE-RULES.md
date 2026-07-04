# URO P0-a 实施说明

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md](./PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md) v0.2.0 |
| **阶段** | P0-a/b/c（基础设施 + UR-01～06 + 评估体系） |
| **默认** | `layout.usage_rules.enabled: false` |
| **merge 条件** | P0-a/b：`enabled=false` 可 merge；**`enabled=true` 须过 AC-URO-BLIND** |

---

## 1. 交付范围

| 组件 | 路径 | 说明 |
|------|------|------|
| 规则包 | `travelogue/curation/usage_rules/` | registry · context · evaluator · density |
| 配置 | `travelogue/config/layout.py` + `loader.py` | `UsageRulesConfig` |
| MCS 过滤 | `curation/mosaic/candidates.py` | 几何/main 通过后 `evaluate_reject` |
| Legacy 守门 | `curation/mosaic/legacy.py` | `append_legacy_window` 返回前守门 |
| Log | `curation/mosaic/log.py` + `schemas/trip.schema.json` | `usageRuleRejects` |
| 测试 | `tests/test_usage_rules_*.py` | 单元 + baseline parity + metrics |

**P0-c 已交付**：layoutMetrics 诊断块 · off/on 评估脚本 · AC-URO-BLIND 盲评模板/计分 · 循环 import 修复。

**不在 P0-c merge 门禁**：AC-URO-BLIND 人工盲评（≥55%）须单独完成后再开 `enabled=true`。

---

## 2. 调用链

```text
compose._score_window_candidates_with_rejections
  → build_window_context(...)
  → generate_window_candidates_with_rejections(..., window_ctx=ctx)
       geom_ok && main_ok && evaluate_reject → skip append
  → pick_best_window → extract usageRuleRejects from rejected

hook.try_mosaic_window → pick.used_legacy
  → append_legacy_window(ctx, ...)
       → build_legacy_screen
       → evaluate_reject(patternId, ctx) → return False if reject
```

---

## 3. UR-01 / UR-02 实现要点

**UR-01**：pattern ∈ `HERO_LED_PATTERNS` 且 `main_eligible_hero_score_gap(pattern_id) < hero_gap_threshold`。

- gap 在 **main-eligible 子集**上算（`asset_eligible_for_main_slot` + `effective_hero_score`）
- ≤1 张 eligible → gap = `+inf`（不 reject）

**UR-02**：pattern ∈ `HERO_LED_DENSE_PATTERNS` 且：

- `not layout_state.can_use_dense_collage(pattern_id)`，或
- `layout_state.last_was_dense_collage`

不维护独立 `chapter_dense_count`（D3）。

---

## 4. 配置

```yaml
layout:
  usage_rules:
    enabled: false
    hero_gap_threshold: 0.15
    hero_gap_prefer_threshold: 0.22
    tiebreak_enabled: false
    log_rejections: true
    disabled_rules: []
```

---

## 5. 验收对照

| AC | 测试 |
|----|------|
| AC-URO-01 | `test_usage_rules_baseline.py` · enabled=false 不改变候选集 |
| AC-URO-02 | `test_usage_rules_evaluator.py` · UR-01 reject main-hero |
| AC-URO-03 | rejected reason `usage_rule:UR-01` 进入 log |
| AC-URO-09 | `test_usage_rules_legacy_gate.py` · legacy 守门 |

---

## 6. P0-b 规则摘要

| 规则 | 条件 | 落点 |
|------|------|------|
| UR-03 | hero-3-2 主槽 asset AR > 1.6 | `evaluator` + 需 `screen` |
| UR-04 | 1 竖图且竖图 hero 分最高 | `evaluator` + `_can_mosaic_5_main_portrait_3land` |
| UR-05 | landscape/portrait-9 + dense breath | 复用 `can_use_dense_collage` |
| UR-06 | editorial-4mix 章配额已满 | `can_emit_editorial_composite()` |
| 空候选 | 全被 usage reject → 按 UR-06…UR-01 逆序恢复 | `candidates._restore_if_usage_emptied_candidates` |

---

## 7. P0-c 评估体系

### 7.1 诊断指标（G-URO-06 · 非 Gate）

| 指标 | 路径 | 说明 |
|------|------|------|
| `heroMismatchRate` | `usage_rules/metrics.py` | 已输出屏上 post-hoc UR-01 错配率 |
| `denseStreakViolationRate` | 同上 | 连续 dense→dense 屏对占比 |
| `patternExposureEntropy` | 同上 | patternId 分布归一化 Shannon 熵 |
| `usageRules` block | `layout_metrics.py` → `compute_usage_rules_metrics` | reject/hit 计数 · `rejectByRule` |

写入 `trip.curation.layoutMetrics`（及扁平 alias `layout.usage_rules.*`）。

### 7.2 脚本

| 脚本 | 用途 |
|------|------|
| `scripts/usage_rules_eval_report.py` | 8+3 本 trip **off/on** 对比；输出 `docs/acceptance-records/usage-rules-eval-report.json` |
| `scripts/usage_rules_blind_review.py` | `--init-template` 生成盲评 JSON；`--score` 计 AC-URO-BLIND 胜率；**`--export`** 生成 off/on A/B 渲染包 |

```bash
# 单 fixture 冒烟
python scripts/usage_rules_eval_report.py --fixture golden-mixed-scenes

# BQP golden + CI fixture 回退
python scripts/usage_rules_eval_report.py --golden

# 盲评模板（人工填 preference 后计分）
python scripts/usage_rules_blind_review.py --init-template
python scripts/usage_rules_blind_review.py --score docs/acceptance-records/usage-rules-blind-review.json --strict

# WS-0 · off/on A/B 渲染包（需 trips/{id}/ 本地目录）
python scripts/usage_rules_blind_review.py --export demo-2019 chuanzang-studio
python scripts/usage_rules_blind_review.py --export --golden
python scripts/usage_rules_blind_review.py --export demo-2019 --no-render  # 仅 curate，不渲染
```

导出物：`trips/{id}/_uro-blind-review/`（landing · key.json · preference.template.json）；A/B HTML 为 `index-uro-blind-a.html` / `index-uro-blind-b.html`；manifest：`docs/acceptance-records/usage-rules-blind-export.json`。

渲染前会 `ensure_trip_screen_ids()` 补齐缺失 `screenId`；draft 渲染使用 `validate=False`（curate 诊断字段尚未入 schema）。

`--strict` on eval report：任一 trip `layoutSnapshotEqual=false` 则 exit 1（off 基线漂移）。

### 7.3 循环 import 与 config 注入

`registry.py` 使用 pattern id **字面量**，避免 `import mosaic.constants` 触发 `mosaic/__init__` → `candidates` → `usage_rules` 环。  
`usage_rules/__init__.py` 对 `evaluate_reject` 使用 lazy `__getattr__`。  
`context.py` 对 `main_eligibility` / `runtime` 函数内 import。

**eval / blind export 脚本**：`run_variant` 在 `config_override(cfg)` 内跑 clustering+curate，使 `evaluate_reject()` 的 `get_config().layout.usage_rules.enabled` 与 off/on 变体一致（此前 on 变体 silently 等同 off）。

> `usageRuleRejectCount` 仅统计 **persisted** `usageRuleRejects`；空候选 undo（PRD §3.6）会 scrub 已恢复规则的 reject 行，故可为 0 而规则仍被执行。

### 7.4 验收对照

| AC | 验证 |
|----|------|
| AC-URO-04 prep | `usage_rules_eval_report.py --golden` · 报告 JSON |
| AC-URO-05 诊断 | 报告内 `passesHeroMismatchTarget`（≥30% 改善，**非 merge 替代盲评**） |
| AC-URO-BLIND | 人工 pairwise + `usage_rules_blind_review.py --score` ≥55% |

| 测试 | 文件 |
|----|------|
| metrics 单元 | `tests/test_usage_rules_metrics.py`（5 项） |
| eval / blind 脚本 | `tests/test_usage_rules_eval_report.py`（5 项） |

### 7.5 当前 golden 跑批结论（2026-07-04）

本地 `--golden` 共评估 **10** 本（2 本 trip 目录缺失 skip）。  
全部 `layoutSnapshotEqual=true` · `usageRuleRejectCount=0` — 说明当前 dogfood 集上规则未改变排版（符合 AC-URO-01）；  
`heroMismatchRate` 多为 `null`（无 hero-led 屏输出）。  
**AC-URO-BLIND 仍待人工 A/B** 后再考虑 `enabled=true` merge。
