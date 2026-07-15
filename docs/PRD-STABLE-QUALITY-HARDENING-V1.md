# Travelogue · 稳定期质量硬化与体验优化 PRD

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue（Studio + 管线 + 长图） |
| **文档版本** | **v1.1.0-STABLE-QH** |
| **状态** | **Ready for Kickoff**（六席评审阻塞项已合入；[评审纪要](./acceptance-records/stable-qh-prd-review-2026-07-15.md)） |
| **性质** | **稳定期还债 PRD**：契约对齐 + 正确性修复 + 体验硬化；**零 intentional 新功能** |
| **触发来源** | 2026-07-15 首席质量/UX 审查；`tests/unit/web` **16 失败归因**；六席评审 BLK-01..08 |
| **目标分支** | `fix/stable-quality-hardening-v1` → `master` |
| **关联文档** | [PRD-COVER-STYLES-V6.md](./PRD-COVER-STYLES-V6.md) · [PRD-BOOKENDS-ENGINE-V1.md](./PRD-BOOKENDS-ENGINE-V1.md) · [PRD-HELP-ONBOARDING-V1.md](./PRD-HELP-ONBOARDING-V1.md) · [PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1.md](./PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1.md) · [PRD-UX-TRUST-V1.md](./PRD-UX-TRUST-V1.md) · [PRD-STUDIO-HOMEPAGE-v2.1-OPTIMIZATION.md](./PRD-STUDIO-HOMEPAGE-v2.1-OPTIMIZATION.md) · [QUALITY-GATE.md](./QUALITY-GATE.md) · [TESTING.md](./TESTING.md) |
| **评审纪要** | [acceptance-records/stable-qh-prd-review-2026-07-15.md](./acceptance-records/stable-qh-prd-review-2026-07-15.md) |
| **验收配套** | 本文 §10；落地后补 `ACCEPTANCE-STABLE-QUALITY-HARDENING-V1.md` |
| **更新日期** | 2026-07-15 |

---

## 0. 文档说明

### 0.1 定位

项目进入稳定期：短期内不加功能。本 PRD 把「测试红灯 + 实机 UX 审查」收敛为**可排期、可验收、可回滚**的工作包。

两类债：

1. **契约漂移债**：产品已演进（V6 封面、Bookends、L0 文案、路由扩展），测试/schema 未跟进 → 红灯与假安全感并存。
2. **体验正确性债**：旁路上传丢字段、清点失败假进度、取消半成品、stub 观感弱 → 用户信任损伤。

### 0.2 范围承诺

| 承诺 | 说明 |
|------|------|
| **零 intentional 新功能** | 不新开模板商城、账号云同步、小程序 P2、LSE 上量、未完成书架态（方案 B）、可打断长图运行时 |
| **修复优先于重构** | 最小 diff；禁止顺手大拆 `run_curate` |
| **证据驱动** | 每里程碑：复现命令 + 通过证据 + 回滚说明 |
| **测试与产品双真相** | 故意改文案/默认值时，**同步改 AC 与单测**；禁止只改测试糊弄 |
| **假红清完 ≠ 体验完成** | M1+M2 后**下一合并窗必须含 M3**（QH-03/04/05） |

### 0.3 非目标

| # | 排除项 | 理由 |
|---|--------|------|
| OUT-01 | LONGSHOT 2.0 功能面 | 独立 PRD / 分支 |
| OUT-02 | LSE 权重调参 / 默认开启 | 观感路线图已冻结 |
| OUT-03 | Phase 22 全量 CacheRegistry / incremental | 仅做 schema 最小补齐 |
| OUT-04 | 手机端 Studio 工作台 | 产品策略仍为 ≥1024 |
| OUT-05 | 桌面 Gate B/C 签名与商店 | 本 PRD 只要求 Gate A 反馈入口立项勾选 |
| OUT-06 | 长图 Job **真协作取消** | 本期仅诚实文案（§7.4） |
| OUT-07 | 取消方案 B（未完成书架 / 断点续跑） | 属新 IA；另立 PRD |
| OUT-08 | 章节命名完整模板体系 | 归 CHAPTER-NAMING；本期仅禁「日期·二」类最伤标题 |
| OUT-09 | 客户端 `expectedRevision` | ADR-008 / Phase22 归档债，不进本波 P1 |

### 0.4 v1.0 → v1.1 变更摘要（评审合入）

