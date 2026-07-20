# LTN PRD 开发可实现性评审 · 2026-07-20

| 属性 | 内容 |
|------|------|
| **对象** | [PRD-LAYOUT-TRUST-NARRATIVE-V1.md](../PRD-LAYOUT-TRUST-NARRATIVE-V1.md)（v1.0.0） |
| **视角** | 开发负责人 · 对照代码实况（layout_engine / config / render / web / CI）逐条核实 |
| **结论** | **方向可执行；6 处与代码事实不符需修订；真实工期重心与 PRD 波次估计不同** |
| **建议** | 修订 PRD 至 v1.0.1（见 §5）；按 §4 调整落地序 |

---

## 1. 总判

1. PRD 的根因判断（3 槽兜底、hero_first 硬跳过、几何门、P21 非主因）**与代码事实吻合**，Wave C 主刀口有效。
2. **工期重心判断需要修正**：Wave A 实际比 PRD 预估小得多（代码大半已就绪，卡在 CI 拓扑与分支保护）；**真正的大石头是 B2**（推翻 ADR-003 的 longshot flatten 合同，单项 1.5–2.5 周）；其次是 C4（scene 预分段，`sceneId` 字段不存在）。
3. PRD 有 **6 处与代码不符**，其中两处影响任务拆解（活跃族已 15 个 ID、日志默认裁剪 rejects），需在动工前修订。
4. 有 **5 项隐藏前置任务** PRD 未列（schema 枚举、日志格式、codegen 同步、活跃集剪枝决策、demo fixture 策略）。

---

## 2. PRD 与代码事实不符处（须修订）

| # | PRD 表述 | 代码事实 | 影响 |
|---|----------|----------|------|
| F1 | MCS hook 在 `curation/mosaic/` | 实际在 `travelogue/layout_engine/mosaic/hook.py`；`curation/screen_layout_state.py` 只是 `planner_state` 的 shim | 文档路径纠错 |
| F2 | 「将 hero SKU 纳入活跃族，活跃集 ≤12」 | `lte_policy.yaml` 统一集合**已 15 个 ID**；且 5 槽 hero（`hero-3-2-plus-4`）**已是 GA 并在 MOSAIC_5** | C3 的本质是「**加 4 槽 hero + 剪掉等权 4/6/9**」，剪谁是**产品决策**，PRD 未拍 |
| F3 | C4「按 burstGroupId / sceneId / 地点切窗」 | **`sceneId` 字段全库不存在**；只有 `burstGroupId` / `takenAt` / `place`；现有 temporal/clone 均为软信号，预分段基本未做 | C4 是最大的新建量（L 级）；需先定义「scene」= burst+时间+city，勿假造字段 |
| F4 | 「Studio 消费 mosaicDecisionLog 展示 Top3」 | 日志**已持久化**到 `trip.curation.mosaicDecisionLog`，但默认 `log_level=window` 时 `format_log_entry` **剥掉完整 `rejectedTemplates`**（有测试断言此行为）；Studio 现读的是 beam 的 `layoutDecisionLog`，**无** mosaic 日志 API | C6 前置：先改 window 级保留策略或 explain 字段，再谈前端 |
| F5 | 「闭合 LRG required check」暗示防护缺失 | 截断 fail-fast（strict → exit 1）与关键 selector 单测**已存在且在 PR 跑**；缺口是 `validate` job（export+diff）**只在 push 后跑**，其 PR-warn 分支是**死代码**；分支保护未核实 | A1 实际是 **CI 拓扑改造 0.5–1.5 人日**，不是重写门禁 |
| F6 | 「MCR config silent default」作为待修项 | `enabled_window_sizes` 缩成 `[5]` 的 bug **已修**（有单测）；剩余 silent 项是 `layoutDensity` 非法值静默归一 `balanced`、`web_layout_engine`/`screen_plan_scope` 静默回退、未知键仅 warning | A2 范围应改写为「关键 curate 键 fail-loud」，勿重复已完成项 |

另两处工程事实，PRD 需显式承认：

