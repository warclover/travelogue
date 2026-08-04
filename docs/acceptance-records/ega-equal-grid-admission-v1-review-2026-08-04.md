# PRD-EQUAL-GRID-ADMISSION-V1 · 跨职能评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-EQUAL-GRID-ADMISSION-V1.md](../PRD-EQUAL-GRID-ADMISSION-V1.md)（**EGA** · 等权宫准入优化） |
| **模板来源** | [ega-equal-grid-admission-v1-review-TEMPLATE.md](./ega-equal-grid-admission-v1-review-TEMPLATE.md) |
| **相邻挡门** | [SSG](../PRD-SMART-SHOT-GROUPING-V1.md) · [MEGC](../PRD-MOSAIC-EQUAL-GRID-CONTRACT-V1.md) · [MTSO](../PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) · [ALG-V3](../PRD-ALGORITHM-OPTIMIZATION-V3.md) · [6 张拼图](../PRD-6张拼图优化.md) · [P15](../PRD-PHASE15-photo-mosaic-evolution.md) · [LVP](../PRD-LAYOUT-VIBE-PICKER-V1.md) |
| **验收 / 实施** | [ACCEPTANCE…](../ACCEPTANCE-EQUAL-GRID-ADMISSION-V1.md) · [IMPLEMENTATION…](../IMPLEMENTATION-EQUAL-GRID-ADMISSION-V1.md) · [狗粮 GUIDE](./ega-local-dogfood-GUIDE.md) |
| **评审版本** | **v0.1.0 Draft** → Must-Fix 回写后升 **v0.2.0** |
| **日期** | 2026-08-04 |
| **结论** | **有条件通过（Conditional Go）** |
| **编码** | ☑ **可 Kickoff M0（文档冻结）**　☑ **M1 / PR-A Done**　☑ **M2 / PR-B+C Done**（BLK-06 已关 · AC-07 绿 · 锚点 L4≥1）　□ M3 默认延期 |
| **参评角色（七席）** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版 · 用户体验（狗粮手测） |
| **评审方式** | 分席只读 PRD §0～§11 · D/OQ 表 + **对照现网**（`demo-0ebda73294` mosaicDecisionLog · `shot_group_gate.is_slice_pattern` · `hook.six_hero_precheck` · MEGC `allow_peaks`） |
| **记录人** | 七席联合纪要（跨职能模拟联评 · 基于 2026-08-04 锚点册调查 + PRD/AC/IMPL v0.1.0） |
| **本纪要状态** | **已结案 · Conditional Go** · **PRD v0.2.0 已回写** |
| **审查基线** | SSG anti-slice / clone 硬拒 · MEGC 默认 on（电影峰）· MTSO six-hero precheck · 不强制出宫格 |

---

## 0. 会前宣读（主持人）

1. **切口**：EGA = **准入误伤修复**，不是「强制四宫/六宫」，不是关 SSG/MEGC。  
2. **实锤**：`demo-0ebda73294` — 四横同分镜 3:2 窗 L4 被 `shot_group_anti_slice` / `near_scene_clone` 硬清场；hero-70 因 `prefers_burst: true` 豁免；size=6 全挂 `six_hero_precheck` 后整窗放弃。  
3. **勿重开**：关 SSG/MEGC 父开关、给 L4 只贴 `prefers_burst: true` 当结案、默认改 MEGC `allow_peaks`、新建平行 YAML、LVP 用户 vibe。  
4. **本场必拍**：D-EGA-01～12 · OQ-01～04 · 豁免范围是否过宽 · G-06 双成功口径 · M3 是否延期。  
5. **列车**：先 PR-A 闸门软化，再 PR-B/C；禁单 PR 塞满；M3 默认延期。

---

## 1. 总评（一句话）

