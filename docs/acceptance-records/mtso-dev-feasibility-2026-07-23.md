# MTSO · 开发负责人实施前可行性调研

| 属性 | 内容 |
|------|------|
| **日期** | 2026-07-23 |
| **角色** | 开发负责人（落地 PR-A→D） |
| **材料** | [PRD MTSO v0.2.0](../PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) · [七席评审](./mtso-mosaic-template-selection-v1-review-2026-07-23.md) |
| **结论** | **M1 / PR-A 可开工**；SUP-01～10 **产品已认可**（2026-07-23）；PR-B **不得**在现有 `hero_reserve` 上打补丁 |
| **状态** | active · 已转入 [IMPLEMENTATION](../IMPLEMENTATION-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) |

---

## 0. 一句话

PRD 方向与代码事实对齐，且七席已收口主矛盾；但作为落地负责人，我认为 **v0.2 仍把三处「现网已有半成品」写得过轻**——UR-04（默认关 + 可回补）、`hero_reserve`（跨 cursor）、孪生六图双候选——若不在开工前钉死，M2 会做出「看起来像机会保护、实际双状态机打架」的实现。

---

## 1. 总判断

| 维度 | 评分 | 说明 |
|------|------|------|
| 问题真伪 | ✅ | F-01～F-12 与代码一致；六图曝光 0 / TPC 解锁 experimental 可复现 |
| M1 可开工性 | ✅ | lifecycle 单点 + 配置 + 日志字段，不碰窗序 |
| M2 合同完备度 | ⚠ | 资格算法细节、与旧 reserve 关系、UR-04 硬拒语义未钉死 |
| M2/PR-C 视觉前置 | ⚠ | O-1 竖主几何仍开放；工期不可压 |
| 与 P21 冲突风险 | 低 | 若严格「不预扣配额、不增 dense」则可控 |
| 测试债 | 中 | 现有 TPC 测试断言「contract ON ⇒ rail 可候选」，与 D-01 **相反**，必须改语义而非只加测 |

---

## 2. 代码对照：PRD 主张 vs 现实

| # | PRD / 评审主张 | 代码现实 | 风险 | 开发建议 |
|---|---------------|----------|------|----------|
| **C-01** | TPC 不解锁 experimental | `_contract_unlocks_experimental` 仅看 `template_contract.enabled`；`mosaic_registry` / `mosaic_pattern_disabled` 双调用 | 本机狗粮已证实 registry→21 | **PR-A 核心**：统一 `lifecycle_admit`；删/改该耦合 |
| **C-02** | deprecated 永不 emit | LTE 路径 disabled；`append_legacy_window` 末尾再挡；但 `build_legacy_screen` **仍可构造** 6/8/9 deprecated | 未来调用方旁路 | PR-A 负例覆盖「构造后拒」；建议同 PR 做 S-06：构造期直接 `None` |
| **C-03** | §5.5 漏斗字段 | `MosaicWindowLog` 有 winner/reject Top3/candidateSource；**无**窗序/两段资格/机会状态/配额快照；window 日志裁 Top-3 | AC 假绿 | 原始字段写 `to_dict`/capture；AC **只断言 raw**（`drain_mosaic_capture`） |
| **C-04** | 配置易加 | `MosaicConfig` dataclass + nested parser；`template_contract` 未知键 fail-loud | 新段未解析会被静默忽略 | 新增 `TemplateExperimentsConfig` / `SelectionOptimizationConfig`；`effective_*` 强制父 OFF |
| **C-05** | 六图局部 6→5→4 | `try_mosaic_window`：`planner sizes` → exact-tail → single-portrait → loop | 预检若放 loop 内则 4 已胜出 | 在 **exact-tail 之前**算 structural；armed 时覆盖 sizes |
| **C-06** | 新机会状态机 | 已有 LTN C5 `hero_reserve`：任一 scored main → arm，挡**全章** equal-weight dense（`compose.py`） | **作用域与 D-07 冲突** | **替换/隔离**，禁止双机并行；PR-B 开工条件 |
| **C-07** | dense 不双记账 | `can_use_dense_*` 内已调 large；hook 再调一次；记账只在 `note_screen` | 若 admit「预扣」会双扣 | structural **零读配额**；admit **只读**；记账仍只 `note_screen` |
| **C-08** | 强竖禁横主竖辅 | **UR-04 已存在**且测过；但 `usage_rules.enabled` **默认 false**；且 `_restore_if_usage_emptied_candidates` 可把 UR 拒因**回补** | 仅开 URO 或只靠 YAML 会漏 | MTSO ON 时 `mixed_portrait_is_hero` = **不可 undo 硬拒**；或把 UR-04 移出 undo 链 |
| **C-09** | 签名扩 (2,3)/(0,6) | whitelist 仅 4/5 混签；miss 安全回落 | `(1,4)` **无法表达竖强/横强** | 签名只缩窄 mix；竖强分支放 candidate/硬拒，不塞进静态 whitelist |
| **C-10** | 孪生六图家族 | 两 id 同进 `MOSAIC_6`、同走 `_order_hero_six` | 配额/机会双计 | PR-A 可先只记 `sixHeroFamilyId`；PR-B 强制家族去重 |
| **C-11** | hero gap 可复用 | `main_eligible_hero_score_gap` + `usage_rules.hero_gap_threshold` | 单 eligible main 时 gap=`inf`；`_order_hero_six` 读 runtime cfg | 抽纯函数 `qualify_hero_six(..., cfg=)`；PRD 补「inf 是否合格」 |
| **C-12** | 新 SKU 进活跃集 | policy→codegen→schema→active_set 六写点已有清单 | experimental 误写 policy = 立刻 GA | PR-C：YAML+CSS+schema **不进** policy；转正才 `--sync-python` |

