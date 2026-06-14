# Phase 23「最佳时刻」PRD 评审会纪要

| 属性 | 内容 |
|------|------|
| **会议** | P23 最佳时刻 PRD 跨职能评审 |
| **日期** | 2026-06-14 |
| **文档** | [PRD-PHASE23-peak-moment.md](../PRD-PHASE23-peak-moment.md) v0.23.0 · [ACCEPTANCE-PHASE23.md](../ACCEPTANCE-PHASE23.md) |
| **发起人** | 产品负责人 |
| **结论** | **有条件通过** — 可进入 Kickoff（P23-W1）；须合并 §4 决议升版 **v0.23.1** 后开工 |

---

## 1. 参会与角色

| 角色 | 代号 | 关注点 |
|------|------|--------|
| **产品负责人** | PM | 差异化、零编辑路径、与封面/封底不打架 |
| **策展算法负责人** | ALG | `peak_moment_score` 可测、可配置、与 cover/closing 正交 |
| **排版 / BSP 设计** | DES | 沉浸不破坏、脚注不抢戏、动效预算 |
| **渲染工程** | ENG | 模板插入点、`assemble.py`、旧 trip 兼容 |
| **摄影社区顾问** | PHO | EXIF 五元组可信度、DxO 对标、竖图 moment |
| **隐私 / 合规** | LEG | EXIF 存储边界、分享 strip、HTML 脚注 |
| **QA** | QA | Tier 0 可自动化、盲评可复现、回归封面选型 |
| **零编辑用户代言人** | UX80 | 80% 路径不增步骤、小册体验 |

---

## 2. 议程与讨论摘要

### 2.1 需求方向（一致通过 · 全票赞成）

**PM**：P23 解决的是「读完一册，记不住哪张是这趟旅行的代表」——全册单屏 + 1 行 EXIF 比每张挂 EXIF 或加边框更符合 BSP 北极星。

**PHO**：竞品 38 款里没有「装订成稿 + 原始 EXIF 同屏」；moment 屏是护城河落地点，**赞成**。

**UX80**：默认 curate 自动选、成功页不新增按钮——**赞成**；担心多一屏拖慢「滚到底」节奏。

**决议**：

- P23 **立项通过**；定位与 PRD §1–§2 不变。
- moment 屏视为 **「停顿屏」**：插入 `before_closing` 时，读者已读完正文，**不**打断中段沉浸流。

---

### 2.2 开放问题 OQ-P23-01～04（产品已拍板 · 评审确认）

| ID | 问题 | 产品决议 | 评审会 |
|----|------|----------|--------|
| **OQ-P23-01** | 首版是否做 `arc_peak` 插入？ | **否**；W1 仅 `before_closing` | ✅ 全票同意。ALG：`arc_peak` 依赖 P17 highlight 稳定，首版避免双插入点测试矩阵 |
| **OQ-P23-02** | longshot 是否含 moment 屏？ | **否** | ✅ 同意。DES：长图密度预算已紧；moment 属「卷轴深读」特权 |
| **OQ-P23-03** | 脚注含摄影师署名？ | **否**；署名走 `meta` / 封面 | ✅ 同意。PHO：脚注保持「现场参数」；署名在封面/营销墙更合适 |
| **OQ-P23-04** | 竖图允许 moment？ | **允许** | ✅ 同意。ENG：需 `layout-screen--portrait` 分支，写入 W2 任务 |

> 以上四项 **闭合**，自 v0.23.1 起从「开放问题」移至 §3 已拍板决策。

---

### 2.3 三图位分离（ALG + DES · 有条件赞成）

**ALG**：独立 `peak_moment_score` 必要；但 §7.3 选型顺序有隐患——`pick_peak_moment` 在 `resolve_closing_asset_id` **之前**，closing 却需「软避 moment」，而 closing 解析时 moment 已固化，**逻辑可行**。

**争议**：`f_on_screen`（正文名场面）与 closing「偏未用」相反，是否导致 moment 总选「已经看腻」的图？

**DES**：恰恰相反——moment 应是「回看仍震撼」的那张；已在正文 hero 出现过的图 **加分合理**。

**决议**：

