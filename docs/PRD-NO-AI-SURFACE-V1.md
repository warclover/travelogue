# Travelogue · 当前版无 AI 面与主线打磨 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | **v0.2.3** |
| **状态** | **Conditional Go · Must-Fix 已回写**（[评审纪要](./acceptance-records/no-ai-surface-v1-review-2026-07-22.md) · MF-NAS-01～10 · **v0.2.3** 同步 [QFX](./PRD-QUALITY-FIXPACK-V1.md) status 读门控 + **config 投影收口**） |
| **DOC-STATUS** | **active**（本主题为当前版本**用户面**现行合同；DLLM/WEA 用户面见 §1.5） |
| **主题代号** | 「当前版无 AI 面 · 先出图」— **NAS**（No-AI Surface） |
| **触发来源** | 2026-07-22 产品决策：本期隐藏已具备的 AI 产品面，聚焦无 AI 下纯照片出图；**LLM 工程底座保留**，供下期（AI-Return）再聚焦杂志感文案迭代 |
| **前置条件** | Studio Hub 可用；导入主链已强制 stub（`resolve_studio_narrate_provider` → stub）；纯照片长图不依赖 LLM；[PRD-DESKTOP-LLM-SETUP-V1](./PRD-DESKTOP-LLM-SETUP-V1.md) / WEA / L0-Hardening **工程已落地** |
| **关联文档** | [PRD-DESKTOP-LLM-SETUP-V1.md](./PRD-DESKTOP-LLM-SETUP-V1.md) · [PRD-WRITING-ENGINE-API-HARDENING-V1.md](./PRD-WRITING-ENGINE-API-HARDENING-V1.md) · [PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1.md](./PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1.md) · [PRD-HELP-ONBOARDING-V1.md](./PRD-HELP-ONBOARDING-V1.md) · [PRD-SHARE-FACE-INTEGRITY-V1.md](./PRD-SHARE-FACE-INTEGRITY-V1.md) · [PRD-WAIT-TIPS-V1.md](./PRD-WAIT-TIPS-V1.md) · [PRD-FTUE-OPTIMIZATION-V1.md](./PRD-FTUE-OPTIMIZATION-V1.md) · [PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md](./PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md) · [PRD-PHASE2.md](./PRD-PHASE2.md) G-P2-05 · [ERROR-CODES.md](./ERROR-CODES.md) · [adr/019-desktop-user-data-llm-secrets.md](./adr/019-desktop-user-data-llm-secrets.md) |
| **验收** | [ACCEPTANCE-NO-AI-SURFACE-V1.md](./ACCEPTANCE-NO-AI-SURFACE-V1.md)（以本文 §10 为源） |
| **实施清单** | [IMPLEMENTATION-NO-AI-SURFACE-V1.md](./IMPLEMENTATION-NO-AI-SURFACE-V1.md)（前端任务卡 + BE P0） |
| **线框** | 可选 `wireframes/no-ai-surface-v1-wireframe.html`（F1 设置去 AI · F2 预览去再生 · F3 FirstSuccess 中性） |
| **评审记录** | [acceptance-records/no-ai-surface-v1-review-2026-07-22.md](./acceptance-records/no-ai-surface-v1-review-2026-07-22.md) · **Conditional Go** · MF-NAS-01～10 |
| **更新日期** | 2026-07-22 |

> **定位**
>
> NAS 是 **「用户面休眠」**，不是 **「能力退役」**。  
> 本 PRD **不删除** LLM 工程能力，而是把当前版本的**用户默认面**冻结为：**看不见、配不了、也用不到** AI 文案 / 写作引擎。  
> 本期北极星：**无 AI 岔路下把纯照片长图做出、敢发**。  
> 下期（建议代号 **AI-Return**）再聚焦杂志感文案产品化；底座须可解冻、可迭代（见 **§14**）。
>
> **V1 Done 边界（MF-NAS-07）**  
> 本主题交付 = **无 AI 产品面 + 出图主链狗粮（§2.3 / AC-NAS-07）**。  
> **不**包含排版/长图算法深度打磨（另立 Photos-Mainline / FTT 等主题）。  
> **不**借 NAS 窗口重做 LLM 算法或拆除 DLLM/WEA 资产。
>
> **产品共识（七条铁律）**
>
> 1. **默认面 = 无 AI** — 干净安装走完主链，零「AI 文案 / 写作引擎 / 配置 Key / 杂志感升级」引导。  
> 2. **Hide, don't delete** — UI 门控 + 服务端硬拒绝；密钥、handlers、dark 文案包可保留；优先 `nas-allow`，少物理删源。  
> 3. **入口与状态解耦** — 即使本机已存 API Key，默认面仍隐藏全部入口（AC-NAS-10）。  
> 4. **主线不被支线打断** — 成功面 / 失败面 / Dock / Help 不得把用户拽去配写作引擎。  
> 5. **禁词可审计且可恢复** — 默认可达面禁词进门禁；dark 包分 job；下期解冻不得因「删光文案文件」而重写整栈。  
> 6. **可一键回滚 / 可解冻** — dark switch 恢复 DLLM 核心（设置 + Sheet/抽屉 narrate + ping）；**不**恢复能力卡首启硬推。  
> 7. **分期不混 KPI** — 本期只考出图完成与零 AI 岔路；配置率 / 文案满意度留给 AI-Return。

---

## 0. 读者指南

| 章节 | 必须澄清的问题 |
|------|----------------|
| §0.1 | 术语与范围边界 |
| §1 | 为何现在藏 AI；与 DLLM 的 supersede 关系 |
| §2 | 目标 / 非目标 / **出图北极星** |
| §3 | 体验合同 + 冻结决策 D-NAS-* |
| §4 | 触点矩阵 + 功能 F-NAS-* |
| §5 | 门控 · dark switch · **工程冻结清单** |
| §6 | 文案冻结表 COPY-NAS-* |
| §7 | 埋点（含下期漏斗预留） |
| §8 | 非功能 · 双轨发布 |
| §9 | 里程碑 W0–W3 |
| §10 | 验收 AC-NAS-* |
| §11 | 风险与开放问题 |
| §12 | 附录 |
| §13 | 评审审核清单 |
| **§14** | **分期 · AI-Return 解冻合同**（下期指针） |

### 0.1 术语

| 术语 | 定义 |
|------|------|
| **无 AI 面（NAS）** | 默认用户路径中，不展示、不引导、不触发任何依赖外部 LLM API 的产品能力 |
| **用户面休眠** | AI 能力对默认用户不可见不可用，但工程栈与 dark 回归路径仍在 |
| **主线 / 出图主链** | 导入 → 策展/排版 → 预览（可手工改字）→ **纯照片长图** / 分享发群 |
| **AI 产品能力（本期隐藏）** | 写作引擎配置 UI、能力卡 L1 升级链、预览「重新生成文案」、Task Dock AI 就绪条、H7、stub 升级 tip/banner、FirstSuccess/失败面的配置 CTA |
| **AI 工程底座（本期冻结保留）** | 见 §5.5；含 llm 客户端、secrets、narrate Job、WEA、dark 测试附录等 |
| **AI-Return** | 下期主题建议代号：解冻用户面并迭代杂志感文案（见 §14）；**非本主题交付** |
| **本机配文** | `narrate_provider=stub` 产出；对用户**尽量不单独点名**「本机文案 / AI 文案」对立（见 COPY 表） |
| **dark switch** | 仅开发/内部使用的恢复开关；**无设置页入口**；见 D-NAS-03 |
| **禁词（用户面）** | 见附录 C；命中即视为未达标（allowlist 除外） |
| **白名单词** | 「智能挑选 / 智能排版 / 智能匹配」等算法能力词；版式/节奏语境下的「杂志感」（非「杂志感文案」） |

### 0.2 与相邻主题关系

