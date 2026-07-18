# Travelogue · 统一模板合同与版式质量重设计 V1（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | **v0.2.2** |
| **状态** | **Conditional Go · Ready for Kickoff W1**（七席评审结案；**BLK-TPC-01～07 已回写本版**；LQS 瘦身版 S2+ 由本案承接） |
| **评审纪要** | [acceptance-records/template-contract-v1-review-2026-07-18.md](./acceptance-records/template-contract-v1-review-2026-07-18.md)（已结案 · Conditional Go · BLK-TPC-01～07 · 估时修正 17–22 人日） |
| **特性代号** | **TPC**（Template Contract · 统一模板合同） |
| **文档类型** | 版式质量重设计 PRD（问题驱动 · 收敛现网机制 · 非对标搬运） |
| **触发来源** | 开发负责人对 MSR/MGQ/GCS/LQS 的代码级审视（2026-07-18）：三份对标 PRD 拼合后产生四套准入机制与大量防御性合同；重新以「目标不变、机制收敛」出发设计 |
| **目标不变** | 与 LQS 相同：杂志观感提升（进对页 + 同窗更稳 + 库天花板）+ 单屏海报交付 |
| **被继承文档** | [MSR](./PRD-MCS-SIGNATURE-ROUTING-V1.md) · [MGQ](./PRD-MCS-GEOMETRIC-QUALITY-V1.md) · [GCS](./PRD-GENERATIVE-COLLAGE-SURFACES-V1.md) · [LQS](./PRD-LAYOUT-QUALITY-STACK-V1.md)（禁区/术语/诚实叙事**全部继承**；机制方案**部分替代**，见 §1.3） |
| **战略上位** | [观感提升路线图.md](./观感提升路线图.md)（P2 模板+硬约束 = 主战场；P4 solver 冻结） · [P17-LSE-处置建议.md](./P17-LSE-处置建议.md) |
| **现网审计** | [acceptance-records/p17-w0-audit-a-active-scoring-chain.md](./acceptance-records/p17-w0-audit-a-active-scoring-chain.md) |
| **相邻业主** | [URO](./PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md) · [LTE P16](./PRD-PHASE16-layout-template-engine.md) · [LTE Admission](./LTE-ADMISSION-LAYOUT-TEMPLATES.md) · [Output Recipe](./PRD-OUTPUT-RECIPE-V1.md) |
| **实施估量** | 约 **17–22 开发人日 / 4–5 周**（1 开发；含海报旁路；评审修正 · BLK-TPC-02） |
| **更新日期** | 2026-07-18 |

> **v0.2.0 评审回写摘要（七席 Conditional Go）**
>
> - BLK-01：mix_fallback 可行性 = **逐字母判定** + square 归置规则冻结（§3.2）  
> - BLK-02：mainSlotPolicy 迁移修正为 **8 调用点清单 + 两步走**（W2 桥接 · W3 末删除）；估时 15–19 → **17–22**（§4.2 / §7）  
> - BLK-03：captionAreas 属**新渲染能力**，图文 SKU 以 **W2 渲染 spike** 为前置条件；不支持则挪出 V1（§5.1）  
> - BLK-04：shadow diff 升格 **AC-TPC-12**（W1→W2 硬门）  
> - BLK-05：**双轨已收口**——LQS 瘦身版 S2+ 由本 PRD W2 承接（§10）  
> - BLK-06：caption tie-break 可观测定义（同分带 ε + 日志）（§3.4）  
> - BLK-07：配置 fail-loud + 配置根唯一 CI（**AC-TPC-13**）

> **定位**
>
> MSR/MGQ/GCS 各自映射一个外部作品（Shutterfly 专利 · gridwiggle · BRIC），拼合后需要 LQS 纲领事后缝合，且与现网 `mainSlotPolicy` / `usage_rules` 叠成 **四套「模板能否进窗」机制**。  
> 本 PRD 以相同目标重新设计：**一份模板合同（TemplateContract）+ 一个求值器 + 一份债务报表**；匹配只用 **bag-of-mix**（放弃有序签名）；几何质量用**硬面积带**表达（V1 不加 soft 罚项）；扩库回归**设计师手写**；海报旁路原样保留 GCS 轨 B。
>
> **一句话目标**：把「这个模板能不能进这个窗」收敛为模板 YAML 里的一份合同、代码里的一个求值器；省下的人日花在真正决定观感的地方——几个设计师级的好模板。
>
> **设计三原则**
>
> 1. **问题驱动**：每个机制必须对应 debt 报表中可测的现网问题，不因外部系统有而做。  
> 2. **机制收敛**：新能力只能扩展 TemplateContract 字段，禁止新增第五套准入机制。  
> 3. **品味优先**：版式观感的天花板是模板本身；机制为模板服务，不反客为主。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0.1 | 拟冻结决策（D-TPC-*） |
| §1 | 与三 PRD 的差异、继承与替代清单 |
| §2 | 目标 / 非目标 |
| §3 | TemplateContract 合同规范 |
| §4 | 求值器与匹配架构 |
| §5 | 模板创作（主战场）与海报旁路 |
| §6 | 测量与标定（debt 报表 + compare CLI） |
| §7 | 里程碑与迁移 |
| §8 | 验收 AC |
| §9 | 风险 |
| §10 | 生效状态与双轨收口 |
| §11 | 工程保障与测试迁移策略（不破坏现网 · 无缝集成 · 测试处置） |
| 附录 | 与 MSR/MGQ/GCS 条款映射 · 版本记录 |

