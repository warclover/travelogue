# PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1 · 跨职能评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md](../PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md)（**MTSO** · 拼图模板选型与使用优化） |
| **模板来源** | [mtso-mosaic-template-selection-v1-review-TEMPLATE.md](./mtso-mosaic-template-selection-v1-review-TEMPLATE.md) |
| **相邻挡门** | [P21](../PRD-PHASE21-mosaic-density-budget.md) · [TPC](../PRD-TEMPLATE-CONTRACT-V1.md) · [LTN 峰会](./ltn-template-slot-summit-2026-07-20.md) · [6 张拼图](../PRD-6张拼图优化.md) · [MGQ](../PRD-MCS-GEOMETRIC-QUALITY-V1.md) · [URO](../PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md) |
| **评审版本** | **v0.1.0 Draft** → Must-Fix 回写后升 **v0.2.0** |
| **日期** | 2026-07-23 |
| **结论** | **有条件通过（Conditional Go）** · **可 Kickoff M1 / PR-A**（生命周期隔离 + 漏斗日志）；**M2 合码前须关闭 BLK-MTSO-03～06** |
| **编码** | □ 本轮仅文档　☑ **可 Kickoff M1 / PR-A**　□ 可开 M2（待 BLK） |
| **参评角色（七席）** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版（LTE SKU）· 用户体验（狗粮手测） |
| **评审方式** | 分席只读 + **对照现网代码核查**（`lte_adapter` · `hook` · `builders._order_hero_six` · `planner_state` · 本机 trips 曝光） |
| **记录人** | 七席联合纪要（跨职能模拟联评 · 基于 2026-07-23 代码探查） |
| **本纪要状态** | **已结案 · Conditional Go** · **PRD v0.2.0 已回写** · 可 Kickoff M1 / PR-A |
| **审查基线** | 仓库 MCS-11 + 本机 `config.yaml`（`template_contract.enabled=true` 狗粮残留） |

---

## 0. 会前宣读（主持人）

1. **切口**：修选型与生命周期，不是堆模板、不是放宽 P21。  
2. **三场手测债**已代码核实（见 §3）。  
3. **勿重开**：dense 硬上限、禁 runtime 改 rect、MCS 权威、QFX 正交。  
4. **本场必拍**：D-01 / D-05·07 / D-03·04 / D-13；关闭 O-1～O-4。  
5. **列车**：M1 可先开；禁止单 PR 塞满 M1–M3。

---

## 1. 总评（一句话）

> **七席一致 Conditional Go：问题→根因→解法链条成立，「机会保护」优于全局改窗宽序，TPC≠实验解锁必须立刻拆；但 v0.1 有三处合同含糊——合格六图资格与配额预检循环定义、孪生六图 SKU 未定权威、AC-11「显著提升」不可测——须回写 v0.2 后方可开 M2。M1（lifecycle + 漏斗）证据充分，可立即 Kickoff。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | **Conditional Go** | 手测三债对得上用户体感；转化率主指标正确；须承诺「不借六图 KPI 强塞」并写进 AC |
| **算法** | **Conditional Go** | 5→4→6 饿死六图与竖强塞横主是真根因；资格预检把「配额允许」写进 qualified 会循环——须拆成 structural vs admit |
| **架构** | **Conditional Go** | `_contract_unlocks_experimental` 是明确设计耦合而非偶然 bug；lifecycle_admit 单一判定对；机会状态机不得变成第二套 dense 账本 |
| **开发** | **Conditional Go** | M1 落点清晰（`lte_adapter`/`log`）；M2 机会武装与 cursor 语义要钉「仅挡抢占该 6 窗的 4/5」，勿章内永久禁 size4 |
| **测试 / QA** | **Conditional Go** | AC-01/02/04 可测；AC-11「显著提升」假绿风险高，须改机会尝试率+转化率双阈值；漏斗字段必须进 fixture 断言 |
| **视觉 / 排版 · LTE SKU** | **Conditional Go** | 支持主从 2P3L、禁等权双竖；竖主 1P4L 几何未出稿前不得占活跃集；孪生 hero-plus-4/5 应定一个 canonical |
| **用户体验 · 狗粮手测** | **Conditional Go** | TPC ON 时看到两竖三横被误读为「退役回潮」——狗粮 GUIDE 必须写清；六图消失比「偶发平庸混向」更伤杂志感 |

