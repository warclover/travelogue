# IMPLEMENTATION · 一句话选风格 LVP V1

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-LAYOUT-VIBE-PICKER-V1.md](./PRD-LAYOUT-VIBE-PICKER-V1.md) **v0.2.0** |
| **验收** | [ACCEPTANCE-LAYOUT-VIBE-PICKER-V1.md](./ACCEPTANCE-LAYOUT-VIBE-PICKER-V1.md) |
| **评审** | [lvp-layout-vibe-picker-v1-review-2026-08-03.md](./acceptance-records/lvp-layout-vibe-picker-v1-review-2026-08-03.md) |
| **状态** | **M0 ✅ · M1 ✅ · M2 代码 ✅（AC-06/BLK-03 签字待） · M3 延期** |
| **更新日期** | 2026-08-03 |

## 列车

| 里程碑 | 内容 | 状态 |
|--------|------|------|
| **M0** | 七席 · PRD v0.2 · ACCEPTANCE/IMPL 拆文 | ✅ |
| **M1** | vibe → mosaic 剖面解析 · `trip.studio.layoutVibe` · 单测 AC-01/02/03/07/08 | ✅ |
| **M2** | 精修 Sheet 两卡 UI · 实验确认 · 三册狗粮 | 🔶 UI/确认 ✅ · 狗粮 ☐ |
| **M3** | 与 CAD 同屏编组（可选） | ⏸ 延期 |

## M1 触点（已落地）

| 区域 | 路径 | 动作 |
|------|------|------|
| 剖面 | `travelogue/config/layout_vibe.py` | `resolve_layout_vibe` / `mosaic_profile_for_vibe` / `apply_layout_vibe_to_config` |
| 持久化 | `trip.studio.layoutVibe` + `schemas/trip.schema.json` `$defs.tripStudio` | `set_trip_layout_vibe` / `read_trip_layout_vibe` |
| 应用 | `travelogue/services/layout.py` · `travelogue/curation/curate.py` | 排版前覆盖 mosaic 三开关；fail-open `magazine_default` |
| 仓库 GA | `config.yaml.example` | MTSO `selection_optimization.enabled: true`（与推荐 vibe 字节级对齐） |
| 测试 | `tests/unit/config/test_layout_vibe.py` | AC-01/02/03/07/08 + BLK-05 |

## M2 触点（已落地 · 待狗粮）

| 区域 | 路径 | 动作 |
|------|------|------|
| API | `POST …/layout-vibe` · `layout_vibe_handlers.py` | 写 vibe → layout → render（job）；实验无确认 400 |
| UI | `features.js` `mountLayoutVibeControls` · Sheet「这本」区 | 两卡 + `toolbarConfirm` |
| 弱提示 | `maybeShowLayoutVibeImportHint` · FirstSuccess 打 pending | **仅导入后**打开预览提示一次；Sheet 可「不再提示」 |
| Entry | `studio_entry` `layoutVibe` / `layoutVibeOptions` | 预览入口回读 |
| 等待面 | `applyVibe` → Task Dock `updateExporting` | 复用精选重排等待面 |
| 帮助 | Help **H8** · SHD-02（H7 留给 NAS 写作引擎） | 不链 LSE admin |
| 线框 | `docs/wireframes/layout-vibe-picker-f1-wireframe.html` | SHD-01 |
| 测试 | `tests/unit/web/test_layout_vibe_m2.py` | AC-04/05 + 路由 |

## 禁令

- 不改 MTSO/MEGC/MSA 公式  
- 不映射 SSG look  
- 不写 LSE capability  
- 仓库默认不因 LVP 改变（推荐卡 ≡ 现网 GA）
