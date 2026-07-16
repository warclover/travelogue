# AAD Holdback 相册清单（M0 / M7 · AC-AAD-24）

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-ARCH-ALGO-DEEPENING-V1](../PRD-ARCH-ALGO-DEEPENING-V1.md) §8 |
| **模板** | [aad-holdback.template.json](./aad-holdback.template.json) |
| **对照** | `prefix_beam_enabled=false` |
| **实验** | `prefix_beam_enabled=true` |
| **状态** | **草稿清单** — 评委填写后复制为 `aad-holdback-YYYY-MM-DD.json` |
| **默认开** | **否**（须另 PR；平局≠默认开） |

## 多样性配额（N≥8）

| 槽位 | 约束 | 候选 tripId（待填） | 覆盖 |
|------|------|---------------------|------|
| 1 | 短途（≤1 日 / ≤40 张） | _TBD_ | ☐ |
| 2 | 长途（≥3 日或 ≥80 张） | _TBD_ | ☐ |
| 3 | 人像偏重 | _TBD_ | ☐ |
| 4 | 风景偏重 | _TBD_ | ☐ |
| 5 | 跨城 / 多段 | _TBD_ | ☐ |
| 6–8 | 补足多样性 / 难例 | _TBD_ | ☐ |

> 可从本地 `trips/` dogfood 或既有 demo（如 `demo-2025`、`linzhi`）选样；**勿**把 Studio homepage holdback 漏斗相册直接当成本清单。

## 评委维度

1. **节奏连贯** — 少连续同 pattern  
2. **拼图合理性** — 主图裁切 / 脸边  
3. **章英雄** — 英雄清晰、不埋没  

各维度至少 1 条否决样例（见模板 `vetoExamples`）。

## 结案动作

1. 填满 N≥8 `tripPairs` 盲评 preference。  
2. Gate-Q：质量不劣且无否决样例命中 → **仍保持默认关**，仅记录「可考虑默认开」。  
3. 真正默认开：另开 PR + 白话 release note（禁用 PrefixBeam / LayoutUtility 黑话）。
