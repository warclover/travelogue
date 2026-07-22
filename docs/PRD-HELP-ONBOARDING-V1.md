# Travelogue · 帮助与情境引导系统 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | **v1.1.4** |
| **状态** | **有条件通过（Conditional Go）** · 评审 Must-Fix 已回写 · 可开 W0 |
| **主题代号** | 「帮助系统 V1」— 情境引导主链 · 按需救援 · 不打断验货 |
| **前置条件** | Studio 首页 v2（M21）可用；Preview Toolbar v3 可用；[PRD-PREVIEW-REFINE-V1.md](./PRD-PREVIEW-REFINE-V1.md) P0～P2 已落地；[PRD-PREVIEW-REFINE-UX-V1.1.md](./PRD-PREVIEW-REFINE-UX-V1.1.md) **Conditional Go / 模式≠面板已落地**；[PRD-PREVIEW-EXPORT-FACADE-V1.md](./PRD-PREVIEW-EXPORT-FACADE-V1.md) 导出门面合同有效 |
| **关联文档** | [PRD-STUDIO-HOMEPAGE.md](./PRD-STUDIO-HOMEPAGE.md) §6.13 · [PRD-PHASE5.md](./PRD-PHASE5.md) P5-H1 · [PRD-PREVIEW-REFINE-V1.md](./PRD-PREVIEW-REFINE-V1.md) · [PRD-PREVIEW-REFINE-UX-V1.1.md](./PRD-PREVIEW-REFINE-UX-V1.1.md) · [PRD-PREVIEW-EXPORT-FACADE-V1.md](./PRD-PREVIEW-EXPORT-FACADE-V1.md) · [PRD-LONGSHOT-2.0.md](./PRD-LONGSHOT-2.0.md) · [PRD-FIRST-SESSION-TRUST-V1.md](./PRD-FIRST-SESSION-TRUST-V1.md) · [PRD-WAIT-TIPS-V1.md](./PRD-WAIT-TIPS-V1.md)（Importing 非 L1 次内容） · [SHARING.md](./SHARING.md) · [PRD-MINIAPP-P1.md](./PRD-MINIAPP-P1.md)（独立轨道 · 见 §2.2） · [PRD-DESKTOP-LLM-SETUP-V1.md](./PRD-DESKTOP-LLM-SETUP-V1.md)（L0/L1 · H7 · 能力卡 · 见 §12.4） |
| **评审记录** | [acceptance-records/help-onboarding-v1-review-2026-07-14.md](./acceptance-records/help-onboarding-v1-review-2026-07-14.md) · **Conditional Go · MF 已回写本版** |
| **线框** | [wireframes/help-onboarding-v1-wireframe.html](./wireframes/help-onboarding-v1-wireframe.html) · F1–F10（W1 挡门：F1–F3/F7） |
| **验收** | 本文 §10；正式文件可后续拆出 `ACCEPTANCE-HELP-ONBOARDING-V1.md` |
| **实施清单** | 可后续拆出 `IMPLEMENTATION-HELP-ONBOARDING-V1.md` |
| **更新日期** | 2026-07-17 |

> **v1.1.2 交叉修订（2026-07-17 · DOC-FST-03）**
>
> 发群三要素 / `publishGuide` / D-HELP-09：**改为按需查阅**（帮助抽屉 H4、用户点「?」），**不再**作为默认长图成功面强制槽位。  
> 默认成功面合同见 [PRD-FIRST-SESSION-TRUST-V1](./PRD-FIRST-SESSION-TRUST-V1.md)（已保存 + 在文件夹中显示；不教微信）。  
> 铁律 5「落盘≠完成」修订为：必须以**稳定可见的成功确认**为终点；「知道怎么发微信」降为 Help 可选救援，非默认成功面拒收条件。

> **v1.1.3 交叉脚注（2026-07-17 · DOC-WT / BLK-01）**
>
> **D-HELP-08′ 澄清**：「忙碌态零 L1」禁止的是 coach / 脉冲 / Help tip。  
> 导入 Importing 进度壳内的 [Wait Tips](./PRD-WAIT-TIPS-V1.md) 属**进度 UI 次内容**（可关闭轮播），**不是** L1；不写 Help `seen`，不经过 `isHelpL1Blocked` 放行通道。  
> 长图导出 / layoutUpdating 忙碌态仍 **零 L1**，且 Wait Tips V1 **不挂**长图 Dock。

> **v1.1.4 交叉脚注（2026-07-17 · DOC-WT-12）**
>
> 帮助抽屉可提供 **「重播等待提示」**（清 `travelogue.waitTips.dismissed`），属 **按需救援 / 非 L1**。  
> 明示：重播后仅在下次 Importing 再显示小提示，**不是**操作引导，也不挡进度。见 [PRD-WAIT-TIPS-V1](./PRD-WAIT-TIPS-V1.md) D-WT-04 W2。

> **定位**
>
> Travelogue Studio 已有分散的引导触点（空态文案、示例画册、FirstSuccess、导出脉冲、Task Dock、精修 Sheet hint、`publishGuide`），但**没有统一的帮助与情境引导合同**。  
> **本 PRD 不扩精修/导出/算法能力**，只把「第一次接触应用的用户如何快速掌握主链」沉淀为可实施的 **三层帮助系统**，并补齐 PRD 已点名、尚未系统化的认知支架。
>
> **与相邻 PRD 的关系**
>
> | 主题 | 解决什么 |
> |------|----------|
> | **精修体验 V1** | 验货默认 · 保存语义 · 导出拦截 |
> | **精修可用性 V1.1** | 模式≠面板 ·「完成」退出 · 情境对齐 · 导出门面收敛 |
> | **导出门面 V1** | 续跑可靠 · Modal 旅程 · 成功发群一句 · 埋点 |
> | **帮助系统 V1（本文）** | 首访主链何时教什么 · 按需帮助抽屉 · 文案/出现一次合同 · 与现有触点统一 |
>
> **产品共识（六条铁律）**
>
> 1. **不做全站 Product Tour** — 禁止开场连环气泡、强制不可跳过的多步导览。  
> 2. **一条主链，两条人格** — ~80% 分享者只走「导入 → 验货 → 长图 → 发群」；精修/G1/多平台是支线，首访不强推。  
> 3. **Just-in-time** — 只在到达关键节点时教一步；可跳过；每个 L1 **只出现一次有效周期**（可重播）。  
> 4. **复用现有触点** — FirstSuccess、导出脉冲、Task Dock、`publishGuide` 是骨架；统一视觉与文案，忌再堆平行 toast。  
> 5. **落盘 ≠ 完成** — 长图成功必须以「知道怎么发微信」为引导终点（与导出门面 G-EXP-05 对齐）。  
> 6. **忙碌态零 L1** — 导入 Job / 更新版面 / 导出进行中，只允许进度面说话，**不弹** coach / 脉冲打扰（D-HELP-08）。

---

## 0. 读者指南

