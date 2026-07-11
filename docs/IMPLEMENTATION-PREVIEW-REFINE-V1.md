# 预览精修体验 V1 · 实施清单

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-PREVIEW-REFINE-V1.md](./PRD-PREVIEW-REFINE-V1.md) v1.2.0 |
| **分支** | `feat/preview-refine-v1-p0` |
| **范围** | **P0 第一拍**（D-REF-17 · M1 + M2 + MF-01～06） |
| **更新日期** | 2026-07-11 |

## P0 任务表

| ID | 状态 | 落点 |
|----|------|------|
| **MF-01** | ✅ | `studio-modal.js` 三钮 stacked；`longshot.js` `startLongshot` 拦截 |
| **MF-02** | ✅ | 用户可见「应用排版」→「更新版面」（toolbar / sheet / task-dock / features / cohort） |
| **MF-03** | ✅ | `dock.js` `dockIconSvg`：`back`/`play`/`refine`/`scroll`；`settings` 别名 |
| **MF-04** | ✅ | Sheet 标题「精修」；四 Tab 暂留；脚注「改精选或拼图后，请点「更新版面」。」 |
| **MF-05** | ✅ | Task Dock：G1 > layoutPending；`showStaleHint` 在 pending 时抑制 |
| **MF-06** | ✅ | pending 时必出 Modal，无法静默旧导出；「更新并导出」经 session 续跑 |
| **M1** | ✅ | Task Dock「版面有更新」；文字 Tab 失焦/chip 立即保存（去掉「保存编辑」主钮） |
| **M2** | ✅ | 「精修」改名；首页「导入偏好」；首访脉冲打在导出 |

## 文件映射

| 区域 | 文件 |
|------|------|
| Modal | `templates/studio/studio-modal.js` · `studio-modal.css` |
| 导出拦截 | `templates/studio/preview-toolbar/longshot.js` · `init-v3.js` |
| Pending / 文案 | `core.js` · `preview-toolbar-v3-task-dock.js` |
| Dock 图标 | `dock.js` · `bootstrap.js` |
| Sheet | `preview-toolbar-v3-sheet.js` · `sheet.css` |
| 立即保存 | `drawers.js` |
| 首页 | `studio-home-v2.html` · `homepage-v2/settings-panel.js` |
| 回归测 | `tests/unit/web/test_preview_toolbar_v3.py` · home/ux markers |

## P1（本拍不做）

- 三区 IA（这页 / 这本 / 导出与更多）
- G1 顶栏横幅完整体验
- 章标题 inline · trip.json 乐观锁 · 阅读视图上 Dock · 放映移出 Dock
