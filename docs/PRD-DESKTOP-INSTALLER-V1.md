# Travelogue · 桌面可安装版 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | **v1.1.1** |
| **状态** | **有条件通过（Conditional Go）** · 批准 M-INS-0 · Gate A/B/C 仍受门禁 |
| **主题代号** | 「桌面可安装版 V1」— 下载 → 安装/解压 → 双击 → 做出一篇 |
| **触发来源** | 种子用户试用需求；Phase 2 M11 backlog 收口；官网 `/install` 与实物倒挂（[PRD-WEBSITE-MARKETING.md](./PRD-WEBSITE-MARKETING.md) D1） |
| **前置条件** | Studio 主路径可用（导入 → 预览 → 长图）；`packaging/travelogue-studio.spec` + `scripts/build-studio-exe.bat` 已存在；`travelogue.desktop.*` 入口可用 |
| **关联文档** | [PRD-PHASE2.md](./PRD-PHASE2.md)（M11）· [IMPLEMENTATION-PHASE2.md](./IMPLEMENTATION-PHASE2.md) · [CHARTER.md](./CHARTER.md) · [SHARING.md](./SHARING.md) · [CLI-SPEC.md](./CLI-SPEC.md) · [adr/004-studio-hub-server.md](./adr/004-studio-hub-server.md) · [adr/005-longshot-server-side.md](./adr/005-longshot-server-side.md) · [adr/018-desktop-installer-layout.md](./adr/018-desktop-installer-layout.md) · [PRD-WEBSITE-MARKETING.md](./PRD-WEBSITE-MARKETING.md) · [PRD-HELP-ONBOARDING-V1.md](./PRD-HELP-ONBOARDING-V1.md) · [PRD-UX-TRUST-V1.md](./PRD-UX-TRUST-V1.md) |
| **验收** | 本文 §11；完整步骤见 [ACCEPTANCE-DESKTOP-INSTALLER-V1.md](./ACCEPTANCE-DESKTOP-INSTALLER-V1.md) |
| **实施清单** | [IMPLEMENTATION-DESKTOP-INSTALLER-V1.md](./IMPLEMENTATION-DESKTOP-INSTALLER-V1.md) |
| **更新日期** | 2026-07-14 |

> **定位**
>
> 当前 Studio 对开发者可用（`pip install` / `start-studio.bat`），对非技术种子用户不可达。  
> M11 已交付 **PyInstaller 骨架**（spec · launcher · IFileDialog · demo 相册），但尚不能称为「可安装产品」：frozen 资源路径未收口、无安装器、无数据目录约定、无签名发布、长图运行时策略未产品化。
>
> 本 PRD 定义 **Windows 桌面可安装 / 可分发** 的最小完备集，使朋友能 **下载 → 打开 → 用自己的照片做出一篇游记并保存长图**，无需 Python、Git、PowerShell。
>
> **产品共识（五条铁律）**
>
> 1. **本地优先不变** — 可安装版仍是本机 Studio；无账号、无强制云同步、无公网多租户。  
> 2. **一人一机一库** — 多用户 = 多安装实例或多 Windows 用户配置；不做进程内租户隔离。  
> 3. **主路径零终端** — 双击后不应出现需用户阅读的黑框命令行（G-P2-02）。  
> 4. **能做出一篇才算装好** — 安装成功 ≠ 产品成功；demo 只证明工程可运行，产品成功必须由非开发者使用自己的 20～100 张照片，无指导完成导入→预览→保存 PNG→找到文件，并能说明如何发群。  
> 5. **不借安装开新能力面** — 不借机做云端注册、自动更新商店、Tauri/Electron 重写、macOS 首版并行。
>
> **2026-07-14 跨职能评审决议**
>
> - 批准立即启动 **M-INS-0 技术收口**。
> - Must-Fix 已回写；`IMPLEMENTATION` / `ACCEPTANCE` / [ADR-018](./adr/018-desktop-installer-layout.md) 已建立。未完成 M-INS-0 冒烟前，不批准 Gate A 外发。
> - Gate B 仅为邀请制安装器测试；未签名、许可未定或真人指标未过时，不得切官网公开下载主 CTA。
> - Gate C 才是签名公开版；Authenticode 证明发布者身份，但不承诺新证书立即消除全部 SmartScreen 提示。

---

## 0. 读者指南

| 章节 | 必须澄清的问题 |
|------|----------------|
| §1 背景 | 现状缺口；与 M11 / 官网关系 |
| §2 目标/非目标 | 范围锁死 |
| §3 交付形态 | 绿色包 vs 安装包；三道门 |
| §4 用户与旅程 | 安装到第一篇的体验合同 |
| §5～§8 需求 | 打包 · 路径 · 运行时 · 安装器 · 首启 · 分发 |
| §9 数据与隐私 | 目录布局；卸载；本地承诺 |
| §10 工程约束 | 与现有代码/决策对齐 |
| §11 验收 | AC 合同与真人门禁 |
| §12 里程碑 | Gate A/B/C |
| §13 风险与开放问题 | |
| 附录 | 现状盘点 · 文案 · 对照表 |

---

## 1. 背景与问题

### 1.1 现状

| 层 | 现状 | 缺口 |
|----|------|------|
| **开发入口** | `pip install -e .` · `python -m travelogue studio` · `scripts/start-studio.bat` | 要求 Python 3.11+ |
| **M11 骨架** | `packaging/travelogue-studio.spec` · `TravelogueStudio.exe` 可构建 · 原生选文件夹 · 内置 demo | 非「可分发安装包」 |
| **frozen 支持** | `is_frozen` / `bundle_root` / `exe_dir` / `default_trips_dir` | 大量 `paths.ROOT` 仍绑源码树，模板/schema 易失效 |
| **长图** | Playwright 服务端；HTML 内有 html2canvas，但 Studio 工具栏尚未接入自动降级 | **OQ-P2-02 已决：exe 不捆绑 Chromium**；Gate A 前须打通双轨 |
| **官网** | `/install` 规划 pip 为主、exe 订阅转化 | 实物未齐，与「一键安装」心智倒挂 |

