# Travelogue · 导入素材质量路由 V1（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | **v0.2.0** |
| **状态** | **Conditional Go · BLK 已回写**（[评审纪要 2026-07-29](./acceptance-records/iqr-ingest-quality-routing-v1-review-2026-07-29.md)）· 可 Kickoff W0；**W1 merge 前拆 ACCEPTANCE + IMPLEMENTATION** |
| **特性代号** | **IQR**（Ingest Quality Routing · 导入质量路由） |
| **文档类型** | 导入前素材策略路由 PRD（管线 Profile · 含前端选项与自动默认） |
| **触发来源** | 2026-07-29 产品讨论：精选夹出片惊艳 vs 杂乱夹出片凌乱；根因在选片而非版式；需按输入质量分策略 |
| **前置条件** | Phase 9 photo cull 稳定；Import Wizard `photoKeepMode`（P9-F3）已落地；[P9-F1](./PRD-PHOTO-CULL-USER-TOGGLE.md) 语义可兼容迁移 |
| **关联文档** | [PRD-PHOTO-CULL-USER-TOGGLE.md](./PRD-PHOTO-CULL-USER-TOGGLE.md) · Import Wizard `photoKeepMode` · [PRD-EXPERIENCE-附录A-精选上传.md](./PRD-EXPERIENCE-附录A-精选上传.md) · [PRD-PHASE9.md](./PRD-PHASE9.md) · [PRD-HERO-INTEREST-TASTE-V1.md](./PRD-HERO-INTEREST-TASTE-V1.md) · [RESEARCH-PHOTO-QUALITY-SELECTION-SURVEY-2026-07-28.md](./RESEARCH-PHOTO-QUALITY-SELECTION-SURVEY-2026-07-28.md) |
| **验收配套** | W1 前拆 `ACCEPTANCE-INGEST-QUALITY-ROUTING-V1.md`（**BLK-12**） |
| **实施清单** | W1 前拆 `IMPLEMENTATION-INGEST-QUALITY-ROUTING-V1.md`（含派生真值表） |
| **评审纪要** | [iqr-ingest-quality-routing-v1-review-2026-07-29.md](./acceptance-records/iqr-ingest-quality-routing-v1-review-2026-07-29.md) |
| **更新日期** | 2026-07-29 |

> **定位**
>
> - 创建游记前为素材集选择 **`ingestQualityMode`**，驱动不同去除率、文案承诺与（`messy`）确认门。
> - **用户可不选**：系统预选推荐；默认安全落点 **`typical`**。自动推荐可标 `messy`，但 **未显式确认前不得生效 `messy`**。
> - **不**替代品类 Profile；IQR 管「素材质量策略」，品类管「内容主轴」。
> - **一句话目标**：精选夹全力排版；乱册强精简并诚实降承诺；大多数一般册轻剔废保故事。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0.1 | 冻结决策（D-IQR-* · v0.2.0 已消化 BLK） |
| §0.2 | 与 HIT / 精选上传边界 |
| §1 | 背景与三分法 |
| §2 | 目标 / 非目标 |
| §3 | 模式合同 + 阈值表 |
| §4 | 前端 · 合并矩阵 · FE 任务 |
| §5 | 自动推断（W2；W1 可砍） |
| §6 | 数据模型 · `resolve_ingest_quality_policy` |
| §7 | 验收（量化）与发布门 |
| §8 | 里程碑 |
| §9 | 风险与叙事红线 |
| 附录 | P9-F3 迁移 · 文案 · 版本 |

### 0.1 冻结决策（D-IQR）

