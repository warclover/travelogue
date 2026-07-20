# 模板与槽位管理落地 · 照片组合与呈现最优化 专题讨论纪要 · 2026-07-20

| 属性 | 内容 |
|------|------|
| **议题** | 模板/槽位管理真正落地；照片组合与呈现最优化 |
| **参会** | 产品 · UI/UX · 算法 · 架构 · 管线 · 视觉（摄影总监）· 排版（editorial） |
| **依据** | [PRD-LAYOUT-TRUST-NARRATIVE-V1.md](../PRD-LAYOUT-TRUST-NARRATIVE-V1.md)、[ltn-dev-feasibility-review-2026-07-20.md](./ltn-dev-feasibility-review-2026-07-20.md) |
| **前提（已拍板不重议）** | Wave A→B→C→D；C1 第一刀；hero_first 降权；preserveGroup 默认 true；机会 reserve；冻结扩库；N3 简化分段 |
| **状态** | 共识决议 + 3 项分歧待定标 + 4 项新硬前置，供项目负责人确认 |

---

## 0. 会议一句话结论

**活跃集收敛到 11（剪 5 加 1，留 1 空位）可以拍死；但 4-hero 转正前必须先修「三个评分暗礁 + 一个几何声明矛盾」，否则 C1–C3 全落地 hero 曝光依然为 0，会被误判成配额问题走回放宽 P21 的老路。**

---

## 1. 共识决议（D-SUMMIT 系列）

### D-01 · 活跃模板集：15 → 11（+1 空位余量）

| 动作 | patternId | 理由（多角色收敛） |
|------|-----------|-------------------|
| **加** | `screen-mosaic-4-hero-70-sidebar`（转 GA，见 D-02） | 产品「4 槽 hero」缺口唯一候选 |
| **剪** | `screen-portrait-6` | 视觉：槽 AR 0.375 必然裁脸；评分侧已在系统性压制 |
| **剪** | `screen-landscape-6` | flat 6 grid 惩罚常年生效=候选池噪声 |
| **剪** | `screen-portrait-9` | 无 flat 惩罚覆盖的漏网密格 |
| **剪** | `screen-landscape-9` | 与剪 9 宫方向一致；同 PR 删除 `R_GRID9_LAND` ×1.06 加成（算法事实 B） |
| **剪** | `screen-mosaic-grid-8` | 产品/UI/UX/视觉一致：画册语言里冗余 |
| **保** | `portrait-4` / `landscape-4` / `portrait-2-landscape-2` | 显式 fallback 与 2P+2L 签名位（N1 原案确认） |
| **保** | 5 槽双 hero、6 槽 main-hero ×2、3 槽族 | hero 主力与 parity 出口 |

九宫独立配额逻辑（`nine_grid_limits_for_trip`）**不受影响**——剪的是 MCS 统一族曝光，不是 planner 九宫路径。

**结构配比（UI/UX）**：3 槽×3 + 4 槽×4 + 5 槽×2 + 6 槽 hero×2 = 11，留 1 空位给未来验证过盲评的新版面。

### D-02 · 4-hero 转 GA 的四项前置（视觉 + 算法联合发现，必须先修）

| # | 问题 | 修复 |
|---|------|------|
| 1 | **几何声明矛盾**：模板声明 AR 1.78，真实 main cell AR ≈ **1.24**（70% 宽 × 满高） | 改 YAML：`targetDisplayAspect: 1.30`，`preferLadder: [1.3333, 1.5, 1.7778]`（4:3 优先，16:9 垫底）；否则 16:9 主图横向裁掉约 30% |
| 2 | **评分暗礁 A**：`_duplicate_density_penalty` 对 burst run≥4 打 0.8 惩罚且不看 `prefers_burst` —— 4-hero 在它唯一的设计场景（4L 连拍）先天背罚 | `prefers_burst: true` 模板豁免（cap 0.2）+ 回归锁单测 |
| 3 | **评分暗礁 C**：hero_first 的 dense max ×0.35 **向下取整**，小 trip（≤50 张）预算归零——C2 删早退也无济于事 | `max(1, floor(...)) if dense_max > 0 else 0` |
| 4 | 配置转正 | `status: ga`、`rollout.percent: 100`、进 `MOSAIC_4_PATTERN_IDS` + schema patternId 枚举 + `--sync-python` codegen + `LEGACY_MOSAIC_REGISTRY_IDS` 补 hero-3-2 |

**竞争设计（算法）**：不无条件抬 base_weight，用**条件化 hero-gap prior**——窗内存在明确主角（hero score gap ≥ 阈值）时 hero 模板 ×1.10、等权模板背 `wasted_hero` 0.35 惩罚；四张均势时反向。即「有主角 hero 赢、均势等分赢」。

**几何审计（视觉红线）**：C3 动工前对全部活跃模板做一次「声明 AR vs 实渲 cell AR」对账，杜绝第二个 1.78 vs 1.24。

### D-03 · 槽位角色标准化

