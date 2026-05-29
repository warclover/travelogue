# Travelogue · 游记智能体

> 照片 + 可选短视频 → 智能策展与短文案 → **杂志风 HTML 游记** · **预览 + 微信长图分享**  
> MVP 管线已完成；**Phase 2** 重点：非开发者可用的 Studio 工作台 + 服务端长图。

| 属性 | 内容 |
|------|------|
| **阶段** | Phase 2「可分享体验」；Phase 3 Curate 聚类；Phase 4 **编辑意图**（[PRD-PHASE4.md](docs/PRD-PHASE4.md)） |
| **主模板** | `visual-journal` v0.2.1 |
| **文档入口** | [docs/README.md](docs/README.md) |

---

## 快速链接

| 你想… | 去看 |
|--------|------|
| **Phase 2 产品与任务** | [docs/PRD-PHASE2.md](docs/PRD-PHASE2.md) · [docs/IMPLEMENTATION-PHASE2.md](docs/IMPLEMENTATION-PHASE2.md) |
| **Phase 3 Curate 聚类（原生算法）** | [docs/PRD-PHASE3.md](docs/PRD-PHASE3.md) · [docs/adr/007-native-clustering.md](docs/adr/007-native-clustering.md) |
| **Phase 4 编辑意图（杂志心智）** | [docs/PRD-PHASE4.md](docs/PRD-PHASE4.md) · [docs/IMPLEMENTATION-PHASE4.md](docs/IMPLEMENTATION-PHASE4.md) |
| Phase 2 验收 | [docs/ACCEPTANCE-PHASE2.md](docs/ACCEPTANCE-PHASE2.md) |
| MVP 需求（已冻结） | [docs/PRD-MVP.md](docs/PRD-MVP.md) |
| 分享策略（长图 vs 小程序） | [docs/SHARING.md](docs/SHARING.md) |
| 本地跑起来 | [docs/WORKSHOP.md](docs/WORKSHOP.md) · [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) |
| 了解项目为什么做 | [docs/CHARTER.md](docs/CHARTER.md) |
| CLI / 校验规范 | [docs/CLI-SPEC.md](docs/CLI-SPEC.md) · `python scripts/validate_trip.py` |
| 全部文档索引 | [docs/README.md](docs/README.md) |
| 预览版式长什么样 | [templates/visual-journal/golden.html](templates/visual-journal/golden.html) |

---

## 快速开始（Phase 2 · 推荐）

**非开发者**：双击 [`scripts/start-studio.bat`](scripts/start-studio.bat)（需已 `pip install -e .`）。

```powershell
cd C:\Users\xiafe\Projects\travelogue
pip install -e ".[dev]"

# 或命令行
python -m travelogue studio
python -m travelogue studio --pick-folder "D:\Photos\某次旅行"

# 长图（默认 scale=1；--scale 2 高清）
python -m travelogue export-longshot trips\<tripId>
```

相册默认 **≤250 张**；浏览器 **Chrome/Edge 90+（Windows）**。

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
