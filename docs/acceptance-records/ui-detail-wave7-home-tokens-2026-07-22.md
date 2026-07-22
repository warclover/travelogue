# UI Detail Wave7 · Homepage tokens + theme-aware hardcodes · 2026-07-22

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | active |
| **合同** | [UI-DETAIL-CONTRACT-V0.md](../UI-DETAIL-CONTRACT-V0.md) D-UID-13 |
| **复跑** | `python scripts/studio_ui_detail_static_audit.py --wave home-tokens` |

---

## 做了什么

1. **`tokens.css`**：裸 `:root` 对齐 mist；cyan 迁入 `:root[data-v2-theme="sky"]`；classic 轮播占位暖褐。
2. **`theme-boot.js` / `store.applyTheme`**：sky 写 `data-v2-theme="sky"`，不再 `removeAttribute`。
3. **Bench / bento / carousel / phone**：去掉硬编码 `rgba(72,202,228)` / slate 阴影，改挂 `--v2-*`；chip ≥11px。
4. Wizard 显式 sky 也用 cream accent（暗玻璃不叠 cyan）。
5. 静态审计新增 `--wave home-tokens` 与 **D-UID-13**。

---

## 结果

- `home-tokens`：**无 D-UID-13 P0/P1**
- 主题契约单测仍绿（含 sky 显式块）