---

## 3. 分 PR 落地建议

### 3.1 PR-A（M1）· 建议立即开工

**范围（严守）**

1. `lifecycle_admit(pattern_id, cfg, trip_id)` 单一判定  
2. 拆 `_contract_unlocks_experimental`；`template_experiments` 三元组  
3. deprecated：candidate / self-heal / legacy append 负例；可选 S-06 构造期拒绝  
4. 漏斗 raw 字段扩展（可先填 `null`/默认，但 schema 先立）  
5. 改写冲突测试：`test_enabled_contract_emits_w3_candidate` → contract≠experiments  
6. 更新 `tpc-local-dogfood-GUIDE.md` + `config-tpc-dogfood.example.yaml` 一句：TPC ON **不再**自动看见 experimental  

**明确不做**：窗序重排、机会状态机、新 YAML SKU。

**工期**：3.5–5 人日（含 S-06 则 +0.5）。

**验收锚点**：AC-01/02/03（字段存在即可先绿）+ BLK-01/02/07。

### 3.2 PR-B（M2 前半）· 开工挡门

**必须先书面确认（§5）后再写代码**，否则易返工：

- 与旧 `hero_reserve`：替换 / 删除 / feature-gate 三选一（推荐：**MTSO ON 时禁用旧 reserve 对 dense 的过滤**）  
- 重排 precedence 矩阵（six / exact-tail / single-portrait / collage-first）  
- size=6 尝试失败后 opportunity 是否 `released`  

**实现要点**

- structural：`orientation + _order_hero_six + gap`，**禁止**调用 `window_has_candidates`（避免三次生成）  
- armed：仅 `start==cursor` 且 sizes 含 6 时挡 4/5  
- family：canonical `…6-main-hero-plus-5`  

**工期**：5–7 人日。

### 3.3 PR-C（混向 SKU）· 拆两段

| 段 | 内容 | 依赖 |
|----|------|------|
| **C1** | `mixed_portrait_is_hero` 硬拒 + rescue（可无新几何） | PR-A；URO 默认关的补偿 |
| **C2** | 竖主 1P4L + 2P3L 主从 YAML/CSS/截图 | **O-1 冻结稿** |

**工期**：C1 2–3 人日；C2 4–6 人日（含视觉）。

---

## 4. 工期总表（现实）

| 阶段 | 人日 | 备注 |
|------|------|------|
| PR-A | 3.5–5 | 可并行写 dogfood GUIDE |
| PR-B | 5–7 | 含旧 reserve 隔离 |
| PR-C1 | 2–3 | 硬拒，无新几何 |
| PR-C2 | 4–6 | 卡 O-1 |
| PR-D 狗粮/转正 | 2–3 | 含 compare |
| **合计** | **≈17–24** | 不含视觉出稿日历时间 |

