# Travelogue · 双竖拼图变体家族试点 V1（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.2.0** |
| **状态** | **Conditional Go · Decision Freeze** · **可 Kickoff M0 / PR-A**（YAML+CSS+探针）；PR-B 合码前关闭实现向 BLK |
| **DOC-STATUS** | **active** |
| **主题代号** | 「双竖变体家族」— **P2VF**（Portrait-2 Variant Family） |
| **触发来源** | 产品草图（4 张 2P 留白/不对称构图）+ 游记版式去重意图（2026-07-27） |
| **试点范围** | **仅 2 张竖版（mix = 2P）**；3–9 张扩展本 PRD **明确不做** |
| **关联文档** | [P16 LTE](./PRD-PHASE16-layout-template-engine.md) · [LTE Admission](./LTE-ADMISSION-LAYOUT-TEMPLATES.md) · [MTSO](./PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) · [TPC](./PRD-TEMPLATE-CONTRACT-V1.md) · [URO](./PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md) · [portrait-row-editorial](./PRD-portrait-row-editorial.md) · [观感提升路线图](./观感提升路线图.md) |
| **评审纪要** | [acceptance-records/p2vf-portrait-2-variant-family-v1-review-2026-07-27.md](./acceptance-records/p2vf-portrait-2-variant-family-v1-review-2026-07-27.md)（六席 Conditional Go · 已结案） |
| **基线模板** | `screen-portrait-2`（满幅双竖 · **保留不动几何**） |
| **草图资产** | 产品提供 4 张示意（黑框=一屏 · 红框=槽位） |
| **更新日期** | 2026-07-27 |

> **v0.2.0 相对 v0.1.0（六席回写 · 产品确认 · 2026-07-27）**
>
> 1. **轮换集收窄**：V1 picker 仅 `fill + gallery + asymmetric-*`；**`offset-right` 砍出轮换**（附录几何可留，不进 allowlist）。  
> 2. **asym 强弱选型**：不跨槽换图；按相对强弱选 `asymmetric-left` / `asymmetric-right`；难分 → gallery/fill。  
> 3. **人物门收紧**：任一方有人 → **仅 fill**（不再限「双人都有人」）。  
> 4. **节奏内核合同**：R-06/R-08/late-reset **家族化且常驻**；点名须改的符号（F-09～F-13）。  
> 5. **experiments 配置**：`cohort_trip_ids` + 双开关；MCS lifecycle **不**自动挡 2P。  
> 6. **diversity**：V1 **只做 picker 软分**；不在 beam 再加家族多样性层。  
> 7. **盲评**：固定三问 + 「坏版/缺图」系统性出现 → No-Go。  
> 8. **gallery 面积**：目标两槽合计约 **55–65%**（防 50% 过空）。

> **定位**
>
> 现网双竖只有一种「尽力占满 16:9」的语法（`screen-portrait-2`）。竖图配对一多，游记翻页易「齐整但重复」。  
> 本 PRD **不扩到其他张数**，在 **2P 家族**内新增杂志感变体，并接上 **家族内软轮换**。  
> V1 狗粮轮换验证的是 **3 个角色**：满幅 / 画廊呼吸 / 有主次的一对——**不是**四草图齐飞。
>
> **一句话目标**：**双竖不再只有满幅一种说法；同册轮换可变生动，且不破坏现有满幅路径与硬质量门。**

> **完成定义**
>
> | 门 | 含义 | 不等于 |
> |----|------|--------|
> | **M0 Go** | 规格冻结 + 轮换集几何可 validate + CSS 探针可读 | 进默认 curate |
> | **M1 Go** | gallery+asym YAML/CSS + `template_experiments` 可狗粮；picker 可开关 | 改默认活跃集 |
> | **M2 Go** | 家族软轮换生效；代表 trip 盲评通过或归档 | 自动推广到 3–9 张 |
> | **M3 Go** | （可选）1～2 个变体转 beta/ga；offset 增量或扩张数另开 | 本文件直接改 3–9 |

---

## 0. 读者指南与边界

### 0.1 与相邻主题

| 主题 | 关系 | 本主题做什么 |
|------|------|--------------|
| [P16 LTE](./PRD-PHASE16-layout-template-engine.md) | **载体** | 新 YAML + CSS export + admission |
| [MTSO](./PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) | **正交** | 复用 `template_experiments` 三元组；**不**占用 LTN 2P3L 空位 |
| [TPC](./PRD-TEMPLATE-CONTRACT-V1.md) | **合同** | mix=2P；禁 runtime 改 rect；TPC ON **不**整批解锁实验 |
| [portrait-row-editorial](./PRD-portrait-row-editorial.md) | **同族手法** | 借鉴留白/inset；本主题是 **16:9 舞台内 2 槽**，不是 3 竖 intrinsic 行 |
| MCS mosaic 3/4/5/6 | **多数不经过** | `screen-portrait-2` 主路径是 **screen_planner 硬 emit**，不是 MCS 窗宽竞选（见 F-01） |
| 3–9 张模板扩库 | **后续** | 本试点验证「家族 + 软轮换」合同后，另开 PRD 复制模式 |

