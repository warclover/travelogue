# PRD-BATCH-EXPORT-MULTISELECT-V1 · 导出面板多选批量出图

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | v0.5 |
| **状态** | **Done（v1 范围内全部完成）**——Stage 1（后端调度）+ Stage 2 MVP（前端多选面板）+ Stage 3（Task Dock 清单化进度渲染）+ Stage 4（真实素材回归 + 单测覆盖收尾）均已实现并通过单测 + 真实素材 Playwright 验证。逐平台专属设置（OQ-BEX-05）明确留待产品侧后续反馈评估，不阻塞本次收尾 |
| **模块代号** | Batch Export（导出面板多选 + 排队批量出图） |
| **前置条件** | [PRD-LONGSHOT-2.0.md](./PRD-LONGSHOT-2.0.md)（平台 Profile / Job Store / Task Dock 现状架构）· [PRD-EXPORT-CARD-COMPOSE-V1.md](./PRD-EXPORT-CARD-COMPOSE-V1.md)（小红书/公众号/画册共享的 CardGrouper 管线） |
| **关联文档** | [ADR-016](./adr/016-longshot-platform-export.md)（朋友圈/微信群的 Playwright 截图架构） |
| **更新日期** | 2026-08-06 |

---

## 1. 背景与问题

用户提问（2026-08-06）：能否在导出面板同时勾选多个导出模式（例如「小红书」+「朋友圈长图」），一次性完成全部出图，而不必逐个平台重复打开面板、点击、等待？

现状：

- 导出面板的平台选择是**互斥单选**——`longshot-export-panel.js` 的 `draft.platform` 是单个字符串，按钮组每次只能高亮一个，切换平台会清空/替换当前设置态。
- 后端 `StudioJobStore` 用**全局单一布尔锁** `_longshot_running`（不分平台、不分 trip）：`create_longshot_job()` 一旦发现已有长图任务在跑，直接返回 `None` → API 层回 409 `E_STUDIO_JOB_BUSY`。这不是偶然限制，是当前"一次只处理一个长图任务"的既有设计假设。
- 六个平台实际分属**两条完全不同的技术栈**（见 §3），资源画像差异很大，"字面意义的同时并发"既不现实也无收益。

用户想要的不是"字面并发"，而是"一次操作、拿到全部结果"的体感——这可以通过**排队批量**而不改变底层并发模型来实现。

---

## 2. 目标 / 非目标

| 编号 | 目标 | 说明 |
|------|------|------|
| G-BEX-01 | 导出面板支持勾选多个平台，一次提交后依次自动完成全部导出 | 不要求用户逐个平台重复打开面板 |
| G-BEX-02 | 每个平台仍保留各自独立设置（张数/跨页数/分段模式/填充方式等），互不覆盖 | 复用现有单平台设置态，只是允许同时"挂号"多个 |
| G-BEX-03 | 进度呈现从"单进度条"升级为"平台清单+逐项状态" | 排队中 / 进行中 / 完成 / 失败，清晰可辨 |
| G-BEX-04 | 某个平台失败不阻塞其余平台，批量任务跑完后统一汇报成败清单 | 2026-08-06 讨论已拍板，见 D-BEX-05 |
| G-BEX-05 | 零风险复用现有单平台导出管线（`export_trip_longshot`），批量层只做调度，不改任何渲染/切分逻辑 | 降低本次改动的回归面 |

| 编号 | 非目标 | 说明 |
|------|--------|------|
| NG-BEX-01 | 不做"真并行"（多个平台同时占用 CPU/浏览器实例跑） | 见 §3 资源画像分析；收益低、风险高 |
| NG-BEX-02 | 不在 v1 做"小红书+公众号合并渲染"优化（共享同一份 `plan_cards` 结果，省一倍算力） | 两者当前各自完整走一遍 `export_collage_pack`；优化留作 OQ-BEX-01，不阻塞 v1 |
| NG-BEX-03 | 不支持"批量任务排队中再追加平台" | v1 提交即锁定清单，追加需等当前批量跑完 |

