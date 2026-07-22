# UI Detail Wave6 · Bench + Wizard empty + Carousel · 2026-07-22

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | active |
| **合同** | [UI-DETAIL-CONTRACT-V0.md](../UI-DETAIL-CONTRACT-V0.md) D-UID-12 |
| **复跑** | `python scripts/studio_ui_detail_static_audit.py --wave bench-wizard-carousel` |

---

## 做了什么

1. **Advanced popover / preview combobox**（`bench.css`）：挂 `--studio-panel-*`；去掉 slate/cyan focus；chip/label ≥11px；删除 classic 叠 slate 覆盖。
2. **Wizard 空主题**：`#90e0ef` → classic cream 族。
3. **Carousel dots**：`#0f172a` → `--studio-panel-ink`（含 classic 主题覆盖）。
4. 静态审计新增 `--wave bench-wizard-carousel` 与 **D-UID-12**。

未改：`tokens.css` 默认 cyan 海洋族、bench 主条非 popover 段（下波 S-HOME-TOKENS / S-BENCH-MAIN）。

---

## 结果

- `bench-wizard-carousel`：**无 D-UID-12 P0/P1**