### 0.2 代码事实（2026-07-27 · 不可重议）

| ID | 事实 |
|----|------|
| **F-01** | `screen-portrait-2` 由 `screen_planner_stages` / `_emit_person_portrait_screens` / late pairing **硬编码 emit**，不是 MCS `MOSAIC_*_PATTERN_IDS` 成员 |
| **F-02** | `layout_contract.rhythm.PORTRAIT_PAIR_PATTERN = "screen-portrait-2"`；`PORTRAIT_PAIR_PATTERNS` 目前只有这一员 |
| **F-03** | R-06：`screen-portrait-2` 连续 streak 上限默认 2（`MAX_PORTRAIT_PAIR_STREAK`） |
| **F-04** | 近屏 diversity：`score_screen` 对 `prior_pattern_ids[-2:]` 同 `patternId` → diversity=0；`score_layout_rhythm` 同 pid→0（**硬 emit 主路径不靠它选型**） |
| **F-05** | MCS MMR/DPP 作用在 mosaic 候选，**不覆盖** planner 硬 emit 的双竖 |
| **F-06** | LTE 允许 `intentionalGaps`；未声明的空格会 V-P16-02 失败 |
| **F-07** | 实验曝光须 `mosaic.template_experiments`：`enabled` + `allowlist` + **`cohort_trip_ids`**（tripId 列表；空 = 无人可见 · MTSO SUP-08） |
| **F-08** | 现网活跃集刻意很薄；本试点 **默认不进** `lte_policy` GA 白名单 |
| **F-09** | `LayoutState.current_portrait_pair_streak()` **只**比较 `last_pattern_id == PORTRAIT_PAIR_PATTERN`（单 id）；仅扩 frozenset **不够**，换变体 id 会绕开 R-06 |
| **F-10** | `PORTRAIT_ORIENTATION_PATTERNS` 目前不含新变体 id；未注册则 emit 可能清零 R-08 朝向 streak |
| **F-11** | late pairing 的 pair-streak reset 同样只认 fill 单 id |
| **F-12** | mobile 现网 **不拆** `screen-portrait-2`（仅 triple / 4mix 等有 expand）；D-08 是**新工程** |
| **F-13** | `_fits_for_pattern` 仅对精确 id `screen-portrait-2` 走 `portrait_fit_for_asset`；新 id 默认全 cover → 脸裁风险（故人脸门走 fill） |

### 0.3 用户可感知问题 → 落点

| ID | 问题 | 严重度 | 落点 |
|----|------|--------|------|
| **Q1** | 双竖只有满幅，缺少杂志留白/主次 | **P0** | §4 gallery + asym |
| **Q2** | 同册连续多种双竖仍「长得一样」 | **P0** | §5 家族软轮换 |
| **Q3** | 怕大改模板库伤稳定算法 | **P0** | 基线几何冻结 + 实验开关 + 软分非硬禁 |
| **Q4** | 怕 3–9 全面铺开调试爆炸 | **P1** | 范围锁死 2P；扩展另案 |
| **Q5** | 留白被读成缺图；主次反 | **P0** | 面积目标 + 强弱选型 + 盲评否决门 |

---

## 1. 背景与北极星

### 1.1 现状

```text
竖图 run / late pairing
  → 硬 emit screen-portrait-2（2 列等分 · cover · 占满 16:9）
  → 连续同 pid 有 R-06 / diversity 惩罚
  → 但候选集里没有「另一种双竖」可换 → 惩罚无法换出生动
```

### 1.2 设计北极星

> **2P Family = 一种需求、多种构图语法。**  
> 满幅负责信息密度与稳妥配对；gallery 负责呼吸；asymmetric 负责主次。  
> **轮换的是变体角色，不是「随便换个也叫两张图的模板」。**  
> **不对称的价值在「对的图做主」，不在「多一个左主/右主模板名」。**

### 1.3 草图 → 变体角色（冻结）

| 草图 | 视觉特征 | `variantRole` | V1 轮换集 | 一句话 |
|------|----------|---------------|-----------|--------|
| （基线）满幅双竖 | 两列等分贴边占满 | `fill` | **是** | 现网默认，稳妥配对 |
| ① 双竖等大居中 | 两槽等大，四周与中缝留白 | `gallery` | **是** | 画廊对页，对称呼吸 |
| ② 左小右大 | 右槽更高/更重 | `asymmetric-right` | **是**（强弱选型） | 右主左辅 |
| ③ 左大右小 | 左槽更高/更重 | `asymmetric-left` | **是**（强弱选型） | 左主右辅 |
| ④ 双竖等大偏右 | 两槽等大，整组贴右 | `offset-right` | **否 · 延后** | 附录几何；不进 V1 picker |

