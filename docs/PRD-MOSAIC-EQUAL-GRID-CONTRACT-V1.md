# Travelogue · 等权拼图几何合同 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.2.0** |
| **状态** | **Conditional Go · 可 Kickoff M0 / M1（PR-A CSS）**（[七席](./acceptance-records/megc-equal-grid-contract-v1-review-2026-07-31.md) · M2 待 BLK · M3 延期） |
| **DOC-STATUS** | **active** |
| **主题代号** | 「等权拼图几何合同 V1」— **MEGC**（Mosaic Equal-Grid Contract） |
| **调研来源** | 2026-07-30 · `demo-2019` `ch-02-sc-06`（`screen-landscape-4`）实机：3:2 人像横图进 16:9 等权四宫「高度不够」；DOM 证实上下行等高，根因非「上排挤下排」；叠加右上 `contain` 触发 CSS `height:auto` 使网格高于舞台、`overflow:hidden` 裁掉下排约 152px |
| **审查基线** | [MSA](./PRD-MOSAIC-SLOT-ADAPTATION-V1.md) v0.2.0（拓扑固定·轨道可变）· [MTSO](./PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) · LTE 等权 YAML · `journal-screens.css` contain→auto 规则 |
| **关联文档** | [MSA](./PRD-MOSAIC-SLOT-ADAPTATION-V1.md) · [MTSO](./PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) · [P16 LTE](./PRD-PHASE16-layout-template-engine.md) · [MGQ](./PRD-MCS-GEOMETRIC-QUALITY-V1.md) · [TPC](./PRD-TEMPLATE-CONTRACT-V1.md) · [P21](./PRD-PHASE21-mosaic-density-budget.md) |
| **评审纪要** | [acceptance-records/megc-equal-grid-contract-v1-review-2026-07-31.md](./acceptance-records/megc-equal-grid-contract-v1-review-2026-07-31.md)（结案）· [模板](./acceptance-records/megc-equal-grid-contract-v1-review-TEMPLATE.md) |
| **验收** | [ACCEPTANCE-MOSAIC-EQUAL-GRID-CONTRACT-V1.md](./ACCEPTANCE-MOSAIC-EQUAL-GRID-CONTRACT-V1.md) |
| **实施** | [IMPLEMENTATION-MOSAIC-EQUAL-GRID-CONTRACT-V1.md](./IMPLEMENTATION-MOSAIC-EQUAL-GRID-CONTRACT-V1.md) |
| **更新日期** | 2026-07-31 |

> **v0.2.0 相对 v0.1.0（七席回写 · 2026-07-31）**
>
> 1. **Conditional Go**：可 Kickoff M0；可 Kickoff M1（CSS，O-05 允许先于父开关）；M2 挡 BLK-03/07；**M3 默认延期**。  
> 2. **O-01 锁定 soft_penalty**；硬拒仅配置开关。  
> 3. **D-06 收紧**：混向等权非电影峰 → **硬拒**（不再「加倍或硬拒」二选一）。  
> 4. **D-04/05（P-释/P-函）**：保留合同、默认 off、**不强制排期**。  
> 5. **新增 D-11**：M1–M2 主责 web 16:9；mobile 不阻塞 PR-A。  
> 6. **新增 F-10～F-12**：CSS 注释与规则矛盾 · trips CSS 拷贝 · 混向 fit:auto。  
> 7. **BLK-02/06**：CSS 纳入/排除名单签字 + templates→trips 同步，为 M1 合码门。

> **定位**
>
> [MSA](./PRD-MOSAIC-SLOT-ADAPTATION-V1.md) 解决 **加权拓扑**（有主有辅）下「轨道贴窗峰」。  
> 但 **等权平铺**（`landscape-4` 等）在数学上 **无法** 用 `trackOverride` 改变槽 AR——等面积约束下每格 AR 恒等于舞台 AR。  
> 本 PRD 补齐这条空洞：**渲染舞台合同 + 等权选型闸 + 等权释舞台例外**，并与 MSA contain 策略对齐，禁止 contain 撑破固定舞台。

> **一句话目标**：**等权格不再假装能被调轨救活；非 16:9 峰别进等权扁槽；固定舞台上 contain 只做格内信箱；加权扁槽继续交给 MSA。**

> **完成定义**