| # | 决策项 | 结论 |
|---|--------|------|
| **D-IQR-01** | 三模式 | `curated` · `typical` · `messy` |
| **D-IQR-02** | 用户可不选 | **允许**；未改选项 → 采用当前预选；推断失败/未就绪 → **`typical`** |
| **D-IQR-03** | 默认安全模式 | **`typical`** |
| **D-IQR-04** | `curated` | ≡ 现网 **`keep_all` 级**：跳过质量 cull **+** 跳过低清硬丢；仍执行损坏/非图 / contentSig dedupe / `max_photos`。文案**禁止**「全部进排版」绝对表述；须 N/M 诚实 |
| **D-IQR-05** | `messy` | 高去除率；**T0 点「开始制作」前**确认门（估 M/N）；`keep_ratio_floor=0` |
| **D-IQR-06** | `typical` | 轻剔废；Pass C = **soft_demote only**；禁止按 messy 力度砍张数 |
| **D-IQR-07** | 与 P9-F3 | **方案 A**：`ingestQualityMode` **取代** `photoKeepMode` 为唯一主路径意图枚举；主路径**禁止**双三选一。`keep_bursts` → `typical` 下进阶「保留连拍」 |
| **D-IQR-08** | 可改 | V1：重新导入改模式；P1：预览「换策略重排」 |
| **D-IQR-09** | 叙事 | 禁「放弃懒用户」；禁把 IQR 说成「更懂审美/挑封面」（那是 HIT）；`messy` =「强力精简 · 请确认」 |
| **D-IQR-10** | 发布 | `enabled=false` ≡ **现网 F3 向导 + 派生行为**；`enabled=true` 须过 §7.3 发布门 |
| **D-IQR-11** | 意图单源 | 全管线只读 `resolve_ingest_quality_policy(...)`；禁止 FE 本地多源推导 |
| **D-IQR-12** | 自动 messy | 推荐徽标可标 messy；**「不改直接开始」不得无确认生效 messy**（必须过 T1，或用户曾显式点选 messy） |
| **D-IQR-13** | 会话记忆 | 新会话默认推荐/`typical`；**不跨会话**记住 `messy`/`curated`（对齐 P9-F1） |
| **D-IQR-14** | W1 范围 | **W1 不含自动推断**（固定预选 `typical` + 显式三模式）；推断与推荐徽标刷新 → **W2**（仍受 D-IQR-12） |
| **D-IQR-15** | ★ | V1：`★ ≡ userTier=featured`；百分位分母排除 ★；Pass C 不出局 |

### 0.2 与 HIT / 精选上传边界

| 能力 | 管什么 | 不管什么 |
|------|--------|----------|
| **IQR** | 入库池厚度与 cull 强度；导入前策略 UI | 主槽品味、LTE 几何、封面算法权重 |
| **HIT** | 几何硬门后的主槽 `purpose_overall(hero)` 品味 | 不驱动 `ingestQualityMode`；不改 LTE |
| **精选双文件夹 / `userTier=featured`** | 资产级 ★ 豁免与双夹上传体验 | ≠ IQR `curated`；`curated` 是「整夹近全收」，不是「标了 ★」 |
| **优先级一句** | ★ 在 cull 中硬保留；HIT 在已入池片上挑主槽；IQR 先决定池多大 | — |

---

## 1. 背景与问题

### 1.1 狗粮事实

| 输入 | 输出观感 | 根因 |
|------|----------|------|
| 人已精选的旅行优质片 | 工整甚至惊艳 | 版式够用，天花板高 |
| 杂乱无章手机片 | 版面工整但游记凌乱 | **选片未抬天花板** |

### 1.2 三分法（产品）

| ID | 类型 | 用户画像 | 策略要点 |
|----|------|----------|----------|
| **(1)** | 已精选 | 摄影师、写真集、自筛文件夹 | **近全收 · 不筛质量 · 省时间** |
| **(2)** | 大乱册 | 张数多、未整理连拍（估少数） | **极大提高去除率** + 降承诺 + 确认 |
| **(3)** | 质量一般 | **用户量最大**；少部分杂片 | **不能大比例淘汰**；轻剔废 + 相对择优 |

### 1.3 现网缺口

- P9-F1 二元勾选已被 **P9-F3 `photoKeepMode`**（`recommended` / `keep_bursts` / `keep_all`）取代，但仍**无法表达「强精简乱册」**。
- 现网 cull 默认 `keep_ratio_floor≈0.90` → 乱册「去不干净」部分是地板保护，不是缺第三个营销卡。
- 无 `messy` 合同与确认门；无与 HIT 正交的「先缩池再品味」权威序。

---

## 2. 目标 / 非目标

### 2.1 目标

