# Travelogue · 高光池竖版布局 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | **v0.1.2-HPPL** |
| **状态** | **Draft · 产品方向已对齐 · 待评审冻结** |
| **DOC-STATUS** | **active** |
| **主题代号** | 「高光池竖版优先拼图」— **HPPL**（Highlight Pool Portrait Layout） |
| **触发来源** | 产品讨论（2026-08-10）：高光池竖版全员 solo 导致峰值稀释与节奏闷感；同意「签名强制 solo + 次要竖版 3→2→1」 |
| **前置条件** | [PRD-PHASE23-peak-moment.md](./PRD-PHASE23-peak-moment.md) P23.1 已交付（`pool_solo` / `pool_exif` / 签名角标）；正文竖游程 `_tile_portrait_run`（triple-first）可用 |
| **关联文档** | [P23 最佳时刻](./PRD-PHASE23-peak-moment.md) · [HGM 高光轻布展](./PRD-HIGHLIGHT-GALLERY-MOUNT-V1.md) · [P2VF 双竖变体](./PRD-PORTRAIT-2-VARIANT-FAMILY-V1.md) · [RENDER-CONTRACT §4c](./RENDER-CONTRACT.md) · [LAYOUT-PLANNER](./LAYOUT-PLANNER.md) |
| **修订对象** | P23.1「池内全部拆 solo」对 **次要高光竖版** 的展示合同；**不**改选型公式 / 池大小 / 签名唯一性 |
| **更新日期** | 2026-08-10 |

> **定位**
>
> P23.1 默认把高光池内**每一张**拆成独立单槽屏（`pool_solo: true`），语义是「展柜峰值 + EXIF」。  
> 池内竖版一多时，长卷会出现一串大竖图停顿：峰值被稀释，节奏闷，且与正文已成熟的竖拼语法（3→2→1）割裂。
>
> 本 PRD **不取消**高光稀缺感，而是把池内展示拆成两层：
>
> 1. **签名时刻**（`momentAssetId` / `data-role="moment"`）→ **继续强制 solo**（角标 + EXIF）。  
> 2. **次要高光竖版**（`momentSecondaryIds` 中的竖/tall）→ **优先拼图**：3 张并列最优 → 2 张并列 → 孤张 solo 兜底。  
> 3. **次要高光横版** → V1 **仍 solo**（不与竖拼混谈；另案）。
>
> **一句话目标**：**签名仍是全书唯一定格；次要竖版用克制拼图减轻闷感，而不是张张占一整屏。**

> **完成定义**
>
> | 门 | 含义 | 不等于 |
> |----|------|--------|
> | **M0 Go** | 本 PRD 决策表冻结；HGM「厅内独屏必须」合同显式修订 | 改默认 curate |
> | **M1 Go** | 配置开关可回退；签名仍 solo；次要竖版可出 3/2/1 | 默认已开，关则回退 |
> | **M2 Go** | 代表 trip 盲评通过或归档；必要时再收默认 | 改选型分 / 池大小 |
> | **M3 Go**（可选） | 横版次高峰规则 / 拼屏 EXIF 增强另开 | 本文件直接扩范围 |

---

## 0. 读者指南与边界

### 0.1 与相邻主题

| 主题 | 关系 | 本主题做什么 |
|------|------|--------------|
| [P23 最佳时刻](./PRD-PHASE23-peak-moment.md) | **选型与角色合同上游** | 选型 / 池大小 / 签名唯一 **不动**；只改「次要竖版如何成屏」 |
| [HGM 高光轻布展](./PRD-HIGHLIGHT-GALLERY-MOUNT-V1.md) | **呈现层合同** | 为厅内高光（B）增加「竖拼屏」例外；签名（A）独屏不变 |
| [P2VF](./PRD-PORTRAIT-2-VARIANT-FAMILY-V1.md) | **2P 变体家族** | V1 池内双竖默认用基线 `screen-portrait-2`；是否启用 gallery/asym **另议**（OQ） |
| 正文 `_tile_portrait_run` | **可复用算法** | 复用 3→2→1 优先级；**不**把池内图交回普通正文游程混排 |
| longshot / 导出拼贴 | **正交** | 本 PRD 只管阅读面 `screens[]`；导出 Card 管线不改 |