- **B2 是改合同不是修 bug**：ADR-003 明文「longshot · screens 按 slot 展平」，`flatten_screens_to_items` 是设计行为。改 `preserveGroup` 须新 ADR 推翻旧 ADR，涉及 `resolve_chapter_items_for_render`、longshot 章内挑屏（`select_longshot_screens`）、breath 插入、平台切分边界、窄幅 mosaic CSS。
- **present 已静默跳过票根**：`chapter-separator` 不在幻灯 selector 内，跳过不是 `skipAuxBlocks` 控制——R-B4 的产品规则确有必要。

---

## 3. 隐藏前置任务（PRD 未列，会卡进度）

| # | 任务 | 卡谁 | 量级 |
|---|------|------|------|
| H1 | `schemas/trip.schema.json` 为 `additionalProperties: false`：B1 五字段（`narrativeRole` 等）与 `screen-mosaic-4-hero-*` patternId 枚举**都要先改 schema** | B1、C3 | S |
| H2 | `format_log_entry` 保留 Top3 reject（或新增 explain 字段）+ 控制日志体积 | C6、A4 | S |
| H3 | `lte_policy.yaml` 改动后须跑 `scripts/lte_export_legacy.py --sync-python` 同步 `_legacy_generated.py`；`LEGACY_MOSAIC_REGISTRY_IDS` 当前缺 hero-3-2（LTE off 路径） | C3 | S |
| H4 | 活跃集剪枝决策：从 15 剪到 ≤12，剪 `portrait-4`/`landscape-4`/`portrait-6`/`landscape-6`/9 宫中的哪些，需产品拍板 + golden 更新 | C3 | 决策 + S |
| H5 | Demo fixture 策略：`trips/*` 全部 gitignore，`demo-65db8fd377` 在干净 clone/CI **不可复跑**；本机该 trip 的决策日志只有 1 条（需 `log_level=debug` re-curate 才有 reject 聚合） | A4、AC-C-01 基线 | 决策 + S |

旧 trip 兼容原则（B1）：新字段全部可选；缺失时由应用层推导（`patternId` 含 mosaic → `preserveGroup=true`），**不要求重 curate**。

---

## 4. 修正后的工作量与落地序

### 4.1 各任务真实量级（对照代码后）

| 任务 | PRD 感觉 | 实测量级 | 关键依据 |
|------|----------|----------|----------|
| A1 门禁闭合 | 重 | **0.5–1.5 人日** | fail-fast+单测已有；把 sync drift 挪进 `test-pr` + 分支保护 |
| A2 config fail-loud | 中 | **1–2 人日** | 主战场是 `layoutDensity` 等归一化改 raise；复用 `template_contract` 的 fail-loud 模式 |
| A3 冻结扩库 | 轻 | 纪律 0.5 日；机器门 ~1 日 | validator 现只挡 &gt;9 槽；「&gt;6 拒」是新规则且要处理 8/9 存量豁免 |
| A4 诊断基线 | 轻 | **0.5–1 人日** + H5 决策 | 复用 `layout_debt_report.py` / `mosaic_config_diag.py` 薄封装 |
| B1 合同 ADR+schema | 中 | **3–5 天** | H1 前置；消费端可后置 |
| **B2 preserveGroup** | 中 | **1.5–2.5 周（最大石头）** | 推翻 ADR-003；render 主路径 + CSS + 过滤/切分 |
| B3 双预览 MVP | 中 | **2–4 天** | iframe 双面（`index.html` vs `index-longshot.html` 同宽模拟）；**可先于 B2 交付** |
| C1 解耦 3 槽 | 小–中 | 小–中 | 切口在 `hook.py` size=3 aux 直连 + `runtime.py` pack_aux；保留 parity/tiler 显式路径 |
| C2 hero_first 降权 | 小 | 小 | 删早退 + 加大 flat/dense 惩罚；**注意** hero_first 还缩 dense×0.35、改非 MCS 网格序，勿只删一行 |
| C3 hero SKU | 中 | 中（含 H1/H3/H4） | 4-hero YAML 已有，卡在 experimental/rollout=0/policy/schema/剪枝 |
| C4 burst 预分段 | 中 | **大** | 无 sceneId；全新窗口切分层；窗供给骤降风险 |
| C5 章级 reserve | 中 | 中–大 | 依赖 C1；state 加字段（`planner_state.py`） |
| C6 Studio 解释 | 中 | 中（含 H2） | 数据半成品；缺 API 与叙事映射 |
| D1 节奏 token | 中 | **2–4 天** | 放 preamble/overlays，**勿进 `@lte-generated` 段**（会被 sync 冲掉） |
| D2 beat 默认 | 中 | **1–2 天改默认** + 验证 | `default.yaml`/config `flat`→`classic_magazine`；进度逻辑已在 `beat_score_multiplier` |