| 门 | 含义 | 不等于 |
|----|------|--------|
| **M0 Go** | 决策表锁定 + 与 MSA/MTSO 边界切清 + 模板清单冻结 | 改默认 GA 权重堆 SKU |
| **M1 Go** | CSS 舞台合同修复合码；等权 contain 不再裁下排 | SoftCollage / 舞台全书改 3:2 |
| **M2 Go** | 等权选型闸（P-选）进 MCS/MTSO 路径；非 16:9 峰降权/禁发 | 平行模板库 |
| **M3 Go** | 等权释舞台（P-释）或整页拼图信箱（P-函）落地 + 三分峰狗粮盲评 | 用 MSA 白名单「假装」覆盖等权 |

---

## 0. 读者指南与边界

### 0.1 与相邻主题

| 主题 | 关系 | 本主题做什么 |
|------|------|--------------|
| [MSA](./PRD-MOSAIC-SLOT-ADAPTATION-V1.md) | **互补 · 不替代** | MSA = 加权族轨道自适应；MEGC = 等权死结 + 渲染合同。**禁止**把 `landscape-4` 塞进 MSA `solve_tracks` 装成功 |
| [MTSO](./PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) | **消费方** | MEGC 向选型输出「等权族何时可发」硬闸；不改 lifecycle / experiments 政治 |
| [P16 LTE](./PRD-PHASE16-layout-template-engine.md) | **继承** | YAML 拓扑仍 SSOT；本主题只改合同与实例策略，不新开平行模板库 |
| [P15 MCS](./PRD-PHASE15-photo-mosaic-evolution.md) | **插入点** | 候选打分增加等权峰匹配惩罚 / 硬拒 |
| [MGQ](./PRD-MCS-GEOMETRIC-QUALITY-V1.md) | **复用** | 复用窗级 AR / crop 特征；不另起度量方言 |
| [TPC](./PRD-TEMPLATE-CONTRACT-V1.md) / [P21](./PRD-PHASE21-mosaic-density-budget.md) | **继承** | 不放宽朝向硬门、dense 配额 |

### 0.2 非目标

| ID | 非目标 | 理由 |
|----|--------|------|
| **N-01** | 全书舞台改 3:2 | 与 MSA D-01 / 长图·Web 契约冲突 |
| **N-02** | 为 3:2 / 4:3 各复制一套等权 YAML | 组合爆炸；混峰无法二分 |
| **N-03** | 用 `trackOverride`「修好」等权四宫槽 AR | **数学不可能**（见 §1.2） |
| **N-04** | SoftCollage / GA 搜等权拓扑 | 与 MSA D-11 一致；本主题不破例 |
| **N-05** | 放宽竖进宽槽 | 朝向硬门保持 |
| **N-06** | 把 `portrait-2/3` 改回固定 16:9 | 竖拼本就 intrinsic；勿与本债混修 |
| **N-07** | 默认全页 `contain` | 破坏杂志满幅；仅合法留白路径 |

### 0.3 代码与实机事实（2026-07-30）

| ID | 事实 |
|----|------|
| **F-01** | `displayAspect=(col_frac/row_frac)×stageAR`（`geometry.slot_display_aspect`） |
| **F-02** | `screen-landscape-4`：等权 2×2 · 舞台 16:9 → 四槽 AR **恒为 1.7778** |
| **F-03** | 等面积约束下调 `cols/rows` **无法** 改变全部等权格的 AR（§1.2 证明） |
| **F-04** | `journal-screens.css`：非 mosaic 的 `--2x2/--3x2` 在 `:has(.layout-slot__img--contain)` 时 → `grid-template-rows: auto` + `height: auto` |
| **F-05** | mosaic 族已有「固定舞台 · contain 格内信箱」保护；等权 primitive **未**受同等保护 |
| **F-06** | `demo-2019` `ch-02-sc-06`：四张 native ~3:2；右上 `asset-088` `fit=contain`（`crop_risk=0.92` face_clipped）；舞台 802px、网格 953px、下排可见约 68% |
| **F-07** | MSA M1 白名单 **不含** `screen-landscape-4` / `portrait-2-landscape-2`（正确）；但等权债无替代合同 |
| **F-08** | `screen-landscape-2/3` 虽 YAML 极扁，CSS `--slot-aspect` 跟原片 → **非本债** |
| **F-09** | `screen-landscape-6`（deprecated）等权 3×2 格 AR≈1.185 → 问题方向不同（偏窄），不进本主题主清单 |
| **F-10** | CSS 注释称 landscape-4 cover 2×2「keep stage box」，但通用 `--2x2:has(contain)` 规则仍 `height:auto`（七席 F-10） |
| **F-11** | 多 trip 存在 `journal-screens.css` 拷贝；只改 templates 可能狗粮不可见（七席 F-11） |
| **F-12** | `portrait-2-landscape-2` 竖槽 `fit:auto`、横槽 cover，格 AR 仍全 16:9（七席 F-12） |

