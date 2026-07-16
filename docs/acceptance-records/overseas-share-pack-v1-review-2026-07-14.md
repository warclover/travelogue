# Travelogue · Overseas Share Pack V1 深度评审记录

| 属性 | 内容 |
|---|---|
| 评审对象 | [PRD-OVERSEAS-SHARE-PACK-V1.md](../PRD-OVERSEAS-SHARE-PACK-V1.md) |
| 评审日期 | 2026-07-14 |
| 评审视角 | 海外社交产品、创作者工作流、增长运营、架构与可交付性 |
| 评审结论 | **Conditional No-Go：批准 Discovery，不批准完整 V1 直接开工** |
| 后续文档 | [PRD-OVERSEAS-SHARE-PACK-V2.md](../PRD-OVERSEAS-SHARE-PACK-V2.md) |

## 1. 结论

PRD V1 的战略方向正确：

- 海外默认交付物应从微信式超长图转向 Instagram Carousel；
- 现有 ingest → curate → narrate → layout → render 管线值得复用；
- Instagram 4:5 profile、Longshot 2.0 分支 B 和 CLI 导出已形成工程基础；
- 不应为海外市场复制第二套策展算法。

但当前方案把“已有长卷切成 4:5 图片并打 ZIP”定义为 Instagram-ready，解决的是尺寸兼容，不是海外用户真正购买的任务：

> 从一趟旅行的大量照片中，快速得到一组有开头、有节奏、有结尾、只需少量修改即可真实发布的 Instagram 轮播。

最大风险不是工程无法导出，而是用户看到“被切碎的网页”后，仍回到 Instagram、Canva 或手机相册重做。

因此评审决议为：

1. 批准一个两周的 Overseas Carousel Discovery；
2. 不批准 V1 原 M-OVSE-0～M-OVSE-4 整体开工；
3. 先验证原生 6～8 页社交构图是否显著优于长卷切片；
4. 验证成立后，再实施 Studio、Share Pack、英文文案和跨设备交付。

## 2. 最值得押注的产品楔子

建议将产品楔子收敛为：

> 面向已有 Instagram 旅行轮播习惯、对隐私敏感且接受电脑处理的英语用户，把 30～150 张旅行照片在本地自动精选并编成 6～8 页可发布轮播，目标 10～15 分钟完成。

不建议首轮押注：

- 通用跨平台一稿多发；
- 私密家庭 Share Link；
- 专业 Creator 工作台；
- Stories、Pinterest、TikTok、Shorts 同时适配；
- 两套视觉皮肤或模板商城；
- AfterTrip 品牌迁移；
- 按次 Share Pack 收费。

## 3. 关键事实修正

### 3.1 Instagram

- Carousel 平台上限已从 10 提升至 20 个媒体项；
- 4:5、1080×1350 仍是合理的 feed 默认规格；
- V1 可主动建议 6～10 页，但必须称“产品建议上限”，不能称平台上限；
- Instagram 主页网格已采用纵向缩略图，首图仍需单独检查 3:4 grid crop；
- `{i}/{n}` 页码会强化模板感，应默认关闭或可选；
- caption 中普通 URL 不是稳定的可点击回流路径，Share Link 不能直接承担轮播回流闭环。

建议 profile 拆分：

```yaml
platformMaxPages: 20
recommendedMinPages: 6
recommendedMaxPages: 10
defaultPages: 7
specVerifiedAt: 2026-07-14
```

### 3.2 其他平台

- TikTok Photo Mode 是 9:16、音乐伴随、搜索型长文案的独立内容表面，不能直接复用 IG 4:5 文件；
- Pinterest 是 2:3、搜索、收藏和外链驱动的长期发现表面，不是旅行结束后的即时分享；
- Stories 的原生价值来自贴纸、音乐、回复、链接和安全区，静态 9:16 图片组只解决部分任务；
- YouTube Shorts/Reels 需要视频时间线、转场、音频、字幕和封面；
- Threads/X 需要独立文本结构与少图适配。

V1 应明确排除上述表面，而不是将产品表述为通用海外 Share Pack。

## 4. 最高优先级产品问题

### P0-01 · 价值主张过宽

“Share Pack”描述的是文件集合，不是用户结果。主 CTA 应优先使用：

> Create an Instagram carousel

而不是抽象的 Share。

### P0-02 · 社交原生构图被错误后置

现有实现是：

```text
完整长卷 capture → 内容边界切分 → 4:5 letterbox → PNG
```

