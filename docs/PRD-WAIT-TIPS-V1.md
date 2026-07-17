# Travelogue · 导入等待教育卡片 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.2.0** |
| **状态** | **Conditional Go · 跨职能 MF 已回写** · **可 Kickoff W0（编码另排期）** · 本轮文档已齐 |
| **主题代号** | 「Wait Tips」— 等待壳内可关闭教育 · 从属进度 · 非 L1 |
| **触发来源** | 产品提议：生成等待期自动播放功能介绍/试用技巧；2026-07-17 设计对齐 |
| **前置条件** | 首页 v2 Importing 壳可用；[PRD-FIRST-SESSION-TRUST-V1](./PRD-FIRST-SESSION-TRUST-V1.md) 进度诚实合同有效；[PRD-HELP-ONBOARDING-V1](./PRD-HELP-ONBOARDING-V1.md)「忙碌态零 L1」有效 |
| **关联文档** | [PRD-FTUE-OPTIMIZATION-V1.md](./PRD-FTUE-OPTIMIZATION-V1.md) · [PRD-DESKTOP-LLM-SETUP-V1.md](./PRD-DESKTOP-LLM-SETUP-V1.md)（能力卡） · [PRD-UX-TRUST-V1.md](./PRD-UX-TRUST-V1.md) |
| **评审记录** | [acceptance-records/wait-tips-v1-review-2026-07-17.md](./acceptance-records/wait-tips-v1-review-2026-07-17.md) · Conditional Go |
| **线框** | [wireframes/wait-tips-v1-wireframe.html](./wireframes/wait-tips-v1-wireframe.html) · F1–F5（W0 UI 挡门：F1/F3；COPY 挡门：F2） |
| **文案润色** | [acceptance-records/wait-tips-v1-copy-workshop-2026-07-17.md](./acceptance-records/wait-tips-v1-copy-workshop-2026-07-17.md) · 市场/运营/产品三席 |
| **验收** | [ACCEPTANCE-WAIT-TIPS-V1.md](./ACCEPTANCE-WAIT-TIPS-V1.md)（本文 §9 为索引） |
| **实施清单** | [IMPLEMENTATION-WAIT-TIPS-V1.md](./IMPLEMENTATION-WAIT-TIPS-V1.md) · **可 Kickoff W0（编码另排期）** |
| **手测** | [acceptance-records/wait-tips-v1-dogfood-CHECKLIST.md](./acceptance-records/wait-tips-v1-dogfood-CHECKLIST.md) |
| **评审模板** | [acceptance-records/wait-tips-v1-review-TEMPLATE.md](./acceptance-records/wait-tips-v1-review-TEMPLATE.md) |
| **更新日期** | 2026-07-17 |

> **v0.2.0 评审回写摘要（跨职能 Conditional Go · 2026-07-17）**
>
> - BLK-01～03：Help / FST / FTUE 交叉脚注  
> - BLK-04：OQ-WT-01～05 **已关闭**（§10）  
> - BLK-05：线框 F1/F3 = W0 UI 挡门；F2 = COPY 挡门  
> - BLK-06：拆 ACCEPTANCE + dogfood  
> - BLK-07：§4 文案为 Kickoff 唯一字符串源  
> - **本轮不动代码**；编码 Kickoff 另排期

> **定位**
>
> 导入生成往往占用数十秒至数分钟。现有 Importing 壳已承担**进度诚实 + 慢安抚**，但次区缺少「等待时可读」的轻量教育。  
> **本 PRD 不新增 Help L1、不重做空态/能力卡/FirstSuccess**，只在导入忙碌壳内增加一套 **可关闭、可跳过、自动轮播** 的 Wait Tips，填补「能力卡关掉 → FirstSuccess」之间的认知空档。
>
> **一句话目标**：用户在等成稿时，可选地了解「会得到什么 / 为何放心 / 做完先干什么 / 怎么试用」，且**随时可关、永不挡进度**。
>
> **产品共识（五条铁律）**
>
> 1. **进度主句优先** — Tips 永远是次内容；阶段主句 / 进度条 / 慢安抚语义不被卡片抢走。  
> 2. **不是 L1 Coach** — 不写 Help `seen`、不脉冲、不挡取消；遵守 D-HELP-08′「忙碌态零 L1」。  
> 3. **可关、可静** — 关闭后本会话不再出现；悬停/聚焦暂停；成功/失败/取消时立刻收起。  
> 4. **Outcome-first** — 教结果与试用技巧，**不复述** stage / estimate；先验货再长图；**不教精修、不教微信操作、不承诺杂志级文案**。  
> 5. **首版只挂导入等待** — 长图 Dock / 更新版面 / 失败面不做轮播。

