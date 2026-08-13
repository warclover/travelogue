# 精修封面 IA 升档 V1 · 验收清单

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-PREVIEW-REFINE-COVER-IA-V1.md](./PRD-PREVIEW-REFINE-COVER-IA-V1.md) v0.1.0 |
| **实施清单** | [IMPLEMENTATION-PREVIEW-REFINE-COVER-IA-V1.md](./IMPLEMENTATION-PREVIEW-REFINE-COVER-IA-V1.md) |
| **线框** | [wireframes/preview-refine-cover-subseg-v1-wireframe.html](./wireframes/preview-refine-cover-subseg-v1-wireframe.html) v1.2 |
| **分支** | `feat/cover-craft-focus-v1` |
| **状态** | 工程门禁就绪 · **手测待签** |
| **日期** | 2026-08-11 |
| **狗粮脚本** | [acceptance-records/preview-refine-cover-ia-v1-dogfood-GUIDE.md](./acceptance-records/preview-refine-cover-ia-v1-dogfood-GUIDE.md) |

---

## 1. 里程碑

| 里程碑 | 状态 | 说明 |
|--------|------|------|
| **W1** | ✅ | 二级分段照片｜版式｜杂志名；拆挂载 |
| **W2** | ✅ | 杂志名流；画册去重；文案「字体」；深链 API |
| **W3** | 🔄 | 单测门禁 ✅ · AC 手测 ⬜ |
| **Companion** | ✅ | 换封面忙态不回退 |

---

## 2. AC-RCI 手测清单

| ID | 用例 | 期望 | 结果 |
|----|------|------|------|
| **AC-RCI-01** | Dock 打开精修 →「封面」 | 顶下可见二级分段照片｜版式｜杂志名，无需下滚即可点三段 | ⬜ |
| **AC-RCI-02** | 切「照片」 | 仅见换图/封面·封底切换；不见版式卡与「生成字体」主按钮 | ⬜ |
| **AC-RCI-03** | 切「版式」 | 可见 Opening 卡片与保留封面图；切换时有遮罩/「更新中」 | ⬜ |
| **AC-RCI-04** | 「照片」内切封底 | 可达封底换图；预览可滚到封底 | ⬜ |
| **AC-RCI-05** | 「杂志名」改名并保存 | `meta.title` 更新；封面展示名同步 | ⬜ |
| **AC-RCI-06** | 已有字体贴纸时改名 | 出现「杂志名已改 · 旧字体已过期…」；重新生成后提示消失且贴纸匹配新名 | ⬜ |
| **AC-RCI-07** | 「生成字体」 | 字库或（勾选）AI；失败/回退可理解；UI **无「装帧字」** | ⬜ |
| **AC-RCI-08** | 「画册」Tab | 无杂志名输入框；有一句话、成册风格、署名、进阶 | ⬜ |
| **AC-RCI-09** | 画册底「去改杂志名 / 字体」 | 一键到「封面 · 杂志名」 | ⬜ |
| **AC-RCI-10** | 成册风格 ↔ 版式 | 两侧均有「不是对方」边界文案 | ⬜ |
| **AC-RCI-11** | 情境深链 | 点封面图 → 照片；点书名/贴纸 → 杂志名；经典版式提示后开精修 → 版式（或照片段「去换版式」） | ⬜ |

---

## 3. 工程静态门禁

| 项 | 命令 / 位置 | 结果 |
|----|-------------|------|
| Sheet / 画册 / 字体文案 | `pytest tests/unit/web/test_preview_toolbar_v3.py -k ux_be_book_tab` | ⬜（合入前跑） |
| 用户文案无「装帧字」 | features / ai-sheet 源码断言 | ✅ 门禁已写 |

---

## 4. 签收

| 角色 | 签字 | 日期 |
|------|------|------|
| 工程狗粮 | | |
| 产品抽检 | | |

**Go**：Must AC-RCI-01～09 全过；Should 10～11 至少狗粮抽检通过。  
**No-Go**：画册仍有杂志名主输入；或用户可见「装帧字」；或点封面/书名无深链。
