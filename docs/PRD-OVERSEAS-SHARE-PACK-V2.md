# Travelogue · Overseas Instagram Carousel V1 产品需求文档

| 属性 | 内容 |
|---|---|
| **文档版本** | **v2.0.0-OVERSEAS** |
| **状态** | Draft · 待 Discovery Gate 评审 |
| **主题代号** | Overseas Carousel V1 |
| **取代文档** | [PRD-OVERSEAS-SHARE-PACK-V1.md](./PRD-OVERSEAS-SHARE-PACK-V1.md) |
| **评审依据** | [Overseas Share Pack V1 深度评审](./acceptance-records/overseas-share-pack-v1-review-2026-07-14.md) |
| **核心前置** | Longshot 2.0 Instagram CLI/API 可用；Desktop Installer Gate A 可支持英语种子 |
| **验收** | 后续拆 `ACCEPTANCE-OVERSEAS-CAROUSEL-V1.md` |
| **实施** | Discovery Go 后拆 `IMPLEMENTATION-OVERSEAS-CAROUSEL-V1.md` |
| **更新日期** | 2026-07-14 |

> **产品定位**
>
> Travelogue Overseas V1 不卖“多个文件的 Share Pack”，而是帮助英语用户把一趟旅行的 30～150 张照片，
> 在本地快速精选并编成一组 **post-worthy Instagram carousel**。
>
> 默认目标是 **6～8 页、10～15 分钟、少量修改后可以真实发布**。
>
> 现有策展管线继续复用；新增的是薄的社交构图与交付层，不复制第二套策展算法。

> **本版评审决议**
>
> 1. 只批准先执行两周 Discovery，不批准完整 V1 直接开发；
> 2. 必须先证明原生页面角色构图显著优于“长卷切片 + letterbox”；
> 3. Instagram 是唯一 V1 平台；
> 4. Stories、TikTok、Pinterest、Shorts、Threads/X、Link、PDF、支付和第二套皮肤全部后置；
> 5. Windows → 实际发布设备的交付完成率是 P0，不再视为发布后的文案问题。

---

## 0. 读者指南

| 章节 | 需要冻结的决策 |
|---|---|
| §1 | 为什么 V1 从通用 Share Pack 收窄为 Instagram-native Carousel |
| §2 | Discovery、Build、Release 三层目标与非目标 |
| §3 | 唯一 ICP、JTBD 与替代方案 |
| §4 | 产品原则和已拍板决策 |
| §5 | 端到端体验与最小编辑权 |
| §6 | 页面角色、视觉、安全区和文案 |
| §7 | 导出、跨设备交付与产物合同 |
| §8 | 配置、数据模型、API 与 Job 状态机 |
| §9 | 隐私、版权、AI 与遥测约束 |
| §10 | 指标、实验与研究口径 |
| §11 | NFR、错误恢复与兼容 |
| §12 | 验收与发布门禁 |
| §13 | 里程碑、风险和开放问题 |

---

## 1. 背景与核心判断

### 1.1 项目现状

Travelogue 当前是本地优先的照片策展与成书工具：

```text
选择本地照片
→ ingest / curate
→ narrate
→ layout / render
→ Studio 预览精修
→ 微信长图 / 平台切片 / HTML
```

已具备的海外基础：

- `instagram` profile 已定义为 1080×1350、4:5；
- ADR-016 分支 B 已支持 full capture、内容边界切分、后处理和原子写盘；
- CLI/API 已能生成 Instagram PNG 序列；
- 国内导出路径已有较强回归资产。

尚未具备：

- Instagram 在 Studio 中的一等入口；
- 英文 UI、英文 stub、独立 `shareCaption`；
- 社交页面角色构图；
- 整组预览与最小编辑权；
- Share Pack job、manifest、ZIP 原子合同；
- Windows 到手机或 Instagram Web 的完整交付路径；
- 海外真实发帖、复用和付款证据。

### 1.2 V1 PRD 的关键误判

旧方案将：

```text
长卷切成 4:5 图片 + ZIP + caption.txt
```

等同于：

```text
Instagram-ready Share Pack
```

二者并不相等。

平台尺寸合规不能保证：

- 首图能抓住注意力；
- 前三页有叙事动力；
- 每页文字在手机上可读；
- 人脸、地标和主体被正确保护；
- 页面不会像被切碎的网页；
- 用户无需回 Canva 或 Instagram 重排。

### 1.3 核心产品判断

> **海外 V1 的价值不是“跨平台导出”，而是“更少选片、更少排版、更少返工地完成一条真实旅行轮播”。**

可复用的是：

- 照片选择；
- 时间、地点与章节事实；
- 故事结构；
- 用户已确认的文案；
- 焦点与审美评分。

不可直接复用的是：

- 最终像素比例；
- 页面角色；
- 每个平台的文字密度；
- 音乐、互动贴纸和 CTA；
- 平台安全区；
- 发布步骤。

---

## 2. 目标、成功定义与非目标

### 2.1 Discovery 目标

| ID | 目标 | 成功口径 |
|---|---|---|
| **G-DISC-01** | 证明原生 6～8 页轮播比长卷切片更愿意发布 | 盲测 B 相对 A 偏好 ≥70% |
| **G-DISC-02** | 证明目标用户可在电脑完成主要编辑 | 无指导完成率 ≥70%，N≥15 |
| **G-DISC-03** | 找到可接受的发布设备交付路径 | 跨设备或 Instagram Web 完成率 ≥80% |
| **G-DISC-04** | 证明用户会真实发，而非只说喜欢 | 24 小时真实发布率 ≥40% |
| **G-DISC-05** | 获得初步付款证据 | 至少 3/20 真实付款或可退款预购 |

