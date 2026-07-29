# Travelogue · 拼图主图审美与趣味筛选 V1（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | **v0.1.0** |
| **状态** | **Draft · Ready for Algorithm / Product Kickoff** |
| **特性代号** | **HIT**（Hero Interest & Taste · 主图审美与趣味） |
| **文档类型** | 选片算法专项 PRD（现网 MCS / hero 主槽轨 · **不**改 LTE 几何 · **不**解冻 LSE） |
| **触发来源** | 2026-07-28 产品讨论：硬几何过关后主图仍被宽高比底座与 AR ladder boost 稀释；合格集内缺「唯美 + 有趣」决胜 |
| **前置条件** | `main_eligibility` / `constraints.eligibility` 硬门禁稳定；`purpose_overall("hero")` 与 PA 美学层可用；`main_eligible_hero_score_gap` / URO UR-01 可复用；BQP / URO / PA 盲评 harness 可复用或可同步 |
| **关联文档** | [DESIGN-PHOTO-AESTHETIC-EVALUATION.md](./DESIGN-PHOTO-AESTHETIC-EVALUATION.md)（U-HERO）· [PRD-AESTHETIC-ALIGNMENT.md](./PRD-AESTHETIC-ALIGNMENT.md) · [PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md](./PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md) · [PRD-LAYOUT-QUALITY-STACK-V1.md](./PRD-LAYOUT-QUALITY-STACK-V1.md) · [PRD-MCS-GEOMETRIC-QUALITY-V1.md](./PRD-MCS-GEOMETRIC-QUALITY-V1.md) · [PRD-PORTRAIT-CULL.md](./PRD-PORTRAIT-CULL.md) · [PRD-PHASE23-peak-moment.md](./PRD-PHASE23-peak-moment.md) · [algorithm-inventory.md](./algorithm-inventory.md) |
| **现网锚点** | `mosaic/main_eligibility.pick_best_main_eligible` · `mosaic/hero.pick_main_for_pattern` · `planner/screen_planner._pick_main_landscape_id` · `curate_scoring.hero_score` / `effective_hero_score` · `usage_rules.context.main_eligible_hero_score_gap` |
| **验收配套** | Kickoff 后拆 `ACCEPTANCE-HERO-INTEREST-TASTE-V1.md`（W1 merge 前必有） |
| **实施清单** | Kickoff 后拆 `IMPLEMENTATION-HERO-INTEREST-TASTE-V1.md` |
| **更新日期** | 2026-07-28 |

> **定位**
>
> - **几何硬门禁不变**：`asset_eligible_for_main_slot` / `constraints.eligibility` 仍是「能不能进主槽」的唯一硬闸；HIT **禁止**为趣味破几何。
> - **HIT 只解决硬闸之后**：在 main-eligible 子集上，用「唯美 + 有趣 + 用户意图」选出真正值得霸屏的一张，并用 **hero gap** 决定要不要强上主图页型。
> - **一句话目标**：几何管资格；分数管品味；差距管是否造英雄；盲评管能否默认开启。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0.1 | 拟冻结决策（D-HIT-*） |
| §1 | 问题与现网诊断 |
| §2 | 目标 / 非目标 / 成功画像 |
| §3 | 分层模型与权威序 |
| §4 | 算法合同（排序键 · 独特性 · gap · 人机） |
| §5 | 接入点与兼容 |
| §6 | 配置与开关 |
| §7 | 验收与盲评 |
| §8 | 里程碑 |
| §9 | 风险与故意不做 |
| 附录 | 公式附录 · 版本记录 |

### 0.1 拟冻结决策（D-HIT · Kickoff 拍板）

