# 封面多样式 V5 · 实施清单

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-COVER-STYLES-V5.md](./PRD-COVER-STYLES-V5.md) v1.1.0 |
| **验收** | [ACCEPTANCE-COVER-STYLES-V5.md](./ACCEPTANCE-COVER-STYLES-V5.md) |
| **更新日期** | 2026-06-15 |

## 变更文件

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `travelogue/services/cover_opening_style.py` | 新增 | `assign_*` / `resolve_*`；`tripId` SHA256 分配 |
| `templates/visual-journal/longshot.js` | 修改 | `prepareClone` 剥离 `color-mix`/`color()` 以兼容 html2canvas |
| `travelogue/services/trip_factory.py` | 修改 | 创建时 telemetry |
| `travelogue/web/studio_homepage_telemetry.py` | 修改 | Cover V5 事件白名单 |
| `schemas/trip.schema.json` | 修改 | `meta.coverOpeningStyle` 枚举 |
| `travelogue/render/assemble.py` | 修改 | 注入 `coverOpeningStyle` 至 Handlebars |
| `travelogue/render/context_types.py` | 修改 | `TripRenderContext.coverOpeningStyle` |
| `templates/visual-journal/partials/cover-opening.hbs` | 修改 | `data-cover-opening="{{coverOpeningStyle}}"` |
| `templates/visual-journal/journal.css` | 修改 | §4.6 token；`split-mat` / `magazine-head`；≥64rem |
| `templates/studio/preview-toolbar.js` | 修改 | Toast；telemetry；**P1 封面版式切换** |
| `templates/studio/preview-toolbar-v3-sheet.js` | 修改 | 排版 Tab 封面版式三选一 |
| `templates/studio/preview-toolbar.css` | 修改 | 封面缩略图样式 |
| `travelogue/web/copy_patch.py` | 修改 | `meta.coverOpeningStyle` patch |
| `travelogue/web/studio_entry.py` | 修改 | entry 返回 `coverOpeningStyle` |
| `travelogue/templating/guardrails.py` | 修改 | 可编辑 scope |
| `templates/visual-journal/manifest.json` | 修改 | `meta.coverOpeningStyle` editable |
| `templates/studio/js/analytics.js` | 修改 | 允许 telemetry 事件 |
| `tests/test_cover_styles_v5.py` | 新增 | 分配 / resolve / render + **Playwright AC** |
| `tests/test_cover_optimization_v4.py` | 修改 | fixture 显式 `data-cover-opening="card-br"` |
| `tests/test_asset_version.py` | 修改 | bundle bump → `ls9fa8c1f79406` |
| `docs/wireframes/cover-styles-v5-split-mat.html` | 新增 | R-06 线框 |
| `docs/wireframes/cover-styles-v5-magazine-head.html` | 新增 | R-06 线框 |
| `docs/ACCEPTANCE-COVER-STYLES-V5.md` | 新增 | 验收记录 |
| `docs/PRD-COVER-STYLES-V5.md` | 修改 | v1.1.0 跨职能评审收敛 |

**不改动**：`coverAssetId` 策展、Mobile 封面段、Icon Dock 结构、`cover-opening.hbs` 块清单。

## 分期交付

### P0

- [x] R-06 静态线框（split-mat / magazine-head）
- [x] Schema + `create_trip` 确定性分配（1:1:1）
- [x] 渲染 `data-cover-opening` + Share 同源
- [x] `split-mat` / `magazine-head` CSS（`@media min-width: 64rem`）
- [x] `<1024px` 沿用 V4 `card-br` 规则（无额外 override）
- [x] Studio 首次预览 Toast + `cover_opening_style_render`
- [x] G-CSV-09 创建时 `cover_opening_style_assigned`
- [x] D-CSV-22 预览区 Mobile 脚注
- [x] Playwright：切换 → 应用排版 / 脚注 / 书名编辑 / longshot smoke
- [x] ACCEPTANCE / IMPLEMENTATION 文档

### P1

- [x] Sheet「排版」封面版式三选一缩略图
- [x] Playwright：切换 → 应用排版 E2E（`test_cover_styles_v5_sheet_switch_and_apply_layout`）

### P2（另立项）

- [ ] Mobile 多封面 PRD

## 测试命令

```bash
python -m pytest tests/test_cover_styles_v5.py \
  tests/test_cover_optimization_v4.py \
  tests/test_asset_version.py \
  tests/test_template_integration_p13.py -q
```

## 本地预览

```bash
# 为已有 trip 写入样式（示例：linzhi → split-mat）
python -c "from travelogue.services.cover_opening_style import assign_cover_opening_style; print(assign_cover_opening_style('linzhi'))"

# 重渲染
python -m travelogue render trips/linzhi/trip.json
```

浏览器打开 Studio 预览，`data-cover-opening` 应与 `trip.json` 一致；首访该 trip 出现 Toast 一次。

## 发布后运维

1. **新建 trip** 自动带 `coverOpeningStyle`；老 trip 缺字段 → `card-br`
2. `assetVersion` 已 bump（`lsa560681aa22d`），重渲染后 CSS query 自动更新
3. telemetry：`cover_opening_style_assigned`（创建）· `cover_opening_style_render`（首次预览）· `cover_opening_style_change`（P1 切换）

## 已知限制

- 窄屏 / 对比度 / Dock 浅底：**Playwright 已覆盖**；longshot 三款 PNG + 捕获后样式表恢复 smoke
- `curate` / `rerender` 不得重算样式；**AC-CSV-03/05** 有 render 集成测试；G-CSV-09 事件有 E2E 行为断言
- 5 人走查为 UX 建议项，非阻塞发布
