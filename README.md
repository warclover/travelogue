# Travelogue · 画册智能体

> 本地照片（+ 可选短视频）→ 智能聚类 / 排版 / 挑片 / 装帧 → **杂志风 HTML 画册**，一键出 **微信长图 / 小红书 / 公众号图文 / 朋友圈**。
> 全流程本机运行，**默认无需 LLM Key**（本机文案 stub）；配置 Key 后可解锁「杂志感」AI 文案。

| 属性 | 内容 |
|------|------|
| **形态** | Studio 网页工作台（`python -m travelogue studio`） · Windows 桌面安装版 · 开发者 CLI |
| **当前用户面** | **v2 Bento 首页**为唯一主入口（M21 已切主站）；**默认无 AI 面**（NAS）——先把纯照片长图做到能放心发朋友圈，AI 文案作为可选升级项 |
| **核心管线** | `ingest`（摄入/挑片/RAW 拦截）→ `cluster`（场景+地理事件聚类）→ `curate`（选片/分章/智能排版）→ `narrate`（文案，默认 stub）→ `render`（HTML）→ `export`（长图/多平台/批量） |
| **主模板** | `visual-journal`；Web 端排版走智能排版引擎（LTE 模板 + MCS 拼图 + 可选 LSE 策略层） |
| **文档入口** | [docs/README.md](docs/README.md)（**现行导读**在文档顶部，其余为历史 Phase 存档） |

---

## 快速链接

| 你想… | 去看 |
|--------|------|
| **向陌生人或用户介绍本项目** | [docs/项目说明手册.md](docs/项目说明手册.md) |
| **了解项目为什么做** | [docs/CHARTER.md](docs/CHARTER.md) |
| **看现行架构 / 分层约束** | [docs/TECH-ARCHITECTURE.md](docs/TECH-ARCHITECTURE.md) |
| **本地跑起来 / 开发调试** | [docs/WORKSHOP.md](docs/WORKSHOP.md) · [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) |
| **CLI 命令契约** | [docs/CLI-SPEC.md](docs/CLI-SPEC.md) · `python scripts/validate_trip.py` |
| **当前版用户面合同（默认无 AI）** | [docs/PRD-NO-AI-SURFACE-V1.md](docs/PRD-NO-AI-SURFACE-V1.md) |
| **Studio 首页 v2 / M21 路由** | [docs/studio-homepage-v2/M21-ROUTING.md](docs/studio-homepage-v2/M21-ROUTING.md) |
| **导出与分享（长图/多平台/批量）** | [docs/PRD-LONGSHOT-2.0.md](docs/PRD-LONGSHOT-2.0.md) · [docs/PRD-EXPORT-CARD-COMPOSE-V1.md](docs/PRD-EXPORT-CARD-COMPOSE-V1.md) · [docs/PRD-BATCH-EXPORT-MULTISELECT-V1.md](docs/PRD-BATCH-EXPORT-MULTISELECT-V1.md) |
| **智能排版 / 拼图 / 模板体系** | [docs/PRD-PHASE17-layout-strategy-engine.md](docs/PRD-PHASE17-layout-strategy-engine.md)（LSE）· [docs/PRD-PHASE16-layout-template-engine.md](docs/PRD-PHASE16-layout-template-engine.md)（LTE） |
| **封面装帧 / Bookends** | [docs/PRD-COVER-STYLES-V6.md](docs/PRD-COVER-STYLES-V6.md) · [docs/PRD-BOOKENDS-ENGINE-V1.md](docs/PRD-BOOKENDS-ENGINE-V1.md) |
| **桌面安装版** | [docs/PRD-DESKTOP-INSTALLER-V1.md](docs/PRD-DESKTOP-INSTALLER-V1.md) |
| **单轨验收入口** | [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md) |
| **文档状态机（现行 / 存档）** | [docs/DOC-STATUS.md](docs/DOC-STATUS.md) |
| **全部文档索引** | [docs/README.md](docs/README.md) |

> 项目已迭代超过 20 个 Phase 与数十个专项 PRD，历史文档均保留在 `docs/` 供考古；**日常只需从 [docs/README.md](docs/README.md) 顶部「现行导读」进入即可**，不必按 Phase 顺序通读。

