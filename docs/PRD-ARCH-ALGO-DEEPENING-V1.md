# Travelogue · 架构收敛与算法加深 V1（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue（核心管线 · 排版 · 策展） |
| **文档版本** | **v1.1.0-AAD** |
| **状态** | **Draft · 五席评审有条件通过 · BLK 已合入 · Ready for Kickoff（勾选 §12）** |
| **性质** | **收敛 + 加深 PRD**：基线修复 → 结构可维护性 → 排版搜索/打分代数升级；**非**新功能面 / 非模板商城 |
| **触发来源** | 2026-07-15 架构/算法专家审查；核心单测 **827 passed · 5 failed**；mosaic/beam 子集 **226 passed**；LSE cross-import **18**（目标 ≤10） |
| **目标分支** | `arch/algo-deepening-v1` → `master`（建议；可按里程碑拆 PR） |
| **关联文档** | [PRD-ARCH-OPTIMIZATION.md](./PRD-ARCH-OPTIMIZATION.md) · [ARCH-OPT-P2-BACKLOG.md](./ARCH-OPT-P2-BACKLOG.md) · [ARCH-OPT-STATUS.md](./ARCH-OPT-STATUS.md) · [PRD-ALGORITHM-OPTIMIZATION-V2.md](./PRD-ALGORITHM-OPTIMIZATION-V2.md) · [algorithm-inventory.md](./algorithm-inventory.md) · [adr/015-lse-planner-migration.md](./adr/015-lse-planner-migration.md) · [QUALITY-GATE.md](./QUALITY-GATE.md) · [TESTING.md](./TESTING.md) |
| **评审纪要** | [acceptance-records/aad-prd-review-2026-07-15.md](./acceptance-records/aad-prd-review-2026-07-15.md) |
| **承接关系** | **承接** ARCH-OPT **P2-A**（拆 `run_curate`）与 ADR-015 边数薄化；**不重开** Algorithm V2 封面 logit（已落地）；**不重开** Stable-QH / LCC / FTUE 体验债 |
| **更新日期** | 2026-07-15 |

> **一句话**：在 WS1 架构闸门已绿、审美/封面 V2 已落地的基础上，先修回归基线，再拆策展神函数与薄化耦合，最后把「伪 beam」升级为真搜索并统一 LayoutUtility——用可验收的里程碑把成片质量与可改性一起抬高。

---

## 0. 读者指南

| 角色 | 读什么 |
|------|--------|
| 产品 | §1–2 · §5 成册收益 · OUT 表 · 盲评维度 |
| 架构 / 开发 | §3–4 · §6–7 · AC 自动化 · WIP |
| 算法 | §4.3–4.5 · §8 holdback · AC 盲评 |
| 测试 | §1.2 证据 · §7 AC · 回滚 · 等价定义 |

**范围承诺**

| 承诺 | 说明 |
|------|------|
| 分波交付 | WS-A（基线）可独立合入；WS-B / WS-C 各拆 PR，禁止大爆炸 |
| 等价优先（WS-B） | 拆分/薄化默认 **零 intentional 版式变更**；须 **curate baseline replay / golden 签名 A/B**（自反脚本仅作确定性烟测） |
| 可感知加深（WS-C） | 真 beam / 统一打分允许成片差异，但须 holdback 盲评门禁，默认 **feature flag 关** 至 Go |
| 证据驱动 | 每里程碑：复现命令 + 通过证据 + 回滚说明 |
| **两本账** | 对外成功故事 = 成册节奏/拼图收益；边数/壳行数 = **工程闸门**，不作用户/changelog 主叙事 |
| **G-AAD-WIP** | 与 FTUE/体验债冲突时 **体验债优先**；默认可先交付 M1+M2(+M3) 切片，M5–M7 不与 FTUE P0 同迭代 |

### 0.1 v1.0 → v1.1 变更摘要（五席 BLK）

