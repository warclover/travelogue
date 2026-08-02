# Travelogue · 周审计代码质量修复包 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.2** |
| **状态** | **Closed · M1～M3 已落地**（2026-07-23） |
| **DOC-STATUS** | **closed** |
| **主题代号** | 「周审计代码质量修复包 V1（Code Quality Audit Fixpack）」— **CQA** |
| **调研来源** | 2026-07-23 代码质量全面审计（窗口 2026-07-16→23）· REQUEST_CHANGES · Fix all 落地目标 |
| **审查基线** | `master` @ `3eb22a5`（审计日 HEAD） |
| **审计产物** | Cursor Canvas（IDE）：`canvases/code-quality-audit-2026-07-23.canvas.tsx` · 聊天审计结论「REQUEST_CHANGES / Fix all」 |
| **评审纪要** | [acceptance-records/code-quality-audit-fixpack-v1-review-2026-07-23.md](../../../acceptance-records/code-quality-audit-fixpack-v1-review-2026-07-23.md) · **Conditional Go** |
| **关联文档** | [QFX](./PRD-QUALITY-FIXPACK-V1.md) · [PDG](../../../PRD-PREVIEW-DELETE-GUARD-V1.md) · [NAS](../../../PRD-NO-AI-SURFACE-V1.md) · [DLLM](../../../PRD-DESKTOP-LLM-SETUP-V1.md) · [SFI](../../../PRD-SHARE-FACE-INTEGRITY-V1.md) · [MSA](../../../PRD-MOSAIC-SLOT-ADAPTATION-V1.md) · [SSG](../../../PRD-SMART-SHOT-GROUPING-V1.md) · [PPF](../../../PRD-PIPELINE-PERF-V1.md) · [LTN](../../../PRD-LAYOUT-TRUST-NARRATIVE-V1.md) · [QUALITY-GATE](../../../QUALITY-GATE.md) |
| **验收** | 本文 §9 · M0 拆出 [ACCEPTANCE-CODE-QUALITY-AUDIT-FIXPACK-V1.md](./ACCEPTANCE-CODE-QUALITY-AUDIT-FIXPACK-V1.md) |
| **实施清单** | M0 落地 [IMPLEMENTATION-CODE-QUALITY-AUDIT-FIXPACK-V1.md](./IMPLEMENTATION-CODE-QUALITY-AUDIT-FIXPACK-V1.md) |
| **更新日期** | 2026-07-23 |

> **v0.2 相对 v0.1（七席回写摘要 · 2026-07-23）**
>
> - **Conditional Go**：方向与根因成立；v0.1 多处「Kickoff 再钉」改为本场冻结。  
> - **D-CQA-01**：`Secure` **当且仅当 TLS**；HTTP LAN 仅 HttpOnly；bootstrap 后清 URL token。  
> - **D-CQA-08/09**：**锁 B**——force=确认覆盖仍走删除门；**删除** `trackOverrideByVariant`（对齐 MSA 单一 `trackOverride`）。  
> - **D-CQA-04**：终态必须基于 `pollJobUntilDone` 同语义。  
> - **D-CQA-05 + busy**：`is_trip_busy` / force / 删除路径 **⊇ on-demand 物化**（代码事实：今日 busy 不含 on-demand）。  
> - **D-CQA-02**：M1 必改 `llm_ping` 形参；进程锁不得进 Closed。  
> - **M0 挡门**：ACCEPTANCE + IMPLEMENTATION 建档前 **不开 M1 合码**。  
> - 详见评审纪要 BLK-CQA-01～10。

> **定位**
>
> 本 PRD 是**缺陷修复包**，不引入新功能面。范围 = 2026-07-23 周审计 **Fix all** 清单（P0～P3 共 15 项），按系统根因收口，禁止「逐症状贴膏药」式散修。
>
> 与已结案 [QFX](./PRD-QUALITY-FIXPACK-V1.md) 正交：QFX 管 NAS/keep-all/审计假绿/manifest 权威切片；**CQA 管凭据隔离、鉴权会话、导出/分章异步契约、物化并发、SSG 残标、force 导入与编排膨胀棘轮**。重叠处（长图 `current` 完整性）以 **QFX D-QFX-06 为 SSOT**，本包只补审计新缺口（乱序分段刷新）。

> **一句话目标**：**管理面令牌不可被 LAN 匿名拿走；LLM ping 永不串扰；导出/分章/物化的异步终态与磁盘写入可预期；SSG/MSA 无死数据；实验面停止继续塞进 hook。**

> **完成定义（Fix all）**
>
> | 门 | 含义 | 不等于 |
> |----|------|--------|
> | **M1 Go（止血）** | P0 + 全部本周 P1 关闭；并发/凭据/字段契约有真测；主干可继续叠主题 | 存量 P1 全清；God-module 大拆 |
> | **M2 Go（存量安全 + 契约）** | 存量 P1 + 本周/架构 P2 关闭；MSA 死路径二选一结案；配置原子写 | longshot.js 拆文件完成 |
> | **M3 Go（防复发）** | P3 棘轮 + 聚合 gate 进 PR required；邻接 PRD 回写；CQA Closed | 历史 facade 清零；公网 SaaS 鉴权 |