---

## 快速开始（三步 · Studio 路径）

1. **安装**：`pip install -e ".[dev]"`（建议 Python 3.11+ · 虚拟环境）
2. **启动**：`python -m travelogue studio`（或双击 [`scripts/start-studio.bat`](scripts/start-studio.bat)）
3. **打开**：浏览器访问 `http://127.0.0.1:8766/` →「开始制作」→ 可选「用示例照片试一次」

```powershell
cd C:\Users\xiafe\Projects\travelogue
pip install -e ".[dev]"
python -m travelogue studio
# 可选：指定相册 / 空态狗粮
# python -m travelogue studio --pick-folder "D:\Photos\某次旅行"
# python -m travelogue studio --trips-dir $env:TEMP\travelogue-ftue-trips --port 8771
```

相册默认 **≤250 张**；浏览器 **Chrome/Edge 90+（Windows）**。默认**无需任何 API Key**即可完成导入→预览→出图；HEIC / vision（人脸/CLIP）等可选依赖见 [docs/WORKSHOP.md](docs/WORKSHOP.md)。

非开发者可直接下载**绿色便携包 / Windows 安装包**，双击运行、无需 Python，见 [Desktop Installer](docs/PRD-DESKTOP-INSTALLER-V1.md)。

<details>
<summary>开发者深链 · Studio 路由 / 管理页 / CLI 出图</summary>

| URL | 说明 |
|-----|------|
| **`http://127.0.0.1:8766/`** | 默认 **v2** Bento 首页（书架 + Import Wizard） |
| **`/classic`** | deprecated 应急 classic（冻结快照，不再迭代） |
| **`/templates-admin`** | 模板 / LTE / LSE 治理控制台（internal） |
| **`/lse-flags-admin`** | 智能排版能力开关（LSE capabilities · 写 `config.yaml`） |
| **`/__travelogue/*`** | Studio 声明式路由表（`web/studio_dispatch.py`），trip 增删查改、cohort、模板路由等 API |

```powershell
# 服务端长图（Playwright）
python -m travelogue export-longshot trips\<tripId> --scale 2

# Longshot 2.0 · 多平台导出（朋友圈 / 小红书 / 公众号 / 单张海报等）
python -m travelogue export-longshot trips\<tripId> --platform xiaohongshu
```

Studio 面板同样支持**多平台勾选批量导出**（Task Dock 清单化进度，见 [PRD-BATCH-EXPORT-MULTISELECT-V1](docs/PRD-BATCH-EXPORT-MULTISELECT-V1.md)）。

</details>

---

## 核心能力一览

| 环节 | 说明 |
|------|------|
| **摄入** | EXIF/朝向/去重（phash + 连拍）· RAW 检测拦截 · 人脸检测 · 低分辨率相对阈值剔除 · 智能挑选（P9 质量闸口，可关） |
| **聚类** | 地理事件分段（自适应 gap）+ 场景聚类（HDBSCAN/DBSCAN）+ 智能分镜（Smart Shot Grouping） |
| **策展/选片** | 章节划分、featured/精选加权、高光时刻池（EXIF 角标）、美食/杂物组屏降权 |
| **智能排版** | LTE 模板引擎（pattern 注册）+ MCS 拼图（equal-grid 等权合同默认开）+ LSE 策略层（评分/节奏/多样性，默认关闭以保稳态） |
| **封面与装帧** | Cover Style Engine V6（多款开场皮肤 + Studio 可选）+ Bookends（封面–封底成对约束与锁定） |
| **文案** | 默认**本机 stub**（零依赖）；可在 Studio「设置 → 模型API 配置」粘贴一把通义百炼 Key，解锁杂志文案和封面字体 |
| **渲染** | Handlebars → HTML；Web 端 `screens`（16:9 舞台）引擎为主，兼容 legacy |
| **导出/分享** | 服务端长图（Playwright）· Longshot 2.0 多平台（朋友圈/小红书/公众号/…）· 3:4 卡片统一管线（画册/小红书/单张海报共用模板库）· 批量多选导出 |
| **桌面分发** | PyInstaller 打包的 Windows 安装版 / 绿色便携包，无需 Python 环境 |

---

