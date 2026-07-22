# 当前版无 AI 面 NAS V1 · 跨职能评审会结论

| 属性 | 内容 |
|------|------|
| **会议日期** | 2026-07-22 |
| **材料** | [PRD-NO-AI-SURFACE-V1.md](../PRD-NO-AI-SURFACE-V1.md) **v0.1.1** · [IMPLEMENTATION-NO-AI-SURFACE-V1.md](../IMPLEMENTATION-NO-AI-SURFACE-V1.md) **v0.1.0** |
| **形式** | 跨职能书面评审（产品 · 架构 · 前端 · 后端 · 测试） |
| **结论状态** | **有条件通过（Conditional Go）** · **Must-Fix 已回写 PRD v0.2.0** · ACCEPTANCE 已建 · **可开 W1 编码** |
| **记录人** | 联合纪要（专家席并行评审汇总） |
| **前置** | 导入主链已强制 stub；纯照片长图不依赖 LLM；DLLM/WEA 工程已落地；NAS 为用户面现行合同候选 |

---

## 1. 与会角色

| 角色 | 关注点 |
|------|--------|
| **产品** | 北极星、主线打磨边界、COPY/AC 是否支撑「看不见也用不到」、升级用户信任 |
| **架构** | 门控单一真相源、FE/BE 一致、narrate/settings 硬拒绝、文档双轨、泄露路径 |
| **前端** | 触点完整性（M1–M12）、FE-NAS 卡可开工性、静态禁词 vs Hide、单测翻转 |
| **后端** | `aiSurfaceEnabled` 暴露、`POST /narrate` 契约、导入是否已安全、错误码 |
| **测试** | AC 可测性、禁词审计语义、负例、DLLM 测试翻转矩阵、dark 回归包 |

---

## 2. 总评（一句话）

> **方向正确：Hide-don't-delete、主线与 LLM 解耦、M1–M12 补漏与 FE-NAS 卡对齐决策。阻塞不在「要不要藏 AI」，而在五处合同未钉死：①「用不到」未升为 narrate（及 settings 写）硬拒绝；② bootstrap `aiSurfaceEnabled` 为 FE 唯一真相源未强制；③ AC-NAS-08 静态禁词与 dark 包共存无扫描语义；④ M1/M11 未进入正式 AC；⑤ DLLM/L0G/SFI 等单测翻转清单过窄。**

**表决**：五席一致 **Conditional Go**（前端/测试强调「文档可评、未可直接按卡开工」→ 汇总为同一结论：MF 回写后开 W1）。

| 角色 | 表决 | 一句话 |
|------|------|--------|
| 产品 | Conditional Go | 铁律对；AC 落后于 P0 触点；「主线打磨」勿超售 |
| 架构 | Conditional Go | FE 切断必要但不完整；BE 门控 + narrate 403 须升 P0 |
| 前端 | Conditional Go* | 触点齐；禁词包装/同步门控/`startLlmNarrate` 硬门闩未写清则勿开工 |
| 后端 | Conditional Go | 导入已安全；最小闭环 = 只读 flag + narrate 先行 403（独立错误码） |
| 测试 | Conditional Go* | AC-08/M1/M11/负例/翻转清单不补则假绿或永红 |

\*前端/测试原文倾向「Conditional No-Go（可测性/可开工）」——与产品/架构/后端的 Conditional Go 合并为：**W0 Must-Fix 关闭前不开编码**。

**对齐评分（主观）**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题定义 | 9 | 根因判断准：支线暴露而非主链缺 LLM |
| 范围克制 | 7 | 非目标清楚；标题「主线打磨」易超售 |
| 体验合同完整度 | 8 | 剧本/触点/M1–M12 强；完成面「纯照片」略糊 |
| 工程可开工性 | 5 | 门控真相源与硬拒绝未钉死 |
| AC 可测性 | 5 | AC-08 语义空；M1/M11 未进 §10；ACCEPTANCE 待建 |
| 与相邻 PRD 仲裁 | 6 | DLLM superseded 有意向；SFI/Help/CSC 指针责任未落 |

---

## 3. 分角色意见摘要

### 3.1 产品

| 态度 | 要点 |
|------|------|
| ✅ | 六条铁律、D-NAS-01/14、T-NAS + M1–M12、FE-NAS 与决策一致 |
| 🔴 MF | **BLK-NAS-P-01**：M1/M2/M11 须升格正式 AC（建议 AC-NAS-13/14） |
| 🔴 MF | **BLK-NAS-P-02**：「用不到」须可验收（narrate 硬拒绝或等价零请求进 AC） |
| 🔴 MF | **BLK-NAS-P-03**：V1 Done 边界签字——藏 AI + 主线可达，或补 polish AC；禁止标题超售 |
| 🔴 MF | **BLK-NAS-P-04**：禁词审计分波（W1 首页侧 / W2 全量） |
| ⚠️ | FS 完成句未点「纯照片」；升级用户缺变更说明；OQ-NAS-04 删「另议」 |
| 📌 | 收口顺序：BLK-02/03/04 → M1/M11 入 §10 → 再开 FE-NAS-00 |

