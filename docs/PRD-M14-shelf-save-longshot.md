# Travelogue Studio · 书架「保存长图」产品需求文档（PRD · M14）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | v0.1.0-M14 |
| **状态** | Draft · 待评审 |
| **模块代号** | **M14 · Shelf Save Longshot** |
| **前置条件** | M13 书架 TripCardMenu 已落地（`shelf-menu.js`）；Phase 2 服务端长图 Job（`POST /__travelogue/longshot`）可用；首页 v2 书架区（M20-e）已接入 |
| **交付形态** | 书架卡片 `⋯` 菜单新增 **「保存长图」**；首页 Modal 进度与结果；默认 **纯照片 · 3×**；每次强制重新生成 |
| **关联文档** | [SHARING.md](./SHARING.md) · [PRD-STUDIO-HOMEPAGE-v2.md](./PRD-STUDIO-HOMEPAGE-v2.md) · [PRD-PHASE5.md](./PRD-PHASE5.md) §4.4 · [PRD-PHASE11-copy-optimization.md](./PRD-PHASE11-copy-optimization.md) · [studio-homepage-v2/DATA-CONTRACT.md](./studio-homepage-v2/DATA-CONTRACT.md) · [wireframes/studio-shelf-trip-menu-v1.html](./wireframes/studio-shelf-trip-menu-v1.html) · [adr/005-longshot-server-side.md](./adr/005-longshot-server-side.md) |
| **更新日期** | 2026-06-03 |

> **定位说明**
>
> - 本 PRD 是 **M13 菜单的增量**：在「删除画册」之上增加 **路径 A（微信群长图）** 的快捷出口。
> - 不改变 [SHARING.md](./SHARING.md) 双轨策略：书架入口仍交付 **PNG 长图**，非 HTML 链接、非小程序鉴权。
> - 与预览页工具栏「保存长图」**刻意区分默认参数**，服务「发微信图为主」vs「编辑验货带文案」两种意图。

---

## 1. 背景与问题陈述

### 1.1 当前问题

| 问题 | 现状 | 影响 |
|------|------|------|
| **导出入口深** | 保存长图主入口在预览页工具栏；书架 stale 时仅「更新长图」→ 跳转 `?focus=longshot` | 80% 分享者需 **先进预览再导出**，路径长 |
| **默认参数不匹配发群场景** | 预览页默认 **2× + 完整文案** | 微信群更常要 **高清纯图**，用户需手动切纯照片 / 3× |
| **菜单能力单一** | M13 菜单仅「删除画册」 | 封面区 `⋯` 未承担「交付物出口」职责 |
| **API 缺文案模式** | `POST /__travelogue/longshot` 仅 `tripId / scale / format` | 无法在 **不改 trip.json** 的前提下按次指定 photos 模式 |

### 1.2 用户诉求

1. 在 Studio **首页书架** 上对某本画册 **一键保存长图**；
2. 默认 **不含叙事文案**（纯照片），适合直接发微信；
3. 默认 **3× 高清**；
4. 每次点击 **重新生成**（不依赖 stale 跳过）；
5. 进度可见，完成后 **在文件夹中显示** PNG。

### 1.3 产品共识

> 书架「保存长图」= **路径 A 的快捷出口**，参数预设为「发微信图」；
> 预览页「保存长图」= **编辑验货出口**，保留杂志感完整文案与 2× 默认。
>
> 两者共用同一 Job 管线，**不**混用隐私假设（长图仍由用户自行发送，不做访问控制）。

---

## 2. 目标与非目标

### 2.1 产品目标

| ID | 目标 | 衡量方式 |
|----|------|----------|
| **G-M14-01** | 书架卡片菜单可触发长图导出 | 菜单项可见 · 点击后 Modal 进度 |
| **G-M14-02** | 默认纯照片 · 3× | API 请求体与成功 Modal 副文案一致 |
| **G-M14-03** | 每次强制重新生成 | 不读 `longshotStale` 跳过逻辑 |
| **G-M14-04** | 完成后可 reveal + 清 stale 徽章 | `V2.reroute()` · `longshotStale` 更新 |
| **G-M14-05** | 与预览页导出行为一致（分段 / P1 / 20MB） | 复用 `export_trip_longshot` · AC 对齐 AC-P2-02 |
| **G-M14-06** | photos 模式语义无回归 | 对齐 `copy-display.css` · decorLine 隐藏（AC-P11-04） |