### 0.4 用户可感知问题 → 落点

| ID | 问题 | 严重度 | 落点 |
|----|------|--------|------|
| **Q1** | 等权四宫 3:2 人像「高度不够 / 像竖图进横槽」 | **P0** | D-03 · D-04 · S-02 |
| **Q2** | 一格 contain 后整屏下排被切、观感像「上挤下」 | **P0** | D-01 · S-01 |
| **Q3** | MSA 开 contain 后等权屏系统性变差 | **P0** | D-01 · D-02 |
| **Q4** | 混向等权棋盘（2L2P）竖图进 16:9 格 | **P0** | D-03 · D-05 |
| **Q5** | 加权侧轨扁横仍砍高度 | **P1** | 移交 MSA；本主题只列清单与验收钩子 |

---

## 1. 背景与根因

### 1.1 三层问题被混为一谈

```text
① 几何死结：等权格 AR ≡ 舞台 AR（16:9）← 调轨无效
② 渲染回归：contain → auto 行高 → 网格高于舞台 → overflow 裁底
③ 选型错配：landPeak=3:2/4:3 的窗仍高权重进 landscape-4
```

用户口语「上面挤了下面」对应 **② 的观感**；**①** 才是即使无 contain 仍「扁」的主因；**③** 决定债出现频率。

### 1.2 等权死结（证明 · 冻结）

对 \(N\times M\) 等权网格、每格占 1 列×1 行、且要求等面积（列权相等、行权相等）：

\[
r_{\mathrm{cell}}=\frac{1/N}{1/M}\cdot r_{\mathrm{stage}}=\frac{M}{N}\cdot r_{\mathrm{stage}}
\]

当 \(N=M\)（2×2、3×3）且 \(r_{\mathrm{stage}}=16/9\)：

\[
r_{\mathrm{cell}}\equiv 16/9
\]

**推论（D-MEGC-00）**：MSA `trackOverride` **不得**宣称修复等权四宫/九宫槽 AR；验收若用「等权主槽贴 1.50」作为 MSA AC，视为 **假绿**。

### 1.3 同型模板清单（冻结 · M0）

#### A. 等权 · 每格≈16:9（主清单）

| patternId | 状态 | 网格 | 备注 |
|-----------|------|------|------|
| `screen-landscape-4` | **GA** | 2×2 | 本债主战场 |
| `screen-portrait-2-landscape-2` | **GA** | 2×2 | 竖角色亦进 16:9 格 |
| `screen-landscape-9` | deprecated | 3×3 | 若复活须服从本 PRD |
| `screen-mosaic-4-2l2p-weighted` | experimental | 等权 2×2 | 棋盘；竖角色危险 |
| `screen-editorial-4mix` | deprecated | 等权 2×2 | 同上 |

#### B. 固定舞台 · contain CSS 易撑破（渲染主清单）

| 条件 | 受影响 |
|------|--------|
| `gridClass ∈ {--2x2,--3x2}` 且舞台声明 16:9 固定盒 | A 类 + deprecated `landscape-6` |
| `data-pattern^="screen-mosaic-"` | **已保护** · 回归测试必须锁住 |

**排除**：`screen-portrait-2` / `portrait-3` / `portrait-4`（intrinsic 合同）；`screen-landscape-2/3`（CSS-primary strip）。

#### C. 加权扁横辅槽（移交 MSA · 本主题只挂接）

GA 例：`mosaic-5-main-portrait-3land`、`mosaic-5-main-hero-plus-4`、`mosaic-6-main-hero-plus-5`、`portrait-1-landscape-2`。  
experimental 加重例：`mosaic-5-1p4l-portrait-hero`（侧轨 @3.2）、`mosaic-5-2p3l-rail`。

---

## 2. 产品原则

