# MEGC · 开发负责人实施前可行性反馈

| 属性 | 内容 |
|------|------|
| **日期** | 2026-07-31 |
| **角色** | 开发负责人（落地 PR-A→B；落实 [PRD MEGC v0.2.0](../PRD-MOSAIC-EQUAL-GRID-CONTRACT-V1.md) · [七席](./megc-equal-grid-contract-v1-review-2026-07-31.md)） |
| **结论** | **同意 Kickoff PR-A（CSS）**；**PR-B 开工前须改写配置合同中的 `penalty: 8.0`**（与现网乘法 scorer 不兼容）；BLK-06 可降级为「重渲同步 + cache-bust」而非第二套 CSS SSOT |
| **DOC-STATUS** | **active** |

---

## 0. 一句话

PRD 分治（等权 ⊥ MSA）与实锤对齐，**PR-A 是真正的低风险止血**；但 v0.2 里选型闸的 **`penalty: 8.0` 按加法写、现网 scorer 是 〔0,1〕乘法**，以及 **landscape-4 同时走 mosaic 候选与 planner/legacy 构造**——若不在 M2 前钉死挂点，soft 闸会「配置开了、分没扣上」或只挡住一半路径。

---

## 1. 总判断

| 维度 | 评分 | 说明 |
|------|------|------|
| 问题真伪 | ✅ | F-01～F-12 与 `geometry` / CSS 1601–1648 / demo DOM 一致 |
| M1（PR-A）可开工性 | ✅ | 可用 **pattern 级更高优先级规则** 覆盖，无需拆掉竖拼 intrinsic 总规则 |
| M2 合同完备度 | ⚠ | `penalty` 语义、挂点（candidates vs scorer vs planner）未钉死 |
| BLK-06（trips CSS） | ⚠→低 | `render/engine.py` 每次 `copy_css` 从 templates 覆盖 trip 拷贝；真风险是 **浏览器缓存** 与 **未重渲** |
| BLK-07（peak 只读） | ✅ 易 | `build_msa_profile` 纯函数，不读父开关；`maybe_apply` 才 early-return |
| 与 MSA/MTSO 冲突 | 低 | 不改白名单、不改 lifecycle；soft 惩罚可挂 scorer |
| 测试债 | 中 | AC-01 宜 Playwright/DOM；纯 CSS 单测弱；需防 portrait-4 回归 |

---

## 2. 代码对照：PRD / 七席主张 vs 现实

| # | 主张 | 代码现实 | 风险 | 开发建议 |
|---|------|----------|------|----------|
| **C-01** | contain 撑破等权 2×2 | `journal-screens.css` L1601–1607 对**所有** `--2x2:has(contain)` `rows:auto;height:auto`；L1612 注释却说 landscape-4 keep stage | 注释误导后人 | **PR-A**：为 `screen-landscape-4` / `portrait-2-landscape-2` 增加 **更高优先级** 规则（对齐 mosaic L1635–1640），恢复 `1fr`+`height:100%`；**不要**删除全局规则（portrait-4 L1614–1627 依赖释舞台） |
| **C-02** | 格内 contain 槽也被 `height:auto` | L1652–1664 非 mosaic 槽 `:has(>contain)` → `height:auto;align-self:start` | 即使 grid 守住，单槽仍可能塌 | 同上 pattern 下覆盖：槽 `height:100%;align-self:stretch`；img 仍 contain + 纸色 |
| **C-03** | BLK-06 trips 双源 | `render/engine.py` L599–617：`shutil.copy2(JOURNAL_SCREENS_CSS → out_dir)` + `?v=bundle_version` | 未重渲的旧 trip 文件会旧；改 templates 后重渲即新 | **降级 BLK-06**：合码说明写「改 CSS 后重渲 demo」；CI 继续盯 **templates** codegen sync；可选 bump `asset_version` / bundle |
| **C-04** | Peak 复用 MSA | `build_msa_profile(assets, cfg=sa)` 不检查 `enabled`；仅 `maybe_apply_slot_adaptation` 父 OFF 直接 return | 无 | PR-B：`megc_gate` 直接调 `build_msa_profile`；AC-07b 断言父 OFF 仍有 `landPeak` |
| **C-05** | soft `penalty: 8.0` | `scorer.score_candidate`：**乘法**惩罚，`total` 夹在 〔0,1〕；`base_w` 也是 `min(1.0, total * base_w)` | **8.0 加法无意义**；配置假绿 | 改合同：`score_mul` ∈ (0,1]，建议默认 **0.55～0.72**（须对照 `landscape-4` `base_weight=1.12` 标定）；或 `score -= x` 再 clamp——**禁止**沿用 8.0 |
| **C-06** | 闸挂「MCS/MTSO」 | `landscape-4` 在 `MOSAIC_4_PATTERN_IDS`、`coarse_segments`、`builders` 排序、**以及** `screen_planner` PATTERN_GRID_CLASS | 只改 scorer 可能漏 planner/legacy 直构 | **双挂点**：① `candidates` 硬拒（混向 D-06）② `scorer` soft mul（纯横）；另在 `build_screen`/finalize 前加 **assert/自愈**（非电影峰 + A 类 → 降级或打点），防旁路 |
| **C-07** | `landscape-4` 权重高 | YAML `base_weight: 1.12`（等权四宫偏爱） | soft mul 不够仍会赢 | 标定狗粮：3:2 四窗下胜出率；不够再降 `score_mul` 或对 A 类叠 `R_MEGC_PEAK_MISMATCH` |
| **C-08** | 混向硬拒 | `candidates._reject` 已有硬拒模式（UR/SSG/contract） | soft 路径若仍生成 2L2P 候选会浪费 | D-06：**只走 hard reject**，不进 soft 分支 |
| **C-09** | MSA contain 与 CSS | `msa_fit` / `crop_solver` 可翻 contain；等权屏一翻就触发 C-01 | PR-A 未合前开 MSA contain = 放大事故 | **先合 PR-A**，再谈 MSA 默认 on（与 MSA hold-off 一致） |
| **C-10** | Playwright AC-01 | 仓库已有 playwright MCP/本地服习惯；单测以 pytest 为主 | 纯 CSS 难测高度 | PR-A：pytest + 最小 HTML fixture（或 trip 片段）用 JSDOM/`playwright` 二选一；至少 **计算 style 优先级** 的回归快照 |