| 来源 | 合入要点 |
|------|----------|
| BLK-01 | Utility = `soft × Π(1−w·p)`；章/窗分层；soft 尺度冻结 |
| BLK-02 | CLI 合同扩至 `_resolve`；Option 默认 `None`；Studio 永不宽松 |
| BLK-03/04 | 等价=A/B replay；AC-04 钉死全绿或 nodeids |
| BLK-05/11 | 成册收益卡 + holdback 产品化；黑话禁用户面 |
| BLK-06/07 | 18→≤10 叙事；kernel 仅 combine；修 ADR-015 链接 |
| BLK-08 | Geo **Parking**；审美降为 lint |
| BLK-09/12 | 状态键写全；M2 估时 5–8d；AC-20 剔除字段 |

---

## 1. 背景与审查证据

### 1.1 定位

项目已过「堆 Phase 证明能做」阶段：

- 分层 + import-linter、统一 `run_trip`、`layout_contract` kernel、Mosaic 统一入口 `compose_trip` 已就位。
- Algorithm V2 已修封面/英雄 logit 与清晰度等结构性短板。
- Stable-QH / LCC 已收口 Studio 信任债。

当前瓶颈转为三类：

1. **基线可信度**：迁移后少量测试/CLI 契约漂移 → 红灯掩盖真实风险。
2. **结构可改性**：`curate` / `screen_planner` / `ingest` 等 god module + `curation→layout_engine` 18 边 → 改排版成本高。
3. **算法搜索深度**：「beam」实为贪心计划的少量变体重排，搜索空间过窄；加性 layout 分与乘性 mosaic 惩罚口径分裂。

### 1.2 自动化快照（2026-07-15）

| 套件 | 结果 |
|------|------|
| `pytest tests/unit/layout_engine tests/unit/curation tests/unit/media -q --maxfail=5` | **827 passed · 5 failed · 4 skipped** |
| `pytest tests/unit/layout_engine -k "mosaic or beam or …"` | **226 passed** |
| `pytest` geo / phash / photo_cull 定向 | **49 passed** |
| `python -m importlinter.cli lint-imports` | **EXIT 0** |
| `python scripts/lse_cross_import_stats.py` | **layout_engine→curation: 0** · **curation→layout_engine: 18** · total **18** |

> **边数叙事（v1.1）**：WS1 结案时曾以 ≤10 / 7～8 边表述达标；shim 退役后 AST **显式化为 18**（非新耦合）。本波 As-Is=**18**，棘轮 ceiling=baseline（只降不升），**goal≤10** 为 M3 验收目标——二者勿混。不重开 M-B4b，只做 adapter 白名单薄化。

### 1.3 五失败归因

| # | 测试 | 判定 | 根因 | 修复归属 |
|---|------|------|------|----------|
| F01 | `test_lte_p4_gaps::test_legacy_generated_matches_codegen` | **CONTRACT** | 仍断言 `travelogue/curation/mosaic/_legacy_generated.py`；实现已在 `layout_engine/mosaic/` | **AAD-01** |
| F02–F05 | `test_cluster_cli`（cache-clear / pending / process-pending×2） | **CODE** | `cluster.py` 始终传入 `trips_dir=ctx.trips_root`，触发 `resolve_trip_json` 沙箱；**绝对路径 trip.json** 被拒 → `E_TRIP_NOT_FOUND` | **AAD-02** |

### 1.4 热点规模（行数 · 2026-07-15）

| 模块 | 约行数 | 角色 |
|------|--------|------|
| `curation/curate.py` | ~1631 | 策展编排神模块 |
| `layout_engine/planner/screen_planner.py` | ~1400 | 贪心组屏 + 特例 |
| `media/ingest.py` | ~1366 | 摄取粘合 |
| `curation/curate_scoring.py` | ~1337 | 封面/英雄打分 |
| `curation/aesthetic_score.py` | ~947 | PA 五维 + 用途投影 |
| `layout_engine/planner/beam_scoring.py` | ~752 | 章计划加性打分 |
| `layout_engine/mosaic/scorer.py` | — | 屏级乘性惩罚（已合理） |

### 1.5 算法 As-Is（关键洞察）

