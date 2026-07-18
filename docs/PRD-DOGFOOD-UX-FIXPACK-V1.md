# Travelogue · 狗粮修复包 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | **v0.2** |
| **状态** | **有条件通过（Conditional Go）** · 评审 Must-Fix 已回写 · 可开 IMPLEMENTATION / M1 |
| **主题代号** | 「狗粮修复包 V1（Dogfood UX Fixpack）」— 导出链路修复 · 命名一致性 · 移动端门面 · FTUE 收尾 |
| **调研来源** | 2026-07-18 五角色狗粮手测（Studio v2 首页 · `demo-album` / `demo-eb9a45b3c4` · Playwright + 人工走查） |
| **评审纪要** | [acceptance-records/dogfood-ux-fixpack-v1-review-2026-07-18.md](./acceptance-records/dogfood-ux-fixpack-v1-review-2026-07-18.md) |
| **关联文档** | [PRD-PREVIEW-EXPORT-FACADE-V1.md](./PRD-PREVIEW-EXPORT-FACADE-V1.md) · [PRD-OUTPUT-RECIPE-V1.md](./PRD-OUTPUT-RECIPE-V1.md) · [PRD-PREVIEW-REFINE-UX-V1.1.md](./PRD-PREVIEW-REFINE-UX-V1.1.md) · [PRD-M14-shelf-save-longshot.md](./PRD-M14-shelf-save-longshot.md) · [PRD-HELP-ONBOARDING-V1.md](./PRD-HELP-ONBOARDING-V1.md) · [PRD-STUDIO-HOMEPAGE-v2.2-OPTIMIZATION.md](./PRD-STUDIO-HOMEPAGE-v2.2-OPTIMIZATION.md) · [acceptance-records/tpc-local-dogfood-GUIDE.md](./acceptance-records/tpc-local-dogfood-GUIDE.md) |
| **验收** | 本文 §9；落地后补 `ACCEPTANCE-DOGFOOD-UX-FIXPACK-V1.md` |
| **实施清单** | [IMPLEMENTATION-DOGFOOD-UX-FIXPACK-V1.md](./IMPLEMENTATION-DOGFOOD-UX-FIXPACK-V1.md) |
| **更新日期** | 2026-07-18 |

> **定位**
>
> 2026-07-18 五角色狗粮手测确认：主链路骨架成立，但暴露 **2 个 P0 功能缺陷、4 个 P1 一致性/门面缺陷、一批 P2 打磨项**。
>
> 本 PRD 是一次**修复包（Fixpack）**，不引入新功能面：
>
> 1. **导出链路修好** — 单屏海报选择必须生效；导出设置弹层在小窗口可完成操作。
> 2. **改名改彻底** — 用户改名后所有展示面跟随；保留 `displayTitle` 防噪投影职责。
> 3. **移动端门面不丢人** — 拦截页无破图；无小程序能力时不假装有二维码。
> 4. **FTUE / 反馈收尾** — 按钮名实相符、操作有回音、内部编号不外漏。

> **v0.2 评审回写摘要（2026-07-18 Conditional Go）**
>
> - D1：平台确认写入**输出域 prefs / Recipe**，**禁止**误用叙事 `PATCH …/intent`；服务端 `resolve_output_recipe` 复核  
> - D2：用户改名 → `title` SSOT + 同步 `displayTitle`；读取保留 `resolve_display_title()`；存量迁移仅清「改名旧缓存」  
> - D3：采纳 sticky + 内滚；补焦点 / Esc / `<560px` Sheet  
> - D4：能力开关控制二维码；无小程序则删位  
> - D5：M14 稳定成功态为主，Toast 为辅  
> - D6：job 级一次定格式；海报固定 PNG  
> - R4.1：**冻结**为真实发起默认微信群长图导出  
> - R5.1：**Park**（独立 layout 议题）  
> - MF-01～10 已回写进 §0 / §4 / §9

