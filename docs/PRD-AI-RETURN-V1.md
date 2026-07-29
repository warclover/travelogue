# Travelogue · AI-Return V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.1.0** |
| **状态** | **Draft · Ready for Review** |
| **DOC-STATUS** | **active** |
| **主题代号** | 「AI 用户面回归」— **AIR**（AI-Return） |
| **触发来源** | 2026-07-29 产品策略：在 NAS「先出图」稳态后，按章程解冻 AI 面；优先杂志文案 + 渠道敢发包，不做强制云 / 假风景 |
| **前置条件** | [PRD-NO-AI-SURFACE-V1](./PRD-NO-AI-SURFACE-V1.md) §5.5 冻结资产可解冻；[PRD-DESKTOP-LLM-SETUP-V1](./PRD-DESKTOP-LLM-SETUP-V1.md) / [PRD-WRITING-ENGINE-API-HARDENING-V1](./PRD-WRITING-ENGINE-API-HARDENING-V1.md) 工程可回归；`aiSurfaceEnabled` 单点门控可翻转；NAS Kickoff 交接检查（NAS §14.3）通过 |
| **关联文档** | [PRD-NO-AI-SURFACE-V1.md](./PRD-NO-AI-SURFACE-V1.md) §14 · [PRD-COPY-OPTIMIZATION.md](./PRD-COPY-OPTIMIZATION.md) · [PRD-SHARE-READY-OPTIMIZATION-V1.md](./PRD-SHARE-READY-OPTIMIZATION-V1.md) · [PRD-SHARE-FACE-INTEGRITY-V1.md](./PRD-SHARE-FACE-INTEGRITY-V1.md) · [INSIGHT-MOMENTS-LATE-SHARE-COPY-2026-07-23.md](./INSIGHT-MOMENTS-LATE-SHARE-COPY-2026-07-23.md) · [INSIGHT-WECHAT-TRAVEL-PHOTO-STORYLINE-2026-07-23.md](./INSIGHT-WECHAT-TRAVEL-PHOTO-STORYLINE-2026-07-23.md) · [PRD-COMMERCIALIZATION-MVP-V1.md](./PRD-COMMERCIALIZATION-MVP-V1.md) · [CHARTER.md](./CHARTER.md) · [adr/019-desktop-user-data-llm-secrets.md](./adr/019-desktop-user-data-llm-secrets.md) |
| **并行但不混交付** | [PRD-COVER-ART-DIRECTION-V1.md](./PRD-COVER-ART-DIRECTION-V1.md)（装帧导演）· [PRD-HERO-INTEREST-TASTE-V1.md](./PRD-HERO-INTEREST-TASTE-V1.md)（主图品味 · 本机） |
| **验收** | Kickoff 后拆 `ACCEPTANCE-AI-RETURN-V1.md`；本文 §10 为源 |
| **实施清单** | Kickoff 后拆 `IMPLEMENTATION-AI-RETURN-V1.md` |
| **更新日期** | 2026-07-29 |

> **定位**
>
> AI-Return 是 NAS 的**用户面解冻 + 卖点迭代**，不是「永远上云 AI 相册」。  
> V1 交付两件事：**(A) 杂志感文案可配可用**；**(B) 渠道出口文案包（朋友圈 / 群 / 小红书）敢复制敢发**。  
> 导入主链默认仍为 **stub 本机文案**；LLM 为显式升级；无 Key 用户仍能走完「预览 → 长图 → 发群」。
>
> **一句话目标**：愿意升级的用户，在本机用自备 Key 写出杂志感；所有人（含 L0）在导出成功面拿到可发的渠道配文；且绝不把「缺 Key」说成「整次生成失败」。
>
> **产品铁律（继承并加两条）**
>
> 1. **本地优先** — 照片默认不上云；LLM 仅发送文案所需摘要（标题意图、地名、章角色、可选低分缩略说明），禁止整册原图上传。  
> 2. **无强制账号 / 无官方代付 LLM** — 用户自备 Key（DLLM 合同）。  
> 3. **首篇可完成** — Community / 无 Key 必须能出长图；AI 不作启动墙。  
> 4. **继承 D-NAS-20** — **默认不恢复**首启能力卡硬推。  
> 5. **渠道文案 ≠ 杂志文案** — `meta.hook` / 章 `lead` 保持 sparse；迟晒/朋友圈腔只进出口包。  
> 6. **分期 KPI 不混 NAS** — 本期考配置转化、升级完成、文案满意度、渠道复制率；不考「零 AI 岔路」。  
> 7. **禁止假旅行风景作默认封面** — 生图封面归 [CAD](./PRD-COVER-ART-DIRECTION-V1.md)；本主题不做。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0.1 | 术语与分层 |
| §0.2 | 与相邻主题边界 |
| §1 | 背景与问题 |
| §2 | 目标 / 非目标 / 成功画像 |
| §3 | 体验合同与冻结决策 D-AIR-* |
| §4 | 功能规格（解冻 · 语气包 · 渠道包） |
| §5 | 数据 / API / 隐私 |
| §6 | 文案与归因 COPY-AIR-* |
| §7 | 埋点 |
| §8 | 里程碑 |
| §9 | 风险与开放问题 |
| §10 | 验收 AC-AIR-* |
| §11 | 与商业化预留 |