---

## 3. 现状架构：为什么不做真并行

| 平台 | 技术栈 | 资源画像 |
|------|--------|----------|
| `wechat_chat` / `wechat_moments`（微信群 / 朋友圈长图） | Playwright 截真实 `index-longshot.html` 长图再按内容感知切段（ADR-016 分支 B） | 独占浏览器实例池 `_BROWSER_POOL`，单次 20–60 秒，内存/CPU 开销大 |
| `xiaohongshu` / `wechat_official` / `album_spread`（小红书 / 公众号 / 画册） | Pillow `CardGrouper → CardTemplateSelector → CardRenderer`（PRD-EXPORT-CARD-COMPOSE-V1） | 无浏览器依赖，纯 CPU 图像处理，单次数秒 |
| `poster_bric`（单张海报） | 同上 Pillow 管线（不同选图策略） | 同上 |

两条技术栈同时跑，本质是在单机上让"重量级浏览器进程"和"轻量级图像处理"抢同一份 CPU/内存——不会更快，只会更不稳定（尤其是 Playwright 冷启动 + 内存降级逃生门 D-LNG2-13 本就对资源敏感）。**串行执行没有实际性能损失**，因为：

- Pillow 三个平台单次几秒钟，即便串行叠加也远快于 Playwright 一次截图。
- Playwright 的"重"是浏览器冷启动/页面渲染的固有成本，与是否有其他任务在跑无关。

因此本 PRD 的方案是**保留现有 Job Store 单锁模型不变**，只在"一个 Job 内部"引入多平台循环调度——见 §4.2。

---

## 4. 方案设计

### 4.1 拍板决策

| 编号 | 决策 | 说明 |
|------|------|------|
| D-BEX-01 | 平台选择从互斥单选改为可勾选多选 | `draft.platform: string` → `draft.platforms: string[]`；`platform` 仍保留 = `platforms[0]`，供未改造的旧调用点向后兼容。**MVP 范围收窄**（用户 2026-08-06 确认）：勾选 2 个及以上平台时暂不提供手风琴式逐平台设置，批量场景下所有平台统一走自动/默认设置（张数/跨页数/分段模式）；需要自定义张数请单选该平台单独导出。真正的"每平台独立设置"留作 OQ-BEX-05，后续迭代补齐 |
| D-BEX-02 | 后端新增"批量导出"入口，内部按用户勾选顺序**依次**复用现有 `export_trip_longshot(platform=...)` | 不改任何 CardGrouper/CardRenderer/Playwright 切分逻辑；批量层只是一个 for 循环 + 结果汇总 |
| D-BEX-03 | Job Store **不新增并发槙位**，批量导出仍是**一个** Job（`type="longshot_batch"` 或复用 `"longshot"`），`_longshot_running` 单锁保持不变 | 批量的"多"体现在 Job 内部的 runner 循环，不体现在 Job Store 的并发模型上——零风险 |
| D-BEX-04 | Task Dock 进度呈现从单行 `stageHint` 升级为「平台清单」：每项独立展示 排队中 / 进行中 / 已完成 / 失败 | `stageIndex`/`stageCount` 语义调整为"当前第几个平台/共几个平台"；`stageHint` 追加当前平台 label，前端渲染清单而非单行文案 |
| D-BEX-05 | 某平台导出失败时**跳过继续跑剩余平台**，批量任务整体仍以"部分成功"收尾，不整体判失败；最终结果汇总"哪些成功、哪些失败+原因" | 2026-08-06 用户讨论已确认，对应 §2 G-BEX-04 |
| D-BEX-06 | 批量导出的文件写入复用各平台既有的文件名前缀规则（`file_prefix_for_platform`），互不冲突 | 无需改 `PlatformExportWriter`；不同平台天然产出不同文件名 |
| D-BEX-07 | 批量提交后清单锁定，不支持追加/移除（对应 NG-BEX-03） | 用户要调整需等当前批量任务结束（成功/失败/取消）后重新勾选提交 |