> **v0.1.1 文案修订（2026-07-17）**
>
> 牌组由「过程 3 + 下一步 2 + 试用 2」改为 **Outcome-first 六张**：结果 · 信任 · 能力 · 下一步 · 示例 · 选片。  
> 砍掉与进度主句 / estimate 行撞车的过程复述；词表对齐能力卡与 FirstSuccess 冻结句。

> **v0.1.2 信任卡叙事修订（2026-07-17）**
>
> WT-02：**目的 = 绝对隐私**；「本机 / 不上传」仅为手段与证据，不作标题主语。  
> 文案语气对齐营销承诺（你的旅行只属于你），仍遵守不夸大、不涉微信/API。

> **v0.1.3 三席润色（2026-07-17）**
>
> 市场 × 运营 × 产品联席：去说明书腔与辩解腔；标签改口语；WT-02 定稿「回忆，只放在你身边」。  
> 纪要：[wait-tips-v1-copy-workshop-2026-07-17.md](./acceptance-records/wait-tips-v1-copy-workshop-2026-07-17.md)

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0.1 | 与相邻主题的边界 |
| §1 | 问题与机会 |
| §2 | 目标 / 非目标 / 成功指标 |
| §3 | 体验合同与冻结决策（D-WT-*） |
| §4 | 卡片文案清单（冻结候选） |
| §5 | 触发、持久化、仲裁 |
| §6 | 埋点 |
| §7 | 非功能 |
| §8 | 里程碑与线框 |
| §9 | 验收 AC（草案） |
| §10 | 风险与开放问题 |

### 0.1 与相邻主题的边界

| 主题 | 关系 | 本主题做什么 |
|------|------|--------------|
| [First-Session Trust](./PRD-FIRST-SESSION-TRUST-V1.md) | **依赖 · 不抢** | 进度主句 / 慢安抚 / FirstSuccess ≤1s 仍归 FST；Tips 嵌其次区 |
| [Help](./PRD-HELP-ONBOARDING-V1.md) | **明确互斥于 L1** | Tips ≠ coachmark / tip / 脉冲；关闭不写 Help seen；忙碌态仍零 L1 |
| [FTUE](./PRD-FTUE-OPTIMIZATION-V1.md) | **并行不抢** | 空态 / 示例 CTA / 冷启动仍归 FTUE；Tips 不替代能力卡 |
| 能力卡（Desktop LLM / L0） | **时段错开** | 能力卡仅 idle；Importing 时只允许 Wait Tips |
| [Share-Ready](./PRD-SHARE-READY-OPTIMIZATION-V1.md) | **不做** | 意图卡 / 真图样品不进等待轮播 |

---

## 1. 背景与问题

### 1.1 As-Is

| 触点 | 时机 | 缺口 |
|------|------|------|
| 能力卡 | 首页 idle 首访 | Importing 时不展示；关掉后等待期无教育 |
| Importing 壳 | 导入 Job | 有阶段主句 + 慢安抚，无「做什么 / 做完干嘛」可读内容 |
| FirstSuccess | Job 成功后 | 才教验货→长图；等待期用户只能干等 |
| Help L1 | 预览 idle | **忙碌态禁止**；不能拿来填等待 |

### 1.2 要解决的问题（P-WT-*）

| ID | 问题 | 影响 |
|----|------|------|
| **P-WT-01** | 等待期只有进度，用户不知「系统在忙什么」之外的产品价值 | 焦虑 / 无聊 / 误以为卡死（即使进度诚实） |
| **P-WT-02** | 首访下一步（验货→长图）要到 FirstSuccess 才说 | 等待期白白浪费认知窗口 |
| **P-WT-03** | 若做成 L1 coach / 全屏 tour | 违反忙碌态零 L1，且抢进度注意力 |

---

## 2. 目标 / 非目标 / 成功指标

### 2.1 目标

1. 在 **导入 Importing** 忙碌壳内提供 **6 张** Outcome-first 自动轮播卡片（默认约 10s/张）。  
2. 用户可：**关闭整套**、**上一张/下一张**、**悬停暂停**。  
3. 内容覆盖：结果交付 · 隐私承诺 · 自动能力 · 成稿下一步 · 示例试用 · 选片技巧。  
4. 与 FST / Help 仲裁清晰：Tips 失败时进度面仍完整可用。

