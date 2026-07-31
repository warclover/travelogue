# ACCEPTANCE · 等权拼图几何合同 V1（MEGC）

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-MOSAIC-EQUAL-GRID-CONTRACT-V1.md](./PRD-MOSAIC-EQUAL-GRID-CONTRACT-V1.md) **v0.2.0** |
| **实施** | [IMPLEMENTATION-MOSAIC-EQUAL-GRID-CONTRACT-V1.md](./IMPLEMENTATION-MOSAIC-EQUAL-GRID-CONTRACT-V1.md) |
| **评审** | [megc-equal-grid-contract-v1-review-2026-07-31.md](./acceptance-records/megc-equal-grid-contract-v1-review-2026-07-31.md) · **Conditional Go** |
| **DOC-STATUS** | **active** |
| **更新日期** | 2026-07-31 |

> **用法**：DOM/几何断言以自动化为准；选型闸以 raw mosaic capture / 单测为准。  
> **正交**：MEGC ⊥ MSA 轨道求解；**禁止**用「等权槽贴 1.50」作为 MSA AC。  
> **勾选**：✅ 已锁 · ☑ 合同已齐待合码 · ☐ 未做。

---

## 0. 编码启动门（M0）

| ID | 检查项 | 结果 |
|----|--------|------|
| **AC-MEGC-W0-01** | PRD v0.2.0 + 七席 Conditional Go | ✅ |
| **AC-MEGC-W0-02** | 本 ACCEPTANCE + IMPLEMENTATION 已拆 | ✅ |
| **AC-MEGC-W0-03** | 列车 M0→M1→M2→M3；禁单 PR 塞满；M3 默认延期 | ✅ |
| **AC-MEGC-W0-04** | A/B/C 模板清单与 MSA/MTSO 边界写清；D-11 web 主责 | ✅ |
| **AC-MEGC-W0-05** | 七席 Conditional Go（2026-07-31） | ✅ |
| **AC-MEGC-W0-06** | M1 合码前：BLK-02 CSS 名单签字 · BLK-06 trips 同步策略 | ✅ BLK-02 见 IMPL §1.4；BLK-06：render 拷模板 CSS（trips 拷贝仅狗粮） |
| **AC-MEGC-W0-07** | M2 合码前：BLK-03 soft 默认 · BLK-07 MSA-OFF 仍可算峰 | ☐ |

---

## 1. 可测常量

| 常量 | 值 | 用途 |
|------|-----|------|
| 舞台/网格高度容差 | **1px** | AC-01 |
| 峰判定 | 复用 MSA（容差 0.08 · 单峰 ≥0.60） | AC-04～06 |
| `allow_mixed_median_min` | **1.70**（O-02 暂定） | mixed 放行 |
| soft `penalty` | **8.0**（暂定） | AC-04 |

---

## 2. M1 / PR-A · 渲染舞台合同

| ID | 期望 | 结果 |
|----|------|------|
| **AC-MEGC-01** | `landscape-4` fixture：3×cover + 1×contain；加载完成后 `gridH ≤ stageH + 1px`；下排槽 `bottom ≤ stage.bottom + 1px` | ✅ Playwright `demo-2019` assets 086/088/089/091：`gridH=stageH` · `bottomOk`（2026-07-31） |
| **AC-MEGC-02** | 任选 1 个 `screen-mosaic-*` contain fixture：行为仍为格内信箱、舞台不因 contain 释高；相对 MEGC 前基线不回退 | ☑ mosaic 既有守卫未回退（`test_mosaic_fixed_stage_*`） |
| **AC-MEGC-03** | `portrait-2` / `portrait-3` contain 屏仍为 intrinsic 高（非强制 16:9 裁盒） | ☑ `portrait-4` intrinsic 守卫 + MEGC 排除名单；portrait-2/3 未列入 INCLUDE |

```text
建议夹具：合成 HTML 或 trips/demo-2019 ch-02-sc-06 强制一槽 contain 后 Playwright evaluate
```

---

## 3. M2 / PR-B · 选型闸

| ID | 期望 | 结果 |
|----|------|------|
| **AC-MEGC-04** | 全 3:2 四横窗 · `selection_gate.enabled`：soft 时 A 类得分下降且日志 `gate_penalize`；hard 时 A 类不出现在最终 screen | ☐ |
| **AC-MEGC-05** | 全 16:9 四横窗：`landscape-4` 仍可合法胜出；日志 `gate_allow` | ☐ |
| **AC-MEGC-06** | 2L2P / `portrait-2-landscape-2` 候选 + 非电影峰：硬纪律生效（拒或加倍罚） | ☐ |
| **AC-MEGC-07** | raw 含 `megcEnabled` / `megcOutcome` / `megcLandPeak` / `megcPatternId` | ☐ |
| **AC-MEGC-07b** | `slot_adaptation.enabled=false` 时 MEGC 闸仍能得到同一套 `landPeak`（只读 `build_msa_profile`）· BLK-07 | ☐ |
| **AC-MEGC-08** | 父开关 OFF 时选型路径与基线一致（允许已合入的 CSS hotfix 单独注明） | ☐ |

```powershell
# 实施后填真实模块路径
python -m pytest tests/unit/layout_engine/test_megc_pr_b.py -q
```

---

## 4. M3 / PR-C · 释舞台 / 整页信箱 + 盲评

| ID | 期望 | 结果 |
|----|------|------|
| **AC-MEGC-09** | 若启用 P-释：非 16:9 峰等权屏 `aspect-ratio` 非强制 16:9；格 AR 贴近 \(r^*±0.08\)；导出/preview 同实例 | ☐ |
| **AC-MEGC-09b** | 若启用 P-函：整页 whitespace ≤ 与 MSA 同源预算；与 P-释不同时默认 on | ☐ |
| **AC-MEGC-10** | 三分峰狗粮（单反 3:2 / 手机 4:3 / 混排）盲评记录入 acceptance-records；默认 on 另决策 | ☐ |

---

## 5. 禁令（防假绿）

| ID | 禁令 |
|----|------|
| **AC-MEGC-X01** | 不得将「等权四宫槽 displayAspect→1.50」写成 MSA 或 MEGC 的轨道求解 AC |
| **AC-MEGC-X02** | 不得以「上下行 fr 不等」解释本债而不测 stage/grid 高度 |
| **AC-MEGC-X03** | 不得放宽竖进宽槽来「改善」2L2P |

---

## 6. 实机锚点（建议狗粮）

| 锚点 | 期望（M2 后） |
|------|----------------|
| `demo-2019` · 原 `ch-02-sc-06` 资产窗 | 不再稳定以砍头砍脚的 `landscape-4` cover 呈现；或等权仅在电影峰 |
| 同窗强制 contain 回归 | AC-01 绿 |