### 0.1 设计决策（D-TPC · **已冻结** · 评审拍板见纪要 §7）

| # | 决策项 | 冻结结论 |
|---|--------|----------|
| **D-TPC-01** | 合同载体 | **采纳** — 模板 YAML 唯一合同：`mix` + `slots[].role` + `constraints.eligibility` + `captionAreas` + `usage`；**SSOT = LTE 模板文件** |
| **D-TPC-02** | 匹配键 | **有条件采纳** — **仅 bag-of-mix**（`{L,P,S}` 计数；panorama→L、tall→P、square→S）；**不做有序签名 / L1-L2-L3 分级**；fallback 可行性与 square 归置按 §3.2 冻结字面（BLK-TPC-01） |
| **D-TPC-03** | 求值器 | **采纳** — 唯一硬层求值器挂 `generate_window_candidates` 入口：mix 倒排 → usage（URO）→ eligibility；单一 reject 命名空间 `contract:*`（URO 保留 `usage_rule:*` 前缀，联合展示） |
| **D-TPC-04** | mainSlotPolicy 收敛 | **修订采纳** — `main_eligibility.py` 实为 **8 调用点横切模块**（评审事实核查）；迁移**两步走**：W2 桥接 + 等价 fixture，**W3 末删除**；共享工具（`asset_native_ar` 等）先解耦至中立位置；**不双轨**长存（BLK-TPC-02） |
| **D-TPC-05** | 几何质量 | **采纳** — V1 **不新增 soft 罚项**；hero 过大/过小用 eligibility **硬面积带**（`heroAreaBand` + `photoCountScale`）表达；raw 特征照记，留复议口。算法席补充论据：固定 SKU 下 coverage/CV 为模板常量，声明进 YAML 更诚实 |
| **D-TPC-06** | 匹配实现 | **有条件采纳** — registry 加载时按 mix 建倒排索引（一次构建、稳定序）；`try_order_for_pattern` 的 if 链降级为「同候选内 asset↔slot 对齐」；**切换入口前须过 AC-TPC-12 shadow diff 硬门**（BLK-TPC-04） |
| **D-TPC-07** | 图文 | **修订采纳** — **前置条件**：`captionAreas` 为新渲染能力，须先过 **W2 渲染 spike**（`render/chapters.py` 可消费文案区且长图导出正确）；不支持则图文 SKU + tie-break **整体挪出 V1**（BLK-TPC-03）。进入 V1 时 tie-break 按 §3.4 可观测定义（BLK-TPC-06） |
| **D-TPC-08** | 扩库 | **采纳** — **设计师手写**，以 debt 报表空洞清单为靶；不建枚举工厂（重启条件：空洞 >10 且滚动补库） |
| **D-TPC-09** | 海报 | **采纳** — GCS 轨 B（`poster_bric`）**原样继承**：vendor MIT · contain · export job sidecar · 不进 `screens[]` |
| **D-TPC-10** | 发布 | **采纳** — `mosaic.template_contract.enabled=false` 可先 merge；off 时与 baseline 逐屏一致；默认开启依据 = debt 报表前后对比 + 狗粮敢发；**对外默认开启前必须补正式盲评**（此承诺在 README 状态行显式保留） |
| **D-TPC-11** | 铁律继承 | **采纳** — 禁 runtime 改 `slots[].rect` · 禁 BRIC 挂 `used_legacy` · LSE 冻结 · 确定性（同输入同输出）· 术语隔离（单屏海报 ≠ 九宫格 ≠ 用户 collage）——**全部继承自 MSR/MGQ/GCS，一字不改** |
| **D-TPC-12** | 守门 | **采纳** — fallback / self-heal / replan 不得产出被 `contract:*` / `usage_rule:*` 拒绝的 pattern（继承 MGQ BLK-10 修复，为 W1 前置） |

### 0.2 v0.1.0 → v0.2.0 变更摘要（评审合入）

| 来源 | 合入要点 | 落点 |
|------|----------|------|
| **BLK-TPC-01** | mix_fallback 逐字母可行性判定 + square 归置规则冻结；AC-TPC-03 删「或」逃生门 | §3.2 · §8 |
| **BLK-TPC-02** | 迁移改 8 调用点清单 + 两步走；W2 估时 5–7d；合计 17–22 人日 | §4.2 · §7 |
| **BLK-TPC-03** | captionAreas 渲染 spike 前置；图文项降级为条件项 | §5.1 · D-TPC-07 |
| **BLK-TPC-04** | shadow diff 升格 AC-TPC-12（W1→W2 硬门） | §8 |
| **BLK-TPC-05** | 双轨收口：LQS 瘦身版 S2+ 由本案 W2 承接 | §10 |
| **BLK-TPC-06** | caption tie-break 可观测定义（ε + 日志） | §3.4 |
| **BLK-TPC-07** | 配置 fail-loud + 配置根唯一 CI（AC-TPC-13） | §3.5 · §8 |
| **Should** | debt 报表 trip 集 = BQP 8 本 SSOT；raw 特征沿用 MGQ 命名；非对称 hero 绑 CSS token 检查；`contract_shadow` 对照日志保留一个 release | §5.1 · §6.1 |