| ID | 目标 |
|----|------|
| **G-IQR-01** | 创建路径可选三模式；**不选则走预选**（失败/未就绪 → `typical`） |
| **G-IQR-02** | `curated` 近全收排版；跳过质量 cull 与低清硬丢 |
| **G-IQR-03** | `messy` 明显提高去除率，T0 确认门 + 量化保留率 |
| **G-IQR-04** | `typical` 轻剔废，成册厚度与故事连贯优于猛砍 |
| **G-IQR-05** | 与 F3 合并为**单一**主控件；FE 任务可实施 |

### 2.2 非目标（V1）

| ID | 非目标 |
|----|--------|
| **N-IQR-01** | 完美自动对齐人类审美（后续接 HIT） |
| **N-IQR-02** | 默认依赖 MLLM |
| **N-IQR-03** | 与品类（写真/宠物）合并为同一选择器 |
| **N-IQR-04** | V1 完整 shortlist 编辑器 |
| **N-IQR-05** | 修改 LTE 几何 / 解冻 LSE |
| **N-IQR-06** | W1 自动推断 / probe 刷新推荐（→ W2） |

---

## 3. 模式合同（算法）

### 3.1 枚举

```text
ingestQualityMode ∈ { curated, typical, messy }
```

排序键（Pass C）：与现网 `_cull_score` 一致（sharpness + aesthetic 合成，可配）。  
百分位分母：**Pass A/B 后仍存活且非 ★** 的集合。

### 3.2 `curated`（已精选）

| 项 | 合同 |
|----|------|
| 质量 cull | **跳过** `apply_photo_cull` |
| 低清门 | **跳过**硬丢（≡ `keep_all`） |
| 仍执行 | 损坏/非图；contentSig dedupe；`max_photos` |
| 排版 | 硬无效外尽量 `layoutEligible`；**允许 M≤N**（去重等） |
| 进度文案 | **不出现**「正在挑选照片」 |
| 成功文案 | 禁「全部进入排版」；用「已按精选尽量保留 · M 张进入排版」 |

### 3.3 `typical`（一般 · 默认）

| 项 | 合同 |
|----|------|
| Pass A | 硬废：严重模糊、严重曝光失败、截图类等（对齐现网） |
| Pass B | 连拍组内留 **`burst_keep: 2`**（进阶「保留连拍」时可抬高/放宽 near-dup） |
| Pass C | **`pass_c_action: soft_demote`**：垫底 `bottom_soft_pct` 非 ★ → **不进封面/hero/moment/签名**；**仍** `layoutEligible=true` |
| 地板 | `keep_ratio_floor: 0.88`；`score_topk_ratio: 1.0`（不靠 topk 猛砍） |
| 禁止 | 按 messy 的 top% 硬砍导致故事空洞 |
| KPI | eligible/N（无 ★、一般册）∈ **[0.85, 0.95]** |

### 3.4 `messy`（需强力精简）

| 项 | 合同 |
|----|------|
| Pass A | 更严（`blur_percentile` 可配更高） |
| Pass B | `burst_keep: 1` |
| Pass C | **`pass_c_action: hard_cull`**：非 ★ 仅保留 `keep_top_pct`；其余 `layoutEligible=false` |
| 地板 | **`keep_ratio_floor: 0.0`（关闭）**——服从 top%；另用 `min_layout_eligible` 护栏 |
| ★ | 硬保留；不进百分位分母 |
| 确认门 | **仅 T0 提交前**（§4.4）；禁止 FirstSuccess 后再弹 |
| KPI | 中等乱册 eligible/N ≈ **0.20–0.35**；且 ≤ 同册 typical 的 **0.55×** |

### 3.5 配置挂载（冻结默认）

