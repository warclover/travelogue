# Phase 6 · G1 灰度预检清单（10%）

| 属性 | 内容 |
|------|------|
| **阶段** | P6-Stability · G1 10% 灰度 |
| **前置** | G0 `passed` 或 `passed_automated_pending_blind_review` |
| **更新日期** | 2026-05-30 |

---

## 1. G0 退出条件

| # | 检查项 | 状态 |
|---|--------|------|
| 1 | AC-P6-01~08 自动化项通过 | ☑ |
| 2 | AC-P6-04 封面盲评 ≥60% | ☑ proxy 100%（待人工复核） |
| 3 | `phase6-quality-eval.json` rollup 建议 `proceed_g0_complete` | ☑ |
| 4 | P5 回滚 drill 已验证 | ☑ |

---

## 2. G1 放量前

| # | 检查项 | 命令 / 动作 | 状态 |
|---|--------|-------------|------|
| 1 | 确认 config `phase6` 开关与灰度比例 | `config.yaml` | ☐ |
| 2 | 监控 BR 导出成功率 ≥97% | 运维看板 | ☐ |
| 3 | 管线耗时 1k 回归 <10% | quality-eval KPI | ☑ fixture proxy |
| 4 | 告警通道就绪 | rollout-log alerts | ☐ |
| 5 | 回滚 runbook 24h 值班 | `phase6_apply_p5_rollback.py --dry-run` | ☑ |

---

## 3. G1 执行

```powershell
# 更新灰度状态（G1 准备）
python scripts/phase6_rollout_advance.py --prepare-g1 --write

# 正式启动 G1 10%（写 rollout-log + 可选写 config）
python scripts/phase6_rollout_advance.py --start-g1 --apply-config --write
python scripts/phase6_apply_g1_rollout.py --dry-run

# 回滚演练（dry-run）
python scripts/phase6_apply_p5_rollback.py --dry-run
```

| 字段 | 值 |
|------|-----|
| 目标用户比例 | 10% |
| 观察窗口 | ≥7 天 |
| 退出条件 | BR 无退化 / 告警触发则回滚 |

---

## 4. 人工复核（发布签字前）

- [ ] 完成 `phase6-cover-blind-review.json` 人工盲评（`--from-json --write`）
- [ ] 产品 / QA / 算法签字 G1 放量