### 0.2 代码事实（2026-08-10 · 不可重议）

| ID | 事实 |
|----|------|
| **F-01** | 默认 `curate.moment.pool_solo: true`：池内全员经 `ensure_pool_assets_solo_screens()` 拆为单槽屏 |
| **F-02** | 签名 → `data-role="moment"` + 角标；次高峰 → `data-role="peak"`；竖 → `screen-portrait-1`，横 → `screen-landscape-1` |
| **F-03** | 插入点约章内 **60%–70%** 屏位（实现 `_pick_pool_insert_index` ≈ `int(n * 0.7)`） |
| **F-04** | 正文竖游程已是 **triple-first**：`screen-portrait-3` → `screen-portrait-2` → `screen-portrait-1`（`_tile_portrait_run`） |
| **F-05** | 节奏：`max_portrait_pair_streak`（R-06）等约束作用于正文 pattern 族；池后处理当前绕开该拼图路径 |
| **F-06** | `pool_solo: false` 时仅签名强制 solo；次高峰可留在正文并走 `secondary_boost`——**不是**本 PRD 要复活的路径 |
| **F-07** | HGM §6.1 写明厅内高光 **V1 独屏必须**（「高光不进组图拼贴主槽」）——本 PRD 须显式修订该合同，否则实现与文档打架 |
| **F-08** | 池大小仍 `clamp(round(n×5%), 1, 5)`；全书次高峰数量极少，拼图供给天然稀缺 |

### 0.3 用户可感知问题 → 落点

| ID | 问题 | 严重度 | 落点 |
|----|------|--------|------|
| **Q1** | 池内多张竖版各自占一整屏，翻页闷、峰值稀释 | **P0** | §4 次要竖版 3→2→1 |
| **Q2** | 签名若进拼图，丢失「全书唯一定格」 | **P0** | D-HPPL-01 签名强制 solo |
| **Q3** | 硬凑 3 张气质不合，像普通宫格不像高光 | **P0** | §4.2 可拼门 |
| **Q4** | 多槽屏每格挂 EXIF 拥挤、像说明书 | **P1** | D-HPPL-05 EXIF 降级 |
| **Q5** | 高光拼屏与正文竖拼连成一片 | **P1** | §4.4 节奏护栏 |
| **Q6** | 静默改 `pool_solo` 语义导致回归难测 | **P0** | 新开关 + 默认灰度 |

---

## 1. 背景与问题

### 1.1 现状摘要

```text
build_moment_pool → pick signature
  → ensure_pool_assets_solo_screens（pool_solo=true）
      池内每张（含竖版）→ 独立 screen-portrait-1 / screen-landscape-1
      role = moment | peak · 可选 EXIF 黑条
      插入各章中后段
```

正文竖图同时走：

```text
竖游程 → _tile_portrait_run：优先 3 → 余 2 → 余 1
```

两套路径对「竖版如何成屏」结论相反；池后处理**覆盖**正文拼版。

### 1.2 问题陈述

| ID | 问题 | 影响 |
|----|------|------|
| **HPPL-P-01** | 池级 `pool_solo` 不区分签名 / 次高峰、不区分横竖 | 次要竖版无法享受已验证的竖拼语法 |
| **HPPL-P-02** | 多张竖版 peak 连续 solo | 阅读停顿过密；「展柜」变成「竖图连廊」 |
| **HPPL-P-03** | HGM 合同写死厅内独屏 | 若不修订，拼图实现无法合入呈现层叙事 |
| **HPPL-P-04** | 拼屏 EXIF / 角标语义未定义 | 直接复用每槽 EXIF 会破坏版式 |

### 1.3 核心判断