### 2.2 Build 目标

Discovery Go 后，V1 Build 的产品目标为：

| ID | 目标 | 验收方向 |
|---|---|---|
| **G-OV2-01** | 一次导入得到默认 7 页 Instagram 轮播草稿 | 页面角色和尺寸 AC |
| **G-OV2-02** | 用户可完成必要修改，无需自由画布 | 排序、删页、替图、焦点、标题和 caption AC |
| **G-OV2-03** | 一次导出得到完整、原子的 Carousel Pack | manifest、ZIP、caption、alt text、guide AC |
| **G-OV2-04** | 用户能将产物带到实际发布环境 | Desktop/Web/Phone 交付 AC |
| **G-OV2-05** | 英文 UI 和内容可用，中文路径不回归 | i18n 与 zh 回归 AC |
| **G-OV2-06** | 隐私承诺与数据流一致 | 本地处理、外部 provider、遥测与元数据 AC |
| **G-OV2-07** | 失败可解释、可重试、不留下残包 | Job 原子性与错误恢复 AC |

### 2.3 产品成功定义

产品成功不是：

- PNG 已落盘；
- ZIP 已生成；
- 用户点击了 Carousel；
- 用户口头表示“挺好看”。

产品成功是：

> 用户使用自己的照片，在无操作指导下完成一组轮播，做完必要修改，将素材带到真实发布环境，并在 24 小时内发布或明确拒绝发布。

### 2.4 V1 明确非目标

| 类别 | 非目标 |
|---|---|
| **平台** | TikTok Photo Mode、Pinterest、Stories、Reels、YouTube Shorts、Threads、X |
| **分享** | 鉴权 Share Link、公开托管、多租户、直接发布 API、社交账号授权 |
| **格式** | PDF、打印、微信长图打包进 Overseas 默认 Pack |
| **编辑器** | Canva 式自由画布、复杂图层、任意字体市场、模板商城 |
| **视觉** | 第二套皮肤、贴纸体系、动态模板、视频转场 |
| **商业** | Stripe/IAP、按次扣费、水印付费墙、订阅系统 |
| **品牌** | AfterTrip 正式更名、包名迁移、商店品牌切换 |
| **端** | macOS/iOS/App Store；可在 Discovery 中记录因此流失的用户 |
| **算法** | 重写 ingest、聚类、CLIP、LTE 或独立海外策展引擎 |

---

## 3. 目标用户、JTBD 与市场边界

### 3.1 唯一 ICP

V1 只服务以下用户：

| 维度 | 条件 |
|---|---|
| 语言 | 英语 UI；内容以英语为主 |
| 行为 | 每季度至少发布一次 Instagram 旅行 Carousel / photo dump |
| 输入 | 单次旅行 30～150 张照片 |
| 当前替代 | Instagram 原生选择、Canva、手机相册、Lightroom 后手工发布 |
| 痛点 | 选片耗时、顺序难定、版式缺乏故事感、想少做设计 |
| 设备 | 接受先在 Windows 电脑处理；实际发布设备需记录 |
| 审美 | 希望有杂志感，但不需要专业品牌模板 |
| 隐私 | 不愿默认上传完整相册，重视本地处理 |

### 3.2 排除人群

V1 不以以下人群为核心：

- 只拍视频或只发 Reels 的用户；
- 一年几乎不发社交内容的普通旅行者；
- 需要完整品牌控制、商业审批和团队协作的职业创作者；
- 主要需求是私密家庭分享的 Privacy Host；
- 不接受电脑参与、只愿使用手机的用户；
- 主要发布平台不是 Instagram 的用户。

排除不等于永久放弃；目的是让首轮证据可解释。

### 3.3 JTBD

> 旅行结束后的 24～72 小时内，当我面对 30～150 张照片时，
> 我想快速得到一组有开头、有节奏、有结尾的 Instagram 轮播，
> 并只做少量修改就能发布，
> 而不是重新选片、决定顺序和学习 Canva。

### 3.4 竞争替代

用户真正比较的是：

1. 直接在 Instagram 里多选照片；
2. 手机相册自动精选；
3. Canva 模板；
4. Lightroom/Photoshop 后手工排版；
5. 不发。

Travelogue 必须证明：

- 比 Instagram 原生选择更有故事；
- 比 Canva 更快；
- 比自动相册更可控；
- 比专业工具更少学习成本；
- 最终结果值得发，而不是只值得保存。

### 3.5 市场顺序

不再先按国家拍脑袋排序。Discovery 招募优先级由以下条件决定：

1. 能否招到符合 ICP 的真实用户；
2. 是否能记录设备组合；
3. 是否愿意使用自己的照片；
4. 是否愿意提供真实发布证据；
5. 是否允许后续付款实验。

英语市场可覆盖 US / UK / AU / CA，但不得以国家替代 ICP。

---

## 4. 产品原则与已拍板决策

### 4.1 产品原则

1. **Post-worthy before multi-surface**：先让一条 IG Carousel 值得发，再扩平台。
2. **Curation reused, composition adapted**：复用策展，平台构图独立适配。
3. **Edit the decisions, not every pixel**：允许改关键决策，不提供自由画布。
4. **Publishing is the finish line**：导出不是终点，进入真实发布环境才是。
5. **Local by default, explicit when not**：默认本地；任何外发数据都显式说明。
6. **One user job per release**：V1 不混入家庭私密分享和专业 Creator 工作台。
7. **Evidence before expansion**：Stories、Link、第二模板和支付都依赖真实证据。