| # | 决策项 | 结论 |
|---|--------|------|
| **D-HIT-01** | 作用域 | **仅** `role=main` 的拼图主槽挑选 + 与之绑定的「是否选用 hero 页型」gap 决策；**不**改封面全量逻辑（封面可复用公式，另开 AC） |
| **D-HIT-02** | 与几何关系 | **硬资格先于品味**；HIT 排序与 soft **不得**绕过 `screen_main_slot_eligible` / `asset_eligible_for_main_slot` |
| **D-HIT-03** | 合格集内主轴 | `enabled=true` 时排序主轴 = **`purpose_overall(hero)`**（及本 PRD 定义的趣味乘子）；**禁止**再用原生 AR / `w/h` 作为主乘子 |
| **D-HIT-04** | AR ladder boost | 合格集内默认 **关闭**；仅当 top1/top2 品味分相对差 \< `ar_tiebreak_eps` 时作 **微 tiebreak**（见 §4.2） |
| **D-HIT-05** | 唯美 vs 有趣 | **拆开**：`beauty`（purpose hero）× `interest`（窗内 uniqueness 等）；禁止把 uniqueness 塞进 `overall` 再二次加权 |
| **D-HIT-06** | gap 语义 | 复用并扩展 `main_eligible_hero_score_gap`：gap 必须基于 **HIT 排序分**（非旧 `hero×AR`），阈值可配置；gap 不足 → **不选**强主图页型（移交无主次模板 / URO） |
| **D-HIT-07** | 用户 ★ | 合格集内 `userTier=featured`：**硬优先于**自动 top1（同窗有合格 ★ → 主图必须来自 ★ 子集的 HIT 最高）；无合格 ★ 时回退自动 |
| **D-HIT-08** | 落点 | 新逻辑挂 **`MosaicConfig.hero_interest_taste`**（或等价 nested）；**禁止**默认写入 `layout.scoring` / LSE |
| **D-HIT-09** | 发布门禁 | `enabled=false` 可先 merge（行为 ≡ 现网）；**默认 `enabled=true`** 须过 **AC-HIT-BLIND ≥55%** |
| **D-HIT-10** | MLLM | V1 **不做**默认路径；仅 P2 可选短名单重排；fail-open |

---

## 1. 背景与问题

### 1.1 用户可感知问题

| ID | 问题 | 典型表现 |
|----|------|----------|
| **HIT-P-01** | 主图「技术合格但不跳」 | 清晰贴 16:9 的平景霸屏，同窗更有光影/故事的图落副槽 |
| **HIT-P-02** | 几何过关后仍被比例二次偏置 | `ar_preference_boost` 让「更贴梯子」压过「明显更好看」 |
| **HIT-P-03** | 无明确主次仍硬造英雄 | top1/top2 分差极小仍选 hero+tiles，页型叙事假强 |
| **HIT-P-04** | 用户 ★ 未主导主槽 | 合格精选图输给自动 CV 高分风景 |
| **HIT-P-05** | 「清晰但重复」连庄 | 同窗 / 同章色调极近的图反复当主，缺趣味/独特性 |

### 1.2 现网事实（代码诊断）

```text
asset_eligible_for_main_slot   ← 硬：朝向 / 禁全景竖方 / AR 梯子 / 超宽
        ↓ 合格子集
pick_best_main_eligible
        sort_key = effective_hero_score × ar_preference_boost
                     ↑
        hero_score = (w/h 底座) × media × [purpose_overall 或 sharpness]
                     ↑ 美感被宽高比底座稀释
        ar_preference_boost  ← 几何已筛过，仍二次偏置贴梯子
```

| 环节 | 现状 | 问题 |
|------|------|------|
| 硬准入 | `main_eligibility.py` | ✅ 正确保留 |
| `hero_score` | 含 `w/h` 底座；开美感时乘 purpose | 底座与几何门禁信息重叠，稀释品味 |
| `ar_preference_boost` | 合格后再乘 | **双重几何** |
| gap | `main_eligible_hero_score_gap` | 用旧 hero 分；未驱动「挑选层」主动避 hero |
| featured | `×1.35` 软乘 | 不足以表达「用户指定趣味」 |
| uniqueness | PA 设计 U-SOLO 有案；主图路径未接 | HIT-P-05 |

### 1.3 与相邻主题边界

| 主题 | 关系 | HIT 做什么 |
|------|------|------------|
| **mainSlotPolicy / eligibility / MGQ** | **上游硬层** | 只消费；不改 DSL；不软化硬拒 |
| **URO UR-01** | **兄弟** | gap 阈值与「无主次不用 hero」对齐；HIT 提供 **HIT 分** 上的 gap |
| **PA / Aesthetic Alignment** | **信号业主** | HIT 消费 `purpose_overall("hero")` 与 dims；不重造 Layer 1 |
| **Portrait Cull** | **输入** | 人像主图依赖 subjectClarity / 睁眼已进 overall |
| **Peak Moment / Cover** | **正交** | 决定性瞬间与封面可后续复用 HIT 公式；V1 不改其入口 |
| **LQS / LSE** | **禁区** | 不进 LSE 软乘子上量；不 runtime 改 slot rect |