**汇总**：**七席一致 Conditional Go**。  
- **M1 / PR-A**：可 Kickoff（BLK-01/02/07 随 PR-A 关闭）。  
- **M2 合码**：BLK-03～06 回写并实现合同前 **不批**。

**对齐评分**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→根因完整度 | **9** | Q1–Q6 / F-01～F-09 与手测一致 |
| 与 P21/TPC/LTN 边界清晰度 | **8** | 不放宽 dense 写清楚；机会状态机需防变相加额度 |
| 工程可开工性 | **7** | M1 可开；M2 资格定义须先改 |
| AC 可测性 / 防假绿 | **5** | AC-11 偏软；须改双阈值 |
| 视觉/SKU 可签核性 | **6** | 2P3L 原则对；竖主 1P4L 几何仍开放 |

---

## 3. 事实核查（代码核对 · 全部属实）

| # | 假设 | 代码事实 | 会中 |
|---|------|----------|------|
| **F-01** | MCS 活跃 11 | `lte_policy.yaml` groups = 11 | ✅ 属实 |
| **F-02** | 两竖三横退役仍见 | 手测/trips 为 `2p3l-rail`；`2p3l-equal` deprecated+disabled | ✅ 属实 |
| **F-03** | TPC ON 解锁实验 | `lte_adapter._contract_unlocks_experimental`；本机 registry=21 | ✅ 属实 |
| **F-04** | 六图模板没了 | `main-hero-plus-4/5` ga+in registry；trips 曝光 **0** | ✅ 属实 |
| **F-05** | 全横被四宫抢 | `window_order=(5,4,6)`；仿真 rem≠6 → landscape-4 先胜 | ✅ 属实 |
| **F-06** | 5 槽吃 large 章配额 | `large_mosaic_min_slots=5`，每章 1 | ✅ 属实 |
| **F-07** | 小册 dense≈1 | `dense_collage_limits_for_trip`；landscape-4 计 dense | ✅ 属实 |
| **F-08** | 竖强委屈 | `main-portrait-3land` usage 有 whenNotToUse，无硬拒 | ✅ 属实 |
| **F-09** | 禁跨段凑六 | `max_window_size_in_segment` / `seg_cap` | ✅ 属实 |

**新增事实（评审发现）**

| # | 事实 | 影响 |
|---|------|------|
| **F-10** | `main-hero-plus-4` 与 `main-hero-plus-5` **几何孪生、双进 MCS-6** | 机会/配额/MMR 应视为同一家族；须定 canonical（→ BLK-06 附带） |
| **F-11** | `SIGNATURE_WHITELIST` **无** `(0,6,*)` 条目 | 现靠 fallback 全集；扩展时不得静默清空 |
| **F-12** | `legacy.append` 已调 `mosaic_pattern_disabled`，但 `build_legacy_screen` 仍可**构造** deprecated 6/8/9 | M1 负例须覆盖构造后拒绝；建议 M2 起直接不构造 |

---

## 4. 全场共识

1. **方向成立**：生命周期隔离 + 合格六图机会 + 混向主次，是从及格到优秀的正确杠杆。  
2. **P21 不放宽**：任何「多发几张六图」诉求用转化率回答，不用加 dense。  
3. **TPC ≠ 上线开关**：D-01 升为 M1 最高优先级。  
4. **机会≠全局改序**：仅 `qualified` 窗局部 6→5→4；禁止把默认序改成 6 优先。  
5. **2P3L 方案 A 锁定**：单竖 main；等权 rail 永不转 GA。  
6. **主指标 = 转化率**；辅以「有配额时的尝试率」防假绿。  
7. **列车**：PR-A → PR-B → PR-C → PR-D；M1 可先合。

**会中新增共识**

- **资格两段论**：`structurally_qualified_six`（段/定向/ordering/gap）与 `admit_six_hero`（dense/相邻/机会状态）分离；日志两字段都要。  
- **armed 作用域**：只阻止「会抢走当前合格 6 窗」的同 cursor size4/5；**不**章内永久禁止 landscape-4。  
- **孪生六图**：评分/配额按家族去重；文档指定 canonical id（建议保留 `screen-mosaic-6-main-hero-plus-5` 为对外名，`…-5-main-hero-plus-4` 为历史别名或逐步降权）。

