# Travelogue Studio · 旧首页（v3）退役与 v2 唯一入口 · 产品需求文档（PRD · M21）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | v0.1.0-M21 |
| **状态** | **Draft · 待评审** |
| **模块代号** | **M21 · Homepage v3 Retirement（v2 Cutover）** |
| **前置条件** | M20 首页 v2 Bento 已可 dogfood（`GET /v2`）；M20-j 门控与 `/classic` 回滚路由已实现；高级分析选项已迁入 v2 工作台（Popover） |
| **交付形态** | 分阶段将 **`GET /` 定为唯一用户首页（v2）**；补齐 v2 **浏览器上传**；**长期保留 `/classic` 作为应急入口（deprecated）**；最终按“两步法”退役 v3 文件 |
| **关联文档** | [PRD-STUDIO-HOMEPAGE-v2.md](./PRD-STUDIO-HOMEPAGE-v2.md) · [PRD-STUDIO-HOMEPAGE.md](./PRD-STUDIO-HOMEPAGE.md)（v3 基线）· [studio-homepage-v2/FEATURE-FLAG.md](./studio-homepage-v2/FEATURE-FLAG.md) · [studio-homepage-v2/EDITOR-LINKS-M20J.md](./studio-homepage-v2/EDITOR-LINKS-M20J.md) · [studio-homepage-v2/RUNBOOK-HOLDBACK.md](./studio-homepage-v2/RUNBOOK-HOLDBACK.md) · [studio-homepage-v2/SIGNOFF-M20J.md](./studio-homepage-v2/SIGNOFF-M20J.md) · [PRD-PHASE3.md](./PRD-PHASE3.md) §6.4（高级分析选项） |
| **更新日期** | 2026-06-03 |

> **定位说明**
>
> - 本 PRD **不**重复描述 v2 Bento 首页功能（见 [PRD-STUDIO-HOMEPAGE-v2.md](./PRD-STUDIO-HOMEPAGE-v2.md)）。
> - 本 PRD 定义：**如何稳妥退役 v3 影像优先首页**（`studio.html` + `studio.js`），使 v2 成为唯一主入口，且 **不破坏** 导入、预览、长图、配置 API 等已有能力。
> - 实施原则：**先切流量、再补缺口、再删文件**；任何阶段均可通过 `/classic` + `TRAVELOGUE_STUDIO_HOMEPAGE_V2=off` 回滚。

---

## 1. 背景与问题陈述

### 1.1 当前双首页现状

| 路由 | 模板 | 入口 JS | 默认（`TRAVELOGUE_STUDIO_HOMEPAGE_V2=off`） |
|------|------|---------|-------------------------------------------|
| `GET /` | 门控：`studio-home-v2.html` 或 `studio.html` | — | **v3** |
| `GET /v2` | `studio-home-v2.html` | `homepage-v2/bootstrap.js` | v2 |
| `GET /classic` | `studio.html` | `studio.js` | v3（M20-j 已预留） |

工程上 v2 与 v3 **共用** `/__travelogue/*` API 与 `templates/studio/js/` 下大量共享模块（`constants` · `http` · `job-poll` · `advanced` · `analytics` 等）。**退役的是 v3 视图层，不是 Studio 服务端。**

### 1.2 为何要退役 v3

| 问题 | 说明 |
|------|------|
| **双轨维护成本高** | 同一能力（导入、高级选项、回访）需在两套 DOM/状态机上对齐 |
| **用户入口分裂** | `/` 与 `/v2`、holdback 302 增加支持与文档负担 |
| **v2 已覆盖主路径** | Bento 双交付、Import Sheet、书架、FirstSuccess、高级选项 Popover 已落地 |
| **产品方向已冻结** | [PRD-STUDIO-HOMEPAGE-v2.md](./PRD-STUDIO-HOMEPAGE-v2.md) 为输出优先范式；v3 PRD 标记为 Implemented · 归档 |

### 1.3 退役前必须补齐的缺口（共识）

对照 [PRD-STUDIO-HOMEPAGE.md](./PRD-STUDIO-HOMEPAGE.md) v3 已落地能力与 v2 现状：