```yaml
ingest:
  quality_routing:
    enabled: false
    default_mode: typical
    auto_infer: false          # W1 关；W2 开
    messy_confirm_gate: true

    infer:                     # W2
      curated_max_n: 60
      messy_min_n: 150
      burst_density_low: 0.12
      burst_density_high: 0.35
      tech_fail_rate_low: 0.05
      tech_fail_rate_high: 0.18
      min_signals_for_non_typical: 2
      forbid_auto_messy_below_n: 120

    curated:
      skip_quality_cull: true
      skip_low_res_hard_drop: true

    typical:
      blur_percentile: 2.0
      burst_keep: 2
      pass_c_action: soft_demote
      bottom_soft_pct: 0.12
      keep_ratio_floor: 0.88
      min_keep: 15
      score_topk_ratio: 1.0

    messy:
      blur_percentile: 5.0
      burst_keep: 1
      pass_c_action: hard_cull
      keep_top_pct: 0.25
      keep_ratio_floor: 0.0
      min_keep: 12
      min_layout_eligible: 12
      featured_exempt: true
```

---

## 4. 前端 · 用户选项 · 合并矩阵

### 4.0 与现网合并矩阵（**D-IQR-07 · BLK-01**）

| 用户目标 | IQR（权威） | 现网 `photoKeepMode` | 派生布尔（BE 写出，FE 不另推） |
|----------|-------------|----------------------|--------------------------------|
| 已筛好，别再丢 | **`curated`** | ← `keep_all` | `photoCullEnabled=false`；`skip_low_res=true`；`keepNearDuplicates=true` |
| 大多数手机册 | **`typical`**（默认） | ← `recommended` | `photoCullEnabled=true`；默认连拍择优 |
| 乱册要砍薄 | **`messy`**（新） | 无旧档 | `photoCullEnabled=true` + messy overlay |
| 保留连拍（进阶） | `typical` + **`keepNearDuplicates=true`** | ← `keep_bursts` | **不占主卡**；进阶抽屉/折叠 |

**UI 唯一主控件**：confirm 区 IQR 三选一。  
原「调整照片处理」抽屉 → **收敛为 IQR 派生摘要**（如「普通相册 · 连拍择优」）+ 可选「进阶」（连拍）。  
**禁止**主路径再出现第二套三选一。

### 4.1 出现时机

| 步骤 | 界面 | 说明 |
|------|------|------|
| **T0** | confirm 步、「开始制作」前 | **主路径**：IQR 三卡（导入模式双卡之下） |
| **T0b**（W2/P1） | 轻量探针后 | 刷新推荐徽标；**不**覆盖 `source=user` |
| **T1** | 用户提交且生效将为 `messy` | **仅 T0 提交前 Modal**（估 M/N）；过门后才派发 job |
| **T1b** | 精简后 &lt; `min_layout_eligible` | 过少门：主 CTA「改用普通相册」 |
| **T2**（P1） | 预览 / 设置 | 「更换素材策略并重新策展」 |

**V1 / W1 必做**：T0 + T1（仅用户显式选 messy 时）+ T1b。  
**W2**：T0b + 自动推荐徽标（仍受 D-IQR-12）。  
**P1**：T2。

### 4.2 用户可见选项（三选一）

控件：`role="radiogroup"` + 三张 `role="radio"` 卡片（复用 `v2-wizard__mode-card`）。  
区标题（结果导向）：**「这批照片希望怎么处理？」**

| value | 对外标题 | 副文案（建议） | 推荐徽标 |
|-------|----------|----------------|----------|
| `curated` | **已是精选** | 几乎每张都会进册（只排除损坏与完全重复）。适合已筛好的导出夹。点选即表示接受几乎不删片。 | W2：推断=`curated` |
| `typical` | **普通相册** | 去掉明显废片与重复连拍，尽量保留旅行故事。大多数手机相册、不确定时选这个。 | W1 默认；W2：推断=`typical` 或回退 |
| `messy` | **需要强力精简** | 未整理的大量连拍会明显变少，并请你确认。适合一次性导入海量未整理片。 | W2：推断=`messy`（仅徽标；生效须确认） |

辅助：

- 灰字：**「不确定就用推荐项。」**（W1：推荐≡普通相册）
- 「恢复推荐」（用户改选后出现）·「了解区别」（P1 可用三行折叠）
- 窄屏：≤639 **单列竖卡**；≥640 三列；主 CTA **sticky 底栏**

### 4.3 用户不选择时的行为

