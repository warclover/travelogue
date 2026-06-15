# 封面多样式 V5 · 验收记录

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-COVER-STYLES-V5.md](./PRD-COVER-STYLES-V5.md) v1.1.2 |
| **实施清单** | [IMPLEMENTATION-COVER-STYLES-V5.md](./IMPLEMENTATION-COVER-STYLES-V5.md) |
| **评审纪要** | [cover-styles-prd-review-2026-06-15.md](./acceptance-records/cover-styles-prd-review-2026-06-15.md) |
| **更新日期** | 2026-06-15 |

## 实施范围

| 阶段 | 内容 | 状态 |
|------|------|------|
| P0 | R-06 两款静态线框 | ✅ |
| P0 | `meta.coverOpeningStyle` + `create_trip` 确定性分配 | ✅ |
| P0 | `split-mat` / `magazine-head` CSS（≥1024px） | ✅ |
| P0 | `<1024px` CSS 回落 `card-br` | ✅ |
| P0 | `card-br` V4 回归 | ✅ |
| P0 | Studio 首次预览 Toast + telemetry | ✅ |
| P0 | D-CSV-22 Mobile 预览脚注 | ✅ |
| P0 | G-CSV-09 创建时 telemetry | ✅ |
| P0 | 单元 / 集成 / Playwright 测试 | ✅ |
| P1 | Studio 封面版式切换 UI | ✅ |
| P1 | Playwright 切换 → 应用排版 E2E | ✅ |
| P2 | Mobile 多封面 | ⏭ 另立项 |

## 自动化验收

| 套件 | 命令 | 结果 |
|------|------|------|
| Cover Styles V5 | 见 IMPLEMENTATION §测试命令 | ✅ **58+ passed** |

### AC 覆盖映射

| AC ID | 自动化 |
|-------|--------|
| AC-CSV-01 | `test_create_trip_writes_cover_opening_style` |
| AC-CSV-02 | `test_assign_cover_opening_style_deterministic` + `test_assign_distribution_covers_all_styles` |
| AC-CSV-03 | `test_render_twice_preserves_cover_opening_style` |
| AC-CSV-04 | `test_build_render_context_legacy_trip_defaults_card_br` |
| AC-CSV-05 | `test_resolve_cover_opening_style_defaults` + `test_render_illegal_cover_opening_style_falls_back_card_br` |
| AC-CSV-10～11 | `tests/test_cover_optimization_v4.py` 全套件 |
| AC-CSV-20～25 | `test_cover_styles_v5_split_mat_layout` · `test_cover_styles_v5_narrow_viewport_falls_back_card_br` · `test_cover_styles_v5_wide_viewport_no_overflow[split-mat]` |
| AC-CSV-24 | `test_cover_styles_v5_split_mat_title_edit_keeps_style` |
| AC-CSV-30～36 | `test_cover_styles_v5_magazine_head_layout` · `test_cover_styles_v5_wide_viewport_no_overflow[magazine-head]` |
| AC-CSV-40 | `test_v4_cover_mobile_layout_unchanged` |
| AC-CSV-41～42 | V4 套件 + `test_cover_styles_v5_journal_css_tokens` |
| AC-CSV-43～45 | `test_cover_styles_v5_split_mat_layout` / `magazine_head_layout`（对比度 + Dock） |
| AC-CSV-44 | `test_cover_styles_v5_longshot_cover_smoke`（`card-br` + `magazine-head` + `split-mat` PNG 捕获与样式恢复） |
| AC-CSV-46 | `test_cover_styles_v5_first_preview_toast_once` |
| AC-CSV-47 | `test_cover_styles_v5_short_title_panel_padding` |
| AC-CSV-50～51 | `test_cover_styles_v5_narrow_viewport_falls_back_card_br` |
| AC-CSV-34 | `test_cover_styles_v5_share_keeps_style` |
| AC-CSV-23/33 | `test_cover_styles_v5_empty_hook_no_collapse` |
| G-CSV-09 创建 | `test_create_trip_records_cover_opening_style_assigned` |
| G-CSV-09 渲染 | `test_cover_styles_v5_first_preview_toast_once`（`cover_opening_style_render`） |
| G-CSV-09 切换 | `test_cover_styles_v5_sheet_switch_and_apply_layout`（`cover_opening_style_change`） |
| D-CSV-22 | `test_cover_styles_v5_mobile_footnote_visible` |
| P1 切换 | `test_cover_styles_v5_sheet_switch_and_apply_layout` |

## 人工走查清单

- [x] 线框 `cover-styles-v5-split-mat.html` / `magazine-head.html` 与 PRD §4.3/4.4 一致
- [x] **linzhi** `split-mat` 首屏：画框分屏、一屏无滚动（≥1024px）（自动化 + 已重渲染）
- [ ] 长 title + 长 hook：三款各 ≤2 行（自动化验 cover 无溢出；行数目视抽测）
- [x] hook 为空：三款 panel 不塌陷（`test_cover_styles_v5_empty_hook_no_collapse`）
- [x] 视口 1023px：回落 `card-br`（Playwright）
- [x] Share `?share=1` 样式与 draft 一致（Playwright）
- [x] 首次预览 Toast 仅一次（Playwright）
- [x] 浅底皮肤 Icon Dock 可辨识（Playwright AC-CSV-45）
- [x] longshot 封面首帧 smoke + 首章 PNG 捕获（三款 + 捕获后样式表恢复）
- [ ] **5 人走查**：是否注意到版式差异、是否满意（UX 研究建议）

## 样例 trip

| tripId | `coverOpeningStyle` | 说明 |
|--------|---------------------|------|
| `linzhi` | `split-mat`（`assign("linzhi")`） | 本地重渲染后人工抽测 |

## 已知限制

- 老 trip 无 `coverOpeningStyle` 字段时渲染为 `card-br`（符合 AC-CSV-04）
- `<1024px` 仅 CSS 回落，trip 数据层样式不变
- Mobile 封面不受本 PRD 影响
- P1 低优「创建前预览封面样式」未做
- 5 人走查为 UX 建议项，非阻塞发布