| 来源 | 合入要点 |
|------|----------|
| BLK-01 | Schema **扫描施工**；补 `bookendsDegraded` / `closingUserPicked`；SoftWarnings 结构化 |
| BLK-02 | `featuredDetected` 根因写死为 disk-intent 优先冲突；intent flush / folders 深合并 |
| BLK-03 | 取消 **定案 A（约束版）**；previewable 谓词 + `purge_trip` + 确认人话 |
| BLK-04 | Help / UX-Trust **正式 supersede**；`HELP_COPY` 为 SSOT |
| BLK-05 | 全链路 stale 词表（含 Dock「已过期」同族化） |
| BLK-06 | 设置描述与 AI 入口一致（入口或改句二选一） |
| BLK-07 | 旁路 AC **成册结果可感知** |
| BLK-08 | 清点四态（含超时/降级） |
| 改进项 | 估时修正；QH-07/QH-13 收口；M4 瘦身；dogfood 扩写；上传 temp 并入取消 |

---

## 1. 背景与审查证据

### 1.1 自动化快照（2026-07-15）

| 套件 | 结果 |
|------|------|
| `tests/unit/config/test_config_fail_loud.py` | **5 passed** |
| `tests/unit/web` + `config`（首轮） | **568 passed · 16 failed · ~10.5 min** |
| 同 16 条定向复跑 | **12 failed · 4 passed**（Playwright/drill 偶绿） |

### 1.2 实机走查摘要

- Studio 首页 / 能力卡 / 导入向导 / 窄屏 Unsupported / 预览工具栏 / 设置：主路径可用。
- 预览 stub 文案工程腔明显；「长图可更新」角标噪声；设置暴露 G1/beam 术语。
- 旁路上传字段与清点失败态：代码审查确认 P0。

### 1.3 六席评审结论

**有条件通过** → 本 v1.1 消化全部 B0 阻塞项后 **Ready for Kickoff**。分席细节见 [评审纪要](./acceptance-records/stable-qh-prd-review-2026-07-15.md)。

---

## 2. 十六失败逐条归因

> 复跑口径：`pytest <nodeid> --tb=short`（2026-07-15）。  
> **判定**：`CODE` = 产线正确性缺口；`CONTRACT` = 产品已变、测试/schema 滞后；`FLAKE` = 环境/时序偶发；`ISOLATION` = 测试隔离不足。

| # | 测试 | 复跑 | 判定 | 根因（一句话） | 产品真相源 | 修复方向 |
|---|------|------|------|----------------|------------|----------|
| F01 | `test_help_copy_contract_locked` | ❌ | **CONTRACT** | 锁定文案仍要求旧短句；实现已为 L0 长句 | L0 · `HELP_COPY.firstSuccessNext` | **改测 + SSOT**；正式 supersede Help（§6.2 / R-QH-04） |
| F02 | `test_first_success_scheme_a` | ❌ | **CONTRACT** | HTML 内联 hint 与旧合同不一致 | 同上 | 与 F01；HTML 跟 `HELP_COPY` |
| F03 | `test_v4_preview_toolbar_playwright_smoke` | ✅偶 | **FLAKE** | Playwright 时序/端口 | Phase5 toolbar | `playwright_serial`；勿堵 PR 快测 |
| F04 | `test_v3_mobile_keeps_bottom_sheet` | ✅偶 | **FLAKE** | 同上 | 同上 | 同 F03 |
| F05 | `test_build_entry_includes_cover_opening_style` | ❌ | **CONTRACT** | 期望 raw `magazine-head`；resolved → `folio-overlap` | Cover V6 | 断言 resolved + raw / legacyMapped |
| F06 | `test_build_entry_cover_opening_style_defaults_card_br` | ❌ | **CONTRACT** | 默认已是 `veil-footer` | V6 `_DEFAULT_STYLE_ID` | 断言 `veil-footer` |
| F07 | `test_homepage_v21_no_internal_terminology…` | ❌ | **CONTRACT+PRODUCT** | 禁止「长图待更新」；Help/深链仍用 | Homepage v2.1 · Help | 全链路改「长图可更新」（§6.2） |
| F08 | `test_pipeline_default_place_passes_schema` | ❌ | **CODE** | Bookends 写入键未进 schema | Bookends §5 | **扫描补 schema**（§6.1 / R-QH-01） |
| F09 | `test_pipeline_persists_intent_and_passes_schema` | ❌ | **CODE** | `featuredDetected` 与 disk-intent 优先冲突 | AC-P4 · ADR-008 | intent flush / folders 深合并（§6.1 / R-QH-02） |
| F10 | `test_studio_export_zip` | ❌ | **CODE** | export validate 同 F08 | 同上 | 随 F08 绿 |
| F11 | `test_studio_config_stub_llm_unavailable` | ❌ | **ISOLATION(+CONTRACT)** | user secrets 覆盖 stub AppConfig | D-DLLM-02 | mock secrets；文档澄清 |
| F12 | `test_preview_toolbar_longshot_integrated_to_top_bar` | ❌ | **CONTRACT** | `SHEET_HINT_KEY` 已移除 | Phase5 / M-C5 | 删过时 token |
| F13 | `test_studio_route_snapshot_matches_baseline` | ❌ | **CONTRACT** | 新增 longshot/upload、shutdown | AC-ARC-13 | 有意更新 fixture |
| F14 | `test_homepage_p2_denoise_no_user_facing_bento` | ❌ | **CONTRACT** | 设置描述已变；须与 AI 入口一致 | UX-Trust / L0 | supersede + BLK-06 |
| F15 | `test_main_spawn_lcp` | ✅偶 | **FLAKE** | spawn LCP 环境敏感 | M20i | 勿堵 PR 快测 |
| F16 | `test_rollback_drill_passes` | ✅偶 | **FLAKE** | 回滚演练偶发 | rollback | 同 F15 |

