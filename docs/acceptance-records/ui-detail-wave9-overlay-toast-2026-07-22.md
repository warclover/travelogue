# UI Detail Wave9 · Unsupported + Failure + Toast · 2026-07-22

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | active |
| **合同** | [UI-DETAIL-CONTRACT-V0.md](../UI-DETAIL-CONTRACT-V0.md) D-UID-15 |
| **复跑** | `python scripts/studio_ui_detail_static_audit.py --wave overlay-toast` |

---

## 做了什么

1. **Unsupported**：`--un-ink/muted`；brand 11px；主按钮 cream→accent-strong，圆角 8px。
2. **FirstSuccess**：去掉重复 `--v2-fs-accent`；muted 对齐 cream。
3. **Failure auth**：去掉薄荷 `#9ec5b8`；echo 11px。
4. **Preview toast** 对齐 `studio__toast` cream 暗底（禁薄荷字/森林底）。
5. 静态审计新增 `--wave overlay-toast` 与 **D-UID-15**。

---

## 结果

- `overlay-toast`：**无 D-UID-15 P0/P1**