| v3 能力 | v2 现状 | M21 处置 |
|---------|---------|----------|
| **本机 pick-folder** | Import Sheet 主按钮 ✅ | 保持 |
| **路径粘贴导入** | Sheet `details` 内 ✅ | 保持 |
| **浏览器上传（≤200MB）** | ❌ 无 `album-upload` | **M21-0 · 必做** |
| **高级 · 分析选项** | 工作台 Popover ✅ | 保持 |
| **最近路径记忆**（`LS.recentPaths`） | 无列表，仅手输路径 | **M21-1 · 建议** |
| **Coach 引导** | 无 | **非 M21**（可后置） |
| **回访样张画廊滚动** | Bento + 书架替代 | **非 M21**（交互差异接受） |
| **sessionStorage 导入续跑** | `import-run.js` 对齐 ✅ | 保持 |

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 | 验收 |
|----|------|------|
| **G-M21-01** | 普通用户访问 `http://127.0.0.1:8766/` **仅**看到 v2 Bento 首页 | `GET /` 200 + `data-homepage-variant="v2"` |
| **G-M21-02** | 预览/编辑器「返回首页」仍指向 v2 | `preview-toolbar` `href="/"` 无需改链（见 EDITOR-LINKS-M20J） |
| **G-M21-03** | v2 支持 **浏览器小文件夹上传**（与 v3 同等约束） | Sheet 内可完成 upload → import_success |
| **G-M21-04** | 任意阶段 **≤5 分钟** 可回滚至 v3 | `off` + `/classic` 文档化演练 |
| **G-M21-05** | 物理删除 v3 后 CI 仍绿 | 见 §8 测试迁移 |

### 2.2 非目标（M21）

- 手机浏览器 / LAN 访问 Studio 完整支持（仍归 §11.3 Unsupported + 小程序）
- 重写 v3 影像优先 Hero 或合并两套 CSS 为单文件
- 修改游记预览页 `/{tripId}/index.html` 渲染逻辑
- 变更 `sessionStorage` 既有键名（`activeJobId` / `activePending`）
- 删除 `/__travelogue/import` 等 API 行为
- Coach 引导、v3 样张 SVG 画廊 1:1 复刻（除非单独立项）

---

## 3. 分阶段实施计划（冻结 · 稳妥路径）

```text
M21-0  缺口补齐（浏览器上传）         ← 可与 M21-a 并行，但切主站前必须完成
M21-a  切主站（配置 / 默认 on）         ← 不删文件；/v2 暂保留 200 兼容
M21-b  稳定观察（dogfood）             ← 观察期内收集回滚信号与上传数据
M21-c  URL 收敛（/v2 → /） + 清理       ← dev 链、文档、telemetry variant
M21-d  测试与 CI 迁移                  ← 静态断言改 v2
M21-e1 v3 冻结只读（保留 /classic）      ← 一版观察，不再演进
M21-e2 物理退役（删 v3 文件）           ← 观察通过后执行
```

### 3.1 阶段 M21-0 · v2 浏览器上传（P0 · 切主站阻塞项）

**用户故事**：无法在访达/资源管理器选文件夹时，可在 Import Sheet 内用浏览器选择**小文件夹**试做游记（与 v3 一致）。

**UI 位置**（建议，可微调）：

- Import Sheet · `其他导入方式` 折叠块内，与「粘贴路径」并列；
- 文案继承 v3：**「小文件夹试用（≤200MB）」**；
- `data-entry-tier="tertiary"`；主路径仍为 pick-folder。

**行为契约**（复用 v3 实现，禁止重写业务逻辑）：

| 项 | 要求 |
|----|------|
| 实现复用 | `templates/studio/js/import-flow.js` 之 `uploadAndImport` / `confirmLargeUpload` / `uploadAndImportCore` |
| v2 接入方式 | `import-sheet.js` 注册 `import-bridge` 或薄封装调用；**禁止** pick-folder 失败时静默降级上传 |
| 隐藏 input | `#album-upload` · `webkitdirectory` · `multiple` · `hidden` |
| 大小提示 | **≤200MB 为建议上限（非硬上限）**；超阈值弹确认（与 v3 `confirmLargeUpload` 一致） |
| 状态机 | 上传开始 → `V2.state = Importing` · `trackStudioEvent("import_start", { via: "upload" })` |
| 失败 | 复用 `errors.js` 文案；Sheet 内 `v2-sheet-error` 展示 |
| 与 pick-folder 互斥 | 同一会话仅一种来源；确认后禁用另一入口直至关闭 Sheet |