> **产品确认（2026-07-27）**：接受「砍 offset 出 V1 轮换」+「asym 强弱选型」。

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 | 衡量 |
|----|------|------|
| **G-01** | 轮换集变体（gallery + asym-L/R）几何可 validate、可渲染、可探针 | AC-P2VF-01～04 |
| **G-02** | 基线 `screen-portrait-2` 几何与默认 emit：**variants OFF 时 emit 序列与基线一致**；家族 streak 内核常驻不改变 fill-only 路径的可见 patternId | AC-P2VF-05 |
| **G-03** | 狗粮双开关 ON 时，picker 在合格候选中按家族软轮换 + 强弱选 asym | AC-P2VF-06～08 |
| **G-04** | 轮换不得压过朝向/人物/硬质量；无合格替代时回退 fill | AC-P2VF-09 |
| **G-05** | 决策可解释（日志含 family / variantRole / pickerReason / strengthSide） | AC-P2VF-10 |
| **G-06** | 盲评三问可驱动「转正 / 砍变体 / 扩到其他张数」 | AC-P2VF-11 |

### 2.2 非目标（V1）

| ID | 不做 |
|----|------|
| **N-01** | 不改 3/4/5/6/7/8/9 张模板库 |
| **N-02** | 不改 MCS 窗序、P21 dense、六图机会（MTSO） |
| **N-03** | 不启 LSE；不加新的第五套准入机制（遵守 TPC） |
| **N-04** | 不做 runtime 改 `slots[].rect`；不做跨槽换图 |
| **N-05** | 不做「用过一次永不再用」的硬禁 |
| **N-06** | 不把实验变体默认写入 `lte_policy` GA 活跃集 |
| **N-07** | 不在本主题做 captionAreas / 文案槽（纯照片 2P） |
| **N-08** | mobile 面不做 2 竖并排杂志变体；拆 2× 单竖后 **不评** 构图轮换 |
| **N-09** | V1 picker **不轮换** `offset-right` / `offset-left` |
| **N-10** | 不在 beam / `score_screen` 再叠一层家族多样性软分（避免与 picker 双重惩罚） |

---

## 3. 已拍板决策（D-P2VF · **已冻结**）

| # | 议题 | 冻结结论 |
|---|------|----------|
| **D-01** | 主路径 | **方案 B**：新建变体 id；**不修改** `screen-portrait-2` 的 `slots[].rect` |
| **D-02** | 家族键 | `familyId: portrait-2`；成员含 fill + gallery + asym-L/R（+ 附录 offset，非轮换） |
| **D-03** | 默认开关 | `layout.portrait_2_variants.enabled=false`；实验可见须 **双开关**：本开关 ∧ `template_experiments`（enabled+allowlist+`cohort_trip_ids`） |
| **D-04** | 轮换强度 | **软分优先**；禁止无替代时硬失败 |
| **D-05** | 近窗定义 | **同章**已 emit 的最近 `recent_window`（默认 2）个 `portrait-2` 家族屏 |
| **D-06** | streak | R-06 **家族化且常驻**：`current_portrait_pair_streak` / late-reset / postcheck 对 `PORTRAIT_PAIR_PATTERNS` 任一成员累计；**即使 variants OFF**，手工注入变体 id 仍计 R-06 |
| **D-07** | 人物门 | **任一方** `asset_has_person` → **仅 emit fill**；`person-pair` overlay 仍只绑 fill |
| **D-08** | Mobile | Web/screens 渲染变体；mobile **拆成 2× `screen-portrait-1`**（左→右）；成功标准=可读，**不**评杂志轮换 |
| **D-09** | 舞台 | LTE `stage.aspect: "16:9"`；舞台内留白表达杂志感 |
| **D-10** | fit | 变体槽默认 `cover`；须把变体 id 纳入与 fill 同等的 portrait fit 白名单路径（防 F-13）；有人已由 D-07 挡到 fill |
| **D-11** | 扩展门 | 盲评三问通过后，才允许另开「3P/4mix 家族」或 offset 增量 PRD |
| **D-12** | V1 轮换集 | **`fill` + `gallery` + `asymmetric-left|right`**；**offset-right 延后** |
| **D-13** | asym 选型 | **不跨槽换图**；用相对强弱选 L/R 主模板；难分 → gallery 或 fill（§5.2） |
| **D-14** | diversity 权威 | V1 **仅 picker** 做家族轮换软分；保留现网同 pid diversity/rhythm 公式，**不新增** beam 家族层 |
| **D-15** | experiments 权威 | MCS `lifecycle_admit` **不**自动决定 2P 可见性；picker 内 `experimental_members_visible` 为唯一门 |