### 4.2 已拍板决策

| ID | 决策 | 结论 |
|---|---|---|
| **D-OV2-01** | V1 唯一平台 | Instagram Carousel |
| **D-OV2-02** | 默认画布 | 1080×1350，4:5 |
| **D-OV2-03** | 平台上限 | 20；产品推荐 6～10；默认 7 |
| **D-OV2-04** | 构图策略 | 原生 Page Roles 为目标；长卷切片只作 Discovery A 组/fallback |
| **D-OV2-05** | 架构 | 复用策展；新增 social composition adapter，不 fork 管线 |
| **D-OV2-06** | 最小编辑 | 排序、删页、替图、焦点裁切、首图标题、caption |
| **D-OV2-07** | 页码 | 默认关闭；可选开启 |
| **D-OV2-08** | 语言配置 | UI、内容、市场和 surface 分离 |
| **D-OV2-09** | 导出 | 独立 `share_pack` job，原子提交 |
| **D-OV2-10** | 跨设备 | 是发布门禁，不是 P1 文案优化 |
| **D-OV2-11** | 遥测 | 默认不联网；研究 cohort 显式 opt-in |
| **D-OV2-12** | 品牌 | V1 继续使用 Travelogue；AfterTrip 另行验证 |
| **D-OV2-13** | 定价 | PRD 不冻结价格；只定义付款实验 |
| **D-OV2-14** | zh 回归 | 默认配置仍为 zh + wechat_chat |

---

## 5. 端到端产品体验

### 5.1 主流程

```text
进入 Studio
→ 选择照片文件夹
→ 本地导入与策展
→ 生成默认 7 页 Carousel draft
→ 整组预览
→ 必要修改
→ Export Instagram carousel
→ 生成完整 Pack
→ 复制 caption / 打开发布路径
→ 用户进入 Instagram 发布
```

### 5.2 首屏

Overseas market profile 下建议：

**标题**

> Turn one trip into a post-worthy carousel

**主 CTA**

> Choose trip photos

**信任行**

> Photos stay on this device

若用户启用外部 LLM，信任行必须切换为准确表述，例如：

> Photos stay local. Selected trip text is sent to {provider} to draft captions.

禁止：

- 在首屏展示 Stories、PDF、Link、Long image；
- 使用“AI magic”作为主价值；
- 宣称所有数据都在本地但实际向外部 provider 发送内容；
- 用功能列表替代输入 → 结果示例。

### 5.3 生成中

产品可见阶段：

| 阶段 | 用户文案 |
|---|---|
| importing | Importing photos… |
| curating | Choosing the strongest moments… |
| composing | Building your carousel story… |
| rendering | Rendering 7 slides… |
| ready | Your carousel draft is ready |

进度不得伪造精确百分比；可使用阶段 + 已完成项。

### 5.4 生成后主界面

信息层级：

1. 全部页面缩略图；
2. 当前页大预览；
3. 关键编辑动作；
4. `Export Instagram carousel` 主 CTA；
5. caption 编辑与复制；
6. `More options` 只收纳页码、页数和重新生成。

不显示尚未支持的平台。

### 5.5 最小编辑权

| ID | 能力 | V1 |
|---|---|---|
| **F-EDIT-01** | 拖拽页面排序 | Must |
| **F-EDIT-02** | 删除页面；不得低于 3 页 | Must |
| **F-EDIT-03** | 从已导入照片替换某页主图 | Must |
| **F-EDIT-04** | 调整焦点/裁切位置 | Must |
| **F-EDIT-05** | 编辑首图标题与副标题 | Must |
| **F-EDIT-06** | 编辑、复制 caption | Must |
| **F-EDIT-07** | 锁定页面后重新生成其余页 | Should，不阻塞首个原型 |
| **F-EDIT-08** | 任意移动图层、改字体和装饰 | 非目标 |

### 5.6 脏状态与导出

- 修改照片、排序、标题、caption 或焦点后，Pack 标记 stale；
- 点导出时必须使用当前已确认版本；
- 不允许静默导出旧页面；
- 导出中重复点击应聚焦到当前 Job，不创建并行重复 Job；
- 用户离开页面后，回来可看到 Job 最终状态；
- trip 在导出中被修改时，当前 Job 以启动时的 revision 生成，并提示新版本需重新导出。

---

## 6. 社交构图、视觉与文案

### 6.1 Social composition adapter

输入：

- 已策展照片与评分；
- 章节、时间、地点；
- 用户锁定/排除的素材；
- 封面候选；
- narrate 字段；
- 焦点或人脸区域（若已有且合规）。

输出：

```json
{
  "schemaVersion": "1.0",
  "surface": "instagram",
  "slides": [
    {
      "id": "slide-01",
      "role": "hook_cover",
      "assetIds": ["asset-17"],
      "title": "Three days in Lisbon",
      "subtitle": "Trams, tiled streets, and one very late dinner",
      "focalPoint": {"x": 0.54, "y": 0.42},
      "locked": false
    }
  ]
}
```

adapter 只决定社交展示结构，不重新运行照片去重、聚类或基础审美评分。

### 6.2 默认 Page Roles

