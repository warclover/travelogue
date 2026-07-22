# CSC 根因复核与根治方案 · 2026-07-22

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | **active**（登记见 [DOC-STATUS.md](../DOC-STATUS.md)） |
| **对象** | [PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md](../PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md) v0.2 + 九席评审 |
| **性质** | 产线代码复核后的**根因 / 根治**决议；优先于「逐项还债清单」 |
| **结论** | 症状治理（藏设置、删 shim、拆文件）必要但不充分；**根治 = 建立唯一 Happy Path Recipe 合同 + 能力预算机制** |
| **证据时点** | 2026-07-22 对照 `master` 工作区代码 |

---

## 0. 一句话

表面积膨胀的根不是「文件太大 / 文档太多」，而是：

> **系统从未拥有「默认启用什么」的单一真相源；每个 Phase 以「加一个默认开的开关」为扩展单位，设置 UI 再镜像这些开关。**

因此最优方案不是继续并列打六场战役（Profile / 配置 / facade / legacy / UI / curate），而是先立 **一条 Recipe 合同**，再让其余五项变成该合同的执行器。

---

## 1. 产线铁证（复核）

| 证据 | 事实 | 说明 |
|------|------|------|
| `StudioProfile.studio_default` | 仅 `run_clustering` / `apply_editorial_hints` / `export_layout` / ingest 并行等 | **编排薄面**，不是产品 Happy Path |
| `AppConfig` 布尔字段 | **150** 个；默认 **True ≈ 97** / **False ≈ 53** | True=静默默认面（隐患主体）；False=防火墙（非待开启清单）· 决议见 PRD §0.0.1 |
| `mosaic.enabled` / LTE 等 | 默认 `True` | 不在 Profile 里，却进默认成册 |
| LSE CAP | 默认全 `False` + FROZEN | 算法研究面已外置——**好模式**，但未推广到产品默认集合 |
| `layout_engine.__all__` | `[]` | facade 合同未落地 |
| `default_web_layout_engine` | mobile→`legacy`；web/auto→可 `screens` | 双引擎是**出口 strangler 未完成**，非缺 enum |
| 设置暴露 | `studio_config_expose` + `patch_config_file` + HTML 手工并联 | UI 随白名单加项而长 |
| 局部 recipe 碎片 | Output Recipe / StrategyPack / LTE lifecycle / aesthetic purpose profiles / phase6 snapshot | **互不统属**，拼不成 Happy Path SSOT |
| curation→layout_engine | ~20 import，多数经 `adapter` | 进口已大半收敛；缺的是**锁死 + 公开符号** |

---

## 2. 症状 vs 根因（复核九席六项）

| 议题 | 若只治症状 | 根因 |
|------|------------|------|
| 冻结 Profile | 改名 / 文档化 `studio_default` | Profile **不拥有**默认能力集合；真相在 AppConfig |
| 配置 ≤10 | 挪 yaml、藏键 | **无 L0/L1 预算**；Phase 默认加根且常默认 True |
| facade | 补 `__all__` | 必要，但是**进口锁**；不阻止新默认 True |
| legacy ceiling | 删字符串 / shim | **出口×引擎未切完** + 正交 flag；债务表是执行器 |
| 设置 UI | 折叠高级 | UI=expose/PATCH 镜像；无「仅 L1 可生成控件」 |
| 拆 curate | 搬文件 | **产品子阶段未进编排合同**；orchestrator 把策展+排版压成黑盒 |

**九席务实优先级仍然对**（先 W0/W1 用户可见面），但必须升级为：**W0/W1 交付的核心产物是 Recipe 合同，而不是又一份说明文。**

---

## 3. Top 5 根因（按杠杆）

1. **无单一 Happy Path 合同**（Profile ≠ Config ≠ 各 enable）  
2. **配置加性生长 + 默认 True 文化**（97/150）  
3. **Settings = 白名单镜像，无产品预算**  
4. **出口×引擎 strangler 未完成 + facade 空合同**  
5. **产品 stage / 文档状态未建模**（编排过粗；PRD 默认永远可读）

---

## 4. 根治方案（首选）：Happy Path Recipe Registry

### 4.1 核心思想

引入**唯一**运行时合同（名称建议 `HappyPathRecipe`，`recipe_id="studio_default"`）：

```text
HappyPathRecipe
├─ orchestration   ← 今日 StudioProfile.studio_default 字段
├─ capabilities[]  ← 默认 ON/OFF 的产品能力（mosaic/LTE/bookends/scoring/LSE/…）
├─ layout_exit     ← mobile/web/auto × legacy|screens 的产品绑定（显式）
├─ l1_keys[]       ← ≤10 结果旋钮（设置 UI 唯一生成源）
└─ advanced[]      ← 仅 Advanced/admin；永不进主 CTA
```

规则：