---

## 2. 目标 / 非目标 / 成功画像

### 2.1 目标

| ID | 目标 |
|----|------|
| **G-HIT-01** | 合格集内主图选择以人类可感知的「耐看 + 有趣」为主轴 |
| **G-HIT-02** | 消除合格集内 AR / 宽高比对品味分的主轴稀释（D-HIT-03/04） |
| **G-HIT-03** | gap 不足时显著减少「假英雄」页型 |
| **G-HIT-04** | 合格 ★ 精选成为主槽强信号（D-HIT-07） |
| **G-HIT-05** | `enabled=false` 与现网逐屏一致；默认开启绑盲评 |

### 2.2 非目标（V1）

| ID | 非目标 |
|----|--------|
| **N-HIT-01** | 放宽或替换几何硬门禁（含为趣味破 AR） |
| **N-HIT-02** | 新建品类全管线（写真/宠物等）；品类 Profile 另案，HIT 只提供可挂接的排序键 |
| **N-HIT-03** | 默认开启 MLLM / CLIP 全量嵌入 |
| **N-HIT-04** | 修图、智能裁切策略大改（可继续用既有 focal） |
| **N-HIT-05** | 副槽全序重排（副槽仍时间/角色填；仅主槽 HIT） |
| **N-HIT-06** | 产品电商图专用模式 |

### 2.3 成功画像

- 同窗 3～5 张均 main-eligible 时，盲评者更常选 HIT 主图而非「最贴 16:9」。
- 用户标 ★ 的合格图显著更常落主槽。
- 分差极小的窗口更常落无主次模板，少「强行主图」感。
- 决策日志可解释：`beauty` / `interest` / `featured_override` / `gap` / `reject_hero_page`。

---

## 3. 分层模型与权威序

### 3.1 硬 → 软权威序（一字面）

```text
1. LTE 几何 / slot 拓扑          （不可改）
2. main eligibility 硬门禁       （HIT 只读）
3. URO usage 硬过滤              （含 UR-01 类；可消费 HIT gap）
4. HIT 主槽排序 + gap 页型决策   （本 PRD）
5. MCS / scorer soft             （几何 soft、重复密度等；不得推翻 2）
```

对齐 LQS：**geometry → … → eligibility → soft**；HIT 落在 eligibility 之后、页型决胜之前。

### 3.2 三层品味模型（消费 PA）

| 层 | 名称 | HIT 用法 |
|----|------|----------|
| **L1 技术及格** | sharpness / 曝光底线 | 仅 tiebreak；不主轴 |
| **L2 唯美** | composition · lighting · color · purpose_overall(hero) | **`beauty` 主轴** |
| **L3 趣味** | 窗内 uniqueness · 叙事锚点 · ★ ·（可选）peak | **`interest` 与意图乘子** |

> 诊断对齐 [PRD-AESTHETIC-ALIGNMENT.md](./PRD-AESTHETIC-ALIGNMENT.md)：人类偏好在 L2+L3；现网主图仍被 L1/几何代理主导。

---

## 4. 算法合同

### 4.1 合格集

```text
Eligible(pattern_id, window) =
  { aid ∈ window | asset_eligible_for_main_slot(aid, pattern_id) }

若 Eligible = ∅ → 本 pattern 不可建主槽（保持现网：候选失败 / 硬罚）
HIT 仅在 Eligible 非空时运行
```

### 4.2 排序键（合格集内）

#### 4.2.1 唯美 `beauty`

```text
beauty(aid) = purpose_overall(aid, "hero")     # 缺省 fail-open → 回退 aesthetic.overall
              若仍缺 → clamp01(sharpness / median_sharp) 作弱代理并记 reason=beauty_fallback_sharp
```

**禁止**（`hit.enabled=true` 时）：

- 以 `width/height` 或 `aspect_kind` 偏好作为 `beauty` 主乘子  
- 对 Eligible 再乘完整 `ar_preference_boost` 作为主轴  

#### 4.2.2 趣味 `interest`（窗内独特性）

相对 **同一窗口 Eligible∪window**（默认整个 MCS 窗口；配置可改为「同章已用主图 + 本窗」）：

