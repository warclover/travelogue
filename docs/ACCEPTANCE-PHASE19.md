# Travelogue · Phase 19 验收标准（LQU）

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-PHASE19-lean-quality-uplift.md](./PRD-PHASE19-lean-quality-uplift.md) v0.2 |
| **实施清单** | [IMPLEMENTATION-PHASE19.md](./IMPLEMENTATION-PHASE19.md) |
| **分支** | `phase19/lean-quality-uplift` |
| **终验记录** | [p19-final.json](./acceptance-records/p19-final.json) · [p19-gate-run.json](./acceptance-records/p19-gate-run.json) |
| **更新日期** | 2026-06-11 |
| **阶段状态** | **工程收尾 · 护栏 Gate 通过 · 北极星未达 · 部分 AC 延期** |
| **后续纲领** | [PRD-PRODUCT-LAYOUT-PRINCIPLES.md](./PRD-PRODUCT-LAYOUT-PRINCIPLES.md)（P-LAY-01～03） |

---

## 1. 验收结论（对照 PRD）

| 类别 | 结论 |
|------|------|
| **可合并护栏** | 自动化 Gate 全绿（`p19_golden_gate_run.py` → `p19-gate-run.json`） |
| **默认产品行为** | P19-candidate 与 P16-default **屏签名零 diff**（kill switch 默认关） |
| **北极星 AC-P19-07** | **未过**：无 ≥3 人盲评；单人 dogfood（王丹精选2）全线 tie，感知无差异 |
| **观感 SKU Gate** | 新版式 / designer SKU 占比 **未达** PRD 线（median new 1.7%、SKU 0%） |
| **减法 AC-P19-06** | LTE 运行时主路径已读 registry；`_legacy_generated` **仍为 LTE 关时 fallback** |

**阶段定性**：P19 作为 **「减法 + 硬约束 + Schema v2 基础 + 可选能力（默认关）」** 可结案；**「盲评胜率 ≥60%」** 不应在本阶段宣称达成。

---

## 2. AC 逐项（权威状态见 `p19-final.json`）

| ID | 标准（PRD §6） | 状态 | 证据 |
|----|----------------|------|------|
| **AC-P19-01** | judge–人评一致率 ≥75% | **未过** | mock judge 55.6%；无 ≥3 人校准 · `p19-judge-calibration.json` |
| **AC-P19-02** | 无 pattern 级 object-position 硬编码；CI 像素；focal telemetry | **通过** | `test_p19_focal_css.py` · `p19_focal_telemetry_audit.py` |
| **AC-P19-03** | breath=0；streak≤2；无 unfiltered fallback | **通过（自动化）** | `p19_rhythm_audit.py` 违规 0 · explicit fallback 0% |
| **AC-P19-04** | Schema v2；SKU + justified 占比达标 | **部分** | v2 + justified-row + BSP 3:2 ✅；占比 Gate ❌ |
| **AC-P19-05** | subset −25%~−40%；故事更清楚 ≥60% | **部分** | planner 中位 30.1% ✅；人评故事 ❌ |
| **AC-P19-06** | 删 `_legacy_generated` 运行时链；LSE 收编 | **部分** | 屏签名零 diff ✅；runtime fallback 仍存在 |
| **AC-P19-07** | 盲评胜率 ≥60%（≥6/8） | **未过** | `p19-human-blind-review-wangdan2.json` |
| **AC-P19-08** | curate P95 ≤+15% | **通过** | P95 −28.5% vs P16 · `p19_curate_profile.py` |

---

## 3. 自动化 Gate（一键重跑）

```bash
python scripts/p19_golden_gate_run.py
python scripts/p19_focal_telemetry_audit.py
```

| 检查项 | 阈值 | 当前 |
|--------|------|------|
| 节奏违规 | 0 | 0 |
| P16 路径屏签名 diff | 0 | 0 |
| subset 中位削减（planner only） | 25%–40% | 30.1% |
| curate P95 vs P16 | ≤+15% | −28.5% |
| explicit fallback 率 | ≤5% | 0% |
| BSP 3:2 viewport | pass | pass |
| 新版式占比中位数 | ≥10% | 1.7%（**非 Gate 阻断项，记入终验**） |
| designer SKU 占比 | ≥15% | 0%（**非 Gate 阻断项**） |

---

## 4. 人评与 dogfood

| 文档 | 用途 |
|------|------|
| [P19-HUMAN-BLIND-REVIEW.md](./P19-HUMAN-BLIND-REVIEW.md) | 组织指南 |
| `p19-human-blind-review-wangdan2.json` | 单人样本归档 |
| `scripts/p19_human_blind_pair.py` | 成稿对比（`--p19-visible` 为 dogfood 全开） |

PRD 要求 ≥3 人 × 8 本；独立开发者以 **dogfood 单本 + 自动化护栏** 替代，北极星 **不宣称通过**。

---

## 5. Sprint Gate 摘要

| Sprint | 主题 | Gate |
|--------|------|------|
| S1 | 裁判 + 像素 | partial（mock judge；focal ✅） |
| S2 | 减法 + 像素 CI | partial（零 diff ✅；legacy fallback 未删） |
| S3 | 硬约束 | pass（rhythm 0） |
| S4 | Schema v2 + SKU | partial（BSP ✅；占比 ❌） |
| S5 | DP + subset spike | partial（P95 ✅；judge/SKU ❌） |
| S6 | 集成 + 终验 | partial（代码交付 ✅；北极星 ❌） |

明细：`docs/acceptance-records/p19-sprint-gates.json`

---

## 6. 默认开关（合并后产品态）

| 开关 | 默认 | 说明 |
|------|------|------|
| `curate.subset.enabled` | `false` | Gate 后择机开 |
| `curate.highlight_opener_binding` | `false` | 同上 |
| `mosaic.chapter_dp_enabled` | `false` | 同上 |
| spread / asymmetric rollout | 15% tripId 分桶 | whitespace-hero 0% |

回滚：[P19-RUNBOOK.md](./P19-RUNBOOK.md)

---

## 7. 延期项（P19 后）

| 项 | 原因 |
|----|------|
| `_legacy_generated` 运行时 fallback 删除 | import 环；需单独 PR 断环 |
| ≥3 人 × 8 本盲评 | 人力；且默认配置下无感知 diff |
| VLM API judge 校准 | 需 API + 人评对照 |
| 北极星胜率 ≥60% | 未证明排版顺序/SKU 对用户有价值 |
| designer SKU 默认占比 | 需产品决策是否提高 rollout / 默认开 subset |

---

## 8. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-06-11 | 对照 PRD v0.2 收尾；自动化 Gate 通过；北极星与 SKU 占比未达 |
