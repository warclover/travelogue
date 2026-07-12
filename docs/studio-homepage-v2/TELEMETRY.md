# Studio 首页 v2 · 埋点与 Holdback 前置

> PRD §13.2 首版可 console + ring buffer；**§17.2 holdback 回滚判据需要真实聚合** — 本文定义 M20-i **硬前置**。

---

## 1. 现状

| 组件 | 路径 |
|------|------|
| v2 客户端 | `templates/studio/homepage-v2/**` · `templates/studio/js/analytics.js` |
| classic 应急 | `templates/studio/legacy-freeze/studio.classic.*` @ **`GET /classic`** |
| 服务端 | `travelogue/web/studio_handlers/telemetry_handlers.py` |
| 落盘 | `~/.travelogue/telemetry/studio-homepage-events.jsonl` |
| 允许事件 | `travelogue/web/studio_homepage_telemetry.py` `ALLOWED_STUDIO_HOMEPAGE_EVENTS` |

**缺口**：无聚合看板、holdback 分 variant 对比需 jsonl 同期数据、Slack 告警待接线。

---

## 1.1 历史（v3 analytics 路径）

| 组件 | 路径 |
|------|------|
| 客户端 | `templates/studio/js/analytics.js` → `POST /__travelogue/studio-event` |
| 服务端 | `travelogue/web/studio_handlers/telemetry_handlers.py` |
| 落盘 | `~/.travelogue/telemetry/studio-homepage-events.jsonl` |
| 允许事件 | `travelogue/web/studio_homepage_telemetry.py` `ALLOWED_STUDIO_HOMEPAGE_EVENTS` |

**缺口**：无聚合看板、无 holdback 分 variant 对比、无 LCP/JS error 管道。

---

## 2. M20-h 事件扩展（客户端 + 服务端同步 ALLOWED）

| 事件 | 触发 | meta（最小） |
|------|------|--------------|
| `experiment_exposure` | variant 确定 | `variant`, `bucket_id` |
| `homepage_view` | 最终态首帧 | `state`, `layout`, `variant` |
| `cta_click` | 开始制作… | `surface: bench \| headline` |
| `settings_open` | ⚙ 设置打开 | `source: toolbar` |
| `bench_resume_click` | bench「继续上次」 | `trip_id`, `stale` |
| `shelf_scroll_into_view` | 书架首次进入视口 | — |
| `sheet_open` | Sheet 开 | `state` |
| `sheet_close` | Sheet 关 | `reason` |
| `sheet_abandon` | 未 import 关 Sheet | — |
| `folder_picked` | pick 成功 | `auto_start` |
| `lightbox_open` | 放大 | `type: scroll\|longshot`, `surface: bento` |
| `spread_page_view` | carousel 翻页 | `page_index` |
| `shelf_resume_click` | 继续编辑 | `trip_id`, `stale` |

**继承不变**：`open_sheet`, `pick_folder`, `import_start`, `import_success`, `demo_try`, …

### Cover Styles V5（G-CSV-09 · Studio 预览 / 创建）

| 事件 | 触发 | meta（最小） |
|------|------|--------------|
| `cover_opening_style_assigned` | `create_trip` 写入样式 | `coverOpeningStyle`, `trip_id` |
| `cover_opening_style_render` | Web 预览首帧（每 trip 1 次） | `coverOpeningStyle`, `trip_id` |
| `cover_opening_style_change` | P1 Sheet 切换并应用排版 | `from`, `to`, `trip_id` |
| `cover_opening_style_selector_impression` | Sheet「排版」封面三选一曝光 | `coverOpeningStyle`, `trip_id` |

### Import Wizard A.1（PRD-IMPORT-WIZARD-A1-DELTA §6）

| 事件 | 触发 | meta（最小） |
|------|------|--------------|
| `photo_count_hint_show` | 验货张数弱提示展示 | `bucket: few\|many`, `photoCount` |
| `advanced_fields_toggle` | 2b 进阶 `<details>` 开合 | `open: bool` |
| `close_confirm` | 关闭确认框选择 | `action: keep\|discard\|cancel` |

登记于 `travelogue/services/studio_homepage_telemetry.py` `ALLOWED_STUDIO_HOMEPAGE_EVENTS`。

**dev ring buffer**（M20-h 可交付）：`localStorage` `travelogue.studio.eventRing` 最近 200 条 + `console.debug` — **不替代** §3 聚合。

---

## 3. M20-i 硬前置 · 真实 Telemetry（Owner 待指派）

| 交付物 | 要求 | 10% 灰度前 |
|--------|------|------------|
| **事件聚合** | 按 `variant × event × day` 汇总 jsonl（或 SQLite） | ✓ 必须 |
| **Holdback 看板** | v2 vs v3 同期：`import_success/import_start`, `cta_click`, PV | ✓ 必须 |
| **LCP P95** | loopback Lighthouse 或 Playwright trace；分 variant | ✓ 必须 |
| **JS error rate** | `window.error` + `unhandledrejection` → 同 pipeline | ✓ 必须 |
| **告警** | 24h 窗口触发 §17.2 阈值 → Slack/邮件 | 建议 |

**最小可行方案（本仓库可落地）**：

1. 脚本 `scripts/studio_telemetry_aggregate.py` 读 jsonl → 日报 CSV
2. CI / nightly：`pytest tests/test_studio_homepage_telemetry.py` + 聚合快照
3. LCP：Playwright `performance.getEntriesByType('largest-contentful-paint')` on `127.0.0.1:8766`
4. **一键演练**：`scripts/studio_homepage_m20i_drill.py`（合并 funnel + LCP + §17.2）
5. **回滚 Runbook**：[RUNBOOK-HOLDBACK.md](./RUNBOOK-HOLDBACK.md)

**Owner 占位**：见 [OPEN-QUESTIONS.md](./OPEN-QUESTIONS.md) `OQ-TELEMETRY`.

---

## 4. 回滚判据数据来源（§17.2）

| 判据 | 数据源 |
|------|--------|
| `import_success/import_start` ↓>15% | 聚合 jsonl，**同期** holdback |
| `cta_click` ↓>20% | 同上 |
| LCP P95 ↑>30% | Lighthouse CI / Playwright，分 variant |
| JS error rate ↑>2× | error pipeline，分 variant |

**禁止**：10% 阶段仅用历史 v3 baseline 自动回滚。

---

## 5. 隐私

- loopback 无 PII；`trip_id` 为 slug
- jsonl 仅存本机 `~/.travelogue/telemetry/`

---

## 6. M21 采样路径（与 LCP 对齐）

| `meta.variant` | 页面 URL | 用途 |
|----------------|----------|------|
| `v2` | **`GET /`**（v2 渲染） | 主路径 funnel · LCP |
| `classic` | **`GET /`**（classic 渲染，holdback 对照）或 **`GET /classic`**（应急 smoke） | holdback 对照 · **非**切主站前历史 baseline |
| — | `GET /v2` | 仅 302 → `/`；**不**单独采样 |

脚本常量：`scripts/studio_lcp_measure.py` → `VARIANT_PATHS = {"v2": "/", "classic": "/classic"}`（legacy 键 `v3` 可读）。

聚合：`scripts/studio_telemetry_aggregate.py` · `scripts/studio_holdback_report.py` 须按 `meta.variant` 分桶，且 holdback 阶段 v2/classic **同期** jsonl。
