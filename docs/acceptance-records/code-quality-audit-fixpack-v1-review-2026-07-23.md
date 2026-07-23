# 周审计代码质量修复包 CQA V1 · 七席评审纪要

| 属性 | 内容 |
|------|------|
| **会议日期** | 2026-07-23 |
| **材料** | [PRD-CODE-QUALITY-AUDIT-FIXPACK-V1.md](../PRD-CODE-QUALITY-AUDIT-FIXPACK-V1.md) **v0.1** → Must-Fix 回写后升 **v0.2** |
| **形式** | 跨职能书面评审（架构 · 算法 · 测试 · 前端 · 后端/安全 · 产品 · UI/UX） |
| **结论状态** | **有条件通过（Conditional Go）** · **PRD v0.2 已回写** · **M0 已完成**（ACCEPTANCE/IMPLEMENTATION）· **可 Kickoff M1**；合码前仍须关闭 BLK-CQA-01～04/08（05/06/09/10 挡 M2） |
| **记录人** | 七席联合纪要（跨职能模拟联评 · 基于 PRD v0.1 + 2026-07-23 代码事实核查） |
| **审查基线** | `master` @ `3eb22a5`（审计日） |
| **相邻挡门** | [QFX](../PRD-QUALITY-FIXPACK-V1.md) Closed · [PDG](../PRD-PREVIEW-DELETE-GUARD-V1.md) · [MSA](../PRD-MOSAIC-SLOT-ADAPTATION-V1.md) · [SSG](../PRD-SMART-SHOT-GROUPING-V1.md) · [DLLM](../PRD-DESKTOP-LLM-SETUP-V1.md) · [NAS](../PRD-NO-AI-SURFACE-V1.md) |

---

## 0. 会前宣读（主持人）

1. **切口**：周审计 Fix all（15 项）的**系统修复包**，不是再开功能主题。  
2. **与 QFX 正交**：不重开 NAS/keep-all/假绿；`current`/manifest SSOT 仍归 QFX；本包只补乱序分段与安全/并发债。  
3. **勿重开**：公网 OAuth、longshot.js 全量大拆、AI-Return。  
4. **本场必拍**：LAN 会话矩阵 · MSA 死路径字母 · force 语义 · busy 是否含 on-demand · Job Promise 真 API · M0 文档挡门。  
5. **列车**：M0 → M1 → M2 → M3；**禁止单 PR 塞满 Fix all**。

---

## 1. 总评（一句话）

> **七席一致 Conditional Go：Fix all 范围与五条系统根因（共享全局 / 契约漂移 / 信任过宽 / 清理非幂等 / 编排无预算）成立，且与 QFX/PDG 边界大体清楚；但 v0.1 把三处「Kickoff 再钉」留成编码陷阱——MSA A|B、force A|B、LAN Secure/bootstrap 交互——且代码事实显示 `is_trip_busy` 不含 on-demand、`pollStudioJob` 非终态 Promise、`llm_ping` 无凭据形参。M0 可立即 Kickoff；M1 合码挡在 BLK-CQA-01～08。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **架构** | **Conditional Go** | R1–R5 正确；须先钉会话模型与 trip 写锁边界，禁止用进程锁冒充 DI 结案 |
| **算法** | **Conditional Go** | SSG 清场与候选复用值得做；MSA 按现合同应删 `trackOverrideByVariant`，勿另立平行字段 |
| **测试 / QA** | **Request Changes → 并入 Conditional Go** | AC 方向对但缺 LAN 可测定义与 Job/并发可失败夹具；ACCEPTANCE 未建前不开 M1 |
| **前端** | **Conditional Go** | mode/Escape/分章终态是真伤；须绑 `pollJobUntilDone`，禁止再包一层假 Promise |
| **后端 / 安全** | **Request Changes → 并入 Conditional Go** | P0 LAN + ping DI + 上传白名单 + force 必须进 M1/M2 硬合同；`Secure` 在纯 HTTP LAN 要改写 |
| **产品** | **Conditional Go** | Fix all 可作结案；LAN 不得毁掉 loopback「打开即用」；force/demo 保护是用户信任红线 |
| **UI/UX** | **Conditional Go** | 假完成/假确认比红灯更伤信任；COPY 三态与禁用态必须可感知 |

**汇总**：**七席一致 Conditional Go**。  
- **M0**：可 Kickoff（回写 v0.2 + 拆 ACCEPTANCE/IMPLEMENTATION + 钉死字母决策）。  
- **M1 合码**：BLK-CQA-01～08 关闭前 **不批**。  
- **M2/M3**：见各 BLK 挡门列。