> **七席一致 Conditional Go：问题真实且因果链可复核，解法切口正确（修误伤与漏评、不强制出宫格）；SSG「假切条」精神保留，等权全横从 slice 硬拒中豁免成立。开工前钉死三件事——（1）patterns 白名单只含 L4/L6；（2）新增 mosaic 配置路径走 CSC/recipe 重签；（3）AC-05 双口径（胜出 **或** 进池可比分）防「修了闸仍无 L4」假失败。M0 立即冻结；M1 可 Kickoff；M2 挡在跨组回归与六图漏斗单测；M3（MEGC 3:2 soft demote）默认延期。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | **Conditional Go** | 用户债是「该并置的没并上」，不是「强制密度」；同意不强制；反对用关闸刷 KPI |
| **算法** | **Conditional Go** | 语义倒置属实：等权并置 ≠ 假切条；豁免须 **pattern 白名单**，禁止扩大到混向等权；MEGC 峰闸 M1/M2 不动 |
| **架构** | **Conditional Go** | `equal_grid_admission` 子树 fail-loud + 父开关回滚清晰；与 SSG/MEGC/MTSO 正交写死；CSC 重签挡合码 |
| **开发** | **Conditional Go** | PR-A 落点清楚（`candidates.py` / config）；**禁止** D-EGA-05 违规只改 `prefers_burst`；PR-B 只动漏斗不改 `qualify_hero_six` |
| **测试 / QA** | **Conditional Go** | AC-02/03/04 可单测；AC-05 必须双口径（A 胜出 ∨ B 进池），否则 3:2+MEGC 会假红；OFF 快照防回潮 |
| **视觉 / 排版** | **Conditional Go** | 同场景四横并置是合法杂志语言；有主图时仍应允许 hero；3:2 四宫观感交 M3/MEGC，不挡准入修 |
| **用户体验 · 狗粮** | **Conditional Go** | 锚点册毕业照场景对口；狗粮须 SSG/MEGC **保持 on**；盲评盯假切条回潮与「主图窗是否仍有主次」 |

**汇总**：**七席 7/7 Conditional Go**。  
- **M0**：文档冻结 ✅（本纪要 + PRD v0.2）。  
- **M1**：可 Kickoff（合码前关闭 BLK-EGA-03/04）。  
- **M2**：BLK-EGA-06 关闭前 **不批** PR-B/C 合入宣称 Done。  
- **M3**：默认 **延期**（OQ-03）。

**对齐评分**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→根因完整度 | **9** | F-01～07 + 拒因漏斗可复核 |
| 与 SSG/MEGC/MTSO 边界 | **9** | 不关闸、不改 hero-6 资格、不改 allow_peaks |
| 工程可开工性 | **8** | PR-A 清晰；CSC 重签已知 |
| AC 可测性 / 防假绿 | **8** | 双口径 G-06/AC-05；须写进合码红线 |
| 视觉/节奏可签核性 | **7** | 盲评四问够用；3:2 观感不挡 M1 |

---

## 3. 事实核查（对照现网）

| # | 假设 | 会中 |
|---|------|------|
| **F-01** | 锚点册 0× L4/L6，有 hero-70 四横 | ✅ 属实（2026-08-04 `trip.json` 直方图） |
| **F-02** | 四横窗 ~3:2 · 同 `sg-scene-0` | ✅ 属实 |
| **F-03** | 拒因 anti_slice×2 · clone×1 | ✅ 属实（mosaicDecisionLog + algoV3） |
| **F-04** | L4 `prefers_burst=None`→slice；hero-70 `true`→豁免 | ✅ 属实（代码） |
| **F-05** | size=6 全 `six_hero_precheck` 后 legacy | ✅ 属实 |
| **F-06** | MEGC `allow_peaks` 仅 `sixteen_nine`；legacy demote 非电影峰 L4 | ✅ 属实 |
| **F-07** | summary log 级可能丢细字段 | ✅ 属实；AC 以 rejectedTemplates / raw 为准 |

**新增事实（评审发现）**

