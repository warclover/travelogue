# UI Detail Wave4 · wait-tips tip-tone · 2026-07-22

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | active |
| **合同** | [UI-DETAIL-CONTRACT-V0.md](../UI-DETAIL-CONTRACT-V0.md) D-UID-10 |
| **复跑** | `python scripts/studio_ui_detail_static_audit.py --wave wait-tips` |

---

## 做了什么

1. `.v2-import-panel` 增加暗玻璃 token：`--wt-ink/muted/gold/gold-soft/cream`。
2. Import source 去掉 cyan `#90e0ef` → `--wt-gold-soft`；字号 10→11。
3. wait-tips `data-tone` 五色彩虹（cyan/green/blue/orange）收敛为 gold / cream / white 浓淡。
4. 标签字号 10→11；title/body/dot 挂 `--wt-*`。
5. 静态审计新增 `--wave wait-tips` 与 **D-UID-10**。

---

## 结果

- `wait-tips` 波次：**无 D-UID-10**
- 契约单测 + wait-tips 合同测试仍绿