### 2.1 聚类

```text
Cluster A · Schema/数据契约（F08/F09/F10）     → P0 CODE
Cluster B · 封面 V6 测试对齐（F05/F06）         → P0 CONTRACT
Cluster C · 文案/术语合同（F01/F02/F07/F14）   → P0 CONTRACT + 词表
Cluster D · 路由/工具栏静态门禁（F12/F13）     → P0/P1 CONTRACT
Cluster E · LLM 配置测试隔离（F11）            → P1 ISOLATION
Cluster F · Playwright 偶绿（F03/F04/F15/F16） → P2 FLAKE
```

---

## 3. 已拍板决议（R-QH-*）

> 六席评审收敛；本表为 v1.1 **真相源**。

| ID | 决议 | 说明 |
|----|------|------|
| **R-QH-01** | Schema **扫描施工**，禁止只按五列表补 | 见 §6.1 D-QH-01 |
| **R-QH-02** | `featuredDetected` 用 **intent flush / folders 深合并** 落盘 | 见 §6.1 D-QH-02；承认与 ADR-008 disk-intent 优先的张力 |
| **R-QH-03** | 取消半成品 = **方案 A（约束版自动清理）** | 见 §6.3 D-QH-05；方案 B 为 OUT-07 |
| **R-QH-04** | FirstSuccess / 设置描述合同：**采纳 L0 现行语义**，本 PRD **正式 supersede** Help V1 副文案锁与 UX-Trust F-TRU-HOME-02 | 禁止只改测；新句仍满足验货 + 『长图』、不推精修 |
| **R-QH-05** | 用户面唯一 stale 主词：**「长图可更新」**；废除「长图待更新」；Dock「已过期」改同族主词 | 见 §6.2 词表 |
| **R-QH-06** | 设置描述与 AI 入口必须一致：Popover **加入口** 或 **改句不承诺 AI** | 见 §6.2；默认推荐改句（更小 diff） |
| **R-QH-07** | 旁路上传 AC 验 **成册结果**，不止 FormData | 见 §6.3 / §10 |
| **R-QH-08** | 清点态机含 **超时/降级** 诚实态 | 见 §6.3 D-QH-04 |
| **R-QH-09** | 首发 PR = **M1+M2**；**下一合并窗必须含 M3** | 假红 ≠ 体验完成 |
| **R-QH-10** | 本波长图取消 = **诚实文案**「导出开始后无法取消」 | 真打断 = OUT-06 |
| **R-QH-11** | `expectedRevision` **不进本波** | OUT-09；仅归档指针 |
| **R-QH-12** | FirstSuccess 文案 **SSOT = `HELP_COPY`（JS）**；HTML 禁止长期双源 | T-M2-02 |

---

## 4. 问题总览与优先级

### 4.1 P0（合并/发布前必须）

