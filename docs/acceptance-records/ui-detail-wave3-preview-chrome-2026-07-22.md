# UI Detail Wave3 · Preview chrome + Help · 2026-07-22

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | active |
| **合同** | [UI-DETAIL-CONTRACT-V0.md](../UI-DETAIL-CONTRACT-V0.md) D-UID-09 |
| **复跑** | `python scripts/studio_ui_detail_static_audit.py --wave preview-chrome` |

---

## 做了什么

1. `preview-toolbar/tokens.css` 增加 `--preview-ink/muted/accent/...`，映射到 `--studio-panel-*`。
2. 批量改挂（约 60 处）：`shell` / `longshot` / `drawers` / `legacy-bar` / `cohort` / `task-dock` / `v3-bar` + `help-drawer.css`。
3. Dock running 态渐变改为 `preview-muted` 系。
4. Sheet 的 `--sheet-*` 优先读 `--preview-*`。
5. 静态审计新增 `--wave preview-chrome` 与 **D-UID-09**（裸 hex 门禁）。

`sheet.css` 仍保留一处字面 `#1a2f28`（unit gate / inventory）。

---

## 结果

- `preview-chrome` 波次：**P0=0 / P1=0**（无 D-UID-09）
- Wave1/2 回归：modal + settings-sheet 审计仍绿
