# 精修可用性优化 V1.1 · 实施清单

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-PREVIEW-REFINE-UX-V1.1.md](./PRD-PREVIEW-REFINE-UX-V1.1.md) **v0.2.1** |
| **评审纪要** | [preview-refine-ux-v1.1-review-2026-07-14.md](./acceptance-records/preview-refine-ux-v1.1-review-2026-07-14.md) |
| **线框** | [preview-refine-ux-v1.1-wireframe.html](./wireframes/preview-refine-ux-v1.1-wireframe.html) |
| **分支建议** | 当前工作分支继续，或 `feat/preview-refine-ux-v1.1` |
| **范围** | M1（模式解耦）→ M2（净化/缩略图/导出）→ M3（文案/乱码）→ M4（验收） |
| **更新日期** | 2026-07-14 |

---

## 执行序总表

| 序 | ID | 项 | 类型 | 状态 |
|----|-----|-----|------|------|
| 1 | **M1** | 模式 ≠ 面板解耦（MF-01～04 · AC-01～03/13～15） | 代码 | ✅ |
| 2 | **M1-T** | 更新 Trust 测：关 Sheet 后 `refine` 仍 `on`；静态门禁 | 测试 | ✅ |
| 3 | **M2** | 这本净化 · 迁移 tip · 封面缩略图 · 导出收敛 · hint | 代码 | ✅ |
| 4 | **M3** | 文案重命名 · 手机对照发现性 · 引号乱码 | 代码 | ✅ |
| 5 | **M4** | `ACCEPTANCE-PREVIEW-REFINE-UX-V1.1.md` + S1 手测记录 | 文档 | ✅ 模板 · 手测待补 |

**Park**：PK-01 半高面板 · PK-02 版式迷你预览 · PK-03 手机双栏 · PK-04 Copy Gate

---

## M1 任务表（本拍 · 可独立合入）

| ID | 项 | 落点 | 状态 |
|----|-----|------|------|
| **MF-01a** | `onSheetClosed` **不再** `refine=off` | `init-v3.js` | ✅ |
| **MF-01b** | 面板开再点 Dock「精修」= 关面板保模式 | `preview-toolbar-v3-sheet.js` | ✅ |
| **MF-01c** | 面板关 + 模式 on 时 Dock「完成」；点击退出模式 | `preview-mode.js` + sheet | ✅ |
| **MF-01d** | 返回首页强制 `refine=off` | `init-v3.js`（back 链） | ✅ |
| **MF-02** | Esc：面板开→关；面板已关→无操作 | `preview-toolbar-v3-sheet.js`（既有条件确认） | ✅ |
| **MF-03** | pending +「完成」→ toast + Task Dock 保留 | `init-v3.js` | ✅ |
| **MF-04a** | mode-chip「精修中」 | `preview-mode.js` + `dock.css` | ✅ |
| **MF-04b** | 首次收起面板后一次性 tip | `maybeShowRefineStarTip` | ✅ |
| **D-REFUX-02** | 「这页」空态主 CTA「收起面板，去画面上修改」 | `preview-toolbar-v3-sheet.js` | ✅ |
| **SF-04** | `aria-pressed` / `aria-expanded` 分离 | `syncRefineDockChrome` | ✅ |
| **AC 回归** | 关 Sheet 后 ★ 可见可点；完成退出后隐藏 | 静态测 + 真机狗粮 | ✅ |

### M1 非目标（勿膨胀）

- 不改「这本」字段迁移 / 封面缩略图 / 导出 Tab 改名（→ M2）  
- 不改 Share / 导出拦截 / G1 优先级栈  

### M1 文件映射

| 区域 | 文件 |
|------|------|
| 模式权威 | `templates/studio/preview-toolbar/preview-mode.js` |
| Sheet 开闭 / Dock 点击 / 空态 CTA | `templates/studio/preview-toolbar-v3-sheet.js` |
| Hooks / 完成退出 / 回首页 | `templates/studio/preview-toolbar/init-v3.js` |
| Dock「完成」样式 / chip | `templates/studio/preview-toolbar/dock.css`（+ 必要时 `drawers.css`） |
| 单测 | `tests/unit/web/test_preview_toolbar_v3.py` |

### M1 Go / No-Go

| | 标准 |
|--|------|
| **Go** | AC-REFUX-01～03、13～15；关面板后 ★ 可点；V1 导出拦截不回归；Share 无壳 |
| **No-Go** | 关面板后 `refine=off`；或 Esc 误退出模式 |

---

## M2 任务表

| ID | 项 | 落点 | 状态 |
|----|-----|------|------|
| D2 / SF-01 | 章锚点/意图迁「这页」；这本迁移 tip | `drawers.js` 拆 `bookEditTpl`/`pageEditTpl`；`maybeShowBookTabMigrateTip` | ✅ |
| D3 / MF-05 | 封面/封底缩略图；无 `asset-` 明文 | `bookends.js` + `sheet.css`（3:4、「当前」角标） | ✅ |
| D4 / SF-03 | Tab「导出」+ 更多工具；prefs 单源 | `renderAdvancedPanel`；Dock ▾ 同 `readLongshotExportPrefs` | ✅ |
| D-REFUX-05 | Sheet hint ≤1；Task Dock 主 CTA | 删 Sheet 三连脚注；保留进阶「更新版面」按钮 | ✅ |
| SF-02 | 「完成」≠「更新版面」 | M1 Dock 文案已钉死 | ✅ |

### M2 Go / No-Go

| | 标准 |
|--|------|
| **Go** | AC-REFUX-04～08、12、16；UI 无 `asset-` 明文；导出首屏无 zip/LLM |
| **No-Go** | 「这本」仍有章锚点；封面仍是 id 按钮 |

---

## M3 / M4

| ID | 项 | 状态 |
|----|-----|------|
| M3 | 「给这本游记的一句话」；手机封面首次展开 + summary；pull quote `\201C` | ✅ |
| M4 | [ACCEPTANCE-PREVIEW-REFINE-UX-V1.1.md](./ACCEPTANCE-PREVIEW-REFINE-UX-V1.1.md)；[S1 记录](./acceptance-records/preview-refine-ux-v1.1-s1-2026-07-14.md) | ✅ 模板 · 手测待补 |

---

## 对照基线（狗粮）

合入前可用此对照证明修复：

1. 打开预览 → 点「精修」→ `refine=on`、★ 出现  
2. 点 × / Esc → 面板关、**`refine` 仍 `on`、★ 仍可见可点**  
3. Dock 显示「完成」→ 点击 → `refine=off`、★ 隐藏  
4. （可选）有 layoutPending 时点「完成」→ toast + Task Dock 仍在  
5. 「这页」正文屏可见锚点；「这本 · 整本故事」无「当前章」  
6. 首次开「这本」见迁移 tip  
7. 「导出」首屏仅导出决策；「更多工具」内才有 zip / LLM  
8. 封面候选为缩略图，无 `asset-` 明文  

---

## 验收入口

- [ACCEPTANCE-PREVIEW-REFINE-UX-V1.1.md](./ACCEPTANCE-PREVIEW-REFINE-UX-V1.1.md)  
- S1：[preview-refine-ux-v1.1-s1-2026-07-14.md](./acceptance-records/preview-refine-ux-v1.1-s1-2026-07-14.md)  