---

## 4. 家族模型与模板规格

### 4.1 家族登记（逻辑合同）

```yaml
familyId: portrait-2
mix: { portrait: 2, landscape: 0 }
rotationSet:   # V1 picker 候选（D-12）
  - id: screen-portrait-2
    variantRole: fill
    status: ga
  - id: screen-portrait-2-gallery
    variantRole: gallery
    status: experimental
  - id: screen-portrait-2-asymmetric-left
    variantRole: asymmetric-left
    status: experimental
  - id: screen-portrait-2-asymmetric-right
    variantRole: asymmetric-right
    status: experimental
deferred:      # 不进 V1 allowlist / picker
  - id: screen-portrait-2-offset-right
    variantRole: offset-right
    note: 附录 §12.4；M3+ 增量
```

**实现要求（节奏内核 · BLK-P2VF-01/02）：**

| 符号 / 位点 | 动作 |
|-------------|------|
| `PORTRAIT_PAIR_PATTERNS` | 加入轮换集全部 id（fill+gallery+asym×2）；offset 若落 YAML 亦加入集合（防泄漏绕 streak），但 **不**进 picker |
| `PORTRAIT_ORIENTATION_PATTERNS` | 同上加入新 id |
| `LayoutState.current_portrait_pair_streak` | 改为 `last ∈ PORTRAIT_PAIR_PATTERNS` 累计（禁止只比 fill 字符串） |
| late pairing pair-streak reset | 同上家族判定 |
| `layout_kind` | 家族成员 → `portrait_pair` |
| YAML `scoring.tags` | `portrait-2`、`variant-<role>` |

`familyId` SSOT：优先 `layout_contract` 常量；YAML tags 镜像，禁止第三处硬编码列表。

### 4.2 公共字段（轮换集变体）

| 字段 | 值 |
|------|-----|
| `kind` | `primitive` |
| `photoCount` | `{ min: 2, max: 2 }` |
| `mix` | `{ portrait: 2, landscape: 0 }` |
| `stage.aspect` | `"16:9"` |
| `status`（试点） | `experimental` |
| `scoring.base_weight` | gallery/asym：`0.90`（fill=1.0） |
| `render.cssBundle` | `journal-screens.css` |
| `render.fitPolicy` | `auto_delegate` |

### 4.3 网格约定（gallery · 防过空）

稀疏轨道 + `intentionalGaps`。坐标：`rect: [c0, c1, r0, r1]`（1-based 闭区间）。

**gallery 建议 SSOT（v0.2 上修面积）：**

```text
cols 权重: [2, 5, 1, 5, 2]     → 边距 | 槽A | 缝 | 槽B | 边距
rows 权重: [1, 7, 1]           → 顶距 | 内容 | 底距   （相对 v0.1 的 [1,6,1] 增高内容带）
```

| 区域 | 近似面积（16:9） |
|------|------------------|
| 单侧等大槽 | 5/15 × 7/9 ≈ **25.9%** |
| 两槽合计 | ≈ **52%**（实现允许微调至 **55–65%** 合计，以探针「不像缺图」为准） |
| 留白 | 其余；须为屏级纸色/中性场 |

> M0 探针签字标准含：**留白=设计而非缺陷**。过空则继续收边距或加高内容行，并回写本节数字。

---

### 4.4 模板 A · `screen-portrait-2-gallery`（轮换 · 必留）

**角色：** `gallery` · 草图 ①  

```text
┌──────────────────────── 16:9 ────────────────────────┐
│                                                      │
│      ┌──────┐              ┌──────┐                 │
│      │  P0  │              │  P1  │                 │
│      │      │              │      │                 │
│      └──────┘              └──────┘                 │
│                                                      │
└──────────────────────────────────────────────────────┘
```

| 项 | 规格 |
|----|------|
| **stage** | `cols: [2, 5, 1, 5, 2]` · `rows: [1, 7, 1]` |
| **slot 0/1** | `rect: [2,2,2,2]` / `[4,4,2,2]` · `role: portrait` · `visualWeight: 1.0` |
| **intentionalGaps** | 全部非槽单元格 |
| **gridClass** | `layout-screen__grid--portrait-2-gallery` |
| **何时用** | 两图强弱接近；前屏 dense/满幅后需换气 |
| **何时不用** | 一张明显更强（asym）；任一方有人（fill）；需信息密度（fill） |

```yaml
usage:
  summary: 双竖画廊：两槽等大居中，四周留白，杂志对页感。
  whenToUse: |
    - 连续 2 张竖图权重接近
    - 前屏为满幅拼贴/多槽，需要换气
  whenNotToUse: |
    - 一张明显更强（应选 asymmetric-left/right）
    - 任一方含人物（应选 screen-portrait-2）
```