> **禁止**
>
> - **禁止单 PR 塞满 Fix all**（至少按 M1 / M2 / M3 三列合入）。  
> - **禁止**用「加锁 sleep」假装修完并发。  
> - **禁止**在未改鉴权模型前宣称「LAN 已安全」。  
> - **禁止**把 QFX 已 Closed 条款平行再开 SSOT。

---

## 0. 读者指南与边界

### 0.1 与相邻主题

| 主题 | 关系 | 本主题做什么 |
|------|------|--------------|
| [QFX](./PRD-QUALITY-FIXPACK-V1.md) | **邻居 · 已 Closed** | 不重开 NAS/keep-all/假绿；长图 manifest SSOT 仍归 QFX；本包补 **乱序分段 → current** 缺口 |
| [PDG](../../../PRD-PREVIEW-DELETE-GUARD-V1.md) | **删除门邻居** | force 导入必须**复用** `begin_trip_delete` / busy / demo 保护，不另造删除语义 |
| [DLLM](../../../PRD-DESKTOP-LLM-SETUP-V1.md) / [NAS](../../../PRD-NO-AI-SURFACE-V1.md) | **LLM 面** | ping 凭据隔离；不重开 AI-Return；NAS off 仍早拒 |
| [SFI](../../../PRD-SHARE-FACE-INTEGRITY-V1.md) / Output Recipe | **导出 prefs** | 统一 `prefs.mode`；不重开人话命名 / density IA |
| [MSA](../../../PRD-MOSAIC-SLOT-ADAPTATION-V1.md) | **回写** | `trackOverrideByVariant` 死路径必须接线或删除 |
| [SSG](../../../PRD-SMART-SHOT-GROUPING-V1.md) | **回写** | 重算前清空 `shotGroup*`；孤儿字段 = 合同违规 |
| [PPF](../../../PRD-PIPELINE-PERF-V1.md) | **物化邻居** | on-demand 线程合并 + 原子 `trip.json`；不重开 decode/NIMA 主题 |
| [LTN](../../../PRD-LAYOUT-TRUST-NARRATIVE-V1.md) | **编排邻居** | hook 候选复用 / 质量池 hoist；新实验禁塞 hook |

### 0.2 审计问题 → 落点

| 审计 ID | 严重度 | 来源 | 问题 | 落点 |
|---------|--------|------|------|------|
| **Q-CQA-01** | **P0** | 存量 | LAN 匿名可拿管理令牌 | §4 R0.1 · D-CQA-01 · S-01 |
| **Q-CQA-02** | **P1** | 本周 | LLM ping 全局 monkey-patch / env 串扰 | §4 R1.1 · D-CQA-02 · S-02 |
| **Q-CQA-03** | **P1** | 本周 | `segmentMode` 误读，整卷确认失效 | §4 R1.2 · D-CQA-03 · S-03 |
| **Q-CQA-04** | **P1** | 本周 | 分章 202 即「完成」 | §4 R1.3 · D-CQA-04 · S-04 |
| **Q-CQA-05** | **P1** | 本周 | on-demand 物化并发写 `trip.json` | §4 R1.4 · D-CQA-05 · S-05 |
| **Q-CQA-06** | **P1** | 本周 | SSG 重跑留孤儿 `shotGroup*` | §4 R1.5 · D-CQA-06 · S-06 |
| **Q-CQA-07** | **P1** | 存量 | 长图上传可覆盖 trip 文件 | §4 R2.1 · D-CQA-07 · S-07 |
| **Q-CQA-08** | **P1** | 存量 | `force` 导入绕过删除保护 | §4 R2.2 · D-CQA-08 · S-08 |
| **Q-CQA-09** | **P2** | 本周 | MSA `trackOverrideByVariant` 未消费 | §4 R2.3 · D-CQA-09 · S-09 |
| **Q-CQA-10** | **P2** | 本周 | Escape 关闭导出面板不 settle | §4 R2.4 · D-CQA-10 · S-03 |
| **Q-CQA-11** | **P2** | 本周 | Book 面板重绘泄漏 LLM 监听 | §4 R2.5 · D-CQA-11 · S-10 |
| **Q-CQA-12** | **P2** | 本周 | 分段乱序上传不刷 `current` | §4 R2.6 · D-CQA-12 · S-11 |
| **Q-CQA-13** | **P2** | 架构 | mosaic 候选/质量池重复计算 | §4 R3.1 · D-CQA-13 · S-12 |
| **Q-CQA-14** | **P2** | 架构 | 配置 PATCH 非原子读改写 | §4 R2.7 · D-CQA-14 · S-13 |
| **Q-CQA-15** | **P3** | 架构 | hook / longshot 等 God-module 膨胀 | §4 R3.2 · D-CQA-15 · S-14 |

### 0.3 系统根因（非表象）