---

## 1. 背景与差异

### 1.1 现有设计的结构性问题（重设计动机）

| 问题 | 表现 |
|------|------|
| **对标驱动** | 三份 PRD 各自照搬一个外部系统的概念体系（签名 taxonomy / eligibility DSL / 轨道枚举），需 LQS 纲领事后缝合 |
| **准入机制发散** | `mainSlotPolicy` + `usage_rules` + MGQ eligibility + MSR signature = 四套机制回答同一问题，各有 reason / 撤销序 / 开关 |
| **防御性合同过重** | L1≠填槽序、UNDO 边界、双轨分账等条款，源于「三系统怕互踩」；单一系统下大半不需要存在 |
| **模板创作缺席** | 围绕模板建了大量机制，唯独没给「做出好模板」排工时；而路线图明言「模板库 = 美学天花板」 |

### 1.2 关键技术判断（为何敢删）

| 判断 | 依据 |
|------|------|
| **有序签名无增量信息** | 填槽本就按 role 重排（`_order_by_roles` / ordering）；MSR 评审自认「混合页 bag 是实际主力」；有序 L1 是从专利继承的概念，删除后 BLK-03（L1≠填槽序）类合同整体消失 |
| **soft 罚项大概率无感** | 本项目已用 LSE 全开 dogfood 实测：软分微调 ≈ 0% 屏变、肉眼无差异。MGQ 三罚项本质仍是软分微调 |
| **硬面积带可替代软罚** | 「hero 过大/过小」由模板声明舒适带、超带不进候选——可解释、可测、零调权 |
| **枚举工厂投入产出倒挂** | 26 模板的库缺的是「个位数好版式」；手写 3–5 个 YAML 1–2 天，工厂 6–10 人日 |

### 1.3 与三 PRD 的继承 / 替代 / 放弃清单

| 来源条款 | 处置 | 说明 |
|----------|------|------|
| MSR 字母表（L/P/S · panorama→L · tall→P） | **继承** | 作为 mix 计数口径 |
| MSR bag 匹配 + 倒排索引 + registry load 构建 | **继承（简化）** | 成为唯一匹配层 |
| MSR 有序签名 L1 / L3 分级 / signature taxonomy | **放弃** | D-TPC-02；方向冲突由 mix 计数天然表达 |
| MSR caption prefer（同 level 可观测偏置合同） | **简化替代** | D-TPC-07 tie-break；先补 SKU |
| MSR page_group / caption replan / Studio 调屏 | **放弃（V1）** | 与 LQS 瘦身版一致 |
| MGQ `constraints.eligibility`（heroDominance / heroAreaBand / photoCountScale / canvasAr） | **继承为核心** | 成为 TemplateContract 主字段；含 BLK-11 默认语义（未声明 ≡ 不参与硬拒绝） |
| MGQ 三 soft 罚项 + 阈值 + 评分台 | **放弃（V1）** | D-TPC-05；raw 特征仍落 log 供 G2 复议 |
| MGQ 面积口径（`col_frac × row_frac` · BLK-09） | **继承** | eligibility 面积带与 debt 报表同源 |
| MGQ BLK-10 绕过修复 + 守门 | **继承为前置** | D-TPC-12 |
| MGQ `hero_separation` 语义锁 | **继承** | W0 命名纪律 |
| GCS 轨 B `poster_bric` 全部合同 | **继承** | D-TPC-09；含 D-GCS-05/06/07 一字不改 |
| GCS 轨 A 枚举工厂 | **放弃（V1）** | D-TPC-08；重启条件登记 |
| LQS 硬过滤序纲领 | **简化替代** | 四层管道 → geometry → contract 求值器（内含 usage→eligibility）→ soft |
| 三主题独立 BLIND Gate | **降级** | D-TPC-10；对外默认开启前补正式盲评 |

---

## 2. 目标与非目标

### 2.1 目标（G-TPC-*）

| ID | 目标 | 验收口径 | 阶段 |
|----|------|----------|------|
| **G-TPC-01** | layout-debt 报表：legacy 率 / 错配窗 / mix 空洞 / caption 覆盖，从现有 log 提取 | CLI + 固定 trip 集报告 | W1 |
| **G-TPC-02** | registry 按 mix 建倒排；`try_order_for_pattern` if 链降级为槽内对齐 | 单测：新模板零 Python 改动即可被命中 | W1–W2 |
| **G-TPC-03** | TemplateContract 求值器上线；mainSlotPolicy **W2 桥接 → W3 末删除**（BLK-TPC-02） | AC-TPC-03/04 | W2–W3 |
| **G-TPC-04** | 手写 4–6 个新模板（混向空洞 ×2–3 · 非对称 hero ×1 · captionAreas ×2 **视 spike**） | validator + admission experimental + 狗粮 | W3 |
| **G-TPC-05** | `poster_bric` Writer 可导出（flag=false 狗粮） | 继承 AC-GCS-05/06/07/09 | W4 |
| **G-TPC-06** | compare CLI + 手记：on vs off 并排可判断 | 复用 `compare.html` 范式 | W4 |
| **G-TPC-07** | off 时与 baseline 逐屏一致；golden/LRG 全绿 | AC-TPC-01 | 全程 |