它不能保证：

- 首图承担 hook；
- 前三页形成浏览动力；
- 每页有明确角色；
- 文案不会跨页断裂；
- 人脸和地标不被弱化；
- 文字在手机上可读；
- 最后一页完成收束。

建议保留现有策展结果，增加薄的 social composition adapter：

```text
trip.json / curated assets
→ page-role planner
→ social slide manifest
→ fixed-ratio card renderer
→ platform export
```

这不是第二套策展引擎，而是同一故事的社交展示适配器。

推荐默认页面角色：

1. Hook cover；
2. Strongest photo；
3. Place / time context；
4～6. Highlights with rhythm variation；
7. Close / reflection / optional CTA。

长卷切片仅作为技术 fallback 或 Discovery 对照组。

### P0-03 · 缺少最低编辑权

生成后必须至少支持：

- 整组缩略图预览；
- 拖拽排序；
- 删除弱页；
- 替换页面照片；
- 调整焦点与裁切；
- 修改首图标题；
- 编辑和复制 caption；
- 重新生成时锁定满意页面。

否则“自动生成”之后仍需去其他工具返工。

### P0-04 · Windows 到手机的交付断点

“Open ZIP → Photos”不是完整流程。Windows 用户仍需：

1. 找到 ZIP；
2. 解压；
3. 将多张图片传到手机；
4. 确认顺序；
5. 在 Instagram 中重新选择。

建议优先验证：

- Instagram Web 直接发 Carousel 是否可满足目标用户；
- 打开文件夹与复制 caption 的桌面路径；
- 显式同意、同一局域网内的 QR 取图方案；
- 用户已有 OneDrive/Google Drive 时的可选引导，但不得破坏本地优先承诺。

跨设备完成率必须进入发布门禁。

### P0-05 · locale 模型错误耦合

`locale=en` 不应同时决定 UI、内容、市场、平台可见性和成功引导。

建议拆为：

```yaml
studio:
  uiLocale: en
  marketProfile: global
  defaultSurface: instagram
  enabledSurfaces:
    - instagram

narrative:
  contentLocale: en
```

中文用户仍可导出 Instagram；英文 UI 也不应被强制隐藏其他允许表面。

## 5. 工程现状核验

### 已有基础

- `config/platform_profiles.yaml` 已定义 Instagram 1080×1350；
- ADR-016 分支 B 已实现 full capture、内容边界切分、后处理与原子写盘；
- CLI/API 已支持 `--platform instagram`；
- Instagram 输出尺寸与命名已有单测；
- 国内微信、朋友圈和小红书路径具有较强回归资产。

### 主要缺口

- Studio 前端硬过滤 Instagram；
- `studio.locale`、`defaultPlatform` 不存在；
- 无 `export-share-pack`；
- 无 Share Pack job、manifest、ZIP 原子合同；
- 无 `shareCaption`；
- narrate stub 深度绑定中文；
- 成功引导与帮助仍以微信为中心；
- 新埋点不在前端 allow-list；
- 无海外 AC、实施文档和真实发帖验收；
- Installer Gate A 尚未完成。

结论：

> 引擎层已有 80% 以上基础，产品交付层不足 20%；低算法风险，中高产品集成风险。

## 6. Share Pack 工程合同缺口

V1 只提供目录示例，没有冻结：

- request / response schema；
- job 类型和状态机；
- manifest 版本；
- caption 持久化路径与覆盖规则；
- ZIP 包含规则；
- 幂等与覆盖策略；
- trip 更新时的 stale 行为；
- PNG 成功但 ZIP 失败时的处理；
- 磁盘不足、无权限、文件占用、Chromium 缺失等错误；
- 刷新或关闭页面后的恢复；
- 临时目录和最终提交边界。

建议使用独立 `share_pack` job，不继续把产品打包语义塞进 longshot job。

原子边界应为：

```text
临时目录生成 slides + caption + alt text + guide + manifest + zip
→ 校验文件、尺寸、数量与 checksum
→ 全部成功后 rename 为最终目录
→ 失败回滚临时目录
```

## 7. 隐私、版权与合规

必须在 V1 升为 P0：

