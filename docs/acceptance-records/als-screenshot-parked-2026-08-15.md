# ALS · 长图截屏不可用 · 横版画册导出待调整

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-15 |
| **分支** | `park/als-screenshot-unusable` |
| **权威** | 本纪要（产品拍板）· 原合同 [PRD-ALBUM-LANDSCAPE-SCREENS-V1.md](../PRD-ALBUM-LANDSCAPE-SCREENS-V1.md) **截屏方案停泊** |
| **状态** | **parked** · 截屏内核仅作考古；导出模式等待独立 `page-*` 模板系统 |

---

## 结论（勿重开）

1. **用 Web 长图 / `index.html` 逐屏截图做出 16:9 画册，不可用。**  
   阅读流不是胶片：章名、票根分隔、封面文案带、`viewport-fit` 收窄导致大约 30% 页错位。能「同一部」，做不到「每一页都是干净 16:9 画册页」。
2. **不要为对齐画册去改微信长图、`index-longshot.html`、日常预览 CSS。**  
   长图与横版画册 **不共享管线、不共享脸库、不再截屏。**
3. **横版画册导出模式等待调整。**  
   下一条路：单独建 `page-*` 16:9 页模板 + 离线合成（不进 Playwright）。平台 id 仍可用 `album_landscape`。社交 `card-*`、Web `screen-*`、画册 `page-*` 三柜分立。  
   与 [TEMPLATE-SYSTEM-UPGRADE.md](../templates/TEMPLATE-SYSTEM-UPGRADE.md) 送审稿的分歧：该稿写「同一套 `page-*` 服务 Web 与画册」——**已改**，画册脸库不服务长图。

## 本分支保存了什么

第七出口隔离实现（注册、菜单、错误码、CDP 视口截屏内核、单测）。这是对话期间的活代码，**不是**下一版产品合同。新模板系统落地后，截屏内核应卸下，不要当 fallback 与 `page-*` 混出。

## 明确不要做

- 继续用截屏补 16:9 细节
- 截屏与 `page-*` 同一次导出混出
- 改 `album_spread` / CardGrouper / 六种长图路径
