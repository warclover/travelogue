# TPC · 本机狗粮手测记录（版式 + 导入稳定性）· 2026-07-18

| 属性 | 内容 |
|------|------|
| 日期 | 2026-07-18 |
| 分支 | `feat/tpc-template-contract-w1` |
| 关联 | [手测指南](./tpc-local-dogfood-GUIDE.md) · [缺口清单](./tpc-gap-checklist-2026-07-18.md) · mosaic harden `d79d253` · trip-save `6c2bd8d` |
| 本机配置 | `mosaic.template_contract.enabled=true`（gitignore `config.yaml`；仓库默认仍 false） |
| 结论 | **开发期狗粮通过（F1–F6）** · 可开 PR 合入；**不**改仓库默认 on |

---

## 1. 测过的游记（抽样）

| trip / 相册 | 关注点 | 结果 |
|-------------|--------|------|
| `demo-2025` | 近景假拼图；compare on/off | 拒选后稳定；compare **0/72** 变化 → `prefer: tie` |
| `demo-815dc906d3`（张智慧精选2） | 四图锯齿、竖进横槽 | 等分 + geometry 硬拒后正常；compare **0/140** → `prefer: tie` |
| `demo-65db8fd377`（凯哥拍摄精选4） | 导入锁文件；海报 | 导入可完成；poster_bric 成功且 screens 未变 |

手记原文：[tpc-layout-compare-notes-2026-07-18.jsonl](./tpc-layout-compare-notes-2026-07-18.jsonl)  
Compare 产物（本机，gitignore）：`.cache/tpc-layout-compare/<tripId>/`

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
| F2 | 混向相册 re-curate / 合理 fallback | ✅ | 仍可见 `landscape-4` / `hero-70` / `1l3p-rail` / `5-2p3l-rail`；假 2L2P 已消 |
| F3 | `layout_compare` + 手记 ≥3 行 | ✅ | 三本；差异率均为 0%；手记已提交 |
| F4 | hero-70 / 1L3P 至少各看一本 | ✅ | `demo-2025` hero-70；`demo-815dc906d3` 1l3p-rail |
| F5 | poster_bric 导出 + screens 不变 | ✅ | `demo-65db8fd377` → PNG + `runs/gcs-poster-bric.json`；fingerprint 不变 |
| F6 | 关回 `enabled=false` 对照 | ✅ | compare 即 off vs on；本批三本版面序列一致（`prefer: tie`） |

---

## 4. Compare 摘要（F3 / F6）

| tripId | screens | changed% | 解读 |
|--------|--------:|---------:|------|
| demo-2025 | 72 | 0% | on≈off；硬化后 W3 不等分棋盘不再制造差异 |
| demo-815dc906d3 | 140 | 0% | 同上；rail/hero 仍可出现（槽位几何合法） |
| demo-65db8fd377 | 41 | 0% | 同上 |

含义：当前狗粮配置下，**打开 contract 相对关闭无明显回归**；差异主要来自此前已合入的几何/近景门闩（对 on/off 两侧同样生效）。

---

## 5. 已知限制（刻意不在本轮做）

- 等分 2×2 **不再**承载「杂志感不等分 2L2P」；真竖槽棋盘需另设计再开。
- 仓库默认 `template_contract.enabled` **保持 false**（AC-TPC-01）。
- AC-TPC-12 BQP / 正式盲评 / 删除 `main_eligibility.py` 仍按缺口清单阻塞。

---

## 6. 建议下一步

1. 开 PR 合入本分支（开发期狗粮已签）。
2. 默认开：等 corpus/盲评，不在本结论内。