| ID | 根因 | 表象 |
|----|------|------|
| **R1** | **进程/线程共享可变全局**（env、函数指针、无线程表合并、非原子文件写） | Q-02, Q-05, Q-14 |
| **R2** | **跨层字段/契约漂移**（prefs `mode` vs `segmentMode`；job 提交 vs 终态；MSA 写而不读） | Q-03, Q-04, Q-09, Q-10 |
| **R3** | **信任边界过宽**（未认证页面发管理 token；客户端文件名可信；force 旁路） | Q-01, Q-07, Q-08 |
| **R4** | **清理非幂等**（跳过路径不擦旧字段；监听器只绑不卸） | Q-06, Q-11 |
| **R5** | **编排热点无预算**（候选双算、质量池循环重建、巨型文件继续接需求） | Q-13, Q-15 |

### 0.4 已锁定决策（v0.2 · 七席拍板）

| 决策 | 锁定结论 |
|------|----------|
| **D-CQA-01 LAN 会话** | **区分绑定面**：`loopback` 可保留「启动后本地信任」。**非 loopback**：未认证响应**零**完整管理 token（HTML/JS/非 HttpOnly Cookie 皆禁）。Bootstrap：一次性 URL/query（或等价）兑换 **HttpOnly** 会话 Cookie；**`Secure` 当且仅当 TLS**（纯 HTTP LAN **不得**标 Secure，否则 Cookie 无法保存）。兑换成功后**清除 URL 中的 token**。后续 API 只认会话。LAN 上 Studio 静态资源不得永久匿名 `auth=False`。（BLK-CQA-01） |
| **D-CQA-02 LLM ping DI** | **删除**模块级 `read_user_llm_secrets =` 与 ping 写 `os.environ[api_key_env]`。M1 **必须**扩展 `llm_ping` / resolve 接受请求本地 `UserLlmSecrets` + config（显式参数或 contextvar）——**不可只改 handler**。过渡进程锁若存在须标 `expires≤M2`，**不得**作为 M3 Closed 态。（BLK-CQA-02） |
| **D-CQA-03 导出 prefs 字段** | SSOT = **`mode`**（`full` \| `chapter`）。业务路径禁止读写 `segmentMode`。`maybeConfirmFullExportThen` 读/写 `prefs.mode`；「改用按章」→ `mode=chapter` + `writeExportPrefs`。 |
| **D-CQA-04 Job 终态 Promise** | `regenerateStructure` / `confirmStructure` 必须基于 **`pollJobUntilDone`（或同语义）** 返回终态 Promise；**禁止**用回调式 `pollStudioJob` 假装 settle。终态前禁用操作；**禁止** 202 时「已保存/已完成」。（BLK-CQA-03） |
| **D-CQA-05 物化单飞 + 原子写 + busy** | 同 `trip_dir` 至多一条 on-demand 执行流：存活则**合并 asset 并复用**，禁 `join(0.05)` 盲起线程。`trip.json`：**tmp + `os.replace`**。`is_trip_busy` / `begin_trip_delete` / force 覆盖路径必须将 **on-demand 存活线程视为 busy**，或先 `stop_or_join_on_demand` 再删——今日 busy **仅** jobs+deleting，本包必须扩展。（BLK-CQA-04）失败可观测，不得只归零 `derivativesPreparing`。 |
| **D-CQA-06 SSG 清场** | 每次成功进入分组写回前，对**全部** assets 清 `shotGroup*`，再只为本次成员赋值。视频 / 无簇 / noise 跳过**不得**留旧字段。回写 SSG Acceptance。 |
| **D-CQA-07 长图上传白名单** | **忽略**客户端落盘名；服务端按 `fmt`+`batchId`/`segment` 固定命名；校验扩展名、魔数、体积；拒绝保留名（`trip.json`、`index.html`、`*.html`/`*.js`/`*.css` 等）。失败 4xx 不落盘。（BLK-CQA-10） |
| **D-CQA-08 force 导入** | **锁 B（废除 A）**：HTTP `force=true` = 用户确认覆盖；仍须 demo 永拒 + `begin_trip_delete`（或等价 tombstone）+ busy（**含 on-demand**）通过后才清盘再导入。禁止裸 `rmtree` 旁路。（BLK-CQA-05） |
| **D-CQA-09 MSA 死路径** | **锁 B（废除 A / 废除 Kickoff 二选一）**：删除 `trackOverrideByVariant` 写入、summary 与断言。对齐 MSA SSOT：持久化 **`layoutGeometry.trackOverride`（单一）**；各 variant 求解过程可观测。未来多轨持久化归 MSA 新合同，不在 CQA 接线。（BLK-CQA-06） |
| **D-CQA-10 导出面板单一关闭** | Escape / 遮罩 / 取消 / 确定共用关闭路径：卸监听、释 trap、`finish` settle。确定路径 **只 apply 一次**草稿。 |
| **D-CQA-11 监听器生命周期** | window 级监听绑 **sheet/panel 生命周期**；destroy/close 必须移除。验收以「destroy 后无残留」为准（弱化脆弱的计数==1）。 |
| **D-CQA-12 current 完整性** | 每次分段上传后检查整批是否齐；齐则原子更新 `current`。**字段/schema 零分叉**，对齐 QFX D-QFX-06；本包只改触发条件。（BLK-CQA-09） |
| **D-CQA-13 候选复用** | 复用 `WindowCandidateResult`；`build_quality_pool` 禁止在 pattern 循环内全 trip 重建。 |
| **D-CQA-14 配置原子写** | **Must**：文件锁 + tmp + replace，并发不截断。**Should**：revision/CAS。 |
| **D-CQA-15 膨胀棘轮** | hook.py / longshot.js 行数棘轮（基线=审计日）；新实验禁塞 hook。不要求本包拆完巨石文件。 |
| **D-CQA-16 测试合同** | P0/P1 必须有**可执行夹具**的可失败自动化（LAN 鉴权双态、双线程 ping、双 on-demand、prefs.mode、job 终态、SSG 清场、上传保留名、force+demo/busy）。禁止「理论上测得到」。（BLK-CQA-08） |
| **D-CQA-17 ping 落盘错误** | `persist=true` 遇 `OSError` → 稳定错误码；`pingOk` 与 `persisted` 分字段。 |