| 主题 | 关系 |
|------|------|
| **Desktop LLM Setup V1** | 工程与 API **保留**；用户面 L0/L1 分层叙事 **被本 PRD 冻结为「默认无 AI 面」** |
| **WEA / L0 Guidance Hardening** | 配置加固与死循环修复代码可留；其「用户配置路径」AC 对本版本降为 **dark-switch 附录** |
| **Help Onboarding** | 删除/隐藏 H7；改写 H0 / FirstSuccess / 重播 toast；重播不得再恢复能力卡（默认） |
| **Share Face Integrity** | 主线对齐「敢发」；**废止** FE-SFI-04「重新生成文案」用户面入口合同，改由本 PRD 接管 |
| **Wait Tips** | 文案无需大改（现网已无 AI 词）；回归 Importing 期间不得冒出能力卡 |
| **FTUE / FST / PMX / CSC** | FirstSuccess 取消 `loadLlmReadiness` 分支；CSC Happy Path 用户文案去 AI bullet |
| **Phase 2 G-P2-05 / US-P2-08** | G-P2-05（不强制 Key）**继承并强化**；US-P2-08（可选杂志感）**当前版本产品面暂停曝光** |
| **Copy Optimization / Phase 11** | stub / decorLine **算法不在本主题范围**；`decor_line_llm_enabled` 保持默认关 |
| **Aesthetic MLLM / Bookends VL** | 保持默认关；本主题确认**无设置入口** |

---

## 1. 背景与问题

### 1.1 产品一句话（本主题前提）

把旅行照片在**本机**自动变成可预览的杂志风卷轴，并导出适合微信传播的**纯照片长图**。  
当前版本的完成定义是「敢发长图」，不是「配好 API 写出杂志感句子」。

### 1.2 As-Is（工程已有 vs 产品错位）

| 层 | 现状 | 错位 |
|----|------|------|
| 导入 narrate | 永远 stub；配好 Key 也不自动 LLM | 用户仍被教育「可升级 AI 文案」 |
| 预览 LLM | 藏在精修 → 这本 → 整本信息；按钮名「重新生成文案」 | 难发现；发现后差异又被 `scope=frame` 压得很弱 |
| 设置 / 能力卡 / H7 | 完整 L1 配置面 | 与「无 AI 主线」心智冲突 |
| 纯照片长图 | 不依赖 LLM；朋友圈等强制 photos | 主线本可与 AI 完全解耦 |
| 工程栈 | DLLM/WEA/ADR-019 已投入 | **硬删**会浪费回滚能力；应藏不应拆 |

### 1.3 问题清单（P-NAS-*）

| ID | 问题 | 用户感知 | 严重度 |
|----|------|----------|--------|
| **P-NAS-01** | 产品要主线打磨，UI 仍推 L1「升级 AI 文案」 | 分心；以为还要配东西 | P0 |
| **P-NAS-02** | 预览「重新生成文案」暗示联网 AI 写作 | 找不到 / 点了变化弱 / 像半成品 | P0 |
| **P-NAS-03** | 能力卡 / stub banner / H7 / FirstSuccess 分支持续教育写作引擎 | 「是不是没配好才这么素」 | P0 |
| **P-NAS-04** | 导入失败面仍可能出现「去配置写作引擎」 | 失败归因跑偏 | P1 |
| **P-NAS-05** | 单测/CSC/狗粮锁定旧 L1 文案 | 改面即红，阻碍收敛 | P1 |
| **P-NAS-06** | 若硬删 LLM 栈 | 丢失 WEA/DLLM 投资与回滚 | P1 |
| **P-NAS-07** | 「智能*」「杂志感」易被误伤或误留 AI 义 | 文案不一致 | P2 |

### 1.4 核心判断

1. **根因是产品面暴露了不该当季售卖的支线**，不是主链缺 LLM。  
2. **正确动作**：默认面隐藏 AI + 文案去升级叙事 + 验收改绑主线。  
3. **错误动作**：为「洁癖」删除 `travelogue/llm`；或只藏按钮不改 FirstSuccess/H7（教育残留）。

### 1.5 对 DLLM / WEA / L0-Hardening 的文档状态策略（D-NAS-11）

| 文档族 | DOC-STATUS 建议 | 说明 |
|--------|------------------|------|
| PRD/ACCEPTANCE/IMPLEMENTATION · DLLM | **active（engineering）· user-facing superseded by NAS** | 工程合同仍有效；用户面以 NAS 为准 |
| WEA | 同上 | dark switch 下仍可回归 |
| L0-Hardening | 死循环修复 **保留**；「引导去配置」用户句 **废止** | 失败面改中性 |

登记落点：[DOC-STATUS.md](./DOC-STATUS.md) + 本文文首。

---

## 2. 目标与非目标

### 2.1 产品目标（G-NAS-*）

| ID | 目标 | 衡量 |
|----|------|------|
| **G-NAS-01** | 干净安装默认路径：导入 → 预览 → 纯照片长图，**零** AI/写作引擎/配置 Key 引导 | AC-NAS-01～07 |
| **G-NAS-02** | 设置 / 帮助 / 预览 / 成功 / 失败面均无 L1 配置出口 | AC-NAS-02～06 |
| **G-NAS-03** | 用户可见禁词表清零（静态审计 + 狗粮） | AC-NAS-08 |
| **G-NAS-04** | LLM 工程栈可经 dark switch 完整恢复 | AC-NAS-09 |
| **G-NAS-05** | 已存 Key 时默认面仍不暴露入口 | AC-NAS-10 |
| **G-NAS-06** | 主线体验与 Share Face「敢发」一致；不被文案再生打断 | AC-NAS-07 · 手测 |
| **G-NAS-07** | **出图北极星**：无 Key 下纯照片长图可完成、失败不归因 AI | §2.3 · AC-NAS-07 · AC-NAS-OUT-* |
| **G-NAS-08** | **底座可解冻**：dark 路径可完整回归 DLLM 核心，供 AI-Return 承接 | AC-NAS-09 · §5.5 · §14 |

### 2.2 非目标（V1 明确不做）

- 删除 `travelogue/llm/**`、ADR-019 secrets、`/__travelogue/llm/*` handlers  
- 修改 stub / decorLine **算法质量**（Copy Optimization 另轨）  
- 默认开启 `decor_line_llm_enabled` / `aesthetic.mllm.enabled` / Bookends VL  
- 官网 / 营销站大改（若外站仍写 AI，另立主题；本 PRD 以 **Studio 默认面**为准）  
- 整站视觉重设计（UI Detail 另轨）  
- **导入 / 排版 / 长图截图链路的深度体验打磨**（另立 Photos-Mainline / FTT 等；本主题只去掉 AI 岔路并保证出图可达）  
- **本期解开 `scope=frame` / 加浓 AI 文案**（属 AI-Return 卖点，见 §14）  
- 改变「智能挑选 / 智能排版」算法语义（仅文案层是否改「智能」见 OQ-NAS-02）  
- 强制离线模式改造（本主题不新增网络策略；仅要求默认面不引导外连 Key）  
- 向终端用户提供 dark switch UI / 设置项（仅 env/config）  
- 清空用户已落盘 API Key（升级用户下期应能直接解冻使用）

### 2.3 成功指标 · 出图北极星（本期 KPI）

| ID | 指标 | 目标（V1 狗粮） |
|----|------|----------------|
| **OUT-01** | 出图完成 | 非技术用户无 Key 可完成「选夹 → 预览 → **纯照片长图**」 |
| **OUT-02** | 零 AI 岔路 | 首访路径禁词 0；无人被引导去申请 DeepSeek/通义 Key |
| **OUT-03** | 失败归因干净 | 失败面只谈文件夹 / 照片 / 磁盘 / 重试；不谈写作引擎 |
| **OUT-04** | 分享话术干净 | 发群 / 朋友圈路径不出现「先配 AI」 |
| **OUT-05** | 底座未腐 | dark switch 下设置可配 + 预览可 narrate（月度冒烟，见 §5.5） |

> 配置转化率、杂志感满意度、LLM 调用成功率等 **不作为本期 KPI**（留给 AI-Return）。

### 2.4 分期一览（摘要 · 全文见 §14）

| 期 | 用户面 | 工程 | KPI |
|----|--------|------|-----|
| **本期 NAS** | 无 AI | 休眠 + 硬拒绝；底座冻结保留 | 出图 · 零岔路 |
| **下期 AI-Return** | 再开放杂志感文案 | 解冻用户面并迭代 | 配置 · 升级 · 文案质量 |
| **禁止** | 把 NAS 做成「永远不要 AI」 | 借 NAS 拆除 llm / secrets / dark 测试 | 混用两期 KPI |

