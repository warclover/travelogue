# Travelogue Studio · 首页（工作台）产品需求文档

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | v1.3.3-HOMEPAGE |
| **状态** | Draft · 待设计评审与 M12 排期 |
| **页面路由** | `GET /` → `templates/studio/studio.html` |
| **前置条件** | [PRD-PHASE2.md](./PRD-PHASE2.md) M8–M10 已交付；`travelogue studio` 单端口 8766 |
| **关联文档** | [PRD-PHASE2.md](./PRD-PHASE2.md) · [PRD-PHASE3.md](./PRD-PHASE3.md) · [IMPLEMENTATION-PHASE2.md](./IMPLEMENTATION-PHASE2.md) · [ACCEPTANCE-PHASE2.md](./ACCEPTANCE-PHASE2.md) · [adr/004](./adr/004-studio-hub-server.md) · [SHARING.md](./SHARING.md) |
| **负责人** | 首席产品经理 |
| **更新日期** | 2026-05-27 |

---

## 1. 文档范围与术语

### 1.1 「进入应用」≠ 账号登录

Phase 2 **无用户账号体系**（见 PRD-PHASE2 §2.2）。本文所称 **「进入应用后的第一眼」** 指：

| 入口 | 用户动作 | 第一眼 URL |
|------|----------|------------|
| 双击 `scripts/start-studio.bat` | 启动本地服务 | `http://127.0.0.1:8766/` |
| 运行 `TravelogueStudio.exe`（M11） | 同上 | 同上 |
| CLI `python -m travelogue studio` | 开发者 / 高级用户 | 同上 |

**伪登录态**：浏览器打开即视为「已在本机进入 Studio」；数据存于本地 `trips/`，无云端同步。

> **Phase 3 预留**：账号、素材洞察、引擎状态灯等扩展见 **§19**；不改变首页「选图 → 预览 → 长图」主路径。

### 1.2 首页在产品中的角色

首页 = **Studio 工作台（Hub）**，不是游记正文页。

| 页面 | 路由 | 职责 |
|------|------|------|
| **首页 / 工作台** | `/` | 价值传达、选图导入、进度等待、继续编辑 |
| **预览页** | `/{tripId}/index.html` + preview-toolbar | 改字、生成长图、导出 |
| **长图捕获面** | `/{tripId}/index-longshot.html` | **无 UI 注入**；仅供 Playwright 截图 |

首页回答三个问题：

1. **这是什么？** — 旅行照片 → 杂志风长图 → 发微信  
2. **我下一步做什么？** — 选照片 / 试示例 / 继续上次  
3. **还要等多久？** — 导入进度与预估时间  

### 1.3 与 Phase 3 的关系

[PRD-PHASE3.md](./PRD-PHASE3.md) v0.3.3 Kickoff 将 **Curate 聚类** 作为 pipeline 内部增强，**不改变** Studio 首页主路径（选文件夹 → 预览 → 长图）。Studio 可见变化见 PRD **§6.4**（Importing hint · D′ 高级折叠）。

| 阶段 | 用户可见变化 | 首页影响 |
|------|--------------|----------|
| **Phase 2 · 首页** | 首次 import → preview | §6.11 首次成功过渡 |
| **Phase 3 · 聚类** | 成稿章/组屏质量提升（无新页面） | **无** 新增 CTA / 顶栏 slot |

Phase 2 首页的 **首次成功过渡（§6.11）** 仍是核心 Aha：**用户第一次看到自己生成的游记**。

---

## 2. 背景与问题

### 2.1 现状（M8–M10 已交付）

当前 `studio.html` 已具备：Hero、样例长图、路径表单、示例相册、浏览器上传、Job 进度、失败重试、trip 列表。

### 2.2 交互断裂（本 PRD 要解决的）

| ID | 断裂 | 用户感受 | 首页应补什么 |
|----|------|----------|--------------|
| **HP-GAP-01** | 三种导入方式平铺，无优先级 | 「我该用哪个？」 | 主路径卡片 + 次级折叠 |
| **HP-GAP-02** | 回访用户与首次用户同一布局 | 老用户只想「继续编辑」 | **回访态**置顶「最近编辑」 |
| **HP-GAP-03** | trip 列表信息密度低 | 不知道长图是否过期 | 卡片含封面缩略图 + 状态徽章 |
| **HP-GAP-04** | 原生选文件夹未暴露 | 只能粘贴路径 | 主按钮「选择文件夹」（exe / API） |
| **HP-GAP-05** | 系统 confirm 弹窗 | 不像一个产品 | 首页内 Modal 组件 |
| **HP-GAP-06** | 样例图为占位 | 价值感不足 | 真实输出样例 + 制作标准（§6.6） |
| **HP-GAP-07** | 首次生成无过渡反馈 | 「完成了吗？」 | §6.11 首次成功过渡 |
| **HP-GAP-08** | `/trips` 加载空白 | 「页面坏了？」 | Loading 态 + 骨架屏（§5、§6.12） |
| **HP-GAP-09** | 轻量操作无反馈 | 复制 IP 无确认 | StudioToast（§7.5） |
| **HP-GAP-10** | 用户无「照片文件夹」心智 | 不知道选哪个 | §6.13.1 照片准备引导 |
| **HP-GAP-11** | 多次导入关系不明 | Day2 会覆盖吗 | §6.13.2 新建预期 |
| **HP-GAP-12** | stale 徽章与 CTA 不一致 | 点了继续编辑还要自己找长图 | §6.4 更新长图 CTA |
| **HP-GAP-13** | 试用后无转化引导 | 示例看完就停 | §6.13.3 试用回流 |
| **HP-GAP-14** | 首页像工具不像作品 | 摄影用户无感 | §6.3 · §6.6 杂志 Hero + 画廊 |

### 2.3 产品目标