| 用户行为 | 系统行为 |
|----------|----------|
| 未改选项，直接开始 | W1：生效 **`typical`**。W2：若预选为推荐且推荐≠messy → 用推荐；若推荐=messy → **先弹 T1**，确认前不派发 |
| 推断未完成极速开始 | **`typical`**；开始后模式锁定 |
| 信号不足 | **`typical`** + `source=auto_fallback` |
| 用户显式点选 | `source=user`；不被后续推断覆盖 |
| `enabled=false` | 回退现网 F3 `photoKeepMode` UI 与行为（AC-IQR-07） |

### 4.4 `messy` 确认门（T1）· 时序冻结

**钉死：T0 提交前确认**（用探针或保守公式估 M/N）。**不**进管线中段 pause；**不**在 FirstSuccess 后弹。

| 元素 | 内容 |
|------|------|
| 触发 | 即将提交的生效模式为 `messy` |
| 标题 | 将强力精简这批照片 |
| 正文 | 约 N 张里预计留下约 M 张。会优先去掉明显模糊和连拍重复；你标记过的（★）会尽量保留。想多留故事请选「改用普通相册」。 |
| M/N | `ceil(n * keep_top_pct) + ★` 或同 profile 干跑计数；误差目标 ≤15%（狗粮） |
| 主按钮 | 确认并继续 |
| 次按钮 | 改用「普通相册」（切 `typical` 并继续） |
| 第三 | 返回修改策略（回 confirm，预选当前） |
| 过少门 T1b | 标题「精简后照片可能过少」；主 CTA「改用普通相册」；次「仍要继续（风险）」；埋点 `iqr_messy_too_few` |

### 4.5 进度与成功面文案

| 模式 | Importing hint | FirstSuccess 次行 |
|------|----------------|-------------------|
| `curated` | 正在导入照片…（无「挑选」） | 已按精选尽量保留 · M 张进入排版 |
| `typical` | 正在导入并整理照片… | 已去掉明显废片与重复 · M 张进入排版 |
| `messy` | 正在强力精简照片… | 已强力精简 · M 张进入排版（可换策略重做 · P1 入口就绪前勿空头支票） |

词表禁令：禁「智能挑选最好的」「AI 审美」；`typical` 限「明显废片/重复」。

### 4.6 前端任务清单（FE）

| ID | 任务 | 优先级 | 验收 |
|----|------|--------|------|
| **FE-IQR-01** | confirm 区 IQR 三模式单选 UI | P0 | 互斥；W1 默认 `typical` |
| **FE-IQR-02** | 「推荐」徽标（W2 绑推断；W1 可固定在 typical） | P0/W2 | §4.3 |
| **FE-IQR-03** | **隐藏/移除**旧二元勾选 **与** 主路径 `photoKeepMode` 三档并行；抽屉改摘要+进阶 | P0 | 附录 A；无双三选一 |
| **FE-IQR-04** | 提交 `ingestQualityMode` + `source`（+ 进阶连拍布尔） | P0 | intent 有字段 |
| **FE-IQR-05** | 推断未就绪仍可点开始 → `typical` | P0 | 不死锁 |
| **FE-IQR-06** | `messy` T1 Modal（焦点陷阱 / Esc） | P0 | AC-IQR-06 |
| **FE-IQR-07** | 进度 / FirstSuccess 文案分支；与旧 cull 文案优先级表 | P0 | §4.5 |
| **FE-IQR-08** | 「了解区别」三点折叠 | P1 | 文案过审 |
| **FE-IQR-09** | 预览换策略重排 | P1 | re-curate |
| **FE-IQR-10** | `POST /ingest/probe` 刷新推荐 | P1/W2 | 不覆盖 user |
| **FE-IQR-11** | a11y：独立 radiogroup `aria-label`；推荐 `aria-describedby` | P0 | 抽检 |
| **FE-IQR-12** | 埋点：`iqr_mode_shown` / `selected` / `auto_used` / `messy_confirm` / `messy_too_few` | P0 | 可读 |
| **FE-IQR-13** | 「恢复推荐」；触摸后禁止推断覆盖 | P0 | UX-06 |
| **FE-IQR-14** | 与 `photoKeepMode` 草稿/脏确认 **合并迁移**；禁双写推导 | P0 | BLK-01/02 |
| **FE-IQR-15** | 窄屏竖排 + sticky CTA | P0 | ≤639 |
| **FE-IQR-16** | `min_layout_eligible` 过少门 UI | P0 | T1b |
| **FE-IQR-17** | T1 估算中禁用主按钮；取消回 confirm | P0 | 时序 |
| **FE-IQR-18** | confirm **与** fine 步状态同步 | P0 | 无分歧 |
| **FE-IQR-19** | 会话草稿：mode + source + touched（不跨会话记 messy/curated） | P1 | D-IQR-13 |
| **FE-IQR-20** | 错误文案从「调整照片处理」改 IQR 话术 | P1 | — |
| **FE-IQR-21** | `enabled=false` 回退 F3 三档 UI | P0 | AC-IQR-07 |
| **FE-IQR-22** | `curated` 点选短确认或副文案代价句（防误点） | P0 | U-01 / BLK-09 |

