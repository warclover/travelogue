# 日更质量修复包 QFX V1 · 跨职能评审会结论

| 属性 | 内容 |
|------|------|
| **会议日期** | 2026-07-22 |
| **材料** | [PRD-QUALITY-FIXPACK-V1.md](../PRD-QUALITY-FIXPACK-V1.md) **v0.1** |
| **形式** | 跨职能书面评审（架构 · 算法 · 测试 · 前端 · 后端 · 产品 · UI/UX） |
| **结论状态** | **有条件通过（Conditional Go）** · **PRD v0.2.0 已回写** · 可开 IMPLEMENTATION（编码前仍须勾选 Kickoff 剩余项） |
| **记录人** | 联合纪要（七席并行评审汇总） |
| **审查基线** | `master` @ `ed4f032` |

---

## 1. 与会角色

| 角色 | 关注点 |
|------|--------|
| **架构** | 单一真相源、合入闭环、导出事务、真实护栏 vs 代理指标 |
| **算法** | keep-all 预处理合同、尺寸归一化、长图批次身份、curate 不变量 |
| **测试** | 假绿机制、fail-closed、PR required checks、AC 可测性 |
| **前端** | setter 威胁定性、hydration 状态机、草稿真值表、复制三态 |
| **后端** | status 早拒、telemetry schema、keep-all 回填拆分 |
| **产品** | 用户承诺、流程债、Fix all 分期、原 PRD 回写 |
| **UI/UX** | 体验信任信号、a11y 真测、复制诚实、L1 等值契约 |

---

## 2. 总评（一句话）

> **方向正确，但 v0.1 仍是 14 个局部补丁的集合。系统性根因是：多源推导状态、用代理指标验收合同、合入后才跑重型 CI、导出无成功事务点。最根本解法不是逐条打补丁，而是：预合入闭环 + NAS/keep-all 单一真相源 + 导出 manifest + fail-closed 真组件审计；并回写 NAS/Keep-All/CSC，禁止 QFX 长期成为第四份 SSOT。**

**表决汇总**

| 角色 | 表决 | 一句话 |
|------|------|--------|
| 架构 | **Conditional Go** | 补齐合入闭环与真相源后可 Kickoff；仅 AC 变绿不算通过 |
| 算法 | **Conditional Go** | D-06/07/08/02 合同不够严；批次/幂等/预处理须钉死 |
| 测试 | **No-Go*** | 当前 AC 挡不住假绿；PR required + fail-closed 前不开码 |
| 前端 | **Request Changes** | setter 是契约问题非安全边界；hydration/草稿/复制须先修 |
| 后端 | **Request Changes** | status 早拒 + schema 是服务端边界；先修再放行 |
| 产品 | **Conditional Go** | Fix all 可作结案目标，不可单 PR；产品挡门关闭前不发版 |
| UI/UX | **Conditional Go** | 假绿伤信任；能力卡真挂载 + 复制三态 + L1== 为体验挡门 |

\*测试席「No-Go」与其余席「Conditional Go / Request Changes」合并为统一结论：**Conditional Go · Must-Fix 关闭前不开 IMPLEMENTATION 编码**。

**对齐评分（主观）**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题清单完整度 | 9 | Q1–Q14 覆盖当日真实缺陷 |
| 根因深度 | 6 | v0.1 偏症状；本纪要升系统根因 |
| 范围克制 | 5 | Fix all 过大；须分可回滚 PR |
| 工程可开工性 | 4 | 决策需改写后再开码 |
| AC 可测性 / 防假绿 | 3 | 描述目标 ≠ 强制门禁 |
| 与相邻 PRD 仲裁 | 5 | 须回写 NAS/Keep-All，勿平行 SSOT |

---

## 3. 系统级根因（七席共识）