| 页 | Role | 目标 |
|---|---|---|
| 1 | `hook_cover` | 在 feed 和 profile grid 中建立主题 |
| 2 | `hero` | 展示最强照片，快速兑现首图承诺 |
| 3 | `context` | 地点、时间或旅程起点 |
| 4～6 | `highlight` | 不同节奏、场景和人物关系 |
| 7 | `closing` | 反思、回味或轻 CTA |

允许：

- 3～10 页；
- 跳过 context；
- 以 hero 作为无字封面；
- closing 仅使用照片，不强制品牌尾页。

禁止：

- 为凑页数插入纯品牌页；
- 连续多页使用相同照片和相同尺度；
- 自动添加关注、点赞、收藏等 engagement bait；
- 默认添加 Travelogue 水印。

### 6.3 Instagram 规格

| 项 | 规格 |
|---|---|
| 画布 | 1080×1350 |
| 比例 | 4:5 |
| 平台最大媒体项 | 20 |
| 产品推荐 | 6～10 |
| 默认 | 7 |
| 格式 | PNG；后续可评估高质量 JPEG |
| 色彩 | sRGB |
| 文件顺序 | `01` 起始、零填充 |
| 页码 | 默认关闭 |
| 规格核验日期 | 2026-07-14 |

平台规格变更不得要求发布新代码才能调整上限；profile 需配置化。

### 6.4 安全区

必须同时预览：

1. 完整 4:5 feed；
2. 3:4 profile grid thumbnail；
3. 小屏手机文字可读性。

最低要求：

- 首图关键标题在 3:4 grid crop 中完整；
- 人脸、主体和地标不得被默认裁掉；
- 文本与画布边缘保持结构性留白；
- 正文不得依赖低对比度叠字；
- 最小字号和对比度在视觉金样例中冻结；
- alt text 不嵌入图片，而是独立输出。

具体像素安全区由视觉原型评审后写入 Design Spec，不在本 PRD 臆造固定值。

### 6.5 Caption contract

`shareCaption` 为用户可编辑字段，包含：

```json
{
  "hook": "A slow weekend in Lisbon.",
  "body": "We followed the yellow trams...",
  "cta": "",
  "hashtags": ["#lisbon", "#portugaltravel"],
  "disclosure": "",
  "contentLocale": "en"
}
```

规则：

- hook 必须在 Instagram 折叠前独立成立；
- body 默认简短，不以 2200 字符上限作为目标；
- hashtags 默认 0～5 个，可全部删除；
- 不生成虚假的地点、日期、人物关系或体验；
- 涉及事实不确定时标记待确认；
- 用户编辑后不得被重新生成静默覆盖；
- 无 LLM Key 时必须有自然、克制的英文 fallback；
- 不使用“AI-generated masterpiece”等工具味表达。

### 6.6 Alt text

每页输出独立 alt text：

```json
{
  "slideId": "slide-02",
  "altText": "A yellow tram turning through a narrow tiled street in Lisbon."
}
```

要求：

- 描述主要视觉内容，不堆关键词；
- 不猜测人物身份、族裔、健康或敏感属性；
- 用户可编辑；
- 输出到 `alt-text.txt` 和 manifest；
- publish guide 说明如何在 Instagram Advanced settings 中填写。

### 6.7 商业与 AI 披露文案

提供可选模板：

- `Ad`
- `Sponsored`
- `Gifted stay`
- `Affiliate link`

产品不得自动判断法律义务。

仅使用 AI 辅助选片、布局和 caption 时，不自动要求“合成媒体”标签。
若未来生成或实质修改写实人物、场景、语音或视频，应另立披露规则。

---

## 7. 导出、跨设备交付与产物合同

### 7.1 导出主动作

主 CTA：

> Export Instagram carousel

导出成功后动作优先级：

1. `Post from this computer`（若 Instagram Web 验证可用）；
2. `Send to phone`（仅在安全方案通过后开放）；
3. `Copy caption`；
4. `Show in folder`；
5. `Open ZIP`。

ZIP 是兼容产物，不是首要用户价值。

### 7.2 跨设备交付

Discovery 必须比较：

| 路径 | 验证内容 |
|---|---|
| Instagram Web | 能否完成多图顺序、caption、alt text 和发布 |
| 本地文件夹 | 用户能否找到文件并保持顺序 |
| 用户自有云盘 | 是否已有自然工作流；必须由用户主动选择 |
| 局域网 QR | 防火墙、网络发现、临时 token、过期、显式同意和照片暴露范围 |

局域网 QR 若实施，必须满足：

- 默认关闭；
- 用户主动点击后启动临时服务；
- 使用随机短期 token；
- 只暴露当前 Pack；
- 显示局域网访问提示；
- 默认 10 分钟过期；
- 用户可立即停止；
- 不上传第三方云端；
- 日志不记录照片内容与长期访问 token。

### 7.3 Pack 目录

```text
export/share-packs/{pack-id}/
  manifest.json
  instagram-caption.txt
  alt-text.txt
  publish-instagram.txt
  carousel/
    {slug}-instagram-01.png
    ...
    {slug}-instagram-0N.png
  {slug}-instagram.zip
```

ZIP 内包含：

- `manifest.json`；
- caption；
- alt text；
- publish guide；
- `carousel/` 全部图片。

### 7.4 Manifest

