# Travelogue · 海外改版 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue（海外对外品牌见 §3.1） |
| **文档版本** | **v0.1.0-OVERSEAS** |
| **状态** | Draft · 待跨职能评审 |
| **主题代号** | 「Overseas Share Pack V1」— 按海外社交习惯改交付默认项，不重写策展管线 |
| **前置条件** | Longshot 2.0 分支 B 可用（ADR-016）；`config/platform_profiles.yaml` 已含 `instagram`（Phase C · CLI/API）；Studio 导入→预览→导出主路径可用 |
| **关联文档** | [SHARING.md](./SHARING.md) · [PRD-LONGSHOT-2.0.md](./PRD-LONGSHOT-2.0.md) · [adr/016-longshot-platform-export.md](./adr/016-longshot-platform-export.md) · [PRD-PREVIEW-EXPORT-FACADE-V1.md](./PRD-PREVIEW-EXPORT-FACADE-V1.md) · [PRD-DESKTOP-INSTALLER-V1.md](./PRD-DESKTOP-INSTALLER-V1.md) · [PRD-UX-TRUST-V1.md](./PRD-UX-TRUST-V1.md) · [CHARTER.md](./CHARTER.md) |
| **验收** | 本文 §11；完整步骤后续拆 [ACCEPTANCE-OVERSEAS-SHARE-PACK-V1.md](./ACCEPTANCE-OVERSEAS-SHARE-PACK-V1.md) |
| **实施清单** | 后续拆 [IMPLEMENTATION-OVERSEAS-SHARE-PACK-V1.md](./IMPLEMENTATION-OVERSEAS-SHARE-PACK-V1.md) |
| **更新日期** | 2026-07-14 |

> **定位**
>
> 国内主路径是「杂志风 HTML + **微信群竖版长图**」。海外主流分享形态是 **Instagram Carousel / Stories + 可转发链接**，不是超长竖图。  
> 本 PRD **不推翻** ingest → curate → narrate → layout → render 管线，只改：**默认导出表面、文案语气、Studio 导出门面、市场话术与首发范围**。  
> 一句话：**引擎继续做「单次事件照片 → 叙事成书」；海外卖的是 Instagram-ready Share Pack。**

> **产品共识（五条铁律）**
>
> 1. **管线复用** — 禁止为海外 fork 第二套策展/排版引擎；差异收敛在 export profile、文案 locale、UI 默认项。  
> 2. **交付默认项对齐海外习惯** — Overseas locale 下默认 CTA 是 Share Pack（Carousel 优先），不是 WeChat longshot。  
> 3. **本地优先不变** — 与 CHARTER / Desktop Installer 一致：无强制账号、无公网多租户；云端托管若做，走独立路径 B 且单独讲清隐私。  
> 4. **不做成截图拼接工具** — 不与 Picsew / Tailor 抢「screenshot stitch」；差异化仍是照片策展 + 叙事。  
> 5. **中文市场路径不破坏** — `locale=zh` / 默认配置下微信群长图、朋友圈、小红书行为与现网一致（G-OVSE-00）。

---

## 0. 读者指南

| 章节 | 必须澄清的问题 |
|------|----------------|
| §1 背景 | 为何要改、As-Is 代码能力缺口 |
| §2 目标/非目标 | 范围锁死 |
| §3 定位与品牌 | 对外叫什么、卖什么 |
| §4 用户与市场 | 先打谁、验证什么 |
| §5 已拍板决策 | D-OVSE-* |
| §6～§8 需求 | Share Pack · 文案 · Studio · 配置 |
| §9 商业与运营 | 定价、获客、埋点（产品边界内） |
| §10 工程约束 | 与现有模块对齐 |
| §11 验收 | AC 清单 |
| §12 里程碑 | 90 天节奏 |
| §13 风险与开放问题 | OQ |

---

## 1. 背景与问题

### 1.1 市场判断（运营结论摘要）

