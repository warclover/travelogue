# LTN Dogfood AC · 2026-07-20

| 属性 | 内容 |
|------|------|
| **对应** | [PRD-LAYOUT-TRUST-NARRATIVE-V1](../PRD-LAYOUT-TRUST-NARRATIVE-V1.md) AC-B-02 / AC-D-01 / AC-D-02 / AC-D-03 |
| **机器入口** | `python scripts/ltn_dogfood_ac.py` · `travelogue/layout_contract/ltn_dogfood.py` |
| **CI fixture** | `tests/fixtures/ltn/trip.ltn_dogfood_hero_chapter.json` |
| **单测** | `tests/unit/layout_contract/test_ltn_dogfood_ac.py` |

---

## 1. 机器可复跑结果（fixture）

| AC | 口径 | 结果 |
|----|------|------|
| **AC-B-02** | hero mosaic → longshot `preserve-stack` +「一组」标记 + assetIds 守恒 | **PASS**（机器） |
| **AC-D-02** | `rhythmGap` 非全 L1/全 L2；L2 优先挂 scene/章界 | **PASS**（代理） |
| **AC-D-03** | hero mosaic 中章进度占比 ≥60%（带 `[0.35, 0.80]`） | **PASS**（fixture 1/1 @ 0.75） |
| **AC-D-01** | 小样本盲评节奏分 ≥7 | **人评待办**；工程 proxyScore 仅作提示 |

本地可选：`python scripts/ltn_dogfood_ac.py --include-demos`（有 `trips/demo-*` 时附加）。

---

## 2. 人评清单（AC-D-01 / B-02 目视）

1. 打开 Studio 双预览（网页 vs 长图，同宽 ~428）。
2. 确认 mosaic hero 在长图仍读作「一组」，而非无提示拆成单卡。
3. 盲评 3–5 本小样节奏观感（1–10），均值 **≥7** 记入本表下方。

| 评审人 | 日期 | 样本 | 节奏分 | 备注 |
|--------|------|------|--------|------|
| _待填_ | | | | |

---

## 3. 说明

- AC-D-01 **不以 proxy 替代盲评**；CI 只卡 B-02 / D-02 / D-03 机器项。
- fixture 章序刻意把 hero mosaic 放在中章，用于锁 D-03 与 beat 峰窗语义对齐。
