# PRD-CHAPTER-NAMING · 跨职能评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-CHAPTER-NAMING.md](../PRD-CHAPTER-NAMING.md) |
| **评审版本** | v1.0.0 → **v1.1.0** |
| **日期** | 2026-06-15 |
| **结论** | **收敛通过**（Draft · 跨职能评审已收敛） |

---

## 参会角色

产品 · UX 设计 · UX 研究 · 内容编辑 · 算法 · LLM · 前端

---

## 核心议题

章名如何更走心，且 **不画蛇添足、少 AI 味**。

---

## 全场共识

1. 问题判断成立；provisional → narrate → 可改 架构保留。  
2. AI 味主因是 **系统文艺模板**（theme/arc/「那场」体），不是 LLM 本身。  
3. **用户原词 > segment > 日期 >>> 文艺词**；起不好保留日期。  
4. 读者面 **只露 title**；lead/decorLine 默认空。  
5. 新增 **AI 味盲评** KPI；P0 **rules only**，LLM 默认关。

---

## 决议对照（已写入 v1.1）

| 议题 | v1.0 | v1.1 决议 |
|------|------|-----------|
| 默认 mode | hybrid + llm_refine | **rules** |
| P0 策略链 | 8 项含 theme/arc | **4 项** anchor/segment/date |
| anchor_primary | 可润色「寺里的雨」 | **原词直通** |
| KPI G-CN-01 | 80% 非日期 | **有 anchor 90% 原词**；无 anchor 允许日期 |
| KPI G-CN-02 | 70% 故事线 | **80% 序列可区分** + **80% 低 AI 味** |
| sequence S-01/S-03 | 强制文艺 | **删除** |
| 附录 A | 三层全满 | **sparse**；反例单独标注 |
| Studio explain | G1 默认展示 | **⋯ 二级 · 人话** |
| 锚点保存 | 提示 regenerate | **不 auto**；菜单可选 |
| 新增 | — | **D-CN-10~13** · **namingStyle** · **VR-N16** |

---

## 遗留 / 后续

- [ ] 撰写 [ACCEPTANCE-CHAPTER-NAMING.md](../ACCEPTANCE-CHAPTER-NAMING.md)  
- [ ] 撰写 [IMPLEMENTATION-CHAPTER-NAMING.md](../IMPLEMENTATION-CHAPTER-NAMING.md)  
- [ ] `docs/README.md` 索引挂链（产品自行决定时机）
