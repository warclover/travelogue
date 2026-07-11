# 预览精修体验 V1 · 实施清单

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-PREVIEW-REFINE-V1.md](./PRD-PREVIEW-REFINE-V1.md) v1.2.0 |
| **分支** | `feat/preview-refine-v1-p0` · `feat/preview-refine-v1-p1` · `feat/preview-refine-v1-p2` |
| **范围** | **P0 第一拍**（D-REF-17 · M1 + M2 + MF-01～06） |
| **更新日期** | 2026-07-11 |

## P2 任务表（M5 / M6 · 不阻塞发布）

| ID | 状态 | 落点 |
|----|------|------|
| **M5** | ✅ | inline 成功改为字段旁 ✓（≤0.8s）；去掉「已保存到 trip.json」；首访「点一下文案可修改」保留；杂志名同轻 ✓ |
| **M6** | ✅ | `cohortEnabled` 为假时「这本」内同框区 `hidden`（不展示未开启提示） |
| **阅读视图上 Dock** | ⏸ | 仍按 PK-03 不上 Dock；留在「导出与更多」 |

### P2 文件映射

| 区域 | 文件 |
|------|------|
| Inline ✓ | `templates/visual-journal/inline-edit.js` · `inline-edit.css` |
| 封面杂志名 | `preview-toolbar/inline-edit.js` · `inline-edit.css` |
| Cohort 藏入口 | `preview-toolbar-v3-sheet.js` |

## P1 任务表（第二拍 · M4 → M3）


| ID | 状态 | 落点 |
|----|------|------|
| **M4** | ✅ | `features.js` `mountG1Banner`；顶栏「章节顺序 OK / 重新生成结构」；横幅可见时 Task Dock 不互抢 |
| **M3** | ✅ | Sheet Tab →「这页 / 这本 / 导出与更多」；这页空态；这本=文字+封面/模板/同框；导出与更多=原高级 |
| **D-REF-18** | ✅ | `_g1BannerVisible` + IntersectionObserver 镜像 |

### P1 文件映射

| 区域 | 文件 |
|------|------|
| G1 横幅 | `features.js` · `drawers.css` · `drawers.js`（regenerateStructure） |
| 优先级 | `core.js` `refreshTaskDockState` |
| 三区 IA | `preview-toolbar-v3-sheet.js` · `sheet.css` · `init-v3.js` |
| Task Dock 文案 | `preview-toolbar-v3-task-dock.js` |

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