| ID | 问题 | 来源 | 用户影响 |
|----|------|------|----------|
| **QH-01** | trip.schema 缺 Bookends 已写字段 | F08/F10 · BLK-01 | 导出 zip / schema 门禁失败 |
| **QH-02** | `featuredDetected` 与 disk-intent 冲突 | F09 · BLK-02 | Intent 不变量破 |
| **QH-03** | 浏览器上传丢精细字段 + 错模板选择器 | UX · BLK-07 | 旁路偏好静默失效 |
| **QH-04** | 清点假进度 + 缺超时态 | UX · BLK-08 | 假忙 / 误点开始 |
| **QH-05** | 导入取消半成品 | UX · BLK-03 | 书架脏、再导入冲突 |
| **QH-06** | 合同测试 / 词表 / 设置 IA 脱节 | F01–F07/F12–F14 · BLK-04/05/06 | CI 不可信；用户词混乱 |

### 4.2 P1（稳定期第一波 · 瘦身）

| ID | 问题 | 说明 |
|----|------|------|
| **QH-07** | 长图「取消」可点无果 | **仅诚实文案**（R-QH-10） |
| **QH-08** | stub 封面系统句；同日「日期·二」 | 最小观感；非完整命名体系 |
| **QH-09** | 角标噪声 | 词表 P0 已统一；**降噪矩阵**在 M4 |
| **QH-10** | 导入慢安抚；FirstSuccess/Failure focus trap | |
| **QH-11** | `llmAvailable` 测隔离；密钥优先语义文档化 | |
| **QH-12** | 长图捕获 `object-fit: fill` | 实现债；无设置项 |

### 4.3 P2 / 归档指针

| ID | 问题 |
|----|------|
| **QH-14** | Playwright flake marker 对齐 |
| **QH-15** | Help 遥测白名单；实验项折叠（可与 M4 合并） |
| **QH-16** | Windows CAS；P2-B 文档同步 |
| **QH-17** | unit 禁隐式 NIMA/torch |
| **QH-13†** | `expectedRevision` → **归档债**（非本波交付） |

---

## 5. 目标与成功指标

### 5.1 工程成功

| 指标 | 目标 |
|------|------|
| §2 所列 12 硬红 | **0 failed** |
| `pytest tests/unit/web -q --timeout=60`（排除 playwright markers） | 无新增失败 |
| `validate_trip(level=schema)` 对新管线产物 | 绿 |
| `POST /__travelogue/export` zip | **200** |
| Schema 扫描 | 产线写入键 ⊆ schema 已声明 properties |
| 旁路 | 成册结果与 Wizard 一致（§10） |

### 5.2 体验成功（dogfood · 可感知）

| 指标 | 目标 | 观察点 |
|------|------|--------|
| 无 Key 主路径 | 导入→预览→长图可完成 | UX-QH-01/07 |
| 取消 | 书架无空壳；确认框说「未完成草稿将删除」 | UX-QH-03/06 |
| 清点 | 无假「正在清点」；超时有诚实降级句 | UX-QH-05 |
| 旁路精细 | 成册标题/模板可见生效 | UX-QH-02 |
| 词表 | 用户面无「长图待更新」；Dock 主词同族 | 抽查 Help/首页/Dock |
| 角标（M4） | 唯一主 CTA 矩阵落地 | UX-QH-09 |

**产品 KPI 补充**：无 Key「导入→预览→长图」**零假失败**（对齐 L0 G-L0G-01）；不可仅用「CI 全绿」对外宣称体验硬化完成。

---

## 6. 工作流与里程碑

| 里程碑 | 内容 | 估时 | 依赖 |
|--------|------|------|------|
| **M0** | Kickoff：勾选 §12；冻结扩展文案表 + schema 扫描结果归档 | **0.5–1d** | — |
| **M1** | Schema 扫描补齐 + featuredDetected flush + export 绿 | **1–2d**（取上沿若碰 BLK-02） | M0 |
| **M2** | 合同/词表/路由/设置 IA（QH-06） | **0.5–1d** | M0 |
| **M3** | 上传旁路 + 清点四态 + 取消 A（QH-03/04/05） | **3–4d** | — |
| **M4** | 瘦身观感（QH-07～12 子集 · §7.4） | **1.5–2.5d** | M2 文案表 |
| **M5** | CI 卫生 + acceptance-records | **0.5–1d** | M1–M4 |