**对齐评分（主观）**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题清单完整度 | **9** | 对齐审计 15 项，P0/P1 无漏 |
| 根因深度 | **8** | 已升系统根因，非纯症状表 |
| 范围克制 | **6** | Fix all 仍大；列车切分可接受 |
| 工程可开工性 | **5** | 多处「Kickoff 再钉」+ 缺 ACCEPTANCE |
| AC 可测性 / 防假绿 | **5** | LAN/监听计数/并发需可执行夹具 |
| 与相邻 PRD 仲裁 | **7** | QFX/PDG 指针清楚；MSA 字母未锁 |

---

## 3. 事实核查（代码核对）

| # | PRD/审计假设 | 代码事实 | 会中 |
|---|--------------|----------|------|
| **F-01** | LAN 可匿名拿 token | `GET /` `auth=False`；首页注入 `studio-token` Cookie；loopback 未开 LAN 时全放行；LAN 认 header/cookie/query | ✅ 属实 · P0 成立 |
| **F-02** | ping 靠全局 patch/env | `llm_ping(provider=…)` **无**凭据形参；handler 写 `os.environ` + 替换 `read_user_llm_secrets` | ✅ 属实 · DI 必改 `client.py` |
| **F-03** | force 绕过删除门 | `force` 仅绕过「目录已存在」；随后 `shutil.rmtree`；**未**调 `begin_trip_delete` / demo 保护 | ✅ 属实 |
| **F-04** | busy 含 on-demand | `is_trip_busy` **仅** jobs + `_deleting_trip_ids`，**不含** `derivatives` on-demand 线程 | ✅ **属实且修正 PRD 隐含假设** |
| **F-05** | 长图上传用客户端文件名 | `filename`/`relPath` → `Path.name`，仅保证仍在 trip 目录内 | ✅ 属实 |
| **F-06** | 配置非原子写 | `patch_config_file` → `path.open("w")` + `yaml.safe_dump` | ✅ 属实 |
| **F-07** | MSA 多 variant 合同 | MSA PRD：各 variant **各自求解**；持久化 **`layoutGeometry.trackOverride`**；AC-MSA-04「整屏单一 trackOverride」 | ✅ **byVariant 字段超前/偏离 MSA SSOT** |
| **F-08** | drawers 202 非终态 | `pollStudioJob` **不**返回 Promise；`pollJobUntilDone` 才在终态 resolve | ✅ 属实 · 合同应钉后者 |
| **F-09** | PDG 有 stop/join on-demand | `stop_or_join_on_demand` 存在（PDG 路径） | ✅ 属实 · force/删除须复用 |
| **F-10** | prefs SSOT 为 `mode` | `readExportPrefs()` 只返回 `mode`；`maybeConfirmFullExportThen` 读 `segmentMode` | ✅ 属实 · P1 成立 |

**新增事实（评审发现）**

| # | 事实 | 影响 |
|---|------|------|
| **F-11** | 纯 HTTP LAN 上 `Secure` Cookie **不会被浏览器保存** | D-CQA-01 原文「HttpOnly + Secure 若 HTTPS」须改写为：**Secure 当且仅当 TLS**；HTTP LAN 仅 HttpOnly |
| **F-12** | MSA 已要求按 variant 求解，但产品持久化合同是单一 `trackOverride` | CQA **不得**把「渲染读 byVariant」当成默认 A；本场拍板 **B 删除** |
| **F-13** | QFX 已 Closed 最小 `current.json` | CQA D-12 **禁止**第三套字段方言；仅补「每次上传查整批」触发条件 |

---

## 4. 全场共识

1. **Fix all = 结案范围**，不是单 PR；M0/M1/M2/M3 列车保留。  
2. **信任边界 > 体验捷径**：LAN 匿名发管理 token 必须死；loopback「打开即用」可保留。  
3. **结案态禁止全局可变凭据**：进程锁只可作 M1 过渡，不得进 M3 Closed。  
4. **异步 UI：提交 ≠ 完成**；一律终态 Promise + 禁用态。  
5. **force / 上传 / 删除共用 PDG 门**；不平行发明第二套 rmtree。  
6. **MSA 死路径本场锁 B（删除）**；多 variant 渲染消费若未来需要，归 MSA 新合同，不在 CQA 加字段。  
7. **SSG 清场 = 幂等合同**，回写 SSG Acceptance。  
8. **QFX manifest SSOT 不重开**；CQA 只修乱序触发。  
9. **busy 定义扩大**：凡会 `rmtree`/覆盖盘的路径，必须看见 on-demand 物化。  
10. **假完成比功能缺失更伤信任**（导出确认、分章 toast、ping 落盘）。

---