| 章节 | 必须澄清的问题 |
|------|----------------|
| §0.1 | v1.1.x 相对前版改了什么 |
| §1 背景 | 现有引导散落在哪；首访卡在哪 |
| §2 目标/非目标 | 范围锁死，防止做成文档站或全站 tour |
| §3 体验合同 | 三层架构 + 点击预算 + 文案合同 + V1.1 语义 |
| §4 触达矩阵 | 每个节点：触发 · 文案 · seen key · 优先级 |
| §5 帮助抽屉 | L2 按需救援规格 · 与精修面板冲突 |
| §6 组件与持久化 | Coachmark / Hint 规格 · localStorage 键 · 冻结决策 |
| §7 埋点 | 引导漏斗可观测 |
| §8 非功能 | A11Y · 性能 · 兼容 |
| §9 里程碑 | 分波落地与 Go/No-Go |
| §10 验收 | 可执行 AC |
| §11 风险与开放问题 | 未决项默认建议 |
| §13 | 评审审核清单 |

### 0.1 版本回写摘要

#### v1.1.0（相对 v1.0.0）

| 项 | 结论 |
|----|------|
| 与精修 V1.1 对齐 | §3.3～3.4 / T-REFINE-SAVE / H2 含「完成 ≠ 更新版面」与模式≠面板 |
| **D-HELP-03** | 案 A：脉冲；不叠独立 coach |
| **D-HELP-07 / 08** | 全局技能 seen · 忙碌态零 L1 |
| W0 / W1 | W1 不强制 Coach 组件 |

#### v1.1.1（相对 v1.1.0 · 评审 Must-Fix）

| 项 | 结论 |
|----|------|
| **D-HELP-10** | FirstSuccess **方案 A**：主 CTA=「打开卷轴预览」；「保存长图」为次按钮（关闭 OQ-HELP-01） |
| **D-HELP-03′** | 首访长图：**脉冲 + 一次性可见 tip + aria**；禁止「仅 aria」过验收 |
| **D-HELP-07′** | L1 门禁仅全局键；`exportPulseSeen` per-trip 只读兼容、不再作门禁；双写/重播双清 |
| **D-HELP-09** | 默认微信群：backend `publishGuide` 空时 **客户端三要素兜底**必显 |
| **D-HELP-08′** | `isHelpL1Blocked()`；idle 后可补评估脉冲 |
| 帮助↔精修 | 开帮助关面板保模式；chip/「完成」保留；不清 pending |
| 重播文案 | 明示重置长图引导 **与** 精修保存 hint |
| **线框** | W1 前至少 F1–F3、F7；见 [help-onboarding-v1-wireframe.html](./wireframes/help-onboarding-v1-wireframe.html) |
| AC | 增 04a/05a/06a/13a/16/17 |

---

## 1. 背景与问题

### 1.1 产品一句话（引导设计前提）

把旅行照片自动变成**杂志风卷轴预览 + 可发微信的长图 PNG** 的本地 Studio。默认本地处理、无需注册。主交付物是「可预览卷轴 + 可发群长图」，不是 zip 或链接分享。

### 1.2 As-Is（已落地的引导触点）

| 类型 | 位置 | 机制 | 缺口 |
|------|------|------|------|
| 空态 / 信任行 | 首页 Bento | 价值主张 +「照片留在本机」 | 文件夹心智仍弱 |
| 示例画册 | 首页 demo trip | 无照片也能看到产出 | 试用→真实转化弱（HP-GAP-13） |
| Import 进度 | Importing | 4 段 Job + 慢提示 | 与帮助系统无统一文案合同 |
| FirstSuccess | `first-success.js` | 成功 overlay · 倒计时开预览（现网倒计时常禁用） | **v1.1.1**：主 CTA 须为「打开卷轴预览」；`quick_share`「保存长图」降次按钮（D-HELP-10） |
| 首访导出脉冲 | `init-v3.js` / `longshot.js` | `exportPulseSeen`（含历史 per-trip） | **v1.1.1**：全局门禁 + 可见 tip；busy 门禁（D-HELP-03′/07′/08′） |
| Task Dock | `preview-toolbar-v3-task-dock.js` | 进度/成功 · 部分 `publishGuide` | **v1.1.2**：默认成功面=已保存确认（First-Session Trust）；三要素改 H4 按需（原 v1.1.1 D-HELP-09 范围收窄） |
| G1 横幅 | `features.js` | 结构待确认 | 首访未必理解；属支线 |
| 精修模式 / Sheet | `preview-mode.js` + sheet | V1.1：模式≠面板；「完成」退出；chip「精修中」 | 保存语义 +「完成≠更新版面」未产品化为帮助对照 |
| Phase 5 常驻「?」 | P5-H1 | **规划采纳 · 未系统交付** | 无帮助抽屉、无可重播 |

### 1.3 仍存在的断裂（P-HELP-*）

| ID | 问题 | 影响 | 用户 | 来源 |
|----|------|------|------|------|
| **P-HELP-01** | 无「照片文件夹」心智；不知选哪个夹 | 首访卡在导入前 | 分享者 | HP-GAP-10 · §6.13.1 |
| **P-HELP-02** | 多次导入：新建 vs 覆盖预期不清 | 不敢再导 / 怕覆盖 | 双 persona | HP-GAP-11 · §6.13.2 |
| **P-HELP-03** | 看完示例不知下一步 | 试用不转化 | 分享者 | HP-GAP-13 · §6.13.3 |
| **P-HELP-04** | 进预览后不知「验货即可走」 | 误开精修或空转 | 分享者 | 精修 persona |
| **P-HELP-05** | 保存/退出语义并存，无一张对照 | 以为「完成」=更新版面，或改了就能导出最新 | 编辑者 | P-REF + **REFUX V1.1** |
| **P-HELP-06** | 长图成功后发群指引不稳定/不醒目 | 落盘 ≠ 发出 | 分享者 | P-EXP-05 |
| **P-HELP-07** | 引导触点无统一组件与 seen 合同 | 脉冲反复或文案打架 | 双 persona | P-EXP-04 · 工程现状 |
| **P-HELP-08** | 无按需帮助入口 / 不可重播 | 回访找不到「怎么发群」 | 双 persona | P5-H1 |
| **P-HELP-09** | 反馈面过碎（toast + 红点 + Dock + 横幅） | 注意力分散 | 双 persona | P-REF-06 |
| **P-HELP-10** | 小程序轨道若照搬 Studio 选夹引导 | 心智错位（云端/双主权） | 小程序用户 | MINIAPP PRD |

### 1.4 核心判断

> **帮助系统不是新功能面，是主链认知的合同与触达纪律。**  
> 首访成功 = 用户在无人指导下完成「（示例或真实）导入 → 打开预览 → 导出长图 → **理解如何发微信**（口述或点开文件夹）」。  
> 精修教育属于支线，**首次打开精修时**再教，绝不塞进开场 tour；且必须与 **精修 V1.1（模式≠面板）** 同一套用词。

### 1.5 用户分层（沿用 Phase 5 / 精修）

| Persona | 占比（估） | 本 PRD 策略 |
|---------|------------|-------------|
| **分享者** | ~80% | L0 示范 + L1 主链微引导；不提 G1/版式细节 |
| **编辑者** | ~20% | 首次开精修时 L1 保存/退出语义；L2 可查对照表 |
| **回访用户** | — | 默认静默；「?」可重播；stale / pending 走既有拦截文案 |

---

## 2. 目标与非目标

### 2.1 产品目标