---

### 4.5 模板 B/C · asymmetric（轮换 · 强弱选型）

#### B · `screen-portrait-2-asymmetric-right`（草图 ② · 右主）

| 项 | 规格 |
|----|------|
| **stage** | `cols: [2, 4, 1, 6, 2]` · `rows: [1, 2, 4, 2, 1]` |
| **slot 0（辅·左）** | `rect: [2, 2, 3, 3]` · `visualWeight: 0.72` |
| **slot 1（主·右）** | `rect: [4, 4, 2, 4]` · `visualWeight: 1.0` |
| **gridClass** | `layout-screen__grid--portrait-2-asym-right` |

#### C · `screen-portrait-2-asymmetric-left`（草图 ③ · 左主）

| 项 | 规格 |
|----|------|
| **stage** | `cols: [2, 6, 1, 4, 2]` · `rows: [1, 2, 4, 2, 1]` |
| **slot 0（主·左）** | `rect: [2, 2, 2, 4]` · `visualWeight: 1.0` |
| **slot 1（辅·右）** | `rect: [4, 4, 3, 3]` · `visualWeight: 0.72` |
| **gridClass** | `layout-screen__grid--portrait-2-asym-left` |

**主槽绑定（D-13 · 冻结）：**

- asset **时间序不换槽**（N-04）。  
- picker 计算 `strengthSide ∈ {left, right, tie}`（§5.2.1）。  
- `left` → 只考虑 `asymmetric-left`；`right` → 只考虑 `asymmetric-right`；`tie` → **不进 asym**，改 gallery/fill。  
- **禁止**「为了轮换」在强弱明确时选反侧主模板。

**面积 AC：** 主槽面积 > 辅槽 × **1.15**。

---

### 4.6 基线 · `screen-portrait-2`

| 项 | 规格 |
|----|------|
| **variantRole** | `fill` |
| **几何** | 维持现网；**禁止**改 rect |
| **YAML 增量** | 仅 `scoring.tags` / `usage.siblings` |
| **何时用** | 默认；任一方有人；狗粮 OFF；变体不可见/不合格；强弱难分且需密度 |

### 4.7 延后 · `offset-right`

见 **附录 §12.4**。PR-A **可不落**该 YAML；若落盘则 `status: experimental` 且 **禁止**写入狗粮 allowlist。

---

## 5. 与现有 diversity / 节奏怎么接

### 5.1 分层：谁管什么

| 层 | 现网机制 | 本主题增量 |
|----|----------|------------|
| **A. 硬 emit 入口** | planner 写死 fill | → **`pick_portrait_2_variant(...)`**（OFF ≡ fill） |
| **B. 家族集合** | `PORTRAIT_PAIR_PATTERNS` 单员 | 扩轮换集（+可选 offset id 仅防 streak 泄漏） |
| **C. R-06 / R-08** | 只认 fill 单 id | **家族化且常驻**（D-06；改 F-09～F-11 位点） |
| **D. 近屏 diversity / rhythm** | 同 pid 惩罚 | **保持现网公式**；轮换差异来自不同 pid，**不再加** beam 家族软分（D-14 / N-10） |
| **E. MCS MMR/DPP** | mosaic 候选 | **不改** |
| **F. experiments** | MCS lifecycle | **不**自动挡 2P；picker 内可见性为准（D-15） |

### 5.2 Picker 伪代码（权威行为）

```text
pick_portrait_2_variant(assets=[a0,a1], ctx, cfg):
  if not cfg.layout.portrait_2_variants.enabled:
      return fill, reason=default_off

  # D-07 · 任一方有人
  if asset_has_person(a0) or asset_has_person(a1):
      return fill, reason=person_fill

  visible = experimental_members_visible(          # D-15
      cfg.mosaic.template_experiments,
      trip_id=ctx.trip_id,
      allowlist_intersect=ROTATION_EXPERIMENTAL_IDS,  # gallery, asym-L, asym-R
  )
  # 双开关：enabled 已通过；visible 空则仅 fill
  candidates = [fill] + visible
  candidates = filter_hard_gates(candidates)       # §5.2.2
  if candidates == [fill] or not candidates:
      return fill, reason=fallback_fill

  side = strength_side(a0, a1)                     # §5.2.1 · left|right|tie
  pool = []
  for pid in candidates:
      role = variant_role(pid)
      if role in (asymmetric-left, asymmetric-right):
          if side == tie: continue
          if side == left and role != asymmetric-left: continue
          if side == right and role != asymmetric-right: continue
      pool.append(pid)
  if not pool:
      pool = [fill] + [p for p in candidates if variant_role(p) == gallery]
  if not pool:
      return fill, reason=fallback_fill

  recent = last_k_family_pattern_ids(ctx, k=cfg.recent_window)  # 同章
  scored = []
  for pid in pool:
      s = base_weight(pid)
      if pid in recent:
          s *= cfg.repeat_penalty                  # 默认 0.55；单一软罚，无 role 二次乘
      if prefer_breath_after_dense and prev_screen_dense(ctx) and variant_role(pid) == gallery:
          s += 0.08
      scored.append((s, stable_order_key(pid), pid))
  best = max(scored)                               # 确定性
  return best.pid, reason=rotate|weight
```