| # | 事实 | 影响 |
|---|------|------|
| **F-08** | 即便 PR-A 让 L4 进 MCS 池，legacy 路径对 3:2 仍可能 `should_block_legacy_equal_grid` → demote 3/1 | → **G-06 / AC-05 双口径冻结**：「进池可比分」亦算 M1 准入成功；不得要求必胜出 L4 |
| **F-09** | `screen-landscape-6` **不在** MEGC `patterns` 默认元组 | → PR-B 评估 L6 与 MEGC 峰闸解耦；勿误写「L6 被 MEGC 硬挡」 |
| **F-10** | AC/IMPL/GUIDE **已在 v0.1 拆文** | → 原 BLK「拆文」关闭；不挡 M0 |
| **F-11** | 给 L4 标 `prefers_burst: true` 会污染 SSG slice 语义且可能放宽跨组行为 | → **D-EGA-05 升为合码红线**（BLK-EGA-04 相关） |

---

## 4. 全场共识

1. **EGA 是准入层，不是密度强制层**；禁止 KPI=「必须出 N 个 L4」。  
2. **假切条精神保留**：跨组 `shot_group_cross`、hero+窄条 clone 硬拒 **不动**。  
3. **等权全横白名单极窄**：默认仅 `screen-landscape-4` · `screen-landscape-6`。  
4. **anti-slice：豁免硬拒**（OQ-01）；可选 soft 默认关。  
5. **clone：等权全横软罚**（OQ-02=`0.85`）；slice hero 族仍硬拒。  
6. **六图：precheck 失败 ≠ 删除 size=6**；只挡 hero-6 族。  
7. **MEGC `allow_peaks` M1/M2 不动**；M3 默认延期。  
8. **不绑 LVP 文案**；回滚 = `equal_grid_admission.enabled=false`。  
9. **列车**：PR-A → PR-B∥PR-C；禁单 PR 塞满。

---

## 5. Must-Fix（阻塞）

| ID | 议题 | 要求（冻结一字面） | 挡 | 状态 |
|----|------|-------------------|----|------|
| **BLK-EGA-01** | D/OQ 回写 | D-01～12 · OQ-01～04 按本纪要写入 PRD v0.2；状态改 Conditional Go | M0 | ✅ 本纪要回写 |
| **BLK-EGA-02** | 拆 AC/IMPL | M1 合码前须有 ACCEPTANCE/IMPL | M0 | ✅ **已齐**（v0.1） |
| **BLK-EGA-03** | CSC / recipe | 新增 `mosaic.equal_grid_admission*` bool 路径 → ALG-V3 **AC-32** 重签；合码说明列路径 | M1 | ✅ 基线 115 True / 69 False（+enabled/+size6 keep /+megc soften false） |
| **BLK-EGA-04** | 白名单 + 禁 prefers_burst 捷径 | 代码 frozenset / 配置默认 = L4+L6；**禁止**仅靠 L4 `prefers_burst: true` 合入结案；单测锁 | M1 | ✅ `is_ega_equal_grid_pattern` + 单测 |
| **BLK-EGA-05** | AC-05 双口径 | 狗粮记录必须勾选 A（≥1 L4）**或** B（进池无 hard 拒 + 比分可解释）；禁止只报「没出 L4」判失败 | M1 Done 宣称前 | ✅ **A+B** · [ega-dogfood-2026-08-04](./ega-dogfood-2026-08-04.md)（成册 1× L4） |
| **BLK-EGA-06** | 回归门 | PR-B/C 合入前：`shot_group_cross` 单测绿 + `demo-2019` 电影峰 L4 不回退（AC-08） | M2 | ✅ `test_ega_pr_b` AC-08 + 狗粮 §AC-08（16:9 gate_allow×2） |

**Should-Fix（不阻塞 M1）**