## 5. Must-Fix（结案成立 · 合入挡门）

| ID | 议题 | 要求（冻结一字面） | 挡 | 状态 |
|----|------|-------------------|----|------|
| **BLK-CQA-01** | LAN 会话矩阵 | **loopback**：可保留本地信任（打开即用）。**非 loopback**：未认证响应**零**完整管理 token（HTML/JS/非 HttpOnly Cookie 皆禁）。Bootstrap：一次性 URL/query 或等价握手 → 兑换 **HttpOnly** 会话 Cookie；**`Secure` 当且仅当 TLS**；HTTP LAN 只用 HttpOnly。兑换后清除 URL 中的 token。静态资源在 LAN 不得永久 `auth=False` 匿名。 | M1 | ✅ 本场拍板 · 已回写 v0.2 |
| **BLK-CQA-02** | LLM ping DI | M1 必须扩展 `llm_ping`（或 resolve）接受请求本地 secrets/config；**删除**模块级 `read_user_llm_secrets =` 与 ping 写 `os.environ[api_key_env]`。进程锁若存在须标 `expires≤M2`，**不得**作为 M3 结案态。并发双 ping 单测为 PR required。 | M1 | ✅ 本场拍板 · 已回写 |
| **BLK-CQA-03** | Job 终态 API | `regenerateStructure`/`confirmStructure` **必须**基于 `pollJobUntilDone`（或同语义）返回终态 Promise；**禁止**以 `pollStudioJob` 回调包装假装 settle。202 期间禁用操作；禁止「已保存/已完成」类 toast。 | M1 | ✅ 本场拍板 · 已回写 |
| **BLK-CQA-04** | busy ⊇ on-demand | `is_trip_busy` / `begin_trip_delete` / force 覆盖路径必须将 **on-demand 物化存活线程** 视为 busy（或先 `stop_or_join_on_demand` 再删）。仅查 studio jobs **不算**关闭本条。 | M1（force 相关断言可并 M2 PR-E，但 busy 定义 M1 必须落地） | ✅ 本场拍板 · 已回写 |
| **BLK-CQA-05** | force 语义锁 B | **废除 A 选项**。HTTP `force=true` = 用户确认覆盖；仍须：demo 永拒；`begin_trip_delete`（或等价 tombstone 门）+ busy（含 on-demand）通过后才允许清盘再导入。禁止裸 `rmtree` 旁路。 | M2 | ✅ 本场拍板 · 已回写 |
| **BLK-CQA-06** | MSA 死路径锁 B | **删除** `trackOverrideByVariant` 写入、summary 与断言；保持 MSA SSOT：`layoutGeometry.trackOverride`（单一）+ 各 variant 求解过程可观测。若未来要按 variant 持久化多轨，单独立项 MSA，不在 CQA 接线 A。 | M2 | ✅ 本场拍板 · 已回写 |
| **BLK-CQA-07** | M0 文档挡门 | M1 合码前必须存在：`ACCEPTANCE-CODE-QUALITY-AUDIT-FIXPACK-V1.md` + `IMPLEMENTATION-CODE-QUALITY-AUDIT-FIXPACK-V1.md`（含 I-CQA-*、PR 切片、LAN 测法）。 | M1 | ✅ **已关闭** · 2026-07-23 |
| **BLK-CQA-08** | LAN/并发可测夹具 | AC-CQA-01/02/03/10 必须写明**可执行**夹具：LAN bind 或 `studio_auth` 测试双态；双线程 ping；同 trip 双 on-demand。禁止「理论上测得到」。 | M1 | ✅ 本场拍板 · 已回写 |
| **BLK-CQA-09** | current 零分叉 | 乱序分段只改**触发条件**（每次上传查整批）；字段/原子写对齐 QFX D-QFX-06；禁止第三套 `current` schema。 | M2 | ✅ 本场拍板 · 已回写 |
| **BLK-CQA-10** | 上传保留名 | 忽略客户端落盘名；固定服务端命名；拒 `trip.json`/`index.html`/`*.html` 等；魔数+体积上限。 | M2 | ✅ 已在 v0.1 · 维持 |

---

## 6. Should-Fix