### 2.2 非目标

| # | 排除项 | 理由 |
|---|--------|------|
| OUT-01 | 有序格式签名 / L1-L2-L3 分级 | D-TPC-02 |
| OUT-02 | MGQ 三 soft 罚项 / 评分台 / 30–50 用例集 | D-TPC-05；raw 特征 log 留复议口 |
| OUT-03 | 轨道枚举 SKU 工厂 | D-TPC-08 |
| OUT-04 | page_group / caption replan / require 模式 | 需求驱动后另议 |
| OUT-05 | 解冻 LSE / Hungarian 上量 / runtime 改 rect / BRIC@legacy | 铁律继承 |
| OUT-06 | 另起第二套 usage 引擎 | URO 业主不变；求值器**调用**而非复制 |
| OUT-07 | 选片 subset / 章级弧线 | 观感 P1/P3 另轨 |
| OUT-08 | 正式三方盲评作为内部 dogfood 前置 | D-TPC-10；对外默认开启前必补 |

---

## 3. TemplateContract 合同规范

### 3.1 YAML 形态（单一 SSOT · 全部挂模板文件）

```yaml
# screen-mosaic-4-2p2l-editorial.yaml（示例）
mix: { landscape: 2, portrait: 2 }        # 匹配键（bag）；square 单列
slots:
  - { index: 0, role: portrait, rect: [...] }
  - { index: 1, role: landscape, rect: [...] }
  # ...
constraints:
  eligibility:                             # 硬准入（继承 MGQ 语义）
    heroDominance: moderate                # extreme | moderate；未声明=不限
    heroAreaBand: [0.30, 0.50]             # col_frac×row_frac 口径
    photoCountScale: { referenceCount: 20, maxHeroAreaAtRef: 0.40, floorFactorAt50: 0.55 }
    canvasAr: [0.5, 2.25]
  # mainSlotPolicy: ←—— 迁移期兼容读取；W2 末删除
captionAreas:                              # 图文能力（非空 ⇒ 带文案区）
  - { anchor: slot-3, position: below }
usage:                                     # URO 既有字段，不动
  signals: [...]
```

**行为冻结**：

- `mix` 与 `slots[].role` 计数必须一致，validator fail-loud。  
- 未声明 `eligibility` ≡ 不参与硬拒绝（继承 MGQ BLK-11）。  
- schema 变更 PR 同批全量 validate + registry cache 重建。  
- 面积口径全栈统一 `col_frac × row_frac`（继承 BLK-09）。

### 3.2 求值器（唯一硬层）

```text
generate_window_candidates(window)
  ① 窗口 mix 计数（aspectKind → L/P/S；taken_at 仅用于展示序）
  ② 倒排命中候选集
       exact：模板 mix 与窗口 mix 逐字母相等
       fallback：exact 为空时，同 N 且「可行」的模板，reason contract:mix_fallback
  ③ usage_rules 求值（URO 引擎调用，reason usage_rule:*）
  ④ eligibility 求值（reason contract:eligibility_*）
  ⑤ 返回 candidates + rejected(reason)
  → 既有 soft score（+ caption tie-break · §3.4）→ pick
  → self-heal / legacy 仍经 ①–④（D-TPC-12）
```

**fallback 可行性判定（BLK-TPC-01 · 冻结一字面）**：

> 模板可进入 fallback 候选，当且仅当对**每个字母** `x ∈ {L, P, S}`：`template_required(x) ≤ window_available(x) + window_flexible(x)`。其中 `template_required(x)` = 该模板 role 为 x 的槽数（`any`/`main` 槽按 `eligibleAspectKinds` 归置：单值计入该字母；多值计入 `window_flexible` 可吸收侧，不计入 required）；`window_available(x)` = 窗口中 aspectKind 映射为 x 的资产数。任一字母不满足 → 模板**不可行**，不得进入候选，reject 记 `contract:infeasible_mix`（等价于旧「方向冲突禁入」）。

**square 归置规则（BLK-TPC-01 · 冻结）**：

1. 窗口 S 资产在 **exact 匹配**时严格计 S。  
2. **fallback** 时若库内无 S 槽可用：S 资产可折算填 P 或 L 槽，优先序 **S→P**（竖向裁切损失通常小于横向），其次 S→L；折算发生时 decision_log 记 `squareRelaxed=true`。  
3. 模板侧 S 槽**不得**由 P/L 资产反向折算填充（防止方图槽被非方图硬撑）。

**reject reason 枚举（冻结）**：`contract:mix_miss` · `contract:mix_fallback` · `contract:infeasible_mix` · `contract:eligibility_hero_band` · `contract:eligibility_count_scale` · `contract:eligibility_canvas_ar` · `contract:invalid_template`（+ URO 既有 `usage_rule:*`）。

### 3.3 决策日志最低集

`windowMix` · `candidateSource（exact|fallback）` · `squareRelaxed` · `rejectReasons[]` · raw 几何特征（`heroProminenceRatio` / `heroCoverageRatio` / `cellAreaCv`，只记录，命名沿用 MGQ BLK-13）· `captionActive` / `captionTiebreakApplied`。