| # | 根因 | 为何会系统性发生 | 表象（QFX 条目） |
|---|------|------------------|------------------|
| **R1** | **状态多源推导** | NAS gate、photoKeepMode、L1 keys 在 FE/BE/草稿各自再推；每加调用点即可绕过 | Q3,Q4,Q7,Q9,Q13,Q14 |
| **R2** | **用代理指标验收合同** | LOC/bool 计数/substring/假 DOM 比真行为便宜；绿灯不等于产品真 | Q2,Q5,Q10,Q11,Q14 |
| **R3** | **合入闭环断裂** | 重型 e2e/validate 偏 post-push；本地 Merge 可绕过 PR required | Q1,Q2 + master 已红 |
| **R4** | **导出无成功事务点** | 预览扫目录猜文件；name/mtime 都不是「刚导出成功」的业务身份 | Q6 |
| **R5** | **兼容逻辑散落边缘** | 旧布尔→模式、回填绑 exclusion、telemetry 去重在 JS realm | Q7,Q8,Q9,Q14 |

**产品补充根因（流程债）**：同日多主题合入本身不是罪；罪在缺少跨主题合同差量审查与「主题 Done ≠ 列车可发」的责任人——CSC Recipe / NAS / Keep-All 各自正确，旁路各自解释，QFX 被迫成补丁仲裁层。

---

## 4. 最根本解决办法（评审合成 · 按杠杆）

> 以下 **supersede** v0.1 中若干「创可贴」表述；实施以本表为准，并回写 PRD v0.2。

### P0 · 先修系统，再修症状

| ID | 根本解法 | 退出标准 |
|----|----------|----------|
| **S-QFX-01** | **预合入闭环**：QFX 相关 lint/unit/targeted e2e 进 `pull_request` **required**；主干红禁止继续合入 | 失败 PR 无法 merge；本地/CI 同绿 |
| **S-QFX-02** | **NAS 单一真相源**：BE policy 覆盖 config/status/settings/ping/narrate；FE 只读 snapshot，**无公开写 API**；off 时敏感投影为空 | AC-QFX-04/05 + 早拒测；回写 NAS D-NAS-17/§5.3 |
| **S-QFX-03** | **keep-all 意图合同**：仅显式校验通过的 `photoKeepMode` 有策略权威；旧布尔只经 **BE adapter** 一次归一（展示可推断，**不落盘升档、不反向派生**）；FE/Python **共用合同向量** | 跨语言表同绿；回写 Keep-All §4.4 |
| **S-QFX-04** | **导出事务**：成功导出原子写 manifest/`current`（batch id + 有序文件）；预览只读该记录；mtime **仅**旧盘 fallback；分段按完整批次再按段号排序 | 改标题二次导出指新批次；不完整批次不可预览 |

### P1 · 合同真测，替换伪护栏

| ID | 根本解法 | 退出标准 |
|----|----------|----------|
| **S-QFX-05** | **策展预处理合同**：`尺寸回填 → 清理本策略低清旧标记 → 条件低清硬丢 → layout_assets`；独立、幂等；在封面/分桶前完成 | keep_all 有尺寸；模式切换不污染资格 |
| **S-QFX-06** | **审计 fail-closed**：真组件挂载 + 非空 schema + bare `--strict`=all；禁止假 DOM/跳过 focus/缺字段转 0；报告含 renderer/样本/断言计数 | AC-QFX-16～20；mutation fixture 必败 |
| **S-QFX-07** | **真实架构护栏**：facade 用模块边界合同（扩扫 + grandfather owner/expiry）；god-module **依赖/职责**约束为主，LOC 仅预警 | 抽离成功 ≠ 行数下降 alone |
| **S-QFX-08** | **QFX 不长期做 SSOT**：结案必须回写 NAS / Keep-All / CSC Acceptance；宣布 Closed 前平行条款归零 | DOC 指针闭环 |

### P2 · 体验与防复发（不挡系统 P0，但挡发版）

| ID | 解法 |
|----|------|
| **S-QFX-09** | hydration：`unknown \| disabled \| enabled`；真实 `studioAuthHeaders`；失败可重试；仅成功后 telemetry；服务端 strict `{enabled:bool}` |
| **S-QFX-10** | 复制三态：成功 / fallback 成功 / 最终失败；失败聚焦可选手动地址 |
| **S-QFX-11** | L1：`data-csc-key` **集合 ==** `happyPath.l1Keys`（禁止缩成 ⊆） |
| **S-QFX-12** | 聚合门禁入口 `scripts/quality_fixpack_gate.py`（或等价）= required check |