| 能力 | As-Is | 问题 |
|------|-------|------|
| 「Beam」 | `generate_day_bucket_candidates` 对贪心 planner 枚举 ≤`beam_width` 个**完整**变体（hero/mosaic 开关），再 `score_screen_plan` 选优 | **名实不符**；不扩展部分假设；搜索空间过窄 |
| Layout vs Mosaic 分 | 加性加权 vs `base × ∏(1−p_i)` | 同一资产跨路径「好坏」不可比 |
| Geo 分段 | Haversine + 自适应 p75/p90 时间间隙 | 时/空未联合；小段 merge 偏张数阈值 |
| 审美多轨 | rules / ToPIQ / MLLM / U-* / cullScore | 下游读字段不一，用户改封面难回流 |
| 增量打分 | `IncrementalScoreState` 已存在 | 真前缀扩展未强制使用 |

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 | 主要 AC |
|----|------|---------|
| **G-AAD-01** | 核心单测基线可信：本 PRD 列出的 5 失败清零；CLI 接受绝对/`trip.json` 路径与显式 `--trips-dir` 沙箱语义分离 | AC-AAD-01～03 |
| **G-AAD-02** | `run_curate` 变为显式 stage 编排壳 **≤80 行**；各 stage 可单测；行为等价门禁绿 | AC-AAD-10～12 |
| **G-AAD-03** | `curation → layout_engine` 静态边 **≤10**（棘轮只降不升）；LE→curation 保持 0 | AC-AAD-13 |
| **G-AAD-04** | 真·章内 beam（或等价 DP）：状态为「已放置前缀 + 剩余资产」；默认 flag 关；开启后 holdback 不劣于对照 | AC-AAD-20～24 |
| **G-AAD-05** | 统一 **LayoutUtility** 代数：软分 × 硬惩罚积；beam 与 mosaic 共用契约 | AC-AAD-25～26 |
| **G-AAD-06** | 审美用途读口治理：热点路径经 `purpose_overall`；本波以 **lint/allowlist** 落地（不新建 facade） | AC-AAD-30 |
| **G-AAD-07** | ~~Geo 联合切分~~ → **Parking**（见 §11）；本波不进 DoD | — |

### 2.2 非目标

| # | 排除 | 理由 |
|---|------|------|
| OUT-01 | 新模板 / 模板商城 / 多皮肤运营 | 产品策略冻结 |
| OUT-02 | 重开封面 logit / sharpness v2 主方案 | Algorithm V2 已落地 |
| OUT-03 | LSE 默认开启 / 权重大调参上量 | LSE CAP FROZEN |
| OUT-04 | 云同步、账号、协作编辑 | 本地优先 |
| OUT-05 | 全量 Typed domain 一次到位 | 仅热点路径可机会主义引入 |
| OUT-06 | 配置面大删减 / 场景预设产品化 | 可记 Parking；不进本波 DoD |
| OUT-07 | 用户 preference 在线学习闭环（生产） | 本波最多落 **日志 schema 草案**（Parking） |
| OUT-08 | Docker / 云部署 | 非本波 |
| OUT-09 | 顺手大拆 `ingest.py` / `cover_engine` | 非阻塞；机会主义 |
| OUT-10 | Stable-QH / LCC / FTUE 体验项 | 已另 PRD |
| OUT-11 | Geo 联合切分 / αβ 网格（原 AAD-23） | 五席 Parking；避免污染版式 holdback 归因 |
| OUT-12 | 新建审美 facade API | 与既有 `purpose_overall` 重复；本波仅 lint |

---

## 3. 问题清单（工作项 ID）