### 0.5 七席 BLK 速查

| ID | 挡 | 摘要 |
|----|----|------|
| BLK-CQA-01～04、08 | **M1** | LAN 矩阵 · ping DI · Job 终态 · busy⊇on-demand · 可测夹具 |
| BLK-CQA-07 | **M0→M1** | ACCEPTANCE + IMPLEMENTATION 建档 |
| BLK-CQA-05/06/09/10 | **M2** | force B · MSA 删 byVariant · current 零分叉 · 上传白名单 |

---

## 1. 背景与证据

### 1.1 审查环境

| 项 | 内容 |
|----|------|
| 窗口 | 2026-07-16 → 2026-07-23 |
| HEAD | `master` @ `3eb22a5` |
| 体量 | 159 commits（无 merge）· ~485 代码文件 · 约 +49k / −4k |
| 主导波次 | studio / ltn / sfi / csc / tpc / mtso / wait-tips / msa / ssg / pipeline |
| 裁定 | **REQUEST_CHANGES** |

### 1.2 已核对证据（抽样）

| 证据 | 位置 |
|------|------|
| ping 替换 `us.read_user_llm_secrets` + 写 `os.environ` | `travelogue/web/studio_handlers/llm_settings_handlers.py` ~328–369 |
| 确认读 `prefs.segmentMode`；prefs SSOT 为 `mode` | `longshot.js` ~2234；`longshot-export-panel.js` `readExportPrefs` |
| `runG1Confirm`/`Regenerate` 在 202 后 `return` 不 await poll | `drawers.js` ~592–640 |
| on-demand `join(0.05)` 后起新线程；`path.write_text` | `derivatives.py` ~258–320 |
| SSG 循环 `continue` 不清场 | `shot_grouping.py` ~296–304 |
| MSA 写 `trackOverrideByVariant`；render 只读 `trackOverride` | `msa_apply.py` ~163；`render/context.py` ~928 |

### 1.3 正向能力（本包不回退）

- trip 静态 / upload 路径 `resolve` + `relative_to` 约束。  
- 命令调用参数数组（无 shell 拼接）在审计范围内成立。  
- LLM 自定义 endpoint HTTPS + provider/model 白名单。  
- NAS AI surface 默认关闭与硬门控。  
- PDG tombstone 删除主路径（force 必须接入，不得另辟旁路）。  
- FE 成功面多用 `textContent`。

---

## 2. 问题陈述（P-CQA-*）

| ID | 审计 | 用户/系统可感伤害 |
|----|------|-------------------|
| **P-CQA-01** | Q-01 | LAN 上他人打开首页即可获得管理权 |
| **P-CQA-02** | Q-02 | 并发设置/测试时 API Key 可能发错端点或互读 |
| **P-CQA-03** | Q-03 | 大相册选整卷不弹确认；选「按章」仍可能整卷导出 |
| **P-CQA-04** | Q-04 | 分章显示已保存但后台仍在跑；可双重提交 |
| **P-CQA-05** | Q-05 | 预览/导出期间 `trip.json` 损坏或丢更新 |
| **P-CQA-06** | Q-06 | 旧分镜标记污染策展/拼图门禁 |
| **P-CQA-07** | Q-07 | 认证调用者可破坏 trip 或植入同源脚本 |
| **P-CQA-08** | Q-08 | 示例/进行中旅程被静默抹掉 |
| **P-CQA-09** | Q-09 | 多布局下轨道适应「看起来做了」实际未生效 |
| **P-CQA-10** | Q-10 | Escape 后导出状态机卡死 / 重复副作用 |
| **P-CQA-11** | Q-11 | 长时间使用内存与幽灵刷新 |
| **P-CQA-12** | Q-12 | 分段导出完成后预览仍旧 |
| **P-CQA-13** | Q-13 | 大相册排版变慢（重复候选） |
| **P-CQA-14** | Q-14 | 并发改设置丢配置或截断 YAML |
| **P-CQA-15** | Q-15 | 后续主题合入成本与回归面失控 |

---

## 3. 根本解法与目标

### 3.1 根本解法（S-CQA-*）

#### P0 · 信任边界

| ID | 解法 | 退出 |
|----|------|------|
| **S-CQA-01** | LAN 会话模型（D-01）：bootstrap 兑换 + HttpOnly；匿名页零 token | AC-CQA-01/02 |

#### P1 · 共享可变全局与契约

