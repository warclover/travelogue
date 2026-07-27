# PRD-PORTRAIT-2-VARIANT-FAMILY-V1 · 跨职能评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-PORTRAIT-2-VARIANT-FAMILY-V1.md](../PRD-PORTRAIT-2-VARIANT-FAMILY-V1.md)（**P2VF** · 双竖变体家族试点） |
| **评审版本** | **v0.1.0 Draft** → Must-Fix 已回写 **[PRD v0.2.0](../PRD-PORTRAIT-2-VARIANT-FAMILY-V1.md)** |
| **日期** | 2026-07-27 |
| **结论** | **有条件通过（Conditional Go）** · **可 Kickoff M0 / PR-A**（YAML+CSS+探针）；**PR-B** 按 v0.2 合同实现并关闭实现向 BLK |
| **编码** | ☑ 文档已回写 v0.2.0　☑ **可 Kickoff M0/PR-A**　□ PR-B（实现关 BLK-01/02/06/07） |
| **参评角色（六席）** | 产品 · 算法 · 架构 · 开发 · UI/UX（视觉/排版）· 典型用户代表 |
| **评审方式** | 分席只读 + 对照现网代码核查（`screen_planner*` · `layout_contract/rhythm` · `template_experiments` · `mobile_screens`） |
| **记录人** | 六席联合纪要（跨职能模拟联评 · 2026-07-27） |
| **本纪要状态** | **已结案 · Conditional Go** · **PRD v0.2.0 已回写**（产品确认：砍 offset 轮换 + asym 强弱选型） |

---

## 1. 总评（一句话）

> **六席一致 Conditional Go：方向与范围控制成立（只做 2P、不改 fill 几何、软轮换、实验门），但 v0.1 在节奏内核（R-06/R-08）、实验配置合同、mobile 新行为、留白「坏版感」、asym 主次绑定上有合同缺口——可先落几何/CSS，不可未回写就合 picker。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | **Conditional Go** | 范围锁 2P 成熟；须把「坏版/缺图」写入盲评否决门；O-* 冻结态要理清 |
| **算法** | **Conditional Go** | 最大洞：streak 仍按单 id，换变体会绕开 R-06；R-08 未注册新 id；双重软罚与 person 门过窄 |
| **架构** | **Conditional Go** | experiments 挂 picker 可接受，但须写清「MCS lifecycle 不自动挡 2P」；OFF 与家族 streak 常驻语义要裁定 |
| **开发** | **Conditional Go** | PR-A 可开；硬编码/fit/mobile 位点未列全；`cohort: dogfood` 与代码 `cohort_trip_ids` 不符 |
| **UI/UX** | **Conditional Go** | gallery 值得做；offset 建议延后；asym 要「强图→主槽」而非双 id 硬轮；50% 留白易读成坏版 |
| **典型用户代表** | **Conditional Go** | 竖图多的风景册会更生动；怕半屏空白当 bug、主次反、手机/电脑完全两套 |

**汇总**：**六席一致 Conditional Go**。  
- **M0 / PR-A**：可 Kickoff。  
- **PR-B / M1b**：BLK 回写前 **不批**。

**对齐评分**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→根因完整度 | **8** | F-01～F-08 主路径正确；漏写 streak 运行时细节 |
| 与 MTSO/TPC/LTE 边界 | **8** | 不占 2P3L 空位、不扩 MCS；experiments 接线须写清 |
| 工程可开工性 | **7** | PR-A 可开；PR-B 依赖 BLK |
| AC 可测性 / 防假绿 | **6** | 生动比可刷；缺坏版否决门 |
| 视觉/SKU 可签核性 | **6** | 四变体偏多；gallery+asym 更干净 |

---

## 3. 事实核查（代码核对）

| # | PRD 假设 | 代码事实 | 会中 |
|---|----------|----------|------|
| **F-01** | 硬 emit，非 MCS | planner 多处写死 `screen-portrait-2`；不在 `MOSAIC_*` | ✅ 属实 |
| **F-02** | `PORTRAIT_PAIR_PATTERNS` 单员 | `rhythm.py` 仅 fill | ✅ 属实 |
| **F-03** | R-06 默认 2 | `MAX_PORTRAIT_PAIR_STREAK=2` | ✅ 属实 |
| **F-04** | diversity / rhythm 公式 | `beam_scoring` 近 2 屏同 pid→0 | ✅ 属实（硬 emit 不靠它选型） |
| **F-05** | MCS diversity 不覆盖 2P | MCS 窗不含 2P | ✅ 属实 |
| **F-06** | intentionalGaps / V-P16-02 | validator 强制声明 | ✅ 属实 |
| **F-07** | experiments 三元组 | `cohort_trip_ids`（tripId 列表） | ⚠️ PRD §5.3 样例写错 |
| **F-08** | 默认不进 GA | 意图成立 | ✅ 意图 |

**评审新增事实**

| # | 事实 | 影响 |
|---|------|------|
| **F-09** | `current_portrait_pair_streak()` 只比 `PORTRAIT_PAIR_PATTERN` 单 id | 仅扩 frozenset **不够**；换变体绕开 R-06 → **BLK-ALG-01** |
| **F-10** | `PORTRAIT_ORIENTATION_PATTERNS` 不含新 id | 变体 emit 可能清零 R-08 → **BLK-ALG-02** |
| **F-11** | late pairing reset 只认 fill id | 同 F-09 |
| **F-12** | mobile 现网 **不拆** `screen-portrait-2`；仅 triple/4mix 有 expand | D-08 是**新工程**，非照搬 |
| **F-13** | `_fits_for_pattern` 仅精确 id 走 portrait fit；新 id 默认全 cover | 脸裁风险 → **BLK-ALG-03 / DEV** |