| 判断 | 含义 |
|------|------|
| 微信式超长竖图在美欧不是默认分享形态 | IG / TikTok / WhatsApp 更常用轮播、Stories、短视频、链接 |
| 「截图拼接」海外有成熟红海 | Picsew 等评分高，但与本产品优势无关，**不做** |
| 本产品优势可迁移 | 单次事件照片 → 自动策展 → 叙事排版；缺的是 **社交尺寸与发布引导** |
| 长图仍有次要价值 | WhatsApp/邮件/存档；Overseas 中降为 Advanced，不删 |

### 1.2 As-Is（相对代码库）

| 能力 | 现状 | 证据 |
|------|------|------|
| 微信群长图 | 默认主路径 `wechat_chat` | `DEFAULT_PLATFORM` · [SHARING.md](./SHARING.md) 路径 A |
| 朋友圈 / 小红书 | Longshot 2.0 Phase A/B；Studio 灰度 | `PHASE_A_PLATFORMS` · `studio.longshot2.platforms` |
| **Instagram 4:5** | Profile **已定义**（1080×1350），**仅 CLI/API** | `config/platform_profiles.yaml` · `PHASE_C_CLI_ONLY` |
| Stories 9:16 组图 | 仅有 `douyin_cover` 单张封面，无 IG Stories 多页包 | 同上 |
| Share Pack（一次导出多表面） | **无** | 导出门面仍以「长图」为成功终点 |
| 英文文案 / locale | Stub/LLM 文案偏中文叙事模板 | `travelogue/services/narrate.py` hook/章导语模板 |
| Studio UI 语言 | 中文为主 | 预览 Toolbar / 首页 |
| Desktop 分发 | Windows Installer V1 | [PRD-DESKTOP-INSTALLER-V1.md](./PRD-DESKTOP-INSTALLER-V1.md)；无 macOS / App Store |

### 1.3 核心问题（P-OVSE-*）

| ID | 问题 | 影响 |
|----|------|------|
| **P-OVSE-01** | 默认交付物与海外平台习惯错位 | 即使导出成功，用户也不知道往哪发、发什么格式 |
| **P-OVSE-02** | `instagram` 已有 profile 但 Studio 不可见 | 海外种子无法用主路径验证 |
| **P-OVSE-03** | 文案与发布引导中文心智 | 英文用户感知「翻译工具」而非原生产品 |
| **P-OVSE-04** | 成功态仍导向「发微信群」 | 与 [PRD-PREVIEW-EXPORT-FACADE-V1](./PRD-PREVIEW-EXPORT-FACADE-V1.md) G-EXP-05 国内合同冲突于海外 locale |
| **P-OVSE-05** | 缺少「一次点 Share → 拿到可发素材包」的产品概念 | 用户要自己理解 platform 参数 |

### 1.4 核心判断

> **海外改版 = 导出门面与 locale 的产品化，不是新算法项目。**  
> 优先把 Phase C 的 `instagram` 升到 Studio 一等公民，并包装为 **Share Pack**；长图与 HTML 作为包内可选项保留。

---

## 2. 目标与非目标

### 2.1 产品目标

| ID | 目标 | 衡量方式 |
|----|------|----------|
| **G-OVSE-00** | `locale=zh`（或未设）行为与现网一致 | 回归：微信群/朋友圈/小红书 AC 全绿 |
| **G-OVSE-01** | Overseas locale 默认导出 **Instagram Carousel**（4:5 · 1080×1350） | AC-OVSE-01；Studio 主 CTA 可见 |
| **G-OVSE-02** | 一次 Share 可得到 **Share Pack**（至少 Carousel ZIP + 发布指引；可选 Stories / Link / Long image） | AC-OVSE-02 |
| **G-OVSE-03** | 文案与 UI 可切换 `en`：caption-ready（短句、可直接贴 IG） | AC-OVSE-03 |
| **G-OVSE-04** | 成功态指引「How to post on Instagram」，不再提微信 | AC-OVSE-04 |
| **G-OVSE-05** | 90 天种子：导入→导出完成率 ≥40%；Carousel 选用占比 ≥70% | Telemetry §9.3 |
| **G-OVSE-06** | 不新增第二套 layout 引擎；平台模式仍遵守 ADR-016 分支 B | 代码审查 / 架构验收 |