```json
{
  "schemaVersion": "1.0",
  "packId": "sp_20260714_ab12cd",
  "tripId": "lisbon-weekend",
  "tripRevision": "2026-07-14T08:30:00Z",
  "surface": "instagram",
  "uiLocale": "en",
  "contentLocale": "en",
  "createdAt": "2026-07-14T09:00:00Z",
  "pageCount": 7,
  "canvas": {"width": 1080, "height": 1350, "colorSpace": "sRGB"},
  "files": [
    {
      "path": "carousel/lisbon-weekend-instagram-01.png",
      "sha256": "...",
      "slideId": "slide-01",
      "role": "hook_cover"
    }
  ],
  "captionPath": "instagram-caption.txt",
  "altTextPath": "alt-text.txt",
  "guidePath": "publish-instagram.txt"
}
```

### 7.5 原子性与幂等

- Job 先写入 `.part-{jobId}` 临时目录；
- 所有图片、文本、manifest 和 ZIP 完成后执行校验；
- 校验通过后 rename 为最终 `pack-id` 目录；
- 失败时删除临时目录，不留下最终残包；
- 同一 trip revision + composition revision + export options 可复用成功 Pack；
- 用户明确“Export again”时生成新 packId，不静默覆盖旧 Pack；
- 删除旧 Pack 由用户主动操作，不在 V1 自动清理。

### 7.6 成功文案

主句必须根据实际路径生成，禁止统一写“Open ZIP → Photos”。

示例：

> Your 7-slide carousel is ready.

次句：

> Copy the caption, then post from Instagram Web.

或：

> Open this pack on your phone and select slides 01–07 in order.

---

## 8. 配置、数据模型、API 与 Job

### 8.1 配置拆分

```yaml
studio:
  uiLocale: en                    # zh-CN | en
  marketProfile: global           # domestic | global
  defaultSurface: instagram
  enabledSurfaces:
    - instagram

narrative:
  contentLocale: en               # zh-CN | en

privacy:
  telemetryMode: off              # off | research-opt-in
  externalNarration:
    enabled: false
    provider: null

instagram:
  platformMaxPages: 20
  recommendedMinPages: 6
  recommendedMaxPages: 10
  defaultPages: 7
  pageNumbersDefault: false
  specVerifiedAt: "2026-07-14"
```

兼容规则：

- 未配置时保持 `uiLocale=zh-CN`；
- 未配置时 `marketProfile=domestic`；
- 未配置时 `defaultSurface=wechat_chat`；
- 旧 `studio.longshot2.platforms` 继续生效；
- UI 可见性与 API 可调用性必须拆开，不再用 `PHASE_C_CLI_ONLY` 隐式表达产品权限。

### 8.2 Trip 中的 composition 状态

建议独立 sidecar，避免把大量草稿状态直接塞入 `trip.json`：

```text
trips/{trip-id}/social/instagram-composition.json
```

包含：

- composition schema version；
- base trip revision；
- slides；
- page role；
- asset references；
- focal points；
- user locks；
- caption；
- alt text；
- updatedAt。

### 8.3 API

#### 生成或更新草稿

```http
POST /__travelogue/social-compositions
```

```json
{
  "tripId": "lisbon-weekend",
  "surface": "instagram",
  "contentLocale": "en",
  "targetPages": 7,
  "preserveLockedSlides": true
}
```

响应：

```json
{
  "compositionId": "cmp_ab12cd",
  "tripRevision": "2026-07-14T08:30:00Z",
  "slides": [],
  "warnings": []
}
```

#### 保存编辑

```http
PATCH /__travelogue/social-compositions/{compositionId}
```

使用 revision/etag 防止覆盖并发编辑。

#### 导出 Pack

```http
POST /__travelogue/share-packs
```

```json
{
  "tripId": "lisbon-weekend",
  "compositionId": "cmp_ab12cd",
  "surface": "instagram",
  "includeZip": true
}
```

响应：

```json
{
  "jobId": "job_sp_123",
  "state": "queued"
}
```

#### 查询 Job

```http
GET /__travelogue/share-packs/jobs/{jobId}
```

成功结果：

```json
{
  "jobId": "job_sp_123",
  "state": "succeeded",
  "packId": "sp_20260714_ab12cd",
  "packRelPath": "export/share-packs/sp_20260714_ab12cd",
  "zipRelPath": "export/share-packs/sp_20260714_ab12cd/lisbon-weekend-instagram.zip",
  "pageCount": 7,
  "outputs": [],
  "warnings": []
}
```

### 8.4 Job 状态机

```text
queued
→ validating
→ rendering
→ writing_text
→ packaging
→ verifying
→ succeeded

任一阶段 → failed
用户取消 → cancelled
```

UI 文案应对应真实阶段。

### 8.5 错误码

| code | 场景 | 用户动作 |
|---|---|---|
| `E_SP_INVALID_COMPOSITION` | composition 缺失或 schema 不支持 | 返回编辑页重建 |
| `E_SP_TRIP_REVISION_CHANGED` | trip 已更新 | 重新生成或确认旧 revision |
| `E_SP_RENDER_FAILED` | 页面渲染失败 | 重试；保留 composition |
| `E_SP_CHROMIUM_UNAVAILABLE` | Playwright/Chromium 不可用 | 显示安装/修复，不伪装成功 |
| `E_SP_DISK_FULL` | 磁盘不足 | 清理空间后重试 |
| `E_SP_PERMISSION_DENIED` | 输出目录无权限 | 更换目录或权限 |
| `E_SP_FILE_IN_USE` | ZIP/文件被占用 | 关闭占用程序后重试 |
| `E_SP_CAPTION_WRITE_FAILED` | 文本写入失败 | 重试；不提交残包 |
| `E_SP_ZIP_FAILED` | ZIP 失败 | 重试 packaging；不提交最终目录 |
| `E_SP_VERIFY_FAILED` | 尺寸、数量或 checksum 失败 | 自动回滚并记录诊断 |
| `E_SP_CANCELLED` | 用户取消 | 清理临时目录 |

