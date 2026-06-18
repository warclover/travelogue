# D-14 预览画册选择器 · 任务清单

> 权威规格：[PRD-STUDIO-HOMEPAGE-v2.md §6.8](../PRD-STUDIO-HOMEPAGE-v2.md#68-预览画册选择器d-14--v206-草案) · [DATA-CONTRACT §2.5 / §5](./DATA-CONTRACT.md)

**目标：** 用单一 select 替代双 Tab，支持指定任意用户画册预览；未指定默认示例作品。

**估时：** MVP 1.5–2d · Phase 2 +1d · Phase 3 +1–2d

---

## MVP（必做）

### 阶段 A · 状态与存储

| ID | 任务 | 文件 | DoD | AC |
|----|------|------|-----|-----|
| T1 | preference 键与读写 | `store.js` | `V2_BENTO_PREVIEW_TRIP_KEY`；read/persist/clear | — |
| T2 | 派生 `bentoTab` | `store.js`、`bento-tabs.js` | 写入只改 `bentoPreviewTripId` | AC-D14-01 |

### 阶段 B · 数据加载

| ID | 任务 | 文件 | DoD | AC |
|----|------|------|-----|-----|
| T3 | 单 trip 加载，去 tryAt | `trip-preview.js` | `resolvePreviewTrip`；404 不回退 | AC-D14-05 |
| T4 | `refreshBentoUserPreview` | `bento-tabs.js` | 仅加载 preference tripId | AC-D14-02, 08 |
| T5 | `setBentoPreviewTripId` | `bento-tabs.js` | null→demo；非 null→fetch→render | AC-D14-02 |

### 阶段 C · UI

| ID | 任务 | 文件 | DoD | AC |
|----|------|------|-----|-----|
| T6 | HTML | `studio-home-v2.html` | select 替代 Tab；label「预览画册」 | AC-D14-06 |
| T7 | picker 模块 | `bento-preview-picker.js` | init / syncOptions / change | AC-D14-02, 03 |
| T8 | CSS | `studio-home-v2.css` | select 布局 | — |

### 阶段 D · 边界与关联

| ID | 任务 | 文件 | DoD | AC |
|----|------|------|-----|-----|
| T9 | 校验与 D-13 迁移 | `bootstrap.js` / picker | 删 trip→demo+toast | AC-D14-03, 04 |
| T10 | 404 UI | `bento.js` / html / css | 占位+内联提示 | AC-D14-05 |
| T11 | demo-flag | `bento-tabs.js` | 仅 demo 时显示 | AC-D14-01, 02 |
| T12 | stale bar | `bento-stale.js` | 读 `bentoPreviewTripId` | AC-D14-07, 08 |
| T13 | 离线 | picker / bootstrap | 缓存 trips 填选项 | `test_ac_d14_offline_trips_cache` |

### 阶段 E · 遥测

| ID | 任务 | 文件 | DoD |
|----|------|------|-----|
| T14 | `bento_preview_select` | `analytics.js`、picker | payload `{ trip_id, source }` |
| T15 | allowlist | `studio_homepage_telemetry.py` | 新事件入列 |

### 阶段 F · 测试

| ID | 任务 | 文件 | AC |
|----|------|------|-----|
| T16 | 静态断言 | `test_studio_home_v2.py` | select 存在 |
| T17 | 单测（可选） | `bento-preview-picker-logic.test.mjs` | ✅ |
| T18–T19 | E2E | `test_studio_home_v2_ac_playwright.py` | AC-D14-01–06 |
| T20 | harness | `harness.js` | `?bentoPreviewTrip=` |

**MVP 完成定义：** AC-D14-01～08 通过；`test_studio_home_v2.py` + Playwright 绿。

> **PRD 对照遗漏（收尾）** → [D-14-GAP-TASKS.md](./D-14-GAP-TASKS.md)

---

## Phase 2（+1d）

| ID | 任务 | 状态 |
|----|------|------|
| P2-1 | Combobox + 缩略图 popover | ✅ |
| P2-2 | Recent 卡 `is-previewing` 描边 | ✅ |
| P2-3 | 书架「在上方预览」 | ✅ |
| P2-4 | FirstSuccess「设为首页预览」 | ✅ |
| P2-5 | Playwright 书架入口 | ✅ |

## Phase 3（+1–2d）

| ID | 任务 | 状态 |
|----|------|------|
| P3-1 | 分页 / 搜索 | ✅ |
| P3-2 | `?preview=` deep link | ✅ |
| P3-3 | AS-IS 文档更新 | ✅ |

---

## 风险自检

- [x] `null` preference 不隐式切 mine
- [x] 404 不静默换书
- [x] trips 就绪后再 syncOptions
- [x] curate 后刷新 preference trip
- [x] telemetry allowlist 已更新