---

## 0. 评审导读与已拍板决策

### 0.1 D1–D6（已拍板 · 2026-07-18）

| 决策 | 拍板结论 |
|------|----------|
| **D1 海报导出通路** | 「确定」后写入**已确认输出偏好**（prefs / session resume / 可选 `trip.output`）；同步改写主按钮文案与 aria；主按钮按已确认 `platform` 提交。服务端以 `resolve_output_recipe` + `POST /longshot` 的 `platform`/`intent` **复核**。**禁止**用叙事 `PATCH /trips/{id}/intent` 存平台。`gcs_poster_bric=false` 时 UI 隐藏且 API 拒绝。 |
| **D2 displayTitle** | 用户显式改名：`meta.title` = 编辑 SSOT，并**同步写入同值** `meta.displayTitle`。读取端继续走 `resolve_display_title()`（防噪 / 地点·日期回退）。存量惰性迁移**仅**当检测到「用户改名后展示面仍残留旧 displayTitle」；**禁止**把目录噪声 `title` 反灌进展示面。预览热刷新可内存对齐；**落盘发生在用户保存路径**。 |
| **D3 弹层适配** | `max-height: calc(100vh - 顶栏 - 16px)` + 内容区滚动 + 底部操作条 sticky。视口高 `<560px` → 全屏 Sheet。须具备焦点陷阱、Esc 关闭、背景滚动锁定。 |
| **D4 移动拦截页** | 修复二维码资源；`onerror` 降级。**无小程序能力（配置/资源不可用）时删除二维码位**，仅保留诚实文案 + 「复制电脑打开地址」。 |
| **D5 导出成功反馈** | **稳定成功态**（Task Dock / 主按钮 done / 书架「分享图已就绪」）为权威；非阻断 toast（约 8s）叠加即时提示 + 「在文件夹中显示」/「已保存到此游记文件夹」。Toast 不独担成功终点。 |
| **D6 输出格式** | 同一次 export job 内扩展名与编码参数一致；job **启动前**决定 format（或首段触发容量策略后清理并整批重跑）。海报 `poster_bric` **固定 PNG**，不被「默认 JPG」覆盖。失败/取消不留混合半成品。 |

### 0.2 确认态状态机（MF-02 · D1）

| 状态 | 含义 | UI |
|------|------|-----|
| **drafting** | 弹层打开，用户改选未点确定 | 卡片高亮 = draft；主按钮仍显示**上一已确认**平台 |
| **confirmed** | 点「确定」成功写入 prefs | 主按钮文案/aria/设置入口摘要 = 已确认平台；draft 清空 |
| **cancelled** | 点「取消」或 Esc | 丢弃 draft；prefs 与主按钮不变 |
| **exporting** | 主按钮提交中 | loading；失败时**不切换**已确认平台 |
| **succeeded / failed** | 任务结束 | 见 D5；失败可重试，平台保持 confirmed |

**铁律**：CTA 可见文案 · 设置入口「当前将导出」摘要 · `POST /longshot` payload · 三者同读 **confirmed platform**（非 draft）。

### 0.3 标题迁移合同（MF-03 · D2）

| 场景 | 行为 |
|------|------|
| 用户在封面/「这本」改杂志名并保存 | 写 `meta.title` + `meta.displayTitle`（同值）；触发覆盖面重渲染 |
| 纯预览加载（未保存） | 内存对齐展示；**不**静默改 trip.json |
| 存量 trip 打开后用户保存 | 若 `displayTitle` 与用户已编辑的 `title` 不一致且 `title` 通过非噪声验收 → 落盘同步并记 `decision_log` |
| 首次导入 / 文件夹噪声 | 继续 `resolve_display_title()` / humanize；**不**因本包迁移破坏防噪 |

### 0.4 R4.1 冻结（MF-04）

FTUE 完成弹窗次按钮「保存长图」：**真实发起**默认微信群长图导出（跳转预览页并展示导出进度 / 成功态）。禁止仅改文案却仍链到预览 URL。