---

## 9. 隐私、版权、AI 与遥测

### 9.1 数据流声明

每种模式必须展示：

| 模式 | 照片 | EXIF/地点 | 文案上下文 | 遥测 |
|---|---|---|---|---|
| Fully local | 本机 | 本机 | 本机 stub | off |
| External caption provider | 原图默认不发送 | 仅经用户确认的必要字段 | 发送到指定 provider | off 或单独 opt-in |
| Research cohort | 同上 | 同上 | 同上 | 显式同意的最小事件 |

如果 provider 需要图片输入，必须另立 PRD 和同意界面，V1 默认不允许。

### 9.2 输出隐私

导出必须：

- 剥离 EXIF、GPS 和设备序列信息；
- 不把本机绝对路径写入 manifest；
- 不把用户 API Key 写入日志或产物；
- 不在图片元数据中写入未经同意的作者身份；
- 日志不记录 caption 全文、人物姓名和照片路径；
- ZIP 只包含 manifest 声明的文件。

### 9.3 发布前检查

首次导出显示轻量检查：

- minors or people who may not want to be posted；
- home addresses, plates, tickets, passports or room numbers；
- real-time location；
- photos you do not have the right to publish。

用户可勾选“不再提示”，但不得用恐吓式文案。

### 9.4 遥测

默认：

```yaml
privacy.telemetryMode: off
```

Research cohort 可显式开启，仅记录：

- 随机 session/cohort ID；
- app version；
- stage；
- page count；
- duration；
- error code；
- 是否完成跨设备步骤；
- 用户主动确认是否发布。

禁止记录：

- 原始照片；
- 文件名和绝对路径；
- caption/alt text 全文；
- 精确地点；
- 人脸数据；
- 外部社交账号。

### 9.5 版权与商业披露

- 用户确认拥有发布照片的权利；
- 示例作品必须取得书面授权；
- 字体、模板、图标、模型权重进入 NOTICE/EULA 审查；
- Sponsored/Gifted/Affiliate 只提供模板，不给法律结论；
- 不附带跨平台音乐素材。

---

## 10. 指标、实验与研究

### 10.1 指标字典

| 指标 | 定义 | 建议门槛 |
|---|---|---|
| 合格启动 | 符合 ICP、使用自己的 30～150 张照片并进入生成 | 作为分母 |
| 无指导完成率 | 无操作提示完成草稿、必要修改和导出 | ≥70%，N≥15 |
| 中位可发布时间 | 选文件夹至用户确认“可以发” | ≤15 分钟 |
| 真实发布率 | 24 小时内提供帖子或截图证据 | ≥40% |
| 原生构图偏好 | 盲测中选择 B 原生卡片而非 A 长卷切片 | ≥70% |
| 返工率 | 导出后回其他工具替换/重排超过半数页面 | ≤25% |
| 跨设备完成率 | 成功进入实际发布环境且保持顺序 | ≥80% |
| 关键编辑负担 | 修改页面数、替图数、裁切数和耗时 | 观察并建立基线 |
| 真实付款 | 非关联用户付款或可退款预购 | ≥3/20 |

删除旧指标：

- Carousel 选用占比 ≥70%；
- 单独以 ZIP 成功率代表产品成功；
- waitlist、浏览、点赞作为 Go 指标。

### 10.2 Discovery A/B

| 项 | A | B |
|---|---|---|
| 输入 | 同一用户照片 | 同一用户照片 |
| 构图 | 现有长卷切片 4:5 | 半人工原生 Page Roles |
| 页数 | 6～10 | 6～8 |
| 呈现 | 隐藏生成方式 | 隐藏生成方式 |
| 评价 | 愿发、首图、节奏、可读性、修改与真实发布 | 相同 |

Discovery No-Go：

- B 偏好低于 60%；
- 真实发布率低于 25%；
- 多数用户仍需回 Canva/IG 大幅返工；
- Windows/发布设备断点导致完成率低于 60%；
- 招募用户实际不是 ICP。

### 10.3 付款实验

PRD 不冻结最终价格。Discovery 后只测试两个清晰报价：

1. 官方桌面版一次性 $29～49；
2. Creator 版一次性 $79～99。

必须使用：

- 真实支付页；
- 可退款预购；
- 明确交付对象；
- 14 天退款记录。

口头“愿意买”不算付款证据。

### 10.4 渠道

只运行两个渠道：

- privacy-conscious travel photography 社区；
- 已稳定发布 IG photo dump/carousel 的小型账号。

归因链：

```text
渠道 → 合格照片集 → 完成 Carousel → 真实发布 → 报价 → 付款
```

---

## 11. 非功能、错误恢复与兼容

### 11.1 性能

性能门槛须绑定测试硬件和输入：

| 输入 | 建议门槛 |
|---|---|
| 30～60 张 | 草稿生成 P50 ≤10 分钟，目标逐步降至 5 分钟 |
| 61～150 张 | 草稿生成 P95 ≤20 分钟 |
| 7 页 Pack | 已有 composition 后导出 P95 ≤90 秒 |
| ZIP 增量 | 典型 Pack P95 ≤3 秒；记录包大小 |