### 2.2 非目标

- **不做** 真「一键发到微信好友」（无此类 Web API；见 [SHARING.md](./SHARING.md) §2）；
- **不做** 书架菜单导出 HTML 链接 / zip（zip 仍仅在预览高级菜单）；
- **不改** `trip.json` 的 `export.copyDisplay` 持久值；
- **不做** 书架内 scale / 文案模式选择 UI（v1 固定预设；v1.1 可开放）；
- **不做** Mobile Studio Web / 小程序内本菜单（归各自 PRD）；
- **不做** 批量导出多本画册。

---

## 3. 已拍板决策（D-M14）

| ID | 决策 | 结论 |
|----|------|------|
| **D-M14-01** | 菜单文案 | **保存长图** |
| **D-M14-02** | 进度 UI | **Modal**（进行中 / 成功 / 失败） |
| **D-M14-03** | stale 策略 | **每次强制重新生成** |
| **D-M14-04** | 文案模式 | **`copyDisplay: "photos"`**（现有 photos 语义） |
| **D-M14-05** | 清晰度 | **`scale: 3`** |
| **D-M14-06** | photos 边界 | **方案 A**：沿用现有 photos 模式；**可能保留**章分隔标题、封面叠字等 |
| **D-M14-07** | 持久化 | capture 前 **DOM 注入**，**不写** `trip.json` |
| **D-M14-08** | 双入口差异 | 书架 3×+photos · 预览 2×+full（现状） |
| **D-M14-09** | 示例画册 | **允许**保存长图 · **仅**删除 disabled |
| **D-M14-10** | 后端扩展 | `POST /__travelogue/longshot` 增加可选 **`copyDisplay`** |

---

## 4. 用户故事与主路径

### 4.1 用户故事

**作为** 微信群分享者，**我想** 在 Studio 首页书架上对某本画册点「保存长图」，**以便** 拿到纯照片 3× PNG 并自行发到微信，**而不必** 先打开预览页。

### 4.2 主路径（Happy Path）

```
首页书架 · 悬停/聚焦卡片封面
  → 点击 ⋯
  → 点击「保存长图」
  → Modal：正在保存长图 · 纯照片 · 3× 高清
  → POST /__travelogue/longshot { tripId, scale:3, format:"png", copyDisplay:"photos" }
  → 轮询 GET /__travelogue/status?jobId=
  → Modal：长图已保存 · [在文件夹中显示] [关闭]
  → V2.reroute() · 卡片「长图待更新」消失
  → 用户拖 PNG 进微信
```

### 4.3 与现有入口关系

| 入口 | copyDisplay | scale | 跳转预览 | 用途 |
|------|-------------|-------|----------|------|
| **书架 ⋯ · 保存长图（M14）** | `photos` | **3** | 否 | 发微信 · 纯图高清 |
| **预览工具栏 · 保存长图** | `full` | **2** | — | 编辑验货 · 杂志文案 |
| **Resume · 更新长图** | — | — | 是 `?focus=longshot` | 先看再导（保留） |

---

## 5. 功能规格

### 5.1 菜单（M13 扩展）

**挂载点**：`attachShelfTripMenu()` · `surface`: `grid` | `resume`（与删除一致）。

**菜单结构（冻结 v1）**：

```
⋯ 更多操作
├── 保存长图          ← 新增 · 常规样式 · role="menuitem"
└── 删除画册          ← 已有 · danger · 置底
```

| 项 | 规则 |
|----|------|
| 点击菜单项 | 关闭菜单 · `stopPropagation` |
| 示例画册 | 「保存长图」**enabled** · 「删除画册」disabled |
| 导入进行中 | v1 **不** disabled 保存长图（若 Job 409 再 Toast）；v1.1 可 disabled |
| 键盘 | ↑↓ 移动 · Enter 选中 · Esc 关菜单（继承 M13） |