1. “Photos stay on this device” 与实际数据流一致；
2. 若使用外部 LLM，明确发送的是文字、地点、缩略图还是原图；
3. 遥测默认不联网，研究 cohort 明确 opt-in；
4. 输出保证剥离 EXIF/GPS，并有自动化验收；
5. 提醒检查未成年人、同行者、住址、车牌、票据、护照、房号与实时位置；
6. 提供轻量版权确认：“I have the right to publish these photos”；
7. AI 仅辅助选片、排版或 caption 通常不等于合成媒体；生成或实质修改写实人物/场景时再提示平台披露；
8. 提供 Sponsored / Gifted stay / Affiliate 等披露模板，但不替用户作法律判断；
9. 不附带跨平台“热门音乐”，平台音乐许可不能默认互通；
10. 字体、模板资产、模型权重和示例照片授权必须进入发布门禁。

## 8. 建议验证实验

先执行 12～15 人 concierge A/B：

| 项 | A 组 | B 组 |
|---|---|---|
| 输入 | 用户自己的 30～150 张旅行照片 | 相同 |
| 产物 | 当前长卷切片 4:5 | 半人工原生 6～8 页轮播 |
| 用户知情 | 不告知具体生成方式 | 不告知具体生成方式 |
| 测量 | 愿发程度、真实发布、耗时、修改、返工、付款 | 相同 |

建议 Go 门槛：

- 无指导完成率 ≥70%，N≥15；
- 中位可发布时间 ≤15 分钟；
- B 相对 A 偏好 ≥70%；
- 24 小时真实发布率 ≥40%；
- 跨设备完成率 ≥80%；
- 导出后回 Canva/IG 大幅返工率 ≤25%；
- 至少 3/20 发生真实付款或可退款预购。

若原生卡片版没有显著胜出，不应继续建设 Stories、PDF、Link、更多模板或跨平台导出。

## 9. 定价与增长建议

不建议把纯本地 Pack 的默认价格直接定为 $4.99～9.99/次：

- 用户承担本机算力与存储；
- 旅行天然低频；
- 按次付款会放大首次价值不确定；
- 与项目现有“一次性桌面发行版”商业方向冲突。

首轮只测试两个真实报价：

- 官方桌面版一次性 $29～49；
- Creator 版一次性 $79～99。

按次收费更适合云端处理、人工精修或 concierge 服务。

首轮只运行两个可归因渠道：

1. privacy-conscious travel photographers 所在的摄影/旅行社区；
2. 已稳定发布 photo dump/carousel 的小型 Instagram 账号。

渠道成功必须追踪到：

```text
合格照片集 → 完成 Carousel → 真实发布 → 真实报价/付款
```

浏览、点赞和 waitlist 不能替代上述证据。

## 10. PRD 必须重写的章节

| 章节 | 必须回写 |
|---|---|
| 目标与范围 | 只保留 Carousel V1；Stories/Link/PDF/皮肤/品牌移出阻塞范围 |
| 定位与品牌 | 改为 post-worthy travel carousel；品牌另立 Decision |
| 用户与市场 | 冻结 ICP、设备组合、替代方案、招募与排除人群 |
| 产品规格 | 先定义页面角色、编辑权、网格安全区，再定义像素与 ZIP |
| 文案 | caption schema、alt text、事实确认、编辑权、fallback、披露模板 |
| 配置 | 拆分 uiLocale/contentLocale/marketProfile/defaultSurface |
| API / 数据 | 独立 job、manifest、幂等、原子性、错误恢复 |
| 指标 | 删除 Carousel 选用率；增加真实发布、耗时、返工和跨设备完成率 |
| NFR | 隐私数据流、遥测同意、Unicode、磁盘、ZIP、sRGB、字体许可、日志脱敏 |
| 验收 | Given/When/Then、真实账号发帖、真实设备、10 个 trip 视觉金样例 |
| 发布 | Discovery Gate → Prototype Gate → Seed Gate；feature flag 与回滚门槛 |

## 11. 最终决议

**批准：**

- 两周 Overseas Carousel Discovery；
- 复用现有 Instagram profile 做 A 组；
- 半人工建立原生 6～8 页 B 组；
- 用户研究、真实发帖和跨设备验证；
- 根据证据冻结 PRD V2。

**不批准：**

- 按 V1 原 90 天计划直接开发；
- 将长卷切片宣传为 Instagram-native；
- 同时建设 Stories、Link、PDF、第二套皮肤；
- 未验证品牌即切换 AfterTrip；
- 默认联网遥测；
- 在真实发布与付款前承诺固定价格。

---

可视化评审：`overseas-share-pack-v1-review.canvas.tsx`（Cursor Canvas）。