### 2.2 非目标（V1 明确不做）

| 类别 | 非目标 |
|------|--------|
| **竞品形态** | 不做 screenshot stitch；不做 Canva 式自由画布；不做信息流社区 |
| **端** | 不做 App Store / iOS 首发；不做 macOS Installer（可列 P2） |
| **平台** | 不做「一键发到 Instagram」系统级分享 API 承诺 |
| **模板** | 不做模板商城；Overseas 仅 2～3 套视觉皮肤（见 §7） |
| **本地化** | 不做全欧洲语言；V1 仅 `en`（+ 保留 `zh`） |
| **算法** | 不重做 HDBSCAN/CLIP/LTE；不改 ADR-016 切分主算法（可调 profile 参数） |
| **商业** | 不在本 PRD 落地支付系统；仅定义定价假设与埋点预埋 |
| **国内** | 不弱化微信/朋友圈/小红书路径 |

---

## 3. 定位与品牌

### 3.1 对外品牌（待拍板 · 默认建议）

| 项 | 建议 | 说明 |
|----|------|------|
| 对外名 | **AfterTrip**（备选 Tripfolio / Recap） | 避免「游记」直译；代码库仍可称 Travelogue |
| 一句话 | Trip photos → share-ready story pack | 对应国内「相册 → 微信长图」 |
| App Store / 站点分类话术 | Photo & Video · travel recap | 避开 stitch / screenshot 关键词主攻 |
| 信任点 | On-device · your photos stay yours | 对齐本地优先 |

**D-OVSE-01**：代码与文档内部名保持 Travelogue；对外英文品牌在官网/安装包文案层切换，不强制 rename 包名。

### 3.2 产品公式

```
现有管线（不变）
  ingest → curate → narrate(locale) → layout(screens) → render
                         ↓
Overseas Share Pack（新增产品概念）
  ├─ Instagram Carousel   1080×1350 · 6–10 页 · 默认
  ├─ Instagram Stories    1080×1920 · 封面 + 3–5 高光 · 可选
  ├─ Share Link           私密 HTML（路径 B 子集）· 可选 / P1
  ├─ PDF                  家庭/邮件 · 可选 / P1
  └─ Long image           WhatsApp/存档 · Advanced
```

---

## 4. 用户与市场

### 4.1 Persona（海外）

| Persona | 描述 | V1 策略 |
|---------|------|---------|
| **A · Recap Sharer（主）** | 旅行/周末结束后 24–72h，想发 IG 轮播，不愿学 Canva | 默认 Share Pack · 零平台术语 |
| **B · Privacy Host** | 想给家人看完整故事，不愿公开帖 | Share Link / PDF（P1） |
| **C · Creator Lite** | 旅行博主，要无水印与多表面 | Pro 话术预留；V1 不阻塞免费种子 |

### 4.2 市场切入顺序

| 阶段 | 市场 | 理由 |
|------|------|------|
| **P0** | US / UK / AU / CA（英语） | 付费与 IG 习惯清晰 |
| **P1** | 日韩 / 新加坡 | 仍有精致图文文化，接近国内心智 |
| **P2** | 德法西 | 需更深本地化，V1 不做 |

### 4.3 核心场景（User Stories）

| ID | 作为… | 我想要… | 以便… |
|----|--------|---------|--------|
| US-OVSE-01 | Recap Sharer | 选一次旅行照片文件夹一键成书 | 不用学排版 |
| US-OVSE-02 | Recap Sharer | 一键得到 Instagram 轮播图组 | 直接发帖 |
| US-OVSE-03 | Recap Sharer | 看到英文短 caption 建议 | 复制到 IG 正文 |
| US-OVSE-04 | Recap Sharer | 成功后按步骤指引发帖 | 不卡在「文件在哪」 |
| US-OVSE-05 | Privacy Host | 可选导出链接或 PDF | 不公开到 IG |
| US-OVSE-06 | 中文用户 | 继续用微信长图路径 | 不被海外改版打断 |