| ID | 目标 | 衡量 |
|----|------|------|
| **G-HP-01** | 首次进入 **10 秒内** 理解产品并找到主操作 | 5 人可用性测试 |
| **G-HP-02** | 回访用户 **5 秒内** 打开最近 trip | 点击「继续编辑」≤ 2 次 |
| **G-HP-03** | 非开发者 **不看到** 路径输入框作为主视觉（exe 场景） | AC-P2-03 |
| **G-HP-04** | 导入等待时 **不焦虑** | stageHint + 取消 + 慢速提示 |
| **G-HP-05** | 与预览 toolbar 形成 **一条旅程** | 首页 CTA 文案与 toolbar 一致 |
| **G-HP-06** | 首次成功生成后 **7 天内再次打开** Studio | 本地 `firstPreviewDone` + 二次 `GET /` 会话 |
| **G-HP-07** | 摄影 / 发烧友 **10 秒内** 感受到「理解美」 | 5 人走查；首屏全幅 Hero + 画廊可见 |

---

## 3. 目标用户与第一眼场景

### 3.1 Persona

**A · 首次旅行者（主）**  
旅行后 1–3 天，Windows 笔记本，照片在 `D:\Photos\xxx`，不会命令行。

**B · 回访编辑者**  
上周做过一篇，今天想改字或重新生成长图。

**C · 好奇试用者**  
尚无照片，想先看效果再决定。

**D · 摄影 / 发烧友（视觉敏感）**  
在意输出审美与界面气质；对 stock 图、系统 UI 字体敏感；希望首页「像作品而非工具」。

### 3.2 第一眼 User Stories

| ID | 作为… | 第一眼我想… | 以便… |
|----|--------|-------------|--------|
| **US-HP-01** | 首次用户 | 看到「输出长什么样」 | 判断值不值得做 |
| **US-HP-02** | 首次用户 | 一个主按钮开始 | 不用读三种导入说明 |
| **US-HP-03** | 回访用户 | 看到上次那篇置顶 | 直接继续 |
| **US-HP-04** | 所有用户 | 知道照片不会上传云端 | 安心选文件夹 |
| **US-HP-05** | 等待中用户 | 看到「导入→排版→渲染」进度 | 知道还要几分钟 |
| **US-HP-06** | 失败用户 | 看到中文原因 + 重试 | 不面对错误码 |
| **US-HP-07** | 首次成功用户 | 生成完成时有明确反馈 | 知道即将看到预览 |
| **US-HP-08** | 从预览返回用户 | 看到「最近编辑」并知道点哪 | 第二次打开不迷路 |
| **US-HP-09** | 不擅长电脑的用户 | 知道照片该放哪、怎么选文件夹 | 不被「文件夹」术语卡住 |
| **US-HP-10** | 多次导入用户 | 知道再导入会**新建**游记而非覆盖 | 安心分 Day1/Day2 导入 |
| **US-HP-11** | 试用示例后用户 | 被引导用自己的照片做一篇 | 从演示转化为真实使用 |
| **US-HP-12** | 摄影爱好者 | 第一眼感受到「这个工具理解美」 | 愿意继续选照片 |

### 3.5 视觉气质方向（摄影 / 发烧友）

**基调**：Kinfolk 的克制留白 + Unsplash 的全幅摄影冲击 — **不是** VSCO 式全深色，保持 Studio 现有浅色编辑台可读性。

| 参考 | 借鉴 | 不照搬 |
|------|------|--------|
| Unsplash | Hero 全幅图 + 操作浮于图上 | 搜索框主导 |
| Kinfolk | 留白、Light 字重、letter-spacing | 纯 serif 全书 |
| Apple Photos Memories | 情感化标题 + 真实照片 | 自动视频 |
| Notion 首页 | 空态 = 灵感 + 渐进复杂度 | SaaS 仪表盘 |

**核心原则（冻结）**：首页应 **像产品输出的作品**，而不只是管理作品的工具。

### 3.6 视觉升级优先级

| 优先级 | 项 | 投入 | 章节 |
|--------|-----|------|------|
| **P0** | 杂志式 Hero（全幅真实输出裁切 + 蒙版 + CTA 内嵌） | 中 | §6.3 |
| **P0** | 多样例画廊（**M12 横滑 carousel**） | 中 | §6.6 · §8.2 |
| **P0** | Hero Light 字重 + letter-spacing（零 Web Font） | 低 | §6.14.2 |
| **P1** | 纸张纹理背景 | 低 | §6.14.3 |
| **P1** | 空态 **瀑布流灵感墙（M12b）** | 中 | §6.6 |
| **P1** | 卡片 / CTA 微交互 | 低 | §6.14.4 |
| **P2** | Display Web Font（可选） | 中 | §6.14.2 · M13 |
| **P2** | preview 主色提取占位 | 高 | §6.4 · M13 |
| **P2** | 进度条渐变 + 光点 | 低 | §6.8 |

---

## 3.3 模拟用户旅程与认知断点

基于 Persona 走查（小王 / 老用户 / 好奇试用者），首页 **操作流通畅**，最大缺口在 **认知支架**，而非信息架构。

| Persona | 场景摘要 | 通畅点 | 断点 |
|---------|----------|--------|------|
| **A · 小王** | 京都 200+ 张，照片在手机/OneDrive/分散子文件夹 | 试用示例 → 看到输出；进度条知道在处理 | ① 什么叫「文件夹」② 多个子文件夹选哪个 ③ 再导入 Day2 会覆盖还是新建 |
| **B · 老用户** | 改字后需重新发长图 | C 区置顶、一眼找到 | 「长图待更新」与「继续编辑」行动暗示不一致 |
| **C · 试用者** | 无照片，点示例 | 示例相册可用 | 回到首页与首次空态相同，缺下一步引导 |

**结论**：在 **文案与引导层** 补充认知支架（§6.13），不改变「首页 → 预览 → toolbar 生成长图」分工。

### 3.4 认知支架优先级