```text
# V1 默认：Lab 主色 ΔE76 代理（复用 delta_e_cie76 / tone_uniqueness 思路）
tone_dist(aid, peers) = median ΔE76(dominantTone(aid), dominantTone(p)) for p in peers\{aid}

uniqueness(aid) = triangular_or_rank_norm(tone_dist) ∈ [0, 1]
                  # 过近（ΔE < u_near）→ 低；适中高；过跳可选轻罚（默认不轻罚）

interest(aid) = (1 - λ_u) + λ_u * uniqueness(aid)     # 默认 λ_u = 0.4 → (0.6 + 0.4 u)
```

| 规则 | 说明 |
|------|------|
| 范围 | **窗内**（或章内已曝光主图），**禁止**相对全库 |
| CLIP | V1 不默认；配置位预留 `interest_backend: delta_e \| clip` |
| 单 eligible | `interest = 1.0`（无对照） |

#### 4.2.3 意图乘子

```text
featured_mult(aid) =
  若启用 D-HIT-07 硬优先：不进入连续乘子，见 §4.4
  否则（兼容模式）：featured_weight（默认 ≥ 现网 1.35，建议可配到 1.6）

anchor_mult(aid) = 现网 anchor_match_multiplier（记忆地标等）  # 保持；默认弱

narrative_mult(aid) = 可选 P1：peak/moment 池命中 → 1.0+ε；未接线时 ≡ 1.0
```

#### 4.2.4 综合分与选择

```text
hit_score(aid) = beauty(aid) × interest(aid) × featured_mult(aid) × anchor_mult(aid) × narrative_mult(aid)

pick_main =
  max(Eligible, key=hit_score)
  tiebreak1 = sharpness
  tiebreak2 = ar_ladder_proximity   # 仅当 |hit_score1 - hit_score2| / max(hit_score1,ε) < ar_tiebreak_eps
  tiebreak3 = assetId 字典序       # 确定性
```

**AR 微 tiebreak**（D-HIT-04）：

- `ar_tiebreak_eps` 默认 `0.02`（相对差）  
- 仅比较 `preferLadder` 距离，**加分量级不得改变**非极近对的胜负  

### 4.3 Gap 与「是否强主图页」

```text
scores = sorted([hit_score(a) for a in Eligible], reverse=True)
gap =
  +inf  if len(scores) <= 1
  scores[0] - scores[1]  otherwise

若 pattern 需要明确主次（hero+tiles 类）且 gap < hero_gap_threshold_hit:
  → 拒绝本 hero pattern（reason=hit_gap_insufficient）
  → 交 URO / MCS 选无主次或弱主次 sibling
```

| 合同 | 说明 |
|------|------|
| 与 URO | `hero_gap_threshold` 可映射为 `hero_gap_threshold_hit`；**禁止**两套互相矛盾的默认值长期并存（W1 须单一 SSOT 或显式 alias） |
| 分母 | gap 基于 **hit_score**，不是旧 `effective_hero_score×boost` |
| 单合格 | gap=`+inf` → **结构合格**（与 MTSO 可行性结论一致） |
| 日志 | 写入 mosaic decision log：`hit_gap` / `hit_beauty` / `hit_interest` |

### 4.4 用户 ★ 硬优先（D-HIT-07）

```text
FeaturedEligible = { a ∈ Eligible | userTier == featured }

若 FeaturedEligible ≠ ∅:
  main = argmax hit_score over FeaturedEligible
  reason += featured_override
否则:
  main = argmax hit_score over Eligible
```

| 规则 | 说明 |
|------|------|
| 不合格 ★ | 不进 FeaturedEligible（几何仍至上） |
| 多 ★ | 仅在 ★ 子集内比 HIT |
| 开关 | `featured_hard_prefer: true`（默认 true）；false 时退回软乘子 |

### 4.5 Cohort / 双人同框（P1 软）

若 trip 启用 cohort 且窗口含双人同框标记：对 Eligible 内命中资产 `× cohort_main_boost`（默认 1.08，ceiling 防止淹没 beauty）。**V1 可只留配置与探针，不强制默认开。**

### 4.6 人像主槽模板

当 `eligibleAspectKinds` 含 `portrait`（竖主家族）：

- 仍走 HIT；`beauty` 继续 `purpose_overall("hero")`（或配置映射 `purpose_overall("moment")` 若盲评证明更优）  
- subjectClarity / 睁眼已由 PA + Portrait Cull 进入 overall → **不另写第二套人脸分**  
- uniqueness 对竖主同样按窗内 ΔE  