| ID | 解法 | 退出 |
|----|------|------|
| **S-CQA-02** | LLM ping 请求本地 DI（D-02/17） | AC-CQA-03/04 |
| **S-CQA-03** | 导出 prefs + 面板生命周期（D-03/10） | AC-CQA-05/06/07 |
| **S-CQA-04** | Job 终态 Promise（D-04） | AC-CQA-08/09 |
| **S-CQA-05** | 物化单飞 + 原子 trip 写（D-05） | AC-CQA-10/11 |
| **S-CQA-06** | SSG 清场（D-06） | AC-CQA-12 |

#### P1/P2 · 存量安全与一致性

| ID | 解法 | 退出 |
|----|------|------|
| **S-CQA-07** | 长图上传白名单（D-07） | AC-CQA-13/14 |
| **S-CQA-08** | force 接入删除门（D-08） | AC-CQA-15/16 |
| **S-CQA-09** | MSA 死路径结案（D-09） | AC-CQA-17 |
| **S-CQA-10** | 监听器生命周期（D-11） | AC-CQA-18 |
| **S-CQA-11** | 分段 current 完整性（D-12 · 对齐 QFX） | AC-CQA-19 |
| **S-CQA-12** | 候选/质量池复用（D-13） | AC-CQA-20 |
| **S-CQA-13** | 配置原子写（D-14） | AC-CQA-21 |

#### P3 · 防复发

| ID | 解法 | 退出 |
|----|------|------|
| **S-CQA-14** | 行数棘轮 + 禁塞 hook（D-15） | AC-CQA-22 |
| **S-CQA-15** | `scripts/code_quality_audit_fixpack_gate.py`（或等价命令列表）= PR required | AC-CQA-23 |
| **S-CQA-16** | 邻接 PRD/Acceptance 回写；CQA 非长期平行 SSOT | DOC 闭环 |

### 3.2 非目标

- 不重开 AI-Return、公网多租户 IAM、OAuth。  
- 不重写 curate / narrate / 排版族算法内核。  
- 不强制拆完 `longshot.js` / `curate.py` / `screen_planner.py`。  
- 不清理历史 facade grandfather（归 CSC/QFX 棘轮）。  
- 不把工作区 `.tmp-*` / `qa-*.png` 纳入产品合同（工程卫生另议）。  
- **不**在本包修改 QFX 已 Closed 的 NAS/keep-all 合同正文（仅必要时交叉链接）。

### 3.3 成功指标

| 指标 | 现状 | 目标 |
|------|------|------|
| LAN 匿名响应含完整 studio token | 是 | **否** |
| 并发 ping 串扰 | 可能 | **0（有测）** |
| 整卷确认读错字段 | 是 | **0** |
| 分章 202→「已保存」 | 是 | **0** |
| 同 trip 并行 on-demand 写 | 可能 | **0** |
| SSG 重跑后孤儿 shotGroup | 可能 | **0** |
| 客户端文件名覆盖 trip.json | 可能 | **0** |
| force 抹 demo / busy trip | 可能 | **0** |
| MSA byVariant 死数据 | 是 | **0（接线或删除）** |
| Escape 后导出 Promise 泄漏 | 是 | **0** |
| 乱序分段后 current 陈旧 | 可能 | **0** |
| pattern 循环内重建质量池 | 是 | **否** |
| 配置并发截断 | 可能 | **0** |
| hook/longshot 无预算净增 | 是 | **棘轮拦** |

---

## 4. 需求详述

### WS0 · 信任边界 — M1（可与 WS1 同列车，但独立 PR）

#### R0.1 LAN 会话（P-CQA-01 · D-CQA-01 · S-01 · BLK-01）

- 识别 server bind：loopback vs LAN。  
- LAN：未认证零 token；bootstrap → HttpOnly 会话；`Secure` iff TLS；兑换后清 URL token。  
- 回归：loopback「打开即用」保留；ACCEPTANCE 写清允许矩阵 + **可执行 LAN 鉴权夹具**。  
- 验收：AC-CQA-01/02。

---

### WS1 · 本周 P1 止血 — M1

#### R1.1 LLM ping DI（P-CQA-02 · D-CQA-02/17 · S-02 · BLK-02）

- 扩展 `travelogue/llm` 的 `llm_ping`/resolve：**请求本地凭据**；handler 删除猴子补丁与 ping 写 env。  
- 双线程并发 ping（不同 key/baseUrl）互不污染；grep/钩子门禁禁模块级赋值残留。  
- `persist` 写盘 `OSError` → 结构化错误；`pingOk` 与 `persisted` 分离。  
- 验收：AC-CQA-03/04。

#### R1.2 导出 mode 契约 + 面板关闭（P-CQA-03/10 · D-CQA-03/10 · S-03）

- 修正 `maybeConfirmFullExportThen`；grep 清 `segmentMode` 业务读。  
- 单一关闭路径；确定只 apply 一次。  
- 单测/逻辑测：keptN 超阈 + `mode=full` 必确认；secondary → `mode=chapter` 且后续请求带 chapter。  
- 验收：AC-CQA-05/06/07。  
- **列车注**：可与 R1.1 分独立 PR（SF-CQA-02）。