**稳定序（同分）：** `fill` → `gallery` → `asymmetric-left` → `asymmetric-right`。

**日志字段：** `portrait2.familyId`、`portrait2.variantRole`、`portrait2.strengthSide`、`portrait2.pickerReason`  
（`default_off` / `person_fill` / `rotate` / `fallback_fill` / `weight`）。

#### 5.2.1 `strength_side`（D-13）

最小可测定义（实现可换等价特征，须单测钉死）：

```text
score(asset) = 0.50 * aesthetic01 + 0.30 * sharpness01 + 0.20 * (1 if featured/hero else 0)
delta = score(a0) - score(a1)
if abs(delta) < 0.08: return tie
return left if delta > 0 else right
```

- 特征缺失时退化为 `tie`（安全侧）。  
- **不**交换 slots；只选模板。

#### 5.2.2 `filter_hard_gates`（最小集）

| 门 | 行为 |
|----|------|
| `overrides.disable` / YAML disabled | 剔除 |
| 非 experiments 可见 | 剔除实验 id |
| 任一方有人 | 候选坍缩为 `[fill]`（上游已短路径，双保险） |
| photoCount/mix 不匹配 | 剔除（防御） |

### 5.3 配置合同

```yaml
layout:
  portrait_2_variants:
    enabled: false
    recent_window: 2
    repeat_penalty: 0.55          # 单一软罚；无 role_repeat_penalty
    prefer_breath_after_dense: true
    strength_tie_epsilon: 0.08

mosaic:
  template_experiments:
    enabled: true
    allowlist:
      - screen-portrait-2-gallery
      - screen-portrait-2-asymmetric-left
      - screen-portrait-2-asymmetric-right
      # 故意不含 offset-right
    cohort_trip_ids:
      - trips/your-dogfood-trip-id
```

**狗粮启动条件（双开关）：**

1. `layout.portrait_2_variants.enabled=true`  
2. `mosaic.template_experiments.enabled=true`  
3. allowlist 非空且含目标变体  
4. `cohort_trip_ids` 含本 tripId（空列表 = **无人可见**）

### 5.4 观察指标（非假绿主裁决）

狗粮 ON、且一册 **≥3 次非 person_fill 双竖** emit 时记账（**盲评为主**）：

| 指标 | 观察目标 |
|------|----------|
| `unique_roles / emit_count`（roles∈{fill,gallery,asymmetric}） | ≈ ≥0.5（观察） |
| 连续两次同 patternId 比例 | ≈ ≤0.35（观察） |
| fill 回退率（person / 不可见） | 只记账 |
| 盲评「坏版/缺图」「主次反」系统性出现 | **否决门**（AC-11） |

> 删除模糊词 `variant_entropy`；上表角色多样性即扩展门的量化参考。

---

## 6. 渲染与工程落点

### 6.1 文件清单（预计）

| 路径 | 动作 |
|------|------|
| `travelogue/layout_templates/templates/screen-portrait-2-gallery.yaml` | 新增 |
| `…/screen-portrait-2-asymmetric-left.yaml` | 新增 |
| `…/screen-portrait-2-asymmetric-right.yaml` | 新增 |
| `…/screen-portrait-2-offset-right.yaml` | **可选**附录；不进 allowlist |
| `…/screen-portrait-2.yaml` | 仅 tags/siblings |
| `templates/visual-journal/journal-screens.css` / `css_gen` | gallery + asym gridClass |
| `travelogue/layout_contract/rhythm.py` | `PORTRAIT_PAIR_PATTERNS` + `PORTRAIT_ORIENTATION_PATTERNS` |
| `travelogue/layout_contract/planner_state.py` | `current_portrait_pair_streak` 家族化；late-reset |
| `travelogue/layout_engine/planner/portrait_2_picker.py` | **新** · picker + strength_side + 日志 |
| `travelogue/layout_engine/planner/screen_planner.py` | emit / person-pair / fit 白名单接线 |
| `travelogue/layout_engine/planner/screen_planner_stages.py` | 硬编码 → picker |
| `travelogue/layout_engine/planner/screen_planner_attach.py` | late pairing → picker |
| `travelogue/curation/moment_scoring.py` | 若仍硬编码 fill，改为 picker 或共享 helper |
| `travelogue/render/mobile_screens.py`（或等价） | **新** · 家族 id 拆 2× portrait-1 |
| `travelogue/config/layout.py` | `Portrait2VariantsConfig` |
| `docs/config-p2vf-dogfood.example.yaml` | 狗粮样例（`cohort_trip_ids`） |
| `tests/unit/layout_engine/test_portrait_2_picker.py` | picker / strength / person / OFF |
| `tests/unit/layout_contract/…` | R-06 家族 streak 不因换 id 清零 |

