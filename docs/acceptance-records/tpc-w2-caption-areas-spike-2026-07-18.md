# TPC W2 · captionAreas 渲染 Spike 结论

| 属性 | 内容 |
|------|------|
| 日期 | 2026-07-18 |
| 关联 | [PRD-TEMPLATE-CONTRACT-V1](../PRD-TEMPLATE-CONTRACT-V1.md) D-TPC-07 / BLK-TPC-03 |
| 结论 | **Defer · 图文 SKU + caption tie-break 整体挪出 V1** |

## Spike 问题

`render/chapters.py` 能否消费模板 `captionAreas`，且长图导出正确呈现？

## 核查结果

| 检查项 | 结果 |
|--------|------|
| LTE schema / `TemplateDef` / 现网 YAML 是否已有 `captionAreas` | **无**（schema `additionalProperties: false`） |
| mosaic / `layout-screen.hbs` 是否渲染 per-slot 图注区 | **无**（仅有图 + 偶发 editorial-4mix copy / folio plate） |
| `asset.caption` 是否进入 screens 主路径 | **否**（legacy media-card 路径另轨） |
| 长图导出能否看到 captionAreas 区域 | **不能**（DOM 无该区域） |

## 最小闭环若要做（未开工）

1. schema + `TemplateDef` 透传可选 `captionAreas`
2. 1 个 experimental YAML + `layout-screen.hbs` markup + CSS
3. `build_layout_screen` 接线 `asset.caption`
4. 长图导出冒烟

估时超出 W2 剩余预算，且不阻塞混向 / 非对称 hero 主战场。

## 决策（冻结）

- V1 **不交付** captionAreas SKU、不实现 §3.4 caption tie-break（AC-TPC-14 条件项失败→跳过）。
- W3 手写模板包以 **混向空洞 + 非对称 hero** 保底。
- 图文能力另立小型 PRD / 后续波次再开。
