# PRD-BAILIAN-AI-INTEGRATION-V1 · 八席评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-BAILIAN-AI-INTEGRATION-V1.md](../PRD-BAILIAN-AI-INTEGRATION-V1.md)（**BAI** · 百炼一体连接） |
| **关联** | [PRD-STUDIO-AI-SURFACE-V1.md](../PRD-STUDIO-AI-SURFACE-V1.md)（SAS）· [PRD-WRITING-ENGINE-API-HARDENING-V1.md](../PRD-WRITING-ENGINE-API-HARDENING-V1.md)（WEA）· [PRD-COVER-CALLIGRAPHY-TITLE-V1.md](../PRD-COVER-CALLIGRAPHY-TITLE-V1.md)（CAL）· [PRD-AI-RETURN-V1.md](../PRD-AI-RETURN-V1.md)（AIR）· [adr/019-desktop-user-data-llm-secrets.md](../adr/019-desktop-user-data-llm-secrets.md) |
| **评审版本** | PRD **v0.1.0** → 产品补充 + Must-Fix 回写后升 **v0.2.0** ✅ |
| **日期** | 2026-08-13 |
| **结论** | **有条件通过（Conditional Go · 可冻结策划；W1 以「仅百炼接入 UI + 任务路由 + Sheet 分区」Kickoff；思考默认开 / 生图换代 / OCR 换代必须先过 W0 实机，不得假绿）** |
| **编码** | ☑ **策划冻结（v0.2.0 · BLK 已关）**　☐ W0 实机狗粮　☐ W1 连接面+路由　☐ W2 生图冠军/审美　☐ W3 帮助与真人狗粮 |
| **参评角色（八席）** | 产品 · 架构 · 开发 · 算法 · 测试/QA · UI/UX · 典型用户 · **AI API 专家** |
| **评审方式** | 分席只读 PRD §0～§11 · D/G/AC/OQ + **对照现网**（`llm-settings.js` 服务商下拉、`user_settings._ALLOWED_PROVIDERS`、`client.py` 非流式 chat、`route_c.py` 万相异步、`ocr_verify.py` 的 `qwen-vl-plus`、`ai-sheet.js` 单一 `llmAvailable`） |
| **记录人** | 八席联合纪要（跨职能模拟联评 · 基于 2026-08-13 PRD v0.1.0 + 产品当场补充 + 代码事实核查） |
| **本纪要状态** | **已结案 · Conditional Go** · **PRD v0.2.0 已回写 BLK-BAI-01～05** |
| **审查基线** | 一门多房 · L0 无 Key 可出图 · 用户面不提型号 · Fail-open · NAS 门控不回退 · **接入面只留百炼** |

---

## 0. 会前宣读（主持人）

1. **切口**：BAI = 用户只配一把通义百炼 Key；文案 / 识图 / 封面生图由应用按任务表换模型。不是第二套 AI 平台，不重写 AIR Prompt。
2. **产品当场补充（会前已拍）**：API 接入 **只提供百炼界面，隐藏全部 DeepSeek 接入控件**（含高级）。§11.3 其余五项一并认可。
3. **勿重开**：CAL 字库路线 B、NAS 默认关闸、CAD 假风景封面。
4. **本场必拍**：隐藏 DeepSeek 后旧用户怎么办；思考默认开 vs 现网非流式 client；万相 2.1→2.7/千问生图是否同一协议；OCR 换代是否仍吃 `image_url`。

---

## 1. 总评（一句话）