七席估时偏乐观处：把「UR-04 已有」当成混向已完成——**默认关 + undo 回补**使它不能当 MTSO 交付。

---

## 5. 请产品/算法在编码 M2 前确认的补充（PRD 补丁清单）

| ID | 补充项 | 建议默认（开发侧） |
|----|--------|-------------------|
| **SUP-01** | `structurallyQualifiedSix` 精确算法：窗口是否必须 `ids[start:start+6]`；square/tall 是否一律不合格 | 必须连续 6；square/tall 不计入合格 landscape/portrait 池 |
| **SUP-02** | 单 eligible main 时 gap=`inf` 是否结构合格 | **是**（唯一合格主图即合格） |
| **SUP-03** | 旧 `hero_reserve` vs 新 opportunity | MTSO `selection_optimization` ON → **跳过** compose 内旧 reserve 过滤 |
| **SUP-04** | 重排 precedence | structural six 覆盖 > exact-tail（对剩余 sizes）> single-portrait-tail；collage-first 另矩阵 |
| **SUP-05** | size6 尝试但合同/评分失败后 | opportunity → **released**（允许后续 cursor 再 arm） |
| **SUP-06** | `mixed_portrait_is_hero` 与 UR-04 | MTSO 路径：**硬拒且不可 undo**；可与 UR-04 共用判定函数 |
| **SUP-07** | 孪生胜出策略 | 评分可双候选；emit 前 tie-break 选 canonical；配额按 family |
| **SUP-08** | cohort 空列表语义 | `enabled=true` 且 `cohort_trip_ids=[]` → **无人可见**（fail-closed） |
| **SUP-09** | O-1 最低交付 | PR-C2 前至少 1 张冻结几何（建议左满高竖 main）；否则 C2 不开码 |
| **SUP-10** | M2 文档挡门 | 合码前拆 `IMPLEMENTATION` + `ACCEPTANCE`（BLK-08）；M1 可继续用 PRD §8–9 |

---

## 6. 风险（开发视角）

| 风险 | 等级 | 缓解 |
|------|------|------|
| 双状态机（旧 reserve + 新 opportunity） | **P0** | SUP-03；单测锁「armed 不挡无关 cursor 的 landscape-4」 |
| UR-04 undo 回补导致强竖仍出横主 | **P0** | SUP-06；空候选时也不得恢复该 pattern |
| 改 TPC 测试破坏 dogfood 叙事 | P1 | GUIDE 同步；实验另开配置样例 `config-mtso-dogfood.example.yaml` |
| 漏斗只写展示 Top3 | P1 | AC 绑 raw capture |
| O-1 拖延 PR-C | P2 | C1/C2 拆分，不堵 M1/M2 |
| 预检调用完整 candidate 生成拖慢排版 | P2 | structural 轻量路径 |

---

## 7. 建议的开工顺序（开发锁定）

```text
1) 产品/算法书面确认 SUP-01～10（可先只确认 SUP-03/06/08 以开 PR-A）
2) PR-A 合入（lifecycle + 日志 schema + 测试改写 + GUIDE）
3) 拆 IMPLEMENTATION/ACCEPTANCE（M2）
4) PR-B（隔离旧 reserve + 两段资格 + 机会）
5) PR-C1 硬拒 → 视觉冻结 O-1 → PR-C2 SKU
6) PR-D 狗粮/盲评/转正
```

---

## 8. 给产品的直接建议

1. **先合 PR-A**：立刻消除「退役又出现」的误判源，且风险最低。  
2. **不要让 M2 依赖「打开 URO 默认」**：那是另一主题的开关，会改变全局行为；MTSO 应自带硬拒。  
3. **竖主新模板可以晚于六图机会**：C1 硬拒 + portrait-1 rescue 已能改善「竖被压」；几何稿不应挡 PR-B。  
4. **本机 `template_contract.enabled=true` 请在 PR-A 后改回 false**，或显式改挂 `template_experiments`，避免继续污染手测归因。

---

## 9. 签名

| 角色 | 意见 |
|------|------|
| 开发负责人 | **同意 Kickoff PR-A**；M2 以 §5 SUP 确认后再开码 |
