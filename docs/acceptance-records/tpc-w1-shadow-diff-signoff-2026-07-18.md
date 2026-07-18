# TPC W1 · AC-TPC-12 Shadow Diff 签核（局部 corpus）

| 属性 | 内容 |
|------|------|
| 日期 | 2026-07-18 |
| 报告 | [tpc-w1-shadow-diff.json](./tpc-w1-shadow-diff.json) |
| Corpus | **局部**：`demo-2025-9` · `demo-49551086fe` · `demo-6180531087`（BQP/URO golden 多数本机无 `trip.json`） |
| 结论 | **Partial Sign-Off** — 差异已逐条定性；**不得**据此开启 `template_contract.enabled` |
| 2026-07-18 复跑 | `demo-2025-9 --from-existing` → `diffCount=2/13`（与局部签核一致）；BQP/`URO_GOLDEN` 仍未齐，`readyToEnable` 仍为 false |

## 差异汇总

| 模式 | 窗数 | 定性 | 签核 |
|------|------|------|------|
| `L0P3S0`：index 多 `screen-portrait-3-editorial` | 4 | 倒排含 editorial，现网 `try_order` 未产出该 pattern（候选超集，非丢版） | ✅ 接受超集 |
| `L4P1S0` / `L3P0S0`：live 空、index 非空 | 2 | `--from-existing` 回放已成屏资产时偶发 `ordering_failed`；成书时 live 已成功 | ✅ 标为 harness 假阳性 |

## 开启条件（未满足）

1. BQP/`URO_GOLDEN_TRIP_IDS` 本地齐备后重跑 `scripts/layout_contract_shadow_diff.py --golden`
2. 全量 `diffCount==0` 或每条 `signOff=true`
3. 报告 `readyToEnable=true` 后才允许默认开 flag

## 命令

```bash
python scripts/layout_debt_report.py --golden --out docs/acceptance-records/tpc-w1-debt-baseline.json
python scripts/layout_contract_shadow_diff.py --golden --out docs/acceptance-records/tpc-w1-shadow-diff.json
```
