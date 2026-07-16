# Travelogue · 新用户首次成功路径优化 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio（本机 Studio / 桌面打包同等体验） |
| **文档版本** | **v1.1.0** |
| **状态** | **Conditional Go · Must-Fix 已回写** · 可 Kickoff **W0**（见 [评审纪要](./acceptance-records/ftue-optimization-v1-review-2026-07-15.md)） |
| **主题代号** | 「首访成稿」— 空态不迷路 · 示例可一键 · 长图知发群 · 冷启动可解释 |
| **触发来源** | 2026-07-15 空态 FTUE dogfood；跨职能评审 Conditional Go |
| **前置条件** | Studio 首页 v2（M21）；能力卡 / L0 分层；帮助系统 V1 · 导出门面 V1 合同有效 |
| **关联文档** | [PRD-HELP-ONBOARDING-V1.md](./PRD-HELP-ONBOARDING-V1.md) · [PRD-PREVIEW-EXPORT-FACADE-V1.md](./PRD-PREVIEW-EXPORT-FACADE-V1.md) · [PRD-DESKTOP-LLM-SETUP-V1.md](./PRD-DESKTOP-LLM-SETUP-V1.md) · [PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1.md](./PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1.md) · [PRD-DESKTOP-INSTALLER-V1.md](./PRD-DESKTOP-INSTALLER-V1.md) · [PRD-STUDIO-HOMEPAGE-v2.md](./PRD-STUDIO-HOMEPAGE-v2.md) · [PRD-UX-TRUST-V1.md](./PRD-UX-TRUST-V1.md) · [PRD-COPY-OPTIMIZATION.md](./PRD-COPY-OPTIMIZATION.md) · [SHARING.md](./SHARING.md) · [WORKSHOP.md](./WORKSHOP.md) · [README.md](../README.md) |
| **评审记录** | [acceptance-records/ftue-optimization-v1-review-2026-07-15.md](./acceptance-records/ftue-optimization-v1-review-2026-07-15.md) |
| **线框** | [wireframes/ftue-optimization-v1-wireframe.html](./wireframes/ftue-optimization-v1-wireframe.html) · F1–F8（W0 挡门：F1–F3/F7；W1 挡门：F4–F6） |
| **验收** | 本文 §10；可后续拆 `ACCEPTANCE-FTUE-OPTIMIZATION-V1.md` |
| **实施清单** | [IMPLEMENTATION-FTUE-OPTIMIZATION-V1.md](./IMPLEMENTATION-FTUE-OPTIMIZATION-V1.md) |
| **更新日期** | 2026-07-15 |