---

## 3. 体验合同

### 3.1 首启场景剧本（以干净安装为准）

**Persona A · 分享者（主用户）**

| 步 | 用户看到/做 | 系统必须 |
|----|-------------|----------|
| 1 | 打开 Studio 首页 | **无**能力卡；无「升级 AI」链 |
| 2 | 打开设置 | 仅见导入偏好 / 存储与磁盘 /（既有非 AI 组）；**无「AI 文案」zone** |
| 3 | 打开帮助 | **无 H7**；H0 不提 AI 文案 |
| 4 | 选相册 → 等待 | Wait Tips 可出现；**无**能力卡抢帧 |
| 5 | FirstSuccess | **仅中性句**（见 COPY-NAS-FS-01）；无「配置写作引擎 / AI 文案已就绪」 |
| 6 | 打开预览 · 精修 · 这本 | **无**「重新生成文案」；无「配置写作引擎」 |
| 7 | 导出纯照片长图 | 成功；文案是否 stub/空不影响纯照片像素 |

**Persona B · 曾配过 Key 的升级用户（回归）**

| 步 | 用户看到/做 | 系统必须 |
|----|-------------|----------|
| 1 | 升级到 NAS 版本后打开 | secrets **可仍留在磁盘**；UI **完全无入口** |
| 2 | 预览 / 设置 | 与 Persona A 相同（隐藏） |
| 3 | 内部打开 dark switch | 可恢复配置面与 narrate（AC-NAS-09） |

**Persona C · 内部狗粮（dark switch ON）** — 不对外承诺；用于回归 DLLM/WEA。

### 3.2 能力承诺表（对外可引用 · 当前版本）

| 能力 | 默认面（NAS） | dark switch ON |
|------|---------------|----------------|
| 选文件夹导入 | ✅ | ✅ |
| 分章 / 策展 / 排版 / 预览 | ✅ | ✅ |
| 手工改标题 / 点缀 / 精修 | ✅ | ✅ |
| 纯照片长图 / 发群指引 | ✅ **必保** | ✅ |
| 写作引擎配置 UI | ❌ 隐藏 | ✅ |
| 预览 LLM 重新生成文案 | ❌ 隐藏 | ✅ |
| 审美 MLLM / decorLine LLM | ❌ 默认关且无入口 | ❌ 仍默认关（不在本主题打开） |

### 3.3 冻结决策（D-NAS-*）

| ID | 决策 | 说明 |
|----|------|------|
| **D-NAS-01** | **默认产品面 = 无 AI** | 不出现 L1 升级叙事 |
| **D-NAS-02** | **Hide, don't delete + 服务端硬拒绝** | UI 门控 + BE 硬拒绝；`studio.ai_surface_enabled` 默认 `false`；代码可留 dark 路径 |
| **D-NAS-03** | **dark switch = env ∪ config，无 UI** | `TRAVELOGUE_AI_SURFACE` / `studio.ai_surface_enabled`；正式包禁止 URL 开关；dev-only 覆盖不得进帮助 |
| **D-NAS-04** | **预览移除 LLM 工具行与 Dock 就绪条** | 含「配置写作引擎」死链；切断 Dock→`startLlmNarrate`（M11） |
| **D-NAS-05** | **设置移除 AI 文案 zone** | 导入偏好 / 存储 / 其他非 AI 组保留；开设置不依赖 `llm/status` 展示入口 |
| **D-NAS-06** | **帮助删除 H7**；H0/重播去 AI | 重播**不得** `clearCapabilityCardSeen` / `clearStubHintSeen` / `clearHomeStubBannerDismissed`（M9） |
| **D-NAS-07** | **FirstSuccess 仅 COPY-NAS-FS-01** | 禁止 readiness 分支；精确串锁死（AC-NAS-04） |
| **D-NAS-08** | **导入主链保持不调 LLM** | 失败面禁止配置 CTA；焦点不落配置钮（M7）；禁止复用 `E_LLM_AUTH` 作文案门控 |
| **D-NAS-09** | **纯照片长图为默认完成态叙事** | 与 SFI/FTT 对齐；完成面不提文案再生 |
| **D-NAS-10** | **禁词审计 = 默认可达面** | 见附录 C 扫描语义；W1 分区、W2 全量；dark 包 `nas-allow` 分 job |
| **D-NAS-11** | **DLLM/WEA/L0 用户面 superseded by NAS** | 工程栈仍 active；见 §1.5 + DOC-STATUS |
| **D-NAS-12** | **「杂志感」白名单** | 仅版式/节奏语境；邻近不得含「文案/升级/AI」 |
| **D-NAS-13** | **忙碌态零配置打扰** | 能力卡默认永不 show（含 dark ON） |
| **D-NAS-14** | **门控优先于 llmAvailable** | FE 以 `aiSurfaceEnabled` 为准；有 Key 亦不渲染入口 |
| **D-NAS-15** | **手工改字保留** | inline-edit / 精修改字仍可用 |
| **D-NAS-16** | **`POST /narrate` 硬拒绝（MF-NAS-01）** | 门控 off → HTTP **403** + `E_AI_SURFACE_DISABLED` + 中性 message；先于 Key/status 检查 |
| **D-NAS-17** | **settings/status/ping 连接面（SAS 修订）** | **2026-08 · SAS D-SAS-07 修订**：门控 off 时 **允许** `/llm/status` 读与 `/llm/settings` 写、`/llm/ping`（预配 Key）；**不等于**开放烧模型。`POST /narrate` 等仍 403。`GET /config` 关闸仍剥离 `llm*`（D-NAS-17b）。旧「连接三路由一律 403」作废。 |
| **D-NAS-17b** | **config 敏感投影收口（QFX v0.2.1 拍板）** | 门控 off → `GET /__travelogue/config` **保留** `aiSurfaceEnabled:false` 与非 LLM 业务字段；**不得**暴露 `llmAvailable` / `llmProvider` / `tripsDir` / provider 细节。dark ON 可恢复完整投影。FE hydration 只读 `aiSurfaceEnabled`；**禁止**因投影收口而对 config 整端 403 |
| **D-NAS-18** | **`aiSurfaceEnabled` 只读下发（MF-NAS-02）** | 服务端解析 → `GET /__travelogue/config`；**禁止** PATCH；FE helper 仅读该字段 |
| **D-NAS-19** | **`startLlmNarrate` 函数级门闩** | 藏 UI 不够；`core.js` 首行门控早退（FE-NAS-09/10） |
| **D-NAS-20** | **dark 恢复范围冻结** | ON：设置 AI zone + Modal + ping + Sheet llm + 抽屉 narrate；**不**恢复能力卡 / stub banner / H7 / FS 分支 |
| **D-NAS-21** | **可恢复性优先于洁癖删除** | 默认面用门控 + `nas-allow` 包住 dark 文案；**禁止**为过 AC-08 而删除 `llm-settings.js` / WEA 文案源文件 |
| **D-NAS-22** | **分期 KPI 隔离** | 本期不考核 LLM 配置转化；不在 NAS 内解开文案密度（`scope=frame` 锁定维持至 AI-Return 另议） |

---

## 4. 信息架构与功能规格

### 4.1 功能清单（F-NAS-*）

| ID | 功能 | 优先级 |
|----|------|--------|
| **F-NAS-01** | 全局 AI 面门控（BE 下发 `aiSurfaceEnabled` + FE helper） | P0 |
| **F-NAS-02** | 设置 IA 收敛（去 AI zone + 总述改写；切断 refreshAiStatus/focus=ai） | P0 |
| **F-NAS-03** | 预览工具收敛（Sheet llm / Dock / **抽屉 narrate** / `startLlmNarrate` 门闩） | P0 |
| **F-NAS-04** | 帮助与 FirstSuccess 文案包（去 H7 / FS-01 精确串 / 重播不恢复卡） | P0 |
| **F-NAS-05** | 失败/错误归因去配置出口 | P0 |
| **F-NAS-06** | 能力卡 / stub banner / stub tip 默认关闭 | P0 |
| **F-NAS-07** | dark switch 恢复包（D-NAS-20 清单；不恢复能力卡） | P1 |
| **F-NAS-08** | 禁词静态审计（默认可达面）+ 完整单测翻转清单 | P0 |
| **F-NAS-09** | 文档索引 / DOC-STATUS / ERROR-CODES / 相邻 PRD 指针 | P1 |
| **F-NAS-10** | BE：`POST /narrate` + settings 写硬拒绝 | P0 |

