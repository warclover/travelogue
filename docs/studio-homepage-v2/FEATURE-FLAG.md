# Studio 首页 v2 · Feature Flag 规格

> Flag ID：`studio.homepage.v2_bento`（PRD D-11 / CMP-HP2-14）
>
> **M21 目标态（当前）**：见 **[M21-ROUTING.md](./M21-ROUTING.md)** — `GET /` 直出 v2 或 classic（holdback），`/v2` 302 → `/`，应急 `/classic`。
>
> 下文 §1–§2 保留 **M20 双路由并行** 历史说明；实现已收敛为 **单根路径渲染**（M21-c）。

---

## 0. M21 门控摘要（现行）

| 模式 | `GET /` | `GET /v2` | `GET /classic` |
|------|---------|-----------|----------------|
| `on`（默认） | v2 @ `/` | 302 `/` | classic 冻结 |
| `auto` | 分桶 v2 或 classic @ `/` | 302 `/` | classic 冻结 |
| `off` | classic @ `/` | 302 `/` | classic 冻结 |

- 环境变量：`TRAVELOGUE_STUDIO_HOMEPAGE_V2=on|auto|off`（默认 **`on`**）
- **不再** `302 / → /v2`（`should_redirect_root_to_v2` 恒 `false`）
- Telemetry / LCP：`v2` → `/`，holdback 对照 **`classic`** → `/classic`（见 TELEMETRY §6；legacy 键名 `v3` 仍可读）

---

## 0.1 v2.1 工作台优化（`studio.homepage.v21_bench`）

| 属性 | 说明 |
|------|------|
| **Flag ID** | `studio.homepage.v21_bench` |
| **文档** | [PRD-STUDIO-HOMEPAGE-v2.1-OPTIMIZATION.md](../PRD-STUDIO-HOMEPAGE-v2.1-OPTIMIZATION.md) |
| **M22 默认** | **on**（与 v2 Bento 同批交付；HTML `data-homepage-v21="1"`） |
| **回滚** | 回退至 v2.0.6 bench 布局需 git revert；无独立 classic 路由 |
| **灰度判据** | 见 v2.1 PRD §8.2：`cta_click`、`import_start`、`bench_resume_click` |

P2 文案类改动（微文案、来源徽标）不设独立 flag，随 v2.1 一并上线。

---

## 1. 门控点（历史 · M20 双路由模型）

| 层级 | 决策 |
|------|------|
| **路由** | **两个独立路由**：`GET /` → `studio.html`（v3 冻结）；`GET /v2` → `studio-home-v2.html`（v2 全新 UI） |
| **模板** | **两套** HTML：`studio.html`（v3）/ `studio-home-v2.html`（v2）；各自 CSS/JS 入口 |
| **服务端注入** | 两个 handler 均仿 `handle_home` 注入 `__STUDIO_TOKEN__`；静态资源共用 `STUDIO_ASSET_PREFIX` |
| **视图** | v2 在 `homepage-v2/bootstrap.js`（DOMContentLoaded 入口）挂载独立视图层；**不** fork v3 DOM |
| **状态机** | v2 **语义对齐** `state.js` 五主态 + 异常态，但用 v2 独立视图渲染；**不复用** v3 `navigation.js` 渲染分支 |
| **共享逻辑** | 从 v2 入口 import 复用 `api.js` / `import-flow.js` / `job-poll.js` / `constants.js` / `http.js` 等（M20-d/g 接入） |
| **API** | `/__travelogue/*` 两页共用，**无新 API** |

```
GET /     → handle_home    → studio.html         （v3 · 冻结）
GET /v2   → handle_home_v2 → studio-home-v2.html  （v2 · homepage-v2/bootstrap.js）
            两者注入同一 __STUDIO_TOKEN__；静态资源 /__studio/* 共用
```

**未来切主站（M20-j，本阶段不做）**：`/` → v2，v3 迁 `/classic`；通过服务端 redirect/handler
切换，editor 内 `href="/"` 暂不改。

---

## 2. Variant 解析（双路由下）

