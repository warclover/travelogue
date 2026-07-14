# Bookends Engine V1 · 验收记录

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-BOOKENDS-ENGINE-V1.md](./PRD-BOOKENDS-ENGINE-V1.md) **v0.2.1** |
| **ADR** | [adr/017-bookends-engine.md](./adr/017-bookends-engine.md) |
| **实施清单** | [IMPLEMENTATION-BOOKENDS-ENGINE-V1.md](./IMPLEMENTATION-BOOKENDS-ENGINE-V1.md) |
| **更新日期** | 2026-07-13 |
| **门禁结论** | **工程封板维持** · DE-BE-01/02 + FE-BE-07 已补；产品封板仍待真实相册盲评或 [限期 waiver](./acceptance-records/bookends-product-seal-waiver.md) |

---

## 0. 金样 trip 列表（B0）

本地无 `trips/` 时以 **pytest fixture / 合成套件** 作为行为金样锚点；真实相册填入 `docs/acceptance-records/bookends-closing-albums.json`。

| 用途 | trip 路径 / id / fixture | 备注 |
|------|--------------------------|------|
| Opening 金样 1 | `schemas/fixtures/trip.render_golden.json` | V6 / `load_golden_trip()` |
| Opening 金样 2 | `tests/unit/curation/test_cover_styles_v6_golden.py` | 各 style boost/penalty 金样 |
| Opening 金样 3 | `tests/unit/curation/test_cover_scoring_v2.py` + gates | cover_scoring_v2 行为锚 |
| Closing · unused | `test_bookends_dogfood_b2a.py`（df-01） | AC-BE-12 |
| Closing · 极小册 degraded | `test_bookends_dogfood_b2a.py`（df-03-tiny） | AC-BE-11 / Colophon |
| Closing · PAIR-H3 人像 | `test_bookends_closing_pairing.py::test_pair_h3` | AC-BE-13 |
| 压字硬闸 fixture | `test_bookends_closing_pairing.py::test_opening_hard_gate_blocks_title_unsafe_top1` | AC-BE-14 |
| Studio 合页半自动 | `test_bookends_studio_ac_b2b.py` | AC-BE-20..25（无真实 trip） |
| 成对正反例图例 | [acceptance-records/bookends-pair-examples-de-be-01.html](./acceptance-records/bookends-pair-examples-de-be-01.html) | DE-BE-01 |
| 合页线框 | [wireframes/studio-bookends-panel-v1-wireframe.html](./wireframes/studio-bookends-panel-v1-wireframe.html) | DE-BE-02 |
| 盲评相册清单 | `docs/acceptance-records/bookends-closing-albums.json` | AC-BE-40..41；`tripDir` 待填 |
| 产品封板 waiver | [acceptance-records/bookends-product-seal-waiver.md](./acceptance-records/bookends-product-seal-waiver.md) | R-BE-18 限期 |

---

## 1. 实施范围

| 阶段 | 内容 | 状态 |
|------|------|------|
| B0 | ADR-017 + IMPLEMENTATION + 本验收骨架 | ✅ 文档 |
| B0 | 金样 trip 列表 + 盲评基线导出 | ✅ 合成锚点 + 导出骨架 + DE-BE-01/02；真实相册待填 |
| B1 | Opening facade + `bookendsLock` + 零回归 | ✅ |
| B2a | Closing + Pairing + 挂点 + 无图 Colophon + 压字闸 | ✅ **工程封板（自动化）** |
| B2b | Studio「封面与封底」合页 | ✅ 代码就绪 · ✅ 半自动 AC · ✅ FE-BE-07 · ⬜ 手工走查 |
| B3 | quiet / VL 接口（实验室页未做） | ✅ 最小交付 · ⏭ 实验室页 |

---

## 2. 验收勾选（对齐 PRD §11）

### 2.1 引擎与兼容（B1）

| ID | 判据 | 结果 |
|----|------|------|
| AC-BE-01 | `resolve_opening` 合法 Decision | ✅ |
| AC-BE-02 | Opening 金样零回归 | ✅（V6 / cover_scoring_v2 pytest） |
| AC-BE-03 | 无 force 不改已锁 opening | ✅ |
| AC-BE-04 | re-export 与 api 等价 | ✅ |
| AC-BE-05 | 无 screens 时 closing 不写假分 | ✅（`ClosingPendingError`） |

### 2.2 Pairing / Closing（B2a）

| ID | 判据 | 结果 |
|----|------|------|
| AC-BE-10 | PAIR-H1 封面≠封底 | ✅ |
| AC-BE-11 | 无候选 → null + degraded；不回退封面 | ✅ |
| AC-BE-12 | post-layout 偏好 unused | ✅ |
| AC-BE-13 | 人像封面避同主体近景封底 | ✅（PAIR-H3） |
| AC-BE-14 | 压字硬闸改 Top1（B2a；B1 不测） | ✅ |

### 2.3 Studio（B2b）

| ID | 判据 | 结果 |
|----|------|------|
| AC-BE-20..25 | 合页 / 换图 / 级联 / mobile 说明 | ✅ 半自动（含 FE-BE-07 状态条）· ⬜ 手工走查（需真实 trip） |

### 2.4 渲染（B2a）

| ID | 判据 | 结果 |
|----|------|------|
| AC-BE-30 | 有图时封底出现 | ✅（既有 render 套件 + cover-closing） |
| AC-BE-31 | null 无封底大图（Colophon 保留） | ✅ |
| AC-BE-32 | longshot 与现网一致 | ✅（既有 longshot 门控未改） |

### 2.5 人工（产品封板）

| ID | 判据 | 结果 |
|----|------|------|
| AC-BE-40 | 封面 A 率 ≥ 冻结基线 | ⬜ / [waiver 模板](./acceptance-records/bookends-product-seal-waiver.md) |
| AC-BE-41 | 封底收束偏好 ≥60% | ⬜ / waiver |
| AC-BE-42 | 压字可读抽样 | ⬜ |

---

## 3. 自动化命令

见 [IMPLEMENTATION-BOOKENDS-ENGINE-V1.md](./IMPLEMENTATION-BOOKENDS-ENGINE-V1.md) §5。

---

## 4. 封板记录

| 轨道 | 日期 | 结论 | 签字 |
|------|------|------|------|
| 工程封板（B1+B2a） | 2026-07-13 | 自动化 AC 通过（dogfood T-B2A-07 可并行） | — |
| 产品封板（+B2b+盲评/waiver） | — | — | — |