### 1.2 问题陈述（P-INS-*）

| ID | 问题 | 严重度 | 主要 Persona |
|----|------|--------|--------------|
| **P-INS-01** | 非开发者无法在无 Python 环境下安装并启动 Studio | 阻塞 | 种子试用者 |
| **P-INS-02** | 现有 exe 构建后主路径（模板/schema）可能因 frozen 路径断裂 | 阻塞 | 所有 exe 用户 |
| **P-INS-03** | 双击后可见控制台黑窗，违背「零命令行」心智 | 严重 | 旅行者 |
| **P-INS-04** | 长图依赖 Playwright/Chromium，安装包未说明降级与引导 | 严重 | 分享者 |
| **P-INS-05** | 数据写在 exe 旁，升级/杀毒隔离/权限导致 trips 丢失风险 | 中等 | 回访用户 |
| **P-INS-06** | 无签名 → SmartScreen / Defender 劝退，外发试用失败 | 严重 | 外发对象 |
| **P-INS-07** | 无卸载 / 无开始菜单 / 无一页安装说明 | 中等 | 非技术用户 |
| **P-INS-08** | 无打包冒烟与发布清单，无法保证「发给朋友的那一版能跑」 | 严重 | 产品方 |

### 1.3 与既有主题的关系

| 主题 | 解决什么 | 与本文关系 |
|------|----------|------------|
| **Phase 2 M11** | exe 骨架 · IFileDialog · demo | 本文 **收口为可分发产品** |
| **Help Onboarding** | 首访主链触达 | 安装后首启 **复用**，不另造全站 tour |
| **UX Trust / Export Facade** | 敢导出 · 敢发群 | 安装版须能跑到同一主路径；不改导出算法 |
| **Website Marketing** | `/install` 门面 | 本文交付 **实物**；官网 CTA 从「订阅」切到「下载」的闸门见 §12 |
| **小程序 / 云端** | 微信内触达 | **不在范围**；叙事分区保持 |

---

## 2. 目标与非目标

### 2.1 产品目标

| ID | 目标 | 衡量方式 |
|----|------|----------|
| **G-INS-01** | 非技术用户在 **干净 Windows 10/11 x64**、无 Python / Git / 源码环境下完成安装或解压并启动 Studio | Gate A 5 人中 ≥4 人启动；Gate B N≥15，安装启动成功率 ≥90% |
| **G-INS-02** | 使用自己的 **20～100 张照片**，无指导完成导入→预览→保存 PNG→找到文件，并能说明如何发微信群 | Gate A ≥4/5；Gate B 独立首篇完成率 ≥60%，完成者中位耗时 ≤30 分钟 |
| **G-INS-03** | 用户旅程 **无终端黑窗**（失败日志写入文件，不弹 cmd） | 目视 + AC |
| **G-INS-04** | 卸载或删除安装目录后，用户数据可按策略保留或清除，且文档说清 | AC-INS-DATA-* |
| **G-INS-05** | 每次发版有可复现构建 + 冒烟清单；产物带版本号与校验和 | 发布清单打勾 |
| **G-INS-06** | Gate C 的 Setup 与主 exe 均有有效 Authenticode 签名、可信时间戳、正确证书链和一致发布者 | ≥5 台 Windows 10/11 真机抽样；如仍有 SmartScreen 提示须如实披露 |
| **G-INS-07** | 外测支持成本可控，问题可通过版本、日志和统一反馈入口定位 | Gate B 支持时长中位数 ≤15 分钟/人，P90 ≤30 分钟/人 |

### 2.2 非目标（V1 明确不做）

- 账号体系、云同步、公网多租户 Studio  
- macOS DMG / Linux 包（V1 **仅 Windows x64**；Mac 进 backlog）  
- 应用商店上架（Microsoft Store）  
- 完整 Tauri / Electron 重写  
- 自动更新服务（V1 允许「下载新版覆盖/重装」；静默 OTA 不做）  
- 捆绑完整 Chromium / 捆绑 Torch·CLIP·cull-ml 重量依赖（保持可选）  
- 把「可安装」做成必须联网激活  
- 改变 CHARTER 本地隐私承诺  

### 2.3 成功定义（一句话）

> **朋友下载我们发布的安装包或绿色包，双击打开，不用问「Python 怎么装」，能做出一篇并保存长图。**

其中“做出一篇”固定指：**自己的照片、无人指导、保存并找到 PNG、知道如何发群**；demo 仅作为构建冒烟和首启示范。

---

## 3. 交付形态与三道门

### 3.1 两种分发包（都叫「可安装文件」族）

| 形态 | 产物 | 适用 | V1 优先级 |
|------|------|------|-----------|
| **A · 绿色便携包（Portable）** | `TravelogueStudio-portable-x.y.z.zip`（onedir） | 熟人试用、内测、免管理员权限 | **P0 · Gate A** |
| **B · 安装包（Installer）** | `TravelogueStudio-Setup-x.y.z.exe`（Inno Setup 或等价） | 邀请制封闭公测；Gate C 后公开下载 | **P0 · Gate B** |

> **决策 D-INS-01**：V1 主产物为 **onedir**（非单文件 onefile）。onefile 启动慢、杀毒误报更高；便携包与安装包均基于同一 onedir 构建产物。现有 `travelogue-studio.spec` 的 onefile 形态须改为 onedir（或并行产出）。