- 保持 `f_on_screen` 权重 **0.15**；R0 盲评后若「与正文重复感过强」再调。
- **新增硬规则**：若 top-1 moment 与 **任意章首 hero** 相同，降权 0.85× 并记录 `momentExplain.duplicate_hero`（ALG · **A8**）。
- closing 解析函数 **必须**接受 `exclude_ids: set` 参数扩展，显式传入 `{momentAssetId}`（ENG · **A9**）。

---

### 2.4 EXIF 脚注形态（PHO + DES · 修订通过）

**PHO**：

- 格式方向对；建议快门统一为 `1/500s` 或 `1/500` 二选一，**全站一致**。
- iPhone / 计算摄影常无 `LensModel`：应显示 `Apple iPhone 15 Pro · 24mm eq.` 而非空白。
- 海拔有 GPS 才写；**禁止**编造。

**DES**：

- `38%` 透明度在暗图下方可能不足 3:1；脚注区加 **`--moment-exif-bg`** 纸色 6% 衬底（非边框），保证 WCAG。
- 左上角 `Moment` 标签：**默认中文「决定性瞬间」**；英文 profile 再切 `Moment`（**A10**）。

**LEG**：

- `assets[].exif` 进 `trip.json` 可接受（用户本机数据）。
- 分享 ZIP `strip_exif` 与 HTML 脚注分离——**必须在 `/install` 数据去向 FAQ 补一句**（非 P23 代码，文档 **A11**）。
- 截图类素材 `exif.completeness: none`：**不得**伪造机型。

**决议**：

- 快门展示：`1/500`（无后缀 `s`，与营销 PRD DxO 风格一致）。
- 脚注区增加可选纸色衬底；验收加 **AC-P23-21** 对比度抽检。
- ingest 对 Apple / 主流 Android 做 **model 规范化**表（W1 最小表，后续扩展）。

---

### 2.5 小册禁用与碰撞（UX80 + PM · 赞成附条件）

**UX80**：≤15 张三张仪式位（封面+时刻+封底）太挤——**赞成** `auto_disable_small_trip`。

**争议**：16–19 张「灰色地带」仍可能三角撞车。

**PM**：PRD 写「&lt;20 张可降级 closing 碰撞」，与 §7.4「≤15 禁用」不一致。

**决议**：

- **≤15**：不渲染 moment（维持）。
- **16–19**：渲染 moment，但 `min_score` 提高为 **0.45**（配置 `small_trip_elevated_min_score`）（**A12**）。
- `momentCollision: closing` 写入时 Studio 显示 **黄色 chip**「与封底共用素材」，不阻断发布。

---

### 2.6 盲评门槛（QA + PM · 对齐封面 PRD）

| 观点 | 结论 |
|------|------|
| QA：AC-P23-09 一次 60% 是否过低 | **分两阶段**：**M1** ≥50%（5 册）；**M2** ≥60%（+3 册 hold-out） |
| PM：是否与封面 M1/M2 对齐 | **对齐**封面选型 M1/M2 节奏 |
| ALG：盲评问句须冻结 | 「这一张最能代表这趟旅行的决定性瞬间吗？」（是/否） |

**决议**：

- 盲评表使用 **`scoreRankedMomentTop3`**（全池 `peak_moment_score` 降序，**不得**用 `momentCandidates` 多样性序作 B 类判定——同封面 PRD 教训）。
- 新增脚本 `scripts/moment_selection_blind_review.py`（**A13**）。

---

### 2.7 工程范围与排期（ENG · 赞成，提两项）

**ENG**：

- W1/W2 拆分合理；`before_closing` 插入只需改 `journal.hbs` + `assemble.py`，**不必**动 screen planner 主链——**赞成**。
- **风险**：`resolve_closing_asset_id` 目前无 `exclude moment` 参数——须 W3 前完成，否则 AC-P23-05 失败。
- **建议**：`ingest.exif_camera` 默认 **true**，但 HEIC 无 EXIF 时 fail-open，不阻断 ingest。

**DES**：P23-W2 须复用 BSP viewport-fit 变量，**禁止**手写死 `16/9` 舞台。

**决议**：

- Kickoff 顺序：**W1 ∥ W2 可部分并行**（ingest 与模板），但 **W3 阻塞发布**。
- 工期 **2–3 周** 维持；若 P22 revision 冲突，P23 可降 Studio API（§10.2）到 W4。

