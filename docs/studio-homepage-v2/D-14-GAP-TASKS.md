# D-14 预览画册选择器 · PRD 对照遗漏清单

> **对照基准**：[PRD-STUDIO-HOMEPAGE-v2.md §6.8](../PRD-STUDIO-HOMEPAGE-v2.md#68-预览画册选择器d-14--v206-草案) · [§6.8.9 AC-D14-01～08](../PRD-STUDIO-HOMEPAGE-v2.md#689-验收标准) · [D-14-TASKS.md](./D-14-TASKS.md)  
> **对照日期**：2026-06-18 · 代码态：MVP + Phase 2 + Phase 3 已落地 · **已提交 master**

---

## 已实现（PRD 覆盖摘要）

| 区域 | 状态 |
|------|------|
| Combobox + 缩略图 popover + stale chip | ✅ |
| `bentoPreviewTripId` / localStorage / 派生 `bentoTab` | ✅ |
| 404 保持选中 + bench 内联提示 +「打开画册」 | ✅ |
| 删 trip → 回示例 + toast | ✅ |
| stale bar 绑定 preference trip | ✅ |
| 书架「在上方预览」· FirstSuccess「设为首页预览」 | ✅ |
| Recent 卡 `is-previewing` | ✅ |
| `?preview=` deep link + harness `?bentoPreviewTrip=` | ✅ |
| 分页「加载更多」+ 客户端搜索 | ✅ |
| `ensureTripInCatalog`（非首屏 preference） | ✅ |
| `bento_preview_select` 遥测 + allowlist | ✅（source 部分见 G-06） |

---

## A · 代码遗漏（PRD 明确要求）

| ID | 优先级 | 任务 | PRD / DoD | 现状 | 建议文件 |
|----|--------|------|-----------|------|----------|
| **G-01** | P0 | **D-13 → D-14 一次性迁移** | §6.8.7 | ✅ `bento-preview-migrate.js` + harness `bentoTabSession` |
| **G-02** | P0 | **16:9 / 9:16 demo-flag** | §6.8.2 / AC-D14-01 | ✅ carousel + phone `[data-demo-flag]` |
| **G-03** | P1 | **无用户画册 · 控件降级** | AC-D14-06 | ✅ trigger disabled + title |
| **G-04** | P1 | **`bento_tab_switch` shim** | §6.8.8 | ✅ `setBentoPreviewTripId` 切换时 fire |
| **G-05** | P2 | **离线 preference 保选项** | §6.8.4：fetch 失败不清 preference；用**缓存 trips** 填选项 | ✅ `tripsCache` + `test_ac_d14_offline_trips_cache` |
| **G-06** | P2 | **遥测 `source` 补全** | §6.8.8 | ✅ deep link 发 `source: deeplink` |
| **G-07** | P3 | **死代码清理** | — | ✅ 移除 `.v2-bento-tabs__*` CSS · `setBentoTab` shim |

---

## B · 验收 / 测试遗漏

| ID | 优先级 | 任务 | PRD AC | 现状 | 建议 |
|----|--------|------|--------|------|------|
| **G-10** | P0 | **AC-D14-01 demo-flag 断言** | 无 preference → demo-flag 可见 | ✅ `test_ac_hp2_02` + `test_ac_d14_06` |
| **G-11** | P1 | **AC-D14-03 持久化** | 选 B → 硬刷新 → 仍 B | ✅ `test_ac_d14_03_persist_refresh` |
| **G-12** | P1 | **AC-D14-04 已删 trip** | preference 指向已删 → 回示例 + toast | ✅ `test_ac_d14_04_deleted_trip_fallback` |
| **G-13** | P1 | **AC-D14-05 preview 404** | 占位 + 说明；控件仍显示 B | ✅ `bentoPreview404` + `test_ac_d14_05` |
| **G-14** | P1 | **AC-D14-07 algorithmStale** | 选 B → stale bar 绑定 B | ✅ `test_ac_d14_07_algorithm_stale_bar` |
| **G-15** | P1 | **AC-D14-08 curate 后刷新** | reroute 后仍刷新 preference manifest | ✅ `page.route` mock curate/status + `test_ac_d14_08` |
| **G-16** | P2 | **AC-VERIFICATION 登记** | PRD §16 引用 AC-D14-01～08 | ✅ 8 行 |
| **G-17** | P3 | **T17 单测（可选）** | D-14-TASKS T17 | ✅ `bento-preview-picker-logic.test.mjs` |

**已有 D-14 相关 e2e（非 AC 编号一一对应）**：`test_ac_hp2_bento_tab_mine` · `test_ac_hp2_d14_*`（combobox / shelf / deeplink / 分页搜索）。

---

## C · 文档 / 契约漂移

| ID | 优先级 | 任务 | 说明 |
|----|--------|------|------|
| **G-20** | P1 | **PRD 状态更新** | ✅ v2.0.6 Combobox / Phase 状态 |
| **G-21** | P1 | **DEV-HARNESS 补参** | ✅ `preview` / `bentoPreviewTrip` / D-14 参数 |
| **G-22** | P2 | **DATA-CONTRACT §5 文件索引** | ✅ migrate / deeplink / picker |
| **G-23** | P2 | **遥测契约** | ✅ PRD §6.8.8 source 枚举 |
| **G-24** | P3 | **§6.4 文案** | ✅ 「Combobox」已同步 PRD §6.4 |

---

## D · PRD 明确不在范围（勿误作遗漏）

| 项 | PRD 出处 | 说明 |
|----|----------|------|
| 服务端 preference 同步 | §6.8.1 MVP 不含 | 仍仅 localStorage |
| 全库**服务端**搜索 | §6.8.1 MVP 不含 | Phase 3 已做**客户端**过滤，非 API 搜索 |
| Import 后**强制**切换预览 | §6.8.4 | 仅 optional「设为首页预览」✅ |
| 后端 API 变更 | §6.8.6 | 仍无变更 ✅ |

---

## E · 建议实施顺序

```
P0 收尾（可 dogfood 前）
  G-02 demo-flag → G-10 测试
  G-01 D-13 迁移（若有 session 态可读）

P1 验收闭环
  G-11～G-15 AC 专项 e2e
  G-03 无画册 disabled
  G-04 bento_tab_switch shim
  G-16 AC-VERIFICATION
  G-20～G-21 文档

P2  polish
  G-05 离线 · G-06 遥测 · G-21～G-23 契约

P3  清理 / 可选
  G-07 CSS · G-17 单测 · G-24 文案
```

**粗估**：P0～P1 约 **0.5～1d** · P2 **0.5d** · P3 可选

---

## F · 风险自检（PRD §6.8.4 再核对）

| 场景 | 实现 | 缺口 |
|------|------|------|
| 首次无 preference → 示例 | ✅ | demo-flag ×2 |
| 404 不静默换书 | ✅ | — |
| 删 trip 回示例 | ✅ | `test_ac_d14_04` |
| curate 后刷新 B | ✅ | `test_ac_d14_08` |
| 无用户画册 | ✅ | disabled + title |
| 离线不清 preference | ✅ | `test_ac_d14_offline_trips_cache` |
| D-13 session 迁移 | ✅ | `bento-preview-migrate.js` |

---

## 变更记录

| 日期 | 说明 |
|------|------|
| 2026-06-18 | G-07 / G-17 / G-24 收尾；状态更新为已提交 |
| 2026-06-17 | G-11～G-16、G-20～G-23、G-06 落地 |
| 2026-06-17 | 初版：对照 PRD v2.0.6 §6.8 vs 当前未提交实现 |
