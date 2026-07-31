# PRD-MOSAIC-EQUAL-GRID-CONTRACT-V1 · 跨职能评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-MOSAIC-EQUAL-GRID-CONTRACT-V1.md](../PRD-MOSAIC-EQUAL-GRID-CONTRACT-V1.md)（**MEGC** · 等权拼图几何合同） |
| **模板来源** | [megc-equal-grid-contract-v1-review-TEMPLATE.md](./megc-equal-grid-contract-v1-review-TEMPLATE.md) |
| **相邻挡门** | [MSA](../PRD-MOSAIC-SLOT-ADAPTATION-V1.md) · [MTSO](../PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) · [P16](../PRD-PHASE16-layout-template-engine.md) · [MGQ](../PRD-MCS-GEOMETRIC-QUALITY-V1.md) · [TPC](../PRD-TEMPLATE-CONTRACT-V1.md) |
| **验收 / 实施** | [ACCEPTANCE…](../ACCEPTANCE-MOSAIC-EQUAL-GRID-CONTRACT-V1.md) · [IMPLEMENTATION…](../IMPLEMENTATION-MOSAIC-EQUAL-GRID-CONTRACT-V1.md) |
| **评审版本** | **v0.1.0 Draft** → Must-Fix 回写后升 **v0.2.0** |
| **日期** | 2026-07-31 |
| **结论** | **有条件通过（Conditional Go）** |
| **编码** | ☑ **可 Kickoff M0**（决策回写）　☑ **可 Kickoff M1 / PR-A（CSS）**（关闭 BLK-02 签字清单后合码）　□ M2 待 BLK-03/06/07　□ M3 延期默认 |
| **参评角色（七席）** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版（LTE·装裱）· 用户体验（狗粮手测） |
| **评审方式** | 分席只读 PRD §0～§5 · D/O 表 + **对照现网**（`slot_display_aspect` · `journal-screens.css` 1601–1648 · MSA 白名单 · `demo-2019` ch-02-sc-06） |
| **记录人** | 七席联合纪要（跨职能模拟联评 · 基于 2026-07-30 实机债 + 2026-07-31 代码复核 + PRD v0.1.0） |
| **本纪要状态** | **已结案 · Conditional Go** · **PRD v0.2.0 已回写** |
| **审查基线** | 等权 16:9 格 + contain→auto 撑破 · MSA 加权调轨（等权明确不做） |

---

## 0. 会前宣读（主持人）

1. **切口**：等权格 **调轨无效**；MEGC = CSS 舞台合同 + 选型闸 + 可选释舞台。  
2. **实锤**：`demo-2019` `ch-02-sc-06` — 非「上挤下」，是扁槽 + contain 撑破。  
3. **勿重开**：舞台全书改 3:2、把 `landscape-4` 塞进 MSA `solve_tracks`、SoftCollage、放宽竖进宽槽。  
4. **本场必拍**：D-00/01/03/06/09 · O-01/03/05 · CSS 排除名单。  
5. **列车**：先 PR-A CSS，再 PR-B 闸；禁单 PR 塞满。

---

## 1. 总评（一句话）

> **七席一致 Conditional Go：等权 ⊥ 加权的分治成立，D-00 数学边界与 demo 实锤足以立项；P-选为主路径正确。开工前必须钉死三件事——（1）固定舞台 pattern 的 CSS 白/黑名单签字，避免误伤 portrait/stack；（2）trips 内 `journal-screens.css` 同步策略；（3）MSA profile 父 OFF 时 MEGC 仍可只读算峰。M0 立即回写；M1 CSS 可 Kickoff（O-05 允许先于父开关）；M2 合码挡在 soft 默认与 peak 只读 AC；M3（P-释/P-函）默认延期，先看 P-选是否够用。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | **Conditional Go** | 用户债真实；P-选保护单反又不毁 16:9 电影窗；同意 soft 先跑，反对一上来 hard 抽空等权密度 |
| **算法** | **Conditional Go** | D-00 证明正确，禁止假绿；峰复用 MSA 阈值 OK，但须 AC：MSA OFF 时仍能算 `landPeak` |
| **架构** | **Conditional Go** | MEGC ⊥ MSA / MTSO 边界清晰；须补 **mobile 变体范围**（M1–M2 主责 web 16:9）与 CSS 单源同步 |
| **开发** | **Conditional Go** | PR-A 可开；1601–1607 与 1612 注释自相矛盾属实；排除名单必须 pattern 级写死，不能只靠「感觉」 |
| **测试 / QA** | **Conditional Go** | AC-01 DOM 高度断言可测；要 CI Playwright/夹具，禁止只靠手眼；X01～X03 禁令须进验收正文（已有 → 升为合码挡） |
| **视觉 / 排版 · 装裱** | **Conditional Go** | 支持格内纸色 contain（继承 BLK-06）；P-释改屏高会打断 16:9 阅读节奏 → **M3 默认延期** |
| **用户体验 · 狗粮手测** | **Conditional Go** | 「下面缺一块」比「略扁」更伤信任，CSS 应先合；闸上要保留电影四宫满幅，避免矫枉过正 |