| ID | 建议 | 状态 |
|----|------|------|
| **SHD-EGA-01** | mosaic summary log 增 `egaEnabled` 等短字段（可后置） | ✅ summary/window 保留 `egaEnabled` · `egaEqualSixKept` · modes |
| **SHD-EGA-02** | `algoV3.rejectFunnelTop` 拆 `ega_soft` 计数 | ✅ |
| **SHD-EGA-03** | LTE YAML 可选加 tag `equal-grid`（非必须；以代码白名单为准） | ✅ L4+L6 均含 `equal-grid` |
| **SHD-EGA-04** | 狗粮记录文件 `ega-dogfood-2026-08-04.md` 按 GUIDE 填 | ✅ PR-A/B/C 实册收口 |

---

## 6. 拍板 D / OQ（锁定）

| ID | 结论 |
|----|------|
| **D-EGA-01** | ✅ 不强制出宫格 |
| **D-EGA-02** | ✅ 白名单族 `equal_grid_pure_landscape` = L4+L6（可配置覆盖，默认冻结） |
| **D-EGA-03** | ✅ anti-slice：**豁免硬拒**；soft 可选默认 **关** |
| **D-EGA-04** | ✅ clone：等权全横 **soft_penalty**；hero+tile slice 硬拒不变 |
| **D-EGA-05** | ✅ **合码红线**：禁止 prefers_burst 捷径结案 |
| **D-EGA-06** | ✅ six_hero precheck fail → 保留 size=6 评估 equal-6 |
| **D-EGA-07** | ✅ 无主次评分偏置（PR-C） |
| **D-EGA-08** | ✅ M1/M2 不改 MEGC `allow_peaks` |
| **D-EGA-09** | ✅ 父开关默认 **true**；false ≡ 现网 |
| **D-EGA-10** | ✅ 不绑 LVP |
| **D-EGA-11** | ✅ 混向等权不豁免 |
| **D-EGA-12** | ✅ 跨组 cross 硬拒保留 |
| **D-EGA-13**（新增） | ✅ **G-06/AC-05 双口径**：胜出 ∨ 进池可比分，均算准入成功 |
| **OQ-01** | ✅ **关闭** · exempt 硬拒（= D-03） |
| **OQ-02** | ✅ **关闭** · clone soft `score_mul=0.85` |
| **OQ-03** | ✅ **关闭** · M3 **延期** |
| **OQ-04** | ✅ **关闭** · 不改 `flat_six_grid` 罚 |

---

## 7. 结论栏

| 项 | 结果 |
|----|------|
| **Conditional Go** | ✅ |
| **可 Kickoff M0** | ✅ 立即（本纪要 + PRD v0.2） |
| **可 Kickoff M1 / PR-A** | ✅（合码前关闭 BLK-EGA-03/04；Done 宣称前 BLK-05） |
| **可 Kickoff M2 / PR-B+C** | ✅ PR-B+C Done（AC-07 · 锚点 L4≥1） |
| **可 Kickoff M3** | ❌ 默认延期 |
| **No-Go** | 无 |

---

## 8. 会后动作

1. 回写 PRD → **v0.2.0**（本纪要链接 · D/OQ 锁定 · D-13 · Conditional Go）。  
2. 更新 ACCEPTANCE W0 · DOC-STATUS / README 状态句。  
3. 工程：按 IMPL PR-A 开工；合码说明附 CSC 路径清单（BLK-03）。  
4. 不在本轮改 MEGC `allow_peaks` / 关 SSG / 开 LVP 新卡。  
5. 锚点狗粮按 GUIDE 填记录（BLK-05）。

---

## 9. 签字栏（模拟联评）

| 席位 | 表决 | 日期 |
|------|------|------|
| 产品 | Conditional Go | 2026-08-04 |
| 算法 | Conditional Go | 2026-08-04 |
| 架构 | Conditional Go | 2026-08-04 |
| 开发 | Conditional Go | 2026-08-04 |
| 测试 / QA | Conditional Go | 2026-08-04 |
| 视觉 / 排版 | Conditional Go | 2026-08-04 |
| 用户体验 · 狗粮 | Conditional Go | 2026-08-04 |