| ID | 建议 | 席位 | 状态 |
|----|------|------|------|
| **SF-CQA-01** | AC-CQA-18 改为「sheet close 后监听器移除」契约测，弱化「计数==1」脆弱断言 | 测试/前端 | 采纳 · 回写 AC |
| **SF-CQA-02** | M1 将「导出 mode + Escape」与「LLM ping」拆独立 PR，降低评审面 | 产品/开发 | 采纳 · 列车注释 |
| **SF-CQA-03** | ping 落盘失败 COPY 与 `pingOk`/`persisted` 字段进 DLLM/WEA 验收一句 | 产品 | 待回写邻接 |
| **SF-CQA-04** | hook/longshot 棘轮基线用「审计日行数」钉死，超限须 CODEOWNER 留痕 | 架构 | 采纳 · M3 |
| **SF-CQA-05** | 配置 CAS/revision 可为 should；**原子 replace + 文件锁**为 must | 后端 | 采纳 · D-14 分层 |
| **SF-CQA-06** | 工作区 `.tmp-*` / `qa-*.png` 不进 CQA AC（工程卫生另议） | 产品 | 维持 Park |

---

## 7. 分席意见摘要

### 7.1 架构

| 态度 | 要点 |
|------|------|
| ✅ | R1–R5 与 S-CQA 映射清楚；禁止平行 SSOT |
| 🔴 | v0.1 把 MSA/force 字母留给 Kickoff = 必翻车 |
| 🔴 | busy 不含 on-demand 时，D-05/D-08 互相假绿 |
| 📌 | 会话模型分层（loopback/LAN/TLS）写进决策表；trip persist 统一入口优于散落 `write_text` |

### 7.2 算法

| 态度 | 要点 |
|------|------|
| ✅ | SSG 清场是正确幂等；候选复用/质量池 hoist 降本正确 |
| 🔴 | `trackOverrideByVariant` 与 MSA「单一 trackOverride」冲突 → **删** |
| 📌 | 清场单测必须覆盖：视频、无簇、曾属组后丢失 cluster 的资产 |

### 7.3 测试 / QA

| 态度 | 要点 |
|------|------|
| 🔴 | ACCEPTANCE 未建 = M1 不可开 |
| 🔴 | LAN/并发 AC 缺夹具定义 → 假绿风险 |
| 📌 | PR required 只收**窄**集合：ping 并发、prefs.mode、SSG 清场、busy+on-demand、上传保留名；禁止整包 e2e 堵列车 |
| 📌 | 监听器改为生命周期契约，不作脆弱计数门神 |

### 7.4 前端

| 态度 | 要点 |
|------|------|
| ✅ | `segmentMode` / Escape / 分章假完成是用户真伤 |
| 🔴 | 合同必须点名 `pollJobUntilDone`，勿再包 `pollStudioJob` |
| 📌 | 导出确定路径只 apply 一次；与永久监听器去重写进 AC-07 |
| 📌 | Book 面板监听绑 sheet destroy（SF-01） |

### 7.5 后端 / 安全

| 态度 | 要点 |
|------|------|
| 🔴 | P0 LAN 与 ping 串扰是真实可利用面（Desktop+LAN 场景） |
| 🔴 | 上传 basename 不足以防保留名覆盖 / 同源 HTML |
| 🔴 | force 裸 rmtree 与 PDG 删除门双轨 = 事故预定 |
| 📌 | `llm_ping` 形参扩展属 M1 必达，不可只改 handler |
| 📌 | HTTP LAN：`Secure` 无效 → 已拍 BLK-01 |

### 7.6 产品

| 态度 | 要点 |
|------|------|
| ✅ | Fix all 分期正确；与 QFX 正交叙述清楚 |
| 🔴 | loopback 体验是 Desktop 底线，LAN 收紧不得误伤 |
| 🔴 | demo 不可 force、分章假成功 = 信任红线 |
| 📌 | COPY-CQA-04 须在 IMPLEMENTATION 出一屏可狗粮文案，不挡 M0 |
| 📌 | 结案必须回写 MSA/SSG/PDG/DLLM，CQA Closed 后无平行条款 |

### 7.7 UI/UX

| 态度 | 要点 |
|------|------|
| 🔴 | 「改用按章」无效、分章「已保存」假态 = 比缺功能更伤 |
| 🔴 | Escape 后状态机卡死会造成重复导出副作用 |
| 📌 | 进行中禁用 + COPY-CQA-01/02；ping 通但未落盘用 COPY-CQA-03 |
| 📌 | 分享意图卡 a11y（审计 P2 旁支）不挡 CQA 结案，可 Park 到 PMX/SFI 邻居 |

---

## 8. 对 D-CQA-01～17 的修订决议