| ID | 优先级 | 工作流 | 问题 | 证据锚点 |
|----|--------|--------|------|----------|
| **AAD-01** | P0 | WS-A | LTE 快照路径测试滞后 | `tests/unit/layout_engine/test_lte_p4_gaps.py` L44 |
| **AAD-02** | P0 | WS-A | cluster CLI 绝对路径被 trips 沙箱误伤 | `cli/cluster.py` · `TripService.resolve_trip_json` |
| **AAD-03** | P1 | WS-A | `algorithm-inventory` / 相关文档路径与代码树不同步（mosaic 已迁） | `docs/algorithm-inventory.md` |
| **AAD-10** | P1 | WS-B | `run_curate` god function（承接 ARCH-OPT P2-A） | `curation/curate.py` |
| **AAD-11** | P1 | WS-B | curation→LE 18 边过厚 | `scripts/lse_cross_import_stats.py` |
| **AAD-12** | P2 | WS-B | `screen_planner` 特例堆叠，难扩展 | `planner/screen_planner*.py` |
| **AAD-13** | P2 | WS-B | import-linter 登记的 media/vision→curation 美学债（可选本波薄化） | `pyproject.toml` ignore_imports |
| **AAD-20** | P1 | WS-C | 伪 beam → 真前缀搜索 | `layout_candidates.py` · `mosaic/search.py` |
| **AAD-21** | P1 | WS-C | LayoutUtility 统一 | `beam_scoring.py` · `mosaic/scorer.py` · `layout_contract` |
| **AAD-22** | P2 | WS-C | 审美用途读口 lint（不新建 facade） | `aesthetic_score.purpose_overall` |
| **AAD-23** | — | Parking | Geo 时×空联合切分（本波不做） | `geo_events.py` |

---

## 4. 技术方案（纲要）

### 4.1 WS-A · 基线修复（零版式意图变更）

#### AAD-01 · LTE 快照路径

- 断言路径改为 `travelogue/layout_engine/mosaic/_legacy_generated.py`（或现 codegen 权威路径）。
- 若快照文件由脚本生成：CI/`scripts` 入口与文档一句同步。

#### AAD-02 · CLI 路径语义

**合同（冻结 · v1.1 三态）**

| 调用 | 行为 |
|------|------|
| CLI `cluster` / `_helpers._resolve` 等，**未**显式传 `--trips-dir`（Option 默认 **`None`**） | 按文件存在性解析绝对/相对 `trip.json`；**不**注入 `trips_dir=` 沙箱支 |
| 显式 `--trips-dir` | 启用沙箱：禁止 `..` / 逃逸；trip id 或相对路径须在该根下 |
| Studio / HTTP / 导入 | **永不**走宽松支；用户输入路径保持现行 trips 根沙箱（安全面不回退） |

实现要点：

- 修复面：**`cli/cluster.py` + `cli/_helpers._resolve`**（同类 `or ctx.trips_root`）；pipeline 等 `Option(Path("trips"))` 默认改为可区分「未传」vs「显式」。
- trip id 解析可用 `ctx.trips_root` 拼路径，但调用 `resolve_trip_json` 时 **`trips_dir=None`**（除非用户显式传入）。
- 风险边界：宽松模式 = **信任本地操作者**可读任意 `trip.json`（非远程 SSRF）；不静默扩大资产路径跟随范围。

#### AAD-03 · 文档对齐

- 更新 `algorithm-inventory.md` 中 mosaic/planner 路径。
- README / ARCH-OPT-P2 交叉链接本 PRD。

### 4.2 WS-B · 架构收敛

#### AAD-10 · 拆解 `run_curate`（P2-A）

建议 stage（可沿用已有 dataclass）：

```text
preflight → refresh/cull/cohort → aesthetic_align
  → build_buckets → build_chapters/cover_hero
  → mosaic_compose / attach → metrics_persist
```

| 约束 | 值 |
|------|-----|
| `run_curate` 壳 | ≤80 行（编排 + 错误边界；不计纯 import） |
| 行为 | 默认等价；**baseline replay / golden 签名 A/B** + 既有 mosaic compose 单测 |
| 估时 | **5–8 人日**（含测试侧签名钉死） |
| PR | **独立 PR**；不与真 beam 混提；合并后 cur→LE 边数 ≤ 合并前 baseline |

#### AAD-11 · Cross-import 薄化

- As-Is **18** → goal **≤10**；棘轮 ceiling=当前 baseline（只降不升）。
- 白名单：优先 `curate` → `layout_engine.adapter`（+ 必要时 `compose_trip`）；消灭 `chapter_items` / `layout_planner` / `moment_scoring` 等外设直连。
- 可选分档：M3a `18→≤14` → M3b `≤10`。
- `layout_engine → curation` 保持 **0**；禁止恢复 curation shim。

#### AAD-12 · Planner 策略注册（机会主义）

