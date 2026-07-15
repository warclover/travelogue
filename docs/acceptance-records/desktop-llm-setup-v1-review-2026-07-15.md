# 桌面首启能力分层与写作引擎配置 V1 · 跨职能评审会结论

| 属性 | 内容 |
|------|------|
| **会议日期** | 2026-07-15 |
| **材料** | [PRD-DESKTOP-LLM-SETUP-V1.md](../PRD-DESKTOP-LLM-SETUP-V1.md) **v1.0.0** |
| **形式** | 跨职能书面评审（产品 · UI/UX · 用户体验 · 前端 · 后端 · 架构 · 典型用户代表×2） |
| **结论状态** | **有条件通过（Conditional Go）** · **Must-Fix 已回写 PRD v1.1 · W1a 核心面已落地** · W2（能力卡/H6）待开 |
| **记录人** | 产品 / UX / 工程联合纪要 |
| **前置** | Phase 2 G-P2-05 stub 主链已落地；Help Onboarding V1 Conditional Go；打包 exe 实测触发本主题 |

---

## 1. 与会角色

| 角色 | 关注点 |
|------|--------|
| **产品（拍板）** | 北极星、L0/L1 边界、与 Help/Installer 关系、W 切拍、转化 vs 打扰 |
| **UI / UX** | 能力卡注意力、设置 IA、预览出口、术语、线框挡门 |
| **用户体验** | 首启认知负荷、分享者是否被 API 话术吓退、L1 配完后预期 |
| **前端开发** | 设置/预览双表面、状态刷新、popover 承载、seen 键 |
| **后端开发** | secrets 注入、merge 优先级、ping/save 状态机、本地信任面 |
| **架构师** | user_data_dir、与 portable trips 分裂、ADR、不扩 PATCH 白名单 |
| **典型用户 · 分享者** | 会不会又要我配东西才能用 |
| **典型用户 · 进阶创作者** | 配好 Key 后为何还是「本机文案」；Key 从哪来 |

---

## 2. 总评（一句话）

> **方向正确、降级原则与 Phase 2 / Help 铁律对齐；阻塞不在「要不要做」，而在六处合同未钉死：① 能力卡 CTA 预算自相矛盾；② 预览→配置表面未唯一化；③ secrets→`resolve_llm_runtime` 注入路径未写清；④「保存」vs「已就绪」状态机含糊；⑤ H6 缺「如何申请 Key」；⑥ L1 已配但仍默认 stub 的预期管理不足。**

**表决**：八席一致 **Conditional Go** · Must-Fix 回写 v1.1 后开 W1。

| 角色 | 表决 | 一句话 |
|------|------|--------|
| 产品 | Conditional Go | L0 开箱是对的；能力卡勿做成第二道门槛 |
| UI / UX | Conditional Go | 无线框 + 三按钮卡 = W1 UI 软阻塞 |
| 用户体验 | Conditional Go | 卡上少提 API；配完要说清「不会自动变杂志感」 |
| 前端 | Conditional Go | 预览内嵌同一表单，禁止跳首页丢上下文 |
| 后端 | Conditional Go | merge/注入/状态机不写清会假绿 |
| 架构 | Conditional Go | user_data 合同可接受；建议短 ADR 或回写 ADR-004 |
| 用户 · 分享者 | Conditional Go | 「别逼我配，也别一打开就吓我」 |
| 用户 · 创作者 | Conditional Go | 「告诉我 Key 怎么弄，以及配完点哪里才变好」 |

**对齐评分（主观）**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题定义 | 9 | 根因判断准确：体验面而非缺 offline 引擎 |
| 范围克制 | 8 | 非目标清楚；Installer 边界清楚 |
| 体验合同完整度 | 6 | 剧本有，状态机/出口面有洞 |
| API/数据可开工性 | 6 | 端点有，注入与优先级需 MF |
| AC 可测性 | 7 | Given/When/Then 有；缺夹具与狗粮 N |
| 与相邻 PRD 仲裁 | 6 | OQ-03 与 Help 抢注意力未冻结 |

---

## 3. 分角色意见摘要

### 3.1 产品