### 5.2 Modal · 进行中

| 字段 | 文案 |
|------|------|
| 标题 | 正在保存长图 |
| 画册名 | 「{title}」 |
| 副标题 | 纯照片 · 3× 高清 |
| 进度 | `{job.stageHint}`（如「正在合成长图…」） |
| 慢提示 | >45s：「比预期久一些，请耐心等待…」 |
| 按钮 | **关闭**（v1：关 Modal **不取消** 后台 Job；完成后 Toast「长图已保存」） |

### 5.3 Modal · 成功

| 字段 | 文案 |
|------|------|
| 标题 | 长图已保存 |
| 副标题 | 本次：纯照片 · 3× |
| 文件列表 | `job.result.outputs[]` 相对路径 |
| 分段提示 | `userHint` 或默认：「已按章导出 N 张…便于按序发微信」 |
| P1 兼容 | 「已使用兼容模式导出，与预览可能有细微差异。」 |
| 主按钮 | **在文件夹中显示** → `POST /__travelogue/reveal` |
| 次按钮 | **关闭** |

### 5.4 Modal · 失败

| 字段 | 文案 |
|------|------|
| 标题 | 无法保存长图 |
| 正文 | `{job.error.message}` 或「导出失败，请重试」 |
| 按钮 | **关闭** |

### 5.5 Toast（补充）

| 场景 | 文案 |
|------|------|
| 409 busy | 已有长图任务进行中，请稍候 |
| 关 Modal 后 Job 成功 | 长图已保存（可选 · v1.1） |
| reveal 失败 | 无法打开文件夹 |

---

## 6. 纯照片模式（copyDisplay: photos）

### 6.1 语义（D-M14-06 · 方案 A）

对齐 [copy_display.py](../travelogue/render/copy_display.py) 与 [copy-display.css](../templates/visual-journal/copy-display.css) 现有 **photos** 模式：

**隐藏**（capture 前 DOM 注入 `data-photos-only="on"` + `data-copy-display="photos"`）：

- hook、导语（chapter-lead）、epilogue、screen 文案块
- 图注、overlay 文案
- **`decorLine`**（Phase 11 · AC-P11-04；实现时补 CSS 选择器若缺失）

**可能仍显示**（预期 · 非 bug）：

- 章分隔标题（`.chapter-separator__title`）
- 封面叠字（若非 `cover-hero--photo-only`）
- 页码水印（分段导出 footer）

### 6.2 与 trip.json 的关系

| 操作 | 是否发生 |
|------|----------|
| 读 `export.copyDisplay` | 否（请求参数优先） |
| 写 `export.copyDisplay` | **否** |
| 改 HTML 源文件 | **否** |
| Playwright 页内注入 | **是** · 仅当次 capture |

---

## 7. API 与数据契约

### 7.1 请求 · `POST /__travelogue/longshot`

**书架入口（M14 冻结 body）**：

```json
{
  "tripId": "dongao",
  "scale": 3,
  "format": "png",
  "copyDisplay": "photos"
}
```

| 字段 | 类型 | 必填 | M14 默认 | 说明 |
|------|------|------|----------|------|
| `tripId` | string | ✓ | — | 画册 ID |
| `scale` | int | | **3** | 1–3 · 见 ADR-005 |
| `format` | string | | `png` | `png` \| `jpeg` |
| `copyDisplay` | string | | **`photos`** | `full` \| `photos` · **M14 新增** |

**预览入口（不变）**：不传 `copyDisplay` 或 `full` · `scale: 2`。

### 7.2 响应

| 状态 |  body |
|------|------|
| 202 | `{ "ok": true, "jobId": "…" }` |
| 409 | `{ "error": "E_STUDIO_JOB_BUSY", "message": "已有长图任务进行中，请稍候" }` |
| 404 | trip 不存在 |

### 7.3 Job 结果（继承 Phase 2）

`job.result` 形状不变：

```json
{
  "tripId": "…",
  "outputs": ["东澳岛-longshot.png"],
  "captureMethod": "p0",
  "segmented": false,
  "pageCount": 1,
  "userHint": "…"
}
```