### 6.2 CSS 要求

- 选择器只匹配对应 `data-pattern`，**不得**污染 fill。  
- 留白 = 屏级纸色/中性场（与 journal / editorial 同族），禁止灰洞、禁止模糊补边冒充第三张图。  
- 不强制改全局 `--screen-gap`。

### 6.3 Admission / 导出

1. `cli validate`（schema + intentionalGaps）  
2. LTE CSS export / sync-journal  
3. experimental→beta 前：探针 + 代表 trip  
4. **不**自动进 GA

### 6.4 回退

| 手段 | 效果 |
|------|------|
| `portrait_2_variants.enabled=false` | picker 恒 fill；**家族 streak 内核仍常驻** |
| 清空 `cohort_trip_ids` / 移出 allowlist | 实验不可见 |
| `overrides.disable` | 单 id 下线 |

---

## 7. 里程碑与估时（1 开发参考）

| 里程碑 | 内容 | 估时 | 退出 |
|--------|------|------|------|
| **M0** | Decision Freeze（本文 v0.2）；网格探针对照草图 ①～③ | 0.5d | 几何签字 |
| **M1a · PR-A** | gallery+asym YAML/CSS + validate + 探针 | 1.5–2d | AC-01～04 |
| **M1b · PR-B** | picker + 节奏内核家族化 + fit/mobile + OFF 等价 | **2–2.5d** | AC-05～10 |
| **M2 · PR-C** | 狗粮 + 盲评三问 | 1d + 评审 | AC-11 |
| **M3** | 可选升 beta；offset 增量另案 | 0.5d | 另开或归档 |

**合计试点：** 约 **5.5–7 人日**（相对 v0.1 上修 PR-B）。

### 7.1 PR 切片

| PR | 内容 | 风险 | 挡门 |
|----|------|------|------|
| **PR-A** | YAML+CSS+validate；**不接** picker | 低 | 无 |
| **PR-B** | picker + R-06/R-08/late-reset + fit 白名单 + mobile 拆屏 + 单测 | 中 | 本文合同已冻结；实现须关 BLK-01/02/06/07 |
| **PR-C** | 狗粮 example + 盲评记录 | 低 | AC-11 |

---

## 8. 验收（AC）

| ID | 断言 | 验证 |
|----|------|------|
| **AC-P2VF-01** | gallery+asym×2 YAML 通过 schema + V-P16-02 | `cli validate` |
| **AC-P2VF-02** | 对应 gridClass 存在且 CSS 无 stale | export + CI |
| **AC-P2VF-03** | 探针可区分 fill / gallery / asym-L / asym-R | 目视（同素材对拍） |
| **AC-P2VF-04** | gallery 两槽合计面积 ∈ **55%–65%**（或 M0 签字修订带）；asym 主槽 > 辅槽 ×1.15 | 算轨 / 探针 |
| **AC-P2VF-05** | `enabled=false` 时固定 fixture 的 **emit patternId 序列**与基线一致 | golden |
| **AC-P2VF-05b** | 手工注入变体 id 时 R-06 streak **不因换 id 清零**（家族常驻） | unit |
| **AC-P2VF-06** | 双开关 ON + 合成「≥6 次无人双竖」出现 ≥2 种非 fill 角色（gallery 与/或 asym） | unit |
| **AC-P2VF-07** | 近窗已用 gallery 后，下一次优先非 gallery（在合格池内） | unit |
| **AC-P2VF-07b** | `strength_side=left` 时不选 asymmetric-right（反之亦然）；`tie` 不选 asym | unit |
| **AC-P2VF-08** | 任一方有人 → 恒 fill | unit |
| **AC-P2VF-09** | 仅 fill 可见时不报错、不空屏 | unit |
| **AC-P2VF-10** | 日志含 `pickerReason` + `strengthSide` | 断言 |
| **AC-P2VF-11** | 盲评三问（§9.2）；**系统性「像缺图/坏版」或「主次反」→ No-Go** | acceptance-record |

---

## 9. 狗粮与盲评协议

### 9.1 样本

- 竖图密集、**人物对少**的 trip ≥2（主样本）  
- 含 late pairing 的长章 ≥1  
- **不**用人物密集团队游作为主验收样本  

### 9.2 对比与三问