| 优先级 | 支架 | 用户价值 | 章节 |
|--------|------|----------|------|
| **P0** | 照片准备引导 | 消除「文件夹」门槛 | §6.13.1 |
| **P0** | 多次导入预期（新建 vs 覆盖） | 避免误操作焦虑 | §6.13.2 |
| **P1** | Stage 用户友好文案 | 等待时不困惑 | §8.2 |
| **P1** | stale 卡片 CTA 对齐 | 行动与徽章一致 | §6.4 |
| **P1** | 样例图期望管理 | 避免效果落差 | §6.6 |
| **P2** | 试用后回流引导 | 演示 → 真实转化 | §6.13.3 |
| **P2** | 删除游记预留位 | 导错可补救感 | §6.4 · M13 |
| **P2** | 动态时间估算 | 等待焦虑管理 | §6.5 · §6.8 |
| **P2** | 页脚 checklist 简化 | 不提前引入「章」 | §6.10 |

---

## 4. 信息架构

### 4.1 首页区块优先级（分态）

**空态（IdleEmpty）**：`A → B★ → D′ → E★ → I`

> **v1.3 IA 调整**：空态 **主 CTA 嵌入杂志 Hero（B）**；D′ 仅保留次级入口（示例 / 上传 / 照片引导），**不重复**主按钮。E★ 升级为 **灵感画廊**（比回访态更大）。

**回访态（IdleReturning）**：`A → B⁻ → C → D → E⁻ → F → I`

> B⁻ = 压缩文字 Hero（无全幅图）；E⁻ = 横向 3 卡样例轮播（克制）。

```
空态 IdleEmpty                 回访态 IdleReturning
─────────────────              ─────────────────────
A  顶栏                         A  顶栏
B★ 杂志 Hero（CTA 内嵌）         B⁻ 压缩 Hero
D′ 次级操作 + 认知支架          C  最近编辑 ★
E★ 灵感画廊 / 瀑布流            D  制作新的游记
I  页脚                         E⁻ 样例轮播（小）
                               F  全部游记
                               I  页脚
```

| 区块 | 职责 |
|------|------|
| **A** | Logo · 本地运行 · favicon |
| **B★** | 全幅摄影 Hero + 情感标题 + **主 CTA** + pills |
| **B⁻** | 一行标题 20px · 无全幅图 |
| **D′** | 示例相册 · 上传 · 照片准备引导 · 路径折叠 |
| **E★** | 2–5 张样例 · 空态瀑布流或横滑画廊 |
| **E⁻** | 回访态横滑 3 卡 + 「精选」居中放大 |

### 4.2 与预览页的分工

| 能力 | 首页 | 预览 toolbar |
|------|------|--------------|
| 选图 / 导入 | ✓ 主责 | — |
| 改标题 / hook / 图注 | — | ✓ 主责 |
| 保存长图 | — | ✓ 主责 |
| 封面 preview.jpg | 列表缩略图 | 路径 + reveal |
| 导出 zip | — | 高级菜单 |
| 返回 | — | ← 返回工作台 |

**原则**：首页只做到「进入预览」；**分享闭环在预览页完成**。

---

## 5. 页面状态机

首页有 **六种** 主状态（同一 URL，无路由跳转）：

```mermaid
stateDiagram-v2
  [*] --> Loading: 打开 /
  Loading --> IdleEmpty: trips 为空
  Loading --> IdleReturning: trips ≥1
  Loading --> Offline: health 失败
  IdleEmpty --> Importing: 开始导入
  IdleReturning --> Importing: 新建导入
  Importing --> FirstSuccess: Job 成功
  FirstSuccess --> Preview: toast 后跳转
  Importing --> Failed: Job 失败
  Failed --> Importing: 重试
  Failed --> IdleEmpty: 取消
  Importing --> IdleReturning: 用户取消 Job
  Offline --> Loading: 服务恢复
  Preview --> IdleReturning: 从 preview 返回 /
```

| 状态 | 条件 | 界面变化 |
|------|------|----------|
| **Loading** | 首次 `GET /trips` 进行中 | Hero 立即显示；C/D/F 骨架屏（§6.12） |
| **IdleEmpty** | `trips` 为空 | 无 C/F；D 置顶；E 置底 |
| **IdleReturning** | `trips.length ≥ 1` | C 置顶；可选首次回访 highlight（§6.11） |
| **Importing** | active Job | 进度 UI；禁用 D；动态 `<title>` |
| **FirstSuccess** | Job succeeded，跳转前 | Toast + 可选全屏过渡条（§6.11） |
| **Failed** | Job failed | 失败面板；`<title>` 含「导入失败」 |
| **Offline** | `GET /health` 失败 | 全页 banner；禁用导入（§21） |

---

## 6. 完整界面设计

### 6.1 布局规格

| 项 | 规格 |
|----|------|
| 内容宽（移动/平板） | `720px` |
| 内容宽（桌面 >1024px） | `1200px`（卡片网格区）；表单区 `640px` |
| 外边距 | 水平 `24px`（移动 `16px`） |
| 卡片圆角 | `12px` |
| 主色 | `--color-accent: #3d6b5a` |
| 背景 | `--color-bg: #f4f7f5` |
| 字体 | Segoe UI / PingFang SC / Microsoft YaHei |
| **CSS 变量化** | 所有颜色、圆角、阴影使用 custom properties；**Phase 2 不做暗色模式**，但变量命名便于 Phase 3 扩展 |
| **Favicon** | `templates/studio/assets/favicon.ico`（16×16 + 32×32）；相机/字标简化形 |
| **`<title>` 动态** | 默认 `Travelogue Studio`；Importing → `正在生成… · Travelogue Studio`；Failed → `导入失败 · Travelogue Studio` |

#### 响应式断点