---

## 5. 接入点与兼容

### 5.1 必须改写的调用点

| 模块 | 函数 | 变更 |
|------|------|------|
| `mosaic/main_eligibility.py` | `pick_best_main_eligible` | `hit.enabled` 时改用 `hit_score`；AR boost 降为微 tiebreak |
| `mosaic/hero.py` | `pick_main_for_pattern` | 走新 pick；保持无 main role 回退 |
| `planner/screen_planner.py` | `_pick_main_landscape_id` | 仅作 `hit.enabled=false` 旧路径或内部委托 |
| `mosaic/builders.py` | `_order_hero_six*` 等 | 继续调 `pick_best_main_eligible`（自动吃到 HIT） |
| `usage_rules/context.py` | `main_eligible_hero_score_gap` | 可选参数 `score_fn=hit_score`；默认随 HIT 开关切换 |
| `mosaic/hook.py` | single hero rescue | gap 改读 HIT 分 |

### 5.2 兼容与回归

| 模式 | 行为 |
|------|------|
| `hero_interest_taste.enabled=false` | **逐屏**与现网 baseline 一致（AC-HIT-01） |
| `enabled=true` 但 aesthetic 缺失 | beauty fail-open 到 sharpness 代理；interest=1.0；不阻断 curate |
| 旧 `hero_score` 宽高比 | 仅旧路径保留；新路径单测断言「Eligible 内 AR 不改变非极近对胜负」 |

### 5.3 解释与探针

- Studio / decision log 字段（schema 同步）：`hitBeauty` · `hitInterest` · `hitScore` · `hitGap` · `hitReason`（`auto` \| `featured_override` \| `gap_reject` \| `beauty_fallback_sharp`）  
- 可选 explain 块：「主图因构图/光影更高；同窗另一张色调过近」

---

## 6. 配置与开关

挂载建议：`config.mosaic.hero_interest_taste`（或 `config.layout.hero_interest_taste`，Kickoff 二选一写死；**推荐 MosaicConfig** 以贴近主槽业主）。

```yaml
mosaic:
  hero_interest_taste:
    enabled: false                 # 默认 false；盲评过后方可 true
    uniqueness_lambda: 0.4         # interest = (1-λ)+λ*u
    uniqueness_scope: window       # window | chapter_mains
    interest_backend: delta_e      # delta_e | clip（clip=P2）
    u_near_delta_e: 8.0            # 过近降权起点（可标定）
    ar_tiebreak_eps: 0.02          # 相对差内才允许 AR 微决胜
    hero_gap_threshold: 0.15       # 与 URO alias；SSOT 在实现清单写死
    featured_hard_prefer: true
    featured_soft_weight: 1.6      # hard_prefer=false 时使用
    cohort_main_boost: 1.08
    cohort_boost_enabled: false    # P1
    narrative_boost_enabled: false # P1 peak
    log_probes: true
```

**铁律**：`enabled=false` ⇒ 不读上述权重；输出与 baseline 字节级或逐屏结构一致（以现有 mosaic golden / fixture 为准）。

---

## 7. 验收与盲评

### 7.1 功能验收（AC-HIT）

| ID | 验收项 | 级别 |
|----|--------|------|
| **AC-HIT-01** | `enabled=false` 与 baseline 逐屏一致 | A · merge 门 |
| **AC-HIT-02** | Eligible 外资产永不可被 HIT 选中 | A |
| **AC-HIT-03** | `enabled=true` 时非极近对：改变 AR 不翻转 hit 胜者（单测合成） | A |
| **AC-HIT-04** | FeaturedEligible 非空 ⇒ main ∈ FeaturedEligible | A |
| **AC-HIT-05** | gap \< threshold ⇒ hero pattern 拒绝且 reason=`hit_gap_insufficient` | A |
| **AC-HIT-06** | 单 Eligible ⇒ gap=+inf 且可建主槽 | A |
| **AC-HIT-07** | decision log 含 beauty/interest/gap/reason | B |
| **AC-HIT-08** | aesthetic 全缺 ⇒ fail-open 不崩 curate | A |

### 7.2 盲评门禁（AC-HIT-BLIND）