---

## 5. 已拍板决策（D-OVSE）

| ID | 决策 | 结论 |
|----|------|------|
| **D-OVSE-01** | 品牌 | 对内 Travelogue；对外英文名可配置（默认 AfterTrip） |
| **D-OVSE-02** | 默认平台（Overseas） | `instagram`（Carousel 4:5） |
| **D-OVSE-03** | 默认平台（Domestic） | 仍为 `wechat_chat`（不变） |
| **D-OVSE-04** | 架构 | 复用 ADR-016 分支 B；`instagram` 从 Phase C 升为 Studio 一等公民 |
| **D-OVSE-05** | Share Pack | V1 最小包 = Carousel PNG 序列 + ZIP + `publish_guide` + caption.txt；Stories/Link/PDF/Longshot 为可选层 |
| **D-OVSE-06** | Locale 开关 | `studio.locale` ∈ {`zh`,`en`}；决定 UI 文案、narrate 语言、默认 platform、成功引导 |
| **D-OVSE-07** | 文案风格（en） | caption-ready：title ≤60 chars；hook ≤120；章导语 ≤80；禁用中文 stub 直出 |
| **D-OVSE-08** | 视觉模板 | V1 上线 2 套英文友好皮肤：`editorial-clean`、`film-soft`（可先映射现有 visual-journal 变量，不强制新模板目录） |
| **D-OVSE-09** | 端形态 V1 | 英文 Studio（Web/桌面）+ waitlist；**不上** App Store |
| **D-OVSE-10** | 商业 | 按次 Pack 假设 $4.99–9.99；V1 只埋点与文案档位，不接支付 |
| **D-OVSE-11** | 与导出门面关系 | Overseas 成功终点从「发微信」改为「Post to Instagram」；国内合同不变 |

---

## 6. Share Pack 规格

### 6.1 表面定义

| Surface ID | 规格 | 来源 | V1 |
|------------|------|------|----|
| `instagram` | 1080×1350 · 4:5 · max 10 页 · letterbox 默认 | 现有 profile | **Must** |
| `ig_stories` | 1080×1920 · 9:16 · 4–6 页（封面+高光） | **新建** profile（可参考 `douyin_cover` 画布，多页） | Should |
| `share_link` | 鉴权 HTML 短链 | SHARING 路径 B 子集 | Could（P1） |
| `pdf` | 打印友好 PDF | 现有/print 路径增强 | Could（P1） |
| `wechat_chat` / longshot | 竖版长图 | 现有 | Advanced（Overseas）/ Default（zh） |
| `wechat_moments` / `xiaohongshu` | 国内平台 | 现有 | `locale=zh` only 展示 |

### 6.2 一次导出产物（Overseas 默认）

目录示例（落在 trip 导出目录）：

```
export/share-pack/
  caption.txt                 # title + hook + suggested hashtags（可选）
  publish-instagram.txt       # 英文发布步骤（来自 publish_guide）
  carousel/
    {slug}-ins-01.png
    …
    {slug}-ins-0N.png
  {slug}-instagram.zip        # carousel 打包，便于隔空投送/网盘
  stories/                    # 若勾选
    {slug}-stories-01.png
    …
```

### 6.3 张数策略

复用 `resolve_aspect_slide_count`（与小红书同一 Guizang 校准公式）：

| 条件 | N |
|------|---|
| 用户指定 `slideCount` | clamp 到 profile min/max |
| 自动 · photos &lt; 12 | 约 3–6 |
| 自动 · photos ≥ 12 | 约 5–9，上限 10（Instagram 实务） |
| 极小 trip | 允许 1 张；引导文案提示「也可发单图帖」 |

