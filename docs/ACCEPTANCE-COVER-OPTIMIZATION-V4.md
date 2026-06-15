# 封面优化 V4 · 验收记录

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-COVER-OPTIMIZATION-V4.md](./PRD-COVER-OPTIMIZATION-V4.md) v1.1.0 |
| **实施清单** | [IMPLEMENTATION-COVER-OPTIMIZATION-V4.md](./IMPLEMENTATION-COVER-OPTIMIZATION-V4.md) |
| **分支** | `feature/cover-optimization-v4` |
| **更新日期** | 2026-06-15 |

## 实施范围

| 阶段 | 内容 | 状态 |
|------|------|------|
| P0 | Icon Dock、状态迁移、`--preview-toolbar-h: 0` | ✅ |
| P0 | 右下实心书名卡、一屏完整 | ✅ |
| P1 | Dock 自定义 tooltip（hover/focus 300ms） | ✅ |
| P1 | Sheet 关闭焦点归还设置钮 | ✅ |
| P1 | 封面 meta 地点 · 日期单行 | ✅ |
| P2 | 滚过封面 Dock 变淡（`--dim`） | ✅ |
| P2 | 触屏长按 tooltip | ⏭ 未做（PRD 可选） |

## 自动化验收

| 套件 | 命令 | 结果 |
|------|------|------|
| 全量 V4 | 见 IMPLEMENTATION §测试命令 | ✅ **24 passed** |

### AC 覆盖映射

| AC ID | 自动化 |
|-------|--------|
| AC-COV-01 | `test_v4_preview_toolbar_playwright_smoke` |
| AC-COV-02 | `test_v4_cover_opening_layout_playwright`（toolbarH=0） |
| AC-COV-03～04, 09～10, 12 | `test_v4_preview_toolbar_playwright_smoke` |
| AC-COV-05, 08, 20, P2 变淡 | `test_v4_dock_states_playwright` |
| AC-COV-11 | `test_v4_share_preview_keeps_minimal_toolbar` |
| AC-COV-22 | Sheet 关闭 focus 断言（toolbar smoke） |
| AC-COV-30～36 | `test_v4_cover_opening_layout_playwright` |
| AC-COV-37 | `test_v4_cover_mobile_layout_unchanged` |
| AC-COV-40 | `test_cover_opening_title_card_styles` |

### 未自动化（建议人工）

| AC ID | 说明 |
|-------|------|
| AC-COV-06 | stale 琥珀态需真实导出后验 |
| AC-COV-07 | 放映 `aria-pressed` 切换需完整 screenplay.js |
| AC-COV-10 | 首访 pulse 需清 localStorage 后验 |

## 人工走查清单

- [x] Studio 预览：封面 `100dvh`，右下书名卡不溢出（Playwright AC-COV-30～32）
- [x] 长标题 / 长 hook：各 ≤2 行，封面无溢出（Playwright AC-COV-33）
- [x] Dock hover 300ms 显示中文 tooltip（Playwright AC-COV-20）
- [ ] 导出 running：真实任务流 + 任务舱同步（部分 Playwright 模拟）
- [x] 放映中 Dock 隐藏；退出后恢复（Playwright AC-COV-08）
- [x] 滚过封面后 Dock 变淡，hover 恢复（Playwright P2）
- [x] Share 模式仍为 minimal 顶栏（Playwright AC-COV-11）
- [ ] 亮图 trip 实心卡可读性抽测

## 已知限制

- 已渲染 trip 的 `journal.css` 需重新导出/同步模板后生效
- 触屏无 hover tooltip，依赖 `aria-label`