### 4.2 触点矩阵（T-NAS-* · 实施源表）

#### A. 必须隐藏（P0）

| ID | 触点 | 锚点（As-Is） | NAS 动作 |
|----|------|---------------|----------|
| **T-NAS-01** | 首启能力卡 | `templates/studio/js/capability-card.js` · `bootstrap.js` `maybeShowCapabilityCard` | 默认不展示；门控外整卡 hidden |
| **T-NAS-02** | 设置 · AI 文案 zone | `studio-home-v2.html` `#v2-settings-zone-ai` · `settings-panel.js` | 默认不渲染/ hidden；去掉「配置写作引擎」CTA |
| **T-NAS-03** | 写作引擎 Modal | `js/llm-settings.js` | 无默认入口；dark 时可挂载 |
| **T-NAS-04** | 首页 stub banner | `js/home-stub-banner.js` | 默认不展示 |
| **T-NAS-05** | 帮助 H7 | `help-onboarding.js` `helpItems` H7 | 条目不进默认列表 |
| **T-NAS-06** | 预览「重新生成文案」 | `preview-toolbar-v3-sheet.js` `data-tool="llm"` · `init-v3.js` · `core.js` `startLlmNarrate` | 工具行不渲染；不绑定 narrate |
| **T-NAS-07** | 预览 llm-setup / llm-expect / unavailable hint | 同上 sheet + `init-v3.js` `setLlmAvailable` | 整段不渲染 |
| **T-NAS-08** | Task Dock AI 就绪条 | `preview-toolbar-v3-task-dock.js` | 不展示 copyRefresh / AI 就绪文案 |
| **T-NAS-09** | 导入失败写作引擎恢复面 | `homepage-v2/import-failed.js` · `errors.js` `E_LLM_*` | 默认面无「去配置」；中性重试/换夹 |
| **T-NAS-10** | FirstSuccess LLM 分支 | `homepage-v2/first-success.js` + `HELP_COPY.firstSuccessNext*` | 仅 `firstSuccessNextNeutral`（或等价 COPY-NAS-FS-01） |
| **T-NAS-11** | 预览 stub narrate tip | `maybeShowStubNarrateTip` · `HELP_COPY.stubNarrateTip` | 关闭 |

#### B. 必须改写（P0/P1）

| ID | 触点 | 动作 |
|----|------|------|
| **T-NAS-12** | 帮助 H0 | 去掉「不配置 AI 文案也可以…」→ COPY-NAS-H0 |
| **T-NAS-13** | 帮助重播 toast | 去掉能力卡 / 本机文案 tip 表述 → COPY-NAS-REPLAY |
| **T-NAS-14** | 设置总述 | `v2-settings-desc` 去「AI 可选」→ COPY-NAS-SET-DESC |
| **T-NAS-15** | CSC Happy Path 用户文案 | `acceptance-records/csc-w1-happy-path-user-copy.md` 去 AI bullet |
| **T-NAS-16** | `errors.js` / `studio_errors.py` 用户句 | 默认面不可达；若保留字符串则移出用户主路径或改为中性（见 §6） |
| **T-NAS-17** | ERROR-CODES.md `E_LLM_*` | 注：NAS 默认不曝光配置引导 |
| **T-NAS-18** | 单元门禁 | `test_desktop_llm_setup_w2.py` 等：**翻转或拆分为** `test_no_ai_surface_*.py`（默认面禁词）+ dark 附录测 |

#### C. 主线 polish 检查（本主题锁范围，非大改算法）

| ID | 触点 | 要求 |
|----|------|------|
| **T-NAS-19** | 导入向导 | 无「AI 写稿」；「杂志感」仅版式节奏 hint（D-NAS-12） |
| **T-NAS-20** | Wait Tips | 文案非回归；Importing 无能力卡 |
| **T-NAS-21** | 长图 / Share | 纯照片主 CTA 清晰；无文案再生旁支 |
| **T-NAS-22** | 精修手工改字 | 保持可点改；帮助可提示 |

#### D. 工程保留（非用户面）

| ID | 模块 | 要求 |
|----|------|------|
| **T-NAS-23** | `/__travelogue/llm/*` | 保留；默认 UI 不调用 |
| **T-NAS-24** | `run_studio_llm_narrate` / narrate Job | 默认不触发 |
| **T-NAS-25** | ADR-019 secrets | 不删；UI 不可达即等价无 AI |
| **T-NAS-26** | `decor_line_llm` / MLLM / VL plugins | 保持默认关 |

#### E. 前端补漏触点（M1–M12 · 2026-07-22 回写）

> 代码复核发现的漏项/边角；与 §4.2 A–B 同等约束。实施任务卡见 [IMPLEMENTATION-NO-AI-SURFACE-V1.md](./IMPLEMENTATION-NO-AI-SURFACE-V1.md) **FE-NAS-00～14**（M1–M12 已映射进卡内）。

| ID | M# | 触点 | 锚点（As-Is） | NAS 动作 | 优先级 |
|----|----|------|---------------|----------|--------|
| **T-NAS-27** | **M1** | 精修抽屉「按新感觉重写这段」 | `preview-toolbar/drawers.js`（`.preview-drawer__narrate-anchors` · 约 421 / 911–935）→ `_startLlmNarrate` | **默认不渲染按钮**；不绑定 narrate。暗门 ON 才恢复 | P0 |
| **T-NAS-28** | **M2** | 保存后 toast 引导「重新生成文案」 | `drawers.js` ~841：`可在「精修」中重新生成文案以写入锚点与点缀` | 改为「编辑已保存」或「点文字可继续改」；禁「重新生成文案」引导 | P0 |
| **T-NAS-29** | **M3** | `constants.js` E_LLM_* 用户句 | `templates/studio/js/constants.js`（与 `errors.js` 双份） | 同步中性化，或标 dark-only / 移出默认用户路径；禁词审计须覆盖 | P0 |
| **T-NAS-30** | **M4** | 能力卡 body 残留升级话术 | `capability-card.js`：`更好的文案可稍后自行升级（可选）` + 「以后再升级 AI 文案」 | 整卡不 show **且** 字符串改写/不进默认包（静态审计仍扫到） | P0 |
| **T-NAS-31** | **M5** | bootstrap 接线副作用 | `homepage-v2/bootstrap.js`：`initLlmSettingsEntry` · `maybeShowCapabilityCard` · stub banner | 一律经 `isAiSurfaceEnabled()` 包裹；默认早退无副作用 | P0 |
| **T-NAS-32** | **M6** | settings ↔ LLM Modal 仲裁/同步 | `settings-panel.js`（badge/entry 文案 · `studio-llm-settings-root` 监听 ~553+） | AI zone 隐藏后相关 sync **短路**；不写「配置/管理写作引擎」 | P0 |
| **T-NAS-33** | **M7** | 失败面焦点落到配置按钮 | `import-failed.js` ~230：`focusId` → `v2-failure-open-settings` | 默认面焦点改「重试 / 打开最近 / 换夹」；永不强制落到配置 | P0 |
| **T-NAS-34** | **M8** | 「继续生成本机游记」对立话术 | `studio-home-v2.html` `#v2-failure-continue-stub` · `import-failed.js` | 主路径无 E_LLM_AUTH 时整组隐藏；否则文案改为「继续生成游记」（去「本机」对立） | P1 |
| **T-NAS-35** | **M9** | 帮助重播恢复能力卡/stub tip | `help-onboarding.js`：`clearCapabilityCardSeen` / `clearStubHintSeen` · replay toast | 默认面重播**不得**再恢复能力卡与 stub tip；toast 用 COPY-NAS-REPLAY | P0 |
| **T-NAS-36** | **M10** | llm-settings deeplink / hash | `llm-settings.js` `openLlmSettings({ source: "deeplink" })` 等 | 门控 off：**忽略** deeplink/hash，不弹 Modal | P1 |
| **T-NAS-37** | **M11** | Dock copyRefresh → `startLlmNarrate` | `preview-toolbar/init-v3.js` ~571–578 · `core.js` · task-dock 刷新钮 | 与 T-NAS-08 一并拆掉**触发路径**，不只藏文案 | P0 |
| **T-NAS-38** | **M12** | G1 确认条「将继续生成文案并排版」 | `preview-toolbar-v3-task-dock.js` ~486（管线阶段词，非 LLM） | 建议改为「将继续排版成册」类，降低「AI 写稿」联想 | P2 |