### 6.4 发布指引（替换微信话术）

`instagram.publish_guide`（en）须包含：

1. Save / unzip → Photos  
2. Instagram → New post → Select in order 01→N  
3. Paste caption from `caption.txt`  
4. 页脚 `{i}/{n}` 用于顺序确认  

成功 Modal（Studio）一句主文案示例：

> **Ready to post.** Open the ZIP, select photos 01→N in Instagram, paste your caption.

### 6.5 与 Longshot 2.0 的边界

| 项 | 规则 |
|----|------|
| Capture | 仍 **full_once** + Python 切分；禁止 P1 fallback（ADR-016） |
| 命名 | 沿用 `file_prefix_for_platform` → `{slug}-ins` |
| Job 原子性 | `PlatformExportWriter` 不变 |
| 新 surface `ig_stories` | 新 profile + 同一分支 B；单独立项实施任务，不阻塞 Carousel Must |

---

## 7. 文案与模板（locale=en）

### 7.1 Narrate

| 项 | 要求 |
|----|------|
| Provider | 可配置；Overseas 文档推荐可出海的 provider；无 Key 时 **英文 stub**（禁止中文模板） |
| Tone | 保留 `relaxed` / `documentary`；en 下措辞改为短 caption |
| 输出字段 | `title`, `hook`, `chapter.lead`, `epilogue`；另生成 `shareCaption`（单段，≤2200 IG 限内建议 ≤300） |
| 禁用 | 直出「帧记录」「拼成这一页」等中文 stub |

### 7.2 UI 文案层

| 区域 | zh | en |
|------|----|----|
| Dock 主 CTA | 长图 | **Share** |
| 导出 Popover 默认 | 微信群 | **Instagram carousel** |
| 成功引导 | 怎么发群 | **How to post** |
| Advanced | 平台… | Long image / PDF / Link |

### 7.3 视觉

- V1 不强制新 HTML 模板仓库；优先 **CSS 变量 / 封面风格** 做出 Clean / Film 两套观感。  
- 避免强「小红书手帐贴纸」默认；贴纸类后置。  
- 字体：Overseas 预览使用拉丁文字友好栈（与现有中文字体策略并存，按 locale 切换）。

---

## 8. Studio 与配置需求

### 8.1 配置

```yaml
studio:
  locale: en                 # zh | en
  longshot2:
    enabled: true
    platforms:               # Overseas 建议默认
      - instagram
      # ig_stories           # Phase 后开
    defaultPlatform: instagram
```

| 规则 | 说明 |
|------|------|
| `locale=en` | UI en；narrate en；`defaultPlatform=instagram`；隐藏微信/小红书菜单（CLI 仍可用） |
| `locale=zh` | 现网行为；`defaultPlatform` 缺省 `wechat_chat` |
| 灰度 | 允许 `studio.longshot2.platforms` 显式加入 `instagram`（与现网灰度机制一致） |

### 8.2 Studio 导出门面（Overseas）

在 [PRD-PREVIEW-EXPORT-FACADE-V1](./PRD-PREVIEW-EXPORT-FACADE-V1.md) 合同上增量：

| 原合同（zh） | Overseas 增量 |
|--------------|---------------|
| 无 pending → 一键长图 | 无 pending → 一键 **Share Pack（Carousel）** |
| 成功 → 发群一句 | 成功 → **Post to Instagram** 一句 + 打开文件夹/ZIP |
| Dock 不抬平台大面板 | 维持；平台切换仍在导出 ▾；但 **默认项已是 IG** |
| 更新并导出续跑 | 续跑目标改为当前 defaultPlatform Job |

### 8.3 CLI

```powershell
python -m travelogue export-longshot trips\<id> --platform instagram --scale 2
python -m travelogue export-share-pack trips\<id>   # 新命令：打 ZIP + caption（可薄封装现有 Job）
```