- 将高频 `if patternId` 抽为注册表；**本波不做全量重写**。
- 验收：至少抽出 1 组 mosaic/portrait 特例且单测覆盖；禁止净增无注册特例。

### 4.3 WS-C · 真 Beam 搜索（AAD-20）

#### 命名

| 名称 | 含义 |
|------|------|
| **VariantRerank**（现行） | 完整贪心计划变体重排；保留为默认 / 降级路径 |
| **PrefixBeam**（本波新增） | 对「screen 前缀 + 剩余资产」做宽度为 B 的搜索 |

#### 状态与扩展（M0 冻结）

```text
state = (
  cursor, remaining_suffix_hash,
  rhythm_state_tuple,          # nine_used / streak / last_kind 等可哈希字段
  last_pattern_id, pattern_streak,
  carry_portrait_sig,
  chapter_index, hero_bits,
)
```

- **扩展**：仅 mosaic candidates 已过硬门的 screen；`B≤beam_width`；耗尽 → VariantRerank。  
- **打分**：章级 **LayoutUtility soft** + 强制 `IncrementalScoreState`（缓存键与前缀 state 一致）。  
- **预算**：复用 `SearchBudget`；`decisionLog.fallbackReason` 必填。  
- **开关**：`layout.prefix_beam.enabled`（最终键名 M0 确认）；默认 **false**。  
- **确定性**：`deterministic_strict` 下候选排序稳定。

#### 与 Mosaic 关系

- **窗级**：硬惩罚选屏（现网 MCS，含 `w·p`）。  
- **章级**：soft 仅跨屏维；硬罚作准入/诊断，**默认不进章级 Π**（防双重计数）。  
- 禁止并行第二套互斥硬规则 / 第二套 `score_*` 长期双实现。

### 4.4 WS-C · LayoutUtility（AAD-21）

统一代数（**实现留 `layout_engine`**；`layout_contract` **仅**纯 combine + DTO）：

```text
utility = soft × Π_i (1 − clamp01(w_i) · clamp01(p_i))
soft    = clamp01(score_screen_plan.total)   # 或 M0 书面替代
```

| 层 | 职责 |
|----|------|
| `layout_contract.combine_utility` | 纯函数 combine + `UtilityBreakdown` DTO |
| soft 维 | 现 beam 跨屏加性维（`beam_scoring`） |
| 硬惩罚表 | 与 `MosaicConfig.penalties` 同源（脸裁切 / 主槽 AR / 连拍密度等） |
| post_multipliers | rhythm/LTE/beat 等：M0 二选一是否进章级 utility，写入 AC |

**迁移**：VariantRerank 先薄包装双跑（winner 一致率建议 ≥95%）再切；decisionLog **保留 `score`，新增 `utility`**。挂 `lint_layout_contract_surface`。

### 4.5 WS-C · 审美 lint（AAD-22）；Geo Parking

**审美**：热点路径 lint/allowlist，强制经 `purpose_overall`；**不新建** facade。  

**Geo（AAD-23）**：**Parking**——本波不改切分；最多只读日志记 Δt/Δd。独立狗粮单再开 flag PR。
---

## 5. 用户 / 产品可感知影响

### 5.1 成册收益卡（WS-C Go 后 · 白话 · 禁工程黑话）

对用户 / release note / dogfood 只用下列表述（或等价白话），**禁止**出现 PrefixBeam / LayoutUtility / plannerPath：

1. 少「连续好几屏长得一样」的呆板节奏  
2. 拼图主图更少脸被裁切 / 画幅拧巴  
3. 章英雄与封面更稳、更贴「杂志选图」  
4. 跨城/同城段边界更贴旅行叙事（若未来 Geo 波次开启；本波不承诺）  
5. 出问题可关「排版搜索加深」开关回退（内部 flag）

### 5.2 感知矩阵

| 波次 | 用户是否可感知 | 沟通 |
|------|----------------|------|
| WS-A | 否（CLI/测试）；修复后 dogfood 用绝对路径 cluster 不再误报 | release note 可选 |
| WS-B | 默认否（等价） | 开发者可见 |
| WS-C flag 关 | 否 | — |
| WS-C flag 开 | **是**（版式节奏/拼图选择可能变好或变化） | dogfood + 盲评通过后才考虑默认开；release note **仅白话** |

