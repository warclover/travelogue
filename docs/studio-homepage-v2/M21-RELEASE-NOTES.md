# Studio 首页 M21 · 发版说明（模板）

> 复制到 GitHub Release / 内部 changelog。**M21-e2 已删除 full v3 入口文件**；应急页保留在 `/classic`。

---

## 摘要

- **主入口**：`http://127.0.0.1:8766/` → **Studio 首页 v2**（Bento）
- **应急入口**：`http://127.0.0.1:8766/classic` → classic 冻结页（**deprecated**，长期保留）
- **兼容**：`GET /v2` → **302 `/`**（旧书签）
- **回滚**：设置 `TRAVELOGUE_STUDIO_HOMEPAGE_V2=off` 后重启 Studio → `/` 回到 classic

---

## 用户可见变更

1. 打开 Studio 默认即为 v2 首页（输出优先 / Bento 书架）。
2. v2 支持浏览器**小文件夹上传**（建议 ≤200MB，超阈值确认继续）。
3. 经典 v3 影像首页移至 **`/classic`**，仅作应急；不再从 `/` 提供 full v3。

---

## 运维 / 配置

| 项 | 值 |
|----|-----|
| 默认 env | `TRAVELOGUE_STUDIO_HOMEPAGE_V2=on` |
| holdback | `auto` + `TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT=10` |
| 回滚卡 | [M21-ROLLBACK-CARD.md](./M21-ROLLBACK-CARD.md) |
| 路由权威 | [M21-ROUTING.md](./M21-ROUTING.md) |

---

## 验证清单（发版后）

- [ ] `GET /` 含 `data-homepage-variant="v2"`（`on` 模式）
- [ ] `GET /classic` 返回 classic 冻结页
- [ ] `GET /v2` → 302 `/`
- [ ] 导入 pick-folder / 上传 → preview → 返回 `/`
- [ ] `python scripts/studio_homepage_rollback_drill.py` 通过（staging）

---

## 已知限制

- M21 dogfood / 盲评等**人工签核**项见 [M21-CUTOVER-CHECKLIST.md](./M21-CUTOVER-CHECKLIST.md) 未勾条目。
- Holdback 告警 Slack 接线见 [OPEN-QUESTIONS.md](./OPEN-QUESTIONS.md) `OQ-TELEMETRY`。

---

## 升级说明（书签 / 文档）

| 旧 | 新 |
|----|-----|
| 收藏 `…/v2` | 改用 **`/`** |
| 文档写「打开 `/v2`」 | 改为 **`/`** |
| 需要 classic 应急 | 使用 **`/classic`** |