## 开发者路径（CLI · 阶段化管线）

Studio 背后走同一套管线；CLI 可分阶段调用，便于调试与自动化：

```powershell
pip install -e ".[dev]"

# 一键预览（ingest → cluster → curate → narrate → render）
python -m travelogue demo "D:\Photos\kyoto-2025" --title "雨后京都" --place 京都

# 单 trip 预览 + inline edit
python -m travelogue serve trips\<tripId>

# 分阶段：trip new → curate → narrate → render → export
python -m travelogue trip new kyoto-2025-04 --from "D:\Photos\kyoto-2025"
python -m travelogue curate kyoto-2025-04
python -m travelogue narrate kyoto-2025-04
python -m travelogue render kyoto-2025-04
python -m travelogue export kyoto-2025-04 --confirm-privacy
```

- 至少 **4 张** JPG/PNG/WebP（HEIC：`pip install pillow-heif`）
- 完整命令契约见 [docs/CLI-SPEC.md](docs/CLI-SPEC.md)
- 验收：`python scripts/quality_gate.py` / `pytest --fast -q`

---

## 仓库结构（实际）

```
travelogue/
├── docs/                    # 章程 + 现行导读 + 20+ Phase / 专项 PRD 存档（DOC-STATUS 标记 active/superseded/archive）
├── schemas/trip.schema.json # trip.json L1 结构校验
├── templates/
│   ├── visual-journal/      # 画册 Handlebars 模板 + golden 快照
│   └── studio/               # Studio 工作台前端（homepage-v2 · preview-toolbar · Task Dock · 模板/LSE 管理台）
├── travelogue/               # Python 包（cli / web / desktop / orchestrator / curation / layout_engine /
│                              #   layout_templates / cover_engine / media / vision / llm / render / export / …）
├── scripts/                  # 度量基线、质量门禁、迁移/回滚脚本（见 scripts/README.md）
├── tests/                    # unit / integration / e2e 分层测试
├── packaging/                # Windows 打包 spec（PyInstaller）
├── trips/{tripId}/           # 运行时画册项目（gitignore）
│   ├── trip.json              # 单一事实源（含 pipeline 状态机）
│   ├── source/ · assets/
│   ├── index.html
│   └── *-longshot.png         # 长图 / 多平台导出物
└── config.yaml.example       # 全量研究面配置样例（用户档见 config.user.example.yaml）
```

架构分层由 `pyproject.toml` 的 `[tool.importlinter]` 强制约束（`cli/web/desktop` → `orchestrator` → `render/export` → `services/templating` → `curation/layout_engine/layout_templates` → `media/vision/llm` → `config` → `util/types/domain/…`），详见 [docs/TECH-ARCHITECTURE.md](docs/TECH-ARCHITECTURE.md) §18。

---

## 预览金样例

在浏览器中打开：`templates/visual-journal/golden.html`（顶栏可切换手机 9:16 / Web 16:9 布局预览）。日常制作请直接用 Studio v2（`python -m travelogue studio`），golden 主要用于模板/CSS 回归对比。

| 文件 | 引擎 |
|------|------|
| [golden.html](templates/visual-journal/golden.html) | legacy |
| [golden-web-screens.html](templates/visual-journal/golden-web-screens.html) | screens（默认） |

---

## 技术栈

- **Python 3.11+**：ingest / 聚类 / 策展 / 排版 / Studio HTTP 服务
- **Handlebars（pybars3）**：`trip.json` → HTML
- **Playwright + Chromium**：服务端长图截图、多平台导出
- **Pillow**：3:4 卡片统一渲染管线（确定性路径，不依赖 Playwright）
- **scikit-learn（HDBSCAN/DBSCAN）· OpenCV**：场景聚类、人脸/构图信号（`vision` 可选依赖）
- **CLIP（open-clip-torch，可选）**：语义聚类增强
- **LLM API（通义百炼 DashScope，可选）**：一把 Key 用于杂志文案和封面字体；默认关闭走本机 stub
- **PyInstaller**：Windows 桌面安装版打包

详见 [docs/TECH-ARCHITECTURE.md](docs/TECH-ARCHITECTURE.md)。

---

## 许可证

待定（自用阶段未发布）。