**汇总**：**七席 7/7 Conditional Go**。  
- **M0**：可 Kickoff（回写 v0.2）。  
- **M1 合码**：BLK-MEGC-02（排除名单）关闭后 **可合**；O-05 **允许** CSS 先于父开关。  
- **M2 合码**：BLK-MEGC-03/06/07 关闭前 **不批**。  
- **M3**：默认 **延期**（O-03 = 延期）；P-选不够再用 P-释。

**对齐评分**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→根因完整度 | **9** | Q1–Q5 / ①②③ 分层清楚；口语误判已纠正 |
| 与 MSA/MTSO 边界 | **9** | D-00/07/08 写死；禁假绿 |
| 工程可开工性 | **7** | M1 清晰；M2 依赖打分挂点与 peak 只读 |
| AC 可测性 / 防假绿 | **7** | X01～X03 好；缺 MSA-OFF peak 与 trips 同步 AC |
| 视觉/装裱可签核性 | **6** | CSS 排除名单未签字前不批「无回归合入」 |

---

## 3. 事实核查（代码核对）

| # | 假设 | 会中 |
|---|------|------|
| **F-01～F-03** | `displayAspect` 公式 · landscape-4 恒 1.778 · 等权调轨无效 | ✅ **属实** |
| **F-04～F-05** | `--2x2:has(contain)→auto`；mosaic 已保护 | ✅ **属实**（`journal-screens.css` 1601–1648） |
| **F-06** | demo-2019 contain 撑破裁底 | ✅ **属实**（2026-07-30 DOM：stage 802 / grid 953） |
| **F-07** | MSA 白名单不含等权四宫 | ✅ **属实**（`msa_solve.MSA_M1_PATTERN_WHITELIST`） |
| **F-08～F-09** | landscape-2/3 CSS-primary；landscape-6 非同型 | ✅ **属实** |
| **D-00** | 等权等面积 ⇒ 槽 AR≡舞台 AR | ✅ **属实 · 冻结** |

**新增事实（评审发现）**

| # | 事实 | 影响 |
|---|------|------|
| **F-10** | CSS 注释写「Cover 2×2 (landscape-4 …) keep their stage box」（约 L1612），但通用规则 L1601–1607 **仍对所有 `--2x2:has(contain)` 释高** | 注释与行为矛盾；PR-A 必须改规则而非改注释了事 |
| **F-11** | 多 trip 目录存在 `journal-screens.css` 拷贝（如 `trips/demo-2019`、`trips/linzhi`） | 只改 templates 可能狗粮看不到；须同步合同（BLK-06） |
| **F-12** | `portrait-2-landscape-2` 竖槽 `fit: auto`，横槽 cover；等权格仍全是 16:9 | D-06 硬纪律必要；不能只闸横等权 |

---

## 4. 全场共识

1. **等权 ⊥ 加权（MSA）**；禁止「等权贴 1.50」假绿。  
2. **固定舞台上 contain 不得改网格外尺寸**（D-01）；与 mosaic 保护对齐。  
3. **主路径 = P-选**；P-释/P-函 **默认延期**（先验证 P-选）。  
4. **CSS hotfix 允许先于 MEGC 父开关**（O-05 = 允许）。  
5. **混向等权严于纯横等权**（D-06）。  
6. **M1–M2 主责 web 16:9**；mobile 9:16 等权另立变体说明，不阻塞 PR-A。  
7. **soft_penalty 为 M2 默认**（O-01）；硬拒留作狗粮后开关。

---

