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

## 结论 · 产品锁（2026-08-04）

| 决策 | 内容 |
|------|------|
| **判定** | **Go · 保留** |
| **默认** | **on**（`size6` 子开关保持仓库默认 true；`landscape1_flood_reopen_after=4`） |
| **依据** | 锚点成册观感更合理；多屏 L6 + 换气后无连发；产品确认可默认打开 |
| **回滚** | `mosaic.equal_grid_admission.enabled: false`（或逐项关 size6 子开关） |
| **不跟进** | EGA M3（3:2 soft demote）仍延期，与本锁无关 |