| 态度 | 要点 |
|------|------|
| ✅ 赞成 | 六条铁律正确；G-P2-05 / US-P2-08 映射清楚；不做官方代付 Key |
| ✅ 赞成 | W1=配置面+文案归因，W2=能力卡——切拍合理（但须承认：**文案归因可先于能力卡止血**） |
| ⚠️ 高 | §3.4 写「≤2 主 CTA」，F1 却有 **三个**按钮（开始导入 / 配置 / 关闭）——会稀释「开始导入」 |
| ⚠️ 高 | §3.1 写次 CTA「了解写作引擎」，F1 写成「配置写作引擎」——文案未统一 |
| ⚠️ | 成功指标「跳过率可接受」不可审计；狗粮门应写 **N≥3 分享者无 Key 走通长图** |
| 📌 拍板建议 | **能力卡降权**：主 CTA 仅「开始导入」；配置改为文内链或「稍后再说」关闭；配置转化靠预览出口+设置，不靠首屏硬推 |
| 📌 切拍微调 | **W1a（止血）**：预览文案 + settings API/UI + 无 Key 长图冒烟；**W1b**：能力卡；避免 W1 大爆炸 |
| ⚠️ 边界 | 「导入偏好」改名「设置」可能让老用户找不到行程识别开关——保留分组标题「导入偏好」，外层叫「设置」即可 |

### 3.2 UI / UX

| 态度 | 要点 |
|------|------|
| ✅ 赞成 | 废止「生成不可用」主归因；L0/L1 能力表可做设置页顶栏说明 |
| 🔴 MF | **预览→配置**：「回首页打开 popover」会断验货流 → **冻结：预览内 Studio Modal 嵌同一表单**（单一实现 `llm-settings` 组件） |
| 🔴 MF | 能力卡三按钮 → 改为 **1 主按钮 + 关闭（X）+ 文内链「升级写作引擎」** |
| ⚠️ | 「写作引擎」偏内部词；用户面可并列「AI 文案（可选）」；设置内再用「写作引擎」 |
| ⚠️ | popover 塞两 Tab 易溢出；设置改为 **Sheet/Modal** 更稳（导入偏好迁入） |
| 🖼 | **无线框** → W1 UI 合入前至少 F1–F3、F5；F4(H6) 可跟 W2 |
| 🔧 SF | 状态徽章色：未配置=中性，已就绪=成功，失败=警告；勿用「错误红」暗示整 App 坏了 |

### 3.3 用户体验

| 态度 | 要点 |
|------|------|
| ✅ 赞成 | 配置非门槛；忙碌态零打扰；FirstSuccess 不提 API |
| ⚠️ 惊吓 | 能力卡正文连续出现「AI 接口 / API」——分享者可能停在卡上不敢点导入 |
| 🔴 MF | **H6 / 设置必须含「如何获取 Key」**：DeepSeek / 通义控制台官方入口 +「只需复制 Key，不用会写代码」；否则 Persona B 卡死在空白输入框 |
| 🔴 MF | **L1 已就绪但导入仍 stub**（D-DLLM-02）易被当成「配置没生效」→ 预览顶或文案区需稳定一句：「本机文案 · 点此生成杂志感」 |
| ⚠️ | T-CAP-05「当前为本机文案」轻提示与能力卡/预览出口可能三重提醒——建议 **砍 T-CAP-05 或并入预览 LLM 行**，避免提示疲劳 |
| 📌 | 狗粮脚本：分享者路径禁止出现「必须先有 DeepSeek 账号」的暗示句 |

### 3.4 前端开发

| 态度 | 要点 |
|------|------|
| ✅ 赞成 | 独立 `/llm/*` 比塞进 PATCH 白名单干净；锚点文件表可用 |
| 🔴 MF | **单一设置表面**：`templates/studio/js/llm-settings.js`（建议）同时挂首页与预览 Modal；禁止两套 DOM 文案 |
| 🔴 MF | 保存成功后：`llmAvailable` 刷新合同——`config` GET 失效缓存 + 自定义事件（如 `travelogue:llm-status`）通知 preview-toolbar |
| ⚠️ | `#settings=writing` 在预览页语义不清；若采用 Modal 则深链改为 `?llmSetup=1` 或 help 深链 |
| ⚠️ | seen 键与 Help 重播：须在 Help「重播引导」清单中显式列入能力卡（对齐 D-DLLM-09） |
| ⏱ | W1a 估 **3–5 人日**（API 联调+设置 UI+预览改写）；能力卡+H6 另 **1.5–2.5 人日** |

