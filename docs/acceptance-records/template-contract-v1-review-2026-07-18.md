# PRD-TEMPLATE-CONTRACT-V1 · 跨职能评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-TEMPLATE-CONTRACT-V1.md](../PRD-TEMPLATE-CONTRACT-V1.md)（TPC · 统一模板合同重设计） |
| **对照方案** | [LQS 瘦身版实施清单](../IMPLEMENTATION-LAYOUT-QUALITY-STACK-V1.md)（已认可 · 与 TPC 二选一） |
| **相邻挡门** | [MSR](../PRD-MCS-SIGNATURE-ROUTING-V1.md) · [MGQ](../PRD-MCS-GEOMETRIC-QUALITY-V1.md) · [GCS](../PRD-GENERATIVE-COLLAGE-SURFACES-V1.md) · [URO](../PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md) · [LTE P16](../PRD-PHASE16-layout-template-engine.md) |
| **评审版本** | **v0.1.0 Draft** → Must-Fix 回写后升 v0.2.0 |
| **日期** | 2026-07-18 |
| **结论** | **有条件通过（Conditional Go）** · **可 Kickoff W1**（守门修复 + debt 报表 + 倒排 shadow）；**W2 合码前须回写 BLK-TPC-01～04** |
| **参评角色** | 算法 · 架构 · 前后端开发 · 产品 · UI/UX · 用户体验（狗粮）· 测试/QA |
| **评审方式** | 分席只读（TPC §0.1 D-TPC · §1.3 处置清单 · §3 合同 · §7 里程碑）+ **对照现网代码核查**（`main_eligibility` 调用面 · captionAreas 渲染链 · 模板 `mix` 字段） |
| **记录人** | 七席联合纪要（跨职能模拟联评） |
| **本纪要状态** | **已结案** · BLK-TPC-01～07 成立，待回写 |

---

## 0. 会前宣读（主持人 · 3 分钟）

1. **切口**：评审 TPC 是否成立为 LQS 瘦身版的替代方案；不重开 MSR/MGQ/GCS 已冻结禁区（TPC 已全盘继承）。  
2. **本场必拍**：D-TPC-01～12；重点 D-TPC-02（放弃有序签名）、D-TPC-04（mainSlotPolicy 迁移删除）、D-TPC-05（不做 soft）。  
3. **代码核查先行**：评审前已核对三处关键假设（见 §3 事实核查）。  
4. **本轮不动代码**；W1 与瘦身版 S1 兼容，可先行。

---

## 1. 总评（一句话）

> **七席一致 Conditional Go：机制收敛方向正确、「四套准入合一」与「品味优先」立得住；但代码核查发现两处 PRD 低估——`main_eligibility` 实为 8 个调用点的横切模块（非「2–4 个模板」量级），`captionAreas` 在渲染链上尚不存在——W2/W3 范围与估时须修正；mix_fallback 可行性定义与 shadow diff 验收须钉死后方可合码。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **算法** | Conditional Go | 放弃有序签名论证成立（固定 SKU 下几何罚多为模板常量，硬带更诚实）；但 mix_fallback「不冲突」未定义、square 归置未定，会假绿 |
| **架构** | Conditional Go | 收敛方向对；`main_eligibility` 调用面被低估 8 倍，迁移须拆两步；共享工具函数（`asset_native_ar`）要先安置 |
| **前后端开发** | Conditional Go | W2 估时偏乐观（4–5d → 建议 5–7d）；倒排替换 if 链必须有 shadow diff 保护；海报 Writer 范围合理 |
| **产品** | Conditional Go | 支持切换 TPC，但**必须收口双轨**：通过即废止瘦身版 S2+，禁止两案并行；对外默认开启前补正式盲评的承诺保留 |
| **UI/UX** | Conditional Go | 海报 ▾ 文案继承 GCS 合同没问题；**captionAreas 渲染链不存在**，图文 SKU 不能按计划直接排 W3 |
| **用户体验 · 狗粮** | Conditional Go | 「off 逐屏一致 + 不因 narrate 改脸」保住了信任底线；debt 报表前后对比比盲评仪式更可感 |
| **测试 / QA** | Conditional Go | AC-TPC-03 的「或」是逃生门；shadow diff 只在风险表里、没进 AC；配置 fail-loud 未写 |