---

## 5. Must-Fix（阻塞项）

| ID | 议题 | 来源 | 要求（冻结一字面） | 挡 | 状态 |
|----|------|------|-------------------|----|------|
| **BLK-MTSO-01** | TPC↔experimental 解耦 | 架构/算法 | 删除「contract ON ⇒ experimental 可见」；`template_experiments` 三元组（enabled∧allowlist∧cohort） | **M1** | ⬜ 待 PR-A |
| **BLK-MTSO-02** | deprecated 全路径 | 测试/开发 | candidate / self-heal / legacy append 负例；LTE OFF 硬禁补 `2p3l-equal` | **M1** | ⬜ 待 PR-A |
| **BLK-MTSO-03** | 资格两段论 | 算法/QA | PRD 改写：`structurallyQualifiedSix` vs `admitSixHero`；qualified 定义**不得**循环依赖配额 | **M2** | ⬜ 待 v0.2 |
| **BLK-MTSO-04** | 机会作用域 | 架构/开发 | armed 仅挡同 cursor 抢占；释放条件写死；**禁止**变相提高 dense_max | **M2** | ⬜ 待 v0.2 |
| **BLK-MTSO-05** | AC-11 可测化 | 测试/产品 | 改双阈值：有配额时 `attempted/structural≥0.80`；`won/attempted` 相对基线提升且 dense 违规=0；删除「显著」模糊词 | **M2** | ⬜ 待 v0.2 |
| **BLK-MTSO-06** | SKU 视觉与孪生 | 视觉/产品 | 2P3L 主从签核门槛不变；孪生六图定 canonical；竖主 1P4L **O-1** 须在 PR-C 前出 ≥1 冻结几何稿 | **M2/PR-C** | ⬜ |
| **BLK-MTSO-07** | 漏斗 fixture | 测试 | §5.5 字段进合成 fixture 断言；AC 禁只读展示日志 | **M1** | ⬜ 待 PR-A |
| **BLK-MTSO-08** | 拆 ACCEPTANCE/IMPL | 测试/产品 | M2 合码前拆文，或豁免写明「M1 用 PRD §8–9，M2 前补齐」 | **M2** | ⬜ 本纪要豁免 M1 |

---

## 6. Should-Fix（不阻塞 M1）

| ID | 建议 | 席位 | 状态 |
|----|------|------|------|
| **S-01** | 增补 `docs/config-tpc-dogfood.example.yaml` / GUIDE：TPC ON 会看见 experimental，**不等于**退役回潮 | 产品/UX | ⬜ |
| **S-02** | `main-hero-plus-4` displayName/usage 强调 6 槽 | 视觉 | ⬜ |
| **S-03** | weekly dashboard 只读六图漏斗 | 算法 | ⬜ |
| **S-04** | 盲评切片：全横12、强竖1P4L、2P3L、段长&lt;6 | QA | ⬜ |
| **S-05** | `2p3l-rail` YAML 文首标注「非 MTSO 继任 · 勿转 GA」 | 开发 | ⬜ |
| **S-06** | `build_legacy_screen` 对 deprecated size6/8/9 直接 return None（不止 append 拒） | 开发 | ⬜ M2 |

---

## 7. D-MTSO / O-* 拍板

### 7.1 决策

| ID | 结论 | 备注 |
|----|------|------|
| **D-MTSO-01** | ✅ **按建议** | M1 P0 |
| **D-MTSO-02** | ✅ **按建议** | 空位不强填 |
| **D-MTSO-03** | ✅ **按建议** | 硬拒码 `mixed_portrait_is_hero` |
| **D-MTSO-04** | ✅ **方案 A** | 单竖 main |
| **D-MTSO-05** | ✅ **按建议** | 禁止全局 6 优先 |
| **D-MTSO-06** | ✅ **按建议** | |
| **D-MTSO-07** | ✅ **按建议 + 作用域收紧** | 见 BLK-04；资格两段论见 BLK-03 |
| **D-MTSO-08** | ✅ **按建议** | |
| **D-MTSO-09** | ✅ **按建议** | |
| **D-MTSO-10** | ✅ **按建议** | |
| **D-MTSO-11** | ✅ **按建议** | |
| **D-MTSO-12** | ✅ **按建议** | |
| **D-MTSO-13** | ✅ **转化率 + 尝试率双阈值** | 见 BLK-05；否决「最低六图屏数」 |