### 0.1 术语

| 术语 | 含义 |
|------|------|
| **L0** | 本机核心：stub 文案 + 排版 + 长图；无外部 LLM |
| **L1** | 写作引擎：用户自备 DeepSeek / 通义等；预览「生成杂志感文案」 |
| **杂志文案** | 写入 trip 的 `meta.title` / `hook` / 章 `lead` / 封底 epilogue 等版心字段 |
| **渠道包 `shareCopyPack`** | 导出/分享面的可复制文案；**不**默认灌入版心 |
| **语气 `voice`** | `editorial`（杂志冷静）· `moments`（朋友圈网感）· `family`（给家人） |
| **迟晒 `late_share`** | 拍摄/行程结束距今 ≥ 阈值时，朋友圈通道优先的语气子类 |
| **解冻** | `aiSurfaceEnabled=true`（或产品等价开关）后，设置 / 预览 narrate / ping 对默认面可见可用 |

### 0.2 与相邻主题边界

| 主题 | 本主题拥有 | 本主题依赖 / 不碰 |
|------|------------|-------------------|
| **NAS** | 用户面 supersede：解冻后默认面再开放 AI | 不拆除 NAS dark；不改写 NAS 出图 KPI 史 |
| **DLLM / WEA** | 用户面合同重新激活并迭代（语气、渠道、归因） | 密钥路径 / Provider 白名单 / ping 以工程栈为准 |
| **Copy Optimization / SFI** | 杂志感生成路径；禁词与 sparse 仍遵守 | 不放宽「敢发宁可空」为说明书腔 |
| **Share-Ready / FST** | 成功面「复制渠道文案」区块 | 禁止第二套成功面；复用 Task Dock |
| **Wait Tips** | 最多 1 张能力暗示（可选 W2） | **禁止**六段迟晒原文进等待轮播 |
| **CAD / HIT / PA-MLLM** | 无 | 装帧与主图品味另立；V1 不做审美 MLLM |

---

## 1. 背景与问题

### 1.1 现状

| 层 | 现状 | 缺口 |
|----|------|------|
| **用户面** | NAS：看不见 / 配不了 / 用不到 AI 文案 | 杂志感与渠道配文无法作为产品卖点 |
| **工程** | narrate / secrets / ping / dark 保留 | 解冻后需产品化语气与渠道，而非仅「重新打开旧按钮」 |
| **出口** | `share_copy_pack` 偏小红书 title+topics；有 Key 才带 hook | 缺朋友圈 / 群 / 迟晒专用通道 |
| **洞察** | 迟晒六段、故事线 INSIGHT 已整理 | **未入库为产品合同** |

### 1.2 问题陈述（P-AIR-*）

| ID | 问题 | 严重度 |
|----|------|--------|
| **P-AIR-01** | NAS 休眠后无「下期」产品合同，解冻易变回旧 DLLM 硬推 | 阻塞 |
| **P-AIR-02** | 用户要的「敢发」常是渠道配文，不是杂志 hook | 严重 |
| **P-AIR-03** | 单一语气灌版心 → 朋友圈鸡汤或说明书腔 | 严重 |
| **P-AIR-04** | 无 Key 时渠道包过瘦，成功面无可复制物 | 中等 |
| **P-AIR-05** | 解冻若恢复能力卡硬推，伤害首篇完成率 | 严重 |
| **P-AIR-06** | LLM 若拉原图，冲突章程与 CMZ「不借商业化开云」 | 阻塞 |

---

## 2. 目标与非目标

