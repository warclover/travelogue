# PRD-MOSAIC-EQUAL-GRID-CONTRACT-V1 · 跨职能评审纪要（模板）

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-MOSAIC-EQUAL-GRID-CONTRACT-V1.md](../PRD-MOSAIC-EQUAL-GRID-CONTRACT-V1.md)（**MEGC**） |
| **相邻挡门** | [MSA](../PRD-MOSAIC-SLOT-ADAPTATION-V1.md) · [MTSO](../PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) · [P16](../PRD-PHASE16-layout-template-engine.md) · [MGQ](../PRD-MCS-GEOMETRIC-QUALITY-V1.md) |
| **验收 / 实施** | [ACCEPTANCE…](../ACCEPTANCE-MOSAIC-EQUAL-GRID-CONTRACT-V1.md) · [IMPLEMENTATION…](../IMPLEMENTATION-MOSAIC-EQUAL-GRID-CONTRACT-V1.md) |
| **评审版本** | **v0.1.0 Draft** → Must-Fix 回写后升 **v0.x.x** |
| **日期** | YYYY-MM-DD（填） |
| **结论** | □ Go　□ **Conditional Go**　□ No-Go |
| **编码** | □ 仅文档　□ 可 Kickoff **M0**　□ 可 Kickoff **M1 / PR-A**　□ 可开 M2 |
| **参评角色（七席）** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版 · 用户体验（狗粮） |
| **记录人** | （填） |
| **本纪要状态** | **模板 · 备查**（结案另存 `megc-equal-grid-contract-v1-review-YYYY-MM-DD.md`） |

---

## 0. 会前宣读（3 分钟）

1. **切口**：等权格 **调轨无效**；本主题 = CSS 舞台合同 + 选型闸 + 可选释舞台。  
2. **实锤**：`demo-2019` `ch-02-sc-06` — 非「上挤下」，是扁槽 + contain 撑破。  
3. **勿重开**：舞台全书改 3:2、MSA 白名单装等权、SoftCollage、放宽竖进宽槽。  
4. **必拍**：D-00/01/03/06/09 · O-01/03/05。  
5. **列车**：先 PR-A CSS，再 PR-B 闸；禁单 PR 塞满。

---

## 1. 总评（会后一句话）

> （填）

---

## 2. 分席表决

| 席位 | 表决 | 一句话（必填） |
|------|------|----------------|
| **产品** | □ Go / □ CG / □ No | |
| **算法** | □ Go / □ CG / □ No | |
| **架构** | □ Go / □ CG / □ No | |
| **开发** | □ Go / □ CG / □ No | |
| **测试 / QA** | □ Go / □ CG / □ No | |
| **视觉 / 排版** | □ Go / □ CG / □ No | |
| **用户体验 · 狗粮** | □ Go / □ CG / □ No | |

**汇总**：_/_ 席 · 结论 ______ 

---

## 3. 事实核查

| # | 假设 | 会中 |
|---|------|------|
| **F-01～F-09** | PRD §0.3 代码/实机事实 | □ 属实 □ 修正：___ |
| **D-00** | 等权等面积 ⇒ 槽 AR≡舞台 AR | □ 属实 □ 修正：___ |

**新增事实**：

- …

---

## 4. 全场共识（预填 · 可改）

1. 等权 ⊥ 加权（MSA）；禁止假绿。  
2. 固定舞台上 contain 不得改网格外尺寸。  
3. 主路径 P-选；P-释/P-函默认 off。  
4. CSS hotfix 可先于父开关（O-05）。  
5. 混向等权比纯横等权更严。

---

## 5. Must-Fix（候选）

| ID | 议题 | 挡 |
|----|------|----|
| **BLK-MEGC-01** | D-00/01/03 一字面冻结 | M0 |
| **BLK-MEGC-02** | CSS 排除名单（portrait/stack/mosaic）签字 | M1 |
| **BLK-MEGC-03** | soft vs hard 默认（O-01） | M2 |
| **BLK-MEGC-04** | 长图导出与 P-释对齐（若开 M3） | M3 |
| **BLK-MEGC-05** | AC 禁令 X01～X03 写进验收 | M0 |

---

## 6. 拍板 D / O

| ID | 结论 |
|----|------|
| D-MEGC-00～10 | □ 按草案　□ 修改：___ |
| O-01 soft/hard | □ soft　□ hard |
| O-03 P-释 vs P-函 | □ 延期　□ P-释　□ P-函 |
| O-05 CSS 可先合 | □ 允许　□ 禁止 |

---

## 7. 结论栏

| 项 | 勾选 |
|----|------|
| Conditional Go | □ |
| 可 Kickoff M0 | □ |
| 可 Kickoff M1 | □（须 BLK） |
| No-Go 理由 | |