| 断点 | 布局 |
|------|------|
| **360–640px** | 单列；padding `16px`；次路径卡片纵向堆叠 |
| **641–720px** | 单列标准（主设计稿） |
| **721–1024px** | D 区次路径可 2 列并排；Hero 填满容器 |
| **1025–1440px** | 内容 `max-width: 1200px` 居中；**Hero 全幅**（`100vw`，内容 `1200px`）；画廊可见 4–5 卡 |
| **>1440px** | 内容 `max-width: 1200px` 居中；**Hero 全幅**（最大 `1400px`）；两侧留白增加 |

> **桌面适配原则**（v1.4 新增）：Hero 全幅呈现杂志冲击感；内容区 1200px 保证画廊/trip 卡片有足够横向空间；表单/页脚等文本密集区缩回 `640px` 内以保可读性。

### 6.2 区块 A · 顶栏（M12 · P1）

| 元素 | 文案 / 行为 |
|------|-------------|
| 左 | **Travelogue Studio**（字标，点击刷新 `/`） |
| 右 | 绿点 + **本地运行中** · `127.0.0.1:8766`（点击复制 → Toast「已复制」） |
| 右 · 预留 | `#studio-shell-slot-p3` 空容器（Phase 3 引擎状态灯，§19） |

### 6.3 区块 B · Hero（双形态）

#### B★ · 杂志 Hero（空态 IdleEmpty · P0）

**布局**：全幅 **真实产品输出** 摄影裁切（非 stock）+ 暗角 / 底部渐变蒙版；白字叠于图上。

| 元素 | 规格 |
|------|------|
| **背景图** | `templates/studio/assets/hero/` 下 2–3 张 WebP；从 golden trip 长图裁切；`sessionStorage` 或日期 hash 轮换 |
| **蒙版** | `linear-gradient(180deg, rgba(0,0,0,.15) 0%, rgba(0,0,0,.55) 100%)` + 可选 vignette |
| **Eyebrow** | `TRAVELOGUE` · `letter-spacing: 0.2em` · 半透明白 |
| **H1（情感）** | **让每一段旅程，都值得被杂志记录** |
| **副标题（功能，可选一行）** | 把旅行照片变成杂志风长图，直接发微信 |
| **主 CTA** | **选择照片文件夹**（Hero 内嵌，首屏无需滚动；**已决 · 2026-05-27**） |
| **Pills** | ◇ 自动分章 · ◇ 留在本机 · ◇ 约 2–5 分钟 |
| **高度** | `min-height: 480px`（桌面）；`360px`（窄屏）；图片 `object-fit: cover` |
| **性能** | Hero 图 **≤ 180KB** · `fetchpriority="high"` · 不 lazy |
| **对比度** | 白字 on 蒙版 **≥ WCAG AA**（4.5:1） |

**D′ 区不再重复主 CTA** — 仅次级入口 + §6.13 认知支架。

#### B⁻ · 压缩 Hero（回访态 IdleReturning）

Eyebrow + **一行功能标题** 20px · **无全幅图** · 无内嵌 CTA（C 区承担主行动）。

#### 文案双层策略（冻结）

| 层 | 用途 | 示例 |
|----|------|------|
| 情感 H1 | 空态杂志 Hero | 让每一段旅程，都值得被杂志记录 |
| 功能副标 | 澄清交付物 | 把旅行照片变成杂志风长图，直接发微信 |
| 主 CTA | 动作 | **选择照片文件夹**（冻结，不做 A/B） |

### 6.4 区块 C · 最近编辑（回访态）

**显示条件**：`trips.length >= 1`

**标题**：`继续上次的游记`

**回访态 Hero 压缩**：标题 **20px**；**省略 pills**（让位 C 区）。

**卡片规格（最多 3 条）** — 竖版封面卡片（cover 在上，body 在下）

| 字段 | 展示规则 |
|------|----------|
| 封面区 | `height: 180px` · lazy · `onerror` 占位（灰色渐变 + 文字） |
| 标题 | ellipsis + `title` tooltip |
| **示例标��** | demo trip → 封面右上角徽章 **示例** |
| 副文案 | `photoCount` · 日期 · stale 徽章 |
| **主按钮 · 默认** | **继续编辑** |
| **主按钮 · stale** | **更新长图** → preview + focus toolbar 长图按钮 |
| 次按钮 | **显示封面**（`reveal` 打开系统文件夹） |
| **⋯ 菜单** | M13：**删除游记**（线框占位） |

**整卡可点** · hover 浮起 · `cursor: pointer`

**试用回流**：仅示例 trip 时，卡片下 **试试用自己的照片做一篇 →**

### 6.5 区块 D′ · 次级操作（空态）/ D · 制作新的游记（回访态）

**空态 D′**（无主 CTA）：试用示例相册 · 浏览器上传 · 照片准备折叠 · 路径折叠 · 多次导入说明见 §6.13

**回访态 D**：副标题「每个文件夹会生成一篇新的游记」+ 选择照片文件夹

### 6.6 区块 E · 样例与灵感画廊

#### E★ · 灵感画廊（空态 · P0/P1）

**标题**：`他们的旅行故事`

| 项 | 规格 |
|----|------|
| **数量** | 4–6 张样例（城市 / 自然 / 人文 / 美食等风格差异） |
| **空态布局** | **M12：横滑 carousel**（3–5 张 · 精选居中放大 · `1/5` 指示）· **M12b：两列瀑布流**（空态加大） |
| **卡片** | 竖版裁切 + 情境标签：`京都 · 雨后 · 86 张 · 约 3 分钟` |
| **精选** | 居中卡片略大 + ★ 精选 角标（carousel 模式） |
| **交互** | 左右箭头 / touch swipe · 指示 `1 / 5` |
| **reveal** | 进入视口 `opacity + translateY` 淡入（§6.14.4） |
| **素材** | 全部 **真实 pipeline 输出**；CI 维护 `templates/studio/assets/gallery/` |
| **期望** | 底部：`杂志风竖版长图 · 保存后可直接发微信` + `实际效果取决于照片数量与质量` |

#### E⁻ · 样例轮播（回访态）