### 3.2 架构

| 态度 | 要点 |
|------|------|
| ✅ | 导入 stub 已解耦；Hide-don't-delete + M1–M12 正确 |
| 🔴 MF | **BLK-NAS-A-01**：FE 不能读进程 env → **BE 必须**下发 `aiSurfaceEnabled`（BE-NAS-01 升 P0） |
| 🔴 MF | **BLK-NAS-A-02**：`POST /narrate` 硬拒绝升 V1 Must（现网有 Key 仍会 202） |
| 🔴 MF | **BLK-NAS-A-03**：门控 off 时 settings **写入**亦应 403（「配不了」） |
| 🔴 MF | **BLK-NAS-A-04**：冻结命名（env / config / wire / helper） |
| 🔴 MF | **BLK-NAS-A-05**：DOC Draft vs active、ACCEPTANCE、相邻文 superseded 指针闭环 |
| 📌 | 完整架构 = FE 全触点 + bootstrap flag + narrate/settings 硬拒绝 + dark 恢复（默认不恢复能力卡） |

### 3.3 前端

| 态度 | 要点 |
|------|------|
| ✅ | M1–M12 锚点存在；FE-NAS-00→W1→W2(09+10)→W3 骨架合理 |
| 🔴 MF | **BLK-NAS-FE-01**：Hide vs AC-08——须「改写 / dark-only 标记 / 移出默认可达面」写入卡 |
| 🔴 MF | **BLK-NAS-FE-02**：门控默认同步 false + 同步注入，禁异步闪出入口 |
| 🔴 MF | **BLK-NAS-FE-03**：`startLlmNarrate` **函数级**早退（不只藏 UI） |
| 🔴 MF | **BLK-NAS-FE-04**：翻转清单扩至 L0G / SFI dock / preview v3 / UX Trust / home settings |
| 🔴 MF | **BLK-NAS-FE-05**：FE-NAS-14 全绿门禁挂 W2 末，或 W1 分区扫 |
| 🔴 MF | **BLK-NAS-FE-06**：M9 须含 `clearHomeStubBannerDismissed` |
| 🔴 MF | **BLK-NAS-FE-07**：切断 `refreshAiStatus` / `focus=ai`（不只 hidden zone） |
| 🔴 MF | **BLK-NAS-FE-08**：FS COPY 精确对齐；死文案 L0/L1 串须隔离 |
| ⚠️ | `openLlmSettings` 全 source 中央 gate；core.js 失败确认禁词；无独立 `task-dock.js` 文件名 |

### 3.4 后端

| 态度 | 要点 |
|------|------|
| ✅ | **导入路径已安全**，NAS 导入侧无需 BE 改动 |
| 🔴 MF | **BLK-NAS-BE-01**：硬拒绝统一 **HTTP 403**（不用 404） |
| 🔴 MF | **BLK-NAS-BE-02**：独立错误码 `E_AI_SURFACE_DISABLED`（**禁止**复用 `E_LLM_AUTH`） |
| 🔴 MF | **BLK-NAS-BE-03**：门控检查在 `studio_llm_status` / Job **之前** |
| 🔴 MF | **BLK-NAS-BE-04**：`aiSurfaceEnabled` 只读，**不进** PATCH allowlist |
| 🔴 MF | **BLK-NAS-BE-05**：拒绝 `message` 中性、无禁词 |
| 📌 | `/llm/status|settings|ping` 保留；settings **写**在门控 off 建议 403（与架构 A-03 对齐） |

### 3.5 测试

| 态度 | 要点 |
|------|------|
| ✅ | 分层矩阵清晰；dark 与默认面须分 job |
| 🔴 MF | **BLK-NAS-QA-01**：AC-08 扫描语义 + `nas-allow` 语法 |
| 🔴 MF | **BLK-NAS-QA-02**：M1/M11 入正式 AC（含 network 0× `/narrate`） |
| 🔴 MF | **BLK-NAS-QA-03**：禁词假阳性规则（勿扫标识符/URL） |
| 🔴 MF | **BLK-NAS-QA-04**：负例 AC（M7/M9/M10/AC-10） |
| 🔴 MF | **BLK-NAS-QA-05**：AC-12 从「抽查」改为可断言 |
| 🔴 MF | **BLK-NAS-QA-06**：完整测试翻转清单 |
| 🔴 MF | **BLK-NAS-QA-07**：FS-01 oracle 锁死精确串 |
| 🔴 MF | **BLK-NAS-QA-08**：建立 ACCEPTANCE-NO-AI-SURFACE-V1 |
| 📌 | 翻转策略：`*_nas_default` + `*_ai_surface_dark`，禁止只删断言 |