| ID | 目标 | 衡量方式 |
|----|------|----------|
| **G-HELP-01** | 新用户能**自助发现**主操作：开始制作 / 信任行「照片留在本机」/ 预览「长图」 | 5 人可用性；代理：主 CTA 可见 + 首次预览不误把精修当必经 |
| **G-HELP-02** | 无人工指导下走通主链，并**知道如何发微信** | UX-HELP-01；埋点：`longshot_export_success` + `help_publish_guide_show`（辅）+ 可选 `help_funnel_reveal_folder` |
| **G-HELP-03** | 导入前「文件夹」门槛可自助越过 | AC-HELP-01 |
| **G-HELP-04** | 首访预览只教「验货 + 长图」，不教精修 | AC-HELP-04/05；脉冲/引导不指向精修 |
| **G-HELP-05** | 长图成功后用户知道下一步怎么发微信 | AC-HELP-06；与 AC-EXP-11 对齐 |
| **G-HELP-06** | 首次进精修能理解：改字即时 · 改精选要更新版面 · **「完成」≠「更新版面」** | AC-HELP-07 / AC-HELP-14 |
| **G-HELP-07** | 回访可通过「?」重播引导或打开帮助抽屉 | AC-HELP-09～10；兑现 P5-H1 |
| **G-HELP-08** | 引导漏斗可观测 | §7 事件齐全 |

### 2.2 非目标

| 类别 | 非目标 |
|------|--------|
| **全站 Tour** | 不做 shepherd/driver.js 式强制多步导览；不做不可跳过遮罩连环 |
| **文档站** | 不做完整 WORKSHOP wiki 内嵌；帮助抽屉最多 **5 个任务型条目**（可链外链文档） |
| **精修 / 导出能力** | 不改三区 IA、不改模式/面板状态机、不改拦截逻辑、不改长图算法（属相邻 PRD） |
| **小程序 onboarding** | **本 V1 仅覆盖本地 Studio**；小程序隐私 / 双主权选图另立 PRD（见 §11 OQ-HELP-03） |
| **账号 / 云同步** | 不引入登录才能看帮助 |
| **一键发到微信** | 本机 Studio 无系统级分享 API 承诺；只做文案 + 打开文件夹 |
| **多语言** | V1 仅简体中文 |
| **AI 对话客服** | 不做 |

### 2.3 成功指标（建议）

| 指标 | 目标（种子期） | 备注 |
|------|----------------|------|
| UX-HELP-01（启动→长图成功并口述发群） | ≥4/5 无协助 | **W1 主门禁** |
| 埋点辅指标：success → publishGuide 曝光 | 趋势向上；样本小时不设硬阈值 | 本地遥测样本小 |
| 点「在文件夹中显示」率（可选） | 观测即可 | 强完成代理 |
| 首次预览后误点精修率 | 下降趋势 | 不设硬阈值 |
| L1 dismiss 后 7 日内同 key 再出现率 | =0（除非重播） | — |
| 帮助抽屉找到目标条目 ≤2 次点击 | ≥4/5 | UX-HELP-02 |

---

## 3. 体验合同

### 3.1 三层架构

```text
L0  空态 / 示范 / 信任行     → 建立「这是什么、产出长什么样」
L1  情境 Hint / 脉冲（W1）· Coachmark（可选 W2） → 首次到达关键节点教一步
L2  按需帮助抽屉（?）         → 回访、出错、进精修后自己打开；非首访强推
```

| 层 | 何时出现 | 用户可否永久关闭 | 与主链关系 |
|----|----------|------------------|------------|
| **L0** | 空态 / 仅有 demo / 信任区常驻 | 不可「关闭产品说明」，但无模态打断 | 主链前置 |
| **L1** | 触发条件满足且 `seen` 未置位，且非忙碌态 | 「知道了」/点目标 CTA / Esc = 本 key 永久 seen；「?」可重播 | 主链微引导 |
| **L2** | 用户主动点「?」或情境「了解更多」 | 抽屉关闭即回到原页 | 救援 / 回访 |

### 3.2 首访主链（唯一强路径）

```text
启动 Studio
  → L0 首页（示例 + 开始制作 + 文件夹支架）
  → 导入 / 等待（忙碌态 · 无 L1）
  → FirstSuccess（方案 A：主 CTA 打开预览 · 副文案验货→长图 · 次按钮保存长图）
  → 预览验货
  → L1 长图脉冲 + 可见 tip + aria（只打长图 · D-HELP-03′）
  → 导出成功
  → Task Dock publishGuide / 客户端兜底三要素（发群 · 每次必现）
```

**FirstSuccess（D-HELP-10 · 方案 A · 已拍板）**

| 项 | 规格 |
|----|------|
| **主 CTA** | **打开卷轴预览**（验货主路径；含 `quick_share` 模式） |
| **次按钮** | **保存长图**（显式跳过验货的快捷；可选展示） |
| **副文案** | 「当前为本机文案；先翻一翻验货。满意就点预览页下方的『长图』；需要杂志感可在「更多工具」升级。」· 与主 CTA **同卡可视区**（非脚注灰字）· **Stable-QH v1.1 supersede** |
| **倒计时自动进预览** | 若产品启用：副文案曝光 **≥2s** 后再跳；现网若倒计时禁用，则 **首次进预览 500ms 内** 必须出现 T-PREVIEW-LONGSHOT 可见 tip 承接同一叙事 |
| **禁止** | 主 CTA 再写成「保存长图」而把打开预览降为唯一主路径（即禁止回到方案 B，除非另立修订） |

**叙事接力（FirstSuccess → 预览）**

| 情况 | 要求 |
|------|------|
| 用户点主 CTA 进预览 | FirstSuccess 副文案已展示即可；进预览后若 L1 未 seen，仍可出长图 tip |
| 用户点次按钮「保存长图」 | 记埋点 `help_funnel_skip_preview`（可选）；成功态仍须 publishGuide / 兜底 |
| 倒计时自动进预览 | 见上表 ≥2s；禁用倒计时时靠 500ms tip 接力 |

**点击预算（分享者 · 理想路径）**

| 阶段 | 用户主动决策次数（上限） |
|------|--------------------------|
| 首页到开始导入 | ≤2（开始制作 → 选文件夹；支架为可选展开） |
| FirstSuccess → 预览 | ≤1（或倒计时自动） |
| 预览 → 长图 | ≤1（点「长图」；dismiss tip 不计入导出） |
| 成功 → 理解发群 | 0（阅读指引）或 1（在文件夹中显示） |

### 3.3 文案合同（对外口径锁死）

| 概念 | 用户可见用词 | 禁止 |
|------|--------------|------|
| 主导出动作 | **长图** | 首访主按钮不要写「导出长图」（高级/无障碍可用完整说法） |
| 成功态 | **长图已保存** + 发群下一步 | 「Job 完成」「capture ok」 |
| 版式生效 | **更新版面** | 「应用排版」「rerender」 |
| 拦截续跑 | **更新并导出** | 「仍导出旧版」 |
| 退出精修模式 | **完成** | 与「更新版面」混用或做成同一按钮 |
| 精修进行中 | **精修中**（chip） | 首访把精修说成必经步骤 |
| 精修侧栏 Tab | **这页 / 这本 / 导出** | 「导出与更多」 |
| 整本备注 | **给这本游记的一句话** | 「写给编辑的一句话」 |
| 首页偏好 | **导入偏好**（下次怎么导入） | 与预览「精修」混称「设置」而不加限定 |
| 预览编辑 | **精修**（改这一本） | 首访引导文案把精修说成必经 |
| 信任 | **照片留在本机 · 无需注册** | 夸大云能力 |

### 3.4 保存 / 退出语义对照（固定文案 · L1/L2 共用）