横滑 3 卡 · 高度 ≤ 180px · 不抢 C 区注意力。

#### 素材标准（单张 fallback）

9:16 · ≤500KB · 角标 **示例效果（约 80 张照片）**

### 6.7 区块 F · 我的游记

**显示条件**：`trips.length >= 2` · 卡片规则同 §6.4 · 「查看更多」+20

### 6.8 区块 G · 导入进度（Importing）

**用户 stage 文案**：见 **§8.2**（如 `2/4 正在智能排版…（约 1 分钟）`）

**multipart**：上传条（蓝）+ pipeline 条 · CLI 仅 pipeline 条

**进度条视觉（P2）**：accent 渐变填充 + 末端微光点 · 尊重 `prefers-reduced-motion`

**`<title>`**：`正在生成… · Travelogue Studio`

### 6.9 区块 H · 失败态（Failed）

**路径回显（P0）**：`D:\Photos\Kyoto2025（3 张照片）` 灰字于错误上方

Modal · 重试 — 同 v1.1

### 6.10 区块 I · 页脚

折叠 + **了解如何发微信 ▸** 展开 3 步 checklist（**简化，无「章」概念**）：

1. 预览页点「保存长图」得 PNG  
2. 微信拖入或手机相册发送  
3. 多张长图按文件名编号顺序发送  

### 6.11 首次成功过渡（FirstSuccess · Aha Moment）

**触发**：用户 **生涯首次** import Job `succeeded`（`localStorage.travelogue.studio.firstPreviewDone` 未设置）。

| 步骤 | UI | 时长 |
|------|-----|------|
| 1 | 进度条满格 | 即时 |
| 2 | **StudioToast**（居中偏上，可略大）：「你的第一篇游记已生成，正在打开预览…」 | 显示 |
| 3 | 可选：D 区上方 **全宽过渡条**（accent 色，indeterminate） | 800ms |
| 4 | `window.location.href = previewUrl` | Toast 后 **≥800ms** 再跳转（避免闪屏） |
| 5 | 写入 `firstPreviewDone=1` + `firstTripId` | 跳转前 |

**非首次成功**：Toast 缩短为「生成完成，正在打开…」300ms 后跳转。

**从 preview 返回 `/` 后（首次）**：

| 条件 | UI |
|------|-----|
| `firstPreviewDone=1` 且 `firstReturnHighlight` 未设置 | C 区 **highlight 动效** + tooltip「你的游记在这里，点击继续编辑」 |
| 用户点击 C 或 5s 后 | 清除 highlight；写 `firstReturnHighlight=1` |

**与 preview toolbar 协同（可选 M12b）**：preview 首次打开时，编辑提示条文案可改为「试试改标题，然后点保存长图」— 由 preview-toolbar 读同一 `localStorage` 键。

### 6.12 加载态与骨架屏（Loading）

| 区域 | Loading 行为 |
|------|--------------|
| **Hero（B）** | 静态 HTML，**不等待** API |
| **C / F** | 2–3 个 `.studio__skeleton-card`（72×128 缩略块 + 两行灰条 shimmer） |
| **D** | 主按钮形 skeleton 或 spinner +「加载中…」 |
| **E** | 样例图 blur-up / 渐变占位（不阻塞） |
| **超时** | `/trips` **>3s** 未返回 → Toast「加载较慢，请稍候」；**>10s** → 显示重试链接 |

**缩略图加载中**：卡片内 shimmer；加载完成后 fade-in（150ms）。

### 6.13 认知支架（文案层 · 不改变 IA）

#### 6.13.1 照片准备引导（P0）

**位置**：D 区主 CTA 下方，**折叠**「不知道选哪个文件夹？」  
**默认**：收起；用户点击 ▸ 展开下列 bullet：

- 把**同一次旅行**的照片放到一个文件夹里（50–100 张最佳）
- 若分散在「Day1 / Day2」等子文件夹：先**合并**到一个文件夹，或**分两次导入**（每次一篇**新**游记）
- 支持 JPG / PNG / WebP / HEIC；照片**不会被移动或修改**
- **手机照片**需先传到电脑（复制到「图片」或用数据线导入）

**非功能**：纯文案，不调 API。  
**覆盖**：空态 + 回访态 D 区均展示（回访态在「每个文件夹会生成一篇新的游记」下方）。

#### 6.13.2 多次导入预期（P0）

| 触点 | 文案 |
|------|------|
| 回访态 D 标题旁 | 每个文件夹会生成一篇**新的**游记，不会覆盖已有游记 |
| 选文件夹后 Toast | 将新建一篇游记 · 已选择 N 张 |
| 覆盖场景 | 仅 **同一 tripId / 示例相册** 再次导入时走 Modal「覆盖」（E_DEMO_EXISTS） |

**Persona A · Day1/Day2**：两次导入 = 两篇独立 trip，首页 F 区均可见。

#### 6.13.3 试用后回流引导（P2）

**条件**：C 区存在且**仅**示例 trip，或 `localStorage.demoTried` 且尚无用户 trip。

**UI**：示例卡片下方：  
`试试用自己的照片做一篇 →`（anchor `#studio-import-primary`）

**示例卡片**：徽章 **示例**，与真实游记视觉区分。

### 6.14 视觉设计语言（摄影 / 发烧友）

#### 6.14.1 气质

首页 = **编辑台 + 作品集封面**。工具性控件（路径、进度）保持清晰；展示性区域（Hero、画廊）追求杂志感。

#### 6.14.2 字体

| 角色 | M12（零加载） | M13 可选 |
|------|---------------|----------|
| Display / H1 | 系统 UI **Light（300）** · `letter-spacing: 0.04em` · `line-height: 1.5` · **30px** | `@font-face` 衬线或霞鹜文楷 **仅 Hero ~20 字** · `font-display: swap` |
| Eyebrow | `letter-spacing: 0.2em` · uppercase | 同左 |
| Body / UI | Segoe UI / PingFang SC · 14–15px | 不变 |