#### R1.3 分章 Job 终态（P-CQA-04 · D-CQA-04 · S-04 · BLK-03）

- 基于 **`pollJobUntilDone`（或同语义）** 返回终态 Promise；chapter-panel 等终态再刷新/toast/close。  
- 进行中禁用 regen/confirm；禁止并行第二个结构 job。  
- 验收：AC-CQA-08/09。

#### R1.4 物化单飞 + busy（P-CQA-05 · D-CQA-05 · S-05 · BLK-04）

- 合并 in-flight asset；原子写；扩展 busy ⊇ on-demand（或 delete/force 前强制 join）。  
- 与 PDG `stop_or_join_on_demand` 同语义，禁止第二套取消 API。  
- 失败状态可观测。  
- 验收：AC-CQA-10/10b/11。

#### R1.5 SSG 清场（P-CQA-06 · D-CQA-06 · S-06）

- 清场后再赋值；单测：预置孤儿字段 → 重跑后视频/无簇资产字段为空。  
- 回写 SSG Acceptance。  
- 验收：AC-CQA-12。

---

### WS2 · 存量安全 + P2 — M2

#### R2.1 长图上传硬化（P-CQA-07 · D-CQA-07 · S-07）

- 固定命名 + 魔数 + 拒保留名。  
- 负向：`filename=../trip.json` / `index.html` / `evil.html` → 失败且文件不变。  
- 验收：AC-CQA-13/14。

#### R2.2 force 导入（P-CQA-08 · D-CQA-08 · S-08 · BLK-05）

- **锁 B**：确认覆盖仍走删除门；demo 永拒；busy（含 on-demand）→ 409；禁止裸 rmtree。  
- 验收：AC-CQA-15/16。

#### R2.3 MSA 死路径（P-CQA-09 · D-CQA-09 · S-09 · BLK-06）

- **锁 B**：删除 `trackOverrideByVariant`；回写 MSA Acceptance。  
- 验收：AC-CQA-17。

#### R2.4 FE 监听泄漏（P-CQA-11 · D-CQA-11 · S-10）

- sheet 生命周期绑定；destroy 后无残留 `travelogue:llm-status` 监听。  
- 验收：AC-CQA-18。

#### R2.5 乱序分段 current（P-CQA-12 · D-CQA-12 · S-11 · BLK-09）

- 每次上传检查完整批；**schema 对齐 QFX**，零分叉。  
- 验收：AC-CQA-19。

#### R2.6 配置原子写（P-CQA-14 · D-CQA-14 · S-13）

- Must：锁 + replace；Should：CAS。并发 PATCH 不截断。  
- 验收：AC-CQA-21。

---

### WS3 · 性能与防复发 — M3

#### R3.1 mosaic 候选复用（P-CQA-13 · D-CQA-13 · S-12）

- 复用 WindowCandidateResult；质量池 hoist。  
- 回归：既有 MTSO/MSA/LTN 单测不回退；可选微基准证明 pool 构建次数下降。  
- 验收：AC-CQA-20。

#### R3.2 God-module 棘轮（P-CQA-15 · D-CQA-15 · S-14）

- lint 脚本：hook.py / longshot.js 基线行数；超限 fail（允许 CODEOWNER 留痕微调，**禁止**静默抬天花板）。  
- 文档：新 LTN/MTSO 类实验模块落点指南（禁塞 hook）。  
- 验收：AC-CQA-22。

#### R3.3 聚合 gate + 结案（S-15/16）

- `python scripts/code_quality_audit_fixpack_gate.py`（或 QUALITY-GATE 钉死列表）进 PR required。  
- 回写 MSA/SSG/DLLM/PDG/SFI 相关 Acceptance；宣布 CQA Closed。  
- 验收：AC-CQA-23 + DOC。

---

## 5. 文案 / 体验（仅缺陷相关）

| ID | 场景 | 文案 / 交互 |
|----|------|-------------|
| **COPY-CQA-01** | 分章进行中 | `正在调整结构…`（禁用「重新分章」「完成」） |
| **COPY-CQA-02** | 分章失败 | 展示 job error；面板保持打开；不出现「已保存」 |
| **COPY-CQA-03** | ping 通但落盘失败 | `已连通，但未能保存状态。请重试保存。`（`pingOk:true` + `persisted:false`） |
| **COPY-CQA-04** | LAN 需登录/兑换 | 简短说明「此网络需授权后才能使用 Studio」；提供粘贴/打开启动链接的路径（IMPLEMENTATION 定交互） |
| **COPY-CQA-05** | force 覆盖冲突 | `该画册正在使用或受保护，无法覆盖导入` |
| **COPY-CQA-06** | 整卷确认（不变语义） | 保持现有：「照片较多，确认导出整卷？」/「改用按章导出」——**仅修字段使其生效** |

不新增营销文案；不改 FirstSuccess / Wait Tips 文案体系。

---

## 6. 里程碑与 PR 列车