性能不以牺牲照片选择和页面质量为代价。

### 11.2 可靠性

- Pack Job 成功率 ≥95% 才可扩大种子；
- 失败不得残留最终目录；
- 重试不得丢失用户编辑；
- 页面刷新后 Job 状态可恢复；
- 取消后临时目录清理；
- 同一 composition 不产生不可解释的不同结果；
- 任何自动降清晰度必须告知用户。

### 11.3 文件与系统

必须覆盖：

- Windows 10/11；
- 无 Python、无源码；
- 中文与 Unicode 路径；
- OneDrive 路径；
- 超长标题和非法文件名字符；
- 标准用户权限；
- 磁盘空间不足；
- 文件被占用；
- 无 Playwright/Chromium；
- frozen 安装包资源路径。

### 11.4 可访问性

- 全键盘可完成排序以外的主要任务；排序需提供上移/下移替代；
- 焦点顺序与 Modal 焦点归还正确；
- 图片有可编辑描述；
- 颜色不作为唯一状态信号；
- 文本对比度达到 WCAG AA；
- reduced motion；
- 错误文案由读屏可感知。

### 11.5 国际化

- UI 字符串集中管理，不在 JS/Python 分散硬编码双语；
- 支持 pluralization；
- 日期、时间、数字和单位按 locale；
- 文件名 slug 对 Unicode 安全；
- fallback 缺失时不混入中文；
- `uiLocale` 与 `contentLocale` 独立测试。

### 11.6 国内兼容

默认配置升级后：

- `uiLocale=zh-CN`；
- `marketProfile=domestic`；
- `defaultSurface=wechat_chat`；
- 微信群、朋友圈、小红书现有行为与文案不变；
- 旧 localStorage 偏好可迁移或安全回退；
- Overseas feature flag 关闭时不加载新主入口。

---

## 12. 验收与发布门禁

### 12.1 Discovery AC

| ID | Given / When / Then |
|---|---|
| **AC-DISC-01** | Given 合格用户和自有照片，When 完成 A/B 盲测，Then 记录明确偏好与原因 |
| **AC-DISC-02** | Given N≥15，When 无操作指导，Then ≥70% 完成可发布草稿 |
| **AC-DISC-03** | Given 完成草稿，When 进入发布设备，Then ≥80% 保持顺序并完成路径 |
| **AC-DISC-04** | Given 导出完成，When 24 小时回访，Then ≥40% 提供真实发布证据 |
| **AC-DISC-05** | Given 至少 20 次报价，When 支付窗口结束，Then ≥3 笔真实付款/预购 |

### 12.2 Build AC 摘要

| ID | 验收 |
|---|---|
| **AC-OV2-01** | 默认生成 7 页，允许 3～10 页；profile 平台上限为 20 |
| **AC-OV2-02** | 每页 1080×1350、sRGB、命名顺序稳定 |
| **AC-OV2-03** | 默认 Page Roles 完整；不插入品牌凑数页 |
| **AC-OV2-04** | 排序、删页、替图、焦点、首图标题、caption 编辑均可用 |
| **AC-OV2-05** | 首图通过完整 4:5 与 3:4 grid preview |
| **AC-OV2-06** | caption、alt text、guide、manifest 和 ZIP 完整 |
| **AC-OV2-07** | Pack 原子写入；任一阶段失败无最终残包 |
| **AC-OV2-08** | 刷新后 Job 状态可恢复；重试保留编辑 |
| **AC-OV2-09** | Fully local 模式无网络请求 |
| **AC-OV2-10** | 外部 provider 模式准确展示数据流并取得同意 |
| **AC-OV2-11** | 导出图片不含 EXIF/GPS；manifest 无绝对路径 |
| **AC-OV2-12** | Windows → 发布环境路径通过真实设备测试 |
| **AC-OV2-13** | en UI/内容无中文残留；zh 国内 AC 全绿 |
| **AC-OV2-14** | 10 个真实 trip 视觉金样例通过人工评审 |
| **AC-OV2-15** | Unicode、无地点、无 LLM Key、极少/超多候选均有明确行为 |

### 12.3 视觉金样例

至少覆盖：

1. 城市周末；
2. 自然风景；
3. 多人物同行；
4. 夜景；
5. 横图为主；
6. 竖图为主；
7. 照片数量 30；
8. 照片数量 150；
9. 无 GPS；
10. 标题与地点含 Unicode。

人工评分维度：

- 首图；
- 前三页节奏；
- 主体裁切；
- 手机可读性；
- 页面重复；
- 结尾完成感；
- 是否愿意发布；
- 需要修改的页数。

### 12.4 发布 Gate

#### Gate D · Discovery Go

- B 偏好 ≥70%；
- 无指导完成 ≥70%，N≥15；
- 真实发布 ≥40%；
- 跨设备完成 ≥80%；
- 明确至少一种可行交付路径。

#### Gate P · Prototype Go

- 最小编辑权全部可用；
- 10 个视觉金样例通过；
- Pack 合同冻结；
- 隐私数据流评审通过。

#### Gate S · Seed Go

- Installer Gate A 通过；
- Pack Job 成功率 ≥95%；
- P0/P1 缺陷为 0；
- zh 回归全绿；
- 英语种子 N≥15 达成完成和发布门槛；
- feature flag 和回滚路径可用。

#### Gate R · Restricted Release