### 2.2 非目标（V1）

- 全站 Product Tour / 连环气泡  
- 长图导出 Dock、layoutUpdating、失败重试面的轮播  
- 精修、G1、多平台、微信发群步骤教学  
- 用 Tips 掩盖假进度或替代慢安抚  
- 与首页 showcase carousel（示例卷轴）合并为同一组件心智

### 2.3 成功指标（评审后启用）

| 指标 | 建议门槛 | 说明 |
|------|----------|------|
| Tips 曝光且未立刻关闭 | ≥40% 首访导入会话 | 关闭过快说明干扰 |
| 平均浏览张数 | ≥2 | 有真实阅读 |
| 关闭后导入完成率 | ≥未曝光组 | 不得伤害完成 |
| FirstSuccess「打开预览」转化 | 不显著下降 | 守卫指标 |

---

## 3. 体验合同与冻结决策

### 3.1 布局合同

```
┌─────────────────────────────────────┐
│ 来源 · 示例相册                      │
│ 正在生成你的游记画册…                 │
│ 自动分章 · 配文 · 排版 · 可离开稍后回来 │
│ ████████░░░░  进度条                 │
│ 正在分章挑选…          ← 阶段主句     │
│ （可选）慢安抚次行                    │
│ ─────────────────────────────────── │
│ ┌ Wait Tips 卡片 ────────── [×] ┐  │
│ │ 标签 · 标题 · 一句说明          │  │
│ │ ‹  ···  ›                      │  │
│ └────────────────────────────────┘  │
│              [取消]                  │
└─────────────────────────────────────┘
```

- Tips 区在阶段主句（及慢安抚）**下方**、取消按钮**上方**。  
- 卡片视觉弱于进度区：更小字号、更低对比；禁止金色主 CTA 抢「取消/继续等待」心智。  
- 窄屏：卡片可缩为单行标题+一句，控件保留关闭。

### 3.2 冻结决策（D-WT-*）

| ID | 决策 |
|----|------|
| **D-WT-01** | 宿主 = 首页 v2 `v2-importing` 面板次区；**不做**独立 Modal / 全屏遮罩 |
| **D-WT-02** | 默认停留 **10s**（首张可 **12s**）；悬停或 `:focus-within` 暂停；失焦继续 |
| **D-WT-03** | 提供：关闭 ×、上一张、下一张、圆点（或等价进度点）；圆点可点击跳转 |
| **D-WT-04** | 关闭 → `waitTipsDismissed=1`（建议 `localStorage`）；**本会话 + 持久**均不再自动播；可用帮助抽屉「重播等待提示」可选（W2，非挡门） |
| **D-WT-05** | `status=succeeded|failed|cancelled` 或离开 Importing → **立即卸载** Tips；不得拖到 FirstSuccess |
| **D-WT-06** | Tips **不**调用 `isHelpL1Blocked` 之外的 L1 通道；**不**写入任何 Help seen key |
| **D-WT-07** | 预计等待过短（建议 Job 已运行 & 剩余可见时间启发式 &lt; 15s，或阶段已到 render 末段）可**不再新开**下一张；已显示的可淡出 |
| **D-WT-08** | 文案禁区：微信发群步骤、精修入口、API Key、Playwright/Chromium、杂志级文案承诺、假百分比 |
| **D-WT-09** | 长图 Task Dock **V1 不做** Wait Tips |
| **D-WT-10** | 与慢安抚并存：慢安抚仍只走 `stage-sub` / slow-hint；Tips 不复述「比预期久一些」 |
| **D-WT-11** | 文案结构 = **Outcome-first**；禁止与 `STAGE_LABELS` / estimate「自动分章 · 配文 · 排版 · 可离开稍后回来」同义复述 |
| **D-WT-12** | 词表：优先「本机」「卷轴预览」「长图」；少用裸「验货」；不用「你的电脑里」替代「本机」 |
| **D-WT-13** | WT-02 信任卡：**隐私目的优先**——标题说情感承诺（如「只放在你身边」）；正文才点「本机 · 不上传」作证据；禁止标题写成功能说明「照片留在本机」；禁止正文辩解腔（「为的是…不是…」） |
| **D-WT-14** | 文案语气：可朗读、第二人称温度；禁用内部词「主链」；标签用口语（马上就好 / 安心 / 省心），不用 IA 分类名 |

### 3.3 出现条件

