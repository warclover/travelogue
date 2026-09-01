# EA-01 源码模板几何体检

| 属性 | 内容 |
|------|------|
| 日期 | 2026-09-01 |
| 任务 | [收敛任务清单.md](../收敛任务清单.md) `EA-01` |
| 源目录 | `travelogue/layout_templates/templates` |
| 排除 | `dist/`, `.version_history/`, `_*.yaml` |
| 检查数 | **123** |
| 三态 | 健康 = 无几何 error/warn；可疑 = 仅几何 warn；破损 = 几何 error/block |
| 不计入三态 | 槽位数量冻结、usage 文档、命名、16:9 main eligibility 等 **政策** 项 |
| 复跑 | `python scripts/ea01_template_geometry_audit.py --write-markdown docs/acceptance-records/ea-01-template-geometry-2026-09-01.md` |

## 总览

- 健康 **79**
- 可疑 **43**
- 破损 **1**

| 族 | 健康 | 可疑 | 破损 | 合计 |
|----|------|------|------|------|
| journal | 16 | 31 | 0 | 47 |
| portfolio | 63 | 12 | 1 | 76 |

## 怎么读这份报告

1. **破损极少不等于竖版已就绪。** 本检查只看 16:9 源几何能否自洽（空槽、越界、重叠、角色、裁切可行性）。`stage.variants` 仍只声明 aspect，竖版槽位几何尚未存在。
2. **唯一破损 `page-10-grid-port` 是 schema 天花板，不是槽位重叠。** `layout_template.schema.json` 把 `photoCount` / `mix` 上限写成 9、`slots.index` 上限写成 8（游记时代的 9 槽合同）。10 槽页的 YAML 轨道可能仍合法，但合同未放行。`CV-01` 不要拿它当健康基线；它倒适合当难迁移对照。
3. **`screen-*` 可疑偏多，主因是 16:9 舞台上的竖槽必然偏离 AR 阶梯。** 例如三列竖图槽 displayAspect≈0.889，不在 `{2/3, 3/4, 1, 4/3, 3/2, 16/9}` 上。这是舞台比例与角色的结构性张力，不是 YAML 写坏。
4. **`square` 槽被现行校验器按横图推荐区间 `[1.25, 2.2]` 衡量**，所以 1:1 英雄页会进可疑。正方形槽几何成立；这是角色分组问题，不是空槽或重叠。
5. **政策备注（文末）不影响三态**，绝大多数是 `usage.siblings` 未互指。

## `CV-01` 选样提示（不代替拍板）

| 角色 | 建议（均须为健康态） | 理由 |
|------|----------------------|------|
| 常用单图 | `page-1-hero-land-right` | 健康、1 槽、作品集高频 |
| 常用混合 | `page-2-1p1l` | 健康、横竖各一 |
| 难迁移 | `page-9-grid-land-wide` | 健康、宽幅九宫，竖屏几乎必然重编 |
| `screen-*` 对照 | `screen-portrait-2-gallery` | 健康、有声明留白 |

不要从可疑集合里选试点：那会把「AR 阶梯预警」和「竖版迁不了」混在一起。

## 破损