#### 6.14.3 色彩与质感

| Token | 值 | 用途 |
|-------|-----|------|
| `--color-accent` | `#3d6b5a` | 主色 · CTA |
| `--color-accent-warm` | `#c4956a` | 暖金 · 徽章 / ★ 精选 |
| `--color-bg` | `#f4f7f5` + **纸张 noise SVG**（inline） | 页面底 |
| CTA 渐变 | `#3d6b5a → #4a7d6a` | 主按钮深度 |
| 缩略图占位 | 默认灰渐变 · **P2** 从 `preview.jpg` 提取主色 CSS var | trip 卡片 |

#### 6.14.4 微交互（P1）

| 元素 | 行为 | 无障碍 |
|------|------|--------|
| Trip 卡片 hover | `translateY(-4px)` + shadow · thumb `scale(1.05)` | 无 hover 设备仍可点 |
| 样例 reveal | IntersectionObserver 淡入上移 | `prefers-reduced-motion: reduce` → 直接显示 |
| 主 CTA | 极 subtle shadow **breathing** 3s | reduced-motion 关闭 animation |
| 画廊 swipe | touch + 箭头 | keyboard 左右键可选 |

---

## 7. 组件与交互规格

### 7.1 组件清单

| 组件 ID | 名称 | 文件 |
|---------|------|------|
| **CMP-HP-01** | `StudioHero` | `studio.html` |
| **CMP-HP-02** | `RecentTripCard` | `studio-trip-card.js` |
| **CMP-HP-03** | `ImportPrimary` | `studio.html` + `studio.js` |
| **CMP-HP-04** | `ImportProgress` | `#studio-progress` |
| **CMP-HP-05** | `TripList` | `#studio-trips` |
| **CMP-HP-06** | `SampleOutput` | `.studio__sample` |
| **CMP-HP-07** | `StudioModal` | `studio-modal.js` |
| **CMP-HP-08** | `StudioShell` | `studio-shell.css` |
| **CMP-HP-09** | `StudioToast` | `studio-toast.js` |
| **CMP-HP-10** | `StudioSkeleton` | `studio.css` |
| **CMP-HP-11** | `FirstSuccessTransition` | `studio.js` |
| **CMP-HP-12** | `OfflineBanner` | `studio.js` |
| **CMP-HP-13** | `PhotoPrepGuide` | `studio.html` · 折叠引导 |
| **CMP-HP-14** | `TripCardMenu` | M13 · 删除等 · 占位 |
| **CMP-HP-15** | `MagazineHero` | `studio-hero.css` · 空态全幅 |
| **CMP-HP-16** | `SampleGallery` | `studio-gallery.js` · carousel / masonry |

### 7.2 Modal 规格（CMP-HP-07）

| 场景 | 标题 | 主按钮 | 次按钮 |
|------|------|--------|--------|
| 覆盖游记 | 该游记已存在 | 覆盖并重新导入 | 取消 |
| 取消导入 | 确定取消？ | 确定取消 | 继续等待 |

### 7.3 原生选文件夹（CMP-HP-03）

方案 A：exe IFileDialog · 方案 B：`POST /__travelogue/pick-folder` · 降级：路径表单

### 7.4 键盘与无障碍

Enter 提交 · Esc 关闭 Modal · 进度区 `aria-live="polite"` · Toast `role="status"`

### 7.5 Toast 规格（CMP-HP-09）

| 项 | 规格 |
|----|------|
| 位置 | **底部居中**，距底 `24px` |
| 时长 | **3s** 自动消失；FirstSuccess 可达 **5s** |
| 堆叠 | 最多 **2 条**；新 Toast 顶掉最旧 |
| 样式 | 深底 `#1a2f28` · 白字 · 圆角 8px · 非阻断 |
| 动画 | slide-up + fade |

| 场景 | 文案 |
|------|------|
| 复制 IP | 已复制 |
| 选文件夹成功 | 已选择 · 约 N 张 · 预计 X 分钟 |
| 新建游记确认 | 将新建一篇游记 · 约 N 张 |
| 首次生成成功 | 你的第一篇游记已生成，正在打开预览… |
| 非首次生成 | 生成完成，正在打开… |
| `/trips` 慢 | 加载较慢，请稍候 |

**不纳入 M12**：版本更新 / 新功能通知（留 Phase 3 顶栏 slot）。

### 7.6 原生选文件夹 / 键盘

（同 v1.0 §7.3、§7.4）

---

## 8. 文案规范

| 位置 | 文案 | 禁止 |
|------|------|------|
| 主 CTA | **选择照片文件夹** | ingest、上传至服务器 |
| 情感 H1 | 让每一段旅程，都值得被杂志记录 | — |

### 8.1 主 CTA（已关闭 A/B）

**冻结（产品已决 2026-05-27）**：全站主 CTA 统一 **「选择照片文件夹」**，含杂志 Hero 内嵌按钮。

**理由**：Persona A（小王）需明确「文件夹」动作；Persona D 的视觉气质由 Hero 摄影与画廊承担，不靠改写 CTA。

~~备选「选择照片，开始创作」「选照片，做游记」~~ — 不再做 A/B。

| 位置 | 文案 | 禁止 |
|------|------|------|
| 样例角标 | 示例效果（约 80 张照片） | mockup |
| 首次成功 Toast | 你的第一篇游记已生成，正在打开预览… | Success |
| Stage 1/4 | 正在准备你的照片… | ingest |
| stale 主按钮 | 更新长图 | — |
| 多次导入 | 每个文件夹会生成一篇新的游记 | — |

### 8.2 M12 画廊形态（已决）

**M12 交付：横滑 carousel**（非瀑布流）。