### 2.1 目标（In Scope）

| ID | 目标 |
|----|------|
| **G-AIR-01** | 完成 NAS → AI-Return **解冻最小包**：设置写作引擎 + 预览生成杂志感 + ping + 已存 Key 无需重贴 |
| **G-AIR-02** | 杂志文案支持 **三语气**（editorial / moments / family），一键换语气不重排版 |
| **G-AIR-03** | 扩展 `shareCopyPack`：**moments / group / xhs** 三通道；L0 模板兜底；L1 可仿写 |
| **G-AIR-04** | **迟晒**自动检测：距今 ≥ `late_share_days`（默认 14）时 moments 优先 `late_share` 种子 |
| **G-AIR-05** | 归因清晰：本机文案 vs 杂志感；渠道包标注「可发模板 / 可再改」 |
| **G-AIR-06** | 默认 **不**恢复首启能力卡硬推（D-NAS-20）；设置与预览为发现路径 |
| **G-AIR-07** | 隐私合同：摘要上云；遥测与 trip 产物永不含 API Key |

### 2.2 非目标（Out of Scope · V1）

| 不做 | 理由 |
|------|------|
| 强制配 Key / 导入自动调 LLM | 伤 L0 与完成率 |
| 官方代付 / 订阅云写作 | 章程 + CMZ |
| 审美 MLLM / 主图 HIT 默认开 | HIT / PA 另轨 |
| AI 生成假景点封面 | CAD 明确禁止为默认 |
| 把迟晒六段写入 `meta.hook` 默认 | 渠道 ≠ 版心 |
| 完整「故事线 Agent 工作台」UI | V1 只做文案与出口；选片故事线表归后续 |
| 海外 locale / IG 主路径 | 对齐 Share-Ready 中文微信主路径 |
| 观众模式（发群/家人）自动重选脸图 | V1.1+；本版只换文案语气 |

### 2.3 成功画像

| 角色 | 成功 |
|------|------|
| **L0 分享者** | 不解冻也能复制 1 条朋友圈/群模板；长图路径不变 |
| **L1 创作者** | 10 分钟内配好 Key → 生成杂志感 → 换语气 → 复制渠道文案发出 |
| **产品** | 解冻后 AC-AIR 绿；配置转化与文案满意度可测；无「生成失败」误归因回流 |

---

## 3. 体验合同与冻结决策

### 3.1 用户旅程（解冻后默认）

```text
干净安装 / 升级安装
  → 主链仍：导入 → stub 文案 → 预览 → 长图（零强制配 Key）
  → 设置可见「写作引擎」（非首启硬推）
  → 预览：「生成杂志感文案」或「配置写作引擎」
  → 导出成功面：「复制朋友圈文案 / 群一句话 / 小红书」候选可换
```

### 3.2 冻结决策（D-AIR-*）

| ID | 决策 | 说明 |
|----|------|------|
| **D-AIR-01** | **解冻触发** | 产品发版开关 `aiSurfaceEnabled=true`（config / 构建旗标）；暗门 `TRAVELOGUE_AI_SURFACE=1` 仅工程 |
| **D-AIR-02** | **解冻最小包** | 设置 AI zone + Sheet/预览 narrate CTA + 保存并测试（ping）+ H7 帮助；**不含**能力卡硬推 |
| **D-AIR-03** | **能力卡** | **默认不恢复**（继承 D-NAS-20）；若实验，须另 OQ 且 CTA 非阻断 |
| **D-AIR-04** | **导入主链 provider** | 即使 L1 已配，导入默认 **stub**；须用户点击「生成杂志感」才写 LLM（继承 D-DLLM-02） |
| **D-AIR-05** | **三语气** | `voice ∈ {editorial, moments, family}`；默认 `editorial`；换语气 = 重跑 narrate 作用域或本地改写层，**不**触发 curate/layout |
| **D-AIR-06** | **渠道包权威** | 成功面 / 分享抽屉读 `shareCopyPack`；**禁止**用渠道腔覆盖版心除非用户显式「同步到封面钩子」 |
| **D-AIR-07** | **L0 渠道兜底** | 无 Key：moments/group/xhs 均有模板；body 可空或短模板；**不**假装 AI 原创 |
| **D-AIR-08** | **迟晒阈值** | 默认 `late_share_days=14`；基于 trip 媒体 `takenAt` max 或 `meta` 行程结束日；不可判定则不启用迟晒优先 |
| **D-AIR-09** | **LLM 输入** | 白名单：title/intent/places/chapter roles/hook 旧值/统计；**禁止**默认附加原图像素；可选「发送封面缩略描述」默认 **关** |
| **D-AIR-10** | **禁编造** | Prompt 合同：不得编造未在摘要中出现的情节、同伴、情绪事件 |
| **D-AIR-11** | **SFI / 禁词** | 杂志与渠道均走既有 unsafe / 工程泄漏禁词；渠道可保留有限度 emoji（可关） |
| **D-AIR-12** | **错误归因** | 缺 Key / LLM 失败 → 仅杂志感路径局部失败；渠道 L0 仍可用；文案见 COPY-AIR-* |
| **D-AIR-13** | **文案密度** | V1 维持 `scope=frame` 现行；解开 `frame_chapters` 为 OQ-AIR-02，须过 SFI 盲评 |
| **D-AIR-14** | **已存 Key** | 解冻后 secrets 路径不变；不得要求用户重新粘贴（NAS Wake） |

