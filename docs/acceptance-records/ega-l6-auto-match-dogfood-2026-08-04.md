# EGA L6 自动匹配狗粮 · 2026-08-04

| 项 | 值 |
|----|-----|
| 册 | `trips/demo-0ebda73294` |
| 流程 | fine_craft + unlock structure + `curate --layout web` |
| size6 默认 | soften / prefer / quota_exempt = true；flood_reopen_after = 4 |

## 直方图

| pattern | 结果 |
|---------|------|
| screen-landscape-6 | **6** |
| screen-landscape-4 | 0 |
| screen-mosaic-4-hero-70-sidebar | 0 |
| screen-landscape-1 | 26 |
| screens（总） | 83 |
| max consecutive L6 | **1** |

## 结论

P0–P3 生效：成册出现多屏 L6，且 L6 后换气避免连发。  
回滚：`mosaic.equal_grid_admission.enabled: false`。
