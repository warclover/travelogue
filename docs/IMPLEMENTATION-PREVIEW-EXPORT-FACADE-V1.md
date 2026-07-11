# 预览导出门面 V1 · 实施清单

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-PREVIEW-EXPORT-FACADE-V1.md](./PRD-PREVIEW-EXPORT-FACADE-V1.md) v1.1.0 |
| **评审** | [preview-export-facade-v1-review-2026-07-11.md](./acceptance-records/preview-export-facade-v1-review-2026-07-11.md) |
| **状态** | **M-EXP-1～4 代码已落地** · M-EXP-5（SF-02）待合入后补签 |
| **更新日期** | 2026-07-11 |

## 任务表

| ID | 项 | 状态 | 落点 |
|----|-----|------|------|
| **M-EXP-1** | 续跑可靠：TTL · trip 校验 · 离开清 flag · expectReload · layoutUpdating 跨刷新 · storage 降级 · consume 立刻清 flag | ✅ | `longshot.js` · `core.js` `applyLayoutRerender(opts)` |
| **M-EXP-2** | Modal 标题「导出前先更新一下」· 仅更新残留 `showNextStepHint` · 失败分叉文案 | ✅ | `longshot.js` · `preview-toolbar-v3-task-dock.js` |
| **M-EXP-3** | 脉冲：仅主钮点击/成功导出停止；成功主句「拖进微信群」；文件夹按钮降为 ghost | ✅ | `init-v3.js` · `task-dock.js` · `longshot.js` 抽屉 |
| **M-EXP-4** | 埋点：blocked / dismiss / update_and_export / update_only / failed / consumed / expired / mismatch / cleared / share_hint · `start.from` | ✅ | `longshot.js` |
| **M-EXP-5** | SF-02 图标盲测 | ⏸ | 合入后一周内补签 |
| **P0.5-1** | 非 Dock 可见「长图」+ aria「导出长图」 | ✅ | `init-v3.js` · `syncLongshotCtaLabel` |
| **P0.5-2** | F-EXP-08「导出时仍会提醒」 | ✅ | `preview-toolbar-v3-task-dock.js` · `task-dock.css` |
| **P0.5-3** | 朋友圈/小红书成功下一步引导 | ✅ | `showSuccess` share-hint |
| **P0.5-4** | `layout_update_failed.error_code` | ✅ | `core.js` onFail · `longshot.js` |

## 文件映射

| 区域 | 文件 |
|------|------|
| 续跑 / 拦截 | `templates/studio/preview-toolbar/longshot.js` |
| rerender opts | `templates/studio/preview-toolbar/core.js` |
| 脉冲 | `templates/studio/preview-toolbar/init-v3.js` |
| Task Dock 成功 / 下一步 | `templates/studio/preview-toolbar-v3-task-dock.js` · `task-dock.css` |
| 长图钮高亮 | `templates/studio/preview-toolbar/sheet.css` |
| 静态门禁 | `tests/unit/web/test_preview_toolbar_v3.py` |

## 验证

```bash
python -m pytest tests/unit/web/test_preview_toolbar_v3.py -m "not e2e" -q
```

| 日期 | 结果 |
|------|------|
| 2026-07-11 | **23 passed**（含 `test_preview_export_facade_v1_markers`） |

## sessionStorage 键

| 键 | 用途 |
|----|------|
| `travelogue.studio.exportAfterLayout` | `{tripId,ts}` 更新并导出续跑 |
| `travelogue.studio.layoutUpdating` | 跨刷新 busy |
| `travelogue.studio.expectLayoutReload` | 区分主动 reload vs 离开 |
| `travelogue.studio.updateOnlyHint` | 仅更新后下一步 |
| `travelogue.studio.exportPulseSeen` | localStorage 脉冲已见 |