### 3.4 caption tie-break 可观测定义（BLK-TPC-06 · 仅当图文项进入 V1）

| 项 | 冻结 |
|----|------|
| 触发条件 | 窗口 caption-active（trim 后非空 `asset.caption`，口径继承 MSR OQ-03）**且**候选集内同时存在带/不带 `captionAreas` 的模板 |
| 行为 | 带文案区最佳候选分数 ≥（无文案区最佳候选分数 − **ε**）时，胜出者取带文案区候选；ε 默认 **0.02**（utility 归一口径；IMPLEMENTATION 可调但须单点定义） |
| 日志 | 生效时 `captionTiebreakApplied=true`；**禁止**无日志的隐形加分 |
| 边界 | 不改 reject 集合（纯 soft 决胜层）；无文案窗零影响 |

### 3.5 配置合同（BLK-TPC-07）

- 唯一配置根：`mosaic.template_contract`（`enabled` 默认 `false`；`shadow_log` 默认 `true`）。  
- 未知子键 **fail-loud**（禁止静默丢键）。  
- CI 断言：配置根唯一；默认 `layout.scoring.enabled is false`（AC-TPC-13）。

---

## 4. 架构增量与迁移

### 4.1 改动面

| 模块 | 改动 |
|------|------|
| `layout_templates/registry` | 加载时构建 mix 倒排（稳定序：pattern_id 字典序） |
| `mosaic/candidates.py` | 候选入口改走倒排 + 求值器 |
| `mosaic/builders.py` | `try_order_for_pattern` 保留为「同候选 asset↔slot 对齐」，删除选版职责分支 |
| `mosaic/main_eligibility.py` | AR 门禁语义迁入 eligibility；迁移完成后删除模块 |
| `mosaic/selfheal.py` / `replan.py` | BLK-10 修复（前置） |
| `layout_templates/validator.py` | mix↔role 一致性、eligibility schema、captionAreas 校验 |
| `export/output_recipe` | 扩 `EngineId` + `poster_bric` Writer（旁路） |
| `scripts/` | `layout_debt_report.py` + `layout_compare.py` |

### 4.2 mainSlotPolicy 迁移（BLK-TPC-02 · 两步走 · 不双轨长存）

**事实修正（评审核查）**：`main_eligibility.py` 是被 **8 个模块**导入的横切依赖，非「2–4 个模板」量级。迁移清单（冻结）：

| 调用点 | 用途 | 迁移处置 |
|--------|------|----------|
| `mosaic/candidates.py` | `screen_main_slot_eligible` 候选过滤 | 改调求值器 eligibility |
| `mosaic/scorer.py` | 同上（评分侧防御） | 改调求值器结果（勿重复求值） |
| `mosaic/metrics.py` | 诊断口径 | 改读求值器 log |
| `mosaic/hero.py` | hero 判定辅助 | 改调 eligibility helper |
| `mosaic/builders.py` | 构建期防御 | 改调求值器结果 |
| `planner/screen_planner.py` | 规划期预检 | 改调 eligibility helper |
| `usage_rules/evaluator.py` | **借用** `asset_native_ar` 工具 | **步骤 0**：工具函数先搬 `layout_contract/`（中立位置） |
| `usage_rules/context.py` | 同上 | 同上 |

**两步走**：

1. **W2 · 桥接**：步骤 0 解耦共享工具 → 求值器优先读 `constraints.eligibility`，模板未迁移时兼容折算 `mainSlotPolicy`（一次性桥接函数 + deprecation 日志）；hero 类模板同批迁移 YAML；**等价 fixture**（原 AR 门禁行为逐例对照）。  
2. **W3 末 · 删除**：确认等价 fixture 与狗粮无回归后，删除 `main_eligibility.py` 与桥接；CI grep 断言仓库无 `mainSlotPolicy` 残留（AC-TPC-04）。

**回归保护**：off 时逐屏一致 + golden/LRG + hero 等价 fixture（QA 估 1–1.5d 单列）。

---

## 5. 模板创作（主战场）与海报旁路

### 5.1 模板包（W3 · 设计师级手写）

| 模板 | 靶点 | 来源 | 条件 |
|------|------|------|------|
| 混向 SKU ×2–3 | debt 报表 mix 空洞 Top（预期 2L2P / 1L3P 族） | 报表驱动 | 无条件（W3 主体） |
| 非对称 hero ×1 | 「算法味 grid」突破（大图 ~70% + 竖条侧栏）；**绑 CSS token（gutter/bleed/max-fill-ratio）渲染检查** | 观感路线图 P2 §6.3.1 | 无条件（W3 主体） |
| captionAreas SKU ×2 | 图文窗「有字仍密铺」 | MSR P-03 | **已 defer（W2 spike 结案）**：见 [tpc-w2-caption-areas-spike-2026-07-18.md](./acceptance-records/tpc-w2-caption-areas-spike-2026-07-18.md)；连同 §3.4 tie-break / AC-TPC-14 **整体挪出 V1** |

要求：带齐 `mix` / `eligibility` / `usage`；经 validator + admission（experimental）；狗粮并排签核后升 beta。**禁止**无 eligibility/usage 的裸模板入库。

### 5.2 海报旁路（W4 · 继承 GCS 轨 B）

