# 精修 Tab 文案/顺序 · 2026-08-04

| 属性 | 内容 |
|------|------|
| **状态** | **落地** |
| **范围** | 用户可见精修三区标签与顺序；情境默认落点不变 |

## 变更

| 项 | 旧 | 新 |
|----|----|-----|
| Tab 顺序 | 这页 · 封面 · 这本 | **封面 · 页面 · 画册** |
| page 标签 | 这页 | **页面** |
| book 标签 | 这本 | **画册** |
| 默认打开 | `resolveDefaultOpenTab`：正文→page；封面/封底→cover | **不变** |

## 触点

- [`preview-toolbar-v3-sheet.js`](../../templates/studio/preview-toolbar-v3-sheet.js) `TAB_MODES`
- 帮助 H8 / toast / shell·drawers 路径文案
- LVP 狗粮 GUIDE / 线框 F1

## 验法

精修 Sheet 顶栏应为「封面 | 页面 | 画册」；滚在正文打开精修仍落在「页面」。
