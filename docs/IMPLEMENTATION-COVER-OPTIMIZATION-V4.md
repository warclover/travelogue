# 封面优化 V4 · 实施清单

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-COVER-OPTIMIZATION-V4.md](./PRD-COVER-OPTIMIZATION-V4.md) v1.1.0 |
| **分支** | `feature/cover-optimization-v4` |
| **更新日期** | 2026-06-15 |

## 变更文件

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `templates/studio/preview-toolbar.js` | 修改 | v4 Icon Dock DOM、tooltip、滚动变淡、状态迁移 |
| `templates/studio/preview-toolbar.css` | 修改 | Dock 胶囊样式、tooltip、dim、放映隐藏 |
| `templates/studio/preview-toolbar-v3-sheet.js` | 修改 | 关闭 Sheet 焦点归还设置钮 |
| `templates/visual-journal/journal.css` | 修改 | 右下实心书名卡、一屏、meta 单行 |
| `tests/test_preview_toolbar_v3.py` | 修改 | v4 选择器、tooltip、focus 断言 |
| `tests/test_cover_optimization_v4.py` | 新增 | 静态 CSS + 封面/Dock/Share Playwright |
| `tests/test_asset_version.py` | 修改 | journal.css bundle bump |
| `tests/test_studio_phase5_tier0.py` | 修改 | v4 token |
| `tests/g8_playwright_suite.py` | 修改 | 等待 `.preview-toolbar--v4` |
| `docs/ACCEPTANCE-COVER-OPTIMIZATION-V4.md` | 新增 | 验收记录 |
| `docs/PRD-COVER-OPTIMIZATION-V4.md` | 新增 | 产品需求 |
| `docs/wireframes/preview-cover-*.html` | 新增 | 线框 |

## 分期交付

### P0

- [x] Icon Dock（返回 → 放映 → 设置 → 导出）
- [x] 移除顶栏 `title-wrap`；`--preview-toolbar-h: 0`
- [x] 导出/放映/设置状态迁移
- [x] 右下实心书名卡（`journal.css`）
- [x] 取消全宽底栏渐变

### P1

- [x] Dock tooltip（hover/focus 300ms）
- [x] Sheet 关闭焦点归还
- [x] meta 地点 · 日期单行
- [x] 验收文档

### P2

- [x] 滚过封面 Dock 变淡
- [ ] 触屏长按 tooltip（可选，未做）

## 测试命令

```bash
python -m pytest tests/test_asset_version.py \
  tests/test_cover_optimization_v4.py \
  tests/test_preview_toolbar_v3.py \
  tests/test_studio_phase5_tier0.py -q
```

## 发布后运维

1. 已出货 trip 需重新渲染或同步 `journal.css` 模板
2. `assetVersion` 已 bump（`ls2dffe9baf5fb`），新渲染页面自动带新 query

## 已知限制

- 封面 focal 仍用 asset 默认点，未加 V4 专用「偏左」偏移
- 放映中 Dock 用 `visibility: hidden`（非 `display: none`），布局占位不变
- 书名编辑入口迁出顶栏属 §13 开放项，未在本迭代实现