合同一字不改：vendor MIT BRIC（钉 commit）· `bric_compose(sizes, width=1080, border=16, spacing=8, round_result=True)` · 统一 contain · n∈[3,9]（1–2 张不调）· `mediaClass=collage` 排除 · export job sidecar · 独立 `intent/engine/platform` · `features.gcs_poster_bric=false` · ▾「单屏海报」次入口 · 禁「九宫格」串词。

---

## 6. 测量与标定

### 6.1 layout-debt 报表（W1 · 一切决策的地基）

| 指标 | 来源 |
|------|------|
| legacy 率（`planner_path=legacy` 按 trip / N 分布） | `MosaicWindowLog` |
| 方向错配（`aspectPatternMatchRate` 低分窗清单） | `layout_metrics` |
| mix 空洞（窗口 mix × 频次 vs 库内 mix 覆盖） | log + registry |
| caption 覆盖（caption-active 窗 vs 带文案区候选可用率） | log + registry |
| raw 几何特征分位（W2 起） | 求值器 log |

**用法**：W1 出 baseline；每次合码后重跑；on vs off 差异即「赚没赚到」的第一证据。

### 6.2 compare CLI（W4）

复用 `lse_flags_curate_compare.py` / `compare.html` 范式：同 trip 双配置并排 HTML + 手记 jsonl（自由标签，不建协议）。**不做** Studio 评分台。

---

## 7. 里程碑

| 波次 | 内容 | 估时（评审修正） | 出口 / Go | No-Go |
|------|------|------------------|-----------|-------|
| **W1** | BLK-10 修复；debt 报表 + baseline；mix 倒排 shadow + **逐窗 diff 报告（AC-TPC-12）** | 4–5d | 报表数字在手；off 逐屏一致；**diff 差异 = 0 或逐条签核** | 未修守门先上硬筛；diff 未签核即切入口 |
| **W2** | 共享工具解耦 + 求值器 + eligibility + mainSlotPolicy **桥接**（不删）+ hero 等价 fixture + **captionAreas 渲染 spike** | **5–7d** | AC-TPC-02/03/05；golden/LRG 绿；spike 结论（决定 W3 图文去留） | 另起第五套机制；桥接无 deprecation 日志 |
| **W3** | 手写模板包（混向 + 非对称 hero 为主；图文视 spike）→ experimental → 狗粮签核；**W3 末删除桥接**（AC-TPC-04） | 4–5d（含设计） | AC-TPC-04/06；debt 空洞 Top 覆盖 | 裸模板入库；删除前等价 fixture 未绿 |
| **W4** | `poster_bric` Writer + compare CLI + 狗粮周 | 4–5d | AC-TPC-07/08；海报可 flag 狗粮 | 海报写入 screens[]；文案串词 |
| **合计** | — | **17–22d**（BLK-TPC-02 修正） | debt 前后对比 + 狗粮结论 → 默认开决策 | 仅 proxy 微涨即全开 |

**与 LQS 瘦身版的关系（BLK-TPC-05 · 已收口）**：瘦身版 S1 与本案 W1 为同一批工作；**S2 起任务卡废止，由本案 W2 承接**；禁止两案并行开发。

---

## 8. 验收 AC

| ID | 条款 |
|----|------|
| **AC-TPC-01** | `template_contract.enabled=false` 时固定 fixture 与 baseline 逐屏一致（patternId + asset 序 + 固化几何） |
| **AC-TPC-02** | 新增模板仅改 YAML（mix/role/eligibility）即可被候选命中，零 Python 选版分支 |
| **AC-TPC-03** | 求值器 reject 含冻结枚举 reason；**混向窗（2L2P）候选集不得含按 §3.2 判定不可行的模板**；fallback 候选必须携带显式 `contract:mix_fallback`（BLK-TPC-01 · 无「或」逃生门） |
| **AC-TPC-04** | 迁移两步验收：① W2 桥接期——原 AR 门禁行为等价（hero 等价 fixture 逐例对照）+ deprecation 日志可见；② W3 末——`main_eligibility.py` 与桥接删除，CI grep 断言仓库无 `mainSlotPolicy` 残留（BLK-TPC-02） |
| **AC-TPC-05** | self-heal / replan / legacy 各 ≥1 负例：不得 emit 已被 `contract:*` / `usage_rule:*` 拒绝的 pattern |
| **AC-TPC-06** | 手写模板 ≥4 个经 validator+admission；带齐 mix/eligibility/usage；狗粮签核记录在案 |
| **AC-TPC-07** | 海报：3–6 张无重叠、保 AR、gutter 一致；导出后 `screens[]` diff 为空；GPL 扫描通过（继承 AC-GCS-05/06/09） |
| **AC-TPC-08** | debt 报表可对同一 trip 集重跑且口径稳定；on vs off 报告可生成 |
| **AC-TPC-09** | 默认 `layout.scoring.enabled is false`；TPC 字段仅出现于 `MosaicConfig` / 模板 YAML 路径 |
| **AC-TPC-10** | raw 几何特征（`heroProminenceRatio` / `heroCoverageRatio` / `cellAreaCv`）落 log 且与任何惩罚解耦（只记录） |
| **AC-TPC-11** | curate P95 增幅 ≤ +10%（相对 off；固定数据集与脚本口径写入 ACCEPTANCE，或挪 W4 末执行） |
| **AC-TPC-12** | **shadow diff 硬门（BLK-TPC-04）**：W1 末在代表 corpus（BQP 8 本）上输出「倒排候选集 vs 现网 `try_order` 候选集」逐窗 diff 报告；差异 = 0 或逐条人工签核；报告文件进仓库；未过此门不得切换候选入口 |
| **AC-TPC-13** | **配置合同（BLK-TPC-07）**：`mosaic.template_contract` 未知子键 fail-loud（负例单测）；CI 断言配置根唯一且默认 `layout.scoring.enabled is false` |
| **AC-TPC-14** | **caption tie-break（条件项 · BLK-TPC-06）**：若图文进 V1——fixture 断言同分带内带文案区候选胜出且 `captionTiebreakApplied=true`；无文案窗行为与 off 完全一致 |