| 条件 | 行为 |
|------|------|
| 进入 Importing 且未 dismiss | 进度壳渲染后 **≥2s** 再显现 Tips（避免与主句抢第一眼） |
| 已 dismiss | 整套不渲染 |
| 能力卡仍在屏 | 不可能（Importing 时能力卡已关）；若竞态，Tips 让位进度即可 |
| prefers-reduced-motion | 关闭自动轮播，仅手动翻页 |

---

## 4. 卡片文案清单（V1 冻结 · 三席润色 v0.1.3）

> 标签 · 标题 · 正文。标题 ≤ 14 字 · 正文 ≤ 32 字（中文，含标点）。  
> 类别配额：**结果 1 · 信任 1 · 能力 1 · 下一步 1 · 试用 2**。  
> 润色纪要：[wait-tips-v1-copy-workshop-2026-07-17.md](./acceptance-records/wait-tips-v1-copy-workshop-2026-07-17.md)

| # | 类别 | 标签 | 标题 | 正文 | 备注 |
|---|------|------|------|------|------|
| **WT-01** | 结果 | 马上就好 | 可翻的卷轴，可发的长图 | 先在大屏慢慢看；喜欢了，再存一张发群用的长图。 | 交付物清晰；不教怎么发微信 |
| **WT-02** | 信任 | 安心 | 回忆，只放在你身边 | 不上传云端，在本机悄悄成册。私密，是旅行该有的样子。 | 目的在标题；手段作证据；无辩解腔（D-WT-13） |
| **WT-03** | 能力 | 省心 | 分章配文排版，交给它 | 选好这一趟的照片就行，不用先一张张归类。 | 能力句口语化；不讲算法 |
| **WT-04** | 下一步 | 小提示 | 先翻卷轴，再存长图 | 打开预览慢慢看；满意了，再点「长图」收下。 | 对齐 FirstSuccess；不提精修 |
| **WT-05** | 试用 | 想先试试 | 没有照片？先用示例 | 向导里一键试用，流程和自己的相册一模一样。 | 场景钩子；禁用「主链」 |
| **WT-06** | 试用 | 选片诀窍 | 一趟旅行，一个文件夹 | 同一次出行放一起就好，不必事先精挑细选。 | 降失败导入；对齐向导心智 |

**轮播顺序**：WT-01 → 02 → 03 → 04 → 05 → 06 → 循环（若仍在 Importing 且未触发 D-WT-07）。

**刻意不做的卡 / 句式**：

| 砍掉 | 原因 |
|------|------|
| 过程复述 stage | 与主句撞车 |
| 「可离开」专卡 | estimate 已有 |
| 「为的是…不是…」辩解句 | 营销否决 · 生硬 |
| 「主链」 | 运营否决 · 内部词 |
| 标签写成 IA 分类名 | 市场否决 · 无温度 |

**可选第 7 张（非默认 · OQ-WT-05）**：仅当壳上 estimate 不再含「可离开」时，可加「离开也没关系 / 生成会继续；回到 Studio 就能看到进度或成稿。」

---

## 5. 触发、持久化、仲裁

### 5.1 持久化键（建议）

| Key | 存储 | 语义 |
|-----|------|------|
| `travelogue.waitTips.dismissed` | localStorage | 用户关闭整套 → 不再自动播 |
| `travelogue.waitTips.version` | localStorage | 文案大改时可 bump；默认不强制重播 |

不引入 per-trip seen（等待教育与 trip 无关）。

### 5.2 仲裁优先级（Importing 期间）

1. 进度主句 / 进度条 / 取消  
2. 慢安抚次行（FST）  
3. Wait Tips（本文）  
4. **禁止**：Help L1、能力卡、FirstSuccess、微信教学

### 5.3 与取消确认

取消确认 Modal（「继续等待」）打开时：**暂停**自动轮播；Modal 关闭后若仍 Importing 则恢复。

---

## 6. 埋点（草案）

| 事件 | 属性 |
|------|------|
| `wait_tips_show` | `card_id`, `job_stage`, `elapsed_ms` |
| `wait_tips_auto_advance` | `from_id`, `to_id` |
| `wait_tips_manual_nav` | `from_id`, `to_id`, `dir` |
| `wait_tips_pause` | `card_id`, `reason=hover\|focus` |
| `wait_tips_dismiss` | `card_id`, `viewed_count`, `elapsed_ms` |
| `wait_tips_suppress_short_wait` | `job_stage`（D-WT-07） |

---

## 7. 非功能

