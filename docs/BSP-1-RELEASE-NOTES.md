# BSP-1 发布说明 · 动效预算收紧

| 属性 | 内容 |
|------|------|
| **范围** | Book Surface Program · Sprint BSP-1 |
| **日期** | 2026-06-08 |
| **关联** | [PRD-页面优化.md](./PRD-页面优化.md) §4.4 |

## 变更摘要

cinematic `breath-image` 滚动 scrub 预算收紧，避免照片 transform 越过屏缝进入 rhythm gap。

| 场景 | 变更前（约） | 变更后 |
|------|-------------|--------|
| Studio Preview · 单图 | lift 20px · scale 1.055 | lift **12px** · scale **1.035** |
| Studio Preview · 多槽 | lift 12px · scale 1.035 | lift **8px** · scale **1.02** |
| Reader · cinematic | 同上 Studio | lift **8px** · scale **1.02** |
| breath 邻接屏 | 无阻尼 | 邻接 `breath-pause` 时 **scrub=0** |
| reduced-motion | breath.js 跳过 scrub | breath-image 不注册 + CSS 清零 transform |

## 用户可见影响

- 滚动时照片「浮起」感更克制，成书缝更干净。
- Studio toolbar 展开预览与日常 Dogfood 一致；测量 vh 时请以 `window.innerHeight` 为准。

## 验收

- `pytest tests/test_bsp_surface_playwright.py -q`
- 仙本那 S3：breath-pause 与相邻屏同宽、无穿帮线