- **签名**承担「就是这一张」→ 必须独屏。  
- **次要竖版**承担「这一段里的好画面群」→ 允许克制并排，仍带 `peak` 角色，但不再张张独占舞台。  
- **可拼优先于凑数**：凑不齐合格组时，降级 2 或 1，绝不跨章硬拼。  
- **配置显式**：不 silently 重解释 `pool_solo`；新增开关表达「次要竖版可拼」。

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 | 验收口径 |
|----|------|----------|
| **G-HPPL-01** | 签名时刻始终独屏 | 任意开关组合下，`momentAssetId` 所在屏槽数 = 1，`data-role="moment"` |
| **G-HPPL-02** | 次要竖版优先 3→2→1 | 同章可拼集合 ≥3 → 优先 `screen-portrait-3`；余 2 → `screen-portrait-2`；余 1 → `screen-portrait-1` |
| **G-HPPL-03** | 不可拼则兜底 solo | 可拼门失败时行为与今日 peak solo 一致（可保留 EXIF） |
| **G-HPPL-04** | 横版次高峰 V1 不变 | 次要横版仍 `screen-landscape-1` solo |
| **G-HPPL-05** | 拼屏 EXIF 克制 | 多槽 peak 屏默认**不**每槽挂 `.moment-exif-bar`；签名 EXIF 合同不变 |
| **G-HPPL-06** | 节奏不塌 | 高光角色屏（moment/peak）不得连续；池内竖拼计入竖朝向/双竖 streak 护栏 |
| **G-HPPL-07** | 可回退 | `curate.moment.pool_portrait_collage`（名见 §5）**默认 true**；关则回退 P23.1 全员 solo |
| **G-HPPL-08** | HGM 合同同步 | 厅内「独屏必须」改为「签名必须独屏；次要竖版允许 2/3 拼」 |

### 2.2 非目标

- **不改** `peak_moment_score` / 池大小公式 / 入池门槛 / 美食禁入等选型规则  
- **不改** 签名角标文案与唯一性（全书 ≤1 个 `data-role="moment"`）  
- **不做** 次要横版拼图、竖+横混排进高光池（另案）  
- **不做** 把次高峰重新丢回正文 mosaic 主槽竞选（仍由高光后处理成屏）  
- **不做** 池内启用 dense 4/6/9 竖宫（仅 3 / 2 / 1）  
- **不要求** V1 启用 P2VF 的 gallery/asymmetric 变体（可选后续）  
- **不改** longshot「不含 moment 屏」等导出合同  
- **不**将 `pool_solo: false` 的旧 hero 加权路径作为本需求主方案

---

## 3. 已拍板决策（2026-08-10 · 产品讨论）

| ID | 决策 | 说明 |
|----|------|------|
| **D-HPPL-01** | **签名强制 solo** | `momentAssetId` 永远单槽；可带角标 + EXIF；**禁止**进 2/3 拼 |
| **D-HPPL-02** | **仅次要竖版可拼** | 适用范围 = `momentSecondaryIds` ∩ 朝向 ∈ {portrait, tall} |
| **D-HPPL-03** | **优先级 3 → 2 → 1** | 与正文 `_tile_portrait_run` 一致：triple-first；余 2 双拼；余 1 solo |
| **D-HPPL-04** | **可拼门：同章优先** | V1 硬约束：**同一 chapter**；时间邻近为软分（见 §4.2）；**禁止跨章拼** |
| **D-HPPL-05** | **拼屏 EXIF 默认关** | 多槽 `peak` 屏不挂每槽 EXIF；solo peak / 签名仍遵循既有 `pool_exif` |
| **D-HPPL-06** | **角色保留 peak** | 拼屏整屏（或每槽）`data-role="peak"`；**无**「决定性瞬间」角标 |
| **D-HPPL-07** | **新开关，不重写 pool_solo** | `pool_solo` 仍表示「池资产离开正文多槽宿主」；竖拼是 solo 管线内的**组屏策略** |
| **D-HPPL-08** | **默认开启，可配置关闭** | `pool_portrait_collage` 默认 `true`；关则回退 P23.1 全员 solo（产品 2026-08-10 修订） |
| **D-HPPL-09** | **pattern 集收窄** | 仅 `screen-portrait-3`（及已有 editorial 等价若准入）、`screen-portrait-2`、`screen-portrait-1`；不用 4/6/9 grid |
| **D-HPPL-10** | **HGM 合同修订** | 签名仍「独屏必须」；厅内高光改为「允许次要竖版 2/3 拼；禁止进非高光 mosaic 主槽」 |

