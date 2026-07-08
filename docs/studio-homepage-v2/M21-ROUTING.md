# Studio 首页 · 路由与门控（M21 目标态）

> **权威文档**（2026-06-06 文档债收口）。代码以 `travelogue/web/studio_homepage_gate.py` · `studio_routes.py` 为准。

---

## 1. URL 一览

| 路径 | HTTP | 模板 / 行为 | `meta.variant` | 说明 |
|------|------|-------------|----------------|------|
| **`GET /`** | 200 | `studio-home-v2.html` 或 `legacy-freeze/studio.classic.html` | `v2` / `classic` | **唯一主入口**；按门控在根路径直接渲染 |
| **`GET /v2`** | **302 → `/`** | — | — | 旧书签兼容；M21-c 已收敛 |
| **`GET /classic`** | 200 | `legacy-freeze/studio.classic.*` | — | **deprecated** 应急入口；长期保留 |
| **`GET /{tripId}/…`** | 不变 | 预览 / 长图 | — | 与首页 variant 无关 |

**默认门控**：`TRAVELOGUE_STUDIO_HOMEPAGE_V2=on`（未设置 env 时亦为 `on`）。

---

## 2. 门控模式

| 模式 | `GET /` | `GET /classic` | 典型用途 |
|------|---------|----------------|----------|
| **`on`** | 始终 v2 | classic 冻结页 | 生产默认 · M21-a 切主站后 |
| **`auto`** | 按分桶 percent：`bucket < percent` → v2，否则 classic @ `/` | 同上 | 10% holdback |
| **`off`** | classic @ `/` | 同上 | 事故回滚（`M21-ROLLBACK-CARD.md`） |

**M21-c 变更**：`/` **不再** `302 → /v2`；variant 在根路径 **200 直出**（`should_redirect_root_to_v2` 恒为 `false`）。

---

## 3. 环境变量

```bash
# 主路径 v2（默认）
TRAVELOGUE_STUDIO_HOMEPAGE_V2=on

# holdback
TRAVELOGUE_STUDIO_HOMEPAGE_V2=auto
TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT=10

# 回滚
TRAVELOGUE_STUDIO_HOMEPAGE_V2=off
```

yaml 可选：`studio.homepage.v2_bento.percent`（见 `config-holdback.example.yaml`）。

---

## 4. Telemetry 口径（M21-c）

| 场景 | 采样 URL | `meta.variant` | 对照组 URL |
|------|----------|----------------|------------|
| v2 主路径 | **`/`**（v2 渲染） | `v2` | — |
| holdback 对照 | **`/`**（classic 渲染） | `v3` | 同期 jsonl，**非**历史 v3 baseline |
| 应急 classic | **`/classic`** | 通常不上报 holdback | 人工 smoke |
| LCP / Playwright | `scripts/studio_lcp_measure.py` | `v2` → `/`，`classic` → `/classic` | 见 `VARIANT_PATHS` |

**禁止**：10% 阶段仅用切主站前的 classic `@ /` 历史数据做自动回滚（须 v2/classic **同期** holdback）。

客户端：`templates/studio/homepage-v2/**` · 共享 `templates/studio/js/analytics.js` → `POST /__travelogue/studio-event` → `~/.travelogue/telemetry/studio-homepage-events.jsonl`。

---

## 5. 快速验证

```powershell
# 门控决策（不启服务器）
TRAVELOGUE_STUDIO_HOMEPAGE_V2=on python scripts/studio_homepage_gate_status.py --json

# 根路径 variant
curl -s http://127.0.0.1:8766/ | findstr data-homepage-variant

# /v2 收敛
curl -sI http://127.0.0.1:8766/v2 | findstr Location

# 应急入口
curl -s http://127.0.0.1:8766/classic | findstr studio.classic
```

---

## 6. 相关文档

| 文档 | 用途 |
|------|------|
| [FEATURE-FLAG.md](./FEATURE-FLAG.md) | 门控历史与 holdback 细节 |
| [TELEMETRY.md](./TELEMETRY.md) | 事件列表与聚合 |
| [RUNBOOK-HOLDBACK.md](./RUNBOOK-HOLDBACK.md) | 回滚判据与演练 |
| [M21-RELEASE-NOTES.md](./M21-RELEASE-NOTES.md) | 发版说明模板 |
| [PRD-M21-studio-homepage-v3-retirement.md](../PRD-M21-studio-homepage-v3-retirement.md) | 产品 PRD |
