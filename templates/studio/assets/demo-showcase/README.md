# Studio 首页 demo-showcase 资产

| 属性 | 内容 |
|------|------|
| **用途** | 首页 v2 Bento：大屏卷轴 carousel + 手机长图 strip 样品图 |
| **清单** | [manifest.json](./manifest.json)（schema 见 `manifest.schema.json`） |
| **关联** | [PRD-SHARE-READY-OPTIMIZATION-V1](../../../../docs/PRD-SHARE-READY-OPTIMIZATION-V1.md) §3.1 · D-SR-03 · DOC-SR-03 |
| **状态（2026-07-28）** | **已烘焙真图**（源：`trips/demo-album` · 斯里兰卡见闻录 · 16 张）· 帧宽 ≥200 · 无默认 PLACEHOLDER |

---

## 1. 合同（敢发闭环 W0）

| 必须 | 禁止 |
|------|------|
| 关键帧 webp `naturalWidth ≥ 200` | 默认上线 `*-PLACEHOLDER.webp` 黑块 |
| manifest 指向真实文件名 | 静默缺图当「有样品」 |
| 样品区标「示例」徽标 | 使用无版权第三方成片 |

---

## 2. 刷新步骤（编码时执行）

```powershell
# 源：trips/demo-album 已 curate/render
python scripts/bake_demo_showcase.py
```

体积建议：单张 webp 控制在合理首页预算内；整包目标 ≤800KB。

---

## 3. 版本记录

| 日期 | 说明 |
|------|------|
| 2026-07-28 | 换源斯里兰卡见闻录（16 张）；manifest `2026.07.28-sri-lanka-bake` |
| 2026-07-17 | W0：自 demo-album 烘焙 `background/longshot/scroll/*`；manifest `2026.07.17-demo-album-bake` |
| 2026-07-17 | 文档合同落地（Share-Ready 评审 BLK-06） |
