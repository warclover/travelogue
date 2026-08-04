# ACCEPTANCE · 一句话选风格 LVP V1

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-LAYOUT-VIBE-PICKER-V1.md](./PRD-LAYOUT-VIBE-PICKER-V1.md) **v0.2.0** |
| **实施** | [IMPLEMENTATION-LAYOUT-VIBE-PICKER-V1.md](./IMPLEMENTATION-LAYOUT-VIBE-PICKER-V1.md) |
| **评审** | [lvp-layout-vibe-picker-v1-review-2026-08-03.md](./acceptance-records/lvp-layout-vibe-picker-v1-review-2026-08-03.md) |
| **状态** | **结案** · M0 ✅ · M1 ✅ · M2 ✅（AC-04/05/06；BLK-03/04 关闭）· M3 延期 |
| **更新日期** | 2026-08-04 |

## 自动化 / 合同门

| AC | 断言 | 里程碑 | 状态 |
|----|------|--------|------|
| AC-LVP-01 | `magazine_default` 解析 ≡ 仓库 GA（MTSO on · MEGC on · MSA off） | M1 | ✅ `tests/unit/config/test_layout_vibe.py::test_ac_lvp_01_magazine_default_equals_repo_ga` |
| AC-LVP-02 | `fit_photo_experimental` 仅多开 `slot_adaptation.enabled` | M1 | ✅ `tests/unit/config/test_layout_vibe.py::test_ac_lvp_02_fit_photo_only_enables_msa` |
| AC-LVP-03 | 写入 `trip.studio.layoutVibe` 后重载仍在 | M1 | ✅ `tests/unit/config/test_layout_vibe.py::test_ac_lvp_03_layout_vibe_persists_roundtrip` |
| AC-LVP-07 | 不改写 SSG look / LSE capability flags | M1 | ✅ `tests/unit/config/test_layout_vibe.py::test_ac_lvp_07_does_not_rewrite_ssg_look_or_lse_flags` |
| AC-LVP-08 | 清除 vibe 或无字段 → 行为 ≡ `magazine_default` | M1 | ✅ `tests/unit/config/test_layout_vibe.py::test_ac_lvp_08_clear_or_missing_equals_magazine_default` |
| AC-LVP-04 | UI 无算法缩写（帮助链除外） | M2 | ✅ `tests/unit/web/test_layout_vibe_m2.py`（options + features.js 源码门） |
| AC-LVP-05 | 实验 vibe 无二次确认不可保存 | M2 | ✅ `tests/unit/web/test_layout_vibe_m2.py::test_ac_lvp_05_*` + UI `toolbarConfirm` |
| AC-LVP-06 | 三册狗粮；无加权屏可记「差异小」 | M2 | ✅ [lvp-dogfood-2026-08-03-DRAFT](./acceptance-records/lvp-dogfood-2026-08-03-DRAFT.md)（三册差异小 · 2026-08-04） |

## 优先级链（BLK-LVP-05）

`trip.studio.layoutVibe` > 进程配置 overlay > 仓库 `config.yaml.example` 默认。

单测：`tests/unit/config/test_layout_vibe.py::test_blk_lvp_05_trip_vibe_beats_process_overlay`。

## BLK-LVP-03 确认文案（**已补签 · 2026-08-04**）

- 标题：`改用「更贴照片比例」？`
- 正文：须含「章节页数或篇幅可能变化」+「可改回推荐」
- 现网默认见 `layout_vibe_handlers.EXPERIMENTAL_CONFIRM_*` / `features.js` 确认模态
- 线框：[wireframes/layout-vibe-picker-f1-wireframe.html](./wireframes/layout-vibe-picker-f1-wireframe.html)
- **签字**：合同要件已核对通过；与 AC-LVP-06 同日结案

## AC-LVP-06

✅ 已结案：见 [acceptance-records/lvp-dogfood-2026-08-03-DRAFT.md](./acceptance-records/lvp-dogfood-2026-08-03-DRAFT.md) · 指标 [lvp-dogfood-metrics-2026-08-04.json](./acceptance-records/lvp-dogfood-metrics-2026-08-04.json)。
