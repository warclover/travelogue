# Phase 9.2 参数建议基线（M4~M7）

基于 `docs/acceptance-records/phase9-eval-baseline.json` 自动生成的离线建议（当前样本：2 trips）。

## 1) 核心信号

- `avgCullRatio`: 0.8229
- `avgFinalRatio`: 0.8077
- `lowResDrop`: 0.0151
- `excludedTotal`: 11
- `cullQuotaRatio`: 1.0
- `blurRatio`: 0.0
- `failOpenRate`: 0.0

## 2) M4~M7 建议配置（最小可上线）

```yaml
cull:
  bucketed_blur_thresholds: false
  bucketed_blur_min_samples: 3
  enable_cull_explain: true
  score:
    duplicate_group_penalty: 0.08
```

## 3) 建议解释

- M4（分桶阈值）：当前 `blurRatio=0`，先保持关闭；样本规模扩大后再灰度开启。
- M5（重复度惩罚）：`cull_quota` 占比高，建议启用轻惩罚（0.08）提升入池多样性。
- M6（可解释性）：保持默认开启，便于 QA 复盘与线上定位。
- M7（ML 缓存）：保持开启；`w2Status=partial`，建议在回归集预热后再扩大灰度。

## 4) 复跑方式

```bash
python scripts/phase9_eval_baseline.py --write docs/acceptance-records/phase9-eval-baseline.json
```