> **八席一致 Conditional Go：方向对——一把百炼 Key、内部路由、Sheet 文案/图像分区、旧阿里型号该换代。产品「只留百炼接入面」当场通过，比 v0.1「高级里还藏 DeepSeek」更干净。但 v0.1 有五处会在 Kickoff 后假绿或伤用户：（1）思考默认开，而现网 `client.py` 非流式、百炼 V4 思考常要求 stream；（2）生图候选可能不是 `route_c.py` 那条万相异步 URL 的 drop-in；（3）`qwen3.5-ocr` 未必兼容现网 vision JSON；（4）隐藏 DeepSeek 后 AC-BAI-04 / secrets 双槽 / COPY-BAI-10 与「文案仍走官方 DeepSeek」自相矛盾；（5）现网设置 UI 仍是 DeepSeek/通义平权下拉，W1 必须物理删掉而非只改文案。关 BLK 后升 v0.2；W0 实机先于「开思考生产默认」和「切生图默认」。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | **Conditional Go** | §11.3 全认。补充必须写死：**设置里不能再出现 DeepSeek**。旧 DeepSeek 用户引导改配百炼，不要做「高级兼容第二条路」——那会让「配一次」重新变成两把 Key。 |
| **架构** | **Conditional Go** | 一门多房、capability registry、Chat vs 万相两套协议——对。secrets 不要再做成 `active` 双槽抢上下文。Studio 只写 dashscope；CLI DeepSeek preset 可留但与设置脱钩。思考若要 stream，是 client 增量，不能假装 `extra_body` 塞进去就完事。 |
| **开发** | **Conditional Go** | W1 可做：删 `llm-settings.js` 服务商 select、强制 POST dashscope、拆 `llmAvailable`、copy 路由。思考/流式、换 `route_c` 协议、换 OCR 合同必须 W0 结论进 IMPLEMENTATION，否则一周估不准。 |
| **算法** | **Conditional Go** | 文案换 V4-Pro 可能改变杂志语气（相对现网 qwen3.7-flash / 官方 DeepSeek-chat），AIR Prompt 本主题不改——W0 要对照抽几条 caption，不能只 ping 通。思考链可能让 JSON 更稳或更碎，用数据关 OQ-BAI-01。生图换代必须保留 CAL 字形门，发布日不是质量。 |
| **测试 / QA** | **Conditional Go** | AC 要能锁「DOM 里没有 DeepSeek option」。旧 secrets 迁移：DeepSeek-only → 文案未连接，不是静默成功。Ping 无思考、narrate 有思考（若 W0 允许）要分两条断言。NAS 关闸 403 回归不能掉。 |
| **UI/UX** | **Conditional Go** | 主路径只留「通义百炼 + Key + 地域 + 保存并测试」——对，比现在的服务商/模型/切换确认轻一个数量级。Sheet 两张卡 + 连接沉底/未就绪置顶继承 SAS，可行。标题「智能连接」与首页「API 配置」建议 W1 定一个主名，避免两套叫法。禁型号、禁「已自动改用」同意。 |
| **典型用户** | **Conditional Go** | 我只想贴一把 Key。不要让我选 DeepSeek 还是通义。已经用官方 DeepSeek 的人会懵一次——设置里没了，要写清楚「请改用通义百炼，文案和封面字都用它」。点 AI 不要自己扣钱。封面字失败别说整本坏了。 |
| **AI API 专家** | **Conditional Go** | 百炼托管 `deepseek-v4-pro` ≠ 官方 `api.deepseek.com`，用同一把百炼 Key 调 V4 文案合理。风险：① V4 思考在兼容模式常要 `enable_thinking` + **stream**；② `qwen3.5-ocr` 是文档 OCR 特化，书法贴纸可能不如通用 VL；③ `wan2.7-image-pro` / `qwen-image-3.0-pro` 多半是新图像 API，不是 `wanx2.1` 那条 `image-synthesis` 异步；④ 控制台「仅免费额度」按 **model id** 计，文案通了万相仍可能 403。 |

**汇总**：**8/8 Conditional Go**。

**对齐评分**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→方案因果完整度 | **9** | P-BAI-01/02 真实；一门多房对症 |
| 接入面简洁度 | **9** | 产品补丁后只留百炼，优于 v0.1 高级双轨 |
| 与现网协议可开工性 | **6** | UI/路由可开；思考/生图/OCR 依赖 W0 |
| AC 可测性 / 防假绿 | **7** | v0.2 补 AC-BAI-15/16 后可测 |
| 旧用户迁移诚实度 | **8** | 改配百炼，不装看不见的 DeepSeek 仍在跑 |
| 用户可感知的信任与成本 | **8** | 分灯 + fail-open；须防「已连接=万相已开」 |

---

## 3. 事实核查（对照现网）