| 决策 | 决议 | 说明 |
|------|------|------|
| **D-CQA-01** | **改写** | 分层 loopback/LAN；`Secure` iff TLS；bootstrap 后清 URL token |
| **D-CQA-02** | **升格** | 必改 `llm_ping` API；锁不得进 Closed |
| **D-CQA-03** | **维持** | `mode` SSOT |
| **D-CQA-04** | **改写** | 点名 `pollJobUntilDone` 语义 |
| **D-CQA-05** | **升格** | 与 busy⊇on-demand / PDG join 对齐 |
| **D-CQA-06** | **维持** | SSG 清场 |
| **D-CQA-07** | **维持** | 上传白名单 |
| **D-CQA-08** | **改写** | **锁 B**；废除 A |
| **D-CQA-09** | **改写** | **锁 B 删除**；废除 Kickoff 二选一 |
| **D-CQA-10** | **维持** | 单一关闭路径 |
| **D-CQA-11** | **微调** | 生命周期契约优先于计数==1 |
| **D-CQA-12** | **升格** | 零分叉 QFX schema |
| **D-CQA-13** | **维持** | 候选/质量池 |
| **D-CQA-14** | **分层** | must=锁+replace；CAS=should |
| **D-CQA-15** | **维持** | 棘轮 |
| **D-CQA-16** | **升格** | 夹具可执行（BLK-08） |
| **D-CQA-17** | **维持** | ping 落盘错误分离 |

---

## 9. 增补 / 修订验收（写入 PRD v0.2 §9）

| ID | 变更 |
|----|------|
| **AC-CQA-01** | 增：测试须切换「LAN 鉴权态」（显式 fixture），非仅文档描述 |
| **AC-CQA-03** | 增：断言源码/运行时不存在模块级 `read_user_llm_secrets` 赋值（grep 门或运行钩子） |
| **AC-CQA-08** | 改：终态来自 `pollJobUntilDone` 同语义 |
| **AC-CQA-10b**（新） | `is_trip_busy(trip)` 在 on-demand 存活时为 true（或 force/delete 前 join 成功可证） |
| **AC-CQA-16** | 与 10b 联动：busy 时 force → 409，盘不被 rmtree |
| **AC-CQA-17** | 改为：仓库无 `trackOverrideByVariant` 写入路径（B） |
| **AC-CQA-18** | 改为：sheet/panel destroy 后无残留 `travelogue:llm-status` 监听（弱化计数==1） |
| **AC-CQA-19** | 增：current 字段集与 QFX 最小 schema 一致 |

---

## 10. Park / Follow-up

| 项 | 理由 |
|----|------|
| 公网 OAuth / 多租户 IAM | 超 Desktop 边界 |
| `longshot.js` / `curate.py` 全量拆分 | P3 棘轮足够；全拆另题 |
| 分享意图卡完整 a11y | 邻居主题；不挡 CQA |
| 配置 revision/CAS 强一致 | Should；原子写足够关 P2 |
| 历史长图物理清理 | QFX Park |
| 工作区临时文件清理 | 工程卫生 |

---

## 11. Kickoff 清单

- [x] 七席 Conditional Go · 本纪要落盘  
- [x] PRD 升 **v0.2**，写入 BLK / D 修订 / AC 修订  
- [x] D-CQA-08/09 **锁 B**（本场冻结）  
- [x] 建立 `ACCEPTANCE-CODE-QUALITY-AUDIT-FIXPACK-V1.md`  
- [x] 建立 `IMPLEMENTATION-CODE-QUALITY-AUDIT-FIXPACK-V1.md`  
- [ ] MSA Acceptance 注记：CQA 删 `trackOverrideByVariant`（结案前）  
- [ ] SSG Acceptance 注记：重算前清场（结案前）  
- [ ] CI：列出 M1 窄 required 集合（编码 PR 同步）  
- [ ] 开 M1 PR-B/C（建议先 ping DI + 导出/分章契约；LAN 会话可并行 PR-A）

---

## 12. 最终结论

| 项 | 内容 |
|----|------|
| **表决** | **Conditional Go** |
| **可否按 v0.1 原文开工** | **否**（由 v0.2 supersede） |
| **下一步** | M0：ACCEPTANCE + IMPLEMENTATION → 再开 M1 编码 |
| **发版挡门** | BLK-01～06/08/10 + AC-CQA-01～12/13～16 |
| **结案挡门** | 棘轮+gate + 邻接回写 + CQA Closed |

---

**签字栏**

| 角色 | 结论 | 日期 |
|------|------|------|
| 架构 | Conditional Go | 2026-07-23 |
| 算法 | Conditional Go | 2026-07-23 |
| 测试 / QA | Request Changes → Conditional Go（MF 前不开 M1） | 2026-07-23 |
| 前端 | Conditional Go | 2026-07-23 |
| 后端 / 安全 | Request Changes → Conditional Go（MF 前不开 M1） | 2026-07-23 |
| 产品 | Conditional Go | 2026-07-23 |
| UI/UX | Conditional Go | 2026-07-23 |