### 4.2 后端：批量调度

```python
def export_trip_longshot_batch(
    trip_dir: Path,
    *,
    requests: list[BatchExportRequest],  # 每项含 platform / slide_count / pad_mode 等
    progress: BatchProgressFn | None = None,
    cancel_check: CancelCheckFn | None = None,
) -> list[BatchExportItemResult]:
    """依平台顺序调用既有 export_trip_longshot，逐项捕获异常、不中断整体循环
    （D-BEX-02/05）。每项结果独立记录成功/失败，不做任何渲染管线改动。"""
    results = []
    for i, req in enumerate(requests):
        if cancel_check and cancel_check():
            break
        def _item_progress(cur, total, hint):
            if progress:
                progress(i, len(requests), req.platform, cur, total, hint)
        try:
            result = export_trip_longshot(
                trip_dir, platform=req.platform, slide_count=req.slide_count,
                pad_mode=req.pad_mode, progress=_item_progress, ...
            )
            results.append(BatchExportItemResult(platform=req.platform, ok=True, result=result))
        except LongshotExportError as exc:
            results.append(BatchExportItemResult(platform=req.platform, ok=False, error=exc))
            continue  # D-BEX-05：跳过继续，不 raise 中断整体循环
    return results
```

`handle_longshot`（`export_handlers.py`）的 `runner()` 闭包按 D-BEX-02/03 改为：若 payload 带 `platforms`（数组）则调用 `export_trip_longshot_batch`，否则保持现有单平台路径不变（向后兼容，现网单平台调用零改动）。

### 4.3 API / 数据契约

请求（`POST /__travelogue/longshot`，扩展现有 payload）：

```json
{
  "tripId": "demo-xxx",
  "platforms": [
    { "platform": "xiaohongshu", "slideCount": null },
    { "platform": "wechat_moments" }
  ],
  "scale": 2
}
```

- 未带 `platforms` 字段 → 沿用现有单平台 `platform` 字段路径，**完全向后兼容**。
- 带 `platforms` 数组 → 走批量路径；数组内每项独立携带该平台的 `slideCount`/`padMode` 等专属设置（对应 D-BEX-01）。

响应（Job 轮询结果，扩展现有 result 结构）：

```json
{
  "ok": true,
  "batch": true,
  "items": [
    { "platform": "xiaohongshu", "ok": true, "outputs": [...], "pageCount": 8, "userHint": "..." },
    { "platform": "wechat_moments", "ok": false, "error": "E_LNG_CAPTURE_TOO_LARGE", "message": "..." }
  ],
  "succeededCount": 1,
  "failedCount": 1
}
```

单平台请求（无 `platforms` 字段）响应结构保持现状不变（`outputs`/`pageCount`/`userHint`/`platform`……），不引入破坏性变更。

### 4.4 前端：多选面板 + 进度清单

**Stage 2 MVP 已实现（`longshot-export-panel.js` + `preview-toolbar/longshot.js`）：**

- 平台按钮组去掉互斥态，改为多选（`role="checkbox"` + `aria-checked`，可用现有按钮外观+勾选态样式，`draft.platforms` 数组存取，`getDraft()`/`setDraft()` 双向兼容 `platform` 单值字段）。
- MVP 范围收窄：勾选 2 个及以上平台时**隐藏**张数/跨页数等逐平台设置字段（`syncPanelUI` 按 `isBatch` 判断），改为展示一条批量提示（`data-batch-hint`：「批量导出 · N 个模式，均使用自动设置」）；不做手风琴式逐平台设置区（对应上移的 D-BEX-01 收窄说明）。
- 确定按钮文案从「导出 XX」变为「导出 N 个模式」（N≥2 时，`ctaLabelForPlatforms`/`shortCtaLabelForPlatforms`），单选时与改造前文案完全一致（零回归）。
- 提交时（`preview-toolbar/longshot.js` 新增 `runBatchExport`）直接构造 `{ platforms: [{platform}, ...] }` 批量请求体，复用现有 `postJsonBusyRetry` + `pollJob` 提交/轮询链路；批量任务几乎总是以 `job.status === "succeeded"` 收尾（部分平台失败已在后端汇总进 `result.items`，不冒泡成 job 失败——D-BEX-05），完成后用 `formatBatchSuccess` 生成一句话汇总文案，走 toast 展示（**未**接入 `showLongshotDrawer`/Task Dock 抽屉——那要求的"单结果形状"渲染留给 Stage 3 统一做清单化改造）。