### 3.5 后端开发

| 态度 | 要点 |
|------|------|
| ✅ 赞成 | 不把 Key 写进 trip；DELETE 回 stub；ping 支持未保存临时 Key |
| 🔴 MF | **§5.2 优先级表述自相矛盾**（「自高到低」列表顺序 vs D-DLLM-10）→ 改写为明确表：`secrets 鉴权 > config.user provider > env/.env > 默认 stub` |
| 🔴 MF | **注入路径**：现网 `resolve_llm_runtime` 读 **env 名**；须规定 UI 保存后：写入 secrets **并** `os.environ[api_key_env]=key`（进程内）或扩展 client 直接读 secrets——**二选一写死**，否则 AC-10 假绿 |
| 🔴 MF | **状态机**：`configured`（已存 Key）≠ `llmAvailable/已就绪`（ping 成功或 runtime 可解析）。禁止「仅保存未 ping」显示已就绪；可选：保存成功但未 ping →「已保存 · 未验证」 |
| ⚠️ | secrets 原子写（temp+replace）；读失败降级 stub 并打安全日志（无 Key） |
| ⚠️ | 本机 Studio 任意本地进程可调 POST——V1 接受并写入安全附录；不假装有鉴权 |
| 🔧 SF | ERROR-CODES 补齐 `E_LLM_*` 与 `studio_errors` 映射表（现网代码多于文档） |

### 3.6 架构师

| 态度 | 要点 |
|------|------|
| ✅ 赞成 | L0/L1 分层是正确架构产品化；独立 llm settings API；trips 不迁 AppData（D-DLLM-11）务实 |
| ✅ 赞成 | 明文 secrets + ACL 作 V1，Credential Manager 进 OQ——符合「先打通」 |
| ⚠️ | portable exe：trips 在 exe 旁、密钥在 AppData——**设置页只读展示两路径**，否则支持成本高 |
| 🔧 SF | 增补短 ADR「Desktop user_data_dir & LLM secrets」或回写 [ADR-004](../adr/004-studio-hub-server.md) 一节；Installer PRD 必须引用本文 §5（OQ-06 通过） |
| ⚠️ | 能力卡 vs Help 仲裁（OQ-03）须升为 **D-DLLM-13**：首页 idle 若将弹 Help L1 与能力卡同帧，**只显示能力卡**；能力卡关闭后本会话不再自动弹非关键 Help coach |
| 📌 | 打包冒烟列入发布门——同意；与 Desktop Installer Gate 对齐时避免双清单打架 |

### 3.7 典型用户代表

| 代表 | 态度 | 原话摘要 |
|------|------|----------|
| **分享者** | 支持方向，怕打扰 | 「我就是想选文件夹出长图。一打开就跟我说 API，我会以为这软件没法直接用。」「三个按钮我不知道先点哪个。」 |
| **进阶创作者** | 支持配置面 | 「终于能在软件里填 Key 了。」「但你们得告诉我去哪申请，还有配完为什么字还没变——我还得再点一次生成吗？」 |

---

## 4. 与现网对齐的关键发现（工程核查）

| 触点 | 现网 | 对 PRD 的影响 |
|------|------|----------------|
| 主链 narrate | 无 Key → stub，可成稿 | 印证「根因是体验面」；W1a 文案止血优先 |
| `llmAvailable` | 只读；stub→false | 配置写入后须强制 reload |
| PATCH config | 无 llm | 独立 `/llm/*` 正确 |
| `resolve_llm_runtime` | 读 env | **secrets 注入未设计则 L1 不通** |
| 预览 LLM 行 | 「生成不可用 · 未配置写作引擎」 | 确认 P-DLLM-02；改写为 P0 |
| 首页设置 | 「导入偏好」popover | 扩写作引擎可能撑爆；倾向 Modal/Sheet |
| user_data_dir | **不存在** | W1 必做；launcher 建目录 |
| Help H1–H5 | 无写作引擎 | H6 属 W2 可接受；但「如何获取 Key」若只在 H6，设置页空态也要有链 |
| Desktop Installer PRD | README 有链、**实体缺失** | 本文锁 user_data 正确；勿阻塞本主题 |