| ID | 原则 |
|----|------|
| **G-01** | 等权与加权分治：等权走 MEGC；加权走 MSA |
| **G-02** | 固定舞台的几何由舞台与轨道决定；**fit 不得改网格外尺寸** |
| **G-03** | 非 16:9 横峰不得「舒服地」落在等权 16:9 格 |
| **G-04** | 宁换模板 / 释舞台 / 整页信箱，不毁主体 cover |
| **G-05** | 可观测：每次等权决策写 raw 日志（§6.5） |
| **G-06** | 默认 fail-closed：新闸默认保守；释舞台默认 off 至盲评 |

---

## 3. 已拍板决策（七席锁定 · v0.2.0）

> 下列决策经 [七席评审](./acceptance-records/megc-equal-grid-contract-v1-review-2026-07-31.md) 锁定。数值可在狗粮内微调，但 **D-00/01/03/06/07** 若推翻需重开评审。

| 决策 | 锁定结论 |
|------|----------|
| **D-MEGC-00 数学边界** | 等权等面积格 AR ≡ 舞台 AR；禁止用 MSA 轨道求解宣称修复；等权贴 1.50 的 AC = **假绿** |
| **D-MEGC-01 舞台合同** | 凡声明固定 16:9（或固定变体）舞台的拼图：`contain` **仅格内** letterbox；网格保持 stretch + 填满舞台；禁止因 contain 撑破后再靠 overflow 裁底 |
| **D-MEGC-02 CSS 作用域** | 修复 `--2x2/--3x2` 等对固定舞台的 `:has(contain)→height:auto`；**不得**误伤 `portrait-2/3/4` 与 `landscape-2/3`；合码前 **BLK-02 名单签字** |
| **D-MEGC-03 等权主路径 = P-选** | 非电影横峰时对 A 类 **强降权（默认 soft）**；仅 `landPeak=sixteen_nine`（或 mixed 且 median≥阈值）时等权 16:9 格为一等公民 |
| **D-MEGC-04 等权例外 = P-释** | 合同保留；默认 **false**；**M3 延期**（七席：先验证 P-选） |
| **D-MEGC-05 P-函** | 合同保留；默认 **false**；与 P-释互斥；**M3 延期** |
| **D-MEGC-06 混向等权** | `portrait-2-landscape-2` / 2L2P：非电影峰 → **硬拒**；禁止竖角色 cover 填 16:9 格；experimental 2L2P **不转 GA** |
| **D-MEGC-07 与 MSA** | 不修改 MSA D-01～D-12；contain 视觉底继承 BLK-06 |
| **D-MEGC-08 与 MTSO** | 选型闸以惩罚/硬拒候选挂接；不塞进 MTSO 转正 KPI |
| **D-MEGC-09 开关** | 父开关 `mosaic.equal_grid_contract.enabled`：**产品默认 true**（[2026-08-03 决策](./acceptance-records/megc-default-on-decision-2026-08-03.md)；七席原稿默认 false 已由转正决议覆盖）；**CSS hotfix（`fix_stage_css`）允许先于父开关合入**（O-05） |
| **D-MEGC-10 失败** | 无替代候选 → 回退次优非等权模板；禁止空屏；打点 `megc_gate_fallback` |
| **D-MEGC-11 变体范围** | M1–M2 **主责 web 16:9**；mobile 9:16 不阻塞 PR-A；若闸启用须按 variant 记日志 |

### 3.1 配置合同（锁定草案）

```yaml
mosaic:
  equal_grid_contract:
    enabled: true                    # 产品默认 on · 2026-08-03 转正
    fix_stage_css: true              # M1：可先于父开关合入（O-05）
    selection_gate:
      enabled: true                  # M2
      mode: soft_penalty             # 七席锁定默认；hard_reject 仅开关
      allow_peaks: [sixteen_nine]
      allow_mixed_median_min: 1.70   # O-02 暂定 · 狗粮可调
      score_mul: 0.62                # SUP-MEGC-01 · 乘法 scorer；禁止 penalty:8.0
    release_stage_on_narrow_peak: false  # M3 延期
    page_letterbox: false                # M3 延期
    patterns:
      - screen-landscape-4
      - screen-portrait-2-landscape-2
      - screen-mosaic-4-2l2p-weighted
```

### 3.2 开放问题结案