---

## 9. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| mainSlotPolicy 迁移引入行为差 | hero 页回归 | fixture 对照等价 + off 逐屏一致 + golden/LRG 硬门 |
| 倒排替换 if 链后隐式规则丢失 | 个别窗选版变化 | W1 shadow 对比：倒排候选集 vs 现网候选集 diff 报告，逐条确认 |
| 放弃有序签名后未来需要时序排布 | 需重新引入 | 届时按需求驱动加 `orderedMix` 扩展字段，不推翻合同 |
| 硬面积带过严 → 候选枯竭 | legacy 上升 | 未声明=不限（默认宽松）；debt 报表监控；带宽先松后紧 |
| 手写模板品味不稳 | 观感不升反降 | admission experimental + 狗粮并排签核；不达标不升 beta |
| 与 MSR/MGQ 已冻结合同的对外一致性 | 文档口径混乱 | §1.3 处置清单为准；被替代条款在子 PRD 状态行标注（§10 已收口） |
| captionAreas spike 不通过 → 图文延期 | 产品差异点推迟 | BLK-TPC-03 预案：图文项整体挪出 V1 另立小 PRD；W3 以混向 + 非对称 hero 保底 |

---

## 10. 生效状态（BLK-TPC-05 · 已收口）

1. **D-TPC-01～12 已冻结**（[评审纪要](./acceptance-records/template-contract-v1-review-2026-07-18.md) §7：8 项采纳、2 项修订采纳、2 项有条件采纳）。  
2. **双轨收口已执行**：[LQS 瘦身版实施清单](./IMPLEMENTATION-LAYOUT-QUALITY-STACK-V1.md) 的 **S1 与本案 W1 为同一批工作；S2 起任务卡废止，由本案 W2 承接**；禁止两案并行开发。  
3. 子 PRD 状态标注：MSR/MGQ 机制方案由 TPC 替代（**冻结禁区与术语纪律继续有效**）；GCS 轨 B 由 TPC 继承执行、轨 A 挂起；LQS 纲领由 TPC 承接。  
4. **对外默认开启前必须补正式盲评**（D-TPC-10 承诺，README 状态行显式保留）。

---

## 11. 工程保障与测试迁移策略

> 回答三个落地问题：如何保障不破坏现有功能；如何无缝融入现有代码；升级后现有测试报错如何处置。  
> 资产盘点（2026-07-18）：全仓 **584 个测试文件**，其中版式 / mosaic / 模板相关约 **100 个**（含 golden、slot order、fallback/self-heal、usage_rules、`test_mosaic_main_eligibility.py` 等）。

### 11.1 五层防护体系 + 一键回滚

```text
第 0 层  Flag off = 逐字节一致（AC-TPC-01）—— 每个 PR 可安全合入的根基
第 1 层  Shadow + 逐窗 diff 报告（AC-TPC-12）—— 未签核不切候选入口
第 2 层  现有 ~100 个版式测试 + golden/LRG 作硬门 —— CI 全量跑
第 3 层  桥接迁移 + hero 等价 fixture（AC-TPC-04）—— main_eligibility 两步走
第 4 层  debt 报表前后对比 + compare 并排狗粮 —— 感知层面兜底
回滚     单开关 mosaic.template_contract.enabled=false，无数据迁移、无 schema 破坏
```

要点：

- **第 0 层含守门修复**：BLK-10 修复（D-TPC-12）在默认配置（`usage_rules.enabled=false`、contract off）下硬规则为空集，把 self-heal 接回硬过滤管道属行为无差改动，不破 off 一致性。  
- **第 1 层针对唯一真危险改动**：倒排索引替换 `try_order_for_pattern` 选版职责可能丢失 if 链中的隐式规则；W1 shadow diff 在 BQP 8 本上逐窗对账，差异 = 0 或逐条人工签核，**没过门旧路径继续跑、新路径只写日志**。  
- **第 4 层承认测试的局限**：测试只证「行为符合断言」，debt 报表 + `compare.html` 并排证「成书没变丑」。

### 11.2 无缝集成原则：加法集成，不做外科手术

**新代码进新模块，老代码只加挂钩，不改签名。**

