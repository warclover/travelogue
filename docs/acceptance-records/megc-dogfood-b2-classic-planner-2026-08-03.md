# MEGC · PR-B2 狗粮增补 · classic planner 挂点 · 2026-08-03

| 属性 | 内容 |
|------|------|
| **承接** | [megc-dogfood-2026-08-03.md](./megc-dogfood-2026-08-03.md) |
| **分支** | `feature/megc-pr-b2-legacy-finalize` |
| **配置** | dogfood knobs · `score_mul=0.62` · soft；跑完已还原本机 `config.yaml` |

## 发现（第一轮 B2 仅挂 `build_legacy_screen`）

整册 ON 仍出现 **3:2 `screen-landscape-4`**（ch-01-sc-02 · 001/006/009/010）。  
根因：经典 `_plan_one_screen` 经 `_pattern_id(landscape,4)` **直构**，不经 `build_legacy_screen`。

## 修复

`_emit_landscape_grid_with_megc`：非电影峰等权 → 降级为 landscape-3/1；电影峰仍 emit + stamp。

## 对照（修复后 re-layout）

| | OFF | ON |
|--|-----|----|
| screens | 25 | 24 |
| `landscape-4` | **1 × three_two**（001/006/009/010） | **1 × sixteen_nine**（019/021/023/025 · `gate_allow`） |
| `landscape-3` | 4 | **5**（承接降级） |
| 锚点 086/088/089 | landscape-3 | landscape-3 |

附件：`attachments/megc-dogfood-2026-08-03/b2-*-relayout-summary.json`

## 结论

| 项 | 结论 |
|----|------|
| classic + legacy 双挂点 | ✅ 3:2 等权四宫在 ON 下不再胜出 |
| 16:9 电影峰 | ✅ 仍可 `gate_allow` |
| 默认 enabled | **已转正 true**（[决策](./megc-default-on-decision-2026-08-03.md)） |
| `score_mul=0.62` | MCS soft 路径仍可保留；本册胜出主战场是 classic demote |

**签名**：Agent　2026-08-03