| 项 | 决定 |
|----|------|
| **形态** | 3–5 张 · 横滑 + 箭头 · `2/5` 指示 · 居中「★ 精选」略大 |
| **理由** | 实现快（纯 CSS scroll-snap + 少量 JS）；满足 AC-HP-22；触摸/键盘友好 |
| **M12b** | 空态升级为 **两列不等高瀑布流**（`SampleGallery` masonry 模式） |
| **回访态 E⁻** | 始终用 **3 卡小轮播**，高度 ≤180px |

### 8.3 Stage 用户文案映射

| `job.stage` | UI 文案 |
|-------------|---------|
| ingest | 正在准备你的照片… |
| curate | 正在智能排版… |
| narrate | 正在撰写游记文字… |
| render | 正在生成游记预览… |

显示：`{i}/{total} {文案}（{stageHint}）`

**Phase 3 · ingest stageHint 变体**（聚类并入 ingest · 仍 4 stage）：见 [PRD-PHASE3.md](./PRD-PHASE3.md) §6.4.2。分级慢提示见 §6.4.4。

---

## 9. 数据与 API 依赖

### 9.1 已有 API

| 方法 | 路径 | 用途 |
|------|------|------|
| `GET` | `/__travelogue/trips` | C / F |
| `POST` | `/__travelogue/import` | 导入 |
| `GET` | `/__travelogue/status` | Job 轮询 |
| `POST` | `/__travelogue/cancel` | 取消 |
| `POST` | `/__travelogue/reveal` | 打开文件夹 |

### 9.2 建议新增（M12）

| 方法 | 路径 | 用途 |
|------|------|------|
| `GET` | `/__travelogue/health` | `{ "ok": true }`；首页启动检测 + Offline 态 |
| `POST` | `/__travelogue/pick-folder` | native 选文件夹 |
| `GET` | `/__travelogue/trips?offset=&limit=` | 可选；「查看更多」分页 |
| `GET` | `/__travelogue/config` | Phase 3 · 高级折叠回显（PRD §9.5） |
| `PATCH` | `/__travelogue/config` | Phase 3 · 写入 clustering/vision 三态 |

### 9.3 localStorage 键

| 键 | 用途 |
|----|------|
| `travelogue.studio.firstPreviewDone` | 首次成功 Aha |
| `travelogue.studio.firstReturnHighlight` | 首次返回 highlight 已展示 |
| `travelogue.studio.editHint.dismissed` | 预览编辑提示（已有） |

---

## 10. 用户旅程（首页段）

```mermaid
flowchart TD
  Start[启动 Studio] --> Open[打开 /]
  Open --> Load[Loading · GET trips]
  Load --> Empty[IdleEmpty]
  Load --> Return[IdleReturning]
  Empty --> Import[Importing]
  Return --> Import
  Import --> FS[FirstSuccess · Toast]
  FS --> Preview[preview]
  Preview --> Return2[返回 / · 可选 highlight]
```

---

## 11. 与现有实现差异（Gap List）

| 项 | 优先级 |
|----|--------|
| 首次成功过渡 §6.11 | **P0** |
| Loading 骨架屏 | **P0** |
| StudioToast | **P0** |
| 最近编辑 + 缩略图 | **P0** |
| health + Offline | **P1** |
| 样例图标准 + 替换脚本 | **P1** |
| 顶栏 + favicon + 动态 title | **P1** |
| 分页「查看更多」 | **P2** |
| **认知支架 §6.13** | **P0** |
| **杂志 Hero + 画廊 §6.3/6.6** | **P0** |
| **视觉语言 §6.14** | **P1** |
| **Stage 用户文案 §8.2** | **P1** |
| **stale → 更新长图 CTA** | **P1** |
| BroadcastChannel 多标签 | **P2**（§21） |

---

## 12. 分期交付

| 里程碑 | 范围 |
|--------|------|
| **M12 · v1** | §6.13 · §8.2 · Modal · Toast · **Magazine Hero · Sample carousel** |
| **M12b** | health · pick-folder · **灵感瀑布流** · 纸张纹理 · 微交互 |
| **M13** | trip 删除 · Display Web Font · 主色占位 · 主色提取 |

---

## 13. 验收标准

| ID | Then |
|----|------|
| **AC-HP-01** | 空态 10s 内见主 CTA |
| **AC-HP-02** | 回访首屏见「继续编辑」 |
| **AC-HP-03** | exe 默认无路径框 |
| **AC-HP-04** | 取消 Job 可重导 |
| **AC-HP-05** | 覆盖用 Modal |
| **AC-HP-06** | 失败中文 + 重试 |
| **AC-HP-07** | stale 徽章 |
| **AC-HP-08** | 预览返回列表更新 |
| **AC-HP-09** | 首次成功见 Toast 再跳转 preview |
| **AC-HP-10** | 首次从 preview 返回见 C 区 highlight / tooltip |
| **AC-HP-11** | `/trips` 请求中 C/D 显示 skeleton，Hero 立即可见 |
| **AC-HP-12** | 复制 IP 出现 Toast |
| **AC-HP-13** | Studio 进程停掉后见 Offline banner |
| **AC-HP-14** | preview.jpg 损坏显示占位，页面不崩 |
| **AC-HP-15** | 空态/回访 D 区可展开「不知道选哪个文件夹？」 |
| **AC-HP-16** | 回访 D 区可见「每个文件夹会生成一篇新的游记」 |
| **AC-HP-17** | stale 卡片主按钮为「更新长图」 |
| **AC-HP-18** | 进度显示用户文案（非 ingest/curate 英文） |
| **AC-HP-19** | 试用后示例卡 + 转化引导 |
| **AC-HP-20** | 空态首屏见全幅 Hero + 内嵌主 CTA，无需滚动 |
| **AC-HP-21** | Hero 背景为真实输出裁切，非 stock |
| **AC-HP-22** | 空态 E 区 ≥3 张样例可滑动/浏览 |
| **AC-HP-23** | `prefers-reduced-motion` 下无 breathing / reveal 动画 |

---

## 14. 非目标