**可接受差异（仅 WS-C Go 后）**

| # | 差异 | 条件 |
|---|------|------|
| DIFF-AAD-01 | 同相册屏序/pattern 分布变化（预览/长图可能「换一版拼法」） | PrefixBeam 开启且 holdback 不劣 |
| DIFF-AAD-02 | decisionLog `plannerPath` 新增 `prefix_beam`；另有 `utility` 字段 | 遥测兼容旧枚举；用户面不可见 |
| DIFF-AAD-03 | Geo 段边界微调 | **本波不适用**（Geo Parking） |

---

## 6. 里程碑与排期

| 里程碑 | 内容 | 估时 | 依赖 |
|--------|------|------|------|
| **M0** | Kickoff：冻结 CLI 路径合同、LayoutUtility 公式、flag 名；确认 holdback 相册集 | 0.5d | — |
| **M1** | WS-A：AAD-01/02/03；5 失败清零 | 0.5–1d | M0 |
| **M2** | WS-B：AAD-10 `run_curate` 拆分 + **A/B 签名等价** | **5–8d** | M1 |
| **M3** | WS-B：AAD-11 边数棘轮（可选 18→14→≤10） | 1–2d | M2 可并行起步 |
| **M4** | WS-C：AAD-21 LayoutUtility（VariantRerank 先切换） | 2–3d | M1 |
| **M5** | WS-C：AAD-20 PrefixBeam + 预算/降级 + 单测 | 4–6d | M4（**分 PR**） |
| **M6** | WS-C：AAD-22 审美 lint（半天～1d）；~~Geo~~ 取消 | 0.5–1d | M1 |
| **M7** | Holdback 盲评 + acceptance-record + Go/No-Go 默认开关决议 | **2–4d** | M5 |

**合计（可并行）**：约 **14–22 人日**（含测试侧）。小团队建议：**M1 → (M2 与 M4 谨慎并行或 M4 先) → M3 → M5 → M6 → M7**；与 FTUE 冲突时砍到 M1+M2(+M3)。

### PR 切分建议

| PR | 内容 | 合并门禁 |
|----|------|----------|
| PR1 | M1 基线（含 `_resolve` / Option 默认） | 定向单测绿 + AC-03 负例 |
| PR2 | M2 curate 拆分 | **replay/golden A/B** + curate/mosaic 单测 |
| PR3 | M3 cross-import | lint 棘轮；边数 ≤ 目标档 |
| PR4 | M4 Utility | 双跑 winner 一致率 + 旧路径包装 |
| PR5 | M5 PrefixBeam（默认关） | 搜索单测 + budget 降级 |
| PR6 | M6 aesthetic lint | lint 绿 |
| PR7 | M7 文档/结案；若 Go 再另 PR 默认开 | 盲评记录 |

---

## 7. 验收标准（AC）

### 7.1 WS-A

- [ ] **AC-AAD-01** `test_lte_p4_gaps::test_legacy_generated_matches_codegen` passed
- [ ] **AC-AAD-02** `tests/unit/curation/test_cluster_cli.py` 全绿（含绝对路径 tmp trip.json）
- [ ] **AC-AAD-03** 显式 `--trips-dir` 时，逃逸绝对路径仍 `E_TRIP_NOT_FOUND`（**自动化负例**）；Studio/HTTP 沙箱不变量 1 正 1 反
- [ ] **AC-AAD-04** `pytest tests/unit/layout_engine tests/unit/curation tests/unit/media -q` **exit 0**（或 `docs/acceptance-records/aad-must-green-nodeids.txt` 钉死列表 exit 0）；禁止「失败类」空话

### 7.2 WS-B

- [ ] **AC-AAD-10** `run_curate` 编排壳 ≤80 行（度量口径写入 PR 描述）
- [ ] **AC-AAD-11** 各 stage 至少 1 个单位测试或既有测试改挂新符号
- [ ] **AC-AAD-12** **curate baseline replay / golden 签名 A/B** 通过（自反 `arch_equivalence_check` 仅烟测，不作唯一等价证明）
- [ ] **AC-AAD-13** `lse_cross_import_stats`：LE→cur=0；cur→LE **≤10**；baseline 已更新且棘轮生效（禁止假压 baseline）

