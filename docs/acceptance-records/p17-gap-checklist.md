# P17 PRD 缺口清单（对照 v0.17.7）

更新：`phase17_sync_rollout_gates` / 6-fixture golden / W3b-12 CI 接入后。

## P0 · 发布闸门

| 项 | 状态 | 下一步 |
|----|------|--------|
| Dogfood 14 天真实 trip | 🟡 | `--trips-dir` 跑生产相册；填满盲评 JSON |
| 盲评 ≥90% | 🟡 | `phase17_blind_review_score.py --strict` |
| Rollout AC-27/28/17b | ✅ CI 同步脚本 | `python scripts/phase17_sync_rollout_gates.py --write` |
| W3b-12 `enabled=true` | 🟡 待产品签字 | **禁止**自动翻默认 |

## P1 · Core 工程

| AC | 状态 |
|----|------|
| AC-13 bump + 反查 | ✅ lock + Studio `/weights/{hash}` |
| AC-11 六 fixture golden | ✅ DEFAULT_FIXTURES 扩展 |
| AC-28 双 fixture perf CI | ✅ |
| W3b-12 readiness CI | ✅ release block |
| AC-29 i18n/aria | ✅ first-success.js |

## P2 · Plus

| AC | 状态 |
|----|------|
| AC-12 telemetry | ✅ `phase17_strategy_telemetry.py` |
| AC-20/26 | ✅ 合成章节单测 |
| AC-25 | ✅ cap-off + 无 hint 快照 |
| W4-08 hungarian 默认 | 🟡 仍 greedy |

## W5+ / 不在 P17-Core

AC-24 pace、AC-32 viewport、CAP-07/11/12、P18 标定自动上线。