### 3.3 功能开关矩阵

| 能力 | L0（无 Key） | L1（已配 Key） | 备注 |
|------|--------------|----------------|------|
| 本机 stub 版心 | ✅ 默认 | ✅ 可保留 | |
| 生成杂志感 | ❌ → 引导配置 | ✅ | |
| 换语气 | 模板弱切换（可选） | ✅ LLM 或规则+LLM | V1 允许 L0 仅渠道换模板 |
| 渠道复制 | ✅ 模板 | ✅ 模板 + 可选仿写 | |
| 审美 MLLM | ❌ | ❌ | 非本主题 |

---

## 4. 功能规格

### 4.1 F-AIR-01 · 解冻与设置面

- 恢复 DLLM 设置「写作引擎」组：Provider、Key、测试连通、状态徽章。  
- 预览工具行：`llmAvailable=true` →「生成杂志感文案」；`false` →「配置写作引擎」（禁止仅 disabled 无出口）。  
- Help **H7** 恢复默认可达（NAS 曾隐藏）。  
- FirstSuccess / Dock **禁止**主 CTA 改为「去配置 API」。

### 4.2 F-AIR-02 · 杂志感生成与三语气

**作用域（V1）**：`meta.title`（若空或用户允许覆写策略沿用现网）、`meta.hook`、各章 `lead`（若 D-AIR-13 未解开则仅 frame 级字段）、封底 epilogue（若现网有槽）。

**语气定义**

| voice | 读者感受 | 禁区 |
|-------|----------|------|
| **editorial** | 冷静、杂志、短句、少emoji | 鸡汤、说明书、「本算法」 |
| **moments** | 轻网感、可迟晒、可少量 emoji | 夸张假情节；**默认不写进版心**除非用户选此 voice 生成杂志感 |
| **family** | 温暖、具体、少梗、适合长辈 | 阴阳怪气、过度网感 |

**交互**

1. 预览「生成杂志感文案」前可选 voice（默认 editorial）。  
2. 生成后提供「换一种语气」→ 三选一，确认后重写版心目标字段。  
3. 确认文案：「将调用写作引擎重写文案；照片仍留在本机。」

### 4.3 F-AIR-03 · 渠道出口包（Share Copy Pack v2）

扩展 `travelogue/domain/share_copy_pack.py`（及 API 投影）为：

```json
{
  "channels": {
    "moments": {
      "candidates": [
        { "id": "LS-01", "tone": "late_share", "opener": "...", "body": "...", "emoji": true }
      ],
      "selectedId": "LS-01"
    },
    "group": {
      "candidates": [{ "id": "g-01", "body": "这次旅行长图做好了，发给大家看看。" }]
    },
    "xhs": {
      "title": "...",
      "body": "...",
      "topics": "#旅行日记 #..."
    }
  },
  "meta": {
    "lateShare": true,
    "voiceHint": "moments",
    "source": "template" | "llm"
  }
}
```

**种子**

- 迟晒：入库 [INSIGHT-MOMENTS-LATE-SHARE-COPY](./INSIGHT-MOMENTS-LATE-SHARE-COPY-2026-07-23.md) 六段为 `late_share` 种子（可去 emoji 变体）。  
- 非迟晒 moments：另备 3～6 条平实晒图模板（W1 定稿）。  
- group：1～3 条短句，忌营销腔。  
- xhs：延续现网 title/topics；body 规则同现网（无 Key 可不造正文）。