**文案规范（M21-0 冻结）**：

- 入口文案：`小文件夹试用（建议 ≤200MB）`
- 提示文案：`超过建议大小可能变慢或失败，仍可继续尝试`

**验收（AC-M21-0）**：

| ID | 场景 | 通过标准 |
|----|------|----------|
| AC-M21-0-01 | 选择 <50MB 文件夹上传 | `import_success` · 预览 URL 可打开 |
| AC-M21-0-02 | 取消超大上传确认 | 不发起 import · Sheet 可继续操作 |
| AC-M21-0-03 | Importing 中打开 Sheet | toast「正在制作中」· 与 pick-folder 一致 |
| AC-M21-0-04 | 刷新后续 poll | `sessionStorage.activeJobId` 恢复 Importing（跨 `/` 与 `/v2`） |

### 3.2 阶段 M21-a · 切主站（不删文件）

**配置**（见 [FEATURE-FLAG.md](./studio-homepage-v2/FEATURE-FLAG.md) §3）：

| 环境 | `TRAVELOGUE_STUDIO_HOMEPAGE_V2` | `GET /` 行为 |
|------|--------------------------------|--------------|
| 本地 dev | `on`（或文档约定默认 on） | 直接 serve `studio-home-v2.html` |
| dogfood / 生产 | `on` | 同上 |
| 紧急回滚 | `off` | 冻结 classic @ `/`；v2 仍可通过 `/v2` |

**代码默认值（建议）**：

- `studio_homepage_gate.resolve_mode()` 默认由 `off` 改为 `on`（或 `config.yaml` `studio.homepage.v2_bento.default: on`）；
- **保留** `auto` + percent 供历史 holdback 脚本，但 M21 完成后 holdback 退出。

**验收（AC-M21-a）**：

| ID | 场景 | 通过标准 |
|----|------|----------|
| AC-M21-a-01 | `GET /` | 200 · 含 `studio-home-v2.css` · 无 `data-studio-v="4"` |
| AC-M21-a-02 | `GET /classic` | 200 · v3 标记仍在 |
| AC-M21-a-03 | 预览页返回首页 | 进入 v2 Bento |
| AC-M21-a-04 | 回滚演练 | `off` 后 `/` 恢复 v3（[RUNBOOK-HOLDBACK.md](./studio-homepage-v2/RUNBOOK-HOLDBACK.md)） |

### 3.3 阶段 M21-b · 稳定观察（dogfood）

| 目标 | 说明 |
|------|------|
| 稳定性观察 | M21-a 后至少 7 天，确认无 P0 且上传漏斗稳定 |
| 回滚演练 | 至少 1 次 `on -> off` 回滚实操（含恢复验证） |
| 指标阈值 | `import_success/import_start`、上传失败率、首页错误率达标 |

### 3.4 阶段 M21-c · URL 收敛 + 开发面与观测清理

| 项 | 动作 |
|----|------|
| `GET /v2` | **302 → `/`**（在 M21-a 观察稳定后执行） |
| 文档 / README | 启动 Studio 提示 `http://127.0.0.1:8766/` 而非 `/v2` |
| `scripts/studio_lcp_measure.py` | 主路径改为 `/`；v3 对比项删除或仅 `/classic` |
| v2 dev panel「经典首页 → /」 | 改为「经典首页 → /classic」或仅 `off` 模式显示 |
| `variant-guard.js` | Importing 仍禁止误切；去掉「拦截进 v3」的 toast 逻辑（若已无 v3 入口） |
| `experiment_exposure` | 统一 `variant: "v2"`；holdback 对照组事件下线 |
| PRD 元数据 | 更新 [PRD-STUDIO-HOMEPAGE-v2.md](./PRD-STUDIO-HOMEPAGE-v2.md) 路由表为 `GET /` → v2 |

**验收**：旧书签 `/v2` 最终落在 v2 首页且地址栏可为 `/`（若采用 302）。