### 3.2 三道发布门

| 门 | 名称 | 准入条件 | 外发对象 |
|----|------|----------|----------|
| **Gate A** | Portable 定向内测 | frozen 主路径通；无黑窗；无 Playwright 可出 PNG；退出/日志可用；5 人中 ≥4 人完成自有照片主路径 | 5 名定向种子用户；不公开索引 |
| **Gate B** | Installer 封闭公测 | Gate A + 安装/升级/卸载 + `%LOCALAPPDATA%` + 校验和 + N≥15、安装启动≥90%、独立完成≥60%、中位≤30分钟、支持成本达标 | 邀请制测试；官网仅可二级入口标注「Windows 测试版」 |
| **Gate C** | 签名公开版 | Gate B + Setup/主 exe 签名与可信时间戳 + ≥5 台真机 + 许可/隐私/NOTICE/支持 SOP 完整 | 官网公开下载主推 |

官网首页主 CTA 从「申请内测 / 加入通知」改为「立即下载 Windows 版」的硬门槛：**Gate C**。Gate B 最多提供邀请制或二级入口的「Windows 测试版」，不得作为公开稳定版主推。

---

## 4. 目标用户与体验合同

### 4.1 Persona

**主 Persona（冻结）**：Windows 10/11 x64、无 Python、会使用文件夹、旅行结束后 24～72 小时内，希望用自己的 20～100 张照片在 20～30 分钟内得到并找到可发群 PNG 的用户。

| Persona | 诉求 |
|---------|------|
| **种子试用者** | 尽量少步骤；用自己照片试；反馈给产品方 |
| **旅行分享者** | 装一次，旅行后 20 分钟内出长图发群 |
| **回访者** | 再打开还能看到上次 trip |
| **产品方（你）** | 可复现打包；坏了能看日志；不逐人远程装 Python |

### 4.2 体验合同（C-INS-*）

| ID | 合同 | 违反即失败 |
|----|------|------------|
| **C-INS-01** | 干净机无 Python 可完成 Gate A 旅程 | 要求用户装 Python / Git |
| **C-INS-02** | 启动后自动打开系统默认浏览器到 Studio（`127.0.0.1`） | 用户需手敲 URL 且无提示 |
| **C-INS-03** | 主路径不出现终端窗口 | `console=True` 且无托盘/日志替代 |
| **C-INS-04** | 首次可点「试用示例」验证产品可运行；demo 不计入产品成功率 | demo 缺失，或用 demo 代替真人自有照片验收 |
| **C-INS-05** | 无 Playwright 时自动使用 html2canvas 或等价轨道保存 PNG；不要求用户理解或安装 pip | 静默失败、只给安装命令，或降级后找不到产物 |
| **C-INS-06** | 照片与 trip 默认留在本机用户数据目录 | 未告知就上传云端 |
| **C-INS-07** | 产品成功必须由非开发者用自己的 20～100 张照片，无指导保存并找到 PNG，且能说明如何发群 | 仅完成 demo / 预览，或主持人提示操作 |
| **C-INS-08** | 用户可在产品内发现「退出 Studio」；退出后端口释放，升级/卸载可安全继续 | 只能杀进程，或关闭浏览器后后台进程不可发现地残留 |

### 4.3 用户旅程（Gate A 最短路径）

```text
下载 zip → 解压到本机可写目录
  → 双击 TravelogueStudio.exe
  → 浏览器打开 Studio 首页
  → 「试用示例」（工程冒烟）或「选择文件夹」（产品成功）
  → 使用自己的 20～100 张照片 → 预览 → 保存长图
  → 找到 PNG → 按引导发微信群
  → 在产品内点「退出 Studio」；浏览器可随后关闭
```

---

## 5. 打包与运行时需求

### 5.1 构建产物内容（F-INS-PACK）

| ID | 需求 | 优先级 |
|----|------|--------|
| **F-INS-PACK-01** | 基于 PyInstaller **onedir** 产出 `TravelogueStudio/` 目录，入口 `TravelogueStudio.exe` | P0 |
| **F-INS-PACK-02** | 捆绑：`templates/**`、`schemas/**`、Studio 静态资源、内置 demo-album（≥4 张） | P0 |
| **F-INS-PACK-03** | 捆绑基础依赖：与当前 `pip install .` 主路径一致的运行库（含 pillow、pybars、jsonschema、yaml 等） | P0 |
| **F-INS-PACK-04** | **不**捆绑：Torch / open-clip / cull-ml 重依赖；缺失时功能降级，文案友好 | P0 |
| **F-INS-PACK-05** | **不**捆绑 Chromium（对齐 OQ-P2-02）；策略见 §5.3 | P0 |
| **F-INS-PACK-06** | 可选捆绑或检测：`pillow-heif`（HEIC）；无则中文提示转 JPG | P1 |
| **F-INS-PACK-07** | 构建脚本：`scripts/build-studio-exe.bat`（或后继）一键产出 onedir + 版本写入 | P0 |
| **F-INS-PACK-08** | 产物目录含 `VERSION.txt`（semver + git describe 可选）与 `SHA256SUMS` | P0 |
| **F-INS-PACK-09** | 便携 zip 根目录含 `使用说明.txt`（或 `.md` 转 txt）半页中文 | P0 |
| **F-INS-PACK-10** | 构建时显式收集 `config/platform_profiles.yaml`、`config.yaml.example`、模板、schema、Studio 静态资源与运行时策略文件；缺任一 P0 资源则构建失败 | P0 |
| **F-INS-PACK-11** | 默认构建关闭或评审关闭 UPX；显式排除 Torch / CLIP / cull-ml，并提供构建依赖清单 | P0 |

