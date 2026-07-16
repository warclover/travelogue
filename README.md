# Travelogue · 游记智能体

> 照片 + 可选短视频 → 智能策展与短文案 → **杂志风 HTML 游记** · **预览 + 微信长图分享**  
> MVP 管线已完成；**Phase 2** 重点：非开发者可用的 Studio 工作台 + 服务端长图。

| 属性 | 内容 |
|------|------|
| **阶段** | Phase 2「可分享体验」；Phase 3 Curate 聚类；Phase 4 **编辑意图**；Phase 5 **整体优化**（[PRD-PHASE5.md](docs/PRD-PHASE5.md)） |
| **主模板** | `visual-journal` v0.2.1 |
| **文档入口** | [docs/README.md](docs/README.md) |

---

## 快速链接

| 你想… | 去看 |
|--------|------|
| **Phase 2 产品与任务** | [docs/PRD-PHASE2.md](docs/PRD-PHASE2.md) · [docs/IMPLEMENTATION-PHASE2.md](docs/IMPLEMENTATION-PHASE2.md) |
| **Phase 3 Curate 聚类（原生算法）** | [docs/PRD-PHASE3.md](docs/PRD-PHASE3.md) · [docs/adr/007-native-clustering.md](docs/adr/007-native-clustering.md) |
| **Phase 4 编辑意图（杂志心智）** | [docs/PRD-PHASE4.md](docs/PRD-PHASE4.md) · [docs/IMPLEMENTATION-PHASE4.md](docs/IMPLEMENTATION-PHASE4.md) |
| **Phase 5 整体优化（双路径交付）** | [docs/PRD-PHASE5.md](docs/PRD-PHASE5.md) v0.5.4 · [IMPLEMENTATION-PHASE5.md](docs/IMPLEMENTATION-PHASE5.md) |
| Phase 2 验收 | [docs/ACCEPTANCE-PHASE2.md](docs/ACCEPTANCE-PHASE2.md) |
| MVP 需求（已冻结） | [docs/PRD-MVP.md](docs/PRD-MVP.md) |
| 分享策略（长图 vs 小程序） | [docs/SHARING.md](docs/SHARING.md) |
| 本地跑起来 | [docs/WORKSHOP.md](docs/WORKSHOP.md) · [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) |
| 了解项目为什么做 | [docs/CHARTER.md](docs/CHARTER.md) |
| CLI / 校验规范 | [docs/CLI-SPEC.md](docs/CLI-SPEC.md) · `python scripts/validate_trip.py` |
| **Studio 首页 M21 路由** | [docs/studio-homepage-v2/M21-ROUTING.md](docs/studio-homepage-v2/M21-ROUTING.md) |
| 全部文档索引 | [docs/README.md](docs/README.md) |
| 预览版式长什么样 | [templates/visual-journal/golden.html](templates/visual-journal/golden.html) |

---

## 快速开始（三步 · 开发者路径）

> 非开发者安装包见 [Desktop Installer](docs/PRD-DESKTOP-INSTALLER-V1.md)。以下为本机开发启动。

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

相册默认 **≤250 张**；浏览器 **Chrome/Edge 90+（Windows）**。可选依赖（Playwright / HEIC / vision）见 [docs/WORKSHOP.md](docs/WORKSHOP.md)。

<details>
<summary>开发者深链 · Studio 路由 / 管理页 / 长图 CLI</summary>

| URL | 说明 |
|-----|------|
| **`http://127.0.0.1:8766/`** | 默认 **v2** Bento 首页 |
| **`/classic`** | deprecated 应急 classic |
| **`/v2`** | 302 → `/`（旧书签） |
| **`/templates-admin`** | 模板 / LTE / LSE 治理控制台（internal） |
| **`/lse-flags-admin`** | 智能排版能力开关（LSE capabilities · 写 `config.yaml`） |

```powershell
python -m travelogue export-longshot trips\<tripId>
python -m travelogue export-longshot trips\<tripId> --scale 2
```

门控：`TRAVELOGUE_STUDIO_HOMEPAGE_V2=on|auto|off`（默认 `on`）。详见 [docs/studio-homepage-v2/M21-ROUTING.md](docs/studio-homepage-v2/M21-ROUTING.md) · [docs/PRD-智能排版开关页.md](docs/PRD-智能排版开关页.md)。

</details>

---

## 开发者路径（MVP · 仍可用）

与正式管线相同：`ingest` → `curate` → `narrate` → `render`。

```powershell
pip install -e ".[dev]"

# 预览（ingest → curate → render）
python -m travelogue demo "D:\Photos\kyoto-2025" --title "雨后京都" --place 京都 --layout auto

# 单 trip 预览 + inline edit
python -m travelogue serve trips\<tripId>

# 高级：可分享 zip（自行托管 / 路径 B 预埋）
python -m travelogue demo "D:\Photos\kyoto-2025" --publish
```

- 至少 **4 张** JPG/PNG/WebP（HEIC：`pip install pillow-heif`）
- Windows 脚本：`.\scripts\workshop-pipeline.ps1`（见 [docs/WORKSHOP.md](docs/WORKSHOP.md)）
- 验收：`python -m travelogue demo verify`

---

## 仓库结构（目标）

```
travelogue/
├── docs/                 # MVP + Phase 2 文档
├── schemas/trip.schema.json
├── templates/
│   ├── visual-journal/   # 游记模板 + golden
│   └── studio/           # Phase 2 工作台（待实现）
├── scripts/
│   └── start-studio.bat  # 双击启动 Studio
├── trips/{tripId}/       # 运行时游记项目（gitignore）
│   ├── trip.json
│   ├── source/
│   ├── assets/
│   ├── index.html
│   └── *-longshot.png    # Phase 2 主分享物
└── config.yaml.example
```

---

## 预览金样例

在浏览器中打开：`templates/visual-journal/golden.html`

顶栏可切换手机 9:16 / Web 16:9 布局预览。

| 文件 | 引擎 |
|------|------|
| [golden.html](templates/visual-journal/golden.html) | legacy |
| [golden-web-screens.html](templates/visual-journal/golden-web-screens.html) | screens |

---

## 技术栈

- **Python 3.11+**：ingest、策展、Studio（`serve --studio`）
- **Handlebars**：`trip.json` → HTML  
- **Playwright + Chromium**：服务端长图、PDF 导出  
- **LLM API**：可选叙事（Studio 默认 stub）  

详见 [docs/TECH-ARCHITECTURE.md](docs/TECH-ARCHITECTURE.md)。

---

## 许可证

待定（MVP 自用阶段未发布）。
