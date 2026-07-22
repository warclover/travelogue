# UI Detail Wave8 · Shelf + Dev + Loading · 2026-07-22

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | active |
| **合同** | [UI-DETAIL-CONTRACT-V0.md](../UI-DETAIL-CONTRACT-V0.md) D-UID-14 |
| **复跑** | `python scripts/studio_ui_detail_static_audit.py --wave shelf-dev-loading` |

---

## 做了什么

1. **Loading shimmer**：去掉 sky cyan `rgba(189,230,240)` → `--v2-border` / `--v2-surface`。
2. **Shelf**：菜单挂 `--studio-panel-*`；resume/菜单钮底 `--v2-surface`。
3. **Dev panel**：`--dev-ink/muted/surface` cream 暗玻璃；字号 ≥11px；`--studio-font-ui`。
4. **ready-badge**：9px → chip 11px；accent 走 panel。
5. 静态审计新增 `--wave shelf-dev-loading` 与 **D-UID-14**。

---

## 结果

- `shelf-dev-loading`：**无 D-UID-14 P0/P1**