`export-share-pack`：V1 可为 `export-longshot --platform instagram` + 打包脚本的产品别名；须写入 CLI-SPEC。

### 8.4 代码触点（实施指引，非本 PRD 详设）

| 模块 | 改动方向 |
|------|----------|
| `config/platform_profiles.yaml` | 强化 `instagram` guide 英文；新增 `ig_stories`（Should） |
| `travelogue/export/platform_profiles.py` | `instagram` 移出「仅 CLI」心智：Studio allow-list 可含之；更新 hint_kind |
| `templates/studio/preview-toolbar/longshot.js` | locale 感知默认平台与成功文案 |
| `travelogue/services/narrate.py` | `locale=en` stub/LLM brief |
| `travelogue/config/loader.py` | `studio.locale` / `defaultPlatform` |
| 导出门面埋点 | 见 §9.3 |

---

## 9. 商业与运营（产品边界内）

### 9.1 定价假设（不接支付）

| 层 | 内容 | 价格假设 |
|----|------|----------|
| Free | 1× Share Pack（可带轻水印或限页） | $0 |
| Pack | 单次 trip 全表面 | $4.99–9.99 |
| Pro 年费 | 无限次 + 无水印 | $29–49 / year |

V1 只预留文案与事件，**不实现 IAP/Stripe**。

### 9.2 冷启动（运营执行，产品配合）

- Before/After Reels（相册乱 → Carousel 滑动）  
- 英语区 10 个 micro travel creators（1–10 万粉）  
- Waitlist 页强调 on-device  

### 9.3 埋点（Must）

| 事件 | 属性 |
|------|------|
| `share_pack_start` | `locale`, `platform`, `slideCount` |
| `share_pack_success` | `pageCount`, `elapsedMs`, `hasZip` |
| `share_pack_fail` | `code` |
| `share_pack_surface_select` | `surface`（carousel/stories/longshot/…） |
| `share_pack_open_folder` | — |
| `locale_active` | `zh`/`en`（会话级） |

漏斗：导入完成 → 首次 Share 点击 → success →（可选）声称已发帖问卷。

### 9.4 90 天成功指标

| 指标 | 目标 |
|------|------|
| 导入 → 首次导出完成率 | ≥40% |
| 导出后选用 Carousel 占比 | ≥70%（Overseas 会话） |
| 种子「24h 内已分享」自报 | ≥25% |
| `locale=zh` 回归缺陷 | 0 P0 |

---

## 10. 工程与架构约束

1. **遵守 ADR-016**：platform 模式禁止 P1；full capture + 切分。  
2. **遵守 SHARING 双轨隐私假设**：Carousel/长图 = 用户自担传播；Link = 鉴权。  
3. **不破坏** Desktop Installer V1 的本地数据目录约定；Overseas 仅为 locale/文案/默认平台配置差。  
4. **性能**：同 Longshot 2.0 G-LNG2-07；Share Pack 额外 ZIP 时间单独记 telemetry，P95 增加建议 ≤3s（小包）。  
5. **测试**：新增 `locale=en` 冒烟 + `instagram` Studio 导出 AC；保留 zh 全量回归。

---

## 11. 验收（AC 摘要）

| ID | 验收项 | 级别 |
|----|--------|------|
| **AC-OVSE-00** | `locale=zh`：微信群长图 / 朋友圈 / 小红书与改版前一致 | P0 |
| **AC-OVSE-01** | `locale=en`：Dock/导出默认 Instagram；一次导出得到 1080×1350 序列 | P0 |
| **AC-OVSE-02** | 成功后存在 ZIP（或等价打包）+ `caption.txt` + 英文 publish 指引 | P0 |
| **AC-OVSE-03** | 无 LLM Key 时英文 stub 可读；无中文残留 | P0 |
| **AC-OVSE-04** | 成功 Modal 无「微信/朋友圈/小红书」字样（en） | P0 |
| **AC-OVSE-05** | CLI `--platform instagram` 与 Studio 产物规格一致 | P0 |
| **AC-OVSE-06** | 非法 platform / 超大 capture 错误码与 LNG2 一致，英文可读 | P1 |
| **AC-OVSE-07** | `ig_stories` 多页导出（若本迭代包含） | P1 |
| **AC-OVSE-08** | 埋点事件齐全，可出周报 | P1 |
| **AC-OVSE-09** | 英语种子 5 人无指导完成：导入→Share→找到 ZIP | P0 发布闸门 |