### 5.2 Frozen 路径收口（F-INS-PATH）— **阻塞项**

| ID | 需求 | 优先级 |
|----|------|--------|
| **F-INS-PATH-01** | 凡读取模板 / schema / studio 资源 / experience-matrix，**frozen 下必须经 `bundle_root()`**（或等价），禁止依赖源码树 `paths.ROOT` | P0 |
| **F-INS-PATH-02** | 默认 trips 目录：见 §9（`%LOCALAPPDATA%\Travelogue\trips`）；便携模式可覆盖为 exe 旁 `trips/` | P0 |
| **F-INS-PATH-03** | 默认配置：首启生成用户配置（从 `config.yaml.example` 拷贝或内置最小配置）；**不**要求用户手改 yaml | P0 |
| **F-INS-PATH-04** | 日志目录：`%LOCALAPPDATA%\Travelogue\logs\`（便携模式：`./logs/`）；崩溃与启动失败可定位 | P0 |
| **F-INS-PATH-05** | 发布前冒烟必须在 **无源码树的干净目录** 运行 exe（防「本机碰巧能跑」） | P0 |
| **F-INS-PATH-06** | 建立唯一 `resource_root()` / `bundle_root()` 契约；生产代码禁止新增裸 `paths.ROOT` 读取捆绑资源 | P0 |
| **F-INS-PATH-07** | Windows frozen 子进程必须显式支持 `multiprocessing.freeze_support()`；导入 spawn 与 pick-folder worker 均在 onedir 中通过 | P0 |

### 5.3 长图运行时策略（F-INS-LNG）— **产品决策**

| ID | 决策 | 说明 |
|----|------|------|
| **D-INS-02** | V1 **不**捆绑 Chromium | 继承 OQ-P2-02；控制体积与签名复杂度 |
| **D-INS-03** | 安装版长图 **双轨** | **轨 1（优先）**：检测到可用 Playwright Chromium 时走服务端 longshot；**轨 2（默认可用）**：缺失或启动失败时自动切到 html2canvas，用户无需再次选择，文案不提 pip |
| **D-INS-04** | 高级可选：设置/帮助中提供「安装高清长图组件」说明（下载官方 Chromium 包或运行一次性 bootstrap） | **P1**；不阻塞 Gate A |
| **D-INS-05** | `E_LNG_PLAYWRIGHT` 不作为终态错误展示；安装版自动进入轨 2，仅在轨 2 也失败时显示中文失败结论与重试/反馈入口 | P0 |
| **D-INS-09** | html2canvas 产物优先回传本地 Studio 写入 trip 输出目录；浏览器直接下载仅作为回传失败时的兜底 | 保持文件命名、打开文件夹、Task Dock 成功态与发群三要素一致 |

> Gate A 验收：**无 Playwright 的干净机**，用户仍能通过预览 UI 得到 PNG。  
> Gate B+：可另附「高清长图可选组件」说明，但不得成为主路径唯一依赖。
>
> **轨 2 端到端合同**：自动检测/切换 → 客户端捕获 → 写入本机输出目录 → 使用与轨 1 一致的文件名与分段/平台元数据 → Task Dock 显示「长图已保存」和发群三要素 →「在文件夹中显示」可用。技术冻结见 [IMPLEMENTATION §4.3](./IMPLEMENTATION-DESKTOP-INSTALLER-V1.md) 与 [ADR-018 D6](./adr/018-desktop-installer-layout.md)。

### 5.4 进程与窗口（F-INS-UX-SHELL）

| ID | 需求 | 优先级 |
|----|------|--------|
| **F-INS-UX-01** | `console=False`（或等价 windowed）；标准输出进日志文件 | P0 |
| **F-INS-UX-02** | 启动成功：自动 `webbrowser.open` Studio URL | P0 |
| **F-INS-UX-03** | 端口占用：自动尝试下一端口或提示「已在运行」并打开已有实例 URL | P0 |
| **F-INS-UX-04** | 提供产品内可发现的「退出 Studio」动作；退出后停止 HTTP/Job、刷新日志并释放端口；托盘 UI 可 P1 | P0 |
| **F-INS-UX-05** | 单实例：第二次启动打开已有实例 URL，不启动第二套写进程；实现可用命名 mutex + 端口状态文件或等价方案 | P0 |
| **F-INS-UX-06** | 安装、升级或卸载检测到运行实例时，提示并安全退出后继续；禁止静默覆盖运行文件 | P0 · Gate B |

---

## 6. 安装包需求（Gate B）

### 6.1 安装器（F-INS-SETUP）

| ID | 需求 | 优先级 |
|----|------|--------|
| **F-INS-SETUP-01** | Windows x64 安装包（Inno Setup 推荐；允许等价工具） | P0 |
| **F-INS-SETUP-02** | 默认安装到 `%LOCALAPPDATA%\Programs\Travelogue\`（**每用户、免管理员**优先） | P0 |
| **F-INS-SETUP-03** | 默认创建开始菜单快捷方式「Travelogue Studio」 | P0 |
| **F-INS-SETUP-04** | 可选创建桌面快捷方式，默认不勾选 | P1 |
| **F-INS-SETUP-05** | 卸载程序：移除程序文件与快捷方式；**用户 trips/配置默认保留**，卸载页提供「同时删除我的游记数据」勾选（默认不勾） | P0 |
| **F-INS-SETUP-06** | 安装结束可勾选「立即打开 Studio」 | P0 |
| **F-INS-SETUP-07** | 安装包显示版本号与出版信息（发布者名称） | P0 |
| **F-INS-SETUP-08** | 桌面快捷方式默认不勾选；开始菜单入口默认创建 | P0 |
| **F-INS-SETUP-09** | 删除用户数据前显示绝对路径并二次确认；只删除带 ownership marker 的默认用户目录，不跟随 junction/symlink，不删除环境变量指向的外部目录 | P0 |

### 6.2 升级（F-INS-UP）

| ID | 需求 | 优先级 |
|----|------|--------|
| **F-INS-UP-01** | V1：覆盖安装保留 `%LOCALAPPDATA%\Travelogue\` 下用户数据 | P0 |
| **F-INS-UP-02** | 不自动迁移旧「exe 旁 trips」；若检测到旧便携 `trips/`，帮助文案提示手动拷贝（P1 可做检测横幅） | P1 |
| **F-INS-UP-03** | 不做静默后台自动更新 | —（非目标） |

---

## 7. 首启与帮助（F-INS-FIRST）

| ID | 需求 | 优先级 |
|----|------|--------|
| **F-INS-FIRST-01′** | 首启首页主 CTA 进入导入向导；向导 pick **必须**同屏提供一等「试用示例相册」（与选文件夹并列次主）。首页**不要求**并排第二主按钮。**（[PRD-FTUE-OPTIMIZATION-V1](./PRD-FTUE-OPTIMIZATION-V1.md) v1.1 附录 C；原 F-INS-FIRST-01 废止）** | P0 |
| **F-INS-FIRST-02** | 复用 [PRD-HELP-ONBOARDING-V1](./PRD-HELP-ONBOARDING-V1.md) 主链触达；**不**另造安装专用全屏向导（除非 Gate A 实测卡住） | P0 |
| **F-INS-FIRST-03** | 包内 `使用说明.txt`：系统要求、如何打开、数据位置、长图说明、如何退出、如何反馈 | P0 |
| **F-INS-FIRST-04** | 失败页：无法绑端口 / 浏览器未开 → 日志路径 + 反馈指引 | P0 |

---

## 8. 分发、签名与发布

### 8.1 发布渠道（F-INS-REL）

| ID | 需求 | 优先级 |
|----|------|--------|
| **F-INS-REL-01** | 邀请制 Release（或等价受控分发）上传：portable zip + Setup exe + SHA256SUMS + 发行说明；Gate C 后才允许公开稳定下载 | P0 · Gate B/C |
| **F-INS-REL-02** | 发行说明含：版本、系统要求、已知问题（SmartScreen）、长图降级说明 | P0 |
| **F-INS-REL-03** | Gate A 前官网保持「申请种子测试/加入通知」；Gate A 为「申请 Windows 内测」；Gate B 最多二级入口「Windows 测试版」；Gate C 后首页主 CTA 才改「立即下载」 | P0 |
| **F-INS-REL-04** | 国内镜像（Gitee / 对象存储）**P2**，不阻塞 Gate B | P2 |
| **F-INS-REL-05** | 冻结唯一反馈入口、负责人、响应时限和问题模板；记录版本、Windows、渠道、失败步骤、日志授权与支持分钟数 | P0 · Gate A |
| **F-INS-REL-06** | 许可、NOTICE、demo 图片授权与发布者主体未明确前，只允许内部构建，不允许公开 Release | P0 |

### 8.2 代码签名（F-INS-SIGN）

| ID | 需求 | 优先级 |
|----|------|--------|
| **F-INS-SIGN-01** | Gate C：Authenticode 签名 Setup 与主 exe；校验证书链、可信时间戳、发布者名称和下载后签名完整性 | P0 · Gate C |
| **F-INS-SIGN-02** | Gate A/B 未签名时，说明中必须写清：「若 Windows 提示未知应用 → 更多信息 → 仍要运行」 | P0 |
| **F-INS-SIGN-03** | 证书采购与续费流程记入运维备忘（不进本 PRD 细节） | — |

> 签名不等于立即建立 SmartScreen 信誉。Gate C 的合同是“身份可验证、剩余警告如实披露、无不可绕过的硬失败”，不是承诺所有新机器均无黄页。

### 8.3 构建可复现（F-INS-CI）

| ID | 需求 | 优先级 |
|----|------|--------|
| **F-INS-CI-01** | 文档化干净构建步骤（Python 版本、`pip install ".[desktop]"`、build 脚本） | P0 |
| **F-INS-CI-02** | `scripts/smoke_studio_portable.py`（或 bat）：在临时目录解压 → 启停 → HTTP 探活 → demo import 或最小 API 探活 | P0 |
| **F-INS-CI-03** | （期望）CI artifact 出 portable zip；签名步骤可人工 | P1 |

---

## 9. 数据、隐私与目录布局

### 9.1 目录约定（D-INS-06）

**安装模式（默认）**

```text
%LOCALAPPDATA%\Programs\Travelogue\     # 程序文件（卸载可删）
%LOCALAPPDATA%\Travelogue\
  ├── trips\                            # 游记工程
  ├── config.yaml                       # 用户配置
  ├── logs\
  └── cache\                            # 可选