| 里程碑 | 范围 | 建议 PR 切分 | 挡门 |
|--------|------|--------------|------|
| **M1** | R0.1 + R1.1～R1.5 | PR-A 鉴权会话 · PR-B LLM ping · PR-C 导出/分章契约 · PR-D 物化+SSG | AC-01～12；主干可叠主题 |
| **M2** | R2.1～R2.6 | PR-E 上传+force · PR-F MSA+FE 泄漏+current · PR-G 配置原子写 | AC-13～19/21 |
| **M3** | R3.1～R3.3 | PR-H 候选复用 · PR-I 棘轮+gate+回写 | AC-20/22/23；CQA Closed |

**依赖**：

- M1 PR-D 物化须与 PDG on-demand stop/join **同语义**，避免互破。  
- M2 current 完整性须读 QFX manifest 字段，禁止第三套 current 格式。  
- M1 PR-A（LAN）可与 PR-B/C 并行，但合并前须过 AC-01/02。

---

## 7. 风险与回滚

| 风险 | 缓解 | 回滚 |
|------|------|------|
| LAN 会话改坏 loopback「打开即用」 | 允许矩阵单测 + dogfood 本机 | 特性开关仅影响非 loopback |
| ping DI 漏改调用点 | 全仓 grep `read_user_llm_secrets =`；并发测 | 临时进程锁（标注到期日） |
| force 收紧破坏内部脚本 | CLI/内部工具另参数；HTTP 面收紧 | 仅恢复内部入口，不恢复裸 rmtree |
| 原子写在部分 FS 行为差异 | Windows CI / 本地 dogfood | 保留重试；不回退截断写 |
| MSA 删 byVariant 被邻接打回 | 七席已锁 B；MSA Acceptance 结案注记 | 仅当 MSA 新开多轨合同才重开 |

---

## 8. Park（明确不做）

| 项 | 原因 |
|----|------|
| 公网多用户 RBAC / OAuth | 超 Desktop Studio 边界 |
| `longshot.js` / `curate.py` 全量拆分 | P3 棘轮即可；全拆另立主题 |
| 历史长图物理清理 | QFX Park |
| 依赖 CVE 全量扫描 | 另立供应链主题 |
| 工作区 `.tmp-*` 清理合同 | 工程卫生，非产品 AC |

---

## 9. 验收标准（AC-CQA-*）

> 编码前将本表同步至 `ACCEPTANCE-CODE-QUALITY-AUDIT-FIXPACK-V1.md`；结案以 Acceptance 勾选为准。

### 9.1 M1

| ID | 断言 | 测法 |
|----|------|------|
| **AC-CQA-01** | 非 loopback（**显式 LAN 鉴权夹具**）下，未认证 `GET /` 响应体与非会话 Cookie **不含**完整管理 token | handler/e2e：切换 LAN 鉴权态（非仅文档） |
| **AC-CQA-02** | LAN bootstrap 兑换后：无会话 → 受保护 API 401/403；有会话可通；URL token 不可复用长期暴露 | handler/e2e |
| **AC-CQA-03** | 两并发 ping（不同 api_key + baseUrl）互不串扰；无模块级 `read_user_llm_secrets` 赋值残留 | 线程单测 + grep/钩子门禁 |
| **AC-CQA-04** | `persist=true` 且写盘 `OSError` → 结构化码；`pingOk` 与 `persisted` 可分离 | 单测 mock 写失败 |
| **AC-CQA-05** | `mode=full` 且 keptN 超阈 → 必出整卷确认 | FE 逻辑测 / e2e |
| **AC-CQA-06** | 「改用按章」后 prefs.`mode`==`chapter`，导出不再按 full | 逻辑测 |
| **AC-CQA-07** | Escape → Promise settled；再次打开确定只 apply 一次 | FE 测 |
| **AC-CQA-08** | regenerate/confirm 终态来自 `pollJobUntilDone` 同语义；成功前不 toast「已保存」；按钮禁用 | 抽屉契约测 |
| **AC-CQA-09** | job 失败 → 错误可见；可重试；无假成功 | 契约测 |
| **AC-CQA-10** | 同 trip 连续两次 on-demand：仅一执行流；asset 合并 | 单测 |
| **AC-CQA-10b** | on-demand 存活时 `is_trip_busy` 为 true，**或** force/delete 前 join 可证完成后才清盘 | 单测 |
| **AC-CQA-11** | persist 使用 replace；并发保存无截断 JSON | 单测 |
| **AC-CQA-12** | 预置孤儿 shotGroup → 重跑后无簇/视频字段清空 | 单测 |

### 9.2 M2

| ID | 断言 | 测法 |
|----|------|------|
| **AC-CQA-13** | 上传 `filename=trip.json` / `index.html` → 拒绝且原文件不变 | handler 测 |
| **AC-CQA-14** | 非图像魔数 → 拒绝不落盘 | handler 测 |
| **AC-CQA-15** | force 覆盖 **demo** → 失败 | handler 测 |
| **AC-CQA-16** | force 在 busy（**含 on-demand**）→ 409；盘不被 rmtree | handler 测 |
| **AC-CQA-17** | 仓库无 `trackOverrideByVariant` 写入路径（锁 B） | 单测 + grep |
| **AC-CQA-18** | sheet/panel destroy 后无残留 `travelogue:llm-status` 监听 | FE 契约测 |
| **AC-CQA-19** | 乱序分段齐套后 `current` 指新批次，且字段集与 QFX 最小 schema 一致 | 单测 |
| **AC-CQA-21** | 并发 config PATCH → 完整合法 YAML，无截断 | 单测 |