| ID | 结案 |
|----|------|
| **O-01** | ✅ 默认 **soft_penalty** |
| **O-02** | ✅ 暂定 **1.70** + 狗粮可调 |
| **O-03** | ✅ **延期** M3；不够再用 P-释 |
| **O-04** | ✅ 2L2P 不转 GA + 闸硬拒 |
| **O-05** | ✅ **允许** CSS 先于父开关 |

---

## 4. 用户故事

| ID | 故事 | 验收钩子 |
|----|------|----------|
| **US-01** | 作为单反用户，我的四张 3:2 连拍不再被压进扁四宫砍头砍脚 | AC-04 · AC-05 |
| **US-02** | 作为预览用户，我不会看到「下面两格缺一块」的裁切事故 | AC-01 · AC-02 |
| **US-03** | 作为电影感 16:9 素材用户，等权四宫仍然好用、满幅 | AC-06 |
| **US-04** | 作为工程，打开 MSA contain 不会让等权屏变差 | AC-03 |

---

## 5. 系统性方案

### 5.1 总览

```text
窗资产 → MTSO/MCS 候选
           ↓
    MEGC selection_gate（P-选）──否──→ 降权/硬拒等权 A 类
           ↓是（峰允许）
    构建等权屏（静态轨 · AR=16:9）
           ↓
    crop_risk / MSA fit（可 contain）
           ↓
    MEGC 渲染合同：固定舞台 · 格内信箱（S-01）
           ↓
    [可选 M3] P-释 / P-函
```

### 5.2 S-MEGC-01 · 渲染舞台合同（M1）

**行为**

1. 对 A/B 类固定舞台 pattern：禁止因任意槽 `contain` 将 grid 改为 `height:auto` / `rows:auto` 导致超出舞台。  
2. contain 槽：格内 `object-fit:contain` + 纸色底（继承 MSA BLK-06）。  
3. 单测/视觉回归：构造「3 cover + 1 contain」的 `landscape-4` fixture → 舞台高 = 网格高（容差 1px）；下排槽底 ≤ 舞台底。

**文件锚点（实施时）**：`templates/visual-journal/journal-screens.css`（及 trips 同步策略按仓库惯例）；镜像规则勿漏 `data-layout=auto` / `layout-engine=screens`。

### 5.3 S-MEGC-02 · 窗峰判定复用

复用 MSA `build_msa_profile` / 峰阈值（梯子容差 0.08、单峰 ≥0.60、`wide_peak_fraction`）。  
MEGC **不** 另起峰算法；只消费 `landPeak` + `landMedianR`。

### 5.4 S-MEGC-03 · 选型闸 P-选（M2）

| 条件 | `mode=soft_penalty` | `mode=hard_reject` |
|------|---------------------|--------------------|
| `landPeak=sixteen_nine` | 不罚 | 不拒 |
| `landPeak∈{three_two,four_three}` | `score *= score_mul` | 拒 A 类 |
| `landPeak=mixed` 且 median ≥ `allow_mixed_median_min` | 不罚 | 不拒 |
| 其他 mixed | `score *= score_mul` | 拒 |
| pattern ∈ 混向等权（D-06）且峰非电影 | **硬拒**（不进 soft） | **硬拒** |

替代偏好（文档约定，实施可配置）：`screen-landscape-2`、`screen-mosaic-4-hero-70-sidebar`、加权 5/6 图横主（交 MSA）。

### 5.5 S-MEGC-04 · P-释 / P-函（M3 · 可选）

| 模式 | 行为 | 启用门 |
|------|------|--------|
| **P-释** | A 类屏 `aspect-ratio:auto`；格 AR 目标 = \(r^*\)（峰）；整屏变高 | 盲评通过 + 长图导出对齐 |
| **P-函** | 内网格按峰 AR 排，外层整页 letterbox 进 16:9 | 与 P-释互斥；whitespace 预算 |

**默认**：二者均 off；M2 仅靠 P-选即可宣称「等权债可控」。

### 5.6 S-MEGC-05 · 可观测性

raw 日志字段（与 mosaic capture 同通道）：

| 字段 | 含义 |
|------|------|
| `megcEnabled` | 父开关 |
| `megcOutcome` | `css_ok` \| `gate_allow` \| `gate_penalize` \| `gate_reject` \| `gate_fallback` \| `release_stage` \| `page_letterbox` \| `skipped` |
| `megcLandPeak` | 复用 profile |
| `megcPatternId` | 原候选 / 最终 pattern |
| `megcStageH` / `megcGridH` | 可选；狗粮断言用 |