---

### 2.8 明确不在 P23（再次确认）

| 项 | 处理 |
|----|------|
| `arc_peak` 动态插入 | 顺延 P23.1 或 P18 叙事编排联动 |
| 每张 EXIF / 艺术边框 | 不做 |
| 用户主路径手选 moment | 不做（Tier 2 Studio 换图保留） |
| 营销站 F-06 hover EXIF | 另线，复用 `format_moment_exif_line()` 工具函数 |
| 实验记录 DB | 顺延 **P24** |

---

## 3. 评审会决议清单（Action Items）

| ID | 事项 | 负责人 | 阶段 |
|----|------|--------|------|
| **A1** | PRD 升版 **v0.23.1**（闭合 OQ、合并本节修订） | PM | 会后 ✅ |
| **A2** | 冻结盲评样本 ≥5 册 JSON（含仙本那、小册、featured） | PM | R0 前 |
| **A3** | `pick_peak_moment()` + `peak_moment_score` + unit tests | ALG | W1 |
| **A4** | `assets[].exif` ingest + Apple model 最小映射表 | ENG | W1 |
| **A5** | `moment-screen.hbs` + CSS + `format_moment_exif_line()` | ENG + DES | W2 |
| **A6** | `resolve_closing_asset_id(exclude_ids=…)` 扩展 | ENG | W3 |
| **A7** | hero 重复降权 + `momentExplain` | ALG | W3 |
| **A8** | 盲评脚本 `scoreRankedMomentTop3` | QA + ALG | W4 |
| **A9** | AC 增补 AC-P23-21（对比度）、M1/M2 盲评分期 | QA | 会后 ✅ |
| **A10** | `IMPLEMENTATION-PHASE23.md` Kickoff 清单 | ENG | 通过后 |

---

## 4. 各专家书面意见汇总

| 专家 | 总评 | 主要意见 | 处理 |
|------|------|----------|------|
| **PM** | ✅ 通过 | 差异化清晰；坚持零编辑 | 维持 |
| **ALG** | ✅ 有条件 | 加 hero 去重；盲评 top3 定义；16–19 张提 min_score | A7、A8、A12 |
| **DES** | ✅ 通过 | 脚注衬底；竖图舞台；禁死 16:9 | A5、OQ-04 |
| **ENG** | ✅ 有条件 | closing exclude API；ingest fail-open | A6、A4 |
| **PHO** | ✅ 通过 | 快门格式；机型规范化；不伪造 EXIF | §8.2 修订 |
| **LEG** | ✅ 通过 | 文档补数据去向；截图不伪造 | A11 |
| **QA** | ✅ 有条件 | M1/M2 分期；Playwright 覆盖竖图 moment | AC 修订 |
| **UX80** | ✅ 通过 | 小册禁用；before_closing 不打断中段 | 维持 |

---

## 5. 风险登记

| 风险 | 级别 | 缓解 |
|------|------|------|
| moment 与正文 hero 同图「重复感」 | 中 | hero 降权 + 盲评 M1 50% 早期发现 |
| EXIF 大面积缺失（微信保存图） | 中 | completeness + 地名时段回退；无 2 段则隐藏行 |
| closing / moment 撞车 | 低 | exclude API + collision chip |
| P17 arc_peak 未就绪导致 f_arc_peak 空转 | 低 | 权重自动重分配到 aesthetic + on_screen |
| trip.json 体积 | 低 | exif 子对象 ~200B/图；momentExplain ≤4 因子 |

---

## 6. 下一步

1. 合并决议发布 [PRD-PHASE23-peak-moment.md](../PRD-PHASE23-peak-moment.md) **v0.23.1**，状态 → **Approved · 待 Kickoff**。  
2. **R0**（只测不改）：在仙本那 + 2 册 featured 上手工标注「心中 moment」，与 `scoreRankedMomentTop3` 对比，建立基线。  
3. **P23-W1 Kickoff**：ingest exif + `pick_peak_moment`；W2 与 W1 后端可并行前端模板。  
4. M1 盲评（50%）通过后再开 Studio 换图 UI（Tier 2）。

---

## 7. 版本

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-06-14 | P23 最佳时刻 PRD 跨职能评审会纪要 |