| 用户动作 | 何时生效 | 导出是否用到 |
|----------|----------|--------------|
| 点字改文案 | **马上**在预览看到 | 是（当前预览） |
| 改精选 / 拼图 / 版式相关 | 需点 **更新版面** | 仅更新后 |
| 点 **长图** | 导出当前已更新结果 | — |
| 点 **精修** | 进入精修模式（可收起面板继续改） | — |
| Esc / × / 再点「精修」（面板开时） | **只关面板**，模式可仍为 on | — |
| 点 **完成** | **退出精修模式**（★ 隐藏） | **不是**更新版面 |

> H2、精修首次 hint（T-REFINE-SAVE）必须引用同一张表（禁止两处说法不一致）。

### 3.5 视觉与打断纪律

| 规则 | 要求 |
|------|------|
| **同时只亮一个 L1** | 同一时刻最多一个 L1 表面；优先级见 §4.4 |
| **忙碌态零 L1（D-HELP-08′）** | 统一门禁 `isHelpL1Blocked()`：导入 Job / `layoutUpdating` / 长图导出进行中为 true 时 **不**展示长图脉冲 / tip / coach；进度只走既有进度 UI。**idle 后**可再评估：若全局未见过长图引导，允许补发脉冲+可见 tip（一次逻辑周期内仍只打扰一轮）。**例外澄清（非例外放行 L1）**：Importing 壳内 [Wait Tips](./PRD-WAIT-TIPS-V1.md) 为进度次内容、非 L1，见 v1.1.3 脚注 |
| **不与 Modal 叠乘** | 导出拦截 Modal 打开时，不弹 L1 |
| **不新增第四类反馈面** | 优先写入 Task Dock / 既有 hint / 脉冲槽；禁止为帮助再发明平行 toast 体系 |
| **Coachmark 结构**（若使用） | 标题 ≤8 字 · 正文 ≤1 句 · 主按钮「知道了」· 可选「了解更多」→ L2 |
| **脉冲 + 可见 tip（D-HELP-03′）** | 归属 L1「长图」；与 `previewLongshotSeen` / 全局 `exportPulseSeen` **同一逻辑周期**；**首访必须**有一次性可见 tip + 合同 `aria-label`；**禁止「仅 aria」过验收**；不叠独立 coach |
| **帮助 vs 精修面板** | 见 §5.3；二者不得同时抢焦点；开帮助关面板时 chip/「完成」保留 |

### 3.6 `seen` 作用域（冻结 · D-HELP-07′）

| 类型 | 作用域 | 说明 |
|------|--------|------|
| 主链 L1（长图引导、精修保存 hint、平台切换等） | **全局技能** | 学一次即可；**门禁键不含 tripId** |
| `exportPulseSeen` 历史 per-trip | **只读兼容** | 读时可识别旧 per-trip 键，但 **不再作门禁**；写入只双写全局键（见 §6.2） |
| `publishGuide` / 发群指引 | **按需查阅**（H4 /「?」）；**默认成功面不强制**（2026-07-17 · First-Session Trust） | 不纳入「只出现一次」；亦不作默认成功面拒收条件 |
| 分析用展开等 | 可选 | 如 `help.importFolderExpanded`，不影响打扰 |

---

## 4. 触达矩阵（L0 / L1）

### 4.1 决策摘要

| 优先级 | 触点 ID | 层 | 教什么 | 形态 |
|--------|---------|----|--------|------|
| **P0** | T-IMPORT-FOLDER | L0/L1 | 选哪个照片文件夹 | Import 区折叠支架 |
| **P0** | T-IMPORT-NEW | L0 | 每个文件夹 = 一篇新游记 | 回访态一句 |
| **P0** | T-SUCCESS-NEXT | L1 | 先打开预览验货；满意再点长图 | FirstSuccess 副文案 + 预览接力 |
| **P0** | T-PREVIEW-LONGSHOT | L1 | 点下方「长图」即可保存 | **脉冲 + 可见 tip + aria**（D-HELP-03′）；不叠独立气泡 |
| **P0** | T-EXPORT-SHARE | L1 | 已保存确认；发群操作说明按需 | 默认成功面：已保存 + 打开文件夹（[First-Session Trust](./PRD-FIRST-SESSION-TRUST-V1.md)）；`publishGuide` / 三要素 → **Help H4 按需** |
| **P1** | T-REFINE-SAVE | L1 | 改字即时；改精选要更新版面；完成≠更新版面 | 首次打开精修 Sheet 顶 hint |
| **P1** | T-DEMO-CONVERT | L0 | 试用后用自己的照片 | 示例区 CTA |
| **P2** | T-PLATFORM-PICK | L1 | 朋友圈/小红书会切多张；失败可改回微信群 | Longshot 2.0 平台选择器首次 |
| **P2** | T-LAYOUT-PENDING | L1 | 「仅更新」后仍要点长图 | 导出门面已覆盖；文案可链到 H3 |

### 4.2 触点规格

#### T-IMPORT-FOLDER · 照片准备引导（P0）

| 项 | 规格 |
|----|------|
| **触发** | 首页空态或打开 Import Sheet/Wizard；回访新建时可见 |
| **默认** | 折叠：「不知道选哪个文件夹？」 |
| **展开内容** | ① 同一次旅行放同一文件夹（50–100 张最佳）② Day1/Day2 子夹：合并或分两次导入（每次一篇**新**游记）③ 支持 JPG/PNG/WebP/HEIC；**不移动不修改**原片 ④ 手机照片需先传到电脑 |
| **seen** | 不强制；展开行为可不记，或记 `help.importFolderExpanded` 仅分析用 |
| **实现归属** | 兑现 [PRD-STUDIO-HOMEPAGE.md](./PRD-STUDIO-HOMEPAGE.md) §6.13.1（若 v2 首页未落地则在 Import Wizard 等价位置落地） |
| **AC** | AC-HELP-01 |

#### T-IMPORT-NEW · 多次导入预期（P0）

| 项 | 规格 |
|----|------|
| **触发** | 回访态导入区常驻一句；选夹后 Toast |
| **文案** | 「每个文件夹会生成一篇**新的**游记，不会覆盖已有游记」；Toast：「将新建一篇游记 · 已选择 N 张」 |
| **例外** | 同一 tripId / 示例再次导入 → 既有覆盖 Modal（不属本 PRD 新造） |
| **AC** | AC-HELP-02 |

#### T-DEMO-CONVERT · 试用回流（P1）

| 项 | 规格 |
|----|------|
| **触发** | 仅有示例 trip，或 `demoTried` 且尚无用户 trip |
| **UI** | 示例区下方：`试试用自己的照片做一篇 →`（锚到主导入 CTA） |
| **禁止** | 全屏拦截弹窗 |
| **AC** | AC-HELP-03 |

#### T-SUCCESS-NEXT · FirstSuccess 下一步（P0）

| 项 | 规格 |
|----|------|
| **触发** | 导入成功展示 FirstSuccess |
| **主 CTA（D-HELP-10 · 方案 A）** | **打开卷轴预览**（含现网 `quick_share` 模式须改回此主 CTA） |
| **次按钮** | **保存长图**（显式跳过验货的快捷；次级样式） |
| **副文案（合同）** | 「当前为本机文案；先翻一翻验货。满意就点预览页下方的『长图』；需要杂志感可在「更多工具」升级。」· 与主 CTA **同卡可视区**（Stable-QH v1.1） |
| **自动跳转** | 见 §3.2（启用倒计时则 ≥2s；禁用则进预览 500ms 内 tip 接力） |
| **禁止** | 主 CTA 写成「保存长图」；成功屏强推精修；多平台选择进成功屏 |
| **AC** | AC-HELP-04 · AC-HELP-04a |