**PR 切分（强制）**：

1. **PR1** = M1 + M2（正确性 + 假红）  
2. **PR2** = M3（信任止血 · **不得跳过**）  
3. **PR3** = M4 瘦身 + M5  

---

## 7. 详细设计与任务

### 7.1 M1 · Schema 与 Intent（QH-01 / QH-02 · R-QH-01/02）

#### D-QH-01 · Schema 扫描补齐（BLK-01）

**施工纪律**：不以固定五列表为闭环；M0/M1 必须：

1. 跑一条真实 Studio/pipeline 产物（或既有 dogfood trip）；  
2. 对照 `cover_engine.api` / `curate.py` 写入点做 **键扫描**；  
3. 凡 `additionalProperties: false` 祖先下出现的未声明键一律补 schema；  
4. 验收：扫描脚本或测试断言「产线键 ⊆ schema」。

**最低已知须声明集合**（扫描可增补）：

| 路径 | 类型（锁形状） | 说明 |
|------|----------------|------|
| `meta.coverClosingStyle` | `string`（可选；无图时 **缺键** 非 null，与 api `pop` 一致） | 封底样式；勿过早锁死枚举 |
| `curation.bookendsExplain` | `object`（已知键 + 保守扩展策略写进 schema 注释） | 含 `userOneLiner` 等 |
| `curation.bookendsVersions` | `object` | 版本戳 |
| `curation.bookendsSoftWarnings` | **`array` of `{ code, message, layout }`** | **禁止**「string 或随便 object」 |
| `curation.coverOrientationByLayout` | `object`（按 `orientation_meta_for_cover` 显式子键） | 勿裸 `object` 无结构 |
| `curation.bookendsDegraded` | `boolean` | api 写入 |
| `curation.closingUserPicked` | `boolean` | Bookends §5.2 |

父级保持 `additionalProperties: false`。补 `schemas/fixtures` + `lint_trip_json`。顺带在 [PRD-BOOKENDS §5.2](./PRD-BOOKENDS-ENGINE-V1.md) 补漏列字段一行（文档债，可同 PR）。

#### D-QH-02 · `featuredDetected` 落盘（BLK-02）

**根因（已核实）**：

1. ingest 后 `_apply_featured_detected_intent` 写 **memory**；  
2. `_persist_trip_state` → `merge_pipeline_persist`：**disk 已有 `intent` 时不覆盖**（ADR-008 / AC-ARC-02）；  
3. clustering 后再 `_sync_trip_from_disk` → memory 上的 `folders.featuredDetected` 被冲掉。

**规定修复（写死一种，禁止含糊）**：

| 规则 | 内容 |
|------|------|
| **策略** | 在 HTTP/disk intent 优先前提下，允许管线对 **`intent.folders` 做深合并**（至少 `featuredDetected: bool`）回盘 |
| **推荐实现** | apply 后走 **intent flush mutator**（与既有 `make_intent_flush_mutator` 同族），或 `TripService.update` 内显式 deep-merge `folders`；**禁止**指望 `merge_pipeline_persist` 整段覆盖 intent |
| **不变量** | 管线结束后 `trip.json` → `intent.folders.featuredDetected ∈ {true,false}` 恒成立 |
| **测试** | F09 必须覆盖「disk 已有 intent 后再写 featuredDetected」路径 |

**验收命令**：

```powershell
pytest tests/unit/web/test_studio_intent.py::test_pipeline_default_place_passes_schema `
  tests/unit/web/test_studio_intent.py::test_pipeline_persists_intent_and_passes_schema `
  tests/unit/web/test_studio_m10.py::test_studio_export_zip -q --timeout=120
```

---

### 7.2 M2 · 合同、词表与设置 IA（QH-06 · R-QH-04/05/06/12）

#### 文案与词表合同表（冻结）