### 4.2 建议落地序（相对 PRD 的三个调整）

1. **A 压缩为 3–5 人日一次做完**（A1→A2→A4→A3 机器门），不占满 1–2 周。
2. **B3 双预览提前**（A 后立即做）：便宜、先让「三模式差异」诚实可见，为 B2 的合同讨论提供实物依据；B1 ADR 同期起草；**B2 作为独立大项排期**，不与 C 抢同一人。
3. **C4 降级为二期或简化版**：先用「burst 链 + takenAt 间隔 + place.city」做粗分段（不发明 sceneId），观测 C1–C3 落地后 hero 曝光是否已达标，再决定是否要完整预分段。C 波主链 = **C1→C2→(H1/H3/H4)→C3→C5**，C6 与 C1 并行（先做 H2）。
4. D2 改默认可与 C 同 PR 周期启动（1–2 天）；D1 等设计定标。

### 4.3 回归风险清单（动工前先加/改测试）

| 改动 | 会碰碎 | 处置 |
|------|--------|------|
| C1 | `test_mosaic_density_budget.py`（断言窗序含 3）、`test_mosaic_s2`（3 竖图→portrait-3）、golden portrait-3 | 改断言 + 新增「奇数尾图不挂住」parity 单测 |
| C2 | 无「hero_first ⇒ skip」现有单测（行为空洞） | 新增降权行为测；观察 curated dense used 上升 |
| C3 | golden mosaic unified、配额测试 | 剪枝后重录 golden |
| B2 | longshot 全链（切分、breath、平台后处理） | 以 dogfood trip 双前后对比为准入 |
| A2 | 依赖静默归一的旧配置/测试 | 提供迁移错误信息（指出合法枚举） |

---

## 5. 建议的 PRD v1.0.1 修订项

1. §1.3/§7：修正模块路径（`layout_engine/mosaic/`）；注明 5 槽 hero 已 GA、缺口在 4 槽 hero + 剪枝。
2. R-C3：改写为「加 4-hero（转 GA、rollout&gt;0、入 schema 枚举、入 MOSAIC_4、同步 codegen）+ 从 15 剪至 ≤12（附剪枝候选清单待拍板）」。
3. R-C4：删去 `sceneId` 表述，改为「burst 链 + 时间间隔 + place.city 粗分段」，并标注为**可降级项**（视 C1–C3 后指标决定）。
4. R-C6/AC-C-05：增加前置「日志 window 级保留 Top3 reject」（H2）。
5. Wave A：改写 R-A1 为「sync drift 检查进 PR job + 分支保护 required（lint/test-pr/sync）+ 删除死代码 warn 分支」；R-A2 改写为「`layoutDensity` 等关键键非法值 → `ConfigError`」，并注明 `[5]` bug 已由 MCR 修复。
6. Wave B：注明 B2 推翻 ADR-003，需新 ADR；B3 可先行；present 跳票根现状与 R-B4 关系。
7. §14 推出与回滚：补 H5——demo fixture 入库/脱敏决策，否则 AC 基线在 CI 不可复现。
8. §8 D1：补「token 只放 preamble / overlays 源文件」的工程约束。

---

## 6. 需要负责人拍板的三个新决策

| # | 决策 | 选项 |
|---|------|------|
| N1 | 活跃集剪枝（C3 前置） | 建议：剪 `portrait-6` / `landscape-6` / 9 宫默认曝光，保 `portrait-4`/`landscape-4` 作显式 fallback（或反之，需产品定） |
| N2 | Demo fixture | ①脱敏入库小型 fixture trip（CI 可复跑）；②仅本机 dogfood + 发布清单（hobbyist 现状） |
| N3 | C4 范围 | ①一期完整预分段；②简化粗分段 + 指标观察后再定（**开发建议 ②**） |

---

## 7. 变更

| 日期 | 说明 |
|------|------|
| 2026-07-20 | 初稿：三路代码深查（MCS / 门禁 / 三模式）汇总的开发可实现性评审 |
