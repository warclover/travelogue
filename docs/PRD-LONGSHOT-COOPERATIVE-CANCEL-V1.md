# Travelogue · 长图 Job 真协作取消 V1（PRD 大纲）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue（Studio 预览 Toolbar · 长图导出） |
| **文档版本** | **v0.2.0** |
| **状态** | **In Progress**（OQ 已拍板 · `feat/longshot-cooperative-cancel-v1`） |
| **性质** | **信任债还债**：可打断导出 + 产物回滚 + 槽位生命周期；非 LONGSHOT 2.0 功能面 |
| **触发来源** | [PRD-STABLE-QUALITY-HARDENING-V1](./PRD-STABLE-QUALITY-HARDENING-V1.md) **OUT-06 / R-QH-10 / QH-07**；Stable-QH 结案后下一信任波 |
| **目标分支** | `fix/longshot-cooperative-cancel-v1` → `master` |
| **关联文档** | Stable-QH · [PRD-M14-shelf-save-longshot](./PRD-M14-shelf-save-longshot.md) · [PRD-PREVIEW-EXPORT-FACADE-V1](./PRD-PREVIEW-EXPORT-FACADE-V1.md) · [PRD-UX-TRUST-V1](./PRD-UX-TRUST-V1.md) |
| **更新日期** | 2026-07-15 |

> **一句话**：Stable-QH 已把假取消换成诚实「无法取消」；本波把「想停就能停」做成与导入取消同级的真协作——打断捕获、回滚半成品、释放槽位、结果态可读。

---

## 0. 背景（As-Is）

| 层 | 现状 | 证据 |
|----|------|------|
| **预览 Dock** | 导出中**无**取消钮；文案「导出开始后无法取消」 | `preview-toolbar-v3-task-dock.js` · T-M4-06 |
| **API** | `POST /__travelogue/cancel` 可将 longshot 标 `cancelled` 并释槽 | `job_handlers.handle_cancel` · `studio_jobs.cancel_job` |
| **Runner** | 仅在 Playwright **前后**查 `is_cancelled`；捕获中途**不打断** | `run_longshot_job` |
| **产物** | 无 cancel 路径 `rollback` / purge；`.part` 依赖失败路径 | `AtomicLongshotWriter` |
| **书架 Modal** | 「关闭」≠ 取消 Job（M14 合同仍有效） | `shelf-longshot.js` |
| **死接线** | `cancelPreviewLongshotExport` 仍 POST cancel，但 Dock **不读** `onCancelExport` | `longshot.js` / `init-v3.js` |

**Stable-QH 已交付**：诚实文案 + 取消后慢 finalize 不覆盖 + 槽位可再开。  
**本波要交付**：用户可点「取消导出」→ 真停 → 盘面干净 → UI 明确「已取消」。

---

## 1. 目标 / 非目标

### 1.1 目标

| ID | 目标 |
|----|------|
| **G-LCC-01** | 导出进行中，用户可一键取消；取消后 **≤3s** 感知到「已取消」（或诚实「正在停止…」） |
| **G-LCC-02** | 取消后本轮未 commit 产物回滚；已 commit 的**本轮**分段集可声明策略（默认：删本轮新写、保留取消前已有完整集） |
| **G-LCC-03** | 槽位：cancel 后须 **await runner 退出** 再允许下一 longshot（对齐 import `await_import_handle_done`） |
| **G-LCC-04** | 三义合同：**取消导出** ≠ Dock × 关面板 ≠ 书架「关闭」 |
| **G-LCC-05** | 埋点 `longshot_export_cancel` 实火；成功/失败/取消互斥 |

### 1.2 非目标

| # | 排除 | 理由 |
|---|------|------|
| OUT-01 | LONGSHOT 2.0 新平台/新布局 | 另 PRD |
| OUT-02 | 取消方案 B（未完成书架 / 断点续跑） | Stable-QH OUT-07 |
| OUT-03 | 导入取消再设计 | 已稳定；仅复用模式 |
| OUT-04 | 可暂停/恢复导出 | 复杂度过高 |
| OUT-05 | 改 `longshotStale` 词表 | Stable-QH 已锁「长图可更新」 |

---

## 2. 体验合同

1. **诚实优先**：若某阶段技术上无法打断（极少），须保持「无法取消」文案，**禁止**假取消钮。本波默认目标是**全程可协作**。
2. **关窗不取消**：Dock ×、书架 Modal「关闭」仍只关 UI；后台 Job 继续（M14）。真停必须点明确「取消导出」。
3. **取消确认**：首次取消可轻确认（「停止导出？已生成的本轮图片将丢弃」）；勿双 Modal 堆叠。
4. **结果态**：取消成功 → Dock/Toast「已取消导出」；勿静默回 idle。
5. **再导出**：取消完成后同一 trip 可立即再点「长图」，无 409 幽灵忙。

---

## 3. 技术方案（纲要）

### 3.1 服务端