| 键 / 表面 | 冻结值 / 规则 | supersede |
|-----------|---------------|-----------|
| `HELP_COPY.firstSuccessNext` | `当前为本机文案；先翻一翻验货。满意就点预览页下方的『长图』；需要杂志感可在「更多工具」升级。` | Help V1 FirstSuccess 副文案锁 |
| FirstSuccess HTML hint | **禁止长期双源**；运行时或构建期与 `HELP_COPY` 一致 | R-QH-12 |
| 设置描述（选定案后锁一句） | **案甲（推荐）**：`导入与分析偏好；AI 文案可在能力卡中升级` · **案乙**：保留「…AI 文案升级」且 Popover **增加**「配置写作引擎」入口 | UX-Trust F-TRU-HOME-02 |
| 用户角标 / Help H3 / 拦截 | 主词 **`长图可更新`** | Homepage v2.1；Help 旧「待更新」 |
| 预览 Task Dock 主标题 | **`长图可更新`**（废除主词「长图已过期」）；副文可保留「内容有更新，请重新导出后再分享」 | BLK-05 |
| algorithm stale 短徽标 | 保留短词 **`可更新`**（与长图全称区分） | D-17 |
| `build_entry` 默认 opening | `veil-footer` | V6 |
| `magazine-head` resolve | → `folio-overlap`（另断言 raw / legacyMapped） | V6 |

#### 任务清单

| ID | 任务 |
|----|------|
| T-M2-01 | 更新 help/first-success 合同断言（F01/F02） |
| T-M2-02 | FirstSuccess 以 `HELP_COPY` 为 SSOT |
| T-M2-03 | V6 entry 测试（F05/F06） |
| T-M2-04 | 全链路「长图可更新」：Help H3、deep link、task-dock、longshot helpLink |
| T-M2-05 | 设置描述断言 + **落地 R-QH-06 选定案**（改句或加入口） |
| T-M2-06 | 更新 `studio_route_snapshot.json` |
| T-M2-07 | 移除 `SHEET_HINT_KEY` 过时 token |
| T-M2-08 | stub LLM 测：mock/清空 `read_user_llm_secrets` |
| T-M2-09 | 文档：用户密钥优先于 `config.llm.provider=stub` |
| T-M2-10 | Help / UX-Trust 文档各加一行「superseded by Stable-QH v1.1 · R-QH-04」 |

扫描「长图待更新」：覆盖 `templates/studio/**`；**排除** `docs/wireframes/**` 与 archive。

---

### 7.3 M3 · 导入旁路、清点、取消（QH-03/04/05 · R-QH-03/07/08）

#### D-QH-03 · 上传与 Wizard 对齐（BLK-07）

| 缺陷 | 修复 |
|------|------|
| `startUploadFromWizard` 未传 title/place/notes/density/template | 与 `buildWizardPayload` 等价传入 |
| `readTemplateParams` 读 `#v2-template-mode` | 统一读 `#v2-wizard-template-mode`（或共享 helper） |
| `buildUploadForm` place 写死「旅途」 | 尊重 Wizard；`placeUserSet` 正确 |
| 旁路跳过 `validateFineFields` | 精细制作路径与文件夹路径同等校验 |

**AC（请求层）**：FormData 含相同 `mode` / `layoutDensity` / `template_*` / `title` / `place` / `placeUserSet`。  

**AC（结果层 · 强制）**：成册后 `trip` / FirstSuccess / 预览可见标题与模板（或 templateFeedback）与 Wizard 一致；dogfood 必含「精细 + 手动模板 + 自定义标题」。

#### D-QH-04 · 清点四态（BLK-08）

| 状态 | 文案（冻结 · 可微调措辞但语义锁定） | Start |
|------|--------------------------------------|-------|
| **loading** | 「正在清点照片…」 | 可弱化 |
| **degraded / timeout** | 「照片较多，制作时将自动清点」 | **允许**；不得显示已清点 N 张 |
| **failed** | 「未能清点照片，可更换文件夹或直接开始」 | **允许**；错误稳定可见（`role="status"` / 行内 error） |
| **ready** | 「已清点 N 张」 | 正常 |

实现：`_previewFailed` / `_previewDegraded` 等显式状态；禁止失败后 `_pendingPhotoCount=null` 仍落入 loading 文案。  
**AC-QH-04** 必须覆盖 **failed 与 timeout** 两条。

#### D-QH-05 · 取消半成品 · 方案 A 约束版（BLK-03）

**定案**：自动清理；**禁止**裸 `rmtree`。