**Stage 3 已实现（Task Dock 清单化）：**

- Task Dock 进度区域从单行文案改为清单，新增 `showBatchChecklist(opts)`（`preview-toolbar-v3-task-dock.js`）：

```
批量导出中（1/2）
⏳ 小红书
・ 画册
```

- 完成态（成功/部分失败）复用同一清单，逐项标注✅/✗，成功项追加页数（如「小红书 · 9 张」），失败项追加错误提示：

```
✓ 2 个模式已全部导出
✅ 小红书 · 9 张
✅ 画册 · 5 张
```

- 进度态与完成态各自的清单结构由 `longshot-export-panel.js` 新增的 `batchChecklistItems`（依 `stageIndex` 推算排队中/进行中/已完成）与 `batchChecklistItemsFromResult`（依后端 `result.items` 生成成功/失败详情）两个纯函数计算，`preview-toolbar/longshot.js` 的 `runBatchExport` 通过 `pollJob` 新增的 `onTick` 回调驱动实时刷新，完成后调用 `showBatchChecklist({done: true, ...})` 替代原 toast 汇总。
- 2026-08-06 用真实素材（`demo-49cbe46479`，247 张照片，小红书+画册双平台）通过 Playwright 端到端验证：进行中清单准确显示「批量导出中（1/2）」+ 逐项排队/进行中状态；完成后清单显示「✓ 2 个模式已全部导出」+「小红书 · 9 张」「画册 · 5 张」，与落盘文件数一致。

---

## 5. 与既有系统的关系

| 现有组件 | 影响 |
|----------|------|
| `StudioJobStore`（`_longshot_running` 单锁） | **不改**——批量导出仍是一个 Job（D-BEX-03） |
| `export_trip_longshot` / `export_collage_pack` / `export_platform_longshot` | **不改**——批量调度层只是循环调用，零侵入 |
| `longshot-export-panel.js`（`draft.platform` 单选态） | 改为 `draft.platforms` 多选态（D-BEX-01），设置面板从表单改手风琴 |
| `preview-toolbar/longshot.js`（`stageIndex`/`stageCount`/`stageHint` 单行进度渲染） | 扩展为清单渲染（D-BEX-04） |
| `PlatformExportWriter` / 文件命名前缀 | **不改**——各平台命名本就互斥（D-BEX-06） |
| `handle_longshot`（`export_handlers.py`） | 新增 `platforms` 数组分支，单平台路径保持向后兼容 |

---

## 6. 验收标准