**汇总**：**七席一致 Conditional Go**。W1 可立即 Kickoff；**BLK-TPC-01～04 回写 v0.2.0 前不批 W2 合码**。

---

## 3. 事实核查（评审前代码核对 · 影响结论）

| PRD 假设 | 代码事实 | 影响 |
|----------|----------|------|
| mainSlotPolicy 迁移涉及「现网 hero 类 ≈ 2–4 个模板」 | `main_eligibility.py` 被 **8 个模块**导入：`hero` / `builders` / `screen_planner` / `candidates` / `scorer` / `metrics` / `usage_rules.evaluator` / `usage_rules.context`；且 `asset_native_ar` 是 URO 复用的工具函数 | **W2 范围低估**；须列调用点迁移清单，删除动作或挪 W3（→ BLK-TPC-02） |
| W3 手写 2 个 `captionAreas` SKU | 模板 schema 与 `render/chapters.py` 渲染链**均无 captionAreas 概念**；现网仅 editorial 系模板有文案感排版 | 图文 SKU 需先做渲染支持验证/spike，否则挪出 V1（→ BLK-TPC-03） |
| registry 按 `mix` 建倒排「有数据基础」 | **属实**：模板 YAML 已带 `mix` 字段（如 `screen-editorial-4mix.yaml`） | 倒排索引可行性确认 ✅ |
| `try_order_for_pattern` 承担隐式选版 | **属实**：约 80 行 if 链 + `_order_by_roles` 兜底 | 替换合理，但须 shadow diff 保护（→ BLK-TPC-04） |

---

## 4. 全场共识

1. **机制收敛成立**：四套「模板能否进窗」机制合为一份 TemplateContract + 一个求值器，是对现网真实债务的正解。  
2. **放弃有序签名成立**：填槽本按 role 重排；固定 SKU 下有序串无增量信息；未来需要时以 `orderedMix` 扩展字段重入，不推翻合同。  
3. **V1 不做 soft 罚项成立**：LSE dogfood 已证软分微调无感知；且固定几何下 coverage/CV 多为模板常量，声明进 YAML 更诚实。raw 特征照记，留 G2 复议。  
4. **手写模板是主战场**：机制为模板服务；W3 模板包是本 PRD 唯一直接改观感的交付。  
5. **海报旁路照抄 GCS 轨 B**：无争议。  
6. **W1 与瘦身版 S1 完全兼容**：先开工不等评审回写。

**会中新增共识**：

- 迁移期间 `main_eligibility` 桥接读取 `mainSlotPolicy` 可以存在，但**必须带 deprecation 日志 + 一个里程碑内删除**；「永久兼容层」不接受。  
- debt 报表的代表 trip 集与 [BQP 8 本](../ROADMAP-PHASE18-BOOK-QUALITY.md)对齐，不另起集合。  
- 非对称 hero 模板（W3）须同步检查渲染 token（gutter/bleed），避免「YAML 合法但渲出来不像设计稿」。

---

## 5. Must-Fix（阻塞 W2 合码 · 须回写 PRD v0.2.0）

