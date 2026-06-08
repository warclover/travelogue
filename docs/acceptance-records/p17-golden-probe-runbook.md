# P17 Golden Probe Runbook

当受控 parity 在 `enabled=true` 下为零 diff 时，用 **窗级/屏级探针** 证明 capability 收益（AC-P17-16～20）。

## 命令

```bash
python scripts/phase17_golden_metrics.py --strict
python scripts/phase17_dogfood_admission.py --strict --append-rollout
```

## Fixture 矩阵

| Fixture | 主要覆盖 AC | 说明 |
|---------|-------------|------|
| `golden-mixed-scenes` | 16、18、19、20 | 风景/混合屏；色调探针用 warm/cool hex 映射 |
| `golden-p17-mixed-person` | 16、17、17b、18 | 人像 mixed；beat/显著性探针可测 |
| `golden-portrait-family` / `travel` | 16、20 | 竖图人像簇 |
| `golden-landscape-coast` / `mountain` | 18、19 | 横图风景簇 |

AC-P17-26（高光窗）在 `golden-p17-mixed-person` 上跑 curate 对比（`highlight_windows` cap）。

## 门禁合并规则

1. **Curate 指标**（`evaluate_ac_delta`）优先：delta 过线则 `passed=true`。
2. **探针救援**：curate 不可测或 parity 零 diff 时，窗级 `run_ac_probe` 过线即可。
3. **AC-P17-17b**：随 AC-P17-17 合并；beat 提升时 hero 质量不得低于 flat baseline。

## 严格模式

`--strict` 要求 `ac_p17` 中所有 AC 不为 `false`（含嵌套的 `AC-P17-17b`）。