| 编号 | 内容 | 现状（2026-08-06） |
|------|------|----------------------|
| AC-BEX-01 | 面板可同时勾选 2 个及以上平台并提交，无需逐个重复打开面板 | ✅ Stage 2 MVP 已实现 |
| AC-BEX-02 | 已勾选的每个平台各自的专属设置（张数/跨页数/分段模式）互不覆盖、互不影响 | ⏸️ MVP 收窄：批量态统一走自动设置，逐平台专属设置留作 OQ-BEX-05（需自定义请单选单独导出） |
| AC-BEX-03 | 批量导出全过程中 Job Store 不出现并发长图任务（`_longshot_running` 仍是单锁语义） | ✅ Stage 1 已实现并有单测覆盖 |
| AC-BEX-04 | 某平台导出失败时，其余平台仍继续跑完，最终结果清单标注每项成败 | ✅ Stage 1（后端 mock 用例）+ Stage 4（`test_batch_real_pipeline_partial_failure_continues` 真实渲染管线用例）+ Stage 2/3（前端汇总/清单展示）均已覆盖 |
| AC-BEX-05 | 未使用 `platforms` 字段的既有单平台请求，行为/响应结构与改动前完全一致（向后兼容回归） | ✅ 全量回归测试已验证（Python export 238 项 + handlers 117 项 / JS 111 项全绿）；Stage 4 新增显式契约测试断言批量专属字段（`batch`/`items`/`succeededCount`/`failedCount`）在单平台响应里不存在 |
| AC-BEX-06 | Task Dock 进度清单实时反映"当前第几个平台/共几个平台"及每项状态 | ✅ Stage 3 已实现，真实素材 Playwright 验证通过 |

---

## 7. 分阶段计划

1. ✅ **Stage 1**：后端 `export_trip_longshot_batch` 调度函数 + `handle_longshot` 的 `platforms` 分支（向后兼容单平台路径不动）。
2. ✅ **Stage 2（MVP）**：前端面板多选态改造（`draft.platforms`）+ `runBatchExport` 批量提交/轮询/toast 完成提示；**范围收窄**为不做手风琴逐平台设置区（批量态统一自动设置），完成提示为简单 toast 而非 Task Dock 清单（那部分挪到 Stage 3）。
3. ✅ **Stage 3**：Task Dock 清单化进度渲染（`showBatchChecklist`）+ 批量成功/部分失败结果的完整展示，已用真实素材 Playwright 验证。
4. ✅ **Stage 4（真实素材回归 + 单测覆盖收尾）**：新增 3 项**完全不 mock** `export_trip_longshot` 的真实管线用例（`test_batch_real_pipeline_multi_platform_success`/`_partial_failure_continues`/`_backward_compat_single_platform_path_unaffected`，走真实 CardGrouper/CardRenderer 渲染种子照片）+ 1 项 handler 层向后兼容契约测试（`test_handle_longshot_single_platform_request_shape_unaffected`，断言单平台响应键集合里不存在任何批量专属字段）。逐平台专属设置（手风琴）留作 **OQ-BEX-05**，明确不在 v1 范围内，需产品侧后续确认是否补齐。

---

## 8. 开放问题

| 编号 | 问题 | 备注 |
|------|------|------|
| OQ-BEX-01 | 小红书 + 公众号同时勾选时，是否共享同一份 `plan_cards`/渲染结果只出两套文件名，省一倍算力 | v1 不做（NG-BEX-02），留作 v2 优化；v1 两者各自完整跑一遍 `export_collage_pack`，实现简单、零风险 |
| OQ-BEX-02 | 是否需要"全选"快捷按钮，一键勾满所有可用平台 | 待实施阶段与 UI 走查一并确认，不阻塞 Stage 1 后端开工 |
| OQ-BEX-03 | 批量导出过程中用户是否可以单独取消清单中的某一项（而非整体取消） | v1 默认仅支持整体取消（复用现有 `cancel_check`/`cancel_register`）；细粒度取消留待用户反馈后再评估 |
| OQ-BEX-04 | `longshot-current.json`（staleness 追踪清单）在批量场景下该如何表达"多平台各自都有产物" | Stage 1 已实现的简化行为：只反映批量中**最后一个成功平台**的产物，其余平台产物已落盘但不计入 staleness 追踪；影响面：若用户后续改动内容，`longshotStale` 提示可能只针对最后一个平台生效。留待前端 Stage 2/3 落地后按真实用户反馈评估是否需要扩展该文件为多条目清单 |
| OQ-BEX-05 | 是否需要为批量态补齐"逐平台专属设置"（手风琴式张数/跨页数/分段模式，即 D-BEX-01 完整版） | Stage 2 MVP 已按用户 2026-08-06 确认收窄为"批量态统一自动设置"；v1 用户若需自定义张数，需单选该平台单独导出。留待真实使用反馈评估是否值得补齐 |
| OQ-BEX-06 | 批量任务是否需要支持"进行中追加/取消单项"，或至少在 Stage 3 清单化 UI 里可视化每平台的独立取消按钮 | v1 仅支持整体取消（同 OQ-BEX-03）；Stage 3 做清单化渲染时可重新评估是否顺带补上单项取消 |