#### T-PREVIEW-LONGSHOT · 首访长图引导（P0）

| 项 | 规格 |
|----|------|
| **触发** | 用户**第一次**进入预览（任意 trip）且**全局** `previewLongshotSeen` / `exportPulseSeen` 未置位；且 `!isHelpL1Blocked()` |
| **内容合同** | 「验货没问题就点『长图』，生成可发微信的长图」 |
| **形态（D-HELP-03′ · 冻结）** | **保留** Dock「长图」脉冲；**必须**一次性**可见 tip**（同类：精修 tip）+ 合同句写入长图 `aria-label`；**W1 不**叠独立 coach 气泡；**禁止仅 aria 过验收** |
| **指向** | **仅** Dock「长图」；**禁止**指向精修 |
| **置 seen** | Esc /「知道了」/ 用户直接点「长图」/ 脉冲周期结束；写 seen 时**双写**全局 `previewLongshotSeen` 与全局 `exportPulseSeen`（见 §6.2） |
| **作用域** | **全局技能**（D-HELP-07′）；per-trip 旧键不参与门禁 |
| **AC** | AC-HELP-05 · AC-HELP-05a · AC-HELP-13 · AC-HELP-13a |

#### T-EXPORT-SHARE · 发群指引（P0）

| 项 | 规格 |
|----|------|
| **触发** | 长图导出 **success**（含分段 / 平台模式） |
| **载体** | Task Dock 成功态主文案槽；**不得**仅依赖易消失 toast |
| **内容优先级** | ① backend / 配置 `publishGuide` 非空 → **优先展示** ② 否则客户端兜底（D-HELP-09） |
| **默认微信群客户端兜底（三要素 · 冻结 COPY）** | ① 「长图已保存到本机」② 「打开微信，按文件名顺序发到群聊」③ 「可点『在文件夹中显示』找到文件」 |
| **内容最低集** | 上列三要素齐全；「在文件夹中显示」控件可用 |
| **平台差异** | Longshot 2.0 非默认平台：优先后端 `publishGuide`；空时可用平台专用兜底或回退三要素 +「页脚有发送顺序」一句 |
| **AC** | AC-HELP-06 · AC-HELP-06a |

#### T-REFINE-SAVE · 精修保存 / 退出语义（P1）

| 项 | 规格 |
|----|------|
| **触发** | 用户**第一次**打开精修 Sheet（`help.refineSaveSeen` 未置位） |
| **内容（两行）** | ① 「改字马上生效；改精选请先点下方『更新版面』」② 「『完成』只是退出精修，不是更新版面」 |
| **了解更多** | → 抽屉 H2（完整对照表 §3.4） |
| **禁止** | 四 Tab 逐个介绍；开场 tour；与 V1.1 Dock 文案冲突 |
| **AC** | AC-HELP-07 · AC-HELP-14 |

#### T-PLATFORM-PICK · 平台选择（P2）

| 项 | 规格 |
|----|------|
| **触发** | 用户首次将平台从默认微信群切到朋友圈 / 小红书等 |
| **内容** | 「会按平台切成多张；页脚有顺序。失败可改回微信群长图」 |
| **前置** | [PRD-LONGSHOT-2.0.md](./PRD-LONGSHOT-2.0.md) 平台选择器已可用 |
| **AC** | AC-HELP-08 |

### 4.3 情境反链（L1/Modal → L2）

| 表面 | 链到条目 |
|------|----------|
| 文件夹折叠支架底部 | H1 |
| 精修首次 hint | H2 |
| 导出拦截 Modal 次要说明 | H3 |
| 「长图待更新」/ stale 说明 | H3 |
| 长图成功态次链 | H4 |
| 通用错误（导入失败等）可选 | H5 |

### 4.4 同时触发时的优先级

```text
忙碌态进度 UI（非 coach，但独占 · D-HELP-08）
  > 导出拦截 Modal（非 coach，但独占）
  > T-EXPORT-SHARE（成功态）
  > T-PREVIEW-LONGSHOT
  > T-REFINE-SAVE
  > T-PLATFORM-PICK
  > G1 横幅（既有 · 非本 PRD coach）
```

FirstSuccess 与预览 L1 **不会同屏**（页面切换）；若自动跳转，靠 §3.2 接力。

---

## 5. 帮助抽屉（L2）

### 5.1 入口

| 入口 | 位置 | 要求 |
|------|------|------|
| **主入口** | 首页与预览顶栏/Chrome **「?」** 常驻（兑现 P5-H1 · **W2**） | `aria-label="使用帮助"`；幽灵图标；**不进** Task Dock；不与金色「长图」并排抢主 |
| **页脚** | 若首页有 footer：「使用帮助」同开抽屉 | 与 v2.2 页脚设想对齐时可合并 |
| **重播** | 抽屉底部：「重新显示操作提示」 | 清除 §6.2 可重播 keys（含长图 + 精修保存）并关闭抽屉；**不**自动连环弹出。关闭后文案：「已重置。下次进入预览会再提示如何保存长图；再次打开精修时会再看到保存说明。」 |
| **情境反链** | §4.3 | 打开并滚动/高亮目标条目 |

### 5.2 信息架构（仅 5 条 · 任务型）

| ID | 标题（用户可见） | 正文要点 | 可选媒体 |
|----|------------------|----------|----------|
| **H1** | 怎么选照片文件夹 | 同 §4 T-IMPORT-FOLDER 四条 | 可选 1 张文件夹结构示意 |
| **H2** | 「完成」和「更新版面」有什么区别 | §3.4 全表（含完成≠更新版面）；短标题便于扫读 | 极简示意图 |
| **H3** | 「长图待更新」/ 更新版面是什么意思 | pending → 更新版面 → 再点长图；与拦截 Modal 人话一致 | — |
| **H4** | 怎么把长图发到微信群 | 打开文件夹 → 按序发送；分段/多平台时跟 `publishGuide` | 可选 2～3 步静态图 |
| **H5** | 出错了怎么办 | **决策树（固定三行）**：① 导入失败 → 换文件夹重试 / 新建一篇 ② 导出失败 → 再点「长图」；仍失败见日志/重开 Studio ③ 提示要更新版面 → 先「更新版面」再导出 · 原片不被改 | — |

**禁止**：按工程模块（Pipeline / G1 / CLIP）组织目录；超过 5 条一级条目。

### 5.3 交互规格

| 项 | 规格 |
|----|------|
| **形态** | 右侧或底部 Sheet/Drawer（跟现有 studio-modal / sheet 体系）；遮罩可点关闭 |
| **宽度** | 桌面 ≤400px；**不得挡住 Dock「长图」命中区**（预览页优先从右侧滑出） |
| **与精修 Sheet 冲突（冻结 · MF-HELP-06）** | ① 精修面板开着时点「?」→ **先关精修面板（保 `refine` 模式）** 再开帮助 ② 关闭面板后 **chip「精修中」与 Dock「完成」必须仍在**；**不**因开帮助清 pending ③ 帮助打开时 **禁止**再开精修 Sheet ④ Esc：若帮助开着则先关帮助 |
| **焦点** | 打开陷阱焦点；Esc 关闭；关闭后焦点回「?」 |
| **空网** | 纯前端文案；不依赖外网（外链文档可「在浏览器打开」） |
| **搜索** | V1 **不做** |

