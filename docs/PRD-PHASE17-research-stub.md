# Phase 17 research stub (out of P16 scope)

| 属性 | 内容 |
|------|------|
| **状态** | 预研占位 · 未开工 |
| **前置** | Phase 16 LTE 默认路径稳定 |

## 候选方向（PRD §15.3）

1. **匈牙利匹配**：窗口内资产 ↔ 槽位全局最优（替代贪心 `try_order_for_pattern`）
2. **生成式合成**：`4×3` 舞台、7 张 `4P+3L` 自动拓扑
3. **6×6 扩展舞台**：超出 P16 `max≤9` 约束的新 schema 分支

## 接口预留

- `travelogue/layout_templates/p17_research.py` — 空模块，供 spike 脚本 import
- MCS hook 点：`compose.score_window_candidates` 之后、`pick_best_window` 之前

## 出口条件

- P16 dogfood 指标稳定 2 周
- Collage / 探针 CI 无 regression
