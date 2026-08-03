# IMPLEMENTATION · 一句话选风格 LVP V1

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-LAYOUT-VIBE-PICKER-V1.md](./PRD-LAYOUT-VIBE-PICKER-V1.md) **v0.2.0** |
| **验收** | [ACCEPTANCE-LAYOUT-VIBE-PICKER-V1.md](./ACCEPTANCE-LAYOUT-VIBE-PICKER-V1.md) |
| **评审** | [lvp-layout-vibe-picker-v1-review-2026-08-03.md](./acceptance-records/lvp-layout-vibe-picker-v1-review-2026-08-03.md) |
| **状态** | **M0 ✅ · M1 ✅ · M2 待 BLK · M3 延期** |
| **更新日期** | 2026-08-03 |

## 列车

| 里程碑 | 内容 | 状态 |
|--------|------|------|
| **M0** | 七席 · PRD v0.2 · ACCEPTANCE/IMPL 拆文 | ✅ |
| **M1** | vibe → mosaic 剖面解析 · `trip.studio.layoutVibe` · 单测 AC-01/02/03/07/08 | ✅ |
| **M2** | 精修 Sheet 两卡 UI · 实验确认 · 三册狗粮 | ☐ |
| **M3** | 与 CAD 同屏编组（可选） | ⏸ 延期 |

## M1 触点（已落地）

| 区域 | 路径 | 动作 |
|------|------|------|
| 剖面 | `travelogue/config/layout_vibe.py` | `resolve_layout_vibe` / `mosaic_profile_for_vibe` / `apply_layout_vibe_to_config` |
| 持久化 | `trip.studio.layoutVibe` + `schemas/trip.schema.json` `$defs.tripStudio` | `set_trip_layout_vibe` / `read_trip_layout_vibe` |
| 应用 | `travelogue/services/layout.py` · `travelogue/curation/curate.py` | 排版前覆盖 mosaic 三开关；fail-open `magazine_default` |
| 仓库 GA | `config.yaml.example` | MTSO `selection_optimization.enabled: true`（与推荐 vibe 字节级对齐） |
| 测试 | `tests/unit/config/test_layout_vibe.py` | AC-01/02/03/07/08 + BLK-05 |

## M2 建议触点

| 区域 | 路径 | 动作 |
|------|------|------|
| UI | `templates/studio/preview-toolbar/features.js` | 封面区同级两卡 |
| 应用 | 复用 apply-layout（`core.js`） | 不新造进度面 |

## 禁令

- 不改 MTSO/MEGC/MSA 公式  
- 不映射 SSG look  
- 不写 LSE capability  
- 仓库默认不因 LVP 改变（推荐卡 ≡ 现网 GA）
