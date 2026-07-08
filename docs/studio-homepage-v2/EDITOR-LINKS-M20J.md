# M20-j · Editor / 预览页「返回首页」链评估

> P2-17 · FEATURE-FLAG §1：切主站后 editor 内 `href="/"` **暂不改** — 本文记录评估结论与例外。

---

## 1. 现状盘点

| 位置 | 链接 | 切主站 (`on`) 后落点 |
|------|------|----------------------|
| `templates/studio/studio.html` topbar | `href="/"` | **v2 首页** ✓ |
| `templates/studio/preview-toolbar.js` | `href="/"` ×4 | **v2 首页** ✓ |
| `templates/visual-journal/partials/*.hbs` | `href="/"` | **v2 首页** ✓ |
| `trips/*/index*.html`（已发布 trip） | `href="/"` | **v2 首页** ✓ |
| `studio-home-v2.html` topbar | `href="/"`（经典首页） | loopback dev → classic @ `/`；生产 `on` 时仍可用 `/classic` |

---

## 2. 决策（冻结）

| 问题 | 结论 |
|------|------|
| M20-j 是否批量改 editor `href="/"` → `/classic`？ | **否**。`on` 模式下 `/` 即 v2，用户期望「返回首页」= 新 Bento 首页。 |
| 是否需要 classic 永久入口？ | **是**。`GET /classic`（已实现）；v2 topbar「经典首页」仅 loopback 显示。 |
| 预览页返回是否应区分 variant？ | **否**。统一 `/`；holdback 对照组用户从 editor 返回仍进 classic 仅当 gate 将其留在 classic 且 **未** 从 editor 导航（editor 链不受 session 分桶影响，始终 `/`）。 |

**Holdback 注意**：对照组用户若从 `/` 进 classic，从 trip editor 点「返回首页」会到 `/` → 仍 classic（gate 不重定向 editor 内导航）。进组用户 editor 返回 → v2。符合 A/B 意图。

---

## 3. 未来可选（非 M20-j）

- 设置页增加「默认首页：经典 / Bento」用户偏好（需产品立项）。
- 桌面壳 WebView 深链统一 `/`（见 OQ-WEBVIEW）。

---

## 4. 验收

- [x] `GET /classic` e2e（`test_studio_home_gate_classic_serves_v3`）
- [x] `on` 模式 `GET /` serve v2（gate 单测 + e2e）
- [ ] PM 确认 editor 返回行为符合产品叙事（签字栏见 [SIGNOFF-M20J.md](./SIGNOFF-M20J.md)）
