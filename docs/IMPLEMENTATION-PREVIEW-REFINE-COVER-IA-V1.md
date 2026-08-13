# 精修封面 IA 升档 V1 · 实施清单

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-PREVIEW-REFINE-COVER-IA-V1.md](./PRD-PREVIEW-REFINE-COVER-IA-V1.md) **v0.1.0** |
| **线框** | [wireframes/preview-refine-cover-subseg-v1-wireframe.html](./wireframes/preview-refine-cover-subseg-v1-wireframe.html) **v1.2** |
| **分支建议** | 当前 `feat/cover-craft-focus-v1` 继续，或 `feat/preview-refine-cover-ia-v1` |
| **范围** | W1（二级分段壳 + 拆挂载）→ W2（杂志名流 + 画册去重 + 文案）→ W3（测/狗粮） |
| **更新日期** | 2026-08-11 |

---

## 执行序总表

| 序 | ID | 项 | 类型 | 状态 |
|----|-----|-----|------|------|
| 1 | **W1** | 封面二级分段照片｜版式｜杂志名；拆 Bookends / 版式 / 字体挂载 | 代码 | ✅ |
| 2 | **W2a** | 杂志名段：改名 + 生成字体；文案「字体」 | 代码 | ✅ |
| 3 | **W2b** | 画册去重（去杂志名输入）；成册风格↔版式互指；弱链 | 代码 | ✅ |
| 4 | **W2c** | 情境深链 `coverSeg`；AI Sheet 文案同步 | 代码 | ✅ |
| 5 | **W2d** | 封面点击深链 · 展示名回填 · 版式入口 · AI 深链按钮 · `open({})` | 代码 | ✅ |
| 6 | **W3** | 单测字符串门禁 + AC 手测 | 测试 | 🔄 门禁已写 · 手测待签 |

**Companion（已合入，勿回退）**：换封面忙态 `573ca42e` · `setOpeningUpdateBusy`

---

## W1 任务表

| ID | 项 | 落点 | 状态 |
|----|-----|------|------|
| **RCI-01** | 封面 Tab 顶栏下二级分段 UI（照片｜版式｜杂志名） | `preview-toolbar-v3-sheet.js` · `sheet.css` | ✅ |
| **RCI-02** | `activeCoverSeg` + `open({ coverSeg })` / `requestTabSwitch` 传 seg | sheet.js | ✅ |
| **RCI-03** | 照片段：Bookends 挂载且 **omitStyleSlot** | `bookends.js` · init hooks | ✅ |
| **RCI-04** | 版式段：`mountCoverStyleControls` + omitTitleArt；viaBookends 回调挂 root | `features.js` · init | ✅ |
| **RCI-05** | 杂志名段：改名输入 + title-art（mode=name） | `features.js` | ✅ |

### W1 文件映射

| 区域 | 文件 |
|------|------|
| Sheet IA | `templates/studio/preview-toolbar-v3-sheet.js` |
| 分段样式 | `templates/studio/preview-toolbar/sheet.css` |
| Bookends | `templates/studio/preview-toolbar/bookends.js` |
| 版式/字体 | `templates/studio/preview-toolbar/features.js` |
| Hooks | `templates/studio/preview-toolbar/init-v3.js` |

### W1 Go / No-Go

| | 标准 |
|--|------|
| **Go** | AC-RCI-01～04；版式切换仍走 bookends cascade；忙态不回退 |
| **No-Go** | 长滚动再次把三块叠在同一屏且无分段 |

---

## W2 任务表

| ID | 项 | 落点 | 状态 |
|----|-----|------|------|
| **RCI-06** | 按钮/说明改为「生成字体」；禁用「装帧字」用户文案 | features · ai-sheet | ✅ |
| **RCI-07** | 改名保存 → stale 黄条；生成前先存未保存改动 | features · inline-edit | ✅ |
| **RCI-08** | 画册：notes-only embed；去「改名字」引导；弱链去杂志名 | sheet · drawers | ✅ |
| **RCI-09** | 成册风格 ↔ 封面版式互指文案 | sheet · features | ✅ |
| **RCI-10** | 情境：书名/贴纸 → 杂志名；封面图 → 照片 | sheet open/default · init 点击深链 | ✅ |
| **RCI-11** | 杂志名回填优先 `displayTitle` / 封面 DOM | `features.js` | ✅ |
| **RCI-12** | 经典版式 toast → prefer `style`；照片段「去换版式」 | shell · sheet | ✅ |
| **RCI-13** | AI Sheet「去精修 · 杂志名」；`cover_seg_switch`；`open({})` | ai-sheet · sheet | ✅ |

### W2 Go / No-Go

| | 标准 |
|--|------|
| **Go** | AC-RCI-05～09 |
| **No-Go** | 画册仍有杂志名主输入；或 UI 仍写「装帧字」 |

---

## W3

| ID | 项 | 状态 |
|----|-----|------|
| **RCI-T** | `test_preview_toolbar_v3` 断言二级分段 / 画册去重 / 生成字体文案 / 深链 | ✅ 门禁已写 |
| **RCI-A** | [ACCEPTANCE-PREVIEW-REFINE-COVER-IA-V1.md](./ACCEPTANCE-PREVIEW-REFINE-COVER-IA-V1.md) | ✅ 模板 |
| **RCI-Dog** | [狗粮 GUIDE](./acceptance-records/preview-refine-cover-ia-v1-dogfood-GUIDE.md) 签 AC-RCI-01～11 | ⬜ 手测 |

---

## 非目标（实施勿膨胀）

- 不拆四/五一级 Tab  
- 不改 title-art 路线 B/C 算法  
- 不把路线 B 改成纯 CSS 免 PNG（OQ-RCI-02）  
- 不改精修模式≠面板状态机  