---

## 6. 里程碑与列车

| 里程碑 | 内容 | 合码门 |
|--------|------|--------|
| **M0** | 七席锁定 D-00～D-10；名单 §1.3 冻结；拆 ACCEPTANCE/IMPL | 评审 Conditional Go |
| **M1 / PR-A** | S-01 CSS 舞台合同 + 回归单测/DOM 断言 | AC-01～03 |
| **M2 / PR-B** | S-03 选型闸 + 日志；demo-2019 等权 3:2 窗不再稳定落 `landscape-4` | AC-04～07 |
| **M3 / PR-C** | P-释或 P-函（**七席默认延期**；仅当 P-选不够时再开） | AC-08～10 |

**合并规则**：M0 未 Go 不开码；M1 未绿不得合 M2；**禁止**单 PR 塞满 M1–M3。  
**紧急例外**：仅 D-01 CSS 回归可在父开关前以 hotfix 合入（须标注 `fix_stage_css`），但不得夹带选型逻辑。

---

## 7. 风险与回滚

| 风险 | 缓解 |
|------|------|
| P-选过严 → 等权屏过少、dense 变栈过多 | soft_penalty 先跑；硬拒阈值可调；打点 gate 率 |
| P-释破坏「每屏 16:9」阅读节奏 | 默认 off；长图导出单独合同 |
| CSS 误伤 portrait intrinsic | 显式 :not 名单 + 视觉回归夹具 |
| 与 MSA contain 双重留白 | 共用 whitespace 预算；等权优先换模板而非 contain |
| 假绿（MSA 测等权贴 1.5） | D-00 + AC 禁令 |

**回滚**：父开关 OFF；CSS hotfix 可独立 revert。

---

## 8. 成功指标

| 指标 | 目标 |
|------|------|
| 等权屏下排裁切事故（gridH−stageH） | = 0（容差 1px）· AC-01 |
| `landPeak=three_two` 窗落入 GA `landscape-4` 率 | 相对基线显著下降（soft）或 =0（hard） |
| 单反狗粮「四宫砍头」主观项 | 盲评显著下降 |
| `landPeak=sixteen_nine` 等权观感 | 不回退（满幅 cover 仍可用） |
| MSA 父 OFF 基线 | 行为不变（除已合入的 CSS hotfix 合同） |

---

## 9. 开放问题（O-）· 已结案见 §3.2

历史开放表已由七席关闭；数值微调走 SHD-01，不重开 D-00/01/03。

---

## 10. AC 摘要

详见 [ACCEPTANCE-MOSAIC-EQUAL-GRID-CONTRACT-V1.md](./ACCEPTANCE-MOSAIC-EQUAL-GRID-CONTRACT-V1.md)。

| ID | 摘要 |
|----|------|
| **AC-MEGC-01** | contain 混排下 `landscape-4` 网格高度 ≤ 舞台高度 |
| **AC-MEGC-02** | mosaic 族 contain 保护不回退 |
| **AC-MEGC-03** | portrait-2/3 intrinsic 不被误伤 |
| **AC-MEGC-04** | 3:2 峰窗 soft/hard 闸对 A 类生效 |
| **AC-MEGC-05** | 16:9 峰窗等权仍可胜出 |
| **AC-MEGC-06** | 混向等权非电影峰硬纪律 |
| **AC-MEGC-07** | 日志字段齐全 |
| **AC-MEGC-08** | 父 OFF 基线（除已批 CSS hotfix） |
| **AC-MEGC-09** | P-释/P-函（M3）合同 |
| **AC-MEGC-10** | 三分峰狗粮盲评 |

---

## 11. 附录

### 11.1 实机锚点（2026-07-30）

- Trip：`demo-2019`  
- Screen：`ch-02-sc-06` · `screen-landscape-4`  
- Assets：`asset-086,088,089,091` · native ≈ 3:2  
- 现象：下排观感扁 + contain 撑破裁底  

### 11.2 与 MSA 一句话对照

| | MSA | MEGC |
|--|-----|------|
| 对象 | 加权拓扑 | 等权拓扑 + 渲染合同 |
| 手段 | `trackOverride` + fit | 选型闸 + CSS 舞台完整性 + 可选释舞台 |
| 等权四宫 | **明确不做** | **主责** |