### 3.5 阶段 M21-d · 测试与 CI 迁移

**原则**：静态 DOM/JS 断言从 `studio.html` / `read_studio_js()` **迁移**到 `studio-home-v2.html` + `homepage-v2/**`，或改为 e2e 只测 `/`。

| 测试文件 | M21 动作 |
|----------|----------|
| `test_studio_home_v2.py` | 扩展为默认 `/` 断言；gate `off` 仅保留回滚用例 |
| `test_studio_p8_regression.py` | 五态/三入口 → 映射 v2 等价 DOM（Sheet · shelf · importing overlay）或标为 v3-legacy 仅 `/classic` |
| `test_studio_a11y_p4.py` · `test_studio_phase5_tier0.py` | 同上 |
| `test_studio_ux_p3.py` | 高级选项 v2 已有；v3 HTML 断言保留至 M21-e |
| `test_studio_lcp_playwright.py` | 仅测 `/` v2 P95 |

**新增建议**：`test_studio_home_v2_browser_upload.py`（或并入 import sheet 测试）覆盖 AC-M21-0。

### 3.6 阶段 M21-e1 · v3 冻结只读（先冻结一版）

**动作**：

- `studio.html` / `studio.js` / `studio.css` 进入 `deprecated` 冻结态，不再新增功能；
- `/classic` 持续可用，作为长期应急入口；
- 保留最小 smoke（首页可打开、可发起导入、可进入预览）。

**进入 M21-e2 前提**：

- 至少一个发布版本观察窗口通过；
- 无需使用 `/classic` 承载常规流程；
- M21-d 测试迁移完成且 CI 稳定。

### 3.7 阶段 M21-e2 · 物理退役（最后执行）

**可删除**（需 M21-d 测试已迁移 + 一个发布周期无回滚需求）：

| 路径 | 说明 |
|------|------|
| `templates/studio/studio.html` | v3 首页 DOM |
| `templates/studio/studio.js` | v3 入口 |
| `templates/studio/studio.css` | v3 首页样式（确认 preview 不依赖） |
| `js/navigation.js` · `render.js` · `sheet.js` · `samples.js` · `init.js` · `viewport.js` | 仅 v3 首页编排（删前全库 `grep`） |

**须保留**（即使 M21-e 完成）：

| 路径 | 原因 |
|------|------|
| `templates/studio/js/import-flow.js` | M21-0 上传 + 潜在 CLI 复用 |
| `js/advanced.js` · `constants.js` · `http.js` · `job-poll.js` 等 | v2 + preview 共用 |
| `studio-toast.js` · `studio-modal.js` · `preview-toolbar.js` | 预览与 v2 |
| `homepage-v2/**` | v2 视图层 |

**`/classic` 处置（冻结）**：

- **长期保留应急入口**：保留最后一版 `studio.html` 快照仅服务 `/classic`，标记 `deprecated`，不再演进；
- 维护责任：只保障“可打开首页、可发起导入、可进入预览”的最小 smoke。

**门控简化**（M21-e 后可选）：

- `handle_home_root` 固定 `studio-home-v2.html`；
- 删除 `should_redirect_root_to_v2` 与 holdback 分桶（或仅保留 telemetry bucket）。

---

## 4. 不受影响的能力清单（回归必测）

以下能力 **不依赖** v3 首页入口，M21 各阶段均需 smoke：

| 域 | 验证点 |
|----|--------|
| **导入 API** | `POST /__travelogue/import` · pick-folder · cancel · busy retry |
| **Job** | 四阶段 poll · `sessionStorage` 续跑 |
| **配置** | `GET/PATCH /__travelogue/config` · 高级选项四项 |
| **画册** | `GET /trips` · 删除 · 书架 longshot（M14） |
| **预览** | `/{tripId}/index.html` + toolbar · 返回 `/` |
| **长图 Job** | `POST /__travelogue/longshot` |
| **Demo** | `demo-showcase/manifest.json` · Bento 示例 Tab |

---

## 5. 路由与门控目标态（M21 完成后）