| 臂 | 配置 |
|----|------|
| **A 基线** | `portrait_2_variants.enabled=false` |
| **B 候选** | 双开关 ON + 轮换集 allowlist + `cohort_trip_ids` 含本 trip |

评审 **只看 Web/screens 屏**；mobile 仅抽查拆屏可读。

**固定三问（每屏或每册汇总）：**

1. 是否比基线更生动？  
2. 是否像缺图 / 坏版？  
3. 主次是否反了？  

### 9.3 Go / No-Go

| 结果 | 动作 |
|------|------|
| 生动↑，且无系统性坏版/主次反/裁切回归 | 保留家族；考虑升 beta；再谈 offset 或其他张数 |
| 系统性「像缺图/坏版」 | **No-Go** → 收留白或下线 gallery |
| 系统性「主次反」 | **No-Go** → 修 strength 阈值或暂时只开 gallery |
| 无差异 | 查双开关 / cohort_trip_ids；或区分度不足 |

---

## 10. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 留白被看成缺图 | 面积 55–65%；纸色场；盲评问项 2 否决 |
| 主次反 | D-13 强弱选型；tie 不进 asym；问项 3 否决 |
| 换 id 绕开 R-06 | 家族 streak 常驻（D-06 / AC-05b） |
| 脸裁 | D-07 任一方有人→fill；fit 白名单（D-10） |
| experiments 配错起不来 | `cohort_trip_ids` 样例；双开关文档 |
| 手机与电脑两套 | 产品诚实叙事；盲评不评 mobile 杂志感 |
| 想顺手扩 3–9 / 塞 offset | N-01 / N-09；评审拒绝夹带 |

---

## 11. 开放问题（O-* · **已冻结**）

| ID | 结论 |
|----|------|
| **O-01** | V1 **不做**跨槽换图；用 **强弱→选 asym-L/R**（D-13） |
| **O-02** | V1 **不做** offset-left；**offset-right 延后**出轮换集（D-12） |
| **O-03** | **任一方有人 → fill**（D-07，相对 v0.1 收紧） |
| **O-04** | 软罚进 `config.yaml`；狗粮再调；governance 可选 |
| **O-05** | V1 **只做 picker**；不在 beam 加家族多样性（D-14） |

---

## 12. 附录

### 12.1 草图 ↔ ID 速查

| 草图 | id | variantRole | V1 轮换 |
|------|-----|-------------|---------|
| 满幅 | `screen-portrait-2` | `fill` | ✅ |
| ① | `screen-portrait-2-gallery` | `gallery` | ✅ |
| ② | `screen-portrait-2-asymmetric-right` | `asymmetric-right` | ✅（强弱） |
| ③ | `screen-portrait-2-asymmetric-left` | `asymmetric-left` | ✅（强弱） |
| ④ | `screen-portrait-2-offset-right` | `offset-right` | ❌ 延后 |

### 12.2 为何算法压力可控

- V1 picker 候选 ≤ **4**（fill+gallery+asym×2），每屏一次 argmax。  
- 调试面在几何品味与 planner/节奏接线，不在组合爆炸。  
- 扩展其他张数时复制 **「1 fill + ≤2～3 角色」**，勿 N×排列。

### 12.3 评审 BLK 对照（v0.2 回写状态）

| BLK | 状态 |
|-----|------|
| BLK-P2VF-01～10 | **已回写本文**（实现向条目随 PR-B 关闭） |
| 产品确认 offset 砍轮换 + asym 强弱 | **已冻结**（D-12/D-13） |

### 12.4 附录几何 · `offset-right`（非 V1 轮换）

保留草图 ④ 规格供 M3+，**不进**狗粮 allowlist：

| 项 | 规格 |
|----|------|
| **stage** | `cols: [5, 5, 1, 5, 1]` · `rows: [1, 7, 1]` |
| **slot 0/1** | `[2,2,2,2]` / `[4,4,2,2]` |
| **gridClass** | `layout-screen__grid--portrait-2-offset-right` |
| **重启条件** | gallery 盲评过「不像缺图」后，另开增量；建议同时评估 offset-left 以防单向疲劳 |

### 12.5 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.1.0** | 2026-07-27 | 初稿：4 变体 + 家族软轮换 |
| **v0.2.0** | 2026-07-27 | 六席 Must-Fix 回写；轮换集收窄；asym 强弱；人物门/streak/experiments/盲评否决门冻结 |

---

## 13. 下一步

1. **Kickoff PR-A**：落地 gallery + asym-L/R YAML/CSS/探针（对照草图 ①～③）。  
2. **PR-B**：按 §5～§6 接 picker + 节奏内核家族化 + fit/mobile。  
3. **PR-C**：`config-p2vf-dogfood.example.yaml` + 竖图多 trip 盲评三问。  
4. 通过后再议 offset 或其他张数——**本试点未验完不扩库**。
