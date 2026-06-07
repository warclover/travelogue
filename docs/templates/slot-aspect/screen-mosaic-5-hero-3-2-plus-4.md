# screen-mosaic-5-hero-3-2-plus-4

- displayName: 五图 · 加权轨道 hero + 四配图
- status: ga
- stage: 16:9

| slot | role | displayAspect |
|------|------|---------------|
| 0 | main | 0.8889 |
| 1 | landscape | 0.8889 |
| 2 | landscape | 0.8889 |
| 3 | landscape | 0.8889 |
| 4 | landscape | 0.8889 |

## Geometry guard (v4)

- Slot 0 main cell is tall (`displayAspect ≈ 0.89`); **landscape is forbidden** in slot 0.
- Pure 5×landscape windows fail MCS geometry; use `screen-mosaic-5-2p3l-equal` or other patterns instead.

## Rollback

- Config: `mosaic.hero_weighted_geometry_guard: false`
- Or disable template: `layout.template_engine.overrides.disable: ["screen-mosaic-5-hero-3-2-plus-4"]`
