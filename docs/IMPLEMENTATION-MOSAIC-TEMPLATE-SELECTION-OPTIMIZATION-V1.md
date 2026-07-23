# IMPLEMENTATION · 拼图模板选型与使用优化 V1（MTSO）

| 属性 | 内容 |
|------|------|
| **文档版本** | **v0.2.0** |
| **对应 PRD** | [PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md](./PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) **v0.2.0** |
| **验收** | [ACCEPTANCE-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md](./ACCEPTANCE-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) |
| **评审** | [mtso-mosaic-template-selection-v1-review-2026-07-23.md](./acceptance-records/mtso-mosaic-template-selection-v1-review-2026-07-23.md) · Conditional Go |
| **实施前调研** | [mtso-dev-feasibility-2026-07-23.md](./acceptance-records/mtso-dev-feasibility-2026-07-23.md) · **SUP 默认已产品认可** |
| **DOC-STATUS** | **active** |
| **状态** | **PR-A ✅ · PR-B/C1 in progress**（同分支 `feat/mtso-pr-a-lifecycle`；**PR-C2 ⛔ O-1**） |
| **更新日期** | 2026-07-23 |

> **定位**：把 MTSO PRD + 七席 + 开发可行性 SUP 展开为可执行任务卡。  
> **铁律**：PR-A → B → C1 → C2 → D；**禁止**单 PR 塞满；**禁止** PR-A 改窗序/机会状态机。  
> **本版重点**：**M1 / PR-A** 全量任务卡；PR-B+ 仅列大纲与风险挡门。

---

## 0. 已锁定决策（实施源）

以 PRD §4 + 可行性 §5 SUP 为准。实施高频引用：

| ID | 一句话 |
|----|--------|
| **D-01** | TPC ≠ 实验解锁；`template_experiments` 三元组 |
| **D-07 / SUP-03** | 新 opportunity 与旧 `hero_reserve` 隔离；MTSO ON 时跳过旧 reserve 过滤（PR-B） |
| **SUP-06** | 强竖硬拒不可 undo（PR-C1；不靠 URO 默认开） |
| **SUP-08** | `experiments.enabled` + 空 cohort → **无人可见** |
| **D-13 / AC-11** | 尝试率+转化率双阈值；禁六图屏数 KPI |
| **O-2** | `selection_optimization` 默认 false 至 M3 |

### 0.1 SUP 默认（产品已认可 · 2026-07-23）

| SUP | 锁定 |
|-----|------|
| **01** | 结构合格窗 = `ids[start:start+6]`；square/tall 不计入合格 P/L 池 |
| **02** | 单 eligible main 且 gap=`inf` → **结构合格** |
| **03** | `selection_optimization.enabled` → compose **跳过**旧 `hero_reserve` 过滤 |
| **04** | 重排：structural six 覆盖 > exact-tail（剩余 sizes）> single-portrait-tail |
| **05** | size6 尝试失败 → opportunity **released** |
| **06** | `mixed_portrait_is_hero` 硬拒且 **不可** usage undo |
| **07** | 孪生可双候选；emit tie-break → canonical；配额按 family |
| **08** | cohort 空 = 无人可见 |
| **09** | PR-C2 前 O-1 ≥1 冻结几何稿 |
| **10** | M2 合码前拆 ACCEPTANCE（本 IMPLEMENTATION 已起；ACCEPTANCE 随 PR-B） |

---

## 1. PR 切片与退出

| PR | 里程碑 | 任务卡 | 退出（最低） | 模板误用风险 |
|----|--------|--------|--------------|--------------|
| **PR-A** | M1 | T-00～07 | AC-01 · 02 · 03（字段）· BLK-01/02/07 | **低**（见 §4） |
| **PR-B** | M2 前半 | T-10～14 | AC-04～06 · 11a · 13 | **中**（须隔离 reserve） |
| **PR-C1** | M2 混向硬拒 | T-20～21 | AC-07（rescue 路径） | **中低** |
| **PR-C2** | M2 SKU | T-22～25 | AC-07/08 · O-1 | **中**（新几何） |
| **PR-D** | M3 | T-30～32 | AC-11/12 · 转正或归档 | 狗粮挡 |

**合并规则**：PR-A 未绿不得合 PR-B；C2 不得早于 O-1 冻结稿。

---

## 2. 任务卡 · PR-A（M1）详述

### T-MTSO-00 · 文档/狗粮叙事对齐（同 PR-A）