| 谓词 / 护栏 | 规定 |
|-------------|------|
| **何时删** | job ∈ `{cancelled, failed}` **且** trip **未达 previewable** |
| **previewable（书面定义）** | 存在可打开的合法卷轴预览（建议：`index.html` 存在 **且** `pipeline.status` 已达可预览态，具体枚举 M0 对照产线 status 表冻结一行）；用户已成功打开预览的项 **不得** 删 |
| **用户 PATCH** | 若存在用户有效精修/intent PATCH，不得当半成品自动删 |
| **删除 API** | 走既有 **`purge_trip`（或等价）** + library index reconcile + 写锁；禁止手搓删除 |
| **上传 temp** | cancel/fail 时一并清理 `upload_dir`（并入本任务） |
| **确认框人话** | 「取消后将删除未完成的草稿」；禁止空泛「丢失进度」而实际留空壳 |
| **成功反馈** | 可选 toast「已清理未完成草稿」 |
| **再导入** | 不得因脏 id 误撞 `E_DEMO_EXISTS`；若撞车须有覆盖/换 id 的用户出口 |

**方案 B**（未完成书架态）= OUT-07，本波不做。

---

### 7.4 M4 · 瘦身观感与交互（P1）

| ID | 任务 | 要点 |
|----|------|------|
| T-M4-01 | stub hook 默认不上用户封面 | 精修可显 |
| T-M4-02 | 禁止默认「日期·二」类标题 | **不做**完整 CHAPTER-NAMING |
| T-M4-03 | 角标主 CTA 矩阵 | 见下方；扩展文案表附件 |
| T-M4-04 | Importing 慢安抚 | 复用/冻结旧 `showSlowHint` 三档文案 |
| T-M4-05 | FirstSuccess **与 Import Failed** focus trap + Esc | 对齐 Wizard |
| T-M4-06 | 长图取消诚实文案 | 「导出开始后无法取消」；去掉假取消或禁用 |
| T-M4-07 | 捕获态 `object-fit` | `fill`→封面/媒体分策；**无设置开关** |
| T-M4-08 | 实验项折叠 | G1/beam 入「实验选项」；用户面去代号（「导入后先确认章节」等） |

#### 角标 / 续编主 CTA 矩阵（BLK-UI-04 · M4 开工附件）

| Surface | 长图 stale 时 | 说明 |
|---------|---------------|------|
| 书架卡片角标 | 静默徽标「长图可更新」**或**隐藏 | 与下一行互斥：若 resume 条有主按钮则角标降级 |
| 续编 / resume 条 | **唯一主 CTA**：「更新长图」 | 默认保留此处 |
| bench 最近卡徽标 | 可保留小徽标 | 非主 CTA |
| 预览 Dock | 主词「长图可更新」+ 导出操作 | 预览上下文独立 |

M4 **不需要**新全页线框；需要 **扩展文案表**（清点四态、慢提示三档、长图取消一句、Help H3、Dock 主/副、实验区标签）+ 本矩阵半页表。

---

### 7.5 M5 · CI 卫生

| ID | 任务 |
|----|------|
| T-M5-01 | F03/F04 与 F15/F16 统一 `playwright_serial` / e2e；PR 快测排除 |
| T-M5-02 | unit 禁隐式 NIMA/torch |
| T-M5-03 | `QUALITY-GATE.md` 增加稳定期 AC 命令 |
| T-M5-04 | `acceptance-records/stable-qh-YYYY-MM-DD.md` |

---

## 8. 风险与回滚

| 风险 | 等级 | 缓解 |
|------|------|------|
| Schema 过严误杀旧 trip | 中 | legacy opening 枚举保留；Closing 勿更严；缺键优于非法 null |
| 取消误删已可预览 trip | 高 | previewable 硬谓词；用户 PATCH 豁免；`purge_trip` |
| 文案改测掩盖真回归 | 中 | 合同表 + supersede 声明；PR 贴字符串 diff |
| 只交 M1+M2 宣称完成 | 高 | R-QH-09；下一窗强制 M3 |
| 设置提 AI 无入口 | 中 | R-QH-06 二选一必须落地 |

回滚：PR1/PR2/PR3 独立；schema revert + fixture 回滚。

---

## 9. 与观感路线图的关系

本 PRD **不替代** [观感提升路线图](./观感提升路线图.md)。

| 本 PRD | 观感路线图 |
|--------|------------|
| 正确性、契约、旁路、取消、stub 可见洞 | 选片 / pairwise / 模板硬约束 |
| M4 仅「默认交付物不像半成品」 | 大杠杆仍在 subset + coverage |

LSE：继续冻结。

---

## 10. 验收标准（AC）

### 10.1 自动化