### 7.4 后端实现要点（D-M14-10）

在 `export_trip_longshot` · `page.goto` 之后、`capture` 之前：

```javascript
if (copyDisplay === 'photos') {
  document.documentElement.setAttribute('data-photos-only', 'on');
  document.documentElement.setAttribute('data-copy-display', 'photos');
}
```

可选：触发 `longshot.js` 内 caption 隐藏逻辑（与预览页纯照片 toggle 一致）。

### 7.5 首页 trips 列表

导出成功后客户端调用 `V2.reroute()` · 刷新 `longshotStale`（[DATA-CONTRACT §2.1](./studio-homepage-v2/DATA-CONTRACT.md)）。

---

## 8. 前端架构

### 8.1 模块拆分

| 模块 | 职责 |
|------|------|
| **`templates/studio/js/longshot-client.js`**（新建） | `runLongshotExport()` · 轮询 · `revealLongshotOutput()` · `LONGSHOT_PRESETS` |
| **`templates/studio/homepage-v2/shelf-menu.js`** | 菜单项 · 调 longshot-client · Modal 态机 |
| **`templates/studio/preview-toolbar.js`** | 改为 import longshot-client · preset `preview` |

**预设常量（冻结）**：

```javascript
export const LONGSHOT_PRESETS = {
  shelf: { scale: 3, copyDisplay: "photos", label: "纯照片 · 3×" },
  preview: { scale: 2, copyDisplay: "full", label: "完整文案 · 2×" },
};
```

### 8.2 Modal 实现

复用现有 **`studioModal`**（[studio-modal.js](../templates/studio/studio-modal.js)）· 与 M13 删除确认同栈。

v1 扩展需求：支持 **动态更新 body**（进度 `stageHint`）或 **替换为 progress Modal 专用 helper**（`studioModalProgress`）。

### 8.3 状态机

| 状态 | 进入 | 退出 |
|------|------|------|
| `menu-open` | 点击 ⋯ | Esc / 外部点击 / 选菜单项 |
| `longshot-modal-progress` | 点「保存长图」 | Job 终态 / 用户关 Modal |
| `longshot-modal-result` | Job succeeded / failed | 用户关闭 |
| `longshot-toast-busy` | 409 | 自动消失 |

---

## 9. 3× 高清 · 产品预期

| 维度 | 预期 |
|------|------|
| 耗时 | 通常 30–60s · Modal 慢提示阈值建议 **45s** |
| 分段概率 | **高于 2×**（高度 ×3 · 20MB 门控） |
| 输出宽度 | `428 × 3 = 1284px`（CAPTURE_WIDTH · ADR-005） |
| 微信体积 | 仍受 **≤20MB/张** 约束 · 超限自动按章或 jpeg 降级（服务端既有逻辑） |
| P1 fallback | 可能增多 · UI 必须展示兼容提示 |

---

## 10. Telemetry

扩展 [studio-homepage-v2/TELEMETRY.md](./studio-homepage-v2/TELEMETRY.md) ALLOWED 列表：

| 事件 | 触发 | 属性 |
|------|------|------|
| `shelf_longshot_start` | 点「保存长图」 | `trip_id`, `surface`, `scale`, `copy_display` |
| `shelf_longshot_success` | Job succeeded | `trip_id`, `segmented`, `capture_method`, `output_count` |
| `shelf_longshot_fail` | Job failed | `trip_id`, `error_code` |
| `shelf_longshot_reveal` | 点「在文件夹中显示」 | `trip_id` |
| `shelf_longshot_busy` | 409 | `trip_id` |
| `shelf_longshot_modal_dismiss` | 进行中关 Modal | `trip_id`, `job_status` |

---

## 11. 边界情况

| 场景 | 行为 |
|------|------|
| 全局 longshot Job 进行中 | 409 · Toast busy · 不叠第二 Modal |
| 无 `index-longshot.html` | Job failed · 「请先完成渲染」类文案 |
| 分段 N 张 | 列表 + userHint · reveal 第一张 |
| 删至 0 本 | 不适用（导出不删 trip） |
| grid / resume 同一 trip | 两处菜单行为一致 |
| Playwright 未安装 | Job failed · 与 preview 相同错误路径 |
| 用户连点两卡片 | 第二本 409 或排队 Toast |
| decorLine 未隐藏 | **阻塞发布** · 补 CSS 后验收 AC-P11-04 |

