# CSC W0 · AppConfig 布尔四档续标（§0.0.1）

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | **active** |
| **日期** | 2026-07-22 |
| **机器可读** | [csc-w0-bool-tier-review.json](./csc-w0-bool-tier-review.json) |
| **代码种子** | `DANGER_DEFAULT_FALSE` / `RESEARCH_DEFAULT_FALSE` in `happy_path_recipe.py` |

---

## 分档口径

| 档 | 本波状态 | 数量（False 侧） |
|----|----------|------------------|
| **Danger** | 代码种子锁定单测 | **5** |
| **Research** | 种子 + 启发式扩标 | **10** |
| **Advanced** | 启发式（scoring/beam 等） | **5** |
| **advanced_or_research_pending** | 待产品续标 | **33** |
| **Happy Path（祖父 True）** | 见祖父条款 JSON | **97**（默认 True） |

## 续标规则（下一批）

1. `advanced_or_research_pending` 只许迁入 Advanced / Research / Danger，**不得**静默改默认 True。  
2. 晋升进用户常用 UI 必须占 L1 预算。  
3. Danger 默认必须保持 False（单测 + Recipe baseline）。

## Danger 种子（必须关）

见 JSON `danger_seeds`（含 `studio.g1_confirm_structure`、`mosaic.allow_drop`、`clustering.force_recluster`、`layout.strategy_engine.enabled`、`studio.layout_templates_internal`）。