---

## 4. 方案规格

### 4.1 处理管线（概念）

在 `pool_solo: true` 且 `pool_portrait_collage: true` 时：

```text
1. 抽出签名 → 强制 solo（moment）· 插入规则同现网
2. 其余池成员按章分组
3. 章内：横版次高峰 → 仍逐张 solo（landscape-1）
4. 章内：竖版次高峰 → 跑可拼门 → 按 3→2→1 切段成屏（peak）
5. 各 peak/moment 屏插入章中后段；满足「高光屏不相邻」
6. 原多槽宿主剩余槽归一化（复用现网拆槽逻辑）
```

`pool_portrait_collage: false` → 行为与今日 P23.1 完全一致（全员 solo）。

### 4.2 可拼门（V1）

对章内次要竖版候选集合 `P`：

| 门 | 级别 | 规则 |
|----|------|------|
| **同章** | 硬 | 只与同 `chapterId` 的次要竖版组合 |
| **供给** | 硬 | `\|P\| ≥ 3` 才允许 emit triple；`\|P\| ≥ 2` 才允许 pair；否则 solo |
| **时间邻近** | 软 | 优先 `takenAt` 间距更小的组合；无时间戳则保持池序 |
| **人物门** | 软（V1） | 若组内存在人脸主导帧，**优先**仍可 3/2 拼（高光池已是精选）；若后续狗粮显示脸裁严重，再收紧为「含人仅 pair/fill」（OQ） |
| **跨章** | 禁止 | 不得为凑 3 张跨章借图 |
| **与签名** | 禁止 | 签名资产不得进入任何 peak 拼屏 |

切段算法（与正文对齐的意图，非要求行级复用同一函数）：

| 余量 n | 切法 |
|--------|------|
| 1 | `[1]` |
| 2 | `[2]` |
| 3 | `[3]` |
| 4 | `[3,1]` |
| 5 | `[3,2]` |
| ≥6 | 尽量多段 `[3,…]`，余 2→pair，余 1→solo |

> 注：池上限 5，章内次要竖版通常 ≤4；上表主要为合同完整。

### 4.3 Pattern 与渲染

| 组大小 | patternId（V1） | 角色 | EXIF |
|--------|-----------------|------|------|
| 3 | `screen-portrait-3`（若 editorial 变体在活跃集且通过准入，允许等价替换） | `peak` | 默认无每槽 EXIF |
| 2 | `screen-portrait-2`（V1 不用 P2VF 变体，除非 OQ 打开） | `peak` | 默认无每槽 EXIF |
| 1 | `screen-portrait-1` | `peak` | 遵循 `pool_exif`（与现网 solo peak 相同） |

签名：

| 朝向 | patternId | 角色 | EXIF |
|------|-----------|------|------|
| 竖/方 | `screen-portrait-1` | `moment` | 遵循 `pool_exif` / `signature_label` |
| 横 | `screen-landscape-1` | `moment` | 同上 |

### 4.4 节奏与插入

| 规则 | 要求 |
|------|------|
| **插入带** | 仍落在章内中后段（约 60%–70%）；多屏时在带内分散，避免叠在同一 index |
| **高光不相邻** | 任意两屏若均含 `moment`/`peak` 角色，中间至少隔 1 屏非高光（与 HGM「禁止连续展室态」对齐） |
| **竖拼 streak** | 池内 emit 的 `screen-portrait-2` 计入 R-06 家族 streak；若插入点会导致超过 `max_portrait_pair_streak`，**降级**为拆成两个 solo 或推迟插入点（正确性：宁可多 solo，不为躲 streak 跨章拼） |
| **与正文竖拼** | 若插入点上一屏已是正文 `portrait-2/3`，优先换插入点或对本组改用更少张数切分，避免「竖拼墙」 |