---

## 12. 验收标准

### 12.1 功能验收（AC-M14）

| ID | 验收项 | 方法 |
|----|--------|------|
| **AC-M14-01** | 书架 grid + resume 菜单含「保存长图」 | DOM / `test_studio_home_v2` |
| **AC-M14-02** | 点击后 Modal 进度 · 副标题「纯照片 · 3× 高清」 | 手测 / harness |
| **AC-M14-03** | API body 含 `scale:3`, `copyDisplay:"photos"` | 集成测试 mock handler |
| **AC-M14-04** | 成功后可 reveal · `longshotStale` 清除 | E2E / reroute |
| **AC-M14-05** | 409 显示 busy Toast | 并发 Job 测试 |
| **AC-M14-06** | 示例画册可导出 · 不可删 | 手测 |
| **AC-M14-07** | photos 导出无 hook/图注/decorLine | 快照或 DOM 断言 |
| **AC-M14-08** | 预览页仍为 2×+full · 无回归 | `test_longshot_*` |
| **AC-M14-09** | 分段 / P1 / 20MB 与 AC-P2-02 一致 | 复用 longshot 测试 |

### 12.2 非回归

- M13 删除流程不变
- `copy-toggle.js` 预览页切换不受影响
- `trip.json` 导出后 `export.copyDisplay` 不变

---

## 13. 实施计划

### 13.1 波次

| 波次 | 内容 | 依赖 |
|------|------|------|
| **W1** | 后端 `copyDisplay` + capture 注入 + handler 测试 | — |
| **W2** | `longshot-client.js` + preview-toolbar  refactor | W1 |
| **W3** | `shelf-menu.js` 菜单 + Modal + reroute | W2 |
| **W4** | decorLine CSS · telemetry · 线框更新 · AC | W3 |

### 13.2 主要改动文件

| 文件 | 变更 |
|------|------|
| `travelogue/web/studio_handlers/export_handlers.py` | 解析 `copyDisplay` |
| `travelogue/export/longshot.py` | URL 或 evaluate 注入 photos |
| `templates/visual-journal/copy-display.css` | decorLine 选择器（若缺） |
| `templates/studio/js/longshot-client.js` | **新建** |
| `templates/studio/homepage-v2/shelf-menu.js` | 菜单项 + Modal |
| `templates/studio/preview-toolbar.js` | 复用 client |
| `tests/test_studio_handlers_import_export.py` | copyDisplay 参数 |
| `tests/test_studio_home_v2.py` | 菜单文案断言 |
| `docs/wireframes/studio-shelf-trip-menu-v1.html` | 第二菜单项 + Modal 态 |

### 13.3 配套文档（实现期）

| 文档 | 说明 |
|------|------|
| `docs/IMPLEMENTATION-M14.md` | 任务拆解（可选 · 实现时创建） |
| `docs/ACCEPTANCE-M14.md` | QA 清单（可选 · 实现时创建） |

---

## 14. 明确不做（v1）

- 菜单内 scale / 文案二选一
- 取消进行中的 longshot Job
- 复制 PNG 到剪贴板
- 手机扫码传图（方案 C · 后续 PRD）
- 修改 Resume「更新长图」为同参数（保留跳转预览）

---

## 15. 开放问题（OQ-M14）

| ID | 问题 | 倾向 |
|----|------|------|
| **OQ-M14-01** | 进行中关 Modal 是否后台继续并 Toast？ | v1 **是**（简单） |
| **OQ-M14-02** | 导入进行中是否 disable 保存长图？ | v1 **否** · v1.1 再议 |
| **OQ-M14-03** | Resume「更新长图」是否改为同预设？ | v1 **保留跳转** |

---

## 16. 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0-M14 | 2026-06-03 | 初稿：菜单保存长图 · Modal · photos 3× · 强制重生成 · 方案 A |
