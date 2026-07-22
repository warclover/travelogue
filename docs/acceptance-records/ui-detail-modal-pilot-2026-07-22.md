# UI Detail 弹窗家族试点 · 审计与修复 · 2026-07-22

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | active |
| **合同** | [UI-DETAIL-CONTRACT-V0.md](../UI-DETAIL-CONTRACT-V0.md) |
| **清单** | [UI-DETAIL-SURFACE-INVENTORY-V0.md](../UI-DETAIL-SURFACE-INVENTORY-V0.md) |
| **复跑** | `python scripts/studio_ui_detail_static_audit.py` · `pytest tests/e2e/test_studio_ui_detail_modal_audit_playwright.py` |
| **附件** | [attachments/ui-detail-modal-pilot/](./attachments/ui-detail-modal-pilot/) |

---

## 修复后结果（复跑）

| 维度 | 修复前 | 修复后 |
|------|--------|--------|
| 静态 P0（双标准） | 15 | **0** |
| 运行时 P0 / P1 | 18 / 7 | **0 / 0** |
| 静态 P2（overlays 文件级离散） | 3 | 2（wait-tips 等仍在 overlays.css，下波） |

运行时表面：

| 表面 | 字号种类 | 颜色种类 |
|------|----------|----------|
| S-MODAL | 3（17/14/13） | ≤5（含 help） |
| S-FS | 5 | **4** |
| S-FAIL | 5 | **4** |
| S-WIZ（可见步） | 3（21/14/12） | **4** |
| S-MODAL-PREVIEW-DUAL | 与规范一致 | 无偏离 |

---

## 已落地修改

1. **P0 · 确认框统一**  
   `preview-toolbar/modal-chrome.css` 掏空为 stub；预览页沿用 `studio_chrome.py` 已注入的 `studio-modal.css`。
2. **P1 · FirstSuccess / Failure**  
   语义色收敛为 ink / muted / accent / cta-ink；去掉多余透明度色阶。
3. **P1 · Import Wizard**  
   辅助字号并入 12px 阶梯；`muted-soft` 对齐 `muted`；测量仅计可见步（排除 × 图标）。

---

## 回归闸门

- `tests/unit/web/test_studio_ui_detail_static_audit.py` · 无 `.studio__*` D-UID-01  
- `tests/e2e/test_studio_ui_detail_modal_audit_playwright.py` · 双 CSS 叠载后无 P0 偏离  

---

## 残留 / 下波

- overlays.css 内 wait-tips 多 tip-tone（静态 P2）  
- Preview sheet / Help drawer / Settings（inventory 扩面）