- [ ] **AC-QH-01** F08/F09/F10 绿；schema 扫描 ⊇ 产线键  
- [ ] **AC-QH-02** F05/F06/F01/F02/F07/F12/F13/F14/F11 绿  
- [ ] **AC-QH-03a** 上传 FormData 字段对齐  
- [ ] **AC-QH-03b** 成册结果标题/模板与 Wizard 一致（集成或 e2e）  
- [ ] **AC-QH-04a** 清点 **failed** 文案翻转  
- [ ] **AC-QH-04b** 清点 **timeout/degraded** 诚实态  
- [ ] **AC-QH-05** 取消后：未 previewable trip 已 purge；书架无空壳  
- [ ] **AC-QH-06** route snapshot 一致  
- [ ] **AC-QH-07** 用户面扫描无「长图待更新」（排除 wireframe）  

### 10.2 手测（dogfood）

- [ ] **UX-QH-01** 无 Key：导入 → 预览 → 长图  
- [ ] **UX-QH-02** 选夹失败 → 上传精细 + 手动模板 + 自定义标题 → **成册可见生效**  
- [ ] **UX-QH-03** 导入中取消：确认「未完成草稿将删除」→ 书架干净  
- [ ] **UX-QH-04** 窄屏 Unsupported（回归）  
- [ ] **UX-QH-05** 清点硬失败 +（若可造）超时降级  
- [ ] **UX-QH-06** 取消后再导入无幽灵冲突  
- [ ] **UX-QH-07** 无 Key 预览封面无「碎片拼成」类系统句（或仅精修可见）  
- [ ] **UX-QH-08** Importing ≥30s 慢安抚；FirstSuccess/Failure：trap + Esc  
- [ ] **UX-QH-09**（M4）角标主 CTA 矩阵抽查  

---

## 11. 修复优先级总表

| 序 | ID | 动作 | 类型 | 估时 |
|----|-----|------|------|------|
| 1 | QH-01 | Schema 扫描补齐 | CODE | 0.5–1d |
| 2 | QH-02 | featuredDetected flush / 深合并 | CODE | 0.5–1d |
| 3 | QH-06 | 合同/词表/设置 IA/路由 | CONTRACT | 0.5–1d |
| 4 | QH-03 | 上传对齐 + 结果 AC | CODE | 0.5–1d |
| 5 | QH-04 | 清点四态 | CODE | 0.5d |
| 6 | QH-05 | 取消 A 约束版 + temp 清理 | CODE | 1–1.5d |
| 7 | QH-07～12 | M4 瘦身 | UX | 1.5–2.5d |
| 8 | QH-14/17 | CI 卫生 | P2 | 0.5d |

---

## 12. Kickoff 检查清单

> 阻塞项已写入正文 §3 / §7。Kickoff 仅确认执行承诺。

### 12.1 决议确认（v1.1 已定案）

- [x] R-QH-04 文案合同采纳 L0 + supersede Help/UX-Trust  
- [x] R-QH-03 取消 A 约束版  
- [x] R-QH-05 「长图可更新」全链路  
- [x] R-QH-09 首发 M1+M2，下一窗必含 M3  
- [x] R-QH-06 设置：案甲改句 **或** 案乙加入口（Kickoff **圈定一案**）  
- [x] R-QH-10/11 长图诚实取消；expectedRevision 不进本波  

### 12.2 开工门槛

- [ ] Owner / Reviewer / 目标合并日已指定  
- [ ] M0：schema 扫描初表归档到 acceptance-records 或 PR 描述  
- [ ] M0：扩展文案表（清点四态 + 慢提示三档 + 取消确认句 + Dock 主副文）已贴  
- [ ] M0：R-QH-06 选定案甲或案乙  
- [ ] 分支 `fix/stable-quality-hardening-v1` 已开  
- [ ] 确认不混入 OUT-01..09  

---

## 13. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0.0 | 2026-07-15 | 初版：16 失败归因 + UX P0/P1 + M0–M5 |
| v1.0.0+review | 2026-07-15 | 六席评审有条件通过；挂纪要 |
| **v1.1.0** | **2026-07-15** | **合入 BLK-01..08**：决议表 R-QH-*、schema 扫描、intent flush、取消 A 谓词、supersede/词表/设置 IA、清点四态、结果态旁路 AC、里程碑/估时/OUT/AC/dogfood 全面修订；状态 **Ready for Kickoff** |