---

## 6. 组件与持久化

### 6.1 最小组件合同

| 组件 | 用途 | 必须支持 |
|------|------|----------|
| **Pulse + Tip**（W1） | T-PREVIEW-LONGSHOT · D-HELP-03′ | 脉冲 · **必现**一次性可见 tip · 合同 `aria-label` · `prefers-reduced-motion` 时静态高亮/描边 |
| **InlineHint** | Sheet 顶 / 折叠支架 | 可关闭（写 seen）· 了解更多 |
| **Coachmark** | 可选（W2+ 或确需箭头指向时） | 定位箭头 · 标题/正文 · 知道了 · 了解更多 · Esc |
| **HelpDrawer** | L2（W2） | 条目列表 · 深链 `?help=H2` 或 hash · 重播 |
| **PublishGuideSlot** | Task Dock 成功态 | 展示 `publishGuide`；空则客户端三要素兜底（D-HELP-09） |

> V1 允许先用现有 DOM/CSS 拼装，但 **seen key 与文案 ID 必须按本文**，避免第三次重构合同时再拆。  
> **W1 不强制新造 Coach 组件**（见 §9）。

### 6.2 localStorage 键（建议命名空间）

前缀：`travelogue.studio.help.`

| Key | 含义 | 重播时清除 |
|-----|------|------------|
| `previewLongshotSeen` | T-PREVIEW-LONGSHOT 已展示或已跳过（**全局**） | 是 |
| `refineSaveSeen` | T-REFINE-SAVE 已展示 | 是（重播文案须明示） |
| `platformPickSeen` | T-PLATFORM-PICK 已展示 | 是 |
| `exportPulseSeen`（全局） | 与 `previewLongshotSeen` **同一逻辑周期**；写时双写；**门禁只读此全局键** | 是（与 preview 双清） |
| `exportPulseSeen:<tripId>`（legacy） | 历史 per-trip；**只读兼容，不作门禁** | 重播时可顺带清，非必须 |
| `demoTried` | 已有/可沿用；试用回流条件 | 否 |

**迁移（W0 · D-HELP-07′）**

1. 读门禁：仅 `previewLongshotSeen` ∨ 全局 `exportPulseSeen`。  
2. 若仅发现 legacy per-trip seen：视为「已学过」→ **双写全局**后不再打扰（零重复脉冲）。  
3. 写 seen：始终双写全局两键；**不再写**新的 per-trip 门禁键。  
4. 重播：清全局两键 + `refineSaveSeen`（及合同所列可重播键）。

**禁止**：用 cookie；禁止按 tripId 永久压制「发群指引」；禁止主链 L1 **门禁**使用 per-trip seen。

### 6.3 决策（本文冻结）

| ID | 决策 | 说明 |
|----|------|------|
| **D-HELP-01** | 不做全站 tour | 见铁律 1 |
| **D-HELP-02** | 帮助抽屉固定 5 条任务 | 见 §5.2 |
| **D-HELP-03** | 长图首访案 A：脉冲保留；不叠独立 coach | **已拍板**；禁止双打扰 |
| **D-HELP-03′** | 首访 = 脉冲 + **可见 tip** + aria；禁止仅 aria 过验收 | **v1.1.1 拍板** |
| **D-HELP-04** | 发群指引每次成功必现 | 不纳入「只出现一次」 |
| **D-HELP-05** | Studio V1 不含小程序 onboarding | 见非目标 |
| **D-HELP-06** | 精修教育仅 P1 · 首次开 Sheet | 不进 FirstSuccess |
| **D-HELP-07** | 主链 L1 seen = **全局技能** | 见 §3.6 |
| **D-HELP-07′** | 门禁仅全局；per-trip 只读兼容；双写/重播双清 | **v1.1.1 拍板** |
| **D-HELP-08** | 忙碌态零 L1 | 见铁律 6 · §3.5 |
| **D-HELP-08′** | `isHelpL1Blocked()`；idle 后可补评估脉冲 | **v1.1.1 拍板** |
| **D-HELP-09** | 默认微信群：`publishGuide` 空时客户端三要素兜底 | **v1.1.1 拍板** · **v1.1.2 收窄**：兜底必显范围 = **Help H4 /「?」按需**，非默认 Task Dock 成功面 |
| **D-HELP-10** | FirstSuccess **方案 A**：主 CTA=打开卷轴预览；保存长图为次按钮 | **v1.1.1 拍板**；关闭 OQ-HELP-01 |

---

## 7. 埋点

> 若项目尚无统一 analytics，允许先 `console` / 本地事件环；字段名按下表预留。

### 7.1 组件事件

| 事件 | 触发 | 属性 |
|------|------|------|
| `help_coach_show` | L1 tip/coach 展示 | `touchpoint`, `tripId?` |
| `help_coach_dismiss` | 知道了 / Esc / 点击目标 CTA | `touchpoint`, `reason` |
| `help_drawer_open` | 打开抽屉 | `source`（`icon` / `footer` / `deep_link` / `replay`） |
| `help_drawer_item` | 点击条目 | `itemId`（H1–H5） |
| `help_publish_guide_show` | 成功态展示 publishGuide | `platform?`, `segmented?` |
| `help_demo_convert_click` | 试用回流 CTA | — |

### 7.2 漏斗事件（建议 · 可复用既有）

| 事件 | 触发 | 用途 |
|------|------|------|
| `help_funnel_preview_open` | 首访进入预览 | 掉队观测 |
| `help_funnel_longshot_click` | 点 Dock「长图」 | 是否找到导出 |
| `help_funnel_reveal_folder` | 成功态点「在文件夹中显示」 | **强完成代理** |
| `help_funnel_skip_preview` | FirstSuccess 点次按钮「保存长图」 | 观测跳过验货比例 |

与导出门面衔接：主链完成率 ≈ `longshot_export_success` + `help_publish_guide_show`（辅以 reveal_folder）。

---

## 8. 非功能

| 类别 | 要求 |
|------|------|
| **A11Y** | Tip / Drawer 角色与焦点陷阱；「?」有 accessible name；长图合同句进 `aria-label`；不唯色彩传达 |
| **动效** | 尊重 `prefers-reduced-motion`；脉冲可改为静态高亮 |
| **性能** | 帮助文案内联或静态 JSON；不得阻塞导入 Job |
| **兼容** | Chrome / Edge 90+（与 Studio 一致） |
| **隐私** | 引导状态仅存本机；不上传帮助行为到第三方（除非产品另立遥测 PRD） |
| **文案变更** | 用户可见字符串集中常量文件，须与精修 V1.1 / 导出门面同一合同 |

---

## 9. 里程碑与 Go/No-Go

### 9.1 波次