### 7.3 WS-C

- [ ] **AC-AAD-20** PrefixBeam 默认 **关闭** 时，与 VariantRerank 产物签名等价；**剔除字段集** M0 冻结（至少含可变 `utility` / 时间戳；`plannerPath` 策略写明）
- [ ] **AC-AAD-21** 开启后：预算耗尽必降级且 `decisionLog` 含 `fallbackReason`
- [ ] **AC-AAD-22** `deterministic_strict=true` 时同输入两次屏签名一致
- [ ] **AC-AAD-23** 前缀扩展路径调用 `IncrementalScoreState` 且缓存键与 state 前缀一致（探针）
- [ ] **AC-AAD-24** Holdback：N≥8 且含多样性（短途/长途、人像/风景、跨城各至少覆盖）；维度=节奏、拼图合理性、章英雄；有否决样例；记录入 `docs/acceptance-records/`；**平局≠默认开**
- [ ] **AC-AAD-25** LayoutUtility：`(1−w·p)` + 章窗分层；`weights_hash` 变更可测；`lint_layout_contract_surface` 绿
- [ ] **AC-AAD-26** 禁止新增平行打分入口（lint 或评审清单）
- [ ] **AC-AAD-30** 热点路径 lint：封面/英雄/solo/moment 经 `purpose_overall`
- [ ] ~~AC-AAD-31/32 Geo~~ → **取消（Parking）**

### 7.4 手测 / 狗粮

| ID | 场景 | 期望 |
|----|------|------|
| UX-AAD-01 | CLI `cluster cache-clear` 指向临时 trip.json | OK，无 E_TRIP_NOT_FOUND |
| UX-AAD-02 | Studio 导入 → 成册（flag 关） | 观感与合入前无 intentional 回退 |
| UX-AAD-03 | PrefixBeam dogfood（flag 开） | 对照 §5.1 收益卡；无连续同 pattern 失控；可关旗回滚 |

---

## 8. Holdback 与 Go/No-Go（M7）

| 门 | 条件 | No-Go |
|----|------|-------|
| **Gate-R** Reliability | AC-AAD-01～04、13；import-linter 绿 | 禁止合入 WS-C 默认开 |
| **Gate-E** Equivalence | AC-AAD-12（A/B）、20 | 禁止宣称「无行为变更」 |
| **Gate-Q** Quality | AC-AAD-24 按产品维度卡 **不劣** 且无否决样例命中 | PrefixBeam **保持默认关**；代码可合入 |

盲评协议（v1.1）：

1. 对照 = 现行默认；实验 = PrefixBeam on。  
2. N≥8 + 多样性约束；评委至少开发 1 + 产品 1；平局第三人破平或记「不劣但不开默认」。  
3. 维度：节奏连贯、拼图合理性、章英雄；各至少 1 条否决样例。  
4. **平局 ≠ Gate-Q 放行默认开**；默认开须另 PR + 白话 release note。  
5. 记录：`docs/acceptance-records/aad-holdback-YYYY-MM-DD.*`

---

## 9. 风险与回滚

| 风险 | 影响 | 缓解 |
|------|------|------|
| 拆 curate 行为漂移 | 成片回归 | A/B replay + 独立 PR；可回滚单 PR |
| PrefixBeam 超时/质量不稳 | 卡顿或怪版式 | 默认关；预算硬顶；降级 VariantRerank |
| Utility 切换分数尺度变化 | 选屏抖动 | 双跑 winner 率；保留 `score` 字段 |
| CLI 宽松扩大本地任意 trip.json | 信任边界 | Studio 永不宽松；合同三态 AC |
| 范围膨胀 / FTUE 抢容量 | 排期失控 | OUT + G-AAD-WIP |
| 章级硬罚双重计数 | 选屏畸变 | BLK-01 分层合同 |

**回滚**