| 项 | 内容 |
|----|------|
| **动作** | 更新 `docs/acceptance-records/tpc-local-dogfood-GUIDE.md`、`docs/config-tpc-dogfood.example.yaml`：TPC ON **不再**自动可见 experimental；实验须 `template_experiments` |
| **新增** | `docs/config-mtso-experiments-dogfood.example.yaml`（enabled+allowlist+cohort 样例） |
| **验收** | 文档无「contract=true ⇒ W3 rail 进候选」的现行表述 |
| **估时** | 0.3d |

---

### T-MTSO-01 · 配置：`template_experiments` + `selection_optimization` 壳

| 项 | 内容 |
|----|------|
| **动作** | `travelogue/config/mosaic.py`：新增 dataclass + `mosaic_from_dict` 解析；未知键 fail-loud（对齐 `template_contract`） |
| **语义** | `selection_optimization.enabled=false`（默认）时子项**全部无效**；本 PR **不实现**子逻辑，只立配置壳 + `effective_selection_optimization_enabled()` |
| **样例** | `config.yaml.example` 注释块，默认 false |
| **路径** | `config/mosaic.py` · `config.yaml.example` · unit parse 测 |
| **验收** | 解析往返；父 OFF 时 effective=false |
| **估时** | 0.5d |

---

### T-MTSO-02 · `lifecycle_admit` 单一判定（核心）

| 项 | 内容 |
|----|------|
| **动作** | 新建（建议）`travelogue/layout_engine/mosaic/lifecycle.py`：`lifecycle_admit(pattern_id, *, app/cfg, trip_id=None) -> AdmitResult(ok, reason)` |
| **规则** | ① deprecated/disabled → `lifecycle_deprecated`；② experimental → 仅 experiments 三元组；③ ga/beta 按 rollout；④ overrides_disable / runtime disabled |
| **接线** | 替换 `_contract_unlocks_experimental` 在 `mosaic_registry` / `mosaic_pattern_disabled` 的用法；**删除**「TPC ON ⇒ experimental」路径 |
| **LTE OFF** | 硬禁补齐至少 `2p3l-equal`（与 deprecated 对齐） |
| **验收** | AC-MTSO-01/02；contract ON + experiments OFF → rail/1l3p **不在** registry |
| **估时** | 1.0–1.5d |

---

### T-MTSO-03 · deprecated 构造期拒绝（S-06）

| 项 | 内容 |
|----|------|
| **动作** | `legacy.build_legacy_screen`：size 6/8/9 若目标 pattern deprecated/disabled → 直接 `None`（不依赖 append 末尾） |
| **验收** | 负例：构造函数返回 None；append 仍保持双重保险 |
| **估时** | 0.5d |

---

### T-MTSO-04 · 漏斗 raw 字段 schema（先立后填）

| 项 | 内容 |
|----|------|
| **动作** | 扩展 `MosaicWindowLog` / `to_dict`：`baseWindowOrder` · `effectiveWindowOrder` · `reorderReason` · `structurallyQualifiedSix` · `admitSixHero` · `sixHeroOpportunityState` · `sixHeroFamilyId` · `quotaSnapshot` · `rejectFunnel`（list） |
| **PR-A 填值策略** | 窗序填实际尝试序（与今日一致即可）；structural/admit/opportunity 填默认 `false`/`idle`/null；`sixHeroFamilyId` 在 winner 为孪生时解析 canonical；`rejectFunnel` 可从现有 rejected 映射一层 |
| **铁律** | AC **断言 raw capture**（`drain_mosaic_capture`），不依赖 Top-3 裁剪后的展示日志 |
| **路径** | `mosaic/log.py` · hook 填字段 · fixture 测 |
| **验收** | AC-03 字段存在且类型稳定 |
| **估时** | 1.0d |

---

### T-MTSO-05 · 孪生 family resolver（只记录）

| 项 | 内容 |
|----|------|
| **动作** | `six_hero_family_id(pattern_id) -> canonical`；canonical = `screen-mosaic-6-main-hero-plus-5` |
| **PR-A** | 仅写日志，**不改**候选/打分/配额 |
| **估时** | 0.2d |

---

### T-MTSO-06 · 测试改写与新增

| 项 | 内容 |
|----|------|
| **改写** | `tests/unit/layout_engine/test_template_contract_w3.py`：`test_enabled_contract_emits_w3_candidate` → **contract ON 不再 emit W3 experimental**；另增 experiments 三元组正例 |
| **新增** | `test_mtso_lifecycle_a.py`（或同类）：deprecated 全路径；cohort 空 fail-closed；LTE OFF 硬禁 equal |
| **保留** | `test_mosaic_2p3l_slot_order` / `test_lte_integration` deprecated 断言 |
| **验收** | CI unit 绿；无「contract⇒rail」旧期望 |
| **估时** | 1.0d |

