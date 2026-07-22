# UI Detail Wave2 · Settings + Preview sheet · 审计与修复 · 2026-07-22

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | active |
| **合同** | [UI-DETAIL-CONTRACT-V0.md](../UI-DETAIL-CONTRACT-V0.md) §5–§6 |
| **清单** | [UI-DETAIL-SURFACE-INVENTORY-V0.md](../UI-DETAIL-SURFACE-INVENTORY-V0.md) |
| **复跑** | `python scripts/studio_ui_detail_static_audit.py --wave settings-sheet` · `pytest tests/e2e/test_studio_ui_detail_wave2_playwright.py` |
| **附件** | [attachments/ui-detail-wave2-settings-sheet/](./attachments/ui-detail-wave2-settings-sheet/) |

---

## 修复后结果

| 维度 | 修前 | 修后 |
|------|------|------|
| 静态 D-UID-08（色族/标题） | P1×2 | **0** |
| 运行时 P0 / P1 | 0 / 8 | **0 / 0** |
| S-SET 可见色 | 8 | **5**（ink/muted/accent/白/黑） |
| S-SHEET 可见色 | **14** | **6** |
| S-SHEET-BOOK 可见色 | 8 | **4** |
| 标题字号 | 13 vs 15 | **均为 15px**（`--studio-panel-title-size`） |

静态残留仅为 P2 文件级直方图（bento 含非 settings 字号；sheet 含关闭图标 18px）。

---

## 已落地

1. **`studio-modal.css`**：新增 `--studio-panel-*` 浅色面板 token（与确认框暖褐 ink + `#3d6b5a` accent 对齐）。
2. **Settings（`bento.css`）**：`--v2-set-*` 挂到 panel token；去掉 slate / `#2f6b55` 双绿；标题 15px。
3. **Preview sheet（`sheet.css`）**：`--sheet-*` 挂到同一套 panel token；蓝灰 muted 合并；9px badge → 11px；文案色收敛。
4. **再次掏空** `modal-chrome.css`（回潮已挡）。

---

## 复跑闸门

- `tests/e2e/test_studio_ui_detail_wave2_playwright.py`
- `tests/e2e/test_studio_ui_detail_modal_audit_playwright.py`（确认框双标准不回潮）
- `tests/unit/web/test_studio_ui_detail_static_audit.py`

---

## 残留 / 下波

- Preview **shell/longshot/drawers** 仍有独立 `#1a2f28` 硬编码（未进本波表面），可继续挂 panel token。
- wait-tips tip-tone、Help drawer 扩面。