### 9.3 M3

| ID | 断言 | 测法 |
|----|------|------|
| **AC-CQA-20** | 质量池每窗口构建次数 O(1)；候选复用路径有测锁 | 单测 |
| **AC-CQA-22** | hook/longshot 棘轮脚本在超基线时 fail | lint CI |
| **AC-CQA-23** | 聚合 gate 为 PR required；本包 AC 子集绿 | CI 配置审 |

### 9.4 结案 DOC

| ID | 断言 |
|----|------|
| **AC-CQA-DOC-01** | MSA / SSG / DLLM（或 WEA）/ PDG / SFI 相关 Acceptance 已回写 CQA 决策 |
| **AC-CQA-DOC-02** | IMPLEMENTATION 勾选完成；PRD 状态 → **Closed**；无平行 SSOT |

---

## 10. Kickoff 检查清单

### M0（可立即开始 · 挡 M1 合码）

- [x] 七席 Conditional Go · 纪要落盘  
- [x] PRD **v0.2** 回写 BLK / D / AC  
- [x] **D-CQA-08/09 锁 B**（本场拍板，无需再选字母）  
- [x] 建立 `ACCEPTANCE-CODE-QUALITY-AUDIT-FIXPACK-V1.md`  
- [x] 建立 `IMPLEMENTATION-CODE-QUALITY-AUDIT-FIXPACK-V1.md`（I-CQA-* · PR-A～I · LAN 夹具 · busy 扩展点）  
- [x] 与 QFX：current schema 零分叉（ACCEPTANCE §2 / I-CQA-10）  
- [x] 与 PDG：on-demand stop/join 不双轨（I-CQA-06/08）  
- [x] CI：CQA ratchet + `code_quality_audit_fixpack_gate.py` 进 ci.yml（AC-22/23）  

### M1 合码前

- [x] BLK-CQA-01～04、08 设计在 IMPLEMENTATION 有文件级任务（T-01～06）  
- [x] ACCEPTANCE / IMPLEMENTATION 均已存在（BLK-CQA-07 **关闭**）  
- [x] 分支 `fix/cqa-m1-hemostasis` 编码并收口 M1～M3

---

## 11. 实施映射（摘要 · 详单见 IMPLEMENTATION）

| 决策 | 主改文件（预期） |
|------|------------------|
| D-01 | `studio_dispatch.py` · `static_handlers.py` · studio 入口 HTML/cookie |
| D-02/17 | `llm_settings_handlers.py` · `travelogue/llm/*` ping/resolve |
| D-03/10 | `longshot.js` · `longshot-export-panel.js` · output-recipe 测 |
| D-04 | `drawers.js` · `chapter-panel.js` · job poll helper |
| D-05 | `derivatives.py` · trip persist helper · PDG join 调用点 |
| D-06 | `shot_grouping.py` · SSG 单测 |
| D-07 | `export_handlers.py` · `longshot.py` 上传路径 |
| D-08 | `import_handlers.py` · `studio_pipeline.py` · PDG delete API |
| D-09 | `msa_apply.py` · `render/context.py` · MSA 测 |
| D-11 | `init-v3.js` |
| D-12 | `longshot.py` / export upload · QFX current 写 |
| D-13 | `mosaic/hook.py` · `candidates.py` |
| D-14 | `config/loader.py` |
| D-15/gate | `scripts/*ratchet*` · `scripts/code_quality_audit_fixpack_gate.py` |

---

## 12. 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.1** | 2026-07-23 | 首版：周审计 Fix all 范围锁定；M1/M2/M3 列车；D-CQA-01～17；AC-CQA-01～23 |
| **v0.2** | 2026-07-23 | 七席 Conditional Go 回写：LAN Secure iff TLS；force/MSA 锁 B；busy⊇on-demand；`pollJobUntilDone`；`llm_ping` 形参；M0 文档挡门；AC-10b/17/18 修订 |

---

## 附录 A · 审计条目速查

| 审计标题 | ID | 里程碑 |
|----------|-----|--------|
| LAN 匿名可拿管理令牌 | Q-CQA-01 | M1 |
| LLM ping 凭据串扰 | Q-CQA-02 | M1 |
| segmentMode 字段错误 | Q-CQA-03 | M1 |
| 分章假完成 | Q-CQA-04 | M1 |
| 物化并发写 | Q-CQA-05 | M1 |
| SSG 孤儿字段 | Q-CQA-06 | M1 |
| 长图上传覆盖 | Q-CQA-07 | M2 |
| force 绕过删除门 | Q-CQA-08 | M2 |
| MSA byVariant 死路径 | Q-CQA-09 | M2 |
| Escape 不 settle | Q-CQA-10 | M1 |
| LLM 监听泄漏 | Q-CQA-11 | M2 |
| 乱序分段 current | Q-CQA-12 | M2 |
| 候选/质量池重复 | Q-CQA-13 | M3 |
| 配置非原子写 | Q-CQA-14 | M2 |
| God-module 膨胀 | Q-CQA-15 | M3 |