| id | 族 | status | 槽数 | 原因 |
|----|----|--------|------|------|
| `page-10-grid-port` | portfolio | experimental | 10 | EA-01-SCHEMA mix.portrait: 10 is greater than the maximum of 9; EA-01-SCHEMA photoCount.max: 10 is greater than the maximum of 9; EA-01-SCHEMA photoCount.min: 10 is greater than the maximum of 9; EA-01-SCHEMA slots: [{'index': 0, 'rect': [2, 2, 2, 2], 'role': 'portrait', 'fit': 'cover'}, {'index': 1, 'rect': [4, 4, 2, 2], 'role': 'portrait', 'fit…; EA-01-SCHEMA slots.9.index: 9 is greater than the maximum of 8 |

## 可疑

| id | 族 | status | 槽数 | 警告 |
|----|----|--------|------|------|
| `screen-editorial-4mix` | journal | deprecated | 4 | V-P16-04 slot 1 portrait displayAspect 1.778 outside [0.5, 1.0]; V-P16-04 slot 2 portrait displayAspect 1.778 outside [0.5, 1.0] |
| `screen-landscape-1-portrait-1` | journal | deprecated | 2 | V-P16-04 slot 0 landscape displayAspect 1.138 outside recommended [1.25, 2.2]; V-P16-13 slot 0 displayAspect 1.138 not on AR ladder (Δ=0.138) |
| `screen-landscape-2-asymmetric-left` | journal | deprecated | 2 | V-P16-04 slot 0 landscape displayAspect 1.086 outside recommended [1.25, 2.2]; V-P16-04 slot 1 landscape displayAspect 1.117 outside recommended [1.25, 2.2]; V-P16-13 slot 0 displayAspect 1.086 not on AR ladder (Δ=0.086); V-P16-13 slot 1 displayAspect 1.117 not on AR ladder (Δ=0.117) |
| `screen-landscape-2-portrait-1` | journal | deprecated | 3 | V-P16-13 slot 2 displayAspect 0.889 not on AR ladder (Δ=0.111) |
| `screen-landscape-3-asymmetric-left` | journal | deprecated | 3 | V-P16-04 slot 0 landscape displayAspect 1.119 outside recommended [1.25, 2.2]; V-P16-13 slot 0 displayAspect 1.119 not on AR ladder (Δ=0.119) |
| `screen-landscape-3-asymmetric-right` | journal | deprecated | 3 | V-P16-04 slot 2 landscape displayAspect 1.119 outside recommended [1.25, 2.2]; V-P16-13 slot 2 displayAspect 1.119 not on AR ladder (Δ=0.119) |
| `screen-landscape-6` | journal | experimental | 6 | V-P16-04 slot 0 landscape displayAspect 1.185 outside recommended [1.25, 2.2]; V-P16-04 slot 1 landscape displayAspect 1.185 outside recommended [1.25, 2.2]; V-P16-04 slot 2 landscape displayAspect 1.185 outside recommended [1.25, 2.2]; V-P16-04 slot 3 landscape displayAspect 1.185 outside recommended [1.25, 2.2]; V-P16-04 slot 4 landscape displayAspect 1.185 outside recommended [1.25, 2.2]; V-P16-04 slot 5 landscape displayAspect 1.185 outside recommended [1.25, 2.2]; V-P16-13 slot 0 displayAspect 1.185 not on AR ladder (Δ=0.148); V-P16-13 slot 1 displayAspect 1.185 not on AR ladder (Δ=0.148); V-P16-13 slot 2 displayAspect 1.185 not on AR ladder (Δ=0.148); V-P16-13 slot 3 displayAspect 1.185 not on AR ladder (Δ=0.148); V-P16-13 slot 4 displayAspect 1.185 not on AR ladder (Δ=0.148); V-P16-13 slot 5 displayAspect 1.185 not on AR ladder (Δ=0.148) |
| `screen-mosaic-4-1l3p-rail` | journal | deprecated | 4 | V-P16-13 slot 1 displayAspect 0.889 not on AR ladder (Δ=0.111); V-P16-13 slot 2 displayAspect 0.889 not on AR ladder (Δ=0.111); V-P16-13 slot 3 displayAspect 0.889 not on AR ladder (Δ=0.111) |
| `screen-mosaic-4-2l2p-weighted` | journal | deprecated | 4 | V-P16-04 slot 1 portrait displayAspect 1.778 outside [0.5, 1.0]; V-P16-04 slot 2 portrait displayAspect 1.778 outside [0.5, 1.0] |
| `screen-mosaic-4-2p2l-portrait-bookends` | journal | experimental | 4 | V-P16-04 slot 1 landscape displayAspect 1.185 outside recommended [1.25, 2.2]; V-P16-04 slot 2 landscape displayAspect 1.185 outside recommended [1.25, 2.2]; V-P16-13 slot 1 displayAspect 1.185 not on AR ladder (Δ=0.148); V-P16-13 slot 2 displayAspect 1.185 not on AR ladder (Δ=0.148) |
| `screen-mosaic-4-hero-70-sidebar` | journal | ga | 4 | V-P16-13 slot 1 displayAspect 1.600 not on AR ladder (Δ=0.100); V-P16-13 slot 2 displayAspect 1.600 not on AR ladder (Δ=0.100); V-P16-13 slot 3 displayAspect 1.600 not on AR ladder (Δ=0.100) |
| `screen-mosaic-5-1p4l-portrait-center-rails` | journal | experimental | 5 | V-P16-04 slot 1 landscape displayAspect 1.185 outside recommended [1.25, 2.2]; V-P16-04 slot 2 landscape displayAspect 1.185 outside recommended [1.25, 2.2]; V-P16-04 slot 3 landscape displayAspect 1.185 outside recommended [1.25, 2.2]; V-P16-04 slot 4 landscape displayAspect 1.185 outside recommended [1.25, 2.2]; V-P16-13 slot 1 displayAspect 1.185 not on AR ladder (Δ=0.148); V-P16-13 slot 2 displayAspect 1.185 not on AR ladder (Δ=0.148); V-P16-13 slot 3 displayAspect 1.185 not on AR ladder (Δ=0.148); V-P16-13 slot 4 displayAspect 1.185 not on AR ladder (Δ=0.148) |
| `screen-mosaic-5-1p4l-portrait-hero` | journal | experimental | 5 | V-P16-04 slot 1 landscape displayAspect 3.200 > 2.5; V-P16-04 slot 2 landscape displayAspect 3.200 > 2.5; V-P16-04 slot 3 landscape displayAspect 3.200 > 2.5; V-P16-04 slot 4 landscape displayAspect 3.200 > 2.5; V-P16-13 slot 1 displayAspect 3.200 not on AR ladder (Δ=1.422); V-P16-13 slot 2 displayAspect 3.200 not on AR ladder (Δ=1.422); V-P16-13 slot 3 displayAspect 3.200 not on AR ladder (Δ=1.422); V-P16-13 slot 4 displayAspect 3.200 not on AR ladder (Δ=1.422) |
| `screen-mosaic-5-2p3l-portrait-hero-rail` | journal | experimental | 5 | V-P16-04 slot 1 portrait displayAspect 0.267 outside [0.5, 1.0]; V-P16-13 slot 1 displayAspect 0.267 not on AR ladder (Δ=0.400); V-P16-13 slot 2 displayAspect 1.600 not on AR ladder (Δ=0.100); V-P16-13 slot 3 displayAspect 1.600 not on AR ladder (Δ=0.100); V-P16-13 slot 4 displayAspect 1.600 not on AR ladder (Δ=0.100) |
| `screen-mosaic-5-2portrait-3land-balanced` | journal | deprecated | 5 | V-P16-04 slot 0 portrait displayAspect 1.778 outside [0.5, 1.0]; V-P16-04 slot 1 portrait displayAspect 1.778 outside [0.5, 1.0]; V-P16-04 slot 4 landscape displayAspect 3.556 > 2.5; V-P16-13 slot 2 displayAspect 0.889 not on AR ladder (Δ=0.111); V-P16-13 slot 4 displayAspect 3.556 not on AR ladder (Δ=1.778) |
| `screen-mosaic-5-3p2l-portrait-hero-lp-stack` | journal | experimental | 5 | V-P16-04 slot 1 landscape displayAspect 0.889 outside recommended [1.25, 2.2]; V-P16-04 slot 3 landscape displayAspect 0.889 outside recommended [1.25, 2.2]; V-P16-13 slot 1 displayAspect 0.889 not on AR ladder (Δ=0.111); V-P16-13 slot 3 displayAspect 0.889 not on AR ladder (Δ=0.111) |
| `screen-mosaic-5-3p2l-portrait-hero-quad` | journal | experimental | 5 | V-P16-13 slot 1 displayAspect 0.571 not on AR ladder (Δ=0.095); V-P16-13 slot 2 displayAspect 0.571 not on AR ladder (Δ=0.095) |
| `screen-mosaic-5-3portrait-2land-balanced` | journal | deprecated | 5 | V-P16-04 slot 3 landscape displayAspect 3.556 > 2.5; V-P16-13 slot 0 displayAspect 0.889 not on AR ladder (Δ=0.111); V-P16-13 slot 1 displayAspect 0.889 not on AR ladder (Δ=0.111); V-P16-13 slot 2 displayAspect 0.889 not on AR ladder (Δ=0.111); V-P16-13 slot 3 displayAspect 3.556 not on AR ladder (Δ=1.778) |
| `screen-mosaic-5-hero-3-2-plus-4` | journal | ga | 5 | V-P16-04 slot 1 landscape displayAspect 0.889 outside recommended [1.25, 2.2]; V-P16-04 slot 2 landscape displayAspect 0.889 outside recommended [1.25, 2.2]; V-P16-04 slot 3 landscape displayAspect 0.889 outside recommended [1.25, 2.2]; V-P16-04 slot 4 landscape displayAspect 0.889 outside recommended [1.25, 2.2]; V-P16-13 slot 1 displayAspect 0.889 not on AR ladder (Δ=0.111); V-P16-13 slot 2 displayAspect 0.889 not on AR ladder (Δ=0.111); V-P16-13 slot 3 displayAspect 0.889 not on AR ladder (Δ=0.111); V-P16-13 slot 4 displayAspect 0.889 not on AR ladder (Δ=0.111) |
| `screen-mosaic-5-main-landscape-2portrait-2land` | journal | deprecated | 5 | V-P16-13 slot 1 displayAspect 0.889 not on AR ladder (Δ=0.111) |
| `screen-mosaic-5-main-portrait-3land` | journal | ga | 5 | V-P16-13 slot 1 displayAspect 0.889 not on AR ladder (Δ=0.111) |
| `screen-portrait-1-landscape-1` | journal | deprecated | 2 | V-P16-04 slot 1 landscape displayAspect 1.138 outside recommended [1.25, 2.2]; V-P16-13 slot 1 displayAspect 1.138 not on AR ladder (Δ=0.138) |
| `screen-portrait-1-landscape-2` | journal | ga | 3 | V-P16-13 slot 0 displayAspect 0.889 not on AR ladder (Δ=0.111) |
| `screen-portrait-1` | journal | ga | 1 | V-P16-13 slot 0 displayAspect 0.562 not on AR ladder (Δ=0.104) |
| `screen-portrait-2-landscape-2` | journal | ga | 4 | V-P16-04 slot 0 portrait displayAspect 1.778 outside [0.5, 1.0]; V-P16-04 slot 3 portrait displayAspect 1.778 outside [0.5, 1.0] |
| `screen-portrait-2` | journal | ga | 2 | V-P16-13 slot 0 displayAspect 0.889 not on AR ladder (Δ=0.111); V-P16-13 slot 1 displayAspect 0.889 not on AR ladder (Δ=0.111) |
| `screen-portrait-3` | journal | ga | 3 | V-P16-13 slot 0 displayAspect 0.188 not on AR ladder (Δ=0.479); V-P16-13 slot 1 displayAspect 0.188 not on AR ladder (Δ=0.479); V-P16-13 slot 2 displayAspect 0.188 not on AR ladder (Δ=0.479) |
| `screen-portrait-4` | journal | ga | 4 | V-P16-13 slot 0 displayAspect 0.562 not on AR ladder (Δ=0.104); V-P16-13 slot 1 displayAspect 0.562 not on AR ladder (Δ=0.104); V-P16-13 slot 2 displayAspect 0.562 not on AR ladder (Δ=0.104); V-P16-13 slot 3 displayAspect 0.562 not on AR ladder (Δ=0.104) |
| `screen-portrait-6` | journal | deprecated | 6 | V-P16-13 slot 0 displayAspect 0.375 not on AR ladder (Δ=0.292); V-P16-13 slot 1 displayAspect 0.375 not on AR ladder (Δ=0.292); V-P16-13 slot 2 displayAspect 0.375 not on AR ladder (Δ=0.292); V-P16-13 slot 3 displayAspect 0.375 not on AR ladder (Δ=0.292); V-P16-13 slot 4 displayAspect 0.375 not on AR ladder (Δ=0.292); V-P16-13 slot 5 displayAspect 0.375 not on AR ladder (Δ=0.292) |
| `screen-portrait-9` | journal | deprecated | 9 | V-P16-13 slot 0 displayAspect 0.562 not on AR ladder (Δ=0.104); V-P16-13 slot 1 displayAspect 0.562 not on AR ladder (Δ=0.104); V-P16-13 slot 2 displayAspect 0.562 not on AR ladder (Δ=0.104); V-P16-13 slot 3 displayAspect 0.562 not on AR ladder (Δ=0.104); V-P16-13 slot 4 displayAspect 0.562 not on AR ladder (Δ=0.104); V-P16-13 slot 5 displayAspect 0.562 not on AR ladder (Δ=0.104); V-P16-13 slot 6 displayAspect 0.562 not on AR ladder (Δ=0.104); V-P16-13 slot 7 displayAspect 0.562 not on AR ladder (Δ=0.104); V-P16-13 slot 8 displayAspect 0.562 not on AR ladder (Δ=0.104) |
| `screen-portrait-grid-8` | journal | deprecated | 8 | V-P16-13 slot 0 displayAspect 0.281 not on AR ladder (Δ=0.385); V-P16-13 slot 1 displayAspect 0.281 not on AR ladder (Δ=0.385); V-P16-13 slot 2 displayAspect 0.281 not on AR ladder (Δ=0.385); V-P16-13 slot 3 displayAspect 0.281 not on AR ladder (Δ=0.385); V-P16-13 slot 4 displayAspect 0.281 not on AR ladder (Δ=0.385); V-P16-13 slot 5 displayAspect 0.281 not on AR ladder (Δ=0.385); V-P16-13 slot 6 displayAspect 0.281 not on AR ladder (Δ=0.385); V-P16-13 slot 7 displayAspect 0.281 not on AR ladder (Δ=0.385) |
| `page-1-hero-square-right` | portfolio | experimental | 1 | V-P16-04 slot 0 square displayAspect 1.000 outside recommended [1.25, 2.2] |
| `page-2-1p1s` | portfolio | experimental | 2 | V-P16-04 slot 1 square displayAspect 1.000 outside recommended [1.25, 2.2] |
| `page-2-1s1p` | portfolio | experimental | 2 | V-P16-04 slot 0 square displayAspect 1.000 outside recommended [1.25, 2.2] |
| `page-2-pair-land-ultra` | portfolio | experimental | 2 | V-P16-04 slot 0 landscape displayAspect 3.765 > 2.5; V-P16-04 slot 1 landscape displayAspect 3.765 > 2.5; V-P16-13 slot 0 displayAspect 3.765 not on AR ladder (Δ=1.987); V-P16-13 slot 1 displayAspect 3.765 not on AR ladder (Δ=1.987) |
| `page-2-pair-square` | portfolio | experimental | 2 | V-P16-04 slot 0 square displayAspect 1.000 outside recommended [1.25, 2.2]; V-P16-04 slot 1 square displayAspect 1.000 outside recommended [1.25, 2.2] |
| `page-3-1s2l-left` | portfolio | experimental | 3 | V-P16-04 slot 0 square displayAspect 1.000 outside recommended [1.25, 2.2] |
| `page-3-1s2l-right` | portfolio | experimental | 3 | V-P16-04 slot 2 square displayAspect 1.000 outside recommended [1.25, 2.2] |
| `page-3-1s2l-wide-left` | portfolio | experimental | 3 | V-P16-04 slot 0 square displayAspect 1.000 outside recommended [1.25, 2.2] |
| `page-3-1s2l-wide-right` | portfolio | experimental | 3 | V-P16-04 slot 2 square displayAspect 1.000 outside recommended [1.25, 2.2] |
| `page-3-2p1s` | portfolio | experimental | 3 | V-P16-04 slot 1 square displayAspect 1.000 outside recommended [1.25, 2.2] |
| `page-6-grid-land` | portfolio | experimental | 6 | V-P16-04 slot 0 landscape displayAspect 1.220 outside recommended [1.25, 2.2]; V-P16-04 slot 1 landscape displayAspect 1.220 outside recommended [1.25, 2.2]; V-P16-04 slot 2 landscape displayAspect 1.220 outside recommended [1.25, 2.2]; V-P16-04 slot 3 landscape displayAspect 1.220 outside recommended [1.25, 2.2]; V-P16-04 slot 4 landscape displayAspect 1.220 outside recommended [1.25, 2.2]; V-P16-04 slot 5 landscape displayAspect 1.220 outside recommended [1.25, 2.2]; V-P16-13 slot 0 displayAspect 1.220 not on AR ladder (Δ=0.113); V-P16-13 slot 1 displayAspect 1.220 not on AR ladder (Δ=0.113); V-P16-13 slot 2 displayAspect 1.220 not on AR ladder (Δ=0.113); V-P16-13 slot 3 displayAspect 1.220 not on AR ladder (Δ=0.113); V-P16-13 slot 4 displayAspect 1.220 not on AR ladder (Δ=0.113); V-P16-13 slot 5 displayAspect 1.220 not on AR ladder (Δ=0.113) |
| `page-8-grid-land` | portfolio | experimental | 8 | V-P16-04 slot 0 landscape displayAspect 1.062 outside recommended [1.25, 2.2]; V-P16-04 slot 1 landscape displayAspect 1.062 outside recommended [1.25, 2.2]; V-P16-04 slot 2 landscape displayAspect 1.062 outside recommended [1.25, 2.2]; V-P16-04 slot 3 landscape displayAspect 1.062 outside recommended [1.25, 2.2]; V-P16-04 slot 4 landscape displayAspect 1.062 outside recommended [1.25, 2.2]; V-P16-04 slot 5 landscape displayAspect 1.062 outside recommended [1.25, 2.2]; V-P16-04 slot 6 landscape displayAspect 1.062 outside recommended [1.25, 2.2]; V-P16-04 slot 7 landscape displayAspect 1.062 outside recommended [1.25, 2.2] |

## 健康（可供 `CV-01` 选样）

下列全部为 16:9 基线几何健康。`CV-01` 仍须从中挑 1 个预判难迁移件（宽幅/多列/密排）。

`page-*` 健康 63 个：

`page-1-hero-land-right`, `page-1-hero-land-ultra`, `page-1-hero-land-wide`, `page-1-hero-port`, `page-2-1l1p-wide`, `page-2-1l1p`, `page-2-1p1l-wide`, `page-2-1p1l`, `page-2-pair-land`, `page-2-pair-port`, `page-3-2l1p-hero-left`, `page-3-2l1p-hero-right`, `page-3-2l1p-hero-wide-left`, `page-3-2l1p-hero-wide-right`, `page-3-2l1p-left`, `page-3-2l1p-right`, `page-3-2l1p-wide-left`, `page-3-2l1p-wide-right`, `page-3-land`, `page-3-port-hero-left`, `page-3-port-hero-right`, `page-3-port`, `page-4-1l3l-left`, `page-4-1l3l-right`, `page-4-1l3l-wide-left`, `page-4-1l3l-wide-right`, `page-4-1p3l-left`, `page-4-1p3l-right`, `page-4-1p3l-wide-left`, `page-4-1p3l-wide-right`, `page-4-2p2l-cross`, `page-4-2p2p`, `page-4-grid-land-wide`, `page-4-grid-land`, `page-4-port`, `page-5-1p4l-center`, `page-5-1p4l-left`, `page-5-1p4l-right`, `page-5-1p4p-center`, `page-5-1p4p-left`, `page-5-1p4p-right`, `page-5-3p2l-center-flip`, `page-5-3p2l-center`, `page-5-3p2l-left`, `page-5-3p2l-right`, `page-5-3p2l-stack-center`, `page-5-3p2l-stack-left`, `page-5-3p2l-stack-right`, `page-5-3p2l-wide`, `page-6-1l5l-wide-left`, `page-6-1l5l-wide-right`, `page-6-2l4p-left`, `page-6-2l4p-right`, `page-6-2l4p-wide-flip`, `page-6-2l4p-wide`, `page-6-4l2p`, `page-7-1p6l-center`, `page-7-1p6l-left`, `page-7-1p6l-right`, `page-8-2l6p-flip`, `page-8-2l6p`, `page-8-grid-port`, `page-9-grid-land-wide`

`screen-*` 健康 16 个：

`screen-full-frame`, `screen-landscape-1`, `screen-landscape-2-overlap-bltr`, `screen-landscape-2-overlap-tlbr`, `screen-landscape-2`, `screen-landscape-3`, `screen-landscape-4`, `screen-landscape-9`, `screen-mosaic-5-2p3l-equal`, `screen-mosaic-5-2p3l-rail`, `screen-mosaic-5-main-hero-plus-4`, `screen-mosaic-6-main-hero-plus-5`, `screen-portrait-2-asymmetric-left`, `screen-portrait-2-asymmetric-right`, `screen-portrait-2-gallery`, `screen-portrait-3-editorial`

## 政策备注（不影响三态）

| id | 备注 |
|----|------|
| `screen-editorial-4mix` | V-P16-U03 sibling screen-portrait-3-editorial does not reference screen-editorial-4mix ba… |
| `screen-landscape-1-portrait-1` | V-P16-U03 sibling screen-portrait-1-landscape-2 does not reference screen-landscape-1-por… |
| `screen-landscape-1` | V-P16-U03 sibling screen-landscape-2 does not reference screen-landscape-1 back |
| `screen-landscape-2-overlap-bltr` | V-P16-U03 sibling screen-landscape-2 does not reference screen-landscape-2-overlap-bltr b… |
| `screen-landscape-2-portrait-1` | V-P16-U03 sibling screen-portrait-1-landscape-2 does not reference screen-landscape-2-por… |
| `screen-landscape-2` | V-P16-S04 stack template skips 3×3 displayAspect ladder; V-P16-U03 sibling screen-portrait-1-landscape-2 does not reference screen-landscape-2 back |
| `screen-landscape-3-asymmetric-left` | V-P16-U03 sibling screen-landscape-3 does not reference screen-landscape-3-asymmetric-lef… |
| `screen-landscape-3-asymmetric-right` | V-P16-U03 sibling screen-landscape-3 does not reference screen-landscape-3-asymmetric-rig… |
| `screen-landscape-3` | V-P16-S04 stack template skips 3×3 displayAspect ladder; V-P16-U03 sibling screen-landscape-4 does not reference screen-landscape-3 back |
| `screen-landscape-4` | V-P16-U03 sibling screen-landscape-6 does not reference screen-landscape-4 back; V-P16-U03 sibling screen-portrait-2-landscape-2 does not reference screen-landscape-4 back |
| `screen-mosaic-4-1l3p-rail` | V-P16-U03 sibling screen-portrait-3 does not reference screen-mosaic-4-1l3p-rail back; V-P16-U03 sibling screen-mosaic-4-hero-70-sidebar does not reference screen-mosaic-4-1l3p… |
| `screen-mosaic-4-2l2p-weighted` | V-P16-U03 sibling screen-landscape-4 does not reference screen-mosaic-4-2l2p-weighted back; V-P16-U03 sibling screen-portrait-2-landscape-2 does not reference screen-mosaic-4-2l2p-w…; V-P16-U03 sibling screen-editorial-4mix does not reference screen-mosaic-4-2l2p-weighted … |
| `screen-mosaic-4-2p2l-portrait-bookends` | V-P16-U03 sibling screen-portrait-1-landscape-2 does not reference screen-mosaic-4-2p2l-p…; V-P16-U03 sibling screen-portrait-2-landscape-2 does not reference screen-mosaic-4-2p2l-p… |
| `screen-mosaic-4-hero-70-sidebar` | V-P16-U03 sibling screen-mosaic-5-hero-3-2-plus-4 does not reference screen-mosaic-4-hero…; V-P16-U03 sibling screen-mosaic-5-main-hero-plus-4 does not reference screen-mosaic-4-her… |
| `screen-mosaic-5-1p4l-portrait-hero` | V-P16-U03 sibling screen-mosaic-5-main-portrait-3land does not reference screen-mosaic-5-…; V-P16-U03 sibling screen-portrait-1 does not reference screen-mosaic-5-1p4l-portrait-hero… |
| `screen-mosaic-5-2p3l-equal` | V-P16-U03 sibling screen-mosaic-5-main-portrait-3land does not reference screen-mosaic-5-… |
| `screen-mosaic-5-2p3l-portrait-hero-rail` | V-P16-U03 sibling screen-mosaic-5-2p3l-rail does not reference screen-mosaic-5-2p3l-portr…; V-P16-U03 sibling screen-mosaic-5-2p3l-equal does not reference screen-mosaic-5-2p3l-port… |
| `screen-mosaic-5-2p3l-rail` | V-P16-U03 sibling screen-mosaic-5-2p3l-equal does not reference screen-mosaic-5-2p3l-rail…; V-P16-U03 sibling screen-mosaic-5-main-portrait-3land does not reference screen-mosaic-5-… |
| `screen-mosaic-5-3p2l-portrait-hero-lp-stack` | V-P16-U03 sibling screen-mosaic-5-2p3l-portrait-hero-rail does not reference screen-mosai… |
| `screen-mosaic-5-3p2l-portrait-hero-quad` | V-P16-U03 sibling screen-mosaic-5-2p3l-portrait-hero-rail does not reference screen-mosai…; V-P16-U03 sibling screen-mosaic-5-3portrait-2land-balanced does not reference screen-mosa… |
| `screen-mosaic-5-3portrait-2land-balanced` | V-P16-U03 sibling screen-portrait-3 does not reference screen-mosaic-5-3portrait-2land-ba… |
| `screen-mosaic-5-hero-3-2-plus-4` | V-P16-U03 sibling screen-mosaic-5-main-portrait-3land does not reference screen-mosaic-5-… |
| `screen-mosaic-5-main-landscape-2portrait-2land` | V-P16-MAIN-01 slot 0 main targets 16:9; constraints.eligibility (or legacy mainSlotPolicy) re… |
| `screen-mosaic-5-main-portrait-3land` | V-P16-U03 sibling screen-mosaic-5-main-hero-plus-4 does not reference screen-mosaic-5-mai… |
| `screen-portrait-1-landscape-1` | V-P16-U03 sibling screen-portrait-1-landscape-2 does not reference screen-portrait-1-land… |
| `screen-portrait-1-landscape-2` | V-P16-U03 sibling screen-portrait-2-landscape-2 does not reference screen-portrait-1-land… |
| `screen-portrait-3` | V-P16-U03 sibling screen-portrait-2 does not reference screen-portrait-3 back |
| `screen-portrait-4` | V-P16-U03 sibling screen-portrait-3 does not reference screen-portrait-4 back |
| `screen-portrait-grid-8` | V-P16-U03 sibling screen-portrait-9 does not reference screen-portrait-grid-8 back |