---

## 4. 全场共识

1. **方向成立**：2P 家族 + 软轮换是验证「版式生动」的正确试点切口。  
2. **范围锁死**：不扩 3–9；不改 fill 几何；不碰 P21/LSE/MCS 窗序。  
3. **列车**：PR-A 几何/CSS → 回写 BLK → PR-B picker → 狗粮盲评。  
4. **节奏内核必须家族化**：R-06 / R-08 / late-reset 与变体 id 对齐，否则轮换破坏硬门。  
5. **视觉试点宜收窄**：优先 `fill + gallery + asym（强弱选型）`；`offset-right` 建议延后。  
6. **Mobile 诚实叙事**：变体价值在 Web/screens；手机拆单竖，不评杂志轮换。  
7. **盲评三问**：更生动？像缺图/坏版？主次反了吗？

---

## 5. Must-Fix（阻塞 PR-B · 回写 v0.2）

| ID | 议题 | 来源 | 要求（冻结一字面） | 挡 |
|----|------|------|-------------------|----|
| **BLK-P2VF-01** | 家族 R-06 streak | 算法/开发 | `current_portrait_pair_streak` / late-reset / postcheck 对家族任一成员累计；禁止「换 id 清零」 | PR-B |
| **BLK-P2VF-02** | R-08 orientation | 算法 | 四变体加入 `PORTRAIT_ORIENTATION_PATTERNS` | PR-B |
| **BLK-P2VF-03** | experiments 配置合同 | 开发/架构 | §5.3 改为 `cohort_trip_ids`；写明双开关（`portrait_2_variants.enabled` ∧ experiments） | 文档 / 狗粮 |
| **BLK-P2VF-04** | picker 可见性权威 | 架构 | 写死：MCS lifecycle **不**自动挡 2P；可见性仅 picker 内 `experimental_members_visible` | 文档 |
| **BLK-P2VF-05** | OFF 与 streak 语义 | 架构 | 裁定：家族 streak **常驻**（即使 variants OFF，手工注入变体 id 仍计 R-06） | 文档+AC |
| **BLK-P2VF-06** | hard gates + 人脸 | 算法/UX | 定义 `filter_hard_gates`；**任一方有人 → 仅 fill**（收紧 D-07）；去掉 id×role 双重软罚 | PR-B |
| **BLK-P2VF-07** | emit/fit/mobile 文件表 | 开发 | §6.1 补 `mobile_screens`、`_fits_for_pattern`、`moment_scoring`、attach 等位点 | 文档 |
| **BLK-P2VF-08** | 坏版否决门 | 产品/UX | 盲评系统性「像缺图/坏版」→ No-Go；AC 增加固定问项 | M2 |
| **BLK-P2VF-09** | 试点变体集合 | UX/产品 | Design Freeze：V1 狗粮默认 **fill+gallery+asym**；**offset-right 延后**（可保留 YAML 不做 picker 轮换） | M0 |
| **BLK-P2VF-10** | asym 主槽绑定 | UX/算法 | 不跨槽换图前提下，按相对强弱选 left/right 主模板；难分 → gallery/fill | PR-B |

**Should（不挡 PR-A）**

- 定义或删除 `variant_entropy` 一词。  
- 消除 §5.1「加家族软分」与 O-05「只做 picker」的表述矛盾。  
- gallery 面积目标可调至两槽合计约 55–65%（防过空）。  
- §5.4 数值作观察指标，盲评为主裁决。  
- 估时上修 PR-B（节奏内核改动）。

---

## 6. 可保持不动（试点资产）

- 方案 B：新 id，不改 `screen-portrait-2` rect。  
- 默认 `enabled=false`；不进 `lte_policy` GA。  
- 软轮换非硬禁；无候选回退 fill。  
- 不做 3–9、不做 captionAreas、不做 offset-left、不做 runtime 改 rect。  
- PR-A 几何/CSS 可先合、探针对照草图签字。

---

## 7. 开放问题拍板建议（供产品确认）

| ID | 建议冻结 |
|----|----------|
| **O-01** | V1 **不做**跨槽换图；改用 **强弱→选 asym-L/R**（BLK-10） |
| **O-02** | V1 **不做** offset-left；**offset-right 延后**出轮换集 |
| **O-03** | 人物（任一方有人）→ fill（收紧） |
| **O-04** | 软罚进 config；狗粮再调 |
| **O-05** | V1 **只做 picker**；删「再加 beam 家族软分」表述 |

---

## 8. 下一步

1. ~~产品确认 BLK-P2VF-09/10~~ ✅ 2026-07-27 接受砍 offset 轮换 + asym 强弱。  
2. ~~回写 PRD → v0.2.0~~ ✅ 已合入。  
3. Kickoff **PR-A**（gallery + asym YAML/CSS；offset 仅附录）。  
4. **PR-B** 按 v0.2 §5～§6 实现并关闭 BLK-01/02/06/07。  
5. 竖图多、人物对少的 trip 狗粮 + 盲评三问。

---

## 9. 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **纪要 v1** | 2026-07-27 | 六席 Conditional Go；10 条 BLK；可 PR-A，不可未回写合 PR-B |
| **纪要 v1.1** | 2026-07-27 | 产品确认 + PRD v0.2.0 回写完成；编码门更新为可 Kickoff PR-A |