---

## 5. 分角色意见摘要

### 5.1 架构

| 态度 | 要点 |
|------|------|
| ✅ | 问题清单准；移除 setter、status 门控、拆回填方向对 |
| 🔴 | mtime **不能**作长图权威；LOC 棘轮不能证明解耦 |
| 🔴 | FE 不是安全边界；BE policy + redacted projection |
| 🔴 | 合入闭环断裂是允许 master 带红继续叠主题的根因 |
| 📌 MF | BLK-QFX-A-01～06（见 §6） |

### 5.2 算法

| 态度 | 要点 |
|------|------|
| ✅ | 拆回填/硬丢；永不从旧布尔推断 keep_all |
| 🔴 | keep_all「跳过函数」破坏尺寸归一 → 横竖/封面/布局族 |
| 🔴 | 模式切换须清理本策略 `low_resolution` 旧标记（幂等） |
| 🔴 | 分段长图禁止逐文件 mtime 混排；须完整批次 |
| 📌 | 抽离 curate 时锁定：per-trip cfg → 回填 → 资格 → 离群/最小数/封面 |

### 5.3 测试

| 态度 | 要点 |
|------|------|
| 🔴 | Wave11 假 DOM + 跳过 trap = 替身污染 oracle |
| 🔴 | helpers fail-open：缺字段→0 仍绿 |
| 🔴 | bare `--strict` 实际只审 modal |
| 🔴 | CSC 红却 38 unit 绿 → 门禁未映射到合入前 |
| 📌 | 增 AC-QFX-16～24；PR 跑 targeted Playwright |

### 5.4 前端 / 后端

| 席 | 要点 |
|----|------|
| **FE** | setter = 契约/误用风险，非严格安全漏洞；须私有化 + 负向测 |
| **FE** | hydration 读错全局 + 失败钉死 + 提前 track = 状态机错 |
| **FE** | 未发现定时轮询 status；403 破坏面可控，但须统一 helper + 更新旧 NAS「status 可 200」验收 |
| **BE** | status 须在 `_status_body()` **之前** 403 |
| **BE** | telemetry 逐事件严格 schema |
| **联合** | FE/Python 共用 keep-all JSON 真值表；工时粗估 4–6 人日（不含合入流程基建） |

### 5.5 产品

| 态度 | 要点 |
|------|------|
| ✅ | Fix all 可作结案；必须拆可回滚批次 |
| 🔴 | NAS status 扩门 = 隐私边界补齐，须回写 NAS 原合同 |
| 🔴 | keep_all 误升 = 用户意图违约；长图陈旧 = 敢发挡门 |
| 📌 | 产品挡门：status/setter、显式 keep_all、尺寸回填、导出权威、真审计 |
| 📌 | 工程清理：LOC 抽法细节、facade 清零、HEAD、旧图物理清理 → Park/Follow-up |

**产品建议里程碑重排**（相对 v0.1 工程序）

| 波次 | 内容 |
|------|------|
| **M1′ 止血+直接伤害** | CI 绿 · status 403 · setter 只读 · 草稿不升 keep_all · 预览绑最新成功导出（manifest 优先，mtime 临时可） |
| **M2′ 合同真实** | 回填拆分+幂等 · hydration/telemetry · 能力卡真双态 · 空测量/strict · 回写 NAS/Keep-All |
| **M3′ 防复发** | L1== · 复制三态 · facade 合同 · 聚合 gate · QFX Closed 指针归零 |

### 5.6 UI/UX

| 态度 | 要点 |
|------|------|
| 🔴 | 假绿比红灯更伤体验信任（决策信号失效） |
| 🔴 | 禁用态 ≠ 已证明可达态 a11y |
| 🔴 | 复制须结果确认，禁止动作即成功 |
| 📌 | L1 锁 **==**；COPY：成功「地址已复制…」/ 失败「无法自动复制。请长按选择下方地址并复制。」+ 聚焦控件 |

---

## 6. Must-Fix 总表（合入挡门）

### 6.1 架构 / 流程