- **主从对比**：main 面积占比 ≥0.55（AC 已有），视觉加码**主从面积比 ≥3:1**、主槽 AR 失配 ≤1.4× 作为闸门参数。
- **main 选择**：新增**窗内相对**软惩罚 `main_not_window_best`（0.4），代替提高全局 sharpness 分位——小 trip 不被饿死。
- **副槽**：最小可读短边 **72–96px**（分歧，见 §3）；新增 `main_clone_in_sidebar` 软惩罚（main 与副槽同 burst 且 |Δt|≤3s → 0.3），防主图威严被复本稀释。
- **硬门不动**（全场红线）：main AR ladder、`LANDSCAPE_AR_BLOCK_HIGH`、near_scene_clone 硬门、face_crop 全部维持。
- **合同缺口（排版）**：模板 YAML 补最小槽宽、出血声明、gap token 化、visualWeight 校验带、caption 锚 5 个参数；validator 增加对 heroAreaBand 与真实几何的对账规则。

### D-04 · 照片→槽位组合规则

- **粗分段**：burst 链永不切断；时间豁口 = min(900s, max(120s, 3×中位间隔))；换 city 切；时间戳缺失贴前段。segment 只是 planner 内存对象，**不发明 sceneId 字段**。`cross_scene_window_rate <5%` 由构造保证。
- **签名路由**：`(nP, nL, burst内聚)` → pattern 白名单缩窄，未命中**回落全量 registry**（禁止路由表成为新静默失败点）；路由结果写入日志 `candidate_source`。示例：`(0,4,true)`→{4-hero, landscape-4}；`(0,4,false)`→{landscape-4}；`(1,4)`→5 槽 main。
- **burst 信号一份两用**：span≤300s 且 `prefers_burst:true` → 加成 ×1.05 级别，同一布尔即 C5 reserve 的触发条件。
- **组合闸门（视觉）**：同场景连拍是「墙感」正证据；跨场景硬拼、色调断裂、主体不连续为拒收项；副槽间时间序或视角变化为佳。

### D-05 · C1 降级序与 C5 状态机（确认算法方案）

- 降级序：删 aux-3 拼接 → 5→4→6 窗宽降级（self-heal 内建）→ **单图 hero 救场**（仅 main-eligible 且 gap 显著；advance=1，余照重进循环）→ 显式 pending 返回 None（fail-loud 日志 `mcs_all_sizes_failed`）。parity/portrait tiler 的显式 3 槽路径**原样保留**。
- Reserve 状态机：`idle→armed→consumed/released` 四态挂 `planner_state`；armed 期间等权 dense 让位 hero 窗；释放条件三种；**永远不越过 P21**（额度不变，只是章内排队权）。

### D-06 · 节奏与呈现值带（排版 + UI/UX）

| Token | 推荐带 | 备注 |
|-------|--------|------|
| **L0 槽缝** | ~3px（拼图内「贴片感」） | 由模板 gap token 化 |
| **L1 屏缝** | `clamp(10–12px, 1.6vh, 20px)` | 现 8px 起步偏黏；起点 10 vs 12 待 JND（§3） |
| **L2 语义 pause** | `clamp(36px, 6vh, 64px)`，L0:L1:L2 ≈ **1:4:16** | 只出现在场景界 |
| **职责分工** | 票根管**章界**；L2 管**章内场景界** | 二者不叠加使用 |
| **beat 峰位** | classic_magazine 峰位 0.60–0.65 章进度 | D2 改默认时采用 |
| **连续容忍** | 同 pattern 连续：单图 ≤3、组合屏 ≤2、mosaic ≤1 | 章内 pattern 熵参考带 0.55–0.75 |

Token 全部放 **preamble / overlays 源文件**（工程约束已定）；命名规范与 `rhythmSignOff` 变更评审由排版侧出稿。

### D-07 · Longshot 三级降级（UI/UX + 视觉收敛）

428px 窄幅下 mosaic 放弃 16:9 网格照搬，按序降级：

1. **保组换排**：竖向组排（stack 内保留组标记/边框语义）——默认；
2. **代表图 + N**：`representativeAssetId` 大图 + 「共 N 张」徽标；
3. **拆屏**：仅显式 `preserveGroup=false` 时。

此定义直接喂给 B2 的新 ADR。

### D-08 · 落地机制（防「名义上线、实际归零」）

- **架构**：现状是**六写**（YAML status、rollout.percent、lte_policy、`LEGACY_MOSAIC_REGISTRY_IDS`、schema 枚举、config override），不止三写。收敛顺序：**先修门（PR drift 检查）→ 再删写点 → 最后建新抽象**。
- **管线**：新增 `active_set_gate` —— policy↔codegen↔schema↔golden 四处对账进 **PR job**（现 drift 检查躺在 push-only 的 validate 里，warn 分支是死代码）。
- **产品**：生命周期规则——**rollout=0 超过 4 周的模板强制 review**（转正或归档），杜绝「4-hero 躺一年」复发。
- **算法**：AC 指标三件套——**配额无关机会 oracle + 原始日志（非裁剪）+ 固定 fixture**，缺一即可被「少尝试 / 多裁剪 / 换标签」刷绿。
- **视觉**：盲评用计数类硬门（裁脸数、AR 失配数）+ 整本 A/B 二选一，防「工程指标好看、画面难看」。