| 项 | 合同 |
|----|------|
| **协议** | 同窗 Eligible 快照；评者二选一「更适合做杂志主图」：A=现网 `hero×AR` · B=HIT |
| **样本** | 与 URO/BQP **共用 trip 集** + 至少 30 个「多 Eligible」窗口；分类型诊断（旅行/人像/混合）**非** Gate |
| **Gate** | **B 胜率 ≥ 55%**（aggregate）；未达不得默认 `enabled=true` |
| **禁区** | 禁止仅用 proxy 分（平均 beauty↑）代替盲评发布 |

### 7.3 狗粮 A/B（落地第 0 步）

1. 导出同窗 Eligible 集 + 两侧选中主图缩略图  
2. 作者盲选（对齐 AA DA-1）  
3. 记录 HIT-P-01/02/05 是否改善；再开权重标定  

---

## 8. 里程碑

| 阶段 | 内容 | 预估 | 退出标准 |
|------|------|------|----------|
| **W0** | 开关骨架 · 探针字段 · `enabled=false` 等价 fixture · 本文决策 Kickoff | 1–2d | AC-HIT-01 |
| **W1** | 改 `pick_best_main_eligible` 主轴；关 AR 主 boost；gap 接 HIT 分；★ 硬优先 | 3–5d | AC-HIT-02～06；狗粮 A/B 可读 |
| **W2** | 窗内 ΔE uniqueness · interest 乘子 · 日志 explain | 2–3d | AC-HIT-07；兴趣项可关 |
| **W3** | 盲评 AC-HIT-BLIND；hero 预设权重轻标定（构图/光影） | 3–5d | ≥55% 方可默认开 |
| **P1** | narrative/peak 弱 boost · cohort boost · 章内 uniqueness scope | 2–4d | 分项 AC + 不回归盲评 |
| **P2** | CLIP uniqueness 或 MLLM 短名单重排（可选） | 另估 | fail-open；非默认 |

**合计（V1 默认开启）**：约 **11–19 人日**（不含 P1/P2）。

---

## 9. 风险与故意不做

### 9.1 风险

| 风险 | 缓解 |
|------|------|
| beauty 与旧 hero 分布不同，gap 阈值失效 | W1 用 HIT 分重标定 threshold；与 URO 联调 |
| ΔE uniqueness 误伤「系列感」成组大片 | λ 可降；scope 可改 chapter；盲评分层看风景册 |
| ★ 硬优先导致用户乱标毁版 | 仅 Eligible 内生效；文档提示；可关 `featured_hard_prefer` |
| 与 MGQ soft / 主槽惩罚双计 | HIT 不管裁切几何 soft；职责表写死 |
| 竖主 purpose=hero 不准 | W3 盲评人像层；必要时 purpose 映射可配 |

### 9.2 故意不做

- 为「更有趣」放行 off-ladder / 竖图进横主槽  
- 一类相册一条完整 curate 管线（应用 Profile 挂 HIT 权重即可）  
- 默认 MLLM 全量评分  
- 用 HIT 替换封面/高光池入口（可复用，须另 AC）

---

## 附录 A · 公式速查

```text
Eligible = main-eligible(window, pattern)

beauty    = purpose_overall(hero) | fallback_sharp
interest  = (1-λ) + λ * uniqueness_window(ΔE)
hit_score = beauty × interest × [featured_soft?] × anchor × [narrative?]

main =
  argmax hit_score(FeaturedEligible)  if FeaturedEligible ≠ ∅ and hard_prefer
  else argmax hit_score(Eligible)
  + sharpness tiebreak
  + AR proximity tiebreak only if relative score gap < eps

gap = +∞ if |Eligible|≤1 else hit_top1 - hit_top2
admit_hero_page = gap ≥ hero_gap_threshold
```

## 附录 B · 与既有建议映射

| 原建议 | 本 PRD |
|--------|--------|
| 改排序键 / 关 AR boost | §4.2 · D-HIT-03/04 |
| 唯美与有趣拆开 | §4.2.1–4.2.2 · D-HIT-05 |
| gap 决策 | §4.3 · D-HIT-06 |
| ★ 强信号 | §4.4 · D-HIT-07 |
| 落地序 狗粮→标定→ΔE→MLLM | §8 W0–W3 / P2 |

## 附录 C · 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-07-28 | 初稿：硬几何后 HIT 品味层；拟冻结 D-HIT-01～10；待 Kickoff 拍板后拆 ACCEPTANCE / IMPLEMENTATION |