```text
GET /              → studio-home-v2.html（唯一主入口）
GET /v2            → 302 /（在 M21-c 执行收敛）
GET /classic       → legacy-freeze/studio.classic.html（长期保留 · deprecated · 应急入口）
GET /{tripId}/...  → 不变
/__studio/*        → 不变（v2 CSS/JS + preview-toolbar + 共享 js）
/__travelogue/*    → 不变
```

**环境变量目标默认**：

```bash
TRAVELOGUE_STUDIO_HOMEPAGE_V2=on   # 主路径
# off 仅用于事故回滚；不再用于日常 dev
```

---

## 6. 依赖与协作

| 角色 | 交付 |
|------|------|
| **前端** | M21-0 上传 · M21-b/c · M21-d 测试 |
| **后端** | 无 API 变更（除非上传边界需新错误码）；维护 `/classic` 最小可用路由 |
| **QA** | §4 回归矩阵 · AC-M21-0 · 回滚演练 |
| **PM** | 确认非目标（Coach、画廊）· 观察期放行 M21-e2 |
| **设计** | Sheet 内上传入口视觉（对齐 v2 ghost/tertiary 层级） |

---

## 7. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 上传实现分叉 | v2/v3 行为不一致 | **强制**复用 `import-flow.js` |
| 删文件过早 | CI 大面积红 / 回滚失效 | 采用 **M21-e1 冻结一版 + M21-e2 删除** 两步法 |
| 用户书签 `/v2` | 404 或困惑 | M21-c 执行 302 收敛 |
| holdback 对照组遗留 | 指标口径混乱 | M21-c 下线 v3 exposure |
| `studio.css` 误删 | 预览样式破坏 | 删前 `grep` preview 引用 |

---

## 8. 验收总表（Sign-off 前）

| 阶段 | 签字项 | 自动验证 |
|------|--------|----------|
| M21-0 | 浏览器上传 4 条 AC | 新增 pytest + 可选 Playwright |
| M21-a | 切主站 + 回滚演练 | `test_studio_home_gate_on_serves_v2_at_root` 为默认 |
| M21-b | 稳定观察 | 指标看板 + 回滚演练记录 |
| M21-c | `/v2` 重定向 + dev/telemetry 清理 | e2e + 人工 |
| M21-d | CI 全绿 | `pytest tests/test_studio_home*.py` + P8 迁移 |
| M21-e1 | v3 冻结只读 + `/classic` 最小 smoke | nightly smoke |
| M21-e2 | 仓库无 v3 主路径引用（如执行删除） | `grep studio.html` + 发版说明 |

---

## 9. 排期建议（工程估算）

| 阶段 | 估时 | 依赖 |
|------|------|------|
| M21-0 浏览器上传 | 1–2 人日 | — |
| M21-a 切主站 | 0.5 人日 | M21-0 |
| M21-b 稳定观察 | 7 天自然观察 | M21-a |
| M21-c URL 收敛 + 清理 | 0.5–1 人日 | M21-b |
| M21-d 测试迁移 | 1–2 人日 | M21-0～c |
| M21-e1 冻结只读 | 0.5 人日 | M21-d |
| M21-e2 物理删除 | 1 人日 | M21-e1 + 一版观察 |

**建议观察期**：M21-a 上线后 **≥7 天** dogfood，无 P0 再执行 M21-e。

---

## 10. 开放问题（评审关闭）

| ID | 问题 | 建议 | Owner |
|----|------|------|-------|
| OQ-M21-01 | `/classic` 是否长期保留 | **已决议：长期保留（deprecated）** | PM/工程 |
| OQ-M21-02 | 最近路径列表是否纳入 M21-1 | 切主站后迭代 | PM |
| OQ-M21-03 | 默认 `on` 是否进 `config.yaml` 示例 | 与 [config-holdback.example.yaml](./studio-homepage-v2/config-holdback.example.yaml) 合并 | 工程 |
| OQ-M21-04 | `/v2` 302 时点 | **已决议：M21-c 执行（非 M21-a 同步）** | 工程 |

---

## 11. 文档修订记录