**挂载点**

| 触点 | 行为 |
|------|------|
| 导出成功面 | 「复制朋友圈文案」主；次「换一条」；折叠群 / 小红书 |
| 分享意图卡旁 | 可选「先复制文案」 |
| Wait Tips | **禁止**贴原文；可选 W2 一张能力暗示卡 |

### 4.4 F-AIR-04 · L1 渠道仿写（可选增强）

- 有 Key 时，可用 moments 种子作 few-shot，生成 1～3 条**不编造情节**的变体。  
- 失败 fail-open → 回落模板；UI 不报「整次失败」。

### 4.5 F-AIR-05 · 显式「同步到封面钩子」（可选）

- 默认关。用户在渠道候选上点「用作封面钩子」才写入 `meta.hook`。  
- 写入后走 SFI 校验。

---

## 5. 数据 / API / 隐私

### 5.1 配置（示意）

```yaml
ai_return:
  enabled: true                    # 与 aiSurfaceEnabled 对齐或由其派生
  default_voice: editorial
  late_share_days: 14
  channel_pack:
    moments_candidates: 6
    allow_emoji: true
  llm:
    send_cover_thumb_caption: false  # 默认关
```

### 5.2 API

| 方法 | 用途 |
|------|------|
| 既有 `POST /narrate`（或 Studio 等价） | 增加 `voice`；解冻后默认可达 |
| `GET/PATCH` 写作引擎设置 | 恢复 WEA 合同 |
| `POST .../ping` | 连通测试；解冻后不再对默认面 403 |
| `GET .../share-copy-pack` | 返回 v2 channels；按 trip 计算 lateShare |

具体路径以 IMPLEMENTATION 对照现网 handlers；**禁止**平行第二套密钥 API。

### 5.3 隐私与安全

- Key：仅 user_data secrets（ADR-019）；禁止进遥测、日志明文、trip.json。  
- 请求体审计：CI 或单测断言无 `file://` 原图、无 base64 整图（除非未来 CAD 显式另议且默认关）。  
- 用户可见隐私句：Help H7 与生成确认框（COPY-AIR-PRIVACY）。

---

## 6. 文案与归因（COPY-AIR-*）

| ID | 场景 | 文案（冻结方向） |
|----|------|------------------|
| **COPY-AIR-01** | L0 预览 | 「当前为本机文案 · 配置写作引擎后可升级杂志感」 |
| **COPY-AIR-02** | 生成确认 | 「将调用写作引擎重写文案；照片仍留在本机。」 |
| **COPY-AIR-03** | LLM 失败 | 「杂志感文案暂时不可用，仍可导出长图；可重试或改用本机文案。」 |
| **COPY-AIR-04** | 渠道区标题 | 「复制可发文案」 |
| **COPY-AIR-05** | 渠道来源 | 「模板 · 可再改」或「写作引擎 · 可再改」 |
| **COPY-AIR-06** | 迟晒角标 | 「迟晒语气」 |
| **COPY-AIR-PRIVACY** | H7 | 「Key 只存在本机；调用时仅发送文案所需摘要，默认不上传原图。」 |

禁词：默认可达面禁止把缺 Key 写成「生成失败」「制作失败」等整单失败语义（继承 DLLM/NAS 教训）。

---

## 7. 埋点

复用 NAS 预留 / DLLM schema，增量：

| 事件 | 属性 |
|------|------|
| `llm_settings_open` | source |
| `llm_ping_result` | ok / error_code |
| `llm_narrate_click` | voice |
| `llm_narrate_result` | ok / voice / latency |
| `share_copy_copy` | channel / tone / source / lateShare |
| `share_copy_reshuffle` | channel |
| `share_copy_sync_hook` | （若用 F-AIR-05） |

KPI（本主题）：配置完成率、narrate 成功率、渠道复制率、语气切换率。  
**不**纳入：NAS OUT-01～05。

---

## 8. 里程碑

| 里程碑 | 交付 | 门禁 |
|--------|------|------|
| **W0** | PRD 评审；NAS §14.3 交接检查打勾；开关设计签字 | Review Go |
| **W1** | 解冻最小包 + 归因文案 + 渠道 pack v2（模板 L0） | AC-AIR-01～08 |
| **W2** | 三语气杂志感 + 迟晒优先 + L1 渠道仿写 fail-open | AC-AIR-09～14 |
| **W3** | 狗粮 N≥5；埋点看板；文档 ACCEPTANCE 勾选 | 主题 Done |

