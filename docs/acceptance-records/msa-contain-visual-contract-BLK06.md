# MSA · contain 视觉最低合同（BLK-MSA-06）

| 属性 | 内容 |
|------|------|
| **挡门** | BLK-MSA-06 · M2 合码前 |
| **对应 PRD** | [PRD-MOSAIC-SLOT-ADAPTATION-V1.md](../PRD-MOSAIC-SLOT-ADAPTATION-V1.md) §6.6.1 |
| **状态** | **✅ 已冻结（PR-B）** |
| **日期** | 2026-07-23 |

## 合同（一字面）

| 项 | 锁定 |
|----|------|
| **底色** | 杂志纸色：CSS `var(--msa-contain-fill, var(--bg-page, var(--color-paper, #f5f2eb)))` |
| **适用范围** | 仅 `slots[].msaContain=true` 且 `fit=contain`（由 crop_risk≥θ 且未超 whitespace_max 授予） |
| **禁止** | 装饰相框、贴纸、第二套花哨 letterbox 纹理 |
| **与 blur-fill** | MSA contain **不**启用 `layout-slot--blurred-fill`（纸色装裱，非模糊铺底） |
| **竖槽** | 既有 `portrait_fit→contain` 可无 `msaContain`；语义不另起方言 |

## 实现锚点

| 层 | 路径 |
|----|------|
| 标记 | `msa_fit.apply_crop_risk_fits` → `slot.msaContain=True` |
| 渲染 ctx | `render/context.py` → `msaContain`；禁 blur-fill |
| 模板 | `templates/visual-journal/partials/layout-screen.hbs` → `layout-slot--msa-contain` |
| CSS | `templates/visual-journal/journal-screens.css` |

## 签核

| 席位 | 结论 |
|------|------|
| 视觉 / 排版 | ✅ 纸色底线可合 PR-B（盲评可调 token，不改「无装饰框」） |