### 4.7 线框（confirm · 桌面）

```text
┌─ 创建游记 · 确认并开始 ──────────────────────────┐
│  旅行手机相册                    [更换]        │
│  清点完成 · 约 128 张                          │
│                                                  │
│  ┌─ 快速分享 ──┐  ┌─ 精细制作 ─┐               │
│  └─────────────┘  └────────────┘               │
│                                                  │
│  这批照片希望怎么处理？                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ 已是精选 │ │普通相册  │ │强力精简  │        │
│  │ 几乎全留 │ │ ★推荐    │ │ 需确认   │        │
│  └──────────┘ └──────────┘ └──────────┘        │
│  不确定就用推荐项 · [了解区别] · [恢复推荐]     │
│  摘要：连拍择优（进阶可改）          [进阶 ▾]   │
│                                                  │
│             [ 开始制作 → ]                       │
└──────────────────────────────────────────────────┘
```

---

## 5. 自动推断（**W2**；W1 `auto_infer=false`）

### 5.1 输入信号（V1 无 LLM）

| 信号 | 说明 |
|------|------|
| `n` | 可导入图片张数 |
| `burst_density` | 短时窗近邻占比或 burst 组覆盖率 |
| `tech_fail_rate` | 抽样：严重模糊/曝光失败占比 |
| `path_hints` | 「精选」「featured」「导出」等 → 偏 `curated`（**仅 mid confidence**） |
| `aesthetic_spread` | P1；V1 可不依赖 |

V1 推断优先 **n + path_hints + 轻量抽样**；重信号勿在全量质量分前假装高精度。

### 5.2 启发式（数值化）

```text
signals_ok = count(defined(n, burst_density, tech_fail_rate))

if signals_ok < 2:
    → typical (auto_fallback)

if path_hints_curated and n <= curated_max_n
   and burst <= burst_density_low and tech <= tech_fail_rate_low:
    → curated (confidence mid)          # 单独 path 不得 high
elif n >= messy_min_n and n >= forbid_auto_messy_below_n
     and (burst >= burst_density_high or tech >= tech_fail_rate_high):
    → messy                             # 仅张数不够；生效仍须 T1
elif n <= curated_max_n and burst <= low and tech <= low:
    → curated (confidence mid)
else:
    → typical
```

**禁止**：仅 `n ≥ 150` 推 messy；置信不足进 messy；覆盖 `source=user`。

### 5.3 输出

```json
{
  "ingestQualityMode": "typical",
  "ingestQualityModeSource": "auto",
  "ingestQualityInfer": {
    "suggested": "typical",
    "confidence": 0.62,
    "signals": { "n": 87, "burstDensity": 0.21, "techFailRate": 0.08 }
  }
}
```

生效 mode+source **只写 intent**；infer 可挂 curation 供「恢复推荐」。

---

## 6. 数据模型与管线接线

### 6.1 Intent / trip 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `intent.ingestQualityMode` | enum | 权威枚举 |
| `intent.ingestQualityModeSource` | enum | `user` \| `auto` \| `auto_fallback` |
| `intent.keepNearDuplicates` | bool | typical 进阶（← `keep_bursts`） |
| `curation.ingestQualityInfer` | object | 探针建议（非生效源） |
| `cullSummary.qualityMode` | string | 实际生效 |