| # | 断言 | 会中核查 |
|---|------|---------|
| **F-01** | 设置 UI 已是「只读百炼」 | ❌ **不属实**：`llm-settings.js` 有 `<option value="deepseek">` 且默认常回落 deepseek |
| **F-02** | secrets 允许两家 | ✅ `_ALLOWED_PROVIDERS = {deepseek, dashscope}`，扁平单 provider |
| **F-03** | 文案与图像共用设置里的 Key | ❌ 文案走 `chat_completion` 当前 provider；路线 C **写死** `DASHSCOPE_API_KEY` |
| **F-04** | `llmAvailable` 同时点亮文案与封面字体 | ✅ `ai-sheet.js` 单一 `llmAvailable` / `lastPingOk` |
| **F-05** | client 支持 `enable_thinking` / stream | ❌ `client.py` 非流式 POST `/chat/completions`，无 thinking 字段 |
| **F-06** | 封面生图为 `wanx2.1-t2i-plus` 异步 | ✅ `route_c.py` `_SUBMIT_URL` = DashScope `image-synthesis` |
| **F-07** | OCR 为 `qwen-vl-plus` + `image_url` | ✅ `ocr_verify.py` |
| **F-08** | 百炼兼容端点已能调 `deepseek-v4-flash-0731` | ✅ 2026-08-12 实机 ping OK（同 Key） |
| **F-09** | `deepseek-v4-pro` 已在同一端点探通 | ⚠ **未在本仓库记录**；OQ-BAI-02 |
| **F-10** | 旧名 `qwen-plus/turbo/max` 仍可用 | ✅ 同日 ping OK；作链尾兼容可以 |

---

## 4. 全场共识

1. **只留百炼接入面**——产品补充升格为 D-BAI-01；高级里也不放官方 DeepSeek。  
2. **一门多房**——用户配门，应用进房间；UI 不出现模型名。  
3. **Sheet 文案 / 图像分区 + 分灯**——单一 `llmAvailable` 必须拆。  
4. **旧阿里型号要换代，但发布日 ≠ 可替换**——生图/OCR 先验协议再比效果。  
5. **思考先开是产品意图，不是工程事实**——W0 验证非流式；失败则生产默认关，不得假绿。  
6. **旧官方 DeepSeek 用户必须改配百炼**——Studio 不再用那把 Key 写文案。  
7. **L0 / NAS / fail-open 不回退**。

---

## 5. Must-Fix（阻塞 · 升 v0.2 前关闭）

| ID | 议题 | 要求（冻结一字面） | 挡 | 状态 |
|----|------|-------------------|----|------|
| **BLK-BAI-01** | 接入面仍可能藏 DeepSeek | **D-BAI-01 / NG-BAI-08**：主路径+高级均无 DeepSeek 控件。AC-BAI-01/15 可测。G-BAI-06 改为引导改配，不保留 Studio 官方 DeepSeek 文案路径。 | 策划→v0.2 | ✅ **已回写 v0.2.0** |
| **BLK-BAI-02** | 思考默认开 vs 非流式 client | **D-BAI-14**：W0 必须实机证明非流式+thinking+JSON。失败则 W1 生产默认关思考。AC-BAI-16。 | W0→开思考生产 | ✅ **已回写** |
| **BLK-BAI-03** | 生图换代当 drop-in | **D-BAI-15**：候选须记录是否仍走现网万相异步 URL。协议不同单独立项，不挡连接 UI。 | W2 切默认 | ✅ **已回写** |
| **BLK-BAI-04** | OCR 换代合同未验 | **D-BAI-16**：`qwen3.5-ocr` 必须打通现网 `image_url`+JSON，否则改 `qwen3.7-flash`。 | W1 OCR 默认 | ✅ **已回写** |
| **BLK-BAI-05** | 旧用户/AC/secrets 自相矛盾 | 删除 L1b、双槽 `active`、COPY「高级 DeepSeek」。AC-BAI-04：DeepSeek-only = 文案未连接。W1 里程碑不再写「旧 DeepSeek 文案不丢」。 | 策划→v0.2 | ✅ **已回写** |

**Should-Fix（不阻塞 v0.2）**

