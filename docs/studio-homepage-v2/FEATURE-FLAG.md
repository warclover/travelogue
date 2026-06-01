# Studio 首页 v2 · Feature Flag 规格

> Flag ID：`studio.homepage.v2_bento`（PRD D-11 / CMP-HP2-14）
>
> **架构变更（M20 · 冻结）**：放弃「单模板同页 feature flag」，改为 **双路由并行**
> （`/` = v3，`/v2` = v2）。M20-a–h 阶段两页独立演进、并排对比；灰度/切主站
> （M20-i/j）以 **服务端 redirect** 实现，而非客户端在 `studio.js` 内 dynamic import。

---

## 1. 门控点（冻结 · 双路由模型）

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

`travelogue.studio.homepageVariant` 为 **加法键**（值 `v2`/`v3`），v2 首帧持久化；
**不得** rename/delete/改类型 `activeJobId` / `activePending`。

---

## 3. 各环境默认值（redirect 策略）

| 环境 | `/` 行为 | 说明 |
|------|----------|------|
| 本地 dev | `/` 留 v3；`/v2` 直达 v2 | 并排对比开发；v2 topbar 提供回 `/` 链 |
| dogfood | `/` 留 v3（或团队按需直达 `/v2`） | 团队内测对比 |
| 10% holdback | `/` 按 `bucket_id` redirect：命中桶 → `302 /v2`，否则留 v3 | 稳定 `bucket_id` hash(UA+首次日期) 或 server cookie；`experiment_exposure` 必报 |
| 100%（M20-j） | `/` → v2（v3 迁 `/classic`） | 切主站 |
| 紧急回滚 | `/` 全部留 v3；停止 redirect | **不清** session job 键 |

**环境变量（建议）**：`TRAVELOGUE_STUDIO_HOMEPAGE_V2=auto|on|off`

- `on` → `/` 100% redirect 到 `/v2`
- `off` → `/` 不 redirect（回滚到 v3）
- `auto` → 读 yaml `studio.homepage.v2_bento.percent`（0–100）按桶 redirect

**yaml 示例**（合并到 `config.yaml`）：[`config-holdback.example.yaml`](./config-holdback.example.yaml)

> redirect 实现落在 M20-i；M20-a–h 阶段 `/` 与 `/v2` 均直达、互不影响。

---

## 4. v3 共存护栏（工程 CI）

1. **默认分支保护**：`main` 上 v3 路径集成测试 **必须** green（`tests/test_studio_p8_regression.py` 等）。
2. **`/` 零回归**：v2 开发期 **不得**改动 `studio.js` 行为；仅当修复 v2 共享模块导致的明确 bug 时才动共享文件，并 **同时** 跑 v3 回归。
3. **Storage 形状**：v2 仅 **新增** `homepageVariant`；不改 `activeJobId` / `activePending` schema。
4. **Import 跨页**：两页共享 `sessionStorage.activeJobId`；v2 必须 `resumeActiveJobIfAny`（M20-g 完整接入），且 Importing 中不闪 Idle。
5. **回滚演练**（M20-i）：v2 写入新键 → 停 redirect 回 v3 → 验证 Import 续 poll、书架、FirstSuccess。
6. **Bundle 隔离**：v2 资源仅由 `/v2` 加载，v3 路径 **不**加载任何 v2 chunk（LCP 护栏）。

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

- [x] `GET /` off 模式仍 v3（gate e2e）
- [x] `GET /v2` 200 且加载 v2 视图层
- [x] Importing 中跨页不切换 variant（AC-HP2-23）
- [x] holdback 分桶稳定（gate 单测 + `bucket.test.mjs` + 10% e2e）
- [x] 回滚（停 redirect）后 v3 忽略 `homepageVariant` 键不报错（Playwright AC-HP2-23）