兼容双写（**仅 BE adapter 一次**）：`photoCullEnabled` / `photoKeepMode` / `keepNearDuplicates` 由 resolver 强制写出；**禁止 FE 再推**。

### 6.2 `resolve_ingest_quality_policy`（**D-IQR-11**）

```text
resolve_ingest_quality_policy(trip, cfg) → {
  mode, source,
  skip_cull, skip_low_res,
  keep_near_dupes,
  cull_overlay,          # keep_ratio_floor / score_topk_ratio / burst_keep / …
  messy_confirm_required
}
```

```text
if not quality_routing.enabled:
    → 现网 F3 派生（photoKeepMode / photoCullEnabled）
else:
    → intent.ingestQualityMode（含 W1 默认 typical）
```

`config.cull.enabled=false` 全局总闸仍优先 → 接近 skip cull。

增量 ingest：默认沿用 trip intent；仅请求显式带 mode 才更新。

### 6.3 管线钩子

| 阶段 | 行为 |
|------|------|
| Import Sheet 提交 | 若 messy → **先 T1**；通过后写入 mode + 派发 |
| ingest finalize | resolver → cull profile / skip |
| re-curate | 同一 resolver；`curated` 不 recull |
| FirstSuccess | 模式文案；勿暗示未使用的强精简 |

---

## 7. 验收

### 7.1 功能

| ID | 验收项 | 级别 |
|----|--------|------|
| **AC-IQR-01** | 三模式可选；提交字段正确；主路径无双三选一 | A |
| **AC-IQR-02** | 不改选项 → W1=`typical`；W2 推荐（messy 须 T1） | A |
| **AC-IQR-03** | `curated` 不跑质量 cull、跳低清硬丢；进度无「挑选」；M≤N 诚实 | A |
| **AC-IQR-04** | 同 fixture：`keep(messy) < keep(typical) ≤ keep(curated)`；messy eligible/N ∈ 配置容差 | A |
| **AC-IQR-05** | typical eligible/N ∈ **[0.85, 0.95]**（G-typical）；硬废仍去；Pass C 仍 layoutEligible | A |
| **AC-IQR-06** | messy T1 可改 typical / 确认 / 返回；M/N 误差 ≤15% | A |
| **AC-IQR-07** | `enabled=false` ≡ 现网 F3 向导行为 | A |
| **AC-IQR-08** | ★（featured）messy 下全保留；不进垫底分母 | A |
| **AC-IQR-09** | 过少门 T1b 可测 | B |
| **AC-IQR-FE** | Modal a11y / 埋点 / 窄屏 | B |

### 7.2 狗粮

| 夹 | 规模 | 过线 |
|----|------|------|
| **G-curated** | 人精选 30–50 | vs 现网 `keep_all`：张数差 ≤2；无「挑选」文案 |
| **G-typical** | 80–120 一般册 | eligible/N ∈ [0.85, 0.95]；章节可读 |
| **G-messy** | 200+ 乱册 | vs typical：eligible/N ≤ 0.55×；T1 后成册；★ 夹具全在 |

### 7.3 发布门（`enabled=true` 前）

1. 三模式狗粮对照通过。  
2. `typical` 相对现网默认 cull **故事厚度不劣**。  
3. FTUE「零点击改模式」路径：**不**新增必过 Modal（除用户显式选 messy）。  
4. `enabled=false` 回退 AC-IQR-07 回归。  
5. W1 合码前已拆 ACCEPTANCE + IMPLEMENTATION。

### 7.4 单测最小集（BE-IQR-05）

UT-01 curated 不调 Pass1–3 · UT-02 typical 连拍最多 2 · UT-03 soft_demote 仍 layoutEligible · UT-04 messy top% 且 floor 不拉回 · UT-05 ★ 豁免 · UT-06 模式序 · UT-07 推断（W2）· UT-08 过少 WARN。

---

## 8. 里程碑与任务拆分