| ID | 议题 | 来源席位 | 要求（冻结一字面） | 挡 |
|----|------|----------|-------------------|----|
| **BLK-TPC-01** | mix_fallback 可行性定义 | 算法 / 测试 | 钉死：模板可入 fallback 当且仅当**每字母** `template_required(letter) ≤ window_available(letter)`（`any`/`main` 槽按 `eligibleAspectKinds` 归置）；**square 归置规则**写死（库无 S 槽时 S 资产计入 P 或 L 的映射及其优先序）；AC-TPC-03 删除「或明确 mix_fallback」逃生门，改为「混向窗候选集不得含方向不可行模板，fallback 须显式 reason」 | W2 |
| **BLK-TPC-02** | mainSlotPolicy 迁移范围修正 | 架构 / 开发 | PRD §4.2 改写：① 列**全部 8 个调用点**迁移清单；② `asset_native_ar` 等共享工具先搬 `layout_contract/`（或等价中立位置）；③ 迁移拆两步——W2 桥接 + 等价 fixture，**删除动作挪 W3 末**；④ W2 估时上调至 5–7d，合计口径改 **17–22 人日** | W2 |
| **BLK-TPC-03** | captionAreas 渲染链前置验证 | UI/UX / 开发 | W3 图文 SKU 前须完成渲染支持 spike（`render/chapters.py` 能消费文案区并在长图导出中正确呈现）；**不支持则图文 SKU + caption tie-break 整体挪出 V1**，W3 改为混向 + 非对称 hero 为主；D-TPC-07 标注此前置 | W3 |
| **BLK-TPC-04** | shadow diff 升格正式 AC | 测试 / 开发 | 新增 **AC-TPC-12**：W1 末在代表 corpus 上输出「倒排候选集 vs 现网 `try_order` 候选集」逐窗 diff 报告；差异 = 0 或逐条人工签核后方可切换入口；报告进仓库 | W1→W2 门 |
| **BLK-TPC-05** | 双轨收口 | 产品 | TPC 评审通过（本纪要）即**废止瘦身版 S2+ 任务卡**；[IMPLEMENTATION-LAYOUT-QUALITY-STACK-V1.md](../IMPLEMENTATION-LAYOUT-QUALITY-STACK-V1.md) 状态行标注「S1 完成后由 TPC W2 承接」；禁止两案并行开发 | 流程 |
| **BLK-TPC-06** | caption tie-break 可观测定义 | 算法 | 若图文进 V1（视 BLK-TPC-03）：钉死触发条件与 epsilon（同分带宽度）；决策日志记 `captionTiebreakApplied`；禁止无日志的隐形加分 | W3 |
| **BLK-TPC-07** | 配置 fail-loud | 测试 / 架构 | `mosaic.template_contract` 未知子键 fail-loud（勿学顶层 penalties 静默丢键）；CI 断言配置根唯一 + `layout.scoring.enabled` 默认 false（沿用 AC-TPC-09） | W2 |

---

## 6. Should-Fix（不阻塞 Kickoff）

1. debt 报表 trip 集 = BQP 8 本 SSOT；脚本与集合清单进仓库（W1）。  
2. AC-TPC-11 P95 的测量脚本与环境口径写进 ACCEPTANCE（或挪 W4）。  
3. raw 几何特征字段名沿用 MGQ（`heroProminenceRatio` / `heroCoverageRatio` / `cellAreaCv`），避免两套命名。  
4. 非对称 hero 模板绑定 CSS token（gutter/bleed/max-fill-ratio）检查项（对齐观感路线图 §6.3.1）。  
5. 海报狗粮口径：N≥5「敢发群」自评表复用 GCS 狗粮清单格式。  
6. 对外默认开启前的正式盲评承诺（D-TPC-10）在 README 状态行显式保留，防止后续被遗忘。  
7. W2 切换入口时保留一个 release 的 `contract_shadow` 对照日志（成本低，回滚有据）。

---

## 7. D-TPC 拍板汇总

| 决策 | 本场决议 |
|------|----------|
| **D-TPC-01** 合同载体 | **采纳** |
| **D-TPC-02** bag-only 匹配 | **有条件采纳** — 绑 BLK-TPC-01（可行性定义 + square 归置） |
| **D-TPC-03** 唯一求值器 | **采纳** |
| **D-TPC-04** mainSlotPolicy 收敛 | **修订采纳** — 按 BLK-TPC-02 拆两步；删除挪 W3 末 |
| **D-TPC-05** V1 不做 soft | **采纳** — raw 特征照记，G2 复议口保留 |
| **D-TPC-06** 倒排替换 if 链 | **有条件采纳** — 绑 BLK-TPC-04（shadow diff AC） |
| **D-TPC-07** 图文 tie-break | **修订采纳** — 绑 BLK-TPC-03 前置验证；不支持则挪出 V1 |
| **D-TPC-08** 手写扩库 | **采纳** — 工厂重启条件照登记 |
| **D-TPC-09** 海报继承 | **采纳** |
| **D-TPC-10** 发布口径 | **采纳** — 对外默认开须补正式盲评（Should-6 显式保留） |
| **D-TPC-11** 铁律继承 | **采纳** |
| **D-TPC-12** 守门 | **采纳** — W1 前置不变 |