| ID | 建议 | 状态 |
|----|------|------|
| **SHD-BAI-01** | 用户可见主名统一为 **「模型API 配置」** | ✅ v0.2.1 D-BAI-17 |
| **SHD-BAI-02** | 线框 F0–F6（无 DeepSeek select） | W0 |
| **SHD-BAI-03** | 帮助 H7 改 COPY-BAI-12 | W3 |
| **SHD-BAI-04** | 文案 V4-Pro vs 现网 flash 抽检语气（算法） | W0 |
| **SHD-BAI-05** | `analytics.js` 去掉 `llm_provider_change` 到 deepseek 的产品路径 | W1 |
| **SHD-BAI-06** | 现网 `providerLabel`「通义千问」与产品「通义百炼」对齐 | W1 |

---

## 6. 典型用户提问 Q&A

| 提问 | 会中回应（对应决策） |
|------|----------------------|
| ① 我还要选 DeepSeek 吗？ | 不要。设置里只有通义百炼（D-BAI-01）。 |
| ② 我以前填过 DeepSeek Key，还能用吗？ | Studio 里不能再靠它写杂志文案。请改填百炼；照片和导出不受影响（AC-BAI-04/12）。 |
| ③ 配一次就能文案+封面字？ | 一把百炼 Key 是前提。封面字若万相没开通，会改用本机字库，不会说整本失败（COPY-BAI-08）。 |
| ④ 点开 AI 会不会自己扣钱？ | 继承 SAS：勾选不请求；生成前确认文案；封面字体要点一次。 |
| ⑤ 为什么有时慢？ | 文案可能在「想一想」（思考默认开）。若太慢，W0 后可以关掉——用户面仍不提型号。 |

---

## 7. 对 OQ 的会中倾向

| OQ | 会中倾向 | 是否升 BLK |
|----|----------|------------|
| **OQ-BAI-01** 思考开/关 | 产品要先开；API 席警告非流式。按 D-BAI-14 用数据关 | 已进 D-BAI-14 |
| **OQ-BAI-02** Pro 端点 | Flash 已通；Pro 未测。W0 优先探 Pro，失败则 Flash 为文案默认 | 否（W0） |
| **OQ-BAI-03** 生图冠军 | 未测不切；先验协议 | 已进 D-BAI-15 |
| **OQ-BAI-04** OCR 专用 vs 通用 VL | 先测 3.5-ocr，不行就 3.7-flash | 已进 D-BAI-16 |
| **OQ-BAI-05** 正式包思考开关 | **隐藏**（v0.2.1 产品拍板 D-BAI-20） | 已关 |
| **OQ-BAI-06** 国际站 | **V1 只中国站**（D-BAI-18） | 已关 |
| **OQ-BAI-07** 自定义 URL | **正式包不提供**（D-BAI-19） | 已关 |
| **（新增）官方 DeepSeek UI** | **完全隐藏** | 已进 BLK-BAI-01 |

---

## 8. 里程碑裁定

| 里程碑 | 本场裁定 |
|--------|----------|
| **策划冻结（v0.2）** | **批准**：关 BLK-BAI-01～05 后 |
| **W0 实机狗粮** | **必须先于** 开思考生产默认、切 t2i 默认、锁定 OCR 默认 |
| **W1（仅百炼 UI + 路由 + Sheet 分区）** | **批准 Kickoff**（思考：W0 绿才开，否则关思考交货） |
| **W2（生图冠军 / 审美）** | **不批改生产 t2i 默认**直至 D-BAI-15 记录齐全 |
| **W3** | 帮助 + 真人：只填一次百炼 |

---

## 9. 签核

| 席位 | 签核 |
|------|------|
| 产品 | Conditional Go · 仅百炼接入面 |
| 架构 | Conditional Go · 单槽 secrets · 思考不假绿 |
| 开发 | Conditional Go · W1 可开 UI/路由 |
| 算法 | Conditional Go · W0 语气与字形 |
| 测试/QA | Conditional Go · AC-BAI-01/04/15/16 |
| UI/UX | Conditional Go · 主路径极简 |
| 典型用户 | Conditional Go · 改配说明要人话 |
| AI API 专家 | Conditional Go · 协议先验 |

**主持人裁定**：策划冻结 **v0.2.0**。W1 编码可与 W0 并行，但 **合并「开思考 / 换生图默认 / 换 OCR 默认」必须以 W0 记录为准。**