- 首页 iframe 预览 · 首页生成长图 · 账号登录
- macOS 首发 · 拖拽导入 · **暗色模式（Phase 2）**
- 版本更新推送 UI（Phase 3）

---

## 15. 线框图（回访态）

（同 v1.0 §15，略）

---

## 16. 线框图（空态 · 已修正 D 在 E 前）

```
┌────────────────────────────────────────────────────────────┐
│  TRAVELOGUE · 旅行游记工坊                                  │
│  把旅行照片变成一篇杂志风长图，直接发微信                    │
│  ✦ 自动分章  ✦ 无需注册  ✦ 约3分钟看到预览                  │
├────────────────────────────────────────────────────────────┤
│  开始制作                          ← D 区紧接 Hero           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  📁  选择照片文件夹                          [ 推荐 ] │  │
│  └──────────────────────────────────────────────────────┘  │
│  [ 试用示例相册 ]    [ 从浏览器上传（较慢） ]                │
├────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐  │
│  │  [ 样例长图 · lazy + blur-up ]   示例效果预览         │  │  ← E 置底
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

---

## 17. 实施指引

| 角色 | 动作 |
|------|------|
| 设计 | 补充 Loading / FirstSuccess / Toast / Offline 态 Figma |
| 前端 | `studio-toast.js` · skeleton CSS · §6.11 逻辑 |
| 后端 | `GET /__travelogue/health`（10 行以内） |
| 内容 | 按 §6.6 重导 `sample-longshot.jpg` |

---

## 18. 页面性能指标

本地应用（127.0.0.1）用户对空白更敏感；指标用于 M12 回归，**非阻塞发布**。

| 指标 | 目标 | 测量 |
|------|------|------|
| **FCP** | ≤ **300ms** | Lighthouse / Performance API；静态 Hero 内联关键 CSS |
| **`/trips` P95** | ≤ **200ms** | 空 trips ≤50ms；20 trips ≤200ms |
| **Hero 图 LCP** | ≤ **180KB** WebP · FCP 仍 ≤300ms | 预载 1 张 · 轮换 lazy 其余 |
| **缩略图** | 可视区优先 | `loading="lazy"` + IntersectionObserver 可选 |
| **JS 体积** | `studio*.js` 合计 ≤ **50KB** gzip | 不引入框架 |

---

## 19. Phase 3 首页说明（v0.3.2 · 无 IA 扩展）

Phase 3 **Curate 聚类** 在 pipeline 内部运行。**不改变** 首页六态状态机、Hero、FirstSuccess、预览分工。

**权威交互规格**：[PRD-PHASE3.md](./PRD-PHASE3.md) **§6.4**（stageHint · 高级折叠 · 慢提示 · 预览无控件）。

| 项 | 决议 |
|----|------|
| `#studio-shell-slot-p3` | **保留空 slot**（HTML comment）供 **Phase 4+**（账号/云 trip）；**不** 用于引擎灯 |
| `#import-primary-slot-p3` | **不实现**「先精选再生成」 |
| **Importing** | 仍 4 stage；聚类并入 ingest · `stageHint` 见 PRD §6.4.2 |
| **D′ 折叠** | 新增 **「高级 · 分析选项」**（行程识别 / 场景分析三态 · 默认收起） |
| **慢提示** | T+30s / T+3min / T+8min · PRD §6.4.4 |
| **预览** | **无** 聚类控件；Aha 仍为 §6.11 FirstSuccess |
| **追加照片** | Phase 3 **不支持** Studio 增量追加；换图需首页 **重新选文件夹** |
| 线框 | [wireframes/studio-homepage-wireframe.html](./wireframes/studio-homepage-wireframe.html) · M13 增补 hint 变体 |

**原则**：M12 首页 HTML **不增加** Phase 3 业务页面；聚类价值体现在 **preview 成稿质量**。

---

## 20. 边界场景与降级（§21 详表）

见 **§21**。

---

## 21. 边界场景与降级策略

| 场景 | 行为 |
|------|------|
| **Studio 进程崩溃** | 每 **30s** `GET /health`；失败 → **OfflineBanner**：「服务已停止，请重新启动 Studio」+ 禁用导入 |
| **用户手动删除 `trips/`** | `/trips` → `[]`；降级 **IdleEmpty**；不抛 uncaught error |
| **`/trips` 500 / 网络错误** | Toast + 重试按钮；3 次失败后 Offline 态 |
| **preview.jpg 损坏 / 0 字节** | `<img onerror>` → 色块 + 相机 icon 占位 |
| **标题过长** | CSS ellipsis + `title` tooltip |
| **>20 篇游记** | 「查看更多」每次 +20 |
| **同一浏览器多标签** | **P2**：`BroadcastChannel('travelogue.studio')` 在 import 完成 / trip 变更时广播 → 其他 tab `loadTrips()`。**M12 不阻塞**，可接受手动刷新 |
| **health 端点不存在（旧版后端）** | 前端降级：仅以 `/trips` fetch 失败推断 Offline |

---

## 22. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0-HOMEPAGE | 2026-05-27 | 首版：IA、状态机、线框、AC-HP-01～08 |
| v1.1-HOMEPAGE | 2026-05-27 | FirstSuccess · Loading · Toast · 边界 · Phase3 预留 |
| v1.2-HOMEPAGE | 2026-05-27 | Persona 走查 · 认知支架 · stale CTA |
| v1.3-HOMEPAGE | 2026-05-27 | 杂志 Hero · 灵感画廊 · §6.14 |
| v1.3.1 | 2026-05-27 | **已决**：CTA 冻结「选择照片文件夹」· M12=gallery carousel · M12b=masonry |
| v1.3.2 | 2026-05-28 | §19 · Phase 3 改为 pipeline 内聚类，取消洞察/引擎首页 slot |
| v1.3.3 | 2026-05-28 | §19 对齐 PRD-PHASE3 v0.3.2 §6.4：高级折叠、慢提示、无 preview 聚类 UI |
