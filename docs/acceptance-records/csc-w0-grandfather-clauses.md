# CSC W0 · 祖父条款（§8.1）

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | **active** |
| **日期** | 2026-07-22 |
| **机器可读** | [csc-w0-grandfather-clauses.json](./csc-w0-grandfather-clauses.json)（**97** 条） |
| **含义** | 当前 `AppConfig()` 默认 **True** 的成册能力面；本波**不强制**重做分享意愿盲测 |

---

## 纪律

1. 从默认 **移除**（True→False）须产品评审 + 回归，禁止 silently。  
2. **新增**默认 True 须改 Recipe 基线 + 过 §8.2；`python scripts/lint_csc_recipe_baseline.py` / 单测红灯。  
3. 四档细标见 [csc-w0-bool-tier-review.md](./csc-w0-bool-tier-review.md)；祖父清单本身不等于「全部已人审为 Happy Path 品牌名」。

## 摘要

| 项 | 值 |
|----|-----|
| 默认 True（祖父） | **97** |
| 默认 False（防火墙/高级） | **53** |
| 完整路径列表 | JSON `grandfatherClauses` |