- 至少 3 笔非关联真实付款；
- 真实发布率稳定；
- 支持成本可控；
- 许可、隐私、NOTICE、示例授权完成；
- 无数据泄漏或误删事故。

---

## 13. 里程碑、风险与开放问题

### 13.1 里程碑

| 阶段 | 时间 | 交付 | Gate |
|---|---|---|---|
| **M0 Discovery** | W1～W2 | A/B concierge、设备路径、真实发布、付款实验 | Gate D |
| **M1 Prototype** | W3～W5 | Page Roles、整组预览、最小编辑权 | Gate P |
| **M2 Pack Contract** | W5～W7 | 独立 Job、manifest、原子 ZIP、错误恢复 | — |
| **M3 English Productization** | W6～W8 | i18n、英文 stub、caption/alt text、成功引导 | — |
| **M4 Seed** | W9～W12 | Installer 种子、N≥15、真实发布与回归 | Gate S |
| **M5 Restricted Release** | 证据驱动 | 许可、隐私、付款与支持闭环 | Gate R |

若 Gate D 未通过，停止 M1～M5，不以新增模板或平台补救。

### 13.2 关键风险

| 风险 | 概率/影响 | 缓解 |
|---|---|---|
| 原生构图未显著优于切片 | 高/高 | Discovery A/B 前置 |
| Windows 用户与目标 ICP 错配 | 高/高 | 记录设备流失；不在未验证前扩 macOS |
| Windows → 手机摩擦过高 | 高/高 | Instagram Web 与 QR 路径前置验证 |
| i18n 分叉破坏国内路径 | 中/高 | 配置拆分、集中字典、zh E2E |
| 外部 LLM 破坏 on-device 信任 | 中/高 | 默认本地；逐字段同意 |
| Pack 部分成功造成误导 | 中/高 | 临时目录、校验、原子 rename |
| 平台规格继续变化 | 中/中 | profile 配置化、specVerifiedAt |
| 用户生成结果仍有 AI 味 | 中/高 | 短文案、可编辑、事实确认、真实样例评审 |
| 旅行低频导致无法复用 | 高/高 | 先按买断/单次价值验证，不强推订阅 |
| 许可和商业文案冲突 | 中/高 | Restricted Release 前完成正式决议 |

### 13.3 开放问题

| ID | 问题 | 默认建议 |
|---|---|---|
| **OQ-OV2-01** | Instagram Web 是否足以成为主发布路径 | Discovery 实测，不预设 |
| **OQ-OV2-02** | 局域网 QR 是否进入 V1 | 仅当 Web/现有路径无法达标 |
| **OQ-OV2-03** | Page Roles 使用独立 HTML 模板还是现有模板变体 | Prototype spike 后 ADR |
| **OQ-OV2-04** | composition sidecar 最终 schema | M1 前冻结 |
| **OQ-OV2-05** | 无 LLM 时 caption fallback 质量门槛 | 10 个金样例 + 英语用户评审 |
| **OQ-OV2-06** | 是否支持 3:4 原生上传 | V1 仍以 4:5 为默认，记录需求 |
| **OQ-OV2-07** | 最终定价 | Gate D 后真实测试 |
| **OQ-OV2-08** | macOS 何时立项 | 至少 10 名合格用户因平台流失且 ≥3 人接受报价 |
| **OQ-OV2-09** | AfterTrip 是否保留 | 完成商标、域名、账号与用户理解测试后决定 |

---

## 14. 追踪矩阵

| 用户问题 | 产品需求 | 验收 |
|---|---|---|
| 不想自己选片和排顺序 | Page Roles + 默认 7 页 | AC-OV2-01/03/14 |
| 自动结果需要小改 | 最小编辑权 | AC-OV2-04 |
| 首图在主页被裁坏 | 3:4 grid preview | AC-OV2-05 |
| 不知道怎么发 | 真实发布路径 | AC-OV2-12 |
| ZIP 或文本缺失 | 原子 Pack | AC-OV2-06/07 |
| 刷新后任务丢失 | Job 恢复 | AC-OV2-08 |
| 担心照片上传 | Fully local + 数据流声明 | AC-OV2-09/10/11 |
| 英文像翻译或 AI | 英文 fallback + 可编辑文案 | AC-OV2-13/14 |
| 国内用户被改坏 | 配置默认与 zh 回归 | AC-OV2-13 |

---

## 15. 外部规格来源

截至 2026-07-14 核验：

- Instagram Carousel 20 项：
  <https://www.theverge.com/2024/8/8/24216111/instagram-carousel-post-expansion>
- Instagram 纵向主页网格：
  <https://www.theverge.com/2025/1/17/24346304/instagram-profile-grids-rectangles-squares>
- TikTok Photo Posting：
  <https://www.tiktok.com/creator-academy/en/article/photo-posting>
- Pinterest Create：
  <https://create.pinterest.com/en-au/product-features/how-to-create-pins/>
- Meta AI 内容标签：
  <https://about.fb.com/news/2024/04/metas-approach-to-labeling-ai-generated-content-and-manipulated-media/>

平台规格必须在实施和发布前重新核验。

---

## 16. 版本记录

| 版本 | 日期 | 说明 |
|---|---|---|
| v2.0.0 | 2026-07-14 | 基于 V1 深度评审重写：从通用 Share Pack 收敛到 Instagram-native Carousel；Discovery 前置；新增 Page Roles、最小编辑权、跨设备、Pack/API、隐私、指标与发布 Gate |