| 项 | 做法 |
|----|------|
| Cancel 入口 | 复用 `POST /__travelogue/cancel`；`type==longshot` 分支补齐 |
| Await | `await_longshot_handle_done(job_id, timeout≈30s)` 后再 `finish_longshot` 语义闭环 |
| 检查点 | `export_trip_longshot` / platform runner 接受 `cancel_check`；每页/每文件 commit 前查询 |
| 打断 | 协作 flag → 关闭 Playwright browser/context；禁止仅标 status 放跑 |
| 产物 | 未 commit → `rollback()`；本轮已 commit 文件按 **策略 A（默认）**：删除本轮 `jobId`/时间窗内新建文件，保留取消前完整旧集 |
| 响应 | `{ ok, status, purgedOutputs: bool, awaitMs }` |

### 3.2 客户端

| 面 | 变化 |
|----|------|
| 预览 Task Dock `showExporting` | 恢复「取消导出」主操作；去掉「无法取消」**或**仅在不可协作窗口显示 |
| `cancelPreviewLongshotExport` | 接确认 → POST → 等 `cancelled` → 结果态文案；接 `longshot_export_cancel` |
| 书架 Modal | 保持「关闭」；可选次要「取消导出」（须文案区分） |
| 选项面板「取消」 | 仍仅关面板（开跑前） |

### 3.3 复用范本

导入取消：`handle_cancel` + `await_import_handle_done` + `cleanup_import_terminal_artifacts`。  
长图应对齐「wait + 清理 + 不抢 finalize」，**不要** purge 整个 trip。

---

## 4. 里程碑

| 里程碑 | 内容 | 估时 |
|--------|------|------|
| **M0** | Kickoff：拍板产物策略 A/B；冻结文案表；列检查点清单 | 0.5d |
| **M1** | 服务端：cancel token 贯穿 runner + await 槽位 + rollback | 1.5–2d |
| **M2** | 预览 Dock UI + 埋点 + 结果态 | 0.5–1d |
| **M3** | 单测 + 1 条 Playwright 串行 AC + acceptance-record | 0.5–1d |

**PR 切分建议**：PR1 = M1（正确性）；PR2 = M2+M3（体验 + 证据）。

---

## 5. 验收（AC 草案）

### 5.1 自动化

- [ ] **AC-LCC-01** cancel 后 status=`cancelled`；慢 runner 不得 `succeeded`
- [ ] **AC-LCC-02** cancel 后 `await` 完成前，第二 longshot → 409 busy；完成后可创建
- [ ] **AC-LCC-03** 取消路径调用 rollback；无残留 `.part`
- [ ] **AC-LCC-04** 策略 A：取消后旧完整 longshot 集仍在；本轮半成品不在
- [ ] **AC-LCC-05** Dock 合同：导出中有「取消导出」；无「无法取消」（或仅在不可协作窗）

### 5.2 手测

- [ ] **UX-LCC-01** 大相册/多页微信长图导出中点取消 → 「已取消」→ 可立刻再导
- [ ] **UX-LCC-02** 关 Dock × ≠ 取消（Job 仍跑完或可在书架见进度）
- [ ] **UX-LCC-03** 取消后再精修标题 → 「长图可更新」语义不坏

---

## 6. 风险

| 风险 | 等级 | 缓解 |
|------|------|------|
| 释槽过早 → 双 Playwright 写同 trip | 高 | 必须 await runner；测 AC-LCC-02 |
| 半成品 + stale 假阳性/漏标 | 中 | 策略 A + 取消后 reconcile `hasLongshotExport` |
| UI 回潮假取消 | 高 | AC 锁「取消后必停」；禁止只 POST flag |
| 浏览器池泄漏 | 中 | finally 关 context；对齐全仓 longshot 超时 |

---

## 7. 开放问题（Kickoff 已拍板）

| ID | 问题 | **定案（2026-07-15）** |
|----|------|------------------------|
| **OQ-LCC-01** | 本轮已 commit 的 PNG 删还是留？ | **策略 A：删本轮、留旧完整集**（未 commit 的 `.part` rollback） |
| **OQ-LCC-02** | 书架 Modal 是否暴露「取消导出」？ | **V1 仅预览 Dock**；书架保持关闭≠取消 |
| **OQ-LCC-03** | 取消是否要确认框？ | **要**；「停止导出？」· 主「停止」· 次「继续导出」 |
| **OQ-LCC-04** | 与导出门面 V1 续跑 flag 交互？ | **取消须清** `exportAfterLayout` / layoutUpdating 类 flag |

---

## 8. Kickoff 检查清单

- [x] Owner / Reviewer / 目标合并日（本波实施中）
- [x] OQ-LCC-01..04 圈定
- [x] 分支 `feat/longshot-cooperative-cancel-v1` 已开
- [x] 对照单测基线扩展（slot await + cancel_check purge）
- [x] Stable-QH OUT-06 在结案记录中回链本文

---

## 9. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-07-15 | Stable-QH 结案后首稿大纲；承接 OUT-06 |
| v0.2.0 | 2026-07-15 | OQ 定案；M1/M2 落地（协作 cancel + Dock CTA） |