| 波次 | 范围 | 依赖 | Go 标准 |
|------|------|------|---------|
| **W0 · 合同对齐** | 文案对拍（含 V1.1）；FirstSuccess 方案 A 现网改点清单；`exportPulseSeen` 全局门禁+双写迁移；默认群聊三要素兜底 COPY；`isHelpL1Blocked` 定义 | 导出门面 V1 · 精修 V1.1 · **本 PRD v1.1.1** | 手测：`publishGuide` 空时仍见三要素；抽检无违禁旧词；迁移后零重复脉冲方案书面冻结 |
| **W1 · P0 主链** | T-IMPORT-FOLDER · T-IMPORT-NEW · T-SUCCESS-NEXT（方案 A）· T-PREVIEW-LONGSHOT（**脉冲+可见 tip**）· T-EXPORT-SHARE（兜底） | W0 · **F1–F3/F7 线框** | AC-HELP-01～06、04a/05a/06a、11～13、13a；**UX-HELP-01 ≥4/5** |
| **W2 · L2 + P1** | HelpDrawer +「?」· T-REFINE-SAVE · T-DEMO-CONVERT · 情境反链 · 面板冲突（chip/完成保留）· 重播文案 | W1 · F4–F6/F8 | AC-HELP-07/09/10/14/15/16/17 |
| **W3 · P2** | T-PLATFORM-PICK · 漏斗周报 · 可选用性复测 | Longshot 2.0 平台 UI | AC-HELP-08 · G-HELP-08 |

### 9.2 No-Go

| 条件 | 处理 |
|------|------|
| W1 引入强制多步 tour | **拒收** |
| W1 首访引导指向精修 | **拒收** |
| W1 脉冲 + 独立 coach **双打扰** | **拒收**（违反 D-HELP-03） |
| W1 首访长图 **仅 aria、无可见 tip** | **拒收**（违反 D-HELP-03′） |
| 成功态无**已保存确认**且无打开文件夹入口 | **拒收**（对齐 First-Session Trust；2026-07-17 起不再以「无发群教学句」拒收） |
| Help H4 被删除且无任何发群说明入口 | **拒收**（按需救援须可达） |
| FirstSuccess 主 CTA 仍为「保存长图」且未改主链 | **拒收**（违反 D-HELP-10） |
| 帮助抽屉一级条目 >5 或改成工程目录 | **拒收** |
| 帮助文案与精修 V1.1「完成 / 更新版面」冲突 | **拒收** |

---

## 10. 验收标准（AC）

| ID | 场景 | 期望 |
|----|------|------|
| **AC-HELP-01** | 空态/Import 可见「不知道选哪个文件夹？」并展开 | 四条要点齐全；不调 API |
| **AC-HELP-02** | 回访新建 | 可见「新的游记 / 不覆盖」句；选夹 Toast 含「将新建」 |
| **AC-HELP-03** | 仅有示例 trip | 可见试用回流 CTA，点击落到主导入 |
| **AC-HELP-04** | FirstSuccess | 副文案含验货 +『长图』且与主 CTA **同卡可视区**；无精修强推；自动跳转满足 §3.2 接力 |
| **AC-HELP-04a** | FirstSuccess CTA | **主 CTA=「打开卷轴预览」**；「保存长图」仅为次按钮（D-HELP-10） |
| **AC-HELP-05** | 首次进预览 | 长图引导只出现一轮；不指向精修；Dismiss 或导出后不再出现；无第二层独立 coach 气泡 |
| **AC-HELP-05a** | 首访长图 tip | **可见 tip 必现**（非仅 aria）；合同句同时进 `aria-label`（D-HELP-03′） |
| **AC-HELP-06** | 长图 success | Task Dock 展示**已保存**确认；「在文件夹中显示」为主操作可用（First-Session Trust）；发群教学句**非**必现 |
| **AC-HELP-06a** | 用户打开帮助 H4 /「?」 | 仍可达发群说明（`publishGuide` 或三要素兜底）；**不**要求默认成功面强制展示 |
| **AC-HELP-07** | 首次打开精修 | 见两行语义 hint（含完成≠更新版面）；「了解更多」打开 H2 |
| **AC-HELP-08** | 首次切换非默认平台 | 见平台切张说明（W3） |
| **AC-HELP-09** | 点击「?」 | 打开 5 条目抽屉；Esc 关闭；焦点可回 |
| **AC-HELP-10** | 「重新显示操作提示」 | 清除可重播 keys；文案明示长图引导 **与** 精修保存 hint；再次进预览可再见到长图引导 |
| **AC-HELP-11** | 导出拦截 Modal 打开时 | 不叠加长图 L1 |
| **AC-HELP-12** | 文案抽检 | §3.3 用词无回归（含禁止「导出与更多」「写给编辑的一句话」「应用排版」） |
| **AC-HELP-13** | 忙碌态（导出中 / 更新版面中 / 导入 Job） | `isHelpL1Blocked()` 为 true 时不出现长图首次 L1 打扰 |
| **AC-HELP-13a** | 忙碌→idle | 若全局未见过长图引导，idle 后可补评估一轮脉冲+tip（仍只打扰一轮） |
| **AC-HELP-14** | 精修 hint / H2 | 明确「完成 ≠ 更新版面」 |
| **AC-HELP-15** | 精修面板与帮助抽屉 | 不同时抢焦点；符合 §5.3 冲突规则 |
| **AC-HELP-16** | 开帮助关精修面板 | 模式仍为 on；chip「精修中」与 Dock「完成」仍在；pending 不清 |
| **AC-HELP-17** | seen 迁移 | 仅有 legacy per-trip seen 的用户：双写全局后 **不**再出现重复脉冲 |

**可用性（建议门禁）**

| ID | 任务 | 通过 |
|----|------|------|
| **UX-HELP-01** | 从未用过的用户：从启动到长图成功并口述如何发群 | ≥4/5 无协助 · **W1 Go 主标准** |
| **UX-HELP-02** | 回访用户：只通过「?」找到「发到微信群」条目 | ≥4/5 |

---

## 11. 风险与开放问题

### 11.1 风险

| 风险 | 缓解 |
|------|------|
| 引导过多导致验货被打断 | 铁律 + 优先级栈 + 忙碌态零 L1 + 同时只亮一个 L1 |
| 与导出门面 / 精修 V1.1 文案再次分叉 | §3.3～3.4 为唯一合同；COPY 变更走同一常量 |
| `exportPulseSeen` 历史用户状态 | D-HELP-07′：legacy per-trip 只读兼容；双写全局后不重复打扰 |
| 忙碌态误弹脉冲 | D-HELP-08′：`isHelpL1Blocked` + idle 补评估 |
| FirstSuccess 跳过验货 | D-HELP-10 方案 A：主 CTA 回预览；次按钮可观测 |
| 帮助抽屉做成文档堆 | 硬限制 5 条；外链进 WORKSHOP |
| 帮助与精修双 Sheet 抢焦点 | §5.3 冲突规则 · AC-15/16 |
| 小程序照搬 | D-HELP-05；OQ-HELP-03 |

### 11.2 开放问题

| ID | 问题 | 状态 / 默认 |
|----|------|-------------|
| **OQ-HELP-01** | FirstSuccess 主 CTA 是否改「保存长图」为唯一主路径 | **已关闭 · D-HELP-10 方案 A**（主 CTA=打开预览；保存长图=次按钮） |
| **OQ-HELP-02** | Coach 用自研还是轻量库 | **自研 DOM**；W1 默认不用 Coach；禁止引入重型 tour 库 |
| **OQ-HELP-03** | 小程序帮助系统何时立项 | **Studio W2 完成后再立** `PRD-MINIAPP-HELP-V1` |
| **OQ-HELP-04** | 帮助媒体（GIF）是否进包 | **W1 纯文案**；W2 可选静态 PNG ≤3 张 |
| **OQ-HELP-05** | 是否要「永不显示提示」总开关 | **V1 不做**；重播足够；避免误关后无法发现长图 |
| **OQ-HELP-06** | 桌面可安装版首启是否另立帮助 | **默认复用本文**；若安装器首启路径显著不同，在 [PRD-DESKTOP-INSTALLER-V1](./PRD-DESKTOP-INSTALLER-V1.md) 增补一节，不平行造 tour |

