# Phase 6 · G3 全量预检清单

| 属性 | 内容 |
|------|------|
| **阶段** | P6-Stability · G3 全量 |
| **前置** | G2 `active_50pct` 且连续 7 天稳定、无 P0 事故 |
| **更新日期** | 2026-05-30 |

---

## 1. G2 退出条件

| # | 检查项 | 状态 |
|---|--------|------|
| 1 | G2 状态 `active_50pct` 或 `passed` | ☑ |
| 2 | 连续 7 天无告警（导出 / 性能 / 封面） | ☐ 生产需 `g2Observation.stableDays≥7` |
| 3 | 无 P0 事故 | ☐ 运维确认 |
| 4 | BR 指标维持 G2 改善 | ☑ fixture proxy |
| 5 | ART-AC ≥3/5 | ☑ fixture proxy |

---

## 2. G3 放量前

| # | 检查项 | 命令 / 动作 | 状态 |
|---|--------|-------------|------|
| 1 | rollout-log 告警均为 false | `phase6-rollout-log.json` alerts | ☑ |
| 2 | 封面人工盲评完成 | `phase6-cover-blind-review.json` | ☐ |
| 3 | License BOM 完整 | AC-P6-08 | ☑ |
| 4 | config `stage=G3`、`trafficPercent=100` | `config.yaml` | ☐ |

---

## 3. G3 执行

```powershell
# G3 准备（写 rollout-log G3-prep entry）
python scripts/phase6_rollout_advance.py --prepare-g3 --write

# 记录 G2 观察满 7 天（生产环境）
python scripts/phase6_rollout_advance.py --prepare-g3 --stable-days 7 --write

# 正式启动 G3 全量
python scripts/phase6_rollout_advance.py --start-g3 --apply-config --write
python scripts/phase6_apply_g3_rollout.py --dry-run
```

| 字段 | 值 |
|------|-----|
| 目标用户比例 | 100% |
| 观察窗口 | 全量后 ≥7 天监控 |
| 回滚 | `phase6_apply_p5_rollback.py --write` |

---

## 4. 发布签字

- [ ] 产品 / QA / 算法 / 工程负责人 G3 全量签字
- [ ] 更新 `phase6-quality-eval.json` rollup 为 `proceed_full_release`
- [ ] 归档 retro：`docs/reports/phase6-retro-template.md`
