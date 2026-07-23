# SSG · 默认 on 决策（F-SSG-M3-04 / D-SSG-20）

| 属性 | 内容 |
|------|------|
| **日期** | 2026-07-23 |
| **PRD** | [PRD-SMART-SHOT-GROUPING-V1.md](../PRD-SMART-SHOT-GROUPING-V1.md) |
| **状态** | **Hold · 不改仓库默认** |

## 决策

| 开关 | 仓库默认 | 理由 |
|------|----------|------|
| `vision.enabled` | **false**（既有） | 默认强制 vision on 另决策；狗粮路径显式打开 |
| `shotGrouping.enabled` | **auto** | 有 scene 簇才写强分镜；无 vision 时 fail-open 空分镜 |
| `shotGrouping.look.enabled` | **auto** | CLIP 可用才跑 look；不可用则保留 scene |

## 转正条件（未满足前禁止改默认）

1. 实拍混导 + 换装盲评按 [ssg-local-dogfood-GUIDE](./ssg-local-dogfood-GUIDE.md) **Pass**（日期版记录）  
2. AC-SSG-05 / 11 在实册上复验（允许 ±0.05 一次）  
3. 另开 PR 改默认，**禁止**塞进功能列车

## 狗粮路径

使用 [`docs/config-ssg-dogfood.example.yaml`](../config-ssg-dogfood.example.yaml) 本机覆盖即可。