### 0.5 与 V1.1 精修状态机

#7（精修「关闭 ×」不退出模式）为 [PRD-PREVIEW-REFINE-UX-V1.1](./PRD-PREVIEW-REFINE-UX-V1.1.md) **已拍板设计**。本包仅核对 MF-04 tip 文案是否含「点『完成』退出精修」（P-DFX-12），不改状态机。

---

## 1. 背景与证据

### 1.1 手测环境

- Windows · Chrome（Playwright + 人工）· Studio 8766  
- 视口：1280×800、1272×675、390×844  
- 样本：`demo-album`、`demo-eb9a45b3c4`（手测改名「贵州+兴义暑假游」→「黔西南三日漫游」）  
- 截图：`.cache/ux-test/`

### 1.2 角色摘要

| Persona | 关键发现 |
|---------|----------|
| **纯小白** | FTUE 可走通；先 409 再弹「已在书架」；「保存长图」名不副实 |
| **普通旅行者** | 改名传播不彻底；「一句话」零反馈 |
| **分享达人** | 长图成功；**海报选择不生效**；矮窗「确定」不可点；导出无回音 |
| **设计爱好者** | 常驻提示碍眼；章节间隙无信息帧（→ Park） |
| **手机端用户** | 拦截页破图；手机封面巨字旧名；toast 过大 |

---

## 2. 问题陈述（P-DFX-*）

| ID | 问题 | 严重度 | 证据 |
|----|------|--------|------|
| **P-DFX-01** | 选「单屏海报」确定后仍导出 `wechat_chat` / `chat_longshot` | **P0** | job `job-ae1f90d3c61e`；CTA 文案未变 |
| **P-DFX-02** | 导出弹层不可滚，「确定」在视口外 | **P0** | 675px 高；Playwright outside viewport |
| **P-DFX-03** | 改名后 `displayTitle`/辑封/`<title>`/alt 残留旧名 | **P1** | trip.json 双字段分叉 |
| **P-DFX-04** | 移动拦截页小程序二维码破图 | **P1** | 390px `/` |
| **P-DFX-05** | 手机封面巨字用旧 displayTitle | **P1** | P-DFX-03 下游 |
| **P-DFX-06** | 「保存长图」与「打开预览」同 URL | **P1** | `first-success.js` 双链同 `url` |
| **P-DFX-07** | 导出成功无稳定反馈 | **P1** | job succeeded UI 静默 |
| **P-DFX-08** | 示例入口先 409/400 再弹窗 | **P2** | console 先于 dialog |
| **P-DFX-09** | 同任务 `ch01.png` + `ch02.jpg` 混格式 | **P2** | 按章容量回退中途切格式 |
| **P-DFX-10** | 「一句话」保存无反馈 | **P2** | 精修「这本」 |
| **P-DFX-11** | 版式差异提示常驻遮挡 | **P2** | 桌面预览 |
| **P-DFX-12** | 精修关闭≠退出（设计如此）消歧不足 | **P2** | 跟进 tip 文案 |
| **P-DFX-13** | 帮助「H1 ·」编号外漏 | **P2** | 帮助抽屉 |
| **P-DFX-14** | 手机「预览需更新」toast 过大 | **P2** | 390px |
| **P-DFX-15** | 章节间隙无信息帧 | **P2** | **Park** → 独立 layout |
| **P-DFX-16** | 首页书架折线下 / 信息过载 | **P3** | 移交 Homepage v2.x |

---

## 3. 目标与非目标

### 3.1 产品目标

1. **导出所选即所得**：确认什么平台，就导出什么；任何视口能完成「选择 → 确定 → 导出」。  
2. **用户改名零残留**：改名保存后，约定展示面 3s 内无旧杂志名。  
3. **操作有回音**：保存/导出成功失败均可感知，成功态可回看。  
4. **门面诚实**：无破图、无假小程序、无内部编号。