### D-09 · N2 决议：**脱敏/合成 fixture 入库**

产品与管线一致表态：合成小型 fixture trip（`log_level=debug` re-curate 后脱敏）入库，CI 可复跑——AC-C-01/02 基线以此为准。本机 dogfood 保留为补充。

---

## 2. 会议新发现（增量事实，动工前必修）

| # | 发现 | 发现方 | 影响 |
|---|------|--------|------|
| S1 | `_duplicate_density_penalty` 不豁免 `prefers_burst:true`（0.8 重罚） | 算法 | 4-hero 上线即死；C3 前置 |
| S2 | `R_GRID9_LAND` ×1.06 加成与剪 9 宫自相矛盾；`portrait-9` 无 flat 惩罚 | 算法 | 剪枝 PR 同步删除 |
| S3 | hero_first dense ×0.35 取整归零（小 trip） | 算法 | C2 必修，否则 curated 轨 hero 预算恒 0 |
| S4 | 4-hero 声明 AR 1.78 vs 实渲 ≈1.24；`portrait-6` 槽 AR 0.375 必裁脸 | 视觉 | GA 前修 YAML；全模板几何审计 |
| S5 | 模板权威实为**六写**非三写 | 架构 | E1 范围扩大；先门后删 |
| S6 | hero-3-2 模板 [7,3] 分栏、2px/3px gap 不统一等网格「杂音」 | 排版 | 纳入 D3 合同参数与几何审计 |

---

## 3. 分歧与建议裁决

| 分歧 | 立场 A | 立场 B | 建议 |
|------|--------|--------|------|
| 副槽最小短边 | UI/UX：72px | 视觉：96px | D1 JND 小样在 72–96px 带内定标；定标前 validator 用 72px 底线 |
| L1 屏缝起点 | 排版：10px | UI/UX：12px | 同上，JND 定标；两案都确认现状 8px 偏黏 |
| 活跃集规模 | 算法：12（不剪 grid-8） | 产品/UI/UX/视觉：11（剪 grid-8） | **采纳 11**：grid-8 在画册语言冗余且无签名位；算法侧无保留理由 |

---

## 4. 对任务清单的增量影响

在 [ltn-dev-feasibility-review](./ltn-dev-feasibility-review-2026-07-20.md) 基础上，Wave C 前置再加 4 项硬前置：

| 新任务 | 归属 | 内容 |
|--------|------|------|
| **H6** 评分暗礁修复 | C3 前置 | S1（burst 豁免）+ S2（删 9 宫加成）+ S3（取整保底），各配回归锁单测 |
| **H7** 模板几何审计 | C3 前置 | 全活跃模板「声明 AR vs 实渲 cell AR」对账；修 4-hero ladder |
| **H8** active_set_gate | Wave A 扩展 | policy↔codegen↔schema↔golden 四处对账进 PR job |
| **H9** 合成 fixture | A4/AC 基线（N2 决议） | 脱敏合成 trip 入库 + debug 级决策日志 |

防回潮单测清单（算法已列 9 条：no_aux3、parity_tail、hero_first_attempts_mcs、dense_floor、burst_no_dup、no_grid9_boost、reserve_release、metric_reads_raw_log、golden 重录）随 C1/C2/C3 各 PR 落地。

---

## 5. 各角色红线汇总

| 角色 | 红线 |
|------|------|
| 产品 | 剪枝清单与 fixture 决议今日拍死；rollout=0 超 4 周强制 review |
| UI/UX | 副槽不得压成信息条；降级阶梯顺序不可倒置 |
| 算法 | 硬门阈值（AR ladder / clone / face_crop）不为凑 hero 松动；reserve 不加额度；AC 禁读裁剪日志 |
| 架构 | 先修门再删写点；schema 演进走可选字段 + 单一 normalize 层推导 |
| 管线 | 基线未冻结不动 C1；golden 重录须与剪枝同 PR |
| 视觉 | 主从 ≥3:1；裁切安全区不破；几何审计先于 GA |
| 排版 | token 单点定义；禁 breath 空屏凑节奏；变更过 rhythmSignOff |

---

## 6. 待项目负责人确认（3 项，其余均已共识）

1. **D-01 活跃集 11 清单**（剪 5 加 1）是否批准？
2. **分歧裁决**：副槽底线与 L1 起点交 D1 JND 定标（先用 72px/10px 保守值）是否接受？
3. **H6–H9 四项新硬前置**插入 Wave A/C 前置（合计约 +3–4 人日）是否批准？

批准后落地序：**Wave A（含 H8/H9）→ H6/H7 → C1 → C2 → C3（剪枝+转正同 PR）→ C5**；B3 双预览与 D2 beat 默认并行提前。

---

## 7. 变更

| 日期 | 说明 |
|------|------|
| 2026-07-20 | 七方专题讨论纪要初稿：D-01–D-09 决议、S1–S6 新发现、3 项分歧、H6–H9 增量任务 |