---

### T-MTSO-07 · PR-A 回归护栏（防模板误用）

| 项 | 内容 |
|----|------|
| **动作** | 固定 corpus（或合成）`selection_optimization=false` + `experiments=false`：与改前 **MCS-11 候选集一致**；逐屏 compare 可选（至少 pattern 直方图无 experimental） |
| **脚本** | 可复用 `layout_compare` / 最小 unit：`mosaic_registry()` keys ⊆ GA∪beta（rollout>0） |
| **验收** | 默认配置下 **零** experimental / deprecated 新曝光 |
| **估时** | 0.5d |

---

### PR-A 合计

| 项 | 值 |
|----|-----|
| **估时** | **3.5–5.5 人日** |
| **退出** | AC-01 · 02 · 03 · T-07 护栏 · GUIDE 更新 |
| **不做** | 窗序重排 · opportunity · 新 YAML · 改 UR-04 默认 |

---

## 3. PR-B / PR-C1 落地（本分支）

### PR-B · 六图机会（T-10～14）

| 卡 | 状态 | 落点 |
|----|------|------|
| T-10 `qualify_hero_six` | ✅ | `mosaic/hero_six.py`（SUP-01/02） |
| T-11 opportunity + 跳过旧 reserve | ✅ | `planner_state.hero_six_*` · compose SUP-03 |
| T-12 重排 / released | ✅ | `hook.try_mosaic_window`（SUP-04/05） |
| T-13 family 配额 | ✅ | `can_use_large_mosaic` / `note_screen`（SUP-07） |
| T-14 单测 | ✅ | `tests/unit/layout_engine/test_mtso_pr_b_c1.py` |
| ACCEPTANCE | ✅ | 已拆 |

### PR-C1 · 混向硬拒（T-20～21）

| 卡 | 状态 | 落点 |
|----|------|------|
| T-20 硬拒不可 undo | ✅ | `candidates.py` · `usage_rule:mixed_portrait_is_hero`（SUP-06） |
| T-21 rescue | ☑ | 沿用 `_try_mcs_single_hero_rescue`（无新几何） |

### PR-C2 · 新 SKU（T-22～25）— **不开码**

- **⛔ O-1**：无冻结竖主 1P4L / 2P3L 几何稿前不写 YAML/CSS/`lte_policy`

### PR-D · 狗粮转正（T-30～32）

- compare · 盲评 · GA 或归档

---

## 4. 模板使用错误风险评估（落地会不会选错模板）

### 4.1 结论先说

| 阶段 | 引入「选错模板」风险 | 说明 |
|------|----------------------|------|
| **PR-A（本切片）** | **低** | 只收紧可见性，不改 MCS-11 打分与窗序；默认配置下候选集应变**更干净** |
| **PR-B** | **中** | 改变谁先尝试 6；隔离旧 reserve 不当会反向改变 4/5 节奏 |
| **PR-C1** | **中低** | 强竖不再进横主竖辅——这是**纠错**；rescue 过度会变碎 |
| **PR-C2** | **中** | 新几何若主从不达标会「新的假拼图」；靠盲评挡 |
| **PR-D** | 过程风险 | 转正门槛防回潮 |

**总体**：按 PRD **分阶段**落地，**不会**在默认现网上突然「乱选模板」；最大风险在 M2 状态机与混向硬拒的边界，不在 PR-A。

### 4.2 PR-A：为什么几乎不会引入误用

| 机制 | 影响 | 误用？ |
|------|------|--------|
| 去掉 TPC→experimental | 默认/仅 contract ON 时，rail/1l3p/editorial **不再进候选** | **否**——消除误曝光；与产品「退役」叙事一致 |
| deprecated 更早拒绝 | 本就不会进 MCS-11 | **否** |
| 日志字段 | 只观测 | **否** |
| 默认 `experiments/selection_optimization=false` | 行为对齐仓库及格线 MCS-11 | **否** |

**唯一需注意的「行为变化」**（有意、正确）：

- 本机曾靠 `template_contract.enabled=true` 看到的 `2p3l-rail` / `1l3p-rail` **会消失**，除非显式开 `template_experiments`。  
- 这不是误用，而是 **修泄漏**；手测前须读 GUIDE（T-00）。