---

## 12. 附录

### 12.1 与既有 PRD 条款映射

| 既有条款 | 本文承接 |
|----------|----------|
| 首页 §6.13.1～6.13.3 | T-IMPORT-FOLDER / T-IMPORT-NEW / T-DEMO-CONVERT |
| Phase 5 P5-H1 | §5 帮助抽屉 + 重播 |
| 精修 V1 保存语义 / 命名 | §3.3～3.4 · T-REFINE-SAVE · H2/H3 |
| **精修可用性 V1.1** | §3.3～3.4「完成/精修中」· AC-14 · 前置条件 |
| 导出门面 G-EXP-05 / publishGuide | T-EXPORT-SHARE · D-HELP-04 · D-HELP-09 |
| Longshot 2.0 publishGuide / 平台 | T-EXPORT-SHARE · T-PLATFORM-PICK |
| M21「Coach 非 M21」 | 本文正式立项，**不阻塞** M21 路由 |
| 评审纪要 2026-07-14 | MF-HELP-01～08 → v1.1.1 冻结决策 |
| **Desktop LLM Setup V1** | §12.4 · H7 · T-CAP-01 · D-DLLM-13 |

### 12.2 首访触达一览（实施用）

```text
[首页 L0]
  信任行 · 示例 · 开始制作
  └─ 折叠：不知道选哪个文件夹？     → H1
  └─（条件）试用回流 CTA

[导入 · 忙碌态]
  Toast：将新建一篇游记 · 无 L1（isHelpL1Blocked）

[FirstSuccess · 方案 A]
  主 CTA：打开卷轴预览
  次按钮：保存长图
  副文案：验货 → 点『长图』（同卡可视区）
  └─ 进预览 → tip 接力（倒计时禁用时 ≤500ms）

[预览 L1]
  长图脉冲 + 可见 tip + aria（一次 · D-HELP-03′） → 禁止指向精修
  └─ 成功：Task Dock publishGuide / 三要素兜底 → H4
  └─（条件）开精修：保存/退出语义 hint → H2

[全局 L2 · W2]
  ? → H1 … H5 · 重播（长图 + 精修保存）
  └─ 开帮助：关面板保模式 · chip/完成保留
  └─（相邻主题扩展）H6 封面封底 · H7 AI 文案 · 见 §12.4
```

### 12.3 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0.0 | 2026-07-11 | 首版 Draft：三层架构 · 触达矩阵 · 帮助抽屉 · 与精修/导出门面合同对齐 |
| **v1.1.0** | **2026-07-14** | 专家审视回写：精修 V1.1 语义；D-HELP-03/07/08 冻结；忙碌态；帮助↔精修冲突；叙事接力；W1 不强制 Coach；漏斗埋点；AC-13～15；H5 决策树 |
| **v1.1.1** | **2026-07-14** | 评审 Must-Fix 回写：D-HELP-03′/07′/08′/09/10；FirstSuccess 方案 A；可见 tip；seen 迁移；发群兜底；AC-04a/05a/06a/13a/16/17；关闭 OQ-HELP-01；Conditional Go 可开 W0 |
| **v1.1.2** | **2026-07-17** | DOC-FST-03：发群三要素改按需查阅；默认成功面对齐 First-Session Trust；AC-HELP-06/06a 修订 |
| **v1.1.2** | **2026-07-15** | 交叉引用 Desktop LLM Setup：§12.4 H7 / T-CAP-01 / D-DLLM-13（不改主链 H1–H5） |
| **v1.1.3** | **2026-07-17** | DOC-WT BLK-01：D-HELP-08′ 脚注 — Importing Wait Tips 为进度次内容、非 L1 |
| **v1.1.4** | **2026-07-17** | DOC-WT-12：帮助抽屉「重播等待提示」= 按需非 L1 |

### 12.4 相邻主题 · Desktop LLM Setup（H7 / 能力卡）

> 权威合同（工程 / dark）：[PRD-DESKTOP-LLM-SETUP-V1.md](./PRD-DESKTOP-LLM-SETUP-V1.md)。  
> **默认用户面 supersede**：[PRD-NO-AI-SURFACE-V1.md](./PRD-NO-AI-SURFACE-V1.md)（NAS · DOC-NAS-02）— **H7 / 能力卡首启硬推 / 重播唤醒 AI 入口**在默认门控 off 时**不生效**；dark（`TRAVELOGUE_AI_SURFACE=1`）可恢复设置与 narrate，**仍不恢复能力卡**（D-NAS-20）。本节历史表仅作工程索引。

| 触点 / 条目 | 说明 | 与本文关系 |
|-------------|------|------------|
| **T-CAP-01** 首页能力卡 | **默认面：永久不 show**（NAS FE-NAS-01）。工程残留见 DLLM；dark 亦不恢复 | **L0 认知补丁**已由 NAS 休眠；busy 同 D-HELP-08 |
| **H7**「要不要配置 AI 文案」 | **默认面：条目删除/隐藏**（NAS FE-NAS-04 / AC-NAS-03） | 支线救援仅 dark / AI-Return |
| **D-DLLM-13** | 能力卡 vs 首页非关键 Help L1 仲裁 | 默认面无卡；仲裁退化为 Help 既有门禁 |
| seen | `travelogue.desktop.capabilityCard.v1` | **默认面重播不得清能力卡 / stub seen**（NAS M9 / AC-NAS-16） |

**铁律对齐**：配置非门槛；缺 Key 不得表现为整次生成失败；忙碌态零配置打扰；**当前发版默认面零 AI 岔路**（NAS）。

---

## 13. 审核清单（跨职能评审用）

> 评审纪要：[help-onboarding-v1-review-2026-07-14.md](./acceptance-records/help-onboarding-v1-review-2026-07-14.md) · **Conditional Go · MF 已回写 v1.1.1**

- [x] 同意 **六条铁律**（含忙碌态零 L1）  
- [x] 同意 **D-HELP-03 / 03′**（脉冲 + 可见 tip；不叠独立 coach）  
- [x] 同意 **D-HELP-07 / 07′**（L1 门禁 = 全局技能；per-trip 只读兼容）  
- [x] 同意 **D-HELP-08 / 08′**（`isHelpL1Blocked`；idle 可补评估）  
- [x] 同意 **D-HELP-09**（默认群聊三要素兜底）  
- [x] 同意 **D-HELP-10 方案 A**（FirstSuccess 主 CTA=打开预览）  
- [x] 同意 §3.4 含「完成 ≠ 更新版面」且与精修 V1.1 一致  
- [x] 同意 §5.3 帮助与精修面板冲突规则（chip/完成保留）  
- [x] 同意 W0→W1 波次；W1 主门禁 = UX-HELP-01；W1 前 F1–F3/F7  
- [x] 同意非目标：无全站 tour、无文档站、不含小程序  

**建议结论**：☑ **Conditional Go**（MF 已回写 · 可开 W0）　☐ 修订后再评　☐ No-Go  

**确认人 / 日期**：产品 / 2026-07-14（v1.1.1 回写）