**补漏验收指针**

| M# | 最小验收 |
|----|----------|
| M1 / M11 | 默认面精修抽屉与 Dock **无法**触发 `/__travelogue/narrate` |
| M2 | 保存编辑 toast 无「重新生成文案」 |
| M3 / M4 | 静态禁词扫描覆盖 `constants.js` 与 `capability-card.js` |
| M5 / M6 | 干净首访：无 Modal、无 AI zone sync 文案 |
| M7 / M8 | 失败面无配置焦点/CTA；无「本机游记 vs 写作引擎」教育 |
| M9 | 帮助重播后仍无能力卡、无 stub tip |
| M10 | 带旧 hash/deeplink 打开不弹写作引擎 |
| M12 | （可选）G1 条无「生成文案」易误解措辞 |

---

## 5. 工程与开关合同

### 5.1 门控命名与解析（MF-NAS-02 / MF-NAS-10）

| 层 | 名称 | 规则 |
|----|------|------|
| Env | `TRAVELOGUE_AI_SURFACE` | ∈ `{1,true,on,yes}`（大小写不敏感）→ 开 |
| Config | `studio.ai_surface_enabled` | bool，**默认 `false`** |
| 服务端解析 | `resolve_ai_surface_enabled()` | `env_truthy OR config==true`；否则 `false` |
| Wire | `aiSurfaceEnabled` | `GET /__travelogue/config`（及/或 bootstrap）**只读** bool；**禁止 PATCH** |
| FE helper | `isAiSurfaceEnabled()` | **仅**读 cached `aiSurfaceEnabled`；默认同步 `false`，禁止异步闪出入口 |
| Dev 覆盖 | localStorage/URL | **仅 dev build**；正式包不编译（OQ-NAS-01） |

```
aiSurfaceEnabled := resolve(env ∪ config)   # 仅服务端
FE.isAiSurfaceEnabled() := boot.aiSurfaceEnabled   # 默认 false
```

| `aiSurfaceEnabled` | 行为 |
|--------------------|------|
| `false`（默认） | §4.2 A+E 隐藏；FS 中性；**不因** `llmAvailable` 显示入口；narrate/settings 写硬拒绝 |
| `true` | 恢复 D-NAS-20 清单（**不**恢复能力卡） |

### 5.2 前端合同

- 所有 **T-NAS-01～11** 与 **T-NAS-27～38（M1–M12）** 读同一 helper。  
- **禁止**仅靠 CSS 隐藏；须不渲染或 `hidden` + 不绑定。  
- **`startLlmNarrate` 首行门控早退**（D-NAS-19）；切断 drawers（M1）与 Dock（M11）。  
- `openLlmSettings` **全 source**（settings/card/banner/import_fail/preview_fail/deeplink）中央 gate。  
- 开设置：**切断** `refreshAiStatus` 驱动的写作引擎 CTA；`focus=ai` no-op。  
- 默认面**跳过** `GET /__travelogue/llm/status`；dark ON 再请求。  
- 默认可达禁词：改写、移出默认包，或标 `nas-allow` 且仅 dark 路径可达（不得「只 hidden 仍扫红」）。

### 5.3 后端合同（P0 · 非可选）

**暴露**

```json
GET /__travelogue/config
{ "ok": true, "aiSurfaceEnabled": false, "llmAvailable": true, "...": "..." }
```

- `aiSurfaceEnabled` 与 `llmAvailable` 并列顶层；前者门控 UI/API，后者供 dark 回归。  
- **不**加入 `patch_config_file` / `allowed_studio`。

**`POST /__travelogue/narrate`（门控 off）**

```http
HTTP/1.1 403
{ "ok": false, "error": "E_AI_SURFACE_DISABLED", "message": "当前版本不可用" }
```

- 检查点：解析 `tripId` 之后、**任何** `studio_llm_status` / Job 创建之前。  
- **禁止**复用 `E_LLM_AUTH`（会点燃失败面配置 CTA）。  
- 门控 on：保持既有 400 `E_LLM_AUTH` / 202 Job 行为。

**`/llm/settings` 写入（门控 off）** → **403** + 同错误码或专用写拒绝码（中性 message）。  
**`GET /llm/status`（门控 off）** → **403** + `E_AI_SURFACE_DISABLED`；**禁止**先组装再过滤敏感字段；检查点在 `_status_body` / secrets / 本机目录读取之前（[QFX](./PRD-QUALITY-FIXPACK-V1.md) D-QFX-04）。  
**`GET /__travelogue/config`（门控 off）** → **200 可保留**（hydration 依赖），但须执行 **D-NAS-17b** 投影收口（[QFX](./PRD-QUALITY-FIXPACK-V1.md) D-QFX-04b · AC-QFX-27）。  
**`/llm/ping`（门控 off）** → 写/探测路径 **403**；dark ON 可回归。默认面 FE 不调用 status。

### 5.4 安全与隐私

- 继承 ADR-019：密钥不进遥测、不进 trip；NAS **不要求删除**磁盘 secrets。  
- 默认面不展示 Key UI；analytics 禁止 Key / `maskedKey`；`ai_surface_gate` 见 §7。  
- 服务端日志不得 dump settings 请求体中的 `apiKey`。

### 5.5 工程冻结清单与 dark 回归节奏（底座保留）

> **目的**：保证 AI-Return 不必重做 DLLM/WEA；NAS 编码只做门控与默认可达文案面。

#### 5.5.1 绝对冻结（本期不得拆除）

| 资产 | 说明 |
|------|------|
| `travelogue/llm/**` · `llm/client.py` · presets | 文本 LLM 运行时 |
| ADR-019 secrets · `user_settings` · launcher inject | 密钥落盘与注入 |
| `/__travelogue/llm/status|settings|ping` | 配置 API（门控 off：settings 写 / status 读 / ping 均 403；dark ON 可回归） |
| `run_studio_llm_narrate` · narrate Job · `llm_narrate` | 杂志感生成管线 |
| WEA 配置面与 ping 状态机 | dark 下可回归 |
| `*_ai_surface_dark` / DLLM·WEA dark 附录测试 | **禁止「删断言了事」** |
| Prompt / `narrative_scope` 主契约 | 可修缺陷；**不借 NAS 做大重构** |
| 用户已落盘 Key | **不迁移、不清除** |

#### 5.5.2 本期允许改动

- Studio 默认面 UI/文案门控、禁词审计、错误码 `E_AI_SURFACE_DISABLED`  
- 导入失败 / Help / FirstSuccess 去 AI 引导  
- 为 dark 包增加 `nas-allow` 标记  

#### 5.5.3 Dark 回归节奏（防底座腐烂）

| 节奏 | 内容 | Owner 建议 |
|------|------|------------|
| **W3 一次性** | AC-NAS-09 全套（设置 + ping + Sheet/抽屉 narrate） | 工程 |
| **此后每月 ≥1 次** | 同上冒烟（内部狗粮机 `TRAVELOGUE_AI_SURFACE=1`） | 工程 on-call / 发版前 |
| **正式包** | 永不附带 dark UI 入口；仅 env/config | 发布 |

---

## 6. 文案冻结表（COPY-NAS-*）

> 实施以本表为准；润色可微调语气，**不得**重新引入禁词。

### 6.1 废止（默认面不得出现）