路由即 variant：访问 `/v2` 即 v2，访问 `/` 即 v3。灰度阶段在服务端按 holdback 分桶决定
**是否将 `/` redirect 到 `/v2`**。客户端读取优先级（仅用于 dev 覆盖与分桶一致性）：

| # | 来源 | 键 / 机制 | 环境 | 说明 |
|---|------|-----------|------|------|
| 1 | **Import 进行中** | `activeJobId` 非空 | 全部 | **禁止**跨页切换 variant（AC-HP2-23）；保持当前路由 |
| 2 | **显式路由** | `/` vs `/v2` | 全部 | 用户/服务端直达；最高优先 |
| 3 | **dev 链接** | v2 topbar「经典首页 → /」 | dev | 仅 loopback 显示 |
| 4 | **sessionStorage 分桶** | `travelogue.studio.homepageVariant`（加法键） | 全部 | holdback 一致性；首帧写入 |
| 5 | **服务端 redirect 策略** | 环境变量 / yaml percent | 各环境 | 见 §3 |

`travelogue.studio.homepageVariant` 为 **加法键**（值 `v2`/`classic`，兼容 legacy `v3`），v2 首帧持久化；
**不得** rename/delete/改类型 `activeJobId` / `activePending`。

---

## 3. 各环境默认值（redirect / 渲染策略）

| 环境 | `/` 行为 | 说明 |
|------|----------|------|
| 本地 dev | 默认 `on` → v2 @ `/` | loopback 可用 `?homepageVariant=classic` 或 legacy `v3` 强制 classic |
| dogfood holdback | `auto` + percent | v2/classic **同期** @ `/`（非 redirect） |
| 100%（M21-a） | `on` → v2 @ `/` | classic 应急 → `/classic` |
| 紧急回滚 | `off` → classic @ `/` | 见 M21-ROLLBACK-CARD |

**环境变量**：`TRAVELOGUE_STUDIO_HOMEPAGE_V2=auto|on|off`（默认 **`on`**）

- `on` → `/` 100% v2
- `off` → `/` classic（回滚）
- `auto` → 读 yaml `studio.homepage.v2_bento.percent` 或 `TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT`

**yaml 示例**：[`config-holdback.example.yaml`](./config-holdback.example.yaml)

> M21-c 后：`/` 与 `/v2` **不再**并行 200；`/v2` 仅 302 兼容旧书签。

---

## 4. 共存护栏（M21 更新）

1. **Classic smoke**：`tests/test_studio_classic_freeze_smoke.py` · `gate_classic_serves_v3` 必须 green。
2. **Storage 形状**：v2 仅 **新增** `homepageVariant`；不改 `activeJobId` / `activePending` schema。
3. **Import 续跑**：`sessionStorage.activeJobId` 跨刷新；Importing 中不切换 variant（AC-HP2-23）。
4. **回滚演练**：`scripts/studio_homepage_rollback_drill.py` · `TRAVELOGUE_STUDIO_HOMEPAGE_V2=off`。
5. **Bundle 隔离**：v2 资源由 `GET /`（v2 渲染）加载；classic @ `/classic` 不加载 v2 chunk。

---

## 5. 服务端实现（双路由备忘）

| 文件 | 改动 |
|------|------|
| `travelogue/web/studio_handlers/paths.py` | `HOME_V2_PATH = "/v2"` |
| `travelogue/web/studio_handlers/static_handlers.py` | `handle_home_v2`（读 `studio-home-v2.html`，注入 token） |
| `travelogue/web/studio_routes.py` | `studio_dispatch_GET` 增 `GET /v2` 分发 + 导出 `HOME_V2_PATH` |

两 handler 共用 `_serve_studio_home(handler, template_name)`，最小 diff。

---

## 6. CMP-HP2-14 验收（双路由）

- [x] `GET /` off 模式仍 classic @ `/`（gate e2e）
- [x] `GET /v2` 200 且加载 v2 视图层
- [x] Importing 中跨页不切换 variant（AC-HP2-23）
- [x] holdback 分桶稳定（gate 单测 + `bucket.test.mjs` + 10% e2e）
- [x] 回滚（停 redirect）后 classic 忽略 `homepageVariant` 键不报错（Playwright AC-HP2-23）