---

## 5. Must-Fix / Should-Fix / Park

### Must-Fix（回写 PRD **v1.1** 后方可开 W1）

| ID | 项 | 结论（待写入 PRD） |
|----|-----|-------------------|
| **MF-DLLM-01** | 能力卡 CTA 预算 | **1 主按钮「开始导入」+ 关闭**；「升级写作引擎」仅为正文链接；统一废止第三按钮 |
| **MF-DLLM-02** | 预览配置表面 | **唯一**：预览内 Modal 复用同一设置组件；禁止为配置而强制跳回首页 |
| **MF-DLLM-03** | 配置优先级 + 注入 | 重写 §5.2 优先级表；冻结 secrets→runtime：**进程内注入 `api_key_env` 或 client 直读 secrets（二选一）** |
| **MF-DLLM-04** | 保存 vs 已就绪 | 状态机三态：`未配置` / `已保存未验证` / `已就绪`；仅 ping ok（或等价 runtime 成功）→ 已就绪/`llmAvailable` |
| **MF-DLLM-05** | 获取 Key 指引 | 设置空态 + H6 必含 DeepSeek/DashScope **官方申请步骤链接**（外链） |
| **MF-DLLM-06** | L1 后仍 stub 的预期 | 预览 LLM 行在 `configured&&!wantAuto` 时固定说明「不会自动重写 · 需点击生成」；确认 D-DLLM-02 |
| **MF-DLLM-07** | 文案一致性 | 统一「了解/配置/升级」用词；用户主词建议「AI 文案（可选）」 |
| **MF-DLLM-08** | 线框挡门 | W1 UI 合入前 F1–F3、F5 必出 |
| **MF-DLLM-09** | 与 Help 仲裁 | 升级 **D-DLLM-13**：能力卡优先于同帧非关键 Help L1 |
| **MF-DLLM-10** | 狗粮 AC | 增 AC：N≥3 非技术用户无 Key 完成导入→预览→长图；记录「是否误以为必须配 Key」 |

### Should-Fix

| ID | 项 |
|----|-----|
| **SF-DLLM-01** | 设置容器用 Modal/Sheet，避免撑爆 popover |
| **SF-DLLM-02** | 设置页只读展示 `user_data_dir` 与 `trips_dir` |
| **SF-DLLM-03** | 砍或降级 T-CAP-05，防三重提示 |
| **SF-DLLM-04** | 短 ADR / ADR-004 增补 user_data |
| **SF-DLLM-05** | ERROR-CODES 全量对齐代码中 `E_LLM_*` |
| **SF-DLLM-06** | W 切拍写明 W1a 止血 / W1b 能力卡 |
| **SF-DLLM-07** | secrets 原子写 + 读失败→stub |
| **SF-DLLM-08** | 保存成功广播 `travelogue:llm-status` |

### Park

| ID | 项 |
|----|-----|
| **PK-DLLM-01** | Windows Credential Manager（OQ-01） |
| **PK-DLLM-02** | 导入后自动 LLM（OQ-02） |
| **PK-DLLM-03** | 官方代付 / 代理 Key |
| **PK-DLLM-04** | 自定义任意 OpenAI 兼容作为主推 |
| **PK-DLLM-05** | macOS/Linux 打包验收 |
| **PK-DLLM-06** | L2 审美 MLLM 设置面 |

---

## 6. 决策拍板（评审当场 · 待回写 v1.1）