**回归护栏**：T-07 固定默认配置下 registry ⊆ 非实验活跃集。

### 4.3 PR-B：可能的误用模式与缓解

| 误用模式 | 原因 | 缓解（已锁定） |
|----------|------|----------------|
| 不合格六图被强推 | 资格过松 | SUP-01/02；main_ar/gap 硬条件 |
| 合格六图仍被 4 抢走 | 重排时机错 | exact-tail **前**覆盖；AC-04 |
| 章内四宫变少、版面变碎 | armed 作用域过大 / 双 reserve | SUP-03/05；仅同 cursor；AC-05 |
| 孪生双计消耗 large 配额 | 两 id 分开记账 | SUP-07；AC-13 |
| dense 被变相加额度 | admit 预扣 | 禁止预扣；只读后 `note_screen` |

### 4.4 PR-C：可能的误用模式与缓解

| 误用模式 | 原因 | 缓解 |
|----------|------|------|
| 弱竖也被拆成单图 | 硬拒阈值过猛 | gap 阈值与 URO 共用；横强 fixture 必绿（AC-07） |
| 强竖仍出横主竖辅 | usage undo | SUP-06 不可回补 |
| 新 2P3L 像等权假拼图 | 几何偷懒 | 主从比+截图；不过不转 GA |
| experimental 误进 policy | 流程错 | C2 禁写 `lte_policy` |

### 4.5 风险矩阵（实施门禁）

| ID | 风险 | 等级 | 挡在 |
|----|------|------|------|
| **R-SEL-01** | PR-A 后狗粮仍开 contract 却期望见 rail | 低 | T-00 GUIDE |
| **R-SEL-02** | PR-B 双状态机导致 4/5 异常稀 | **高** | SUP-03 + AC-05 |
| **R-SEL-03** | PR-C undo 回补导致竖强误用横主 | **高** | SUP-06 |
| **R-SEL-04** | 新 SKU 几何差 | 中 | O-1 + 盲评 |
| **R-SEL-05** | 默认配置候选集漂移出 MCS-11 | 中 | T-07 |
| **R-SEL-06** | 日志 Top3 裁剪导致 AC 假绿 | 中 | raw capture only |

### 4.6 开发负责人结论（模板误用）

1. **PR-A 可安心合**：收紧可见性，不改「谁在 MCS-11 里怎么赢」；模板使用只会更少踩实验坑。  
2. **真正会改「选用结果」的是 PR-B/C**——那是产品要的纠错（六图能上场、竖强不当配角），须靠 fixture+compare 证明「纠错 ≠ 乱选」。  
3. **回滚安全**：全部默认 OFF；关 `template_experiments` / `selection_optimization` 即回 MCS-11 及格线（AC-10）。

---

## 5. PR-A 文件清单（预览）

| 路径 | 动作 |
|------|------|
| `travelogue/layout_engine/mosaic/lifecycle.py` | **新建** admit |
| `travelogue/layout_engine/mosaic/lte_adapter.py` | 拆 contract 解锁；接线 admit |
| `travelogue/layout_engine/mosaic/legacy.py` | 构造期拒 deprecated |
| `travelogue/layout_engine/mosaic/log.py` | 字段扩展 |
| `travelogue/layout_engine/mosaic/hook.py` | 填日志默认字段（不改序） |
| `travelogue/config/mosaic.py` | 配置壳 |
| `config.yaml.example` | 注释默认 |
| `docs/config-mtso-experiments-dogfood.example.yaml` | **新建** |
| `docs/acceptance-records/tpc-local-dogfood-GUIDE.md` | 叙事修正 |
| `docs/config-tpc-dogfood.example.yaml` | 交叉提示 |
| `tests/unit/layout_engine/test_mtso_lifecycle_a.py` | **新建** |
| `tests/unit/layout_engine/test_template_contract_w3.py` | 改期望 |

---

## 6. Kickoff 检查单（PR-A）

- [x] 七席 Conditional Go  
- [x] SUP 默认产品认可  
- [x] IMPLEMENTATION M1 切片就绪（本文）  
- [x] 开分支 `feat/mtso-pr-a-lifecycle`  
- [x] T-00～07 代码落地；相关 unit 绿（待合入 / 全量 CI）  
- [ ] 本机将 `template_contract` 与实验开关叙事对齐（建议 contract 改回 false，或显式 experiments）  

---

## 7. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.1.0** | 2026-07-23 | 首版：M1/PR-A 全量任务卡 + 模板误用风险评估；SUP 锁定；PR-B+ 大纲 |