| 旧文案（示例） | 处置 |
|----------------|------|
| 以后再升级 AI 文案 → | 不展示 |
| AI 文案 / 配置写作引擎… / 管理写作引擎… | 不展示 |
| 重新生成文案（LLM 工具行 / Dock / toast 引导） | 不展示 |
| 按新感觉重写这段（抽屉 LLM 入口） | 不展示（默认面） |
| 更好的文案可稍后自行升级（可选） | 不展示 / 改写（随能力卡） |
| 继续生成本机游记（与 AI 对立义） | 隐藏或改为「继续生成游记」 |
| 将继续生成文案并排版（G1，易误解） | 建议改为「将继续排版成册」（M12） |
| 当前为本机文案 · 配置写作引擎后可升级 | 不展示 |
| AI 文案已就绪；重新生成不会自动覆盖… | 不展示 |
| AI 文案已就绪，可为这本重新生成文案 | 不展示 |
| 要不要配置 AI 文案（H7 全篇） | 删除 |
| 不配置 AI 文案也可以…（H0） | 改写 |
| 游记已做好…当前为本机文案；配置写作引擎后可在预览升级 | 改写 |
| 游记已做好…AI 文案已就绪，可在预览重新生成 | 改写 |
| 当前为本机文案（可随时在设置中升级） | 不展示 |
| 杂志感文案暂不可用 / 去配置写作引擎 | 不展示（失败面） |
| 打开设置 → AI 文案，粘贴 API Key…（默认面错误 hint） | 不展示 |

### 6.2 新文案（冻结稿）

| ID | 场景 | 文案 |
|----|------|------|
| **COPY-NAS-FS-01** | FirstSuccess 下一句（**唯一精确串**） | 画册已做好，可预览与导出长图。 |
| **COPY-NAS-H0-01** | 帮助 H0 要点（替换 AI 句） | 选好一次旅行的相册，即可在本机完成分章、排版，并导出适合发群的竖版长图。 |
| **COPY-NAS-H0-02** | 帮助 H0 可增补 | 预览里点文字即可改；导出可选纯照片，照片永远是主角。 |
| **COPY-NAS-SET-DESC** | 设置总述 | 导入偏好、存储位置与界面选项。改动会立即保存。 |
| **COPY-NAS-REPLAY** | 帮助重播完成 toast | 已重置。下次进入预览会再提示如何保存长图；再次打开精修时会再看到保存说明；切换分享平台、展开首尾装帧时也会再提示；下次导入等待时也会再显示小提示。 |
| **COPY-NAS-FAIL-01** | 通用导入失败下一句（取代配置 CTA） | 检查文件夹是否仍可访问、照片是否足够，然后点「重试」或换文件夹再试。 |
| **COPY-NAS-CAP-NONE** | 能力卡 | （不展示；无替代卡） |
| **COPY-NAS-DRAWER-SAVE** | 精修抽屉保存 toast（M2） | 编辑已保存。 |
| **COPY-NAS-FAIL-CONTINUE** | 失败面续跑 CTA（M8，若仍展示） | 继续生成游记 |
| **COPY-NAS-G1-NEXT** | G1 确认条副文案（M12） | 请浏览各章顺序后确认，将继续排版成册 |
| **COPY-NAS-NARRATE-403** | `E_AI_SURFACE_DISABLED` 用户 message | 当前版本不可用 |

### 6.3 允许保留的用户词（白名单）

| 词 | 允许语境 | 禁止语境 |
|----|----------|----------|
| 智能挑选 / 智能排版 / 智能匹配 | 设置与向导算法能力 | 「智能 AI 文案」 |
| 杂志感 | 「版式更有杂志感」「节奏更贴杂志」 | 「杂志感文案」「升级杂志感」 |
| 点缀 / 一句话 / 标题 | 精修手工编辑 | 「AI 生成点缀」作为卖点 CTA |

### 6.4 品牌 eyebrow（OQ-NAS-02）

- **默认建议（本版）**：保留既有「智能游记画册」类 eyebrow（「智能」≠ 外部 LLM）。  
- 若评审认为易联想生成式 AI，可改为「游记画册」——属文案微调，不阻塞 W1 门控。

---

## 7. 埋点

| 事件 | NAS 默认面 | dark ON / AI-Return |
|------|------------|---------------------|
| `capability_card_*` | 不应再发（卡不 show） | 可选；事件**定义保留** |
| `llm_settings_*` / `llm_save_and_ping` / `llm_narrate_click` | 默认面不应再发 | **沿用**；定义不得从 analytics 白名单删除 |
| `refine_copy_branch` / `first_success_copy_branch` | 恒 `nas_hidden` 或停发 | 可恢复 L0/L1 |
| **`ai_surface_gate`（必做）** | 会话首次 `{ enabled: false }` 一次 | `{ enabled: true }` |

**下期预留**：不删除 `llm_*` 事件 schema，以便 AI-Return 立刻能量「打开设置 → 保存 ping → narrate」漏斗。  
禁止：任何 payload 含 API Key。

---

## 8. 非功能

| 项 | 要求 |
|----|------|
| **A11Y** | 少一层能力卡 dialog；设置/帮助焦点序不因隐藏 zone 断裂 |
| **性能** | 默认面可少一次 llm/status 请求 |
| **兼容** | 旧 localStorage seen 键可残留，但无 UI 读取副作用；**已有 secrets 保留** |
| **打包 / 双轨** | **正式包**默认 `aiSurfaceEnabled=false`，冒烟 = 无禁词 + 纯照片长图；**内部狗粮**可用 env 开 dark，**不对外宣称「又有 AI」** |
| **发布说明（建议）** | 一句即可：「本版专注本机成册与长图导出；写作增强将在后续版本开放。」不必做应用内横幅 |
| **i18n** | 本版中文；禁词表以中文为准 |
| **测试** | 默认可达禁词 CI + dark 分 job；Playwright 狗粮覆盖出图主链 |

---

## 9. 里程碑（W0–W3）

| 波次 | 范围 | 产出 | Go / No-Go |
|------|------|------|------------|
| **W0** | 评审 · MF 回写 v0.2 · ACCEPTANCE 初稿 · 禁词扫描语义签字 | Conditional Go（MF 已回写） | ✅ 纪要 + 本文 v0.2 |
| **W1** | BE：`aiSurfaceEnabled` + narrate/settings 硬拒绝；FE：门控 + 首页/设置/帮助/成功/失败（M3–M10） | 首页侧默认可达禁词 0；API 硬拒绝绿 | AC-NAS-01～04 · 08（分区）· 13 · 15～16 |
| **W2** | 预览 Sheet/Dock/抽屉/`startLlmNarrate`；单测翻转；长图狗粮；SFI/Help/CSC 指针 | 默认面 **0× /narrate**；全量禁词（默认可达） | AC-NAS-05～07 · 11 · 14 · 08（全量）· 17 |
| **W3** | dark 恢复冒烟（D-NAS-20）；ERROR-CODES；打包清单 | 可标 V1 Done | AC-NAS-09～10 · 12 |

**建议工期**：W1 1.5–2.5d（含 BE）· W2 1–2d · W3 0.5–1d。  
**编码启动门**：W0 MF 已回写（本文）→ 可开 W1。

---

## 10. 验收（AC-NAS-*）