- WS-A：revert PR1。  
- WS-B：revert 拆分 PR；shim 不恢复。  
- WS-C：关 flag 即回现行；代码可留。

---

## 10. 开放问题（Kickoff 定案 · v1.1）

| # | 问题 | 定案 | Owner |
|---|------|------|-------|
| Q-00 | Utility 公式与章窗分层 | **`(1−w·p)` + 章窗分层**（§4.4） | 算法 |
| Q-01 | PrefixBeam 默认开启时机 | 本波默认关；默认开另 PR | 产品+算法 |
| Q-02 | Holdback N / 评委 | N≥8+多样性；开发1+产品1；平局破平或不作为默认开依据 | 产品 |
| Q-03 | decisionLog 字段 | 保留 `score`，新增 `utility` | 开发 |
| Q-04 | AAD-13 美学 ignore | **Parking** | 架构 |
| Q-05 | Geo α/β | **关闭 · Parking** | 算法 |
| Q-06 | CLI Option 默认 | 默认 `None`=宽松；显式才沙箱 | 开发 |

---

## 11. Parking Lot（明确不进 DoD）

- **AAD-23 Geo 联合切分 / αβ 网格**  
- 用户改封面 → pairwise preference → 权重校准闭环  
- 配置「场景预设」替代裸权重旋钮  
- Typed `Asset`/`Chapter`/`Screen` 全量  
- `ingest.py` / `cover_engine` 大拆；AAD-13 清 ignore  
- ΔE76→ΔE2000；真 DP 全局最优  
- PrefixBeam **默认开启**；整本 layout 盲评全自动 harness  

---

## 12. Kickoff 检查清单

- [ ] 确认本 PRD 承接 P2-A；评审纪要 BLK-01～12 已反映在 v1.1  
- [ ] 冻结 CLI 三态（§4.1）与 LayoutUtility 公式（§4.4）与状态键（§4.3）  
- [ ] 冻结 holdback 相册清单 / 剔除字段集 / AC-04 定义  
- [ ] flag 键名写入 `config.yaml.example`（默认 false）  
- [ ] 书面 G-AAD-WIP（对 FTUE 串行或砍 scope）  
- [ ] 指定目标分支与 PR1 assignee  
- [ ] 架构 / 算法 / 测试 书面 Ready for Kickoff  

---

## 13. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0.0-AAD | 2026-07-15 | 初稿：三工作流 WS-A/B/C + AC/里程碑 |
| v1.1.0-AAD | 2026-07-15 | 合入五席 BLK-01～12；Geo Parking；Utility/CLI/等价/holdback/WIP 重写 |

---

## 附录 A · 与既有 PRD 边界

| 文档 | 关系 |
|------|------|
| [PRD-ARCH-OPTIMIZATION](./PRD-ARCH-OPTIMIZATION.md) | WS1 多已 Done；本 PRD **执行其后 P2-A 与边数目标** |
| [ARCH-OPT-P2-BACKLOG](./ARCH-OPT-P2-BACKLOG.md) | P2-A 升格为本 PRD M2；P2-B 锁若已在其他分支落地则本 PRD 不重复 |
| [PRD-ALGORITHM-OPTIMIZATION-V2](./PRD-ALGORITHM-OPTIMIZATION-V2.md) | 封面 logit 等 **不再重做**；本波补搜索与打分代数 |
| [PRD-PHASE15 / mosaic](./PRD-PHASE15-photo-mosaic-evolution.md) | 窗级 mosaic 保留；章级 PrefixBeam 为其上层 |
| [PRD-STABLE-QUALITY-HARDENING-V1](./PRD-STABLE-QUALITY-HARDENING-V1.md) | 正交；不混范围 |

## 附录 B · 关键命令（实施期）

```bash
# 基线
python -m pytest tests/unit/layout_engine/test_lte_p4_gaps.py tests/unit/curation/test_cluster_cli.py -q

# 分层与交叉边
python -m importlinter.cli lint-imports
python scripts/lse_cross_import_stats.py

# 等价（WS-B）
python scripts/arch_equivalence_check.py

# 算法子集
python -m pytest tests/unit/layout_engine -k "mosaic or beam or scorer or search" -q
```
