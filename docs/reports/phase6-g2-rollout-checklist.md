# Phase 6 · G2 灰度预检清单（50%）

| 属性 | 内容 |
|------|------|
| **阶段** | P6-Stability · G2 50% 灰度 |
| **前置** | G1 `active_10pct` 且观察窗口 ≥7 天 |
| **更新日期** | 2026-05-30 |

---

## 1. G1 退出条件

| # | 检查项 | 状态 |
|---|--------|------|
| 1 | G1 状态 `active_10pct` | ☑ |
| 2 | 导出成功率 ≥97%（24h） | ☐ 运维看板 |
| 3 | 管线耗时回归 <15%（连续 2 天未触发告警） | ☑ fixture proxy |
| 4 | 封面偏好未低于 P5 baseline | ☑ proxy 100%（待人工复核） |
| 5 | 无 P0 事故 / 回滚 runbook 已验证 | ☑ AC-P6-07 |

---

## 2. G2 放量前

| # | 检查项 | 命令 / 动作 | 状态 |
|---|--------|-------------|------|
| 1 | BR 至少 2 项改善（相对 P5 baseline） | `phase6-quality-eval.json` KPI | ☑ fixture |
| 2 | ART-AC ≥3/5 | `phase6_art_rubric_eval.py` 或 quality `artChecks` | ☑ fixture proxy |
| 3 | 确认 config `phase6.rollout` stage=G2、50% | `config.yaml` | ☐ |
| 4 | cohortSalt 与 G1 一致 | `p6-g1-2026-05` | ☐ |

---

## 3. G2 执行

```powershell
# G2 准备（写 rollout-log G2-prep entry）
python scripts/phase6_rollout_advance.py --prepare-g2 --write

# 正式启动 G2 50%（写 rollout-log + 可选写 config）
python scripts/phase6_rollout_advance.py --start-g2 --apply-config --write
python scripts/phase6_apply_g2_rollout.py --dry-run
```

| 字段 | 值 |
|------|-----|
| 目标用户比例 | 50% |
| cohortSalt | 与 G1 相同（扩展 cohort，非重分桶） |
| 观察窗口 | ≥7 天 |
| 退出条件 | BR 至少 2 项改善 + ART-AC 3/5；告警触发则回滚 |

---

## 4. 人工复核（G3 前）

- [ ] G1 观察期 BR 真实数据回填 `brChecks`
- [ ] ART 主观评分写入 `artChecks`（≥3/5）
- [ ] 产品 / QA / 算法签字 G2 放量