```

**便携模式（固定旁路文件触发）**

```text
<解压目录>\
  ├── TravelogueStudio.exe
  ├── _internal\ …
  ├── portable.flag                      # 固定模式标记
  ├── trips\                            # 默认可写于此
  ├── config.yaml
  ├── logs\
  └── 使用说明.txt
```

| ID | 需求 |
|----|------|
| **D-INS-06** | 安装模式数据与程序分离；便携模式数据随目录 |
| **D-INS-07** | `portable.flag` 决定便携模式；环境变量 `TRAVELOGUE_TRIPS_DIR` / `TRAVELOGUE_USER_DATA` 仅作高级路径覆盖，不改变卸载 ownership |
| **D-INS-08** | 隐私文案：照片默认不离开本机；LLM 仅在用户配置 Key 后可选外发（与现网一致） |
| **D-INS-10** | 安装版版本统一为 `0.2.0-beta.N`；Git tag `v0.2.0-beta.N`；Windows FileVersion 映射为 `0.2.0.N`；Portable / Setup / VERSION / Release 共用单一版本源 |

### 9.2 卸载

- 默认保留 `%LOCALAPPDATA%\Travelogue\` 下 trips、config、logs、cache  
- 勾选「删除我的游记数据与设置」后，显示绝对路径并二次确认；仅删除存在 ownership marker 的默认目录  
- 不删除环境变量指向的外部目录；不跟随 junction/symlink  
- 便携包：删除解压目录即卸载；说明中写明  

**统一隐私文案**：

> Travelogue 默认在本机处理照片和游记，不要求注册，也不会将照片上传给 Travelogue。若你主动启用第三方 LLM，相关内容将直接发送给所选服务商，并受其隐私政策约束。卸载默认保留游记、配置、日志和缓存；仅在你明确勾选并二次确认后删除。

---

## 10. 工程约束与对齐

| 项 | 约束 |
|----|------|
| **技术选型** | 继续 PyInstaller + 现有 `travelogue.desktop.launcher`；不引入新桌面壳除非 Gate A 失败且评审改判 |
| **Studio 协议** | 默认仍绑 `127.0.0.1`；**禁止**安装版默认 `--allow-lan` 对公网暴露 |
| **能力面** | 与源码版 Studio 功能对齐（导入 / 书架 / 预览 / 长图）；安装版可隐藏模板治理等 internal 入口 |
| **架构债** | frozen 路径修复优先于新 UI；参考 [PRD-ARCH-OPTIMIZATION.md](./PRD-ARCH-OPTIMIZATION.md) R-16 |
| **测试** | 单元测保持；**新增** portable 冒烟；长图在无 Playwright 机验收降级 |

### 10.1 建议修订现有决策（写入实施时）

| 原决策 | V1 修订 |
|--------|---------|
| spec `console=True` | → `False` + 文件日志 |
| spec onefile | → onedir 为主产物 |
| `default_trips_dir` = exe 旁 | → 安装模式改 LocalAppData；便携保留 exe 旁 |
| M11「仅 backlog 骨架」 | → 本 PRD 定义为可发布里程碑 |
| Studio 仅服务端 longshot | → Playwright 优先 + html2canvas 自动降级 |
| frozen worker 使用源码式 `-m` / spawn | → 明确 launcher worker 路由 + `freeze_support()` |
| 退出与单实例 P1 | → 升为 Gate A/B P0 生命周期合同 |

---

## 11. 验收标准（AC 合同）

> 完整步骤与环境矩阵见 [ACCEPTANCE-DESKTOP-INSTALLER-V1.md](./ACCEPTANCE-DESKTOP-INSTALLER-V1.md)。环境至少覆盖 Windows 10/11、标准用户、无 Python、无 Playwright、中文/空格/OneDrive 路径、离线启动、升级、运行中卸载与 Defender/SmartScreen。

### 11.1 Gate A · 绿色包

| ID | 场景 | 期望 |
|----|------|------|
| **AC-INS-A01** | 无 Python 的 Windows 10/11 干净机，解压 portable zip | 无报错依赖缺失弹窗（或有中文修复指引） |
| **AC-INS-A02** | 双击 exe | 无 cmd 黑窗；浏览器打开 Studio |
| **AC-INS-A03** | 首页 → 向导 → 点击试用示例 | ≥4 张 demo 跑通至预览页（路径对齐 F-INS-FIRST-01′） |
| **AC-INS-A04** | 选择自己的 JPG/PNG 文件夹（20～100 张） | 无指导导入成功并预览 |
| **AC-INS-A05** | 无 Playwright | 自动降级并经同一「长图」入口保存 PNG；成功态、打开文件夹和发群三要素可用；文案不提 pip |
| **AC-INS-A06** | 将整个目录拷到另一路径再开 | 仍能启动（相对路径/ bundle 正确） |
| **AC-INS-A07** | 故意缺失 templates 模拟 | 失败有中文 + 日志，不静默闪退 |
| **AC-INS-A08** | 同一机器第二次双击 exe | 打开已有实例 URL，不启动第二套写进程 |
| **AC-INS-A09** | 产品内点「退出 Studio」 | HTTP/Job 安全停止、日志刷新、端口释放 |
| **AC-INS-A10** | frozen 选择文件夹与启动导入子进程 | pick-folder worker 与 spawn 正常，不重复启动主程序、不静默挂死 |
| **AC-INS-A11** | 5 名合格非开发者使用自有照片 | ≥4 人独立保存并找到 PNG，且能说明如何发群 |

### 11.2 Gate B · 安装包

| ID | 场景 | 期望 |
|----|------|------|
| **AC-INS-B01** | 运行 Setup（标准用户、非管理员） | 安装成功 |
| **AC-INS-B02** | 开始菜单启动 | 同 A02–A05 |
| **AC-INS-B03** | 关闭后再次打开 | 书架仍见上次 trip（数据在 LocalAppData） |
| **AC-INS-B04** | 卸载（不勾选删数据） | 程序移除；trips 仍在 |
| **AC-INS-B05** | 卸载（勾选删数据） | trips/config 删除 |
| **AC-INS-B06** | Releases 产物 SHA256 与 SUMS 一致 | 校验通过 |
| **AC-INS-B07** | 卸载选择删数据 | 显示绝对路径并二次确认；只删除 ownership marker 默认目录，不跟随链接、不删外部覆盖目录 |
| **AC-INS-B08** | Studio 运行中覆盖安装或卸载 | 识别运行实例，安全退出后继续；不静默覆盖 |
| **AC-INS-B09** | N≥15 邀请制用户完整旅程 | 安装启动≥90%；独立首篇≥60%；完成者中位≤30分钟；支持中位≤15分钟/人、P90≤30分钟/人 |
| **AC-INS-B10** | 覆盖安装后再次启动 | 书架、配置和既有 trips 保留 |

### 11.3 Gate C · 签名

| ID | 场景 | 期望 |
|----|------|------|
| **AC-INS-C01** | 签名属性可见 | 发布者名称正确 |
| **AC-INS-C02** | Setup 与主 exe 签名检查 | 证书链、可信时间戳、发布者与下载后签名完整性全部通过 |
| **AC-INS-C03** | ≥5 台 Windows 10/11 真机下载运行 | 无不可绕过的硬失败；SmartScreen 剩余提示已如实披露 |
| **AC-INS-C04** | 官网/README/安装器/Release 对拍 | 许可、隐私、版本、价格、数据位置和支持入口完全一致 |

### 11.4 非功能

| ID | 项 | 期望 |
|----|----|------|
| **AC-INS-NF01** | 产物体积 | 同时记录 portable zip 下载体积、解压/安装体积；目标压缩后 ≤250MB（不含 Chromium/Torch），超标须评审 |
| **AC-INS-NF02** | 冷启动到浏览器可点 | 目标 **≤ 15s**（SSD 参考机） |
| **AC-INS-NF03** | 冒烟脚本 | 退出码 0 |

---

## 12. 里程碑与实施归属

| 里程碑 | 交付 | 预估 | 依赖 |
|--------|------|------|------|
| **M-INS-0a** | 可构建：onedir + console=False + 日志基础 + datas/版本/SHA256 | 2–3 日 | 开发 |
| **M-INS-0b** | 可启动：resource_root 收口 + user_data/portable + freeze_support/worker 路由 + 干净目录 HTTP 200 | 5–7 日 | M-INS-0a |
| **M-INS-0c** | 可走完：html2canvas 自动降级 + 去 pip 文案 + 端口/单实例/退出 + windowed 失败反馈 | 5–8 日 | M-INS-0b |
| **M-INS-1** | Gate A：portable zip + 使用说明 + 冒烟脚本 + 5 人定向测试，≥4 人完成 | 4–6 日 + 招募 | M-INS-0c |
| **M-INS-2** | Gate B：Inno 安装包 + LocalAppData + 安全卸载 + 受控 Release + N≥15 封闭公测 | 5–7 日 + 测试周期 | M-INS-1 |
| **M-INS-3** | Gate C：代码签名 + 许可/隐私/支持 SOP + ≥5 台真机 + 官网 CTA 切换 | 2–3 日 + 证书/信誉周期 | M-INS-2 |
| **M-INS-4** | （可选）高清长图可选组件 bootstrap | 2–4 日 | M-INS-1 后可并行 |

**建议实施顺序**：文档配套已就绪 → **M-INS-0a → 0b → 0c** → 冒烟 → Gate A（M-INS-1）→ Gate B（M-INS-2）→ Gate C（M-INS-3）。

**总开发工作量基线**：约 **28～42 人日**，不含用户招募、证书采购/审核、SmartScreen 信誉积累和外测日历时间。

**文档配套（已就绪 · 2026-07-14）**：

1. 本文 PRD v1.1.0（Conditional Go）  
2. [IMPLEMENTATION-DESKTOP-INSTALLER-V1.md](./IMPLEMENTATION-DESKTOP-INSTALLER-V1.md) — 任务拆解与 DoD  
3. [ACCEPTANCE-DESKTOP-INSTALLER-V1.md](./ACCEPTANCE-DESKTOP-INSTALLER-V1.md) — 冒烟 + Gate A/B/C 矩阵  
4. [ADR-018](./adr/018-desktop-installer-layout.md) — onedir · 数据目录 · worker/进程 · 长图双轨 · 退出/单实例

---

## 13. 风险与开放问题

### 13.1 风险

| ID | 风险 | 缓解 |
|----|------|------|
| **R-INS-01** | Defender 误报未签名包 | Gate A 说明；尽快 Gate C；避免 UPX（评估关闭） |
| **R-INS-02** | frozen 漏捆动态导入模块 | hiddenimports 审计 + 干净机冒烟 |
| **R-INS-03** | html2canvas 长图质量/体积差于 Playwright | 文案管理预期；P1 可选组件 |
| **R-INS-04** | 体积膨胀（pillow 等） | onedir 精简 excludes；禁捆 Torch |
| **R-INS-05** | 用户杀进程残留端口 | 单实例 + 端口探测 |
| **R-INS-06** | 中文路径 / OneDrive 桌面路径过长 | Gate A/B 真机矩阵；不能长期仅靠说明规避 |
| **R-INS-07** | frozen 下 `sys.executable -m` 与 multiprocessing spawn 重入或挂死 | `freeze_support()` + worker 入口契约 + onedir 集成测试 |
| **R-INS-08** | 误删外部 trips 或 junction/symlink 指向目录 | ownership marker + 绝对路径二次确认 + 不跟随链接 |
| **R-INS-09** | 签名后仍有 SmartScreen 黄页 | 不承诺即时信誉；披露现状并持续抽样 |
| **R-INS-10** | 本地承诺与 LLM/卸载实际行为冲突 | 使用 §9 统一隐私文案；官网/README/安装器对拍 |

### 13.2 开放问题

| ID | 问题 | 建议默认 |
|----|------|----------|
| **OQ-INS-01** | 安装是否默认创建桌面快捷方式 | **已关闭**：默认否；开始菜单默认是（D-INS-11） |
| **OQ-INS-02** | 是否做托盘图标驻留 | Gate A **不做**；Gate B 视反馈 |
| **OQ-INS-03** | 高清长图可选组件分发方式 | 独立 zip vs 首启下载；M-INS-4 再决 |
| **OQ-INS-04** | 版本号与 `pyproject` 0.1.0 如何对齐 | **已关闭**：安装版 `0.2.0-beta.N`；FileVersion `0.2.0.N`（D-INS-10） |
| **OQ-INS-05** | 是否支持「便携模式开关」安装版互转 | **已关闭**：V1 不互转；`portable.flag` 固定便携模式 |
| **OQ-INS-06** | HEIC 是否进默认包 | P1 倾向捆绑 `pillow-heif`（体积可接受则进 Gate B） |
| **OQ-INS-07** | 许可与发布者主体 | **Gate B 外发阻塞**：LICENSE/EULA、NOTICE、demo 授权与 Publisher 必须拍板 |

### 13.3 评审冻结决策

| 决策 | 结论 |
|------|------|
| **D-INS-09** | html2canvas 优先回传 Studio 写盘；浏览器下载仅兜底 |
| **D-INS-10** | 版本统一为 `0.2.0-beta.N`；Windows FileVersion `0.2.0.N` |
| **D-INS-11** | 开始菜单默认创建；桌面快捷方式默认不勾选 |
| **D-INS-12** | `portable.flag` 为便携模式唯一产品判定；环境变量只覆盖路径 |
| **D-INS-13** | 产品内“退出 Studio”、单实例和运行中安装/卸载均为 P0 |
| **D-INS-14** | Gate B 为邀请制测试；Gate C 才允许官网公开下载主推 |
| **D-INS-15** | Gate A 5 人 ≥4 完成；Gate B N≥15、安装≥90%、独立完成≥60%、中位≤30分钟 |

---

## 附录 A · 现状盘点（实施对照）

| 已有 | 路径/位置 | 本 PRD 动作 |
|------|-----------|-------------|
| PyInstaller spec | `packaging/travelogue-studio.spec` | 改 onedir · console · datas 审计 |
| 构建脚本 | `scripts/build-studio-exe.bat` | 输出 zip + VERSION |
| Launcher | `travelogue/desktop/launcher.py` | 用户数据目录 · 日志 · 单实例 |
| Bundle helpers | `travelogue/desktop/bundle.py` · `paths.py` | **收口全站资源路径** |
| Demo album | `templates/studio/assets/demo-album/` | 确保进 datas |
| 可选依赖 | `pyproject.toml` `[desktop]` | 构建文档写明 |
| 开发 bat | `scripts/start-studio.bat` | 保留给开发者；安装版不依赖 |

---

## 附录 B · 用户可见文案（初稿）

### B.1 使用说明.txt（结构）

1. 系统要求：Windows 10/11 64 位；Chrome/Edge 建议  
2. 如何打开：双击 `TravelogueStudio.exe`  
3. 第一次：点「试用示例」或选择照片文件夹  
4. 长图：在预览中「保存长图」；若提示高清组件未安装，可用当前方式保存  
5. 我的数据在哪：`按 Win+R 输入 %LOCALAPPDATA%\Travelogue`（安装版）或解压目录下 `trips`（绿色版）  
6. 若 Windows 拦截：仅在确认来源与 SHA256 后，按邀请说明选择「更多信息 → 仍要运行」  
7. 如何退出：在 Studio 内选择「退出 Studio」  
8. 反馈：使用发行说明中唯一反馈入口；发送日志前需主动同意  

### B.2 SmartScreen 旁注（发行说明）

> 本应用默认在本机处理照片，不强制联网。Gate A/B 测试包可能尚未签名，仅向受邀用户分发；请先确认邀请来源与 SHA256，再决定是否继续运行。Gate C 的 Setup 与主程序将提供 Authenticode 签名和可信时间戳；新证书仍可能触发 SmartScreen 提示，实际状态会在发行说明中如实披露。

---

## 附录 C · 目标 ↔ 需求 ↔ AC 映射

| 目标 | 需求簇 | AC |
|------|--------|-----|
| G-INS-01 | PACK · PATH · FIRST · SETUP | A01–A03 · B01–B02 · B09 |
| G-INS-02 | LNG · 真人主路径 | A04–A05 · A11 · B09 |
| G-INS-03 | UX-SHELL | A02 |
| G-INS-04 | DATA · SETUP 卸载 | B03–B05 |
| G-INS-05 | REL · CI | B06 · NF03 |
| G-INS-06 | SIGN | C01–C04 |
| G-INS-07 | REL · FIRST · 支持运营 | A11 · B09 |

---

## 附录 D · 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| **v1.1.1** | **2026-07-14** | 交叉链接落地：ADR-018 · IMPLEMENTATION · ACCEPTANCE 已建；文档配套从「待建」改为「就绪」；下一步进入 M-INS-0a 编码 |
| **v1.1.0** | **2026-07-14** | 跨职能评审 Must-Fix 回写：Conditional Go；统一自有照片成功口径；长图双轨端到端合同；退出/单实例升 P0；安全删除；版本与便携模式冻结；Gate B 改邀请制、Gate C 才公开；补许可/支持/真人门禁；M-INS-0 拆 0a/0b/0c；总工期调整为 28～42 人日 |
| **v1.0.0** | 2026-07-11 | 首版：绿色包 + 安装包双形态；三道门；frozen/长图/数据目录/签名范围锁定 |

---

*本文档定义 Travelogue Windows 桌面可安装版 V1。v1.1.x 已获 Conditional Go，仅批准 M-INS-0；文档配套已就绪，下一步按 IMPLEMENTATION 启动 M-INS-0a（onedir 打包骨架），冒烟通过后方可约 Gate A。*