> **定位**
>
> 帮助系统 V1、导出门面 V1、Desktop L0 已分别定义「教什么」「导出怎么闭环」「无 Key 怎么活」。  
> **本 PRD 不扩算法 / 精修 / 安装包能力**，只把 **2026-07-15 空态首访实测** 中仍会卡住新用户的断裂点，收成可实施的优化合同。
>
> **一句话目标**：干净机（或等价空书架）用户在 **不配 API、不读 docs/** 的前提下，能在一次会话内完成  
> **看见价值 → 安全试一次 → 验货 → 长图 → 知道怎么发微信**，且过程中不出现「像坏了」的灰按钮、沉默下载、乱码文件名。
>
> **完成定义（BLK-11）**
>
> | 门 | 含义 | 不等于 |
> |----|------|--------|
> | **W0 Go** | 敢试：空态不灰、向导可一键示例、文件名可读、README 三步 | 主题「首访成稿」未完成 |
> | **W1 Go** | 敢发：长图成功面必出 + 发群三要素 + 冷启动可解释 + 系统句不进封面 | 才算主题主链过门 |
>
> **产品共识（五条铁律）**
>
> 1. **空态像新产品，不像坏掉的老产品** — 无作品时禁止灰掉的「继续上次」等回访 CTA（含 disabled DOM）。  
> 2. **最安全的第一次成功必须在产品内** — 「试用示例相册」在向导 pick **一等显眼**，不得只藏在 CLI。  
> 3. **落盘 ≠ 完成** — 长图成功必须以「发群主句 + 打开位置」为终点；**复用** Help/Facade，禁止平行成功面栈。  
> 4. **冷启动可解释** — 首次下载视觉组件等，进度面必须说人话。  
> 5. **文件名对资源管理器友好** — 默认 `{tripId}-ch{nn}.png`；中文标题只作显示名。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0.1 | v1.1.0 相对 v1.0.0（Must-Fix 回写） |
| §1 | 实测方法、问题清单（P-FTUE-*） |
| §2 | 目标 / 非目标 / 完成定义 |
| §3 | 体验合同与冻结决策（D-FTUE-*） |
| §4 | 触点与文案矩阵（含覆盖声明） |
| §5 | 工程任务 |
| §6～§8 | 错误 / 埋点 / 非功能 |
| §9 | 里程碑 |
| §10 | 验收 AC |
| §11 | 风险与已关闭 OQ |
| §12 | 评审清单 |
| 附录 | 实测摘要 · Installer 修订 · 版本记录 |

### 0.1 版本回写摘要（v1.1.0 ← 评审 Must-Fix）

| BLK | 回写结论 |
|-----|----------|
| **BLK-01** | §4.2 / D-FTUE-06：**正式覆盖** COPY-L0G-01～04 与 AC-L0G-10 的能力卡 CTA/主句字面；交叉回写见 §4.2.1 |
| **BLK-02** | **定案 B′**：示例 CTA **仅在向导 pick 一等显眼**；首页主 CTA「开始制作」进向导；**修订** Installer F-INS-FIRST-01（附录 C） |
| **BLK-03** | P-FTUE-01 降为 **P2 · 归属 Installer**；G-FTUE-06 标明开发者路径 |
| **BLK-04** | §3.3：成功面 **复用** Task Dock / `resolvePublishGuide`；发群主句第一可读行；禁止新平行栈 |
| **BLK-05** | 发群 COPY **唯一**对齐 Help `publishGuideFallback` / D-HELP-09 |
| **BLK-06** | AC-FTUE-08′：展示窗口或收起后可达路径可验收 |
| **BLK-07** | §3.2 去重：**默认打开已有示例**；次要「重新生成（覆盖）」 |
| **BLK-08** | 示例与选文件夹同屏次主；「其他导入」上传入口改名去「试用」 |
| **BLK-09** | 空态 **不渲染** `#v2-bench-resume` DOM |
| **BLK-10** | 文件名 `{tripId}-ch{nn}.png` + 中文 title 单测 |
| **BLK-11** | W0/W1 完成定义见文首 |
| **BLK-12** | 线框 F1–F8；W0 挡门 F1–F3/F7 |

---

## 1. 背景与问题

### 1.1 实测方法（可复现）

| 项 | 约定 |
|----|------|
| **环境** | Windows · 本机 Studio · Chrome/Edge |
| **空态** | `python -m travelogue studio --trips-dir <空目录> --no-open --port <闲置端口>` |
| **首访** | 清该 origin 的 `localStorage` / `sessionStorage` 后打开首页 |
| **样片** | `templates/studio/assets/demo-album` 或 `useDemoAlbum: true` |
| **trips 优先级** | **`--trips-dir` > `TRAVELOGUE_TRIPS_DIR` > `config.yaml` `trips_dir` > 默认**（W2 已接入 env；空态仍建议显式 `--trips-dir`） |

### 1.2 目标态剧本（To-Be）

```
第一次打开 Studio（空 trips）
  → 能力卡（§4.2 冻结文案 · 主 CTA「开始制作」· 可关）
  → 首页：书架隐藏；**无**「继续上次」控件
  → 点「开始制作」→ 导入向导 pick
       · 主：选择本次旅行的照片文件夹
       · 次主（同屏）：试用示例相册
       · 折叠「其他导入方式」：本机上传小文件夹（文案不含「试用」）
  → 导入进度（组件准备 vs 整理照片 可区分）
  → FirstSuccess（D-HELP-10）→ 打开卷轴预览
  → 首访：仅 Dock「长图」脉冲 + 可见 tip
  → 长图成功（Task Dock 成功面）：
       · 第一可读行：发群三要素（Help 同源）
       · 次要：在文件夹中显示
       · 文件名无乱码；UI 仍显示中文标题
  → （转化）提示可用自己的照片再做一本
```

### 1.3 问题清单（P-FTUE-*）

| ID | 问题 | 严重度 | 波次 | 归属 |
|----|------|--------|------|------|
| **P-FTUE-02** | vision 冷启动静默下模型 | **P0** | W1 | 本主题 |
| **P-FTUE-03** | 长图成功面 / 发群不稳定 | **P0** | W1 | 本主题（兑现 Help/Facade） |
| **P-FTUE-04** | 空态灰「继续上次」 | **P1** | W0 | 本主题 |
| **P-FTUE-05** | 能力卡工程口吻 | **P1** | W0 | 本主题（覆盖 L0G 字面） |
| **P-FTUE-06** | 向导无示例 CTA | **P1** | W0 | 本主题 |
| **P-FTUE-07** | 双长图入口 | **P1** | W1 | 本主题 |
| **P-FTUE-08** | 首访脉冲 tip 未兑现 | **P1** | W1 | 对齐 Help |
| **P-FTUE-09** | 系统句泄漏（+ stub 弱另轨） | **P1** | W1 挡泄漏 / W2 润色 | 本主题 + Copy |
| **P-FTUE-10** | 中文标题 → 文件名乱码 | **P0** | W0 | 本主题 |
| **P-FTUE-01** | 非开发者安装偏 pip | **P2** | DOC 摩擦 | **Installer**（本主题不扛分发） |
| **P-FTUE-11** | README / 依赖说明 | **P2** | W0 | 本主题 DOC |
| **P-FTUE-12/13** | trips 优先级不直观 | **P2** | W0 DOC / W2 loader | 本主题 |

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 | 可观测 |
|----|------|--------|
| **G-FTUE-01** | 空书架首访能理解「做什么 + 点哪」 | AC-FTUE-01～03 |
| **G-FTUE-02** | 不选自有相册也能一键示例成稿 | AC-FTUE-04～05 |
| **G-FTUE-03** | L0 导入可完成且冷启动可解释 | AC-FTUE-06～07 |
| **G-FTUE-04** | 长图成功后知道发群 + 文件位置 | AC-FTUE-08～10 |
| **G-FTUE-05** | 导出文件名无乱码 | AC-FTUE-11 |
| **G-FTUE-06** | **开发者路径** README 三步可启动 | AC-FTUE-12（**非**干净机非开发者成功） |

### 2.2 非目标

| 不做 | 原因 |
|------|------|
| 全站 Product Tour | 帮助系统铁律 1 |
| 官方代付 LLM | Desktop LLM 非目标 |
| 重做精修 / G1 / 排版算法 | 另轨 |
| stub 叙事深度润色 | Copy 另轨；本文只挡系统句泄漏 |
| 完整 Installer / 签名 / Gate | [PRD-DESKTOP-INSTALLER-V1.md](./PRD-DESKTOP-INSTALLER-V1.md) |
| 新造成功面 / toast 平行体系 | BLK-04；复用 Help/Facade |

### 2.3 成功指标（狗粮目标 · 非发布硬 KPI）

| 指标 | 目标 | 样本建议 |
|------|------|----------|
| 空态 → 示例成稿 | ≥ 90% | N≥5 手测 |
| 成稿 → 见发群引导 | ≥ 85% | N≥5（W1） |
| 空态灰回访 CTA | **0** | — |
| 中文 title 文件名乱码 | **0** | 单测 + 手测 |

---

## 3. 体验合同与冻结决策

### 3.1 空态合同

| 条件 | 必须 | 禁止 |
|------|------|------|
| 无用户作品（`trips` 空或仅系统占位） | 隐藏书架；主 CTA「开始制作我的游记」清晰 | **渲染**「继续上次」（含 `disabled`） |
| 空态快捷区 | 「设置」可保留；示例预览可保留 | 回访语义（继续 / 更新长图） |
| 能力卡关闭后 | 首页主 CTA 进向导即可达示例 | 依赖已关卡内第二主按钮 |

### 3.2 示例试用合同（BLK-02 / 07 / 08）

| 项 | 合同 |
|----|------|
| **入口位置** | **仅**导入向导 pick 步；与「选文件夹」**同屏**；视觉为 **次主 CTA**（非折叠内） |
| **首页** | 主 CTA 进向导；**不**并排第二主按钮「试用示例」 |
| **能力卡** | **禁止**第二主钮；正文最多一句「向导里可一键试用示例」 |
| **行为** | `useDemoAlbum: true` → 完整导入 Job → FirstSuccess |
| **文案** | 「用示例照片试一次」 |
| **上传入口** | 「其他导入方式」内改名，例如「上传小文件夹」——**禁止**含「试用」 |
| **已存在 `demo-album`** | 主：「打开已有示例」→ 预览；次：「重新生成（将覆盖）」；**默认打开**（非默认覆盖） |
| **成稿后转化** | FirstSuccess 或成功后轻提示：「下一步可用自己的旅行照片再做一本」（防试完就走） |

### 3.3 长图成功合同（BLK-04 / 05 / 06 · 加严 G-EXP-05）

长图 Job `succeeded` 后：

1. **可见成功面**：复用 Preview V3 **Task Dock** `showSuccess`（或等价既有门面）；**禁止**新建第四套 Modal/toast 体系。  
2. **第一可读行**：发群引导——COPY **唯一**对齐 Help：

   > 已保存。按文件名顺序发到微信群即可。可点「在文件夹中显示」。  

   （与 `HELP_COPY.publishGuideFallback` / D-HELP-09 同源；backend `publishGuide` 非空则优先。）

3. **次要动作**：「在文件夹中显示」/ 打开文件夹——**不得**压过发群主句第一可读行。  
4. **入口矩阵（均须发群句）**：Preview V3 Dock（主）· 书架长图成功路径 · client fallback——统一 `resolvePublishGuide`（或等价）。  
5. **可验收**：成功面可见 ≥ **3s** 或用户主动关闭前保持；若自动收起，须仍能通过「再点长图」或帮助 H4 **找回**发群说明（写入 AC-FTUE-08′）。  
6. 关闭后不要求每次再弹；文件名磁盘为 `tripId`，UI 展示中文 `meta.title`。

### 3.4 双长图入口（D-FTUE-07 · OQ-02 已关闭）

| 入口 | 首访策略 |
|------|----------|
| Dock「长图」 | **唯一**脉冲 + 可见 tip + aria（D-HELP-03′） |
| 文内「保存长图」 | **保留**；降为 tertiary；**不**脉冲、**不** tip |
| FirstSuccess「保存长图」 | 保持 D-HELP-10 次钮；旁路跳过验货；不与预览 tip 争强调 |

### 3.5 冷启动可解释合同

| 必须 | 禁止 |
|------|------|
| 进度区分「整理照片」vs「首次准备本机组件」 | 长时间无文案变更 |
| `stageHint` 枚举见 §5.2 | 下载失败报成相册损坏 |
| L0 / example 默认不重型 vision | 开发机 `vision: true` 当产品默认 |

**`stageHint` 冻结（W1 · 供 AC-FTUE-07）**

| 值（建议） | 用户可见文案 |
|------------|--------------|
| `preparing_vision` | 正在准备本机视觉组件（仅第一次）… |
| `preparing_browser` | 正在准备长图组件（仅第一次）… |
| `processing_photos` / 既有 stage | 正在整理照片… / 既有人话 |

### 3.6 冻结决策（D-FTUE-*）

| ID | 决策 |
|----|------|
| **D-FTUE-01** | 空态 **不渲染**「继续上次」整控件 |
| **D-FTUE-02** | 向导 pick：**试用示例**次主 CTA（W0 Must） |
| **D-FTUE-03** | 长图成功面必出；复用 Task Dock；发群主句优先；入口矩阵对齐 |
| **D-FTUE-04** | L0/example 默认不重型 vision；启用时 stageHint 解释 |
| **D-FTUE-05** | 文件名 `{tripId}-ch{nn}.png`（或单章 `{tripId}.png`） |
| **D-FTUE-06** | 能力卡文案 §4.2；**覆盖** L0G 字面（§4.2.1） |
| **D-FTUE-07** | 首访仅强调 Dock 长图 |
| **D-FTUE-08** | 封面/开篇禁止模板系统句 |
| **D-FTUE-09** | README 三步（开发者路径） |
| **D-FTUE-10** | 文档写明 trips 优先级；空态狗粮用 `--trips-dir` |
| **D-FTUE-11** | 示例入口定案 B′（仅向导）；Installer F-INS-FIRST-01 修订（附录 C） |
| **D-FTUE-12** | 发群 COPY 与 Help 同源；禁止第二套「选图→发送」 |

---

## 4. 触点与文案矩阵

### 4.1 触点总表

| ID | 触点 | 触发 | 文案要点 |
|----|------|------|----------|
| **T-FTUE-CAP** | 能力卡 | 首访 idle | §4.2 |
| **T-FTUE-RESUME** | 继续上次 | 仅有用户作品时渲染 | — |
| **T-FTUE-DEMO** | 向导试用示例 | pick 步同屏次主 | 「用示例照片试一次」 |
| **T-FTUE-DEMO-EXIST** | 示例已存在 | `E_DEMO_EXISTS` 等 | 打开 / 重新生成 |
| **T-FTUE-PROGRESS** | 导入进度 | Job + stageHint | §3.5 |
| **T-FTUE-FIRST** | FirstSuccess | 导入成功 | D-HELP-10 + 转化一句 |
| **T-FTUE-PULSE** | Dock 长图 tip | 首访预览 idle | D-HELP-03′ |
| **T-FTUE-OK** | 长图成功面 | succeeded | §3.3 |
| **T-FTUE-LEAK** | 系统句拦截 | render/narrate | §4.3 |

### 4.2 能力卡文案（冻结 · 唯一字符串）

| 槽位 | **冻结 To-Be（唯一）** |
|------|------------------------|
| 标题 | 照片留在本机，也能做成杂志游记 |
| 正文 | 选一次旅行的照片，自动分章、排版；微信长图可直接发群。更好的文案可稍后自行升级（可选）。向导里可一键试用示例。 |
| **主 CTA** | **开始制作** |
| 次链 | 以后再升级 AI 文案 → |

#### 4.2.1 对相邻合同的覆盖声明（BLK-01）

本表 **正式 supersede**：

| 被覆盖项 | 原字面（摘要） | 新权威 |
|----------|----------------|--------|
| COPY-L0G-01～03 / 能力卡主 CTA | 「开始导入」等 | **本文 §4.2** |
| AC-L0G-10 CTA 字面断言 | 主 CTA=「开始导入」 | 改为断言 **「开始制作」**（回写 L0G ACCEPTANCE 时同步） |
| Help §12.4 / D-DLLM 能力卡主 CTA | 「开始导入」 | 交叉引用改为本文 |

L0G **铁律不变**（无 Key 可成稿、配置是升级）；仅 **用户可见字面** 以本文为准。

### 4.3 系统句拦截

| 禁止进入封面/开篇可见文案 | 处理 |
|---------------------------|------|
| 「备选有限，已选相对最合适的一款」 | 仅内部 feedback / 日志 |
| 「模板已锁定」作杂志正文 | 仅书架 meta |
| 「N 张碎片拼成」 | W1 去掉「碎片」刺耳词（可选）；深度润色 W2 |

---

## 5. 工程任务

### 5.1 前端

| ID | 内容 | 波次 |
|----|------|------|
| **FE-FTUE-01** | 空态不渲染 `#v2-bench-resume` | W0 |
| **FE-FTUE-02** | 向导 pick：试用示例 + 已存在打开/覆盖 UI | W0 |
| **FE-FTUE-03** | 能力卡 §4.2；上传入口去「试用」 | W0 |
| **FE-FTUE-04** | 成功面：入口矩阵复用 `resolvePublishGuide` + showSuccess | W1 |
| **FE-FTUE-05** | 仅 Dock 脉冲 tip；文内降强调 | W1 |
| **FE-FTUE-06** | 进度文案吃 stageHint | W1 |
| **FE-FTUE-07** | 封面无系统句断言 | W1 |
| **FE-FTUE-08** | FirstSuccess / 成功后「用自己的照片」转化句 | W1 |

### 5.2 后端

| ID | 内容 | 波次 |
|----|------|------|
| **BE-FTUE-01** | 长图文件名 tripId；中文 title 单测 | W0 |
| **BE-FTUE-02** | stageHint 枚举 §3.5 | W1 |
| **BE-FTUE-03** | example/bootstrap vision 默认不重型 | W1 |
| **BE-FTUE-04** | trips：CLI > `TRAVELOGUE_TRIPS_DIR` > config；INFO `source=` | W2 |
| **BE-FTUE-05** | templateFeedback 不进 hook | W1 |
| **BE-FTUE-06** | `formatLongshotResult` / 书架路径发群句对齐 | W1 |

### 5.3 文档

| ID | 内容 | 波次 |
|----|------|------|
| **DOC-FTUE-01** | README 三步 + 折叠深链 | W0 |
| **DOC-FTUE-02** | WORKSHOP 可选依赖表 | W0 |
| **DOC-FTUE-03** | 空态狗粮 `--trips-dir` + 优先级 | W0 |
| **DOC-FTUE-04** | Installer F-INS-FIRST-01 修订脚注 | W0 |
| **DOC-FTUE-05** | L0G/Help 交叉引用字面 | W0 |

---

## 6. 错误与边界

| 场景 | 期望 |
|------|------|
| 示例资源缺失 | 人话错误 + 仍可选文件夹 |
| 示例已存在 | §3.2 打开 / 重新生成 |
| 打开文件夹失败 | 成功面展示可复制绝对路径 |
| vision 下载失败 | 降级或明确关闭视觉增强；不伪报相册 |
| 无 Playwright | `E_LNG_PLAYWRIGHT`；成功面不假装已导出 |

---

## 7. 埋点

| 事件 | 说明 | 与现网映射 |
|------|------|------------|
| `ftue_demo_album_click` | 点试用示例 | 可并行 `capability_card_*` 不替代 |
| `ftue_demo_album_success` | 示例导入成功 | — |
| `ftue_reveal_folder` | 打开文件夹 | — |
| 成功面展示 | **优先复用** `longshot_success_share_hint_shown` | 新增 `ftue_longshot_success_surface` 仅当无法复用时 |

不采集密钥、相册绝对路径明文。

---

## 8. 非功能

| 项 | 要求 |
|----|------|
| **A11Y** | 空态移除控件无焦点陷阱；成功面可键盘关；`prefers-reduced-motion` 脉冲改静态 |
| **忙碌态** | 导入中不弹能力卡；tip 在 busy 时不写 seen（对齐 Help） |
| **兼容** | Windows Chrome/Edge 90+ |
| **安全** | 示例走既有 demo ACL |

---

## 9. 里程碑

| 波次 | 范围 | Go 标准 |
|------|------|---------|
| **W0** | D-01/02/05/06/09～11 · FE-01～03 · BE-01 · DOC-01～05 · 线框 F1–F3/F7 | 敢试 · 不灰 · 不乱码 · README 三步 |
| **W1** | D-03/04/07/08/12 · FE-04～08 · BE-02/03/05/06 · 线框 F4–F6 | **敢发** · 冷启动可解释 · 无系统句 |
| **W2** | stub 用词 · BE-04 · Copy 会签 | 不阻塞主题主链签核 |
| **W3** | 与 Installer 便携包手测联调 | 干净机可选签核 |

**Kickoff**：v1.1.0 已回写 → **可开 W0**（估时约 3 人日，见 IMPLEMENTATION）。

---

## 10. 验收（AC-FTUE-*）

### 10.1 空态与首屏

| ID | 断言 |
|----|------|
| **AC-FTUE-01** | 空 `--trips-dir` + 清存储：能力卡可见；书架不可见 |
| **AC-FTUE-02** | DOM **不存在** `#v2-bench-resume`（或等价「继续上次」） |
| **AC-FTUE-03** | 能力卡主 CTA 文本 **精确等于**「开始制作」；标题/正文符合 §4.2 |

### 10.2 示例一键

| ID | 断言 |
|----|------|
| **AC-FTUE-04** | 向导 pick **同屏**可见「用示例照片试一次」（或冻结同义且评审白名单）；**不在**「其他导入」折叠内作为唯一入口 |
| **AC-FTUE-05** | 点击 → Job 成功 → FirstSuccess → 可预览；无需文件夹选择器 |
| **AC-FTUE-05b** | 已存在 demo：默认「打开已有示例」；次要才覆盖 |

### 10.3 冷启动

| ID | 断言 |
|----|------|
| **AC-FTUE-06** | L0 vision 默认关：示例可完成 |
| **AC-FTUE-07** | 需下载组件时：用户可见文案含「组件」或「仅第一次」类 ≥1 次（stageHint） |

### 10.4 长图闭环

| ID | 断言 |
|----|------|
| **AC-FTUE-08** | succeeded 后成功面可见 |
| **AC-FTUE-08′** | 可见 ≥3s **或** 收起后经再点长图/H4 仍可达发群说明 |
| **AC-FTUE-09** | 第一可读行含发群三要素（Help 同源） |
| **AC-FTUE-10** | 可「在文件夹中显示」或可复制路径（次于发群主句） |
| **AC-FTUE-11** | 中文 `meta.title` 时磁盘 png 匹配 `tripId` 模式、无 mojibake |

### 10.5 文档与回归

| ID | 断言 |
|----|------|
| **AC-FTUE-12** | README 首屏 ≤5 步启动（开发者路径）；WORKSHOP 有依赖表 |
| **AC-FTUE-R01** | 有作品时「继续上次」可用 |
| **AC-FTUE-R02** | Help FirstSuccess 方案 A 仍成立 |
| **AC-FTUE-R03** | L0 无 Key 导入不得整单失败 |

---

## 11. 风险与 OQ（已关闭）

| ID | 决议 |
|----|------|
| **OQ-FTUE-01** | **已关闭 · B′**：仅向导一等示例；附录 C 修订 Installer |
| **OQ-FTUE-02** | **已关闭**：文内保存长图保留降强调 |
| **OQ-FTUE-03** | **已关闭**：V1 强制 tripId；无拼音 slug |
| **OQ-FTUE-04** | **已关闭**：改 example/文档；不强制个人 config |
| **OQ-FTUE-05** | **已关闭**：README 三步 + 折叠深链 |

---

## 12. 评审清单（v1.1 自检）

| # | 检查项 | 通过？ |
|---|--------|--------|
| 1 | BLK-01～12 均已回写 | ✅ 本文 |
| 2 | 未重开 Tour / 精修 / Installer 实施 | ✅ |
| 3 | 与 G-EXP-05 / D-HELP-09 / L0 铁律一致 | ✅（字面覆盖已声明） |
| 4 | W0 可独立狗粮 | ✅ |
| 5 | 文件名 tripId 工程可接受 | ✅ |
| 6 | 埋点无 PII；优先复用现网事件 | ✅ |
| 7 | 线框 F1–F3/F7 可供 W0 | ✅ 见 wireframes |

---

## 附录 A · 实测记录摘要（2026-07-15）

| 项 | 结果 |
|----|------|
| 空态书架 | 隐藏 ✅ |
| 继续上次 | disabled 仍可见 ❌ → W0 |
| 示例一键 UI | 无 ❌ → W0 |
| 文件名乱码 | ❌ → W0 |
| 成功面 / 发群 | 未稳定 ❌ → W1 复用对齐 |
| vision 冷启动 | 慢且难解释 ⚠ → W1 |

```powershell
$empty = Join-Path $env:TEMP "travelogue-ftue-trips"
New-Item -ItemType Directory -Force -Path $empty | Out-Null
$env:TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM = "1"
python -m travelogue studio --no-open --host 127.0.0.1 --port 8771 --trips-dir $empty
```

---

## 附录 B · 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v1.1.0** | 2026-07-15 | 消化评审 BLK-01～12；OQ 关闭；线框 + IMPLEMENTATION；可 Kickoff W0 |
| **v1.0.0** | 2026-07-15 | 首稿 Draft；Conditional Go 评审 |

---

## 附录 C · Installer 合同修订（BLK-02 / D-FTUE-11）

**原** [PRD-DESKTOP-INSTALLER-V1.md](./PRD-DESKTOP-INSTALLER-V1.md) **F-INS-FIRST-01**：

> 首启首页可见「试用示例相册」入口

**修订为（本文权威 · Installer 正文应跟齐）**：

> **F-INS-FIRST-01′**：首启首页主 CTA 进入导入向导；向导 pick 步 **必须**同屏提供一等「试用示例相册」入口（与选文件夹并列次主）。首页 **不要求**并排第二主按钮「试用示例」。

验收 AC-INS-A03 路径改为：首页 → 向导 → 试用示例 → 预览。
