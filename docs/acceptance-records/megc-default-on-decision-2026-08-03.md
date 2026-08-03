# MEGC · 默认 `equal_grid_contract.enabled` 决策

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-03 |
| **决策** | **改为默认 `true`（产品默认开）** |
| **范围** | 父开关 + 既有 P-选（soft `score_mul` / classic·legacy 自愈）；**不含** M3 P-释 / P-函 |
| **依据** | PR-A/B/B2 已合入 master；demo-2019 狗粮 + 开发者实册手测可接受 |
| **关联** | [狗粮](./megc-dogfood-2026-08-03.md) · [B2 classic](./megc-dogfood-b2-classic-planner-2026-08-03.md) · [ACCEPTANCE](../ACCEPTANCE-MOSAIC-EQUAL-GRID-CONTRACT-V1.md) · [PRD v0.2.0](../PRD-MOSAIC-EQUAL-GRID-CONTRACT-V1.md) |

## 决议

1. 仓库默认：`mosaic.equal_grid_contract.enabled: true`（`EqualGridContractConfig` · `config.yaml.example`）。  
2. `selection_gate` 保持 soft_penalty · `score_mul=0.62` · `allow_peaks=[sixteen_nine]`。  
3. **M3 仍延期**：`release_stage_on_narrow_peak` / `page_letterbox` 默认 false。  
4. 旧 trip 须 **重新 layout/curate** 才体现选型变化；PR-A CSS 舞台合同与父开关无关，重渲即可。  
5. 本机若要临时关闭：在 `config.yaml` 显式 `enabled: false`（样例见 [`config-megc-dogfood.example.yaml`](../config-megc-dogfood.example.yaml) 可改作 opt-out）。

## 接受依据（摘要）

| 证据 | 结论 |
|------|------|
| PR-A 几何 | contain 等权 `gridH=stageH`，下排不裁 |
| PR-B 闸语义 | 3:2 → `gate_penalize`；16:9 → `gate_allow` |
| PR-B2 + classic 挂点 | ON 下无 3:2 `landscape-4`，电影峰仍可四宫 |
| 开发者实册 | 输出可接受 → 转正 |

## 已知副作用 / 未做

| 项 | 说明 |
|----|------|
| pacing | ON 可能略改屏数（demo 狗粮 25→24 量级）；可接受 |
| AC-10 正式三分峰盲评 | 未另开盲评轮；本决议以实册可接受 + 自动化/狗粮为准 |
| MCS soft 胜出率精细标定 | classic/legacy 拒发已覆盖主旁路；`score_mul` 暂保持 0.62 |

## 状态

| 项 | 状态 |
|----|------|
| 默认改为 true | ✅ 本决议 |
| 代码 / example / DOC-STATUS 回写 | ✅ 同 PR |
| M3 默认 on | ☐ 不做 |

**签名**：开发者实册 + Agent 代记录　2026-08-03