编码 Kickoff 以 W0 Go 为准；**本文件落地 ≠ 已解冻发版**。

---

## 9. 风险与开放问题

### 9.1 风险

| 风险 | 缓解 |
|------|------|
| 解冻后用户以为必须配 Key | 主链 stub + COPY 归因 + 不硬推能力卡 |
| 渠道腔污染杂志 | D-AIR-06；同步钩子显式 |
| LLM 编造旅行情节 | D-AIR-10；抽检 AC |
| 与 CMZ 付费墙叠加伤害完成率 | AI 不作启动墙；权益预留见 §11，V1 不强制 |

### 9.2 开放问题（OQ-AIR-*）

| ID | 问题 | 默认倾向 |
|----|------|----------|
| **OQ-AIR-01** | 桌面正式版默认 `aiSurfaceEnabled` 开还是关？ | 评审拍板；建议 **先 dark/内测包开，正式版随发版说明** |
| **OQ-AIR-02** | 是否解开 `scope=frame_chapters`？ | V1 维持 frame；W2+ 另评 |
| **OQ-AIR-03** | moments 作杂志 voice 时是否允许 emoji 进 hook？ | 默认 **剥 emoji** 进版心 |
| **OQ-AIR-04** | CMZ License 是否锁「语气包 / 渠道仿写」？ | V1 **不锁**；仅预留 entitlement 位 |
| **OQ-AIR-05** | 故事线「20 张素材表」是否并入 AIR？ | **否**；另立或 HIT 扩展 |

---

## 10. 验收（AC-AIR-*）

| ID | 断言 |
|----|------|
| **AC-AIR-01** | `aiSurfaceEnabled=false` 时行为仍符合 NAS 默认面（回归） |
| **AC-AIR-02** | `=true` 时设置可见写作引擎；已存 Key 无需重贴即可 ping 成功（有效 Key） |
| **AC-AIR-03** | 无 Key：导入→预览→长图全通；预览不出现整单「生成失败」 |
| **AC-AIR-04** | 无 Key：成功面可复制至少 1 条 moments 与 1 条 group 模板 |
| **AC-AIR-05** | 有 Key：点击生成杂志感后版心字段更新；可归因「杂志感」 |
| **AC-AIR-06** | 换 voice 不触发 re-curate / 重排版（无新 layout job） |
| **AC-AIR-07** | 行程结束 ≥14 天：moments 候选优先 `late_share`（可测 fixture） |
| **AC-AIR-08** | 渠道候选默认不写入 `meta.hook` |
| **AC-AIR-09** | LLM 失败时渠道 L0 仍可复制；错误文案符合 COPY-AIR-03 |
| **AC-AIR-10** | 请求审计：默认 narrate payload 无原图像素 |
| **AC-AIR-11** | 首启无能力卡硬推（D-AIR-03） |
| **AC-AIR-12** | H7 默认可达；隐私句可见 |
| **AC-AIR-13** | SFI 禁词：渠道与杂志均不泄漏工程词 |
| **AC-AIR-14** | 狗粮 N≥5：至少 3 人完成「配 Key → 生成 → 复制发出」口述无重大困惑 |

---

## 11. 与商业化预留（CMZ）

| 项 | V1 |
|----|----|
| AI 是否做导出墙 | **否** |
| entitlement 预留 | `ai.voice_pack` / `ai.channel_llm` 位可留，**默认全开** |
| 与买断关系 | 正式版卖「桌面权益」；AI-Return 是体验升级，不单独卖订阅 |

---

## 12. 附录

### A. NAS Wake 对照

本主题兑现 [PRD-NO-AI-SURFACE-V1 §14.2](./PRD-NO-AI-SURFACE-V1.md) 解冻合同，并显式继承 **D-NAS-20**（能力卡默认不恢复）→ **D-AIR-03**。

### B. 迟晒种子所有权

创意备忘 [INSIGHT-MOMENTS-LATE-SHARE-COPY-2026-07-23.md](./INSIGHT-MOMENTS-LATE-SHARE-COPY-2026-07-23.md) 自本文起由 **AIR** 产品合同承接入库；备忘仍保留语气资产原文。

### C. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.1.0** | 2026-07-29 | 初稿：解冻最小包 · 三语气 · 渠道 pack v2 · 迟晒 · 隐私 · AC-AIR |