---

## 3. 分 PR 落地建议

### 3.1 PR-A（M1）· **建议立即开工**

**范围（严守）**

1. `templates/visual-journal/journal-screens.css`：  
   - 纳入：`screen-landscape-4`、`screen-portrait-2-landscape-2`（及若仍 emit 的等权 2×2 experimental，可选）  
   - 排除：保持 `portrait-2/3/4`、`landscape-2/3`、`screen-mosaic-*` 现状  
2. 覆盖 **grid** 与 **slot:has(contain)** 两层（C-01/C-02）  
3. 修正 L1612 误导注释（SHD-03）  
4. 回归：AC-01（landscape-4 混 contain）· AC-02（mosaic）· AC-03（portrait-2）  
5. 重渲 `demo-2019` 验证 ch-02-sc-06 裁底消失  

**明确不做**：选型闸、配置 dataclass、改 MSA 白名单、P-释。

**工期**：0.5～1.5 人日。

**合码门**：BLK-02 名单写进 MR 描述即可视为签字；BLK-06 按 §2 C-03 降级执行。

### 3.2 PR-B（M2）· 开工前书面 SUP（建议产品会签）

| ID | 问题 | 开发建议默认 |
|----|------|----------------|
| **SUP-MEGC-01** | soft 惩罚语义 | 配置改为 `score_mul: 0.62`（名待定），删除 `penalty: 8.0` |
| **SUP-MEGC-02** | 挂点 | scorer soft + candidates hard（混向）；是否要 planner 旁路自愈 |
| **SUP-MEGC-03** | 无替代时 | 已有 D-10；实现上允许仍 emit 等权但打 `megc_gate_fallback` **还是** 拆成 landscape-2×2？推荐：**先打点 + soft**，硬拆窗另开 |

**实现要点**

- 新模块建议：`travelogue/layout_engine/mosaic/megc_gate.py`（纯函数：profile → decision）  
- 配置：`Equal_grid_contract` 挂 `MosaicConfig`，未知键 fail-loud（对齐 MSA）  
- 日志：扩 `MosaicWindowLog` / screen 级字段，AC 只读 raw  

**工期**：2.5～4 人日（含 SUP 回写 + 标定）。

### 3.3 PR-C（M3）· **同意延期**

P-释会碰长图/`layout-screen--16x9` 阅读节奏与导出；现网 `landscape-2/3` 已是 CSS-primary 先例，但等权四宫释舞台影响面更大。等 PR-B 狗粮证明 P-选不够再开。

---

## 4. 对七席 BLK 的执行意见

| BLK | 七席原意 | 开发执行 |
|-----|----------|----------|
| **02** | CSS 名单签字 | PR-A MR 正文贴纳入/排除表；单测两侧各 1 夹具 |
| **03** | soft 默认 | 同意；但须改惩罚语义（SUP-01） |
| **06** | trips 同步 | **降级**：重渲即同步；不新建第二 SSOT |
| **07** | MSA OFF 算峰 | 直接调 `build_msa_profile`；易绿 |

---

## 5. 风险（按概率×伤害）

| 风险 | 等级 | 缓解 |
|------|------|------|
| 删全局 contain→auto 误伤 portrait-4 | 高 | **只加特例覆盖，不删总规则** |
| soft 闸无效（权重 1.12 + 乘法理解错） | 高 | SUP-01 标定；狗粮看胜出率 |
| 只挡 mosaic、不挡 planner | 中 | C-06 双挂点 / finalize 自愈 |
| PR-A 未合就开 MSA contain | 中 | 发布说明互锁 |
| Playwright 不进 CI | 中 | 至少 CSS fixture + 重渲截图入 acceptance-records |

---

## 6. 开发负责人决议

| 项 | 决议 |
|----|------|
| **PR-A** | **Go · 可立即开工** |
| **PR-B** | **Conditional** · 先合并 SUP-01/02 回写 PRD 配置段 |
| **PR-C** | **Hold**（与七席一致） |
| **是否需要产品会签** | SUP-01（惩罚语义）、SUP-03（fallback 行为）建议会签后再写 M2 |

---

## 7. 建议的立即动作顺序

1. 开 PR-A：CSS 特例覆盖 + 注释修正 + demo 重渲截图。  
2. 短会 15min：产品确认 SUP-01（`score_mul` 取代 `penalty: 8.0`）。  
3. 再开 PR-B。
