# AS-PFM-03 · 工坊系列页数与 id 对账（2026-08-21）

| 属性 | 内容 |
|------|------|
| **合同** | [PRD-PORTFOLIO-FOLIO-MODE-V1.md](../PRD-PORTFOLIO-FOLIO-MODE-V1.md) §8.3 / §12.3 |
| **状态** | **对账完成 · 不升格** |
| **范围** | `docs/templates/reserve/series/*.yaml`（8 本）对照现网 LTE `page-*`（75 张）与正式目录（仅 `magazine-16-standard`） |
| **证据** | `tests/unit/layout_engine/test_atelier_series_audit.py` |
| **红线** | 运行时加载器仍拒绝 reserve（ISO-05）。本纪要由测试读工坊，不把 `folio-*` 拷进 `editorial_series/series/` |

---

## 1. 结论

历史挡门「`folio-24-standard` 标了 32 页」**已不在现网工坊文件里**。八本试刊的 `id` 页数、`pageCount`、`sequence` 长度三者一致，`folio-16` 的脸序与正式 P0 `magazine-16-standard` 对齐。

**不入库。** 全部仍是 `status: sketch`。芯片继续只投影现网 SKU（16）。P1 8/24/32 要等产品选档 + 升格包，不是这次对账的出口。

---

## 2. 柜面清单

| 文件 | id | pageCount | 序长 | photo_span | 升格？ |
|------|----|-----------|------|------------|--------|
| folio-8-standard.yaml | folio-8-standard | 8 | 8 | [24, 40] | 否 · 仍 sketch；正式 id 须改 `magazine-8-standard` |
| folio-12-standard.yaml | folio-12-standard | 12 | 12 | [36, 60] | 否 |
| folio-16-standard.yaml | folio-16-standard | 16 | 16 | [48, 80] | **已升格为 P0**（正式目录，不读本文件） |
| folio-20-standard.yaml | folio-20-standard | 20 | 20 | [60, 100] | 否 |
| folio-24-standard.yaml | folio-24-standard | **24** | 24 | [72, 120] | 否 · 历史 `pageCount: 32` 已纠正 |
| folio-28-standard-r2.yaml | folio-28-standard-r2 | 28 | 28 | [84, 140] | 否 |
| folio-32-standard-r2.yaml | folio-32-standard-r2 | 32 | 32 | [96, 160] | 否 · 含未收脸 `page-10-grid-port` |
| folio-36-standard.yaml | folio-36-standard | 36 | 36 | [108, 180] | 否 · 超 `max_pages` 32；含 `page-10-grid-port` |

---

## 3. 升格检查单（下次运营用）

硬拒：

1. id 仍是 `folio-*`
2. `pageCount` ≠ id 中的页数 ≠ `sequence` 长度
3. `status` 不是 `official` / `promote-ready`
4. `faceHint` 不在 LTE（今日仅 `page-10-grid-port`）
5. 页数 > 32

通过后改 id 为 `magazine-{n}-{density}`，放入 `travelogue/layout_engine/editorial_series/series/`，芯片会自己长出来。

---

## 4. 不宣称

- 不宣称 P1 系列已入现网
- 不宣称 AC-PFM-25「像一本」已过
- 不打开 `homepage_entry`