### 3.2 非目标

- 不新增导出平台；不改 V1.1 精修状态机。  
- 不做移动端完整只读模式。  
- 不动首页 IA（P-DFX-16）。  
- 不碰 TPC / mosaic / BRIC 选片 / cover scoring。  
- **不做 R5.1**（Park）。

### 3.3 成功指标

| 指标 | 现状 | 目标 |
|------|------|------|
| 海报导出 platform 正确率 | 0% | 100% |
| 675px 导出设置可完成率 | 0% | 100% |
| 改名后残留旧杂志名的约定展示面 | ≥5 | 0 |
| 导出成功 5s 内可见稳定成功态或 toast | 无 | 100% |

---

## 4. 需求详述

### WS1 · 导出链路修复（P0）

#### R1.1 平台选择贯通（P-DFX-01 · MF-01/02/05）

- 「确定」→ `writeExportPrefs({ platform })` + `syncLongshotCtaLabel` +（可选）session resume；**不**调用叙事 intent PATCH。  
- 主按钮导出：`platform` / `intent` 从 **confirmed prefs** 组装；`poster_bric` → 后端 BRIC 旁路（已有 `export_poster_bric_pack`）。  
- 服务端：`resolve_output_recipe` 复核；`gcs_poster_bric` off 时 4xx；导出前后对规范化 `screens[]` 指纹断言不变。  
- 前端 fail-closed：`selectedConfirmed !== payload.platform` → 阻止提交 + `export_platform_mismatch`。  
- 设置入口展示「当前将导出：{platformLabel}」。  
- 契约冻结：`platform=poster_bric`，`intent=poster_bric`，产物 `*-poster.png` + `runs/gcs-poster-bric.json`（或现有 sidecar 路径），与 unit 测试对齐。

#### R1.2 弹层视口适配（P-DFX-02 · MF-07）

- max-height + 内滚 + sticky 确定/取消。  
- `<560px`：全屏 Sheet；焦点陷阱、Esc、背景锁。  
- Playwright：1272×675、1280×800、`<560` 三档；断言确定可点且 prefs 写入成功。

#### R1.3 导出成功反馈（P-DFX-07 · MF-06）

- 任务 succeeded：刷新主按钮 done / Task Dock / 书架徽标（M14）；叠加 toast「已导出 N 张 · {label}」+ 「在文件夹中显示」（文案可附「已保存到此游记文件夹」）。  
- failed：原因 + 重试；平台保持 confirmed。  
- toast 与 Dock 层级互斥：有 Dock 成功区时 toast 可缩短为 4s 或不重复主句。

#### R1.4 输出格式统一（P-DFX-09 · MF-09）

- job 启动前定 `outputFormat`；容量策略触发则清理临时产物并以 JPEG **整批重跑**。  
- 海报固定 PNG。  
- 失败/取消不留混扩展名最终产物。

### WS2 · 命名一致性（P1）

#### R2.1 用户标题 SSOT（P-DFX-03/05 · MF-03）

- 保存改名：同写 `title` + `displayTitle`；重渲染覆盖：封面主/副标题、辑封、`<title>`、`og:title`、alt 前缀、`index-mobile` 巨字、`index-present`、`index-longshot` 文案层。  
- **不**触发 cover asset / style / scoring 重选。  
- 副标题：`{subtitle 或 一句话} · {日期范围}`；禁止把旧标题拼进副标题。  
- 迁移：见 §0.3；记 `decision_log`；幂等。

#### R2.2 「一句话」反馈（P-DFX-10）

- 失焦/回车保存（IME 组合态下回车不提交）；✓ 1.5s + 「将显示在封面副标题与辑封」；热刷新可见。

### WS3 · 移动端与提示（P1/P2）

#### R3.1 拦截页（P-DFX-04 · MF-08）

