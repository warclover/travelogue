# TPC · 本机狗粮手测记录（版式 + 导入稳定性）· 2026-07-18

| 属性 | 内容 |
|------|------|
| 日期 | 2026-07-18 |
| 分支 | `feat/tpc-template-contract-w1` |
| 关联 | [手测指南](./tpc-local-dogfood-GUIDE.md) · [缺口清单](./tpc-gap-checklist-2026-07-18.md) · mosaic harden `d79d253` |
| 本机配置 | `mosaic.template_contract.enabled=true`（gitignore `config.yaml`；仓库默认仍 false） |
| 结论 | **开发期狗粮通过** · 可合入本分支；**不**改仓库默认 on |

---

## 1. 测过的游记（抽样）

| trip / 相册 | 关注点 | 结果 |
|-------------|--------|------|
| `demo-2025` | 近景假拼图（weighted / 1l3p-rail） | 拒选后消失；重 curate 后稳定 |
| `demo-815dc906d3`（凯哥精选等） | 四图锯齿、竖图进横槽极端裁切 | 等分 2×2 + geometry 硬拒后正常 |
| 多本后续手测 | 「排版正常」口头签核 | 通过（本记录日期当天下午） |

---

## 2. 已修问题（狗粮触发）

| 现象 | 根因 | 处置 |
|------|------|------|
| 四图「假拼图 / 切条」 | 同场景人物连拍进 `prefers_burst:false` 棋盘 | MCS 近景硬拒（`near_scene_clone`） |
| 四图横缝/竖缝不齐、非四分之一 | W3 `2l2p-weighted` / editorial 用 2:3·3:2 轨道 | 改为等分 2×2；`landscape-4` 提高默认权重 |
| 左下角竖图被裁成肩膀特写 | 等分格全是横槽 AR≈1.78，仍 cover 塞竖图 | `slot_geometry` 硬拒竖进宽槽；2L2P 棋盘不再胜出 |
| 导入失败（通用文案） | Windows `os.replace(trip.json)` → WinError 5/32 | 退避重试 + 就地覆写兜底；错误码 `E_TRIP_SAVE_BUSY` |

---

## 3. 指南清单对照

| # | 项 | 状态 | 备注 |
|---|----|------|------|
| F1 | config `contract=True` | ✅ | 本机 dogfood |
| F2 | 混向相册 re-curate / 合理 fallback | ✅ | 2L2P 等分棋盘被 geometry 拒后走 landscape-4 / rail / hero 等 |
| F3 | `layout_compare` + 手记 ≥3 行 | ⬜ | 建议合入前补跑 2～3 本并写 jsonl |
| F4 | hero-70 / 1L3P 至少各看一本 | 🟡 | 手测中出现过；未单独截图归档 |
| F5 | poster_bric 导出 + screens 不变 | ⬜ | 未在本轮强制验收 |
| F6 | 关回 `enabled=false` 对照 | ⬜ | 合入前建议做一次 |

---

## 4. 已知限制（刻意不在本轮做）

- 等分 2×2 **不再**承载「杂志感不等分 2L2P」；真竖槽棋盘需另设计再开。
- 仓库默认 `template_contract.enabled` **保持 false**（AC-TPC-01）。
- AC-TPC-12 BQP / 正式盲评 / 删除 `main_eligibility.py` 仍按缺口清单阻塞。

---

## 5. 建议下一步

1. 合入本分支前：补 F3（compare 手记）、F5 或 F6 任选一项对照。
2. 已合入后：开独立小 PR 仅当「导入稳定性」已随本分支带走时可跳过。
3. 默认开：等 F3 + corpus/盲评，不在本狗粮结论内。