| ID | 结论 | 说明 |
|----|------|------|
| **D-DLLM-01** | ✅ 通过（收紧） | 能力卡非阻断；**CTA 按 MF-01 收紧** |
| **D-DLLM-02** | ✅ 通过 + 预期文案 | 默认 stub；配 MF-06 |
| **D-DLLM-03** | ⚠ 修改 | 外层「设置」；内保留「导入偏好」分组；写作引擎第二组；容器倾向 Modal |
| **D-DLLM-04～12** | ✅ 大方向通过 | 注入与状态机按 MF-03/04 补全 |
| **D-DLLM-13（新）** | ✅ 纳入 | 能力卡 vs Help 同帧仲裁 |
| **OQ-DLLM-01** | ✅ V1 否 | 明文+ACL |
| **OQ-DLLM-02** | ✅ V1 否 | 不自动 LLM |
| **OQ-DLLM-03** | ✅ 关闭 | 由 D-DLLM-13 替代 |
| **OQ-DLLM-04** | ✅ 否 | FirstSuccess 不提写作引擎 |
| **OQ-DLLM-05** | ✅ 高级折叠 | 不主推 |
| **OQ-DLLM-06** | ✅ 通过 | 本文锁 user_data |

### 三道门禁（建议）

| 门禁 | 内容 |
|------|------|
| **Reliability Go（W1a）** | user_data + llm API + 注入；无 Key 预览+长图；预览文案改写；密钥不泄漏 AC |
| **Setup Go（W1a/W1b）** | ping/保存/清除；预览 Modal 配置；获取 Key 指引 |
| **First-run Go（W2）** | 能力卡 MF-01；D-DLLM-13；狗粮 N≥3；H6 |

---

## 7. 工时粗估（供排期，非承诺）

| 波次 | 范围 | 估时 |
|------|------|------|
| W0 | PRD v1.1 回写 + F1–F3/F5 线框 | 0.5–1.5 人日 |
| W1a | 后端 secrets/API/注入 + 设置 UI + 预览文案/Modal | 3–5 人日 |
| W1b / W2 | 能力卡 + H6 + 埋点 + 重播 | 1.5–3 人日 |
| W3 | ACL 打磨、路径展示、打包冒烟记录、ADR | 1–2 人日 |

---

## 8. 评审清单对照（§13）

| 项 | 表决 |
|----|------|
| 铁律 L0 永不因缺 Key 失败 | ✅ OK |
| 配置非门槛 | ✅ OK |
| D-DLLM-01 能力卡非阻断 | ✅ OK（须 MF-01 收紧 CTA） |
| D-DLLM-02 默认 stub | ✅ OK（须 MF-06） |
| D-DLLM-03/07 设置+H6 | ⚠ 需改（容器与 Key 指引） |
| D-DLLM-04/11/12 user_data | ✅ OK（须 MF-03） |
| §5 API 足够开工 | ⚠ 需改（注入+状态机） |
| §6 废止「生成不可用」 | ✅ OK |
| §10 AC | ⚠ 需补 MF-10 |
| 非目标（无代付/无自动 LLM） | ✅ OK |
| OQ 默认建议 | ✅ 大部通过；OQ-03→D-13 |

---

## 9. 下一步

1. ~~**产品**回写 PRD → **v1.1.0**（消化 §5 Must-Fix）~~ ✅  
2. ~~**UI**出线框 F1–F3、F5~~ ✅  
3. ~~拆 IMPLEMENTATION / ACCEPTANCE~~ ✅  
4. ~~W1a 开编码~~ ✅（user_data · `/llm/*` · 设置 Modal · 预览文案）  
5. ~~W2 能力卡 + H7~~ ✅  
6. ~~W2.1 PARTIAL 收口（MF-06 / D-DLLM-03 / D-DLLM-13 tip）~~ ✅  
7. ~~W3 短 ADR + 打包冒烟模板 + 路径双显~~ ✅  
8. **下一步（人工）**：按冒烟模板勾选发布门；ACCEPTANCE 勾选狗粮 AC-DLLM-30（N≥3）  

---

## 10. 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-15 | 首轮跨职能评审 · Conditional Go · MF-DLLM-01～10 |
| 2026-07-15 | MF 回写 PRD v1.1 · W1a 落地 · 线框/IMPLEMENTATION/ACCEPTANCE 就位 |
| 2026-07-15 | W2 + W2.1：能力卡/H7；MF-06 预期常显；外层「设置」；能力卡→设置 tip 接线 |
| 2026-07-15 | W3：ADR-018 · 冒烟模板 · SF 路径双显 |