---

## 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.5 | 2026-08-06 | **Stage 4 实施完成（v1 范围收尾）**。`tests/unit/export/test_longshot_batch.py`：新增 `_seed_kept_photos` 真实照片种子 helper（与 `test_collage_pack.py` 同款）+ 3 项**完全不 mock** `export_trip_longshot` 的真实管线用例——`test_batch_real_pipeline_multi_platform_success`（小红书+公众号+画册三平台批量，全走真实 CardGrouper/CardRenderer，验证三套文件名互不重叠）、`test_batch_real_pipeline_partial_failure_continues`（仅在数据源层 `list_collage_photo_paths` 为第 2 个调用注入真实 `E_COLLAGE_N` 空照片错误，验证 scheduler 对真实 `LongshotExportError` 的捕获/继续行为，且失败项 `writer.rollback()` 确实未产出任何文件）、`test_batch_backward_compat_single_platform_path_unaffected`（直接调用 `export_trip_longshot` vs 经批量调度层调用同一平台，产出文件名/页数完全一致）。`tests/unit/web/handlers/test_studio_handlers_longshot_batch.py`：新增 `test_handle_longshot_single_platform_request_shape_unaffected`（AC-BEX-05 显式契约：断言单平台响应体里 `batch`/`items`/`succeededCount`/`failedCount` 键**不存在**，而非值为空）。全量回归：`tests/unit/export` 238 项 + `tests/unit/web/handlers` 117 项 + JS 111 项全绿。至此 v1 范围内 Stage 1–4 全部完成，PRD 状态置为 Done；OQ-BEX-05（逐平台专属设置手风琴）留待产品侧真实使用反馈评估，作为后续独立迭代 |
| v0.4 | 2026-08-06 | **Stage 3 实施完成**（Task Dock 清单化）。`preview-toolbar-v3-task-dock.js`：新增 `showBatchChecklist(opts)`，渲染进行中/完成态两种清单（每项 排队中/进行中/已完成/失败 图标+文案，完成态含成功页数或错误详情、「换种分享方式」「在文件夹中显示」操作按钮）。`templates/studio/preview-toolbar/task-dock.css`：新增 `.preview-task-dock--batch`/`__batch-list`/`__batch-item`/`__batch-mark`/`__batch-label` 样式。`longshot-export-panel.js`：新增纯函数 `batchChecklistItems`（按 `stageIndex` 推算进行中清单）+ `batchChecklistItemsFromResult`（按后端 `result.items` 生成完成态清单，含每项页数/错误）。`preview-toolbar/longshot.js`：`pollJob` 新增 `onTick` 回调；`runBatchExport` 改为通过 `onTick` 驱动 `showBatchChecklist` 实时刷新进度清单，完成后调用清单化的成功/部分失败展示（替代原 toast）；同时修复三处联动问题——`syncLongshotCtaLabel` 未按 `prefs.platforms.length > 1` 走批量文案（导致 CTA 文案回退单平台）、`writeExportPrefs` 未持久化 `platforms` 数组（刷新页面后批量选择丢失）、`syncPrefsPlatform`（Output Recipe 等单平台猜测逻辑复用）会无条件把已选的多平台数组收缩回单平台（导致批量选择被静默清空）——为其加了"若已有 ≥2 个平台则不覆盖"的保护。单测：`tests/js/longshot-export-panel.test.mjs` 新增 2 项覆盖 `batchChecklistItems`/`batchChecklistItemsFromResult`；全量回归 JS 111 项全绿。真实素材验证：用 Playwright 对 `demo-49cbe46479`（247 张照片）触发小红书+画册双平台批量导出，进行中清单/完成清单/落盘文件数三者一致，确认 AC-BEX-06 达标 |
| v0.3 | 2026-08-06 | **Stage 2 MVP 实施完成**（用户确认范围：多选勾选 + 批量提交/轮询/完成提示都做，但不做手风琴逐平台设置——批量态统一自动设置）。`longshot-export-panel.js`：新增 `normalizePlatformList`/`ctaLabelForPlatforms`/`shortCtaLabelForPlatforms`/`exportSummaryLineForPlatforms`/`formatBatchSuccess`；`readExportPrefs`/`writeExportPrefs` 支持 `platforms: string[]`（`platform` 仍保留 = `platforms[0]` 向后兼容）；`buildPanelHtml`/`syncPanelUI`/`bindPanelDraft` 改造为多选（`role="checkbox"`+`aria-checked`），批量态隐藏张数/跨页数字段并展示 `data-batch-hint` 提示。`preview-toolbar/longshot.js`：新增 `runBatchExport`（`platforms.length > 1` 时从 `runLongshotExport` 分流），直接构造 `{platforms:[{platform},...]}` 批量请求体，复用既有 `postJsonBusyRetry`/`pollJob` 链路，完成后用 `formatBatchSuccess` 生成 toast 文案（不接入 `showLongshotDrawer`/Task Dock，那部分明确留给 Stage 3）。单测：`tests/js/longshot-export-panel.test.mjs` 新增 8 项覆盖多选工具函数与 `syncPanelUI`/`bindPanelDraft` 多选行为；全量回归 Python 242 项 + JS 109 项全绿。AC-BEX-02/06 因 MVP 收窄标记为待续，新增 OQ-BEX-05/06 |
| v0.2 | 2026-08-06 | **Stage 1 实施完成**：新增 `travelogue/export/longshot_batch.py`（`export_trip_longshot_batch` 调度函数，`BatchExportRequest`/`BatchExportItemResult`）+ `export_handlers.handle_longshot` 的 `platforms[]` 分支（`_handle_longshot_batch`）。行为对齐 §4 设计：逐项校验（`resolve_profile`/重复平台/`poster_bric` flag）失败即整体拒绝提交（400）；提交成功后逐平台顺序跑，单项 `LongshotExportError`/意外异常不阻塞其余（D-BEX-05），仅 `LongshotCancelled` 中断整批；仍是同一个 `StudioJob`，`_longshot_running` 单锁不变（D-BEX-03，含单测验证批量提交遇忙返回 409）；未带 `platforms` 字段的既有单平台路径零改动（AC-BEX-05，回归测试 282 项全绿）。已知 v1 简化：批量暂不支持"部分平台需浏览器兼容模式回落"的混合态（缺 Playwright 时整体拒绝提交，见 `E_LNG2_BATCH_CLIENT_FALLBACK_UNSUPPORTED`）；批量场景跳过 Output Recipe / intent 解析（用户已显式多选，无需再猜测分享意图）；`longshot-current.json` 仍是单一清单语义，只反映批量中**最后一个成功平台**的产物（新增 OQ-BEX-04）。单测：`tests/unit/export/test_longshot_batch.py`（调度层）+ `tests/unit/web/handlers/test_studio_handlers_longshot_batch.py`（handler 层）。Stage 2（前端多选面板）/ Stage 3（Task Dock 清单化）待续 |
| v0.1 | 2026-08-06 | 初稿：基于当日讨论（"多选导出模式"）落笔，明确不做真并行、改为排队批量复用现有单平台管线；拍板"部分失败不阻塞其余平台继续跑"（D-BEX-05）。尚未实施，等待排期评审 |