| 规则 | 含义 |
|------|------|
| **R1 单一真相** | `run_trip` / Studio 导入主路径只读 Recipe；禁止各模块再私自「默认 True 即启用」绕过 |
| **R2 预算替换** | 新 Phase **不得**净增 L1；要进默认必须替换预算或进 Advanced |
| **R3 UI 派生** | 设置常用区 **只渲染** `l1_keys`；禁止手写第三套控件表长期分叉 |
| **R4 快照测试** | Recipe JSON/YAML 黄金快照 = AC-CSC-01；变更走评审 |
| **R5 祖父条款** | 现行默认 ON 能力 W0 盘点写入 Recipe；不强制本波盲测重审 |
| **R6 研究外置** | LSE CAP / templates-admin 继续独立；不得写入 Recipe.capabilities 默认 ON |

### 4.2 与已有碎片的关系（复用，不重造）

| 已有 | 并入方式 |
|------|----------|
| `StudioProfile.studio_default` | → Recipe.orchestration（**身份保留**，九席 BLK-01） |
| LSE `effective_capabilities` | → Advanced；保持 FROZEN/默认关 |
| Output Recipe | → 导出子合同；由 Recipe 声明是否启用 |
| aesthetic purpose_profiles | → 静默能力（无 UI）；可标 `silent: true` |
| LTE lifecycle | → 模板治理；不进 L1 |
| `studio_config_expose` | → **改为由 Recipe.l1_keys 生成**（绞杀手工白名单） |

### 4.3 其余 CSC 波次如何变成「执行器」而非「并列战役」

| 波次 | 根治视角下的角色 |
|------|------------------|
| **W0** | 盘点 → **写出第一版 Recipe 草案 + L0/L1 键表 + 债务表**（合同初稿） |
| **W1** | Recipe 挂载主路径 + 设置 UI 改读 `l1_keys`（用户可感） |
| **W2a** | facade = Recipe 对 layout_engine 的唯一进口 |
| **W2b/c** | curate/pipeline 棘轮 = 禁止在合同外堆默认行为 |
| **W3** | 债务/文档清退 = 合同外路径的删除预算 |

### 4.4 防再 sprawl 的硬闸（根治是否生效的判据）

若一年满足，则 CSC 只是一阵还债，半年后复燃：

1. PR 新增 `enabled: bool = True` 且影响默认成册 → **必须改 Recipe 快照**，否则 CI 失败  
2. PR 新增设置控件但不在 `l1_keys` → CI 失败  
3. PR 新增 config 顶层根进用户档 → 必须证明 L1 替换预算  

---

## 5. 备选（明确次优）

**仅 facade + 债务 ceiling + 设置折叠**：进口变干净、短期 UI 变清爽，但**下一个 Phase 仍可默认 True + 新根**。只作容量不足时的降级，不得称为 CSC 根治完成。

---

## 6. 明确不采纳的「伪根治」

| 伪方案 | 为何不根治 |
|--------|------------|
| 再写一个 `FinishThisTripProfile` 类 | 与 `studio_default` 分叉；九席已否 |
| 大拆 `curate.py` 当主故事 | 无 stage 合同则拆完仍会粘回 |
| 全文 legacy 降幅 KPI | 激励删注释 |
| 一次性砍 97 个 True | 无祖父盘点会伤成册质量；应进 Recipe 显式化后再裁 |
| 新开「能力中台」微服务 | 违反单进程 Studio / 过度设计 |

---

## 7. 建议立即执行的最小根治切片（取代散弹）

**切片 A（根合同 · 最高杠杆）**

1. 新增 `travelogue/orchestrator/happy_path_recipe.py`（或等价）  
2. 从现行 `AppConfig()` + `studio_default` **生成**第一版 Recipe 快照（只读宣告，行为暂不变更）  
3. 单测锁定快照  
4. 文档短文绑定该快照（用户语言）

**切片 B（可见面派生）**

1. `studio_config_expose` / 设置常用区改为读 Recipe.l1_keys（可先人工维护 10 键）  
2. 其余 expose 迁 Advanced  

**切片 C（锁进口）**

1. `layout_engine/api.py` + lint  
2. 新增默认能力必须改 Recipe 的 CI 钩子（可先 warning，W1 转 error）

完成 A+B 即达成「根上可控」；C 防结构回潮；债务删除可并行但不阻塞根合同。

---

## 8. 对 PRD v0.2 的修订含义

| v0.2 表述 | 根治修订 |
|-----------|----------|
| W0=基线表 | W0=**Recipe 初稿 + 基线** |
| W1=冻结 studio_default + UI | W1=**挂载 Recipe 为 SSOT** + UI 派生 |
| 六项并列改善 | 一项根合同 + 五项执行器 |
| 成功故事「更短」 | 成功故事「**默认集合可陈述、可测、可预算**」 |

---

## 9. 决议

| ID | 决议 |
|----|------|
| **RES-CSC-ROOT-01** | 采纳 **Happy Path Recipe Registry** 为 CSC 根治架构 |
| **RES-CSC-ROOT-02** | `StudioProfile.studio_default` 保留为 Recipe.orchestration 载体，不平行造类 |
| **RES-CSC-ROOT-03** | 未落地 Recipe 快照前，不宣布 CSC W1 Done |
| **RES-CSC-ROOT-04** | 备选（仅 facade/ceiling）不得称为根治完成 |