- 修资源；能力开关；无能力删二维码位；`onerror` 降级；正常路径必须可加载（禁止「永远降级」假绿）。

#### R3.2 手机 toast 减负（P-DFX-14）

- `<768px`：「预览需更新」高度 ≤48px + safe-area；可关；主操作「更新版面」保留。

#### R3.3 版式差异提示（P-DFX-11）

- 进入预览 5s 淡出；每 trip 一次；localStorage 键**版本化**；帮助内保留说明。

### WS4 · FTUE 收尾（P1/P2）

#### R4.1 保存长图名实相符（P-DFX-06 · §0.4）

- 次按钮点击：导航至预览并**触发**默认 `wechat_chat` 导出（或等价 query/session 续跑），展示进度与成功态。

#### R4.2 示例入口时序（P-DFX-08）

- 先本地判重 → 弹「已在书架」→ 用户选「重新生成」再 `/import`；消除 409。排查 `studio-event` 400。

#### R4.3 帮助去编号（P-DFX-13）

- 可见标题无「H1 ·」；遥测保留 data-attribute。

#### R4.4 精修 tip 核对（P-DFX-12）

- 核对 V1.1 MF-04 tip；可补「点『完成』退出精修」半句。

### WS5 · Park

#### R5.1（P-DFX-15）

不实施。跟踪项：独立 layout PRD；禁止全局 sticky / 盲目压缩间隙。

---

## 5. 交互与文案规格

| 场景 | 规格 |
|------|------|
| 主按钮（confirmed 后） | 微信群：「按章导出长图 · 发微信群」；朋友圈长图：「导出长图 · 发朋友圈」；小红书：「导出 3:4 配图 · 发小红书」；九宫格：「导出九宫格 · 发朋友圈」；单屏海报：「导出单屏海报」 |
| 设置入口摘要 | 「当前将导出：{platformLabel}」 |
| 成功 toast | 「已导出 N 张 · {label}」+ 「在文件夹中显示」 |
| 一句话 | ✓ + 「已保存 · 将显示在封面副标题与辑封」 |
| 移动拦截（无小程序） | 「请用电脑打开制作」+ 当前宽度说明 + 「复制电脑打开地址」 |
| 版式差异 tip | 「手机封面版式与电脑不同，以手机效果为准 · 详见帮助」· 5s |

文案总则：无内部词；按钮动词=动作；提示可关或限时；无能力不假装。

---

## 6. 技术实现要点

| 工作流 | 疑似落点 | 备注 |
|--------|----------|------|
| WS1 平台贯通 | `templates/studio/preview-toolbar/longshot.js`（`_applyDraft` / `resolveExportPlatform` / start export）· `output-recipe.js` · `export_handlers.py` · `poster_bric_pack.py` | 摸底：draft→prefs→CTA→POST 断在何处；poster 是否未进映射表 |
| WS1 弹层 | 预览工具栏 CSS + popover DOM | sticky / Sheet |
| WS1 格式 | `travelogue/export/longshot.py` 按章容量回退 | job 级 format |
| WS2 命名 | `save-copy` · `title_humanize.resolve_display_title` · `render/context` · visual-journal 模板 | 保存同写；迁移判定 |
| WS3 | Studio 首页拦截模板 · 静态资源 | QR 能力开关 |
| WS4 | `homepage-v2/first-success.js` · import 入口 | 次按钮真导出；先判重 |
| QA | Node 映射 · pytest 海报合同 · Playwright e2e | flag 隔离 · `_free_port` |

---

## 7. 里程碑

| 里程碑 | 范围 | 出口 |
|--------|------|------|
| **M1（P0 止血）** | R1.1 · R1.2 | AC-DFX-01～04 + Sheet 分支；跨层四断言；可独立合入 |
| **M2（一致性）** | R2.1 · R2.2 · R1.3 · R1.4 | AC-DFX-05～09 |
| **M3（门面）** | R3.* · R4.* | AC-DFX-10～14；R5.1 不进出口 |