---

## 4. Must-Fix 合并清单（W0 回写 PRD）

> 下列为跨席共识；回写后关闭 OQ-NAS-05，升 BE-NAS-01/02，补 AC-NAS-13+，再建 ACCEPTANCE。

| 合并 ID | 来源 | 冻结内容 |
|---------|------|----------|
| **MF-NAS-01** | P-02 · A-01/02 · BE-01～05 · QA-02 | 门控 off：`POST /narrate` → **403** + `E_AI_SURFACE_DISABLED` + 中性 message；检查顺序先于 Key；列入正式 AC |
| **MF-NAS-02** | A-01 · FE-02 · BE-04 | 服务端解析 env∪config → bootstrap/`GET /config` 下发只读 **`aiSurfaceEnabled`**；FE helper **仅**读该字段；**禁止 PATCH** |
| **MF-NAS-03** | A-03 · BE（settings 写） | 门控 off：`/llm/settings` **写入** 403；status/ping 策略：status 可读、默认面 FE 不请求 |
| **MF-NAS-04** | P-01 · FE-03 · QA-02 | §10 新增 AC：默认面 **抽屉无「按新感觉重写」** + Dock/抽屉/**`startLlmNarrate`** 均不可达 + **0× POST /narrate** |
| **MF-NAS-05** | P-04 · FE-01/05 · QA-01/03 | 禁词审计合同：默认可达面 vs dark-only（`nas-allow`）；W1 分区 / W2 全量；勿扫标识符 |
| **MF-NAS-06** | FE-04 · QA-06 | FE-NAS-14 / ACCEPTANCE 列出完整翻转清单（DLLM w2 + L0G FE + SFI dock + preview v3 + UX Trust + settings） |
| **MF-NAS-07** | P-03 | V1 Done = **无 AI 面 + 主线狗粮（AC-NAS-07）**；深度主线打磨另立主题（标题/触发语降调或脚注） |
| **MF-NAS-08** | A-05 · QA-08 | 建 ACCEPTANCE；统一 DOC-STATUS；DLLM/WEA/L0 用户面 superseded 指针；SFI/Help 责任人 |
| **MF-NAS-09** | FE-06/07/08 · QA-04/07 | 负例：M7 焦点、M9（含 stub banner dismiss）、M10 deeplink、FS-01 精确串、切断 `refreshAiStatus`/`focus=ai` |
| **MF-NAS-10** | A-04 · 全席 | 命名冻结表写入 §5.1（见下） |

### 4.1 建议冻结的门控命名（MF-NAS-10）

| 层 | 名称 |
|----|------|
| Env | `TRAVELOGUE_AI_SURFACE` |
| Config | `studio.ai_surface_enabled`（默认 `false`） |
| Wire | `aiSurfaceEnabled`（只读 bool） |
| FE | `isAiSurfaceEnabled()` |

### 4.2 建议新增 AC（草案 · 待回写 §10）

| ID | 验收项 |
|----|--------|
| **AC-NAS-13** | 门控 off：`POST /__travelogue/narrate` → 403 / `E_AI_SURFACE_DISABLED`（有 Key 亦然） |
| **AC-NAS-14** | 默认面精修抽屉无「按新感觉重写」；保存 toast 无「重新生成文案」；会话 **0×** `/narrate` |
| **AC-NAS-15** | 门控 off：`openLlmSettings` 全 source no-op；`?llmSetup=1` 不弹窗；开设置不请求 `llm/status`（或请求但不渲染入口） |
| **AC-NAS-16** | 帮助重播后无能力卡、无 stub tip/banner |
| **AC-NAS-17** | 禁词审计按「默认可达面」语义通过；dark job 单独跑 AC-NAS-09 |

---

## 5. Should-Fix（不挡 W0→W1，建议 W1/W2 消化）

1. FirstSuccess / 完成 CTA 点明「纯照片长图」或发群（D-NAS-09）。  
2. 升级用户一句变更说明（非 UI 强制）。  
3. dark ON 恢复清单写死：设置 + Sheet/抽屉 narrate + ping；**不**恢复能力卡（关 OQ-NAS-04）。  
4. `handle_narrate` / `studio_errors` 存量「杂志感」句中性化或 dark-only。  
5. Analytics：入口统一停发；`ai_surface_gate` W3 必打一次。  
6. M12 G1 副文案 W2 顺手改。  
7. core.js narrate 失败确认框禁词。  
8. A11Y 焦点序补测试指针。  
9. OQ-NAS-02 eyebrow「智能」发版前定，不挡 W1。

---

## 6. 已关闭 / 建议默认关闭的 OQ

| OQ | 评审建议 | 状态 |
|----|----------|------|
| **OQ-NAS-05** | **硬拒绝 403** + 独立错误码（MF-NAS-01） | **建议关闭** |
| **OQ-NAS-04** | dark **不**恢复能力卡 | **建议关闭** |
| **OQ-NAS-01** | 正式包仅 env/config；dev 才可 localStorage | 维持建议 |
| **OQ-NAS-02** | 本版保留「智能游记画册」 | 不挡 W1 |
| **OQ-NAS-03** | 项目介绍 W3 脚注 | 不挡 W1 |

---

## 7. 测试与回归（摘要）

- **默认面**：静态（默认可达禁词）+ unit（门控早退）+ e2e（无入口 + **0× narrate**）+ 狗粮主链。  
- **Dark**：独立 job；D1–D10 见测试席大纲（设置/ping/Sheet/抽屉 narrate；能力卡仍不 show；关 switch 后有 Key 仍藏）。  
- **翻转**：拆 `*_nas_default` / `*_ai_surface_dark`，覆盖 DLLM w2、L0G FE、SFI dock、preview v3、UX Trust、settings。

---

## 8. 前端冒烟脚本（评审采纳 · ≤10 步）

1. 干净首访：无能力卡、无 stub banner。  
2. 设置：无 AI zone；总述中性；无/不依赖 `llm/status` 展示入口。  
3. 帮助无 H7 → 重播 → 仍无卡/tip/banner。  
4. `?llmSetup=1` 不弹 Modal。  
5. 导入 → FirstSuccess = COPY-NAS-FS-01。  
6. 预览精修：无 Sheet llm 行；抽屉无「按新感觉重写」；toast 无再生引导。  
7. Dock 无 AI 就绪；**零** `POST /narrate`。  
8. （可选）失败面无配置 CTA/焦点。  
9. 静态禁词（默认可达面）通过。  
10. dark ON：可配 + 可 narrate；能力卡仍不出现；再 OFF 有 Key 仍藏。

---

## 9. Go / No-Go

| 条件 | 结果 |
|------|------|
| MF-NAS-01～10 回写 PRD（建议升 **v0.2.0**）+ ACCEPTANCE 初稿 | **开 W1** |
| 仅藏 UI、不接 narrate 硬拒绝 / 无 `aiSurfaceEnabled` 下发 | **No-Go**（违反「用不到」「配不了」） |
| AC-08 无扫描语义即合 FE-NAS-14 | **No-Go**（永红或假绿） |

**本纪要结论**：**Conditional Go** · Must-Fix 回写前不编码。

---

## 10. 行动项

| # | 行动 | Owner 建议 | 期限 |
|---|------|------------|------|
| 1 | PRD 回写 MF-NAS-01～10、AC-NAS-13～17、关 OQ-05/04 | 产品 + 架构 | W0 |
| 2 | IMPLEMENTATION：BE-NAS-01/02 升 P0；FE-NAS-00/09/10/14 按 BLK 补丁 | 前后端 | W0 |
| 3 | 新建 ACCEPTANCE-NO-AI-SURFACE-V1（勾选表） | 测试 + 产品 | W0 |
| 4 | DOC-STATUS / DLLM·WEA·L0 用户面 superseded 注记 | 文档 | W0 |
| 5 | SFI FE-SFI-04 / Help H7 / CSC 指针责任人点名 | 产品 | W0 |
| 6 | W1 编码启动 | 前端（+ 后端门控最小集） | MF 关闭后 |

---

## 11. 回写状态

| 项 | 状态 |
|----|------|
| PRD v0.2.0（D-NAS-16～20 · §5 · AC-13～17 · 附录 C） | ✅ 2026-07-22 |
| ACCEPTANCE-NO-AI-SURFACE-V1 | ✅ |
| IMPLEMENTATION v0.2（BE P0 卡） | ✅ |
| W1 编码 | **已放行**（业务代码仍未开工，待排期） |

---

## 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.1 | 2026-07-22 | MF 回写完成注记；放行 W1 |
| v1.0 | 2026-07-22 | 五席并行评审汇总 · Conditional Go · MF-NAS-01～10 |
