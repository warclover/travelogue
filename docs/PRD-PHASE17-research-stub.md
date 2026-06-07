# Phase 17-B 算法预研占位（LTE 几何扩展）

| 属性 | 内容 |
|------|------|
| **状态** | 预研占位 · 不阻塞 LSE 主线 |
| **前置** | [PRD-PHASE17-layout-strategy-engine.md](./PRD-PHASE17-layout-strategy-engine.md) W4 稳定 |
| **主 PRD** | [PRD-PHASE17-layout-strategy-engine.md](./PRD-PHASE17-layout-strategy-engine.md) §13.2 |

> **注意**：匈牙利匹配、隐式反馈、段内序优化、layout-only replan 已升格为 PRD **§4.5 主线**（W3–W4），不再属于本 stub。

## 候选方向（LTE 侧）

1. **生成式 composite**：guillotine/treemap 枚举 + LTE validator 过滤
2. **7 张 4P+3L**：`4×3` 舞台新模板

## 接口预留

- `travelogue/layout_templates/p17_research.py` — spike 脚本 import 点
- MCS hook 点：`compose.score_window_candidates` 之后、`pick_best_window` 之前

## 出口条件

- LSE W4 能力增强 golden 无 regression
- spike 报告通过评审后方可并入 W5/P18