完整手测脚本见后续 ACCEPTANCE 文档。

---

## 12. 里程碑（建议 90 天）

| 阶段 | 周期 | 交付 | Go/No-Go |
|------|------|------|----------|
| **M-OVSE-0** | W1 | 配置 `locale` + `instagram` 进 Studio allow-list；英文成功指引 | 能 CLI+Studio 出 IG 图 |
| **M-OVSE-1** | W2–W3 | Share Pack ZIP + caption.txt + en stub narrate | AC-OVSE-01～04 |
| **M-OVSE-2** | W4–W5 | 导出门面 Overseas 合同 + 埋点 + zh 回归 | AC-OVSE-00/08/09 |
| **M-OVSE-3** | W6–W8 | `ig_stories` + 2 套视觉差 + waitlist 文案 | Should 项 |
| **M-OVSE-4** | W9–W12 | 50 英语种子内测；指标复盘；决定是否做 iOS/支付 | G-OVSE-05 |

**明确后置**：App Store、Stripe/IAP、日韩文案、社交重排（Longshot P3）、云端多租户。

---

## 13. 风险与开放问题

### 13.1 风险

| 风险 | 缓解 |
|------|------|
| 切分长图→4:5 letterbox 在海外观感「杂志感不足」 | M-OVSE-3 评估是否启动「社交卡片重排」（对齐 LNG2 P3 backlog） |
| 英文 stub 质量差导致「AI 味」差评 | 优先短 caption；鼓励用户改一字 |
| 与国内导出门面文案分叉失控 | 单一 i18n 字典；禁止硬编码双语 |
| 种子以为是云端 App | 首屏强调 on-device；对齐 UX-TRUST |

### 13.2 开放问题（OQ）

| ID | 问题 | 默认建议 |
|----|------|----------|
| **OQ-01** | 对外品牌最终名 | AfterTrip；评审拍板 |
| **OQ-02** | Share Link 是否进 V1 | **否**，进 M-OVSE-3/P1 |
| **OQ-03** | macOS / iOS 何时做 | 指标过 G-OVSE-05 后再立 PRD |
| **OQ-04** | `ig_stories` 是否必须与 Carousel 同包默认勾选 | 默认 **不勾选**，减少首次等待 |
| **OQ-05** | 水印策略 | Free 轻水印 vs 限次；倾向限次免水印 |

---

## 14. 附录

### A. 与现有文档关系

| 文档 | 关系 |
|------|------|
| SHARING.md | 增补「路径 A Overseas = Share Pack」；路径 B 不变 |
| PRD-LONGSHOT-2.0 | `instagram` 从 Phase C CLI-only → Studio；本文为产品升级说明 |
| ADR-016 | 无架构变更；仅消费方与默认项变更 |
| PRD-PREVIEW-EXPORT-FACADE-V1 | Overseas locale 下成功引导替换 |
| PRD-DESKTOP-INSTALLER-V1 | 可后续加 en 首启包；本 PRD 不阻塞 |

### B. 术语

| 术语 | 含义 |
|------|------|
| Share Pack | 一次导出得到的多文件社交素材包 |
| Carousel | Instagram 多图帖（本产品 4:5） |
| Domestic / Overseas | `locale=zh` / `locale=en` 产品模式 |
| Surface | 单一导出规格（instagram / ig_stories / …） |

### C. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-07-14 | 初稿：基于海外运营策略 + 代码库 As-Is（instagram Phase C、ADR-016、导出门面、中文 narrate stub） |