| 版本 | 日期 | 摘要 |
|------|------|------|
| v0.1.0-M21 | 2026-06-03 | 初稿：分阶段退役 v3 · M21-0 浏览器上传 · 路由目标态 · AC/风险/排期 |
| v0.1.1-M21 | 2026-06-03 | 决议固化：`/classic` 长期保留；`/v2` 在 M21-c 后 302；200MB 改建议上限；M21-e 拆为冻结一版再删除 |
| v0.1.2-M21 | 2026-06-03 | 补充现状评估：当前功能验证结论与遗留工作清单 |
| v0.1.3-M21 | 2026-06-03 | 方案 2 落地：移除 `full` 回滚分支并执行 v3 物理删除（保留 `/classic` 冻结应急入口） |

---

## 12. 当前评估（2026-06-03）

### 12.1 首页功能现状（评估结论）

| 维度 | 结果 | 证据 |
|------|------|------|
| v2 主入口可用性 | ✅ 正常 | `pytest tests/test_studio_home_v2.py -q` → **33 passed, 1 skipped** |
| 门控与安全 | ✅ 正常 | `pytest tests/test_studio_homepage_gate.py tests/test_studio_homepage_gate_security.py -q` → **23 passed** |
| AC Playwright | ✅ 正常 | `pytest tests/test_studio_home_v2_ac_playwright.py -q` → **35 passed** |
| 回滚语义 | ✅ 已收敛 | `off` 统一回退到冻结 classic（无 `full` 分支） |
| `/classic` 应急入口 | ✅ 正常 | `/classic` 固定走 `legacy-freeze/studio.classic.html`，nightly 保留 smoke |

### 12.2 发现的问题（需处理）

1. **M21-e2 发布门禁待收口（P0）**  
   `python scripts/studio_m21e2_preflight.py --observed-release --json` 已返回：`ready=true`；  
   当前待完成项为远端 CI 与发布签字流程。

> 已处置（2026-06-03）：  
> - 运行时 `studio.html` 引用已移除，preflight `runtime_blockers=0`。  
> - `test_m20j_holdback_control_experiment_exposure` 已改为 legacy 语义（默认不要求 v3 exposure），并完成 Playwright 回归（35 passed）。

### 12.3 移除旧首页遗留工作（按优先级）

| 优先级 | 遗留项 | 完成标准 |
|--------|--------|----------|
| P0 | 完成 M21-b/M21-e1 观察窗口 | 至少一个发布版本、无 P0/P1、nightly 稳定 |
| P0 | 远端门禁收口 | 远端 CI 全绿、nightly 无新增波动、发布说明完成 |
| P1 | 完成 telemetry 收口 | 文档与查询口径统一到 `/` + v2 主路径，明确 `/classic` 仅应急 |
| P1 | M21-d 门禁收尾 | 将本地回归结果与远端流水线记录对齐归档 |
| P2 | e2 删除后清理 | legacy 测试/文档引用分批清理，完成发布说明与回滚卡更新 |

### 12.4 Go / No-Go 建议

- **当前建议：Go（可进入发布收尾）**  
  原因：e2 技术门禁（preflight + 本地回归）已满足，旧首页物理删除已完成。  
- **可继续推进：M21-d 发布收尾**  
  建议完成远端 CI、nightly 观察与发布说明后签字关闭。

---

## 附录 A · 与现有里程碑对照

| 原里程碑 | M21 关系 |
|----------|----------|
| M20-j 切主站 | M21-a **落实**默认 on + 签字项 |
| M20-i holdback | M21-c **下线**或冻结为历史 |
| PRD-STUDIO-HOMEPAGE v3 | M21-e 后改状态为 **Archived** |
| PRD-STUDIO-HOMEPAGE-v2 | M21 完成后更新 §路由与 §0 状态为 **Implemented · 唯一入口** |

## 附录 B · 关键代码索引（实施时）

|  Concern | 文件 |
|----------|------|
| 根路由门控 | `travelogue/web/studio_handlers/static_handlers.py` · `studio_homepage_gate.py` |
| 路由表 | `travelogue/web/studio_routes.py` · `paths.py` |
| v2 入口 | `templates/studio/homepage-v2/bootstrap.js` |
| v2 Import Sheet | `templates/studio/homepage-v2/import-sheet.js` |
| 上传逻辑（复用） | `templates/studio/js/import-flow.js` |
| v3 入口（已删除） | `templates/studio/studio.js` · `studio.html` |
| 返回首页链 | `templates/studio/preview-toolbar.js` |