| ID | 要求 |
|----|------|
| **BLK-QFX-A-01** | PR required：recipe / god-module / facade / NAS 负向 / UI Detail / keep-all 合同测；主干红禁合入 |
| **BLK-QFX-A-02** | NAS BE policy + 只读 FE snapshot；无公开 setter |
| **BLK-QFX-A-03** | `photoKeepMode` 唯一权威；旧布尔仅 BE adapter；禁 FE/Python 双表 |
| **BLK-QFX-A-04** | 导出成功原子 manifest/`current`；预览按 export id 整组选取 |
| **BLK-QFX-A-05** | 审计 fail-closed：真组件 + 非空 schema + strict=all 进 PR CI |
| **BLK-QFX-A-06** | facade/god-module 改为真实边界合同；LOC 仅预警 |

### 6.2 算法

| ID | 要求 |
|----|------|
| **BLK-QFX-ALG-01** | 回填与低清硬丢拆分；keep_all 必回填 |
| **BLK-QFX-ALG-02** | 清理本策略 `low_resolution` 旧标记，保证幂等 |
| **BLK-QFX-ALG-03** | 旧布尔推断不落盘、不触发 mode→bool 重派生；显式/legacy 来源 |
| **BLK-QFX-ALG-04** | 分段按完整最新批次 + 数字段号；禁逐文件混排 |
| **BLK-QFX-ALG-05** | 抽离 curate 锁定执行顺序与不变量 |
| **BLK-QFX-ALG-06** | 禁整函数 mock；真实图验尺寸/资格/布局池 |

### 6.3 测试

| ID | 要求 |
|----|------|
| **BLK-QFX-QA-01～05** | 删假 DOM；完整 a11y 矩阵不可 skip；metrics schema P0；bare `--strict`=all；token 解析非 substring |
| **BLK-QFX-QA-06～08** | hydration 负向矩阵；gate schema 严格；status 早拒且不调 `_status_body` |
| **BLK-QFX-QA-09～10** | PR targeted Playwright required；baseline 上调需 CODEOWNER/验收留痕 |

### 6.4 前/后端

| ID | 要求 |
|----|------|
| **BLK-QFX-FE-01～05** | setter 私有化；status 统一短路+鉴权；可重试 hydration；草稿真值表；复制三态 |
| **BLK-QFX-BE-01～04** | status 早拒；回归矩阵；telemetry schema；keep_all 只跳硬丢 |

### 6.5 产品 / UX

| ID | 要求 |
|----|------|
| **BLK-QFX-P-01** | 合入列车：每主题后跨主题门禁；红禁叠主题 |
| **BLK-QFX-P-02** | NAS status 403 回写原 PRD/ACCEPTANCE |
| **BLK-QFX-P-03～07** | setter · 显式 keep_all · 回填 · 导出权威 · 真审计（产品挡门） |
| **BLK-QFX-P-08** | 结案回写邻接合同；QFX 非长期 SSOT |
| **BLK-QFX-P-09** | Fix all 拆独立可回滚 PR |
| **BLK-QFX-UX-01～06** | 真挂载 · 完整键盘语义 · 证据元数据 · 复制三态 · 失败聚焦地址 · L1== |

---

## 7. 对 D-QFX-01～14 的修订决议

| 决策 | 决议 | 说明 |
|------|------|------|
| **D-QFX-01** | **升格** | 同步基线必要；另立「主干红禁合入」；基线变更须语义 diff + 同 PR |
| **D-QFX-02** | **改写** | 抽离须保算法不变量；LOC 预警，非充分放行条件；禁「>1 人日自动涨天花板」 |
| **D-QFX-03** | **升格** | 去 setter + BE 只读 snapshot；威胁定性改为契约/纵深，安全边界在 BE |
| **D-QFX-04** | **升格** | status 早拒；评估 config 等读路径敏感投影一并收口；回写 NAS |
| **D-QFX-05** | **改写** | 真组件双态；测试开关禁生产 URL；完整 a11y 不可 skip |
| **D-QFX-06** | **改写** | **manifest 第一权威**；mtime 仅旧盘 fallback；分段按批次 |
| **D-QFX-07** | **升格** | 对齐 §4.4 + BE adapter 单源；推断不落盘 |
| **D-QFX-08** | **强化** | 无条件回填 + 幂等清标 + 真实图断言 |
| **D-QFX-09** | **升格** | 三态状态机 + 成功确认 telemetry |
| **D-QFX-10** | **升挡** | fail-closed schema 进 PR CI |
| **D-QFX-11** | **升格** | bare `--strict`=all 为 required；token 解析引用链 |
| **D-QFX-12** | **降级为发版挡门、非架构挡门** | 必修，可独立小 PR |
| **D-QFX-13** | **改写** | 锁 **==**，禁止 ⊆ 模糊 |
| **D-QFX-14** | **拆分** | telemetry schema ∥ facade 边界合同分项 |