| 阶段 | 内容 | 预估 |
|------|------|------|
| **W0** | 字段 + `enabled=false` 骨架；静态三卡**不**与 F3 双挂 | 2–3d |
| **W1** | 合并矩阵落地；cull profile overlay；文案；T1；迁移；AC-01～03/05/07 | 5–7d |
| **W2** | 自动推断 + 推荐徽标；仍受 D-IQR-12；狗粮调参 | 3–5d |
| **W3** | 三模式狗粮；发布门评估 `enabled=true` | 3–4d |
| **P1** | 预览改策略；messy shortlist；probe | 另估 |

### 8.1 后端 / 算法任务

| ID | 任务 |
|----|------|
| **BE-IQR-01** | intent/schema/`apply_intent` + F3 兼容 adapter |
| **BE-IQR-02** | `resolve_ingest_quality_policy` + cull overlay（含 floor=0） |
| **BE-IQR-03** | 推断函数 + 配置阈值（W2） |
| **BE-IQR-04** | messy M/N 预估（干跑或公式） |
| **BE-IQR-05** | 单测 §7.4 |
| **BE-IQR-06** | `min_layout_eligible` WARN + `suggestMode=typical` |

前端见 **§4.6**。

---

## 9. 风险、叙事红线与故意不做

| 风险 | 缓解 |
|------|------|
| 双三选一认知爆炸 | D-IQR-07 方案 A；FE-IQR-03/14 |
| 自动 messy 伤 FTUE | D-IQR-12；W1 关推断 |
| curated 误点 | FE-IQR-22；代价副文案 |
| messy 砍不动 | `keep_ratio_floor=0` |
| 与精选夹/HIT 混淆 | §0.2 |
| 后悔成本高 | 文案勿假装能轻松改；P1 T2 |

**叙事红线（冻结）**：

1. `curated` 禁「全部进排版」绝对句。  
2. 禁把 IQR 说成「更懂审美 / 更会挑封面」。  
3. 禁「普通相册≈放弃质量」「杂乱=懒用户」。  
4. 禁将「已是精选」模式与「精选文件夹上传」混为同一卖点。  
5. 推荐文案只说「按文件夹情况建议」，不说「已保证成片」。

故意不做：V1 情绪 LLM；V1 完整捡回台；与品类选择器混排；W1 自动推断。

---

## 附录 A · 与 P9-F1 / P9-F3 迁移

| 旧 | 新（IQR） |
|----|-----------|
| `#v2-photo-cull-enabled` 勾选 | → `typical`（兼容路径**勿**因张数静默升 messy） |
| 取消勾选 | → `curated` |
| `photoKeepMode=recommended` | → `typical` |
| `photoKeepMode=keep_all` | → `curated` |
| `photoKeepMode=keep_bursts` | → `typical` + `keepNearDuplicates=true`（进阶） |
| （无） | → `messy`（仅新路径） |

旧 trip 仅有 `photoCullEnabled`：

- `false` → `curated` + `source=user`（兼容）
- `true` / 缺省 → `typical` + `source=auto_fallback`

`enabled=false`：UI 与行为回退 **当前 F3 三档**，不是虚构的「仅 F1 勾选」。

---

## 附录 B · 对外文案定稿候选

| 场景 | 文案 |
|------|------|
| 区标题 | 这批照片希望怎么处理？ |
| 推荐提示 | 已根据文件夹情况选好推荐项，可直接开始 |
| 不确定 | 不确定就用推荐项（普通相册） |
| curated 成功 | 已按精选尽量保留，开始排版 · M 张 |
| typical 成功 | 已整理明显废片与重复，保留旅行故事 |
| messy 成功 | 已强力精简；若不够好，可换「普通相册」或「已是精选」后重做 |
| messy 门 | 约 N 张里预计留下约 M 张。优先去模糊与连拍；★ 尽量保留。想多留请改用普通相册 |
| 过少门 | 精简后照片可能过少，建议改用普通相册 |

---

## 附录 C · 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-07-29 | 初稿：三模式；FE；不选→推荐；messy 门；按 F1 二元迁移 |
| v0.2.0 | 2026-07-29 | 消化评审 BLK：方案 A 合并 `photoKeepMode`；T0 预确认；Pass C 软/硬与 floor=0；阈值表；FE-13～22；W1 砍推断；边界表与发布门；附录 A 重写 F3 |
