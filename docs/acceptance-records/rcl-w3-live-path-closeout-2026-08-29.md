# RCL W3 收口 · 活路径文件头与 CSS 目录

| 项 | 内容 |
|----|------|
| **日期** | 2026-08-29 |
| **里程碑** | RCL W3（FE-RCL-01 / FE-RCL-02 / BE-RCL-13 / DO-RCL-04） |
| **合同** | [PRD-READABLE-CORE-LINE-V1.md](../PRD-READABLE-CORE-LINE-V1.md) v0.2.2 §7 |

## 出门

- §7.2 名单文首有 `LIVE` / `READER`（AC-RCL-16）。
- 三份大 CSS 最顶、第一个 `@lte-generated` 之前有 `RCL-W3-CATALOG`（≤10 行）；`sync_journal_screens_css` / `sync_portfolio_pages_css` 之后仍在（AC-RCL-17 / BLK-RCL-07）。
- 未新增第三份族 CSS。
- `test_asset_version` **一次** bump，原因：W3 文件头 + CSS 目录注释。
- `render_fingerprint` 不因本波变化（CSS 字节不进 trip 载荷摘要）。

## SHD-RCL-03 · 90 秒走读（不挡 merge）

打开 `build_render_context`：表面 → 封面 bundle → 文案护栏 → **S-04** 分发章 builder → folio extras。细节在 `assemble_cover.py` / `assemble_copy.py`，不必先读书法 PRD。

活路径：`docs/frontend-live-path.md` 双入口写死；`preview-toolbar.js` 是 Studio 预览，`visual-journal/longshot.js` 是读者面截图，不要合并。
