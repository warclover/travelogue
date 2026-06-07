# Travelogue · Phase 17 设计说明（智能排版引擎 LSE）

| 属性 | 内容 |
|------|------|
| **文档** | DESIGN-PHASE17-layout-strategy-engine |
| **版本** | v1.0（W0 冻结 · 对照 PRD v0.17.7） |
| **配套** | [PRD-PHASE17](./PRD-PHASE17-layout-strategy-engine.md) · [IMPLEMENTATION-PHASE17](./IMPLEMENTATION-PHASE17.md) · W0 审计 A/B/C |
| **状态** | W0 阻断交付 · W1 实施对照 |

> **定位**：PRD 定义策略契约与 AC；本文定义 **工程接法**——LSE 如何旁路包住 P16 `screen_planner` 链路、与 LTE/MCS/Editorial 如何分界、决策日志与治理如何落地。

---

## 1. 架构总览

```
config.yaml fragments          Strategy Pack YAML (Git)
layout.scoring / mosaic.*  ──W1 merge──>  lse-default-2026-06
ScreenLayoutPlannerState         │
                                 v
run_curate ──> layout_engine/adapter.plan_chapter_screens()
                    ├─ enabled=false → plan_screens_for_chapter (零行为变化)
                    └─ enabled=true  → 解析 pack → 同一 ChapterScreenPlanner + MCS
                                 │
                                 ├─ mosaic/scorer (乘性 · profile 注入)
                                 ├─ screen_layout_state (rhythm 配额)
                                 └─ decision_log.emit → runs/layout-decisions.jsonl

LTE (P16) ──只读──> patternId / quota / overrides.disable
Editorial ──只读 screens[]──> 可读 editorialHints (W4+)
Render ──只读 screens[]──> focal CSS（§4.10 绑定 · W3b 前置）
```

**原则（R-P17-05）**：切引擎与上 CAP 解耦；W3a `enabled=true` 纯收敛 parity，W3b 再开 CAP-02/03/04。

---

## 2. 模块职责（`travelogue/layout_engine/`）

| 模块 | 文件 | 波次 | 职责 |
|------|------|------|------|
| Registry | `registry.py` | W1 | 加载 `strategies/*.yaml`、policy merge、contentHash |
| Policy | `policy.py` | W1 | `lse_policy.yaml` + `data/lse_runtime.json` |
| Adapter | `adapter.py` | W1 | **curate 唯一入口**；15 kwargs 收束（IMPLEMENTATION §3） |
| Decision log | `decision_log.py` | W1 | sidecar schema + 投影 mosaic/beam（审计 C） |
| Validator | `validator.py` | W1 | schema.json 门禁 + dataclass 一致性 |
| CLI | `cli.py` | W1 | `validate` / `probe` / `audit-active-params` |
| Features | `features.py` | W4 | LayoutFeatures 值域 [0,1]（§4.6） |
| Slot assignment | `slot_assignment.py` | W4 | 匈牙利 + 确定性 `max_matrix_n` |
| Sandbox | `sandbox.py` | W3 | trip 重放 diff |
| Pace / hints / … | `pace.py` 等 | W3–W5 | Plus 能力 |

**不搬家（ADR-010）**：`screen_planner_stages.py` / `screen_layout_state.py` 保留原位，经 adapter 注入；W3+ 渐进迁入 `layout_engine/stages/`、`rhythm.py`。

---

## 3. 与上游/下游边界

| 邻接 | LSE 消费 | LSE 输出 | 禁止 |
|------|----------|----------|------|
| **LTE** | `patternId`、模板 scoring hint、`overrides.disable` | — | 改 YAML 几何 |
| **MCS** | 经 adapter 注入 `ScoringProfile` | — | 重写 beam/乘性模型 |
| **Editorial** | — | `editorialHints`（W4） | 改 `screens[]`、插 breath 屏 |
| **Render** | — | —（仅 trip 内 screens/slots） | 读 decisionLog 渲染 |
| **Studio** | templating 治理 | Inspector API（W2） | C 端排版工作台 |

封面选片走算法 V2 `cover_scoring`，**不经** LSE default profile（§4.8）。

---

## 4. 配置双真值与迁移

W0 审计 A 确立的权威链：

| 现网活跃 | Strategy Pack 字段 |
|----------|-------------------|
| `mosaic.weights/penalties` | `scoring_profiles.default` |
| `ScreenLayoutPlannerState` 分档 | `rhythm.nine_grid_limits` + `consecutive_bans` |
| `layout.mixed_proximity_seconds` | `planning.mixed_proximity_seconds` |
| `diversity` (mmr/0.65) | `diversity.*` |
| `layout.scoring.*`（休眠） | `search.*` + `scoring_profiles.beam` |

`layout.scoring.enabled=false` 时现网主路径 **不跑 beam**；parity 基线对此路径冻结（审计 B）。

---

## 5. 确定性预算（D-P17-05）

| 预算类型 | 现网 | W1 目标 |
|----------|------|---------|
| `max_evaluations_per_trip` | 改变产出（确定性） | 保留 |
| `search_timeout_ms` | 改变产出（非确定） | **仅 telemetry** |
| 匈牙利 `max_matrix_n` | — | W4 确定性上限 |

受控 parity runbook：`docs/acceptance-records/p17-w0-audit-b-determinism-parity.md` §4。

---

## 6. 决策日志（审计 C）

```
mosaic/hook drain ──project──> layout-decisions.jsonl
beam replan      ──project──> layout-decisions.jsonl
trip.curation.layoutStrategy ──摘要──> strategyId + weightsHash + digest
```

`explain.contribution` 用 log-domain 分解（§4.3）；W1 占位空对象，W3b 填满。

---

## 7. 治理复用（R-P17-03）

- 生命周期 / RBAC / audit：**复用** `travelogue/templating/`
- L2 runtime patch：`config_governance._apply_approved_patch` 扩 5 键（L0 发版）
- 审批语义：**ADR-013**（提议人 + ≥2 审批人 + approver≠operator）

---

## 8. 测试与 CI 护栏（W1 起）

| 护栏 | 命令 / 测试 |
|------|-------------|
| Pack schema | `layout_engine/cli.py validate` |
| 受控 parity | `tests/test_p17_controlled_parity.py`（待 W1） |
| enabled=false ≡ P16 | golden trip screens 快照 |
| quick_share 零 diff | AC-P17-27（W3a） |
| weights_hash 稳定 | `mosaic/scorer.weights_hash` 对齐 pack |

---

## 9. W0 → W1 出口

| 交付物 | 路径 | W0 |
|--------|------|-----|
| JSON Schema | `layout_engine/lse_strategy.schema.json` | ✅ |
| 默认包 | `layout_engine/strategies/default.yaml` | ✅ |
| Policy | `layout_engine/lse_policy.yaml` | ✅ |
| 设计说明 | 本文 | ✅ |
| 三项审计 | `docs/acceptance-records/p17-w0-audit-*.md` | ✅ |
| 性能 spike | — | W3 前 |
| W1 代码骨架 | `registry` + `adapter` + parity CI | 下一步 |

---

*本文档为 AC-P17-15 阻断设计说明；细节以 PRD、IMPLEMENTATION 与 W0 审计为准。*