| 项 | 要求 |
|----|------|
| A11Y | 卡片区 `aria-roledescription="轮播"`；关闭按钮可聚焦；自动切换时 `aria-live="polite"` 更新标题（reduced-motion 关闭自动） |
| 性能 | 无网络图；纯文本 + CSS；不影响 Job 轮询 |
| 降级 | Tips JS 失败 → 静默不渲染，进度壳不受影响 |
| i18n | V1 仅中文 copy 表 |

---

## 8. 里程碑与线框

| 波次 | 内容 | 挡门 |
|------|------|------|
| **本稿** | PRD v0.1.3 + 线框 F1–F5 + 实施清单 | 跨职能评审（DOC-WT-06） |
| **W0** | Importing 壳嵌入 · **6 卡 Outcome-first** · 10s · 关闭持久化 · 埋点核心 | 线框 F1/F3 + AC-WT-01～06 · 见 IMPLEMENTATION §3 |
| **W1** | D-WT-07 短等待抑制 · reduced-motion · 埋点补齐 | AC-WT-07～08 · IMPLEMENTATION §4 |
| **W2（可选）** | 帮助抽屉「重播等待提示」 | 非挡门 · IMPLEMENTATION §5 |

线框 Tab 见 [wait-tips-v1-wireframe.html](./wireframes/wait-tips-v1-wireframe.html)：

| Tab | 内容 |
|-----|------|
| F1 | To-Be：Tips 嵌导入进度壳 |
| F2 | 六张 Outcome-first 文案墙 |
| F3 | 交互：自动切 / 暂停 / 关闭 |
| F4 | 与 Help L1 / FST 仲裁 |
| F5 | 禁止形态 |

---

## 9. 验收 AC（草案）

| ID | 断言 |
|----|------|
| **AC-WT-01** | Importing 且未 dismiss 时，进度主句下方出现 Tips；主句随 stage 变化不受 Tips 影响 |
| **AC-WT-02** | 默认约 10s 自动切下一张；可手动上一张/下一张 |
| **AC-WT-03** | 悬停卡片区时自动轮播暂停；移出后继续 |
| **AC-WT-04** | 点 × 关闭后，同会话再次进入 Importing **不再**出现；刷新后仍不出现（localStorage） |
| **AC-WT-05** | Job succeeded → ≤1s 关忙碌壳时 Tips 已卸载；FirstSuccess 上无 Tips 残留 |
| **AC-WT-06** | Importing 期间无 Help L1 / 导出脉冲 / 能力卡 |
| **AC-WT-07** | 文案不含微信操作步骤、精修、工程词、杂志级承诺；不含与 stage/estimate 同义的过程复述 |
| **AC-WT-08** | `prefers-reduced-motion: reduce` 时不自动轮播 |
| **AC-WT-09** | 六张牌字面对齐 §4 v0.1.3；WT-02 标题为隐私情感承诺（非「照片留在本机」）；全文无「主链」、无「为的是…不是…」辩解句 |

---

## 10. 风险与开放问题

### 10.1 OQ 已关闭（2026-07-17 跨职能）

| ID | 决议 |
|----|------|
| **OQ-WT-01** | dismiss = **localStorage** `travelogue.waitTips.dismissed` |
| **OQ-WT-02** | V1 **不按 stage 同步**卡片 |
| **OQ-WT-03** | V1 **纯文案 + 标签色**；禁截图墙 |
| **OQ-WT-04** | 短尾抑制（D-WT-07）归 **W1**；W0 必须在终态立刻卸载 |
| **OQ-WT-05** | 默认 **不加**第 7 张「可离开」 |

### 10.2 残余风险

| 风险 | 缓解 |
|------|------|
| 抢进度注意力 | 弱视觉 · ≥2s 显现 · 可关 · 降级完整进度壳 |
| 文案回退生硬腔 | 契约锁 §4；市场签 F2 |
| 与 Help 合同误解 | Help D-HELP-08′ 脚注：Tips ≠ L1 |

---

## 附录 A · 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-07-17 | 初稿 · 过程向 7 卡 · 线框 F1–F5 |
| v0.1.1 | 2026-07-17 | Outcome-first 6 卡 · D-WT-11/12 · 线框文案与标签层级同步 |
| v0.1.2 | 2026-07-17 | WT-02 改为隐私目的叙事（营销向）· D-WT-13 |
| v0.1.3 | 2026-07-17 | 市场/运营/产品三席润色全套六张 · D-WT-14 · 纪要入库 |
| v0.2.0 | 2026-07-17 | 跨职能 Conditional Go · OQ 关闭 · AC/脚注齐 · 可 Kickoff W0（编码另排期） |