### 4.5 对 HGM 合同的修订（须同步改 HGM 文档）

原（HGM §6.1）：

| 变量 | 签名（A） | 厅内高光（B） |
|------|-----------|---------------|
| V1 独屏 | 必须 | 必须 |

修订为：

| 变量 | 签名（A） | 厅内高光（B） |
|------|-----------|---------------|
| V1 舞台 | **必须独屏** | **默认独屏**；当 HPPL 开启且为次要**竖版**时，允许 `screen-portrait-2/3` 整屏作为厅内高光舞台 |
| 禁区 | — | 仍禁止进入**非高光** mosaic/组图主槽；禁止签名与次高峰混槽 |

布展变量 V2–V5：拼屏厅内高光取 **弱气口**；题签默认无；EXIF 按 D-HPPL-05。

### 4.6 `pool_solo` 语义澄清（实现合同）

| 开关 | 含义（修订后） |
|------|----------------|
| `pool_solo: true` | 池资产**不得**留在普通正文多槽宿主里「顺便露出」；必须由高光管线成屏 |
| `pool_portrait_collage: true` | 在上一行成立的前提下，次要竖版可由高光管线 **组屏**（2/3），而非张张单槽 |
| `pool_solo: false` | 旧行为保留：仅签名 solo；次高峰可不拆，走 hero 加权——**本 PRD 不推广为默认** |

---

## 5. 配置合同

YAML 前缀：`curate.moment.*`  
落地：`travelogue/config/moment.py` → `MomentConfig`

| 键 | 类型 | 默认 | 说明 |
|----|------|------|------|
| `pool_portrait_collage` | bool | `true` | 总开关：次要竖版 3→2→1 |
| `pool_portrait_collage_max_per_screen` | int | `3` | 上限；V1 只允许 2 或 3（实现可 clamp） |
| `pool_portrait_collage_exif` | bool | `false` | 多槽 peak 是否挂 EXIF；V1 默认 false |

既有键交互：

| 既有键 | 交互 |
|--------|------|
| `enabled: false` | 整池关闭 → 本功能无操作对象 |
| `pool_solo: false` | **本功能不生效**（避免与旧 secondary_boost 路径纠缠）；日志/诊断可记 skip |
| `pool_exif` | 仅约束签名与 **solo** peak；多槽 peak 看 `pool_portrait_collage_exif` |
| 小册 auto-disable | 不写池 → 本功能自然空转 |

示例：

```yaml
curate:
  moment:
    enabled: true
    pool_solo: true
    pool_exif: true
    pool_portrait_collage: true           # 默认开；false 回退 P23.1 全员 solo
    pool_portrait_collage_exif: false
    pool_portrait_collage_max_per_screen: 3
```

---

## 6. 实现要点（非绑定 API 名，供排期）

| 项 | 建议落点 |
|----|----------|
| 配置 | `MomentConfig` + `moment_config_from_dict` + `config.yaml` 注释样例 |
| 组屏 | `travelogue/curation/moment_scoring.py`：扩展 `ensure_pool_assets_solo_screens` 或抽 `ensure_pool_assets_screens`；签名路径不变 |
| 切段 | 复用 `_tile_portrait_run` 的切段意图（可抽纯函数 `tile_portrait_counts(n)`），**不要**把池图重新喂回章节正文 planner |
| 渲染保险 | `travelogue/render/chapters.py` 现有「渲染前再 ensure pool solo」需同步认识拼屏，避免又拆回单槽 |
| 契约文档 | `RENDER-CONTRACT.md` §4c 增补「peak 多槽例外」；HGM §6.1 表修订 |
| 单测 | 签名永不进拼；同章 3 竖 → 一屏 3；跨章不拼；开关 OFF 黄金一致；相邻高光插入避让 |

---

## 7. 里程碑