---

## 8. 分席要点摘要

### 8.1 算法
- 固定 SKU 下 `hero_coverage` / `cell_area_balance` 本质是模板常量——MGQ 把它做成 runtime 罚项其实是静态重排序；TPC 声明进 YAML 的论证**成立且更诚实**。  
- 真正的 runtime 变量只有 `photoCountScale`（窗口数相关）与 hero 信号匹配（URO/heroDominance 已覆盖）。  
- mix_fallback 的「不冲突」若不定义为逐字母可行性判定，L3 时代的方向冲突 bug 会换个名字回来。

### 8.2 架构
- 收敛是对的，但 `main_eligibility` 是横切模块不是模板属性——8 个调用点里 `scorer`/`metrics`/`usage_rules` 三处属于「借用工具函数」，要先解耦再迁移。  
- reason 双命名空间（`contract:*` + `usage_rule:*`）可接受；求值器**调用** URO 引擎而非内联复制，边界干净。

### 8.3 前后端开发
- 倒排 + 求值器改动集中在 `candidates.py` / `registry`，面可控；风险全在「隐式规则丢失」，shadow diff 是唯一保险。  
- 海报 Writer 前端面小（▾ 入口 + job 状态）；`output-recipe.js` 已有未合入改动，注意合流。

### 8.4 产品
- TPC 比瘦身版少一层概念、多一个模板包，**用户可感知交付更靠前**（W3 就有新版式可看）。  
- 必须单轨：本纪要通过即收口，避免团队心智里同时存在「签名三级」与「bag-only」两套叙事。

### 8.5 UI/UX
- captionAreas 是新渲染能力不是新字段——PRD 把它当元数据写，低估了渲染/导出链工作量。  
- 非对称 hero 模板是 V1 观感上限所在，建议设计投入优先于图文 SKU。

### 8.6 用户体验（狗粮）
- 「off 逐屏一致」「narrate 不改脸」「海报不进杂志」三条信任底线全部保住。  
- debt 报表 + 并排对比的验收方式比抽象盲评分数更能回答「这次改了什么」。

### 8.7 测试 / QA
- AC 总体可测性好于三 PRD 原案（概念少、断言直）；补 BLK-01/04/07 后无假绿口。  
- 回归面：hero 类模板等价 fixture 是 W2 最大测试工作量，估 1–1.5d 单列。

---

## 9. 修正后里程碑（评审口径）

| 波次 | 内容 | 修正估时 | 变化 |
|------|------|----------|------|
| **W1** | 守门 + debt 报表 + 倒排 shadow + **diff 报告（AC-TPC-12）** | 4–5d | +diff 报告 |
| **W2** | 求值器 + eligibility + mainSlotPolicy **桥接**（不删）+ hero 等价 fixture | 5–7d | 拆两步、上调 |
| **W3** | 模板包（混向 + 非对称 hero 优先；图文视 BLK-03 spike 结果）+ 桥接删除 | 4–5d | 图文降级为条件项 |
| **W4** | `poster_bric` Writer + compare CLI + 狗粮周 | 4–5d | 不变 |
| **合计** | — | **17–22 人日** | 原 15–19 上调 |

---

## 10. 下一步

- [ ] BLK-TPC-01～07 回写 PRD → **v0.2.0**（Owner：开发负责人；BLK-05 由产品执行收口）  
- [ ] 更新 [IMPLEMENTATION-LAYOUT-QUALITY-STACK-V1.md](../IMPLEMENTATION-LAYOUT-QUALITY-STACK-V1.md) 状态行（S2+ 由 TPC 承接）  
- [ ] 更新 [docs/README.md](../README.md) TPC 状态行（Conditional Go）  
- [ ] **W1 可立即 Kickoff**（与瘦身版 S1 同物）：守门修复 → debt 报表 → 倒排 shadow + diff  
- [ ] captionAreas 渲染 spike 排入 W2 间隙（决定 W3 图文去留）  

---

## 11. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| 结案 | 2026-07-18 | 七席 Conditional Go；D-TPC-01～12 拍板（2 项修订、2 项有条件）；BLK-TPC-01～07 成立；估时修正 17–22 人日；可 Kickoff W1 |