---

## 8. Park / Follow-up

| 项 | 理由 |
|----|------|
| 历史长图物理清理 | 有 manifest 后再做回收 |
| HEAD 全路径语义 | 不挡产品；现有 check 未阻塞则可后置 |
| facade grandfather 清零 | 本包禁新增 + owner/expiry |
| `curate`/`pipeline` 全量大拆 | 本包只停继续耦合并满足棘轮/边界 |
| 轮播热区放大布局 | 非本包已证根因；勿扩 scope |

---

## 9. 增补验收（建议写入 PRD v0.2 §9）

| ID | 断言 |
|----|------|
| **AC-QFX-16** | 能力卡报告 `renderer=production`；假 DOM mutation 必败 |
| **AC-QFX-17** | 能力卡 a11y 全矩阵执行且无 skipped |
| **AC-QFX-18** | metrics 缺字段/零样本/NaN → P0 |
| **AC-QFX-19** | `main(["--strict"])` ⇒ `wave=all` |
| **AC-QFX-20** | token 仅在无关选择器 → 审计失败 |
| **AC-QFX-21** | hydration 失败后可重试成功；失败期 0 次 false gate |
| **AC-QFX-22** | 同 tab reload ≤1 条 gate；新 session 可再发 |
| **AC-QFX-23** | status off 在 secrets/目录读取前 403 |
| **AC-QFX-24** | QFX PR gate 为 required（流程可证明） |
| **AC-QFX-25** | 导出 manifest 存在时预览忽略更旧 mtime/name 文件 |
| **AC-QFX-26** | keep_all 切换幂等：旧 low_res 标记清除且尺寸齐全 |

---

## 10. Kickoff 清单（勾选后方可编码）

- [x] PRD 升至 **v0.2.0 / v0.2.1**，写入本纪要 S-QFX / BLK / D-QFX 修订
- [x] 回写 NAS（status 读门控 · config 投影）与 Keep-All（§4.2 回填澄清）
- [x] IMPLEMENTATION-NAS **v0.2.2** + IMPLEMENTATION-QFX **v0.1.0**
- [x] 导出最小 `current.json` 字段草签 · 合同向量路径 · PR-A/B/C/D 切片
- [ ] 确认 PR required checks 在 ci.yml 落地（编码 PR-A/D）
- [ ] 开分支开始 PR-A 编码

---

## 11. 最终结论

| 项 | 内容 |
|----|------|
| **表决** | **Conditional Go** |
| **可否按 v0.1 原文开工** | **否**（已由 v0.2.0 supersede） |
| **下一步** | 写 IMPLEMENTATION → 开 M1′ 编码 |
| **发版挡门** | S-QFX-01～06 + 产品挡门（P-02～07）关闭 |
| **结案挡门** | S-QFX-08 邻接合同回写完成 |

---

**签字栏**

| 角色 | 结论 | 日期 |
|------|------|------|
| 架构 | Conditional Go | 2026-07-22 |
| 算法 | Conditional Go | 2026-07-22 |
| 测试 | No-Go → 并入 Conditional Go（MF 前不开码） | 2026-07-22 |
| 前端 | Request Changes | 2026-07-22 |
| 后端 | Request Changes | 2026-07-22 |
| 产品 | Conditional Go | 2026-07-22 |
| UI/UX | Conditional Go | 2026-07-22 |
