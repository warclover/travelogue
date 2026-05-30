# Layout scoring weights

`layout.scoring` 控制 beam search 对章节候选的排序。配置见 `config.yaml.example` → `layout.scoring`。

## 启用条件

| 开关 | 效果 |
|------|------|
| `layout.scoring.enabled: false` | 使用 config 中的原始权重（常为全 0 → legacy 等价排序） |
| `layout.scoring.enabled: true` 且 weights 全 0 | 走 **预设 fallback**（见下） |
| `layout.scoring.enabled: true` 且 weights 非零 | 使用 config 权重；若 `gravity_balance=0` 且 P6 开启则补 0.05 |

## Fallback 预设（`resolve_scoring_weights`）

当 `enabled=true` 且 config weights 总和 ≈ 0 时：

1. **`enable_gravity_balance=true`（默认）** → `PHASE6_WEIGHTS`（含 `gravity_balance`）
2. **否则 + 有 dominantTone** → `PHASE3B_WEIGHTS`
3. **否则** → `PHASE3_WEIGHTS`

`is_aspect_only()` 权重（仅 `aspect_match` 非零）不会 fallback，用于 A/B 对照。

## 相关测试

- `tests/test_layout_scoring.py` — 权重解析与 fallback
- `tests/test_layout_search.py` — beam / consecutive pattern 回归

## 调参提示

- 搜索超时：`layout.scoring.search_timeout_ms`
- 评估预算：`layout.scoring.max_evaluations_per_trip`
- 运营告警阈值：`phase6.alerts`（见 `config.yaml.example`）