| ID | 验收项 | 方法 | 波次 |
|----|--------|------|------|
| **AC-NAS-01** | 干净环境首访：**无**能力卡 | 手测 / e2e | W1 |
| **AC-NAS-02** | 设置无「AI 文案」「写作引擎」字符串与入口；开设置不渲染写作引擎 CTA | 手测 + 静态 | W1 |
| **AC-NAS-03** | 帮助无 H7；H0 无 AI 文案句 | 手测 + 静态 | W1 |
| **AC-NAS-04** | FirstSuccess 文案 **精确等于** COPY-NAS-FS-01 | e2e / 静态 | W1 |
| **AC-NAS-05** | 预览精修「这本 / 整本信息」无「重新生成文案」与 llm-setup | 手测 / e2e | W2 |
| **AC-NAS-06** | Task Dock 无 AI 文案就绪条 /「重新生成文案」钮 | e2e | W2 |
| **AC-NAS-07** | 导入 → 预览 → **纯照片长图**成功 | 狗粮 | W2 |
| **AC-NAS-08** | 禁词审计按附录 C **默认可达面**语义通过（W1 分区 / W2 全量） | CI | W1–W2 |
| **AC-NAS-09** | dark ON：设置可配 + Sheet/抽屉可 narrate；**能力卡仍不出现** | 手测 | W3 |
| **AC-NAS-10** | dark OFF + 磁盘已有 secrets：UI 仍无入口；narrate 仍 403 | 手测 / unit | W3 |
| **AC-NAS-11** | Wait Tips 文案非回归；Importing 无能力卡 | 手测 / 既有 e2e | W2 |
| **AC-NAS-12** | 默认面会话：无强制 `openLlmSettings`；analytics/network spy 无 Key 明文 | e2e spy / unit | W3 |
| **AC-NAS-13** | 门控 off：`POST /__travelogue/narrate` → **403** / `E_AI_SURFACE_DISABLED`（有 Key 亦然） | unit / e2e | W1 |
| **AC-NAS-14** | 默认面抽屉无「按新感觉重写」；保存 toast 无「重新生成文案」；会话 **0×** `POST /narrate` | e2e network | W2 |
| **AC-NAS-15** | `openLlmSettings` 全 source no-op；`?llmSetup=1` 不弹窗 | e2e | W1 |
| **AC-NAS-16** | 帮助重播后无能力卡、无 stub tip、无 home stub banner | e2e | W1 |
| **AC-NAS-17** | 门控 off：`/llm/settings` **写入** → 403；dark job 单独跑 AC-NAS-09（与默认面禁词扫分 job） | unit | W1 / W3 |

---

## 11. 风险与开放问题

### 11.1 风险

| ID | 风险 | 缓解 |
|----|------|------|
| **R-NAS-01** | 用户以为「不能改文案」 | D-NAS-15；帮助强调点文字可改 |
| **R-NAS-02** | 禁词误伤「智能排版 / 杂志感版式」 | D-NAS-12 + 附录 C 白名单 |
| **R-NAS-03** | DLLM 静态单测大面积红 | W1 同步翻转/拆分测试 |
| **R-NAS-04** | dark switch 被终端用户发现 | 无 UI；仅 env/config；不写进帮助 |
| **R-NAS-05** | 文档双轨（DLLM vs NAS）混乱 | D-NAS-11 + DOC-STATUS 明示 |
| **R-NAS-06** | 外站/项目介绍仍写「可选 LLM」 | OQ-NAS-03；可本版脚注「Studio 当前版本默认无 AI 面」 |

### 11.2 开放问题（OQ）

| ID | 问题 | 状态 |
|----|------|------|
| **OQ-NAS-01** | dark switch 是否允许 URL hash 调试 | **开放**：正式包仅 env/config；dev 可覆盖 |
| **OQ-NAS-02** | eyebrow「智能游记画册」是否改名 | **开放**：本版默认保留；发版前可改「游记画册」；不挡 W1 |
| **OQ-NAS-03** | `docs/项目介绍.md` 是否同步 | **开放**：W3 脚注即可 |
| **OQ-NAS-04** | dark ON 是否恢复能力卡 | **已关闭**：不恢复（D-NAS-20） |
| **OQ-NAS-05** | narrate 硬拒绝 vs 软忽略 | **已关闭**：403 + `E_AI_SURFACE_DISABLED`（D-NAS-16 · AC-NAS-13） |

### 11.3 Must-Fix 回写对照（MF-NAS → 本文）

| MF | 落点 |
|----|------|
| MF-NAS-01 | D-NAS-16 · §5.3 · AC-NAS-13 · COPY-NAS-NARRATE-403 |
| MF-NAS-02 | D-NAS-18 · §5.1 |
| MF-NAS-03 | D-NAS-17 · AC-NAS-17 |
| MF-NAS-04 | D-NAS-19 · AC-NAS-14 · F-NAS-03 |
| MF-NAS-05 | D-NAS-10 · 附录 C 扫描语义 · §9 W1/W2 |
| MF-NAS-06 | F-NAS-08 · ACCEPTANCE 翻转清单 · 附录 A |
| MF-NAS-07 | 文首 V1 Done 边界 · §2.2 非目标 |
| MF-NAS-08 | D-NAS-11 · ACCEPTANCE 已建 · DOC-STATUS |
| MF-NAS-09 | D-NAS-06/07/08 · AC-NAS-04/15/16 · §5.2 |
| MF-NAS-10 | §5.1 命名表 |

---

## 12. 附录

### 附录 A · 实现锚点（W1/W2 文件清单）

| 区域 | 路径 |
|------|------|
| 门控 helper | 新建建议 `templates/studio/js/ai-surface.js` |
| 能力卡 | `templates/studio/js/capability-card.js` · `capability-card.css` |
| 首页引导 | `templates/studio/homepage-v2/bootstrap.js` · `first-success.js` · `import-failed.js` |
| 设置 | `templates/studio/studio-home-v2.html` · `homepage-v2/settings-panel.js` |
| LLM Modal | `templates/studio/js/llm-settings.js` · `llm-readiness.js` |
| 帮助 | `templates/studio/js/help-onboarding.js` |
| 错误句 | `templates/studio/js/errors.js` · `templates/studio/js/constants.js`（M3）· `travelogue/web/studio_errors.py` |
| 预览 | `preview-toolbar-v3-sheet.js` · `preview-toolbar/init-v3.js` · `preview-toolbar/core.js` · `preview-toolbar-v3-task-dock.js` · **`preview-toolbar/drawers.js`（M1/M2）** |
| Stub banner | `templates/studio/js/home-stub-banner.js` |
| 后端（P0） | `export_handlers.handle_narrate` · `llm_settings_handlers.py` · config loader / bootstrap · `studio_errors`（新错误码） |
| 测试翻转（完整清单） | `test_desktop_llm_setup_w2.py` · `test_l0_guidance_hardening_fe.py` · `test_preview_toolbar_v3.py` · `test_sfi_dock_arbitration.py` · `test_ux_trust_v1.py` · `test_studio_home_v2.py` / settings accordion · 新建 `test_no_ai_surface_*.py` + `*_ai_surface_dark.py` |
| 审计 | 新建建议 `scripts/studio_no_ai_surface_audit.py`（默认可达面语义） |

### 附录 B · 与 DLLM 决策对照

| DLLM 决策 | NAS 处置 |
|-----------|----------|
| D-DLLM-01 能力卡 | **默认永不 show** |
| D-DLLM-02 导入 stub | **保持** |
| D-DLLM-03 设置含 AI 组 | **默认移除用户面** |
| D-DLLM-06/07 升级文案 / H7 | **废止** |
| D-DLLM-08 忙碌态 | **保持并加强** |
| US-P2-08 可选杂志感 | **产品面暂停** |
| G-P2-05 不强制 Key | **保持并强化为「不暴露 Key」** |

### 附录 C · 禁词表与白名单（审计用 · MF-NAS-05）

#### C.1 扫描语义（冻结）

| 规则 | 说明 |
|------|------|
| **默认可达面** | 默认门控 off 时，用户可不经 dark switch 看到的 HTML 文本与 JS 字符串字面量（含 hidden 但仍随默认包下发、且未标 `nas-allow` 的串） |
| **dark-only** | 仅 `aiSurfaceEnabled===true` 路径使用的模块/字符串块；须文件头或块注释含 `nas-allow`（或列入审计 exclude 表） |
| **不扫** | JS/HTML **标识符与属性名**、纯 URL path、`docs/`、`tests/` 夹具（除非夹具模拟默认面 UI） |
| **分波** | W1：首页/设置/帮助/成功/失败相关文件；W2：全量 `templates/studio` 默认可达面 |
| **分 job** | 默认面 AC-NAS-08 与 dark AC-NAS-09 **禁止**混跑同一禁词断言 |

#### C.2 禁词（默认可达面）