## 5. Must-Fix（阻塞）

| ID | 议题 | 要求（冻结一字面） | 挡 | 状态 |
|----|------|-------------------|----|------|
| **BLK-MEGC-01** | 决策冻结 | D-00/01/02/03/06/07/08/09/10 按本纪要写入 PRD v0.2；D-04/05 标为 **M3 延期** | M0 | ✅ 回写 |
| **BLK-MEGC-02** | CSS 排除/纳入名单 | PR-A 合码前：书面列出 **固定舞台须守合同** 的 pattern 与 **必须排除** 的 intrinsic/CSS-primary pattern；单测覆盖两侧 | M1 | ☐ |
| **BLK-MEGC-03** | soft 默认 | O-01 锁定 `soft_penalty`；`hard_reject` 仅配置/狗粮开关；AC-04 覆盖两 mode | M2 | ☐ |
| **BLK-MEGC-05** | 防假绿禁令 | AC-X01～X03 保持为合码红线（已在 ACCEPTANCE） | M0 | ✅ |
| **BLK-MEGC-06** | CSS 同步 | 定义 templates → trips 拷贝的同步策略（脚本/文档/CI 抽检至少一处 demo） | M1 | ☐ |
| **BLK-MEGC-07** | Peak 只读 | MSA `slot_adaptation.enabled=false` 时，MEGC 闸仍调用同一 `build_msa_profile`；AC 单测锁定 | M2 | ☐ |
| **BLK-MEGC-08** | Mobile 范围 | PRD 写明：M1–M2 **主验收 web 16:9**；mobile 变体不阻塞 PR-A；若闸启用须按 variant 记日志 | M0 | ✅ 回写 |

**不阻塞 M0/M1（Should-Fix）**

| ID | 建议 |
|----|------|
| **SHD-01** | `penalty=8.0` / `allow_mixed_median_min=1.70` 进狗粮可调表，M2 后校准 |
| **SHD-02** | experimental `2l2p-weighted`：闸上硬拒 + 不转 GA（O-04 锁定倾向） |
| **SHD-03** | 删除或改写 L1612 误导注释，与规则同 PR |

---

## 6. 拍板 D / O（锁定）

| ID | 结论 |
|----|------|
| **D-MEGC-00** | ✅ 按草案冻结 |
| **D-MEGC-01** | ✅ 按草案冻结 |
| **D-MEGC-02** | ✅ 按草案 + **BLK-02 名单签字** |
| **D-MEGC-03** | ✅ P-选为主路径；soft 默认 |
| **D-MEGC-04 / 05** | ⏸ **M3 延期**（不删合同，默认 off，不排期强制） |
| **D-MEGC-06** | ✅ 混向等权非电影峰：**硬拒**（比草案「加倍或硬拒」收紧为硬拒） |
| **D-MEGC-07～10** | ✅ 按草案 |
| **D-MEGC-11**（新增） | ✅ M1–M2 主责 **web 16:9**；mobile 不阻塞 CSS |
| **O-01** | ✅ **soft_penalty** |
| **O-02** | ✅ 暂定 **1.70** + 狗粮可调（SHD-01） |
| **O-03** | ✅ **延期** M3；不够再用 P-释 |
| **O-04** | ✅ 2L2P **不转 GA** + 闸硬拒 |
| **O-05** | ✅ **允许** CSS 先于父开关合入 |

---

## 7. 结论栏

| 项 | 结果 |
|----|------|
| **Conditional Go** | ✅ |
| **可 Kickoff M0** | ✅ 立即（本纪要 + PRD v0.2） |
| **可 Kickoff M1 / PR-A** | ✅（合码前关闭 BLK-02；建议并行启动 BLK-06） |
| **可 Kickoff M2 / PR-B** | ❌ 待 BLK-03/07 |
| **可 Kickoff M3** | ❌ 默认延期 |
| **No-Go** | 无 |

---

## 8. 会后动作

1. 回写 PRD → **v0.2.0**（本纪要链接 · D/O 锁定 · D-11 · M3 延期）。  
2. 更新 ACCEPTANCE W0 勾选 · DOC-STATUS / README 状态句。  
3. 工程：按 IMPL PR-A 起草 CSS 纳入/排除名单 MR 说明（关 BLK-02）。  
4. 不在本轮开启 `equal_grid_contract.enabled` 默认 on。