| 里程碑 | 内容 | 出口 |
|--------|------|------|
| **M0** | 评审冻结 D-HPPL-*；同步改 HGM / RENDER-CONTRACT 表述 | 可开工 |
| **M1** | 开关 + 组屏实现 + 单测；默认 ON（可关回退） | 可狗粮 / 可回退 |
| **M2** | 2–3 本代表册盲评（闷感 / 是否仍像高光 / 有无硬凑） | 默认策略拍板 |
| **M3**（可选） | 横版次高峰、P2VF 变体、拼屏 EXIF 增强 | 另开 PRD 或本文件 v0.2 |

---

## 8. 验收（AC）

| ID | 断言 |
|----|------|
| **AC-HPPL-01** | `pool_portrait_collage: false` → 与 P23.1 现网 screens 指纹一致（同 fixture） |
| **AC-HPPL-02** | 签名在任意情况下槽数 = 1，且不出现在任何 `screen-portrait-2/3` |
| **AC-HPPL-03** | 同章 3 张次要竖版 + 开关 ON → 至少一屏 `screen-portrait-3`（或准入的 editorial 等价），三槽均为 peak 池成员 |
| **AC-HPPL-04** | 同章仅 2 张次要竖版 → `screen-portrait-2`；仅 1 张 → `screen-portrait-1` |
| **AC-HPPL-05** | 两章各 2 张次要竖版 → **不得**拼成跨章 3/4；各章独立 2 或 1 |
| **AC-HPPL-06** | 次要横版不因本开关改变 pattern（仍 landscape-1 solo） |
| **AC-HPPL-07** | 多槽 peak 默认无 `.moment-exif-bar`；签名 / solo peak 在 `pool_exif: true` 时仍可有 |
| **AC-HPPL-08** | 不出现连续两屏均为 moment/peak 角色 |
| **AC-HPPL-09** | `pool_solo: false` 时本开关不生效（跳过组屏） |
| **AC-HPPL-10** | 盲评否决门：系统性地把高光读成「普通三竖宫格 / 缺图留白 / 签名被挤进拼图」→ No-Go |

---

## 9. 开放问题（OQ）

| ID | 问题 | 倾向 | 阻塞？ |
|----|------|------|--------|
| **OQ-HPPL-01** | 池内双竖是否启用 P2VF gallery/asym | V1 仅 fill `screen-portrait-2` | 否 |
| **OQ-HPPL-02** | 含人脸的次要竖版是否限制仅 pair/solo | V1 先不限制；狗粮后收紧 | 否 |
| **OQ-HPPL-03** | `screen-portrait-3-editorial` 是否与 fill 轮换 | 跟随正文活跃集；无则只用 fill 3 | 否 |
| **OQ-HPPL-04** | 拼屏是否允许整屏一条弱 EXIF（非每槽） | V1 不做；`pool_portrait_collage_exif` 预留 | 否 |
| **OQ-HPPL-05** | 若盲评否决是否改回默认 `false` | 保持开关；默认以产品最新拍板为准 | 否 |
| **OQ-HPPL-06** | 次要横版是否未来做双横拼 | 另案；本 PRD 明确不做 | 否 |

---

## 10. 风险与回滚

| 风险 | 缓解 |
|------|------|
| 拼屏削弱「展柜感」 | 签名仍 solo；拼屏无角标；可关 `pool_portrait_collage` 回退 + 盲评 |
| 与 HGM 文档不一致 | M0 同步改 HGM §6.1 |
| 渲染前 ensure 再次拆拼屏 | AC + chapters 路径联测 |
| streak 降级导致又变回全 solo | 可接受；指标上记录 collage_emit / collage_fallback 计数 |

回滚：配置关 `pool_portrait_collage` 即回到 P23.1；无需迁数据。

---

## 11. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-08-10 | 初稿：签名强制 solo；次要竖版 3→2→1；可拼门同章；拼屏 EXIF 默认关；新开关默认 false；HGM 独屏合同修订要点 |
| v0.1.1 | 2026-08-10 | **D-HPPL-08 修订**：`pool_portrait_collage` **默认 true**（产品确认可默认打开；关则回退 P23.1） |
| v0.1.2 | 2026-08-10 | 补全：HGM/P23 交叉引用、R-06/竖拼墙降级、pool_solo 门闫、AC-06~09 单测、config.yaml.example |