| 集成点 | 做法 |
|--------|------|
| 求值器 | 新建独立模块（`layout_contract/` 或 `mosaic/contract.py`），不散落 |
| 候选入口 | `generate_window_candidates_with_rejections` 内部加分支：`enabled=true` 走倒排+求值器，否则**原路径一行不动**；函数签名与返回类型不变，调用方无感知 |
| `try_order_for_pattern` | **不删不重写**：其「asset↔slot 对齐」职责保留并被新路径复用；「哪些 pattern 进候选」职责被上游接管后，if 链先成死分支，W3 才清理 |
| `main_eligibility.py` | 8 个调用点 W2 一个不动（仅求值器内加桥接读其语义）；W3 等价 fixture 绿后逐点切换、最后删模块（§4.2） |
| 配置 | 纯加法：新根 `mosaic.template_contract`，不碰既有键（§3.5） |
| 提交节奏 | 每个 PR 独立可合、off 态回归全绿；**禁止「一个大 PR 切换一切」** |

代价与死期：W2–W3 期间新旧两路径并存，由 flag 隔离、shadow diff 对账；**W3 末删除旧路径与桥接**，不是永久双轨。

### 11.3 测试迁移策略：先定性，再分类处置

**首要纪律（团队共识）**：在加法集成 + 默认 off 的前提下，老测试没有理由挂。**现有测试报错默认定性为实现 bug（违反 AC-TPC-01），而不是测试过时。** 严禁为了 CI 变绿而批量改断言——那会把真回归改没。

在此前提下测试影响可精确预判，分四类处置：

| 类别 | 定义 | 涉及测试（举例） | 处置 |
|------|------|------------------|------|
| **A · 必须保持绿** | 与被改路径无关或仅走 off 路径（约 95%） | 全部 golden、`test_mosaic_compose_deterministic.py`、`test_mosaic_fallback.py`、`test_usage_rules_*` | **一行不改**；挂了 = 修实现 |
| **B · 测试对象被删** | 断言目标模块在 W3 删除 | `test_mosaic_main_eligibility.py` | 删模块**同批迁移**：断言对象改为求值器 eligibility 等价断言；等价 fixture 本就是 AC-TPC-04 交付物，测试是**搬家不是重写** |
| **C · 断言挂在将变化的行为上** | 候选入口切换 / 硬规则开启后行为有意变化 | `test_mosaic_2p3l_slot_order.py`、`test_mosaic_hero_order.py`、`test_mosaic_self_heal.py`（开硬规则后） | 每处变化必须先出现在 **shadow diff 签核记录**中；测试更新与行为变化**同 commit** 并说明因果；无 diff 记录背书的测试改动一律打回 |
| **D · 新行为** | 求值器可行性判定、square 折算、fail-loud、tie-break | 新增测试文件 | 只增不改旧文件 |

**配套流程动作**：

1. **绿色基线存档（W1 第一件事）**：全量跑 584 个测试，把绿色基线（含已知 skip/xfail 清单）存档进仓库；此后任何「测试挂了」都能回答「本来就挂 vs 我挂的」。  
2. **PR 验收加一条仪表盘指标**：被修改的测试文件数 ≈ 0（A 类阶段）或 = shadow diff 签核条目数（C 类阶段）；测试改动量本身就是回归风险仪表盘。

---

## 附录 A · 与三 PRD 关键条款速查

| 原条款 | TPC 落点 |
|--------|----------|
| MSR BLK-03（L1≠填槽序） | 概念消失（无有序签名） |
| MSR BLK-04（L3 方向冲突） | §3.2 可行性判定天然表达（`contract:infeasible_mix`） |
| MSR BLK-05（字母表） | §3.2 ①（口径继承） |
| MSR BLK-06（captionAreas SSOT） | §3.1（继承） |
| MGQ BLK-04（soft 阈值） | 挂起；raw 特征留复议 |
| MGQ BLK-09（面积口径） | §3.1（继承） |
| MGQ BLK-10（守门） | D-TPC-12 / W1 前置 |
| MGQ BLK-11/12（eligibility 语义/接线） | §3.1–3.2（继承，接线简化） |
| GCS BLK-01～08 | 轨 B 全继承；轨 A 挂起（重启条件 §D-TPC-08） |

## 附录 B · 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.1.0** | 2026-07-18 | 初稿：统一模板合同重设计；bag-only 匹配；硬面积带替代 soft；手写模板主战场；海报继承；待评审拍板 D-TPC-01～12 |
| **v0.2.0** | 2026-07-18 | 七席评审回写：BLK-TPC-01～07 合入（fallback 可行性/square 归置冻结 · 迁移两步走 8 调用点 · captionAreas spike 前置 · shadow diff 升 AC-TPC-12 · 双轨收口 · tie-break 定义 · 配置 fail-loud）；估时修正 17–22 人日；D-TPC 全部冻结 |
| **v0.2.1** | 2026-07-18 | 新增 §11 工程保障与测试迁移策略：五层防护 + 一键回滚；加法集成原则（挂钩不改签名 · 双轨有死期）；测试四类处置（A 必绿 / B 搬家 / C 同 commit 签核 / D 只增）；W1 绿色基线存档与 PR 测试改动量仪表盘入流程 |
| **v0.2.2** | 2026-07-18 | W2 spike 结案：captionAreas **defer**（验收记录 `tpc-w2-caption-areas-spike-2026-07-18.md`）；图文 SKU + tie-break 挪出 V1；hero 等价 fixture / 共享工具解耦落地 |