### 7.2 开放项

| ID | 结论 |
|----|------|
| **O-1** | **保持开放至 PR-C**：视觉出 ≥1 冻结几何稿（左满高竖优先探索）；算法侧主从比合同先生效 |
| **O-2** | **关闭**：`selection_optimization` 默认保持 **false** 至 M3 盲评后另决策；嵌套子开关仅在父开关 ON 时生效（回写配置语义） |
| **O-3** | **关闭**：默认共用 `usage_rules.hero_gap_threshold`；MTSO 可覆盖但须单测锁 |
| **O-4** | **关闭**：`2p3l-rail` **留 YAML** + 文首标注非继任；默认不进 allowlist；禁止转 GA |

---

## 8. 风险与回滚确认

| 风险 | 可接受 | 备注 |
|------|--------|------|
| 六图保护使部分 4/5 变稀 | ✅ | 仅同 cursor；可关机会开关 |
| 新 2P3L 仍假拼图 | ✅ | 不过则归档 |
| 实验隔离过严无狗粮 | ✅ | cohort 显式 |
| 开关难回滚 | ✅ | 三开关独立默认 off |

**回滚顺序**：experiments OFF → hero_six_opportunity OFF → selection_optimization OFF → **P21 保持 ON**　✅ 同意

---

## 9. 结论与下一步

| 项 | 内容 |
|----|------|
| **结论** | **Conditional Go** |
| **可 Kickoff M1 / PR-A** | **是**（随 PR 关闭 BLK-01/02/07） |
| **可开 M2 合码** | **否**（须先关 BLK-03～06 并回写 v0.2） |
| **Must-Fix 责任人** | 算法+架构主笔合同回写；开发落 M1；视觉主笔 O-1 |
| **回写 PRD 目标版本** | **v0.2.0** |
| **ACCEPTANCE / IMPLEMENTATION** | **M1 豁免**（暂用 PRD §8–9）；**M2 合码前必须拆文**（BLK-08） |
| **README / DOC-STATUS** | 本纪要合入后更新为 Conditional Go |

**列车（锁定）**

| PR | 内容 | 关闭 BLK |
|----|------|----------|
| **PR-A** | `lifecycle_admit` + 实验开关 + 漏斗日志 + 负例 + TPC 狗粮 GUIDE 一句 | 01, 02, 07 |
| **PR-B** | 两段资格 + hero_six_opportunity（作用域收紧）+ 窗序局部重排 | 03, 04, 05 |
| **PR-C** | 1P4L 双分支 + 2P3L 主从 SKU（experimental）+ 孪生 canonical | 06 · O-1 稿 |
| **PR-D** | 狗粮/盲评 → 转正或归档 | AC-11/12 |

---

## 10. 签名栏

| 角色 | 表决 | 日期 |
|------|------|------|
| 产品 | Conditional Go | 2026-07-23 |
| 算法 | Conditional Go | 2026-07-23 |
| 架构 | Conditional Go | 2026-07-23 |
| 开发 | Conditional Go | 2026-07-23 |
| 测试 / QA | Conditional Go | 2026-07-23 |
| 视觉 / 排版 | Conditional Go | 2026-07-23 |
| 用户体验 · 狗粮 | Conditional Go | 2026-07-23 |

---

## 附录 · 回写 PRD v0.2.0 检查单

- [x] §3 术语拆 `structurallyQualifiedSix` / `admitSixHero`  
- [x] §4 D-07 / §5.3 机会作用域与释放条件  
- [x] §4.1 嵌套开关：父 OFF 则子无效  
- [x] §4 D-14 孪生六图 canonical  
- [x] §9 AC-11 双阈值 + AC-13 家族去重  
- [x] §12 O-2/O-3/O-4 关闭结论  
- [x] 文首状态 → Conditional Go · 链到本纪要  