---

## 8. 遥测

- `export_platform_mismatch`（期望 0）  
- `export_ok_toast_shown` / `export_open_folder_clicked`  
- `rename_propagation_migrated`  
- `mobile_gate_qr_error`（期望趋 0）  
- 复用 `studio-event`，不新增采集面  

---

## 9. 验收标准（AC-DFX-*）

| ID | 标准 | 验证 |
|----|------|------|
| **AC-DFX-01** | 选海报→确定→主按钮导出：`platform/intent=poster_bric`；`*-poster.png` + sidecar；`screens[]` 指纹不变 | Playwright + job + 文件 + pytest |
| **AC-DFX-02** | 确认后 CTA 文案/aria + 设置摘要即时更新；覆盖全部平台映射 | Playwright / Node |
| **AC-DFX-03** | 1272×675 与 `<560px` Sheet 下确定可点，prefs 写入成功并完成导出 | Playwright |
| **AC-DFX-04** | `gcs_poster_bric=false`：卡片不展示且 API 拒绝；默认 off 不回归 | pytest + Playwright（隔离配置） |
| **AC-DFX-05** | 用户改名保存后：封面主副/辑封/`<title>`/alt/mobile 巨字/present/longshot 文案层均为新名；cover asset/style/`screens[]` 不变 | Playwright + trip.json + 指纹 |
| **AC-DFX-06** | 存量迁移：仅符合 §0.3 条件时在**保存**路径落盘；预览不静默写盘；decision_log 幂等 | pytest |
| **AC-DFX-07** | 「一句话」IME 安全保存 + ✓ + 展示位热刷新 | Playwright |
| **AC-DFX-08** | 成功：稳定成功态 + toast/reveal；失败：原因+重试 | Playwright（mock job） |
| **AC-DFX-09** | 同 jobId 最终产物扩展名唯一；编码匹配扩展名；取消无半成品 | pytest |
| **AC-DFX-10** | 390px：QR 正常可加载 **或** 能力关时无图无破图；404 降级 | Playwright 双路径 |
| **AC-DFX-11** | `<768` 预览需更新条 height≤48 可关 | Playwright |
| **AC-DFX-12** | 版式 tip 5s 淡出、每 trip 一次、键版本化 | Playwright（可注入计时） |
| **AC-DFX-13** | 「保存长图」触发真实默认长图导出；示例入口无 409/400 **失败请求** | Playwright + 网络断言 |
| **AC-DFX-14** | 帮助可见标题无「H1 ·」前缀 | DOM |
| ~~AC-DFX-15~~ | （原 R5.1）**取消本包验收** · Park | — |

**M1 门禁（MF-10）**：须同时验证 payload · job · 产物 · `screens[]`；禁止仅检查按钮文案。测试用临时 trips_dir / 自由端口 / 显式 flag，不依赖本机 8766。

---

## 10. 风险与开放问题

| # | 项 | 状态 |
|---|-----|------|
| 1 | 与 Facade 主 CTA 职责 | **关闭**：本包只修断链，不改门面结构；海报仍走 ▾ 确认后的主按钮执行 |
| 2 | displayTitle 防噪被破坏 | **关闭**：§0.3 合同 |
| 3 | `/longshot` 与 poster 共用 | **关闭**：沿用现有 `platform=poster_bric` 旁路 |
| 4 | 迁移落盘时机 | **关闭**：保存落盘 / 预览内存 |
| 5 | R5.1 | **Park** |
| 6 | 中文 IME 误提交 | 实施时测；进 AC-07 |

---

## 11. 变更记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-07-18 | 初稿 · P-DFX-01～16 · D1–D6 草案 |
| v0.2 | 2026-07-18 | 评审回写 · D1–D6 拍板 · MF-01～10 · R4.1 冻结 · R5.1 Park · AC 修订 · 链到 IMPLEMENTATION |
