# UI Detail Wave5 · Capability + Narrow gate + Lightbox · 2026-07-22

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | active |
| **合同** | [UI-DETAIL-CONTRACT-V0.md](../UI-DETAIL-CONTRACT-V0.md) D-UID-11 |
| **复跑** | `python scripts/studio_ui_detail_static_audit.py --wave cap-narrow-lightbox` |

---

## 做了什么

1. **恢复** `studio-modal.css` `:root` 的 `--studio-panel-*`（Wave2 token 回潮修复）。
2. 新建 `capability-card.css`（经 `studio-home-v2.css` 引入）；去掉 JS 内联森林色；标题 → 15px。
3. Narrow gate：薄荷 `#eef6f1` / rem 字阶 → cream `#f5f0e8` + px（20/13/14）。
4. Lightbox：占位冷绿渐变 → 暖褐；caption/关闭对齐 cream。
5. 静态审计新增 `--wave cap-narrow-lightbox` 与 **D-UID-11**。

---

## 结果

- `cap-narrow-lightbox`：**无 D-UID-11 P0/P1**
- 能力卡合同单测仍绿