- `AI 文案`
- `写作引擎`
- `配置写作引擎`
- `管理写作引擎`
- `升级 AI`
- `杂志感文案`
- `生成杂志感`
- `API Key`（引导用户申请/粘贴的话术）
- `DeepSeek` / `通义` / `dashscope`（设置引导话术；dark-only 可留）
- `重新生成文案`
- `按新感觉重写这段`
- `更好的文案可稍后自行升级`
- `继续生成本机游记`
- `本机文案`（与 AI 对立教育句）
- `以后再升级`
- Soft（dogfood）：`将继续生成文案并排版`（建议 M12 改掉）

#### C.3 白名单

- `智能挑选` / `智能排版` / `智能匹配` /（可选）`智能游记画册`
- 版式 hint：`杂志感`（邻近窗口不含「文案/升级/AI」）
- `继续生成游记`（COPY-NAS-FAIL-CONTINUE）
- `当前版本不可用`（COPY-NAS-NARRATE-403）
- 标 `nas-allow` 的 dark-only 块

### 附录 D · 首访一览（默认面）

```
打开应用
  → 首页（无能力卡）
  → 设置（无 AI zone）· 帮助（无 H7）
  → 导入相册 → Wait Tips（可）
  → FirstSuccess：「画册已做好，可预览与导出长图。」
  → 预览 / 精修（可手工改字；无重新生成文案）
  → 纯照片长图 → 发群指引
```

### 附录 E · 线框建议（可选）

| 帧 | 内容 |
|----|------|
| F1 | 设置 Modal：仅导入偏好 + 存储…；无 AI zone |
| F2 | 预览精修「这本」：整本信息区无 llm 工具行 |
| F3 | FirstSuccess：中性一句 + 主 CTA 预览/长图 |

---

## 13. 评审审核清单

- [x] **七条铁律**无异议（Conditional Go · v0.2.1 增「分期不混 KPI」）  
- [x] 禁词表 / 扫描语义签字（附录 C · v0.2）  
- [x] dark switch = env/config；无 UI（D-NAS-03）  
- [x] OQ-NAS-04/05 关闭  
- [ ] OQ-NAS-02 eyebrow（发版前）  
- [x] SFI / Help / CSC 文档指针责任人点名（W2 · DOC-NAS-02：产品合同 · 工程门控 · 2026-07-22）  
- [x] 非目标：不硬删 LLM；深度 polish 另立（MF-NAS-07）  
- [x] AC-NAS-01～17 已写入 §10 / ACCEPTANCE  
- [x] M1–M12 + narrate 硬拒绝纳入实施  
- [x] MF-NAS-01～10 已回写本文 v0.2.0  
- [x] **v0.2.1**：§2.3 出图北极星 · §5.5 冻结清单 · §14 解冻合同 · D-NAS-21/22  

---

## 14. 分期 · AI-Return 解冻合同（下期指针）

> **本文档不交付 AI-Return。**  
> 本节约束：NAS 编码与发版**不得堵死**下期；AI-Return 另立 PRD 时可直接引用本表作 Kickoff 门闩。  
> **下期产品合同已立：** [PRD-AI-RETURN-V1.md](./PRD-AI-RETURN-V1.md)（**AIR** · v0.1.0 Draft · 2026-07-29）。装帧导演见并行 [PRD-COVER-ART-DIRECTION-V1.md](./PRD-COVER-ART-DIRECTION-V1.md)，**不**混入 NAS/AIR 解冻 KPI。

### 14.1 产品分期（完整表）

| 期 | 用户面承诺 | 工程态度 | KPI（互不混用） |
|----|------------|----------|-----------------|
| **本期 · NAS** | 看不见 / 配不了 / 用不到 AI；主链 = 导入 → 预览 → **纯照片长图** | Hide + 硬拒绝；底座见 §5.5 **冻结保留** | OUT-01～05（§2.3） |
| **下期 · AI-Return**（建议代号） | 再开放杂志感文案（或更强卖点） | 开 `aiSurfaceEnabled`（或产品化开关）；在保留栈上迭代 | 配置转化 · 升级完成 · 文案满意度 · LLM 成功率 |
| **禁止** | 把 NAS 写成「永远不要 AI」；为过禁词洁癖删源 | 拆除 llm / secrets / narrate / WEA / dark 附录 | 用本期 KPI 考核 AI；用 AI KPI 绑架出图 |

一句话：**NAS = 用户面休眠；AI-Return = 用户面解冻并迭代。**

### 14.2 解冻合同（Wake Contract · 产品默认）

| 项 | 下期默认（除非 AI-Return PRD 另决） |
|----|-------------------------------------|
| **解冻触发** | 先恢复门控 `aiSurfaceEnabled=true`；再决定产品入口放在「设置 / 高级 / AI 文案」哪一层 |
| **解冻最小包** | 设置 AI zone + 预览「重新生成文案」一类 CTA + 保存并测试（ping）+（可选）自动升级叙事 |
| **能力卡** | **另议**是否恢复首启硬推；**不要**默认恢复（与 D-NAS-20 一致） |
| **文案密度** | 是否解开 `scope=frame` → `frame_chapters` / 强度调整 **属 AI-Return 卖点**；本期维持 BE-SFI-06 |
| **密钥与升级用户** | 已落盘 Key **必须仍可用**；解冻后不应强制重新粘贴 |
| **错误码** | `E_AI_SURFACE_DISABLED` 在解冻包中应不再成为默认可达路径；文档注记「门控恢复后不再返回」 |
| **埋点** | 复用保留的 `llm_*` / `llm_narrate_click` 等 schema（§7）；补 AI-Return 漏斗，不另起一套互斥命名 |
| **测试** | 恢复默认面 AC 时，先翻回 DLLM/WEA 用户面合同；dark 附录可升格为默认 job |
| **成功判据** | AI-Return Done ≠ NAS Done；必须以**配置/升级/文案质量**单独验收 |

### 14.3 NAS → AI-Return 交接检查（Kickoff 前）

| # | 检查项 | 证据 |
|---|--------|------|
| 1 | §5.5.1 冻结资产仍在仓库且可 import | 路径存在 + 单测可跑 |
| 2 | AC-NAS-09 月度冒烟最近一次绿 | 内部狗粮记录 |
| 3 | 默认可达禁词审计与 dark 分 job 仍有效 | CI 配置 |
| 4 | 用户 secrets 路径未改、未清 | ADR-019 + 升级狗粮 |
| 5 | FE 门控单点（`aiSurfaceEnabled`）可翻转 | bootstrap / `GET /config` |
| 6 | 新 PRD 已显式继承 D-NAS-20（能力卡默认不恢复）或正式推翻 | AI-Return PRD §决策 |

### 14.4 与相邻主题边界（再钉一次）

| 主题 | NAS 关系 | AI-Return 关系 |
|------|----------|----------------|
| Photos-Mainline / FTT / SFI 出图 polish | 另立；NAS 只保证零岔路可达 | 可并行，不阻塞解冻 |
| DLLM / WEA | 工程 active；用户面 dormant | 用户面合同重新激活并迭代 |
| SFI「重新生成文案」 | 默认面废止入口 | 解冻后可再接管用户面合同 |

---

## 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.2.3+ptr** | 2026-07-29 | §14 挂接 [PRD-AI-RETURN-V1](./PRD-AI-RETURN-V1.md) / [PRD-COVER-ART-DIRECTION-V1](./PRD-COVER-ART-DIRECTION-V1.md) 指针（**未改业务代码**） |
| **v0.2.1** | 2026-07-22 | **分期 / 冻结 / 解冻 / 出图北极星**：七条铁律 · OUT-01～05 · §5.5 · §14 · D-NAS-21/22 · 埋点预留 · 双轨发布；**未改业务代码** |
| v0.2.0 | 2026-07-22 | **Must-Fix 回写**：D-NAS-16～20 · §5 门控/BE P0 · AC-NAS-13～17 · 附录 C 扫描语义 · V1 Done 边界 · 关 OQ-04/05 |
| v0.1.1 | 2026-07-22 | §4.2 E 回写前端补漏 **M1–M12**（T-NAS-27～38）；COPY / 禁词 / 附录 A / §5.2 同步；挂接 IMPLEMENTATION 前端任务卡 |
| v0.1.0 | 2026-07-22 | 初稿：无 AI 面冻结合同 · 触点矩阵 · 文案表 · W0–W3 · AC-NAS-* |
