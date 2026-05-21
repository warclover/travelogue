# Travelogue · 游记智能体

> 照片 + 可选短视频 → 智能策展与短文案 → **杂志风 HTML 游记包**（zip 离线打开）。本地优先，模板驱动，Agent 只改 `trip.json`。

| 属性 | 内容 |
|------|------|
| **阶段** | P0 本地工坊（MVP 开发中） |
| **主模板** | `visual-journal` v0.2.1 |
| **文档入口** | [docs/README.md](docs/README.md) |

---

## 快速链接

| 你想… | 去看 |
|--------|------|
| 了解项目为什么做 | [docs/CHARTER.md](docs/CHARTER.md) |
| 看功能与需求 | [docs/PRD-MVP.md](docs/PRD-MVP.md) |
| 看 Agent 怎么拆 | [docs/AGENT-ARCHITECTURE.md](docs/AGENT-ARCHITECTURE.md) |
| 本地跑起来 | [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) |
| CLI / 校验规范 | [docs/CLI-SPEC.md](docs/CLI-SPEC.md) · `python scripts/validate_trip.py` |
| 全部文档索引 | [docs/README.md](docs/README.md) |
| 预览版式长什么样 | [templates/visual-journal/golden.html](templates/visual-journal/golden.html) |
| MVP 算不算做完 | [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md) |

---

## 仓库结构（目标）

```
travelogue/
├── docs/                 # P0 立项与开发文档
├── schemas/trip.schema.json
├── templates/visual-journal/   # manifest + golden 金样例
├── scripts/              # 工具脚本（如生成 golden）
├── trips/{tripId}/       # 运行时游记项目（gitignore）
│   ├── trip.json
│   ├── source/
│   ├── assets/
│   └── index.html
└── config.yaml.example   # 本地配置样例（见 DEVELOPMENT.md）
```

---

## 预览金样例

在浏览器中打开：

`templates/visual-journal/golden.html`

顶栏可切换手机 9:16 / Web 16:9 布局预览。

**Web 双引擎对比（legacy vs screens）**：

| 文件 | 引擎 |
|------|------|
| [golden.html](templates/visual-journal/golden.html) | legacy（`media-row` / `media-scroll`） |
| [golden-web-screens.html](templates/visual-journal/golden-web-screens.html) | screens（16:9 舞台宫格） |

---

## Web 排版：legacy 与 screens 对比

同一本游记可并排渲染两种 Web 引擎（需先对 **Web** 排版）：

```powershell
# 1. 写入 screens[]（会改 trip.json）
python -m travelogue layout trips\<tripId>\trip.json --layout web --web-layout screens

# 2. 各出一份 HTML
python -m travelogue render trips\<tripId>\trip.json --web-layout legacy --index-name index-legacy.html
python -m travelogue render trips\<tripId>\trip.json --web-layout screens --index-name index-screens.html

# 或一条脚本（Windows）
.\scripts\compare-web-layout.ps1 trips\<tripId> -Serve
```

说明：

- 仅 `render --web-layout screens` **不会**生成 `screens[]`，须先 `layout --web-layout screens`。
- `layoutEngine=screens` 时 **不加载**「保存长图」脚本（DOM 尚未适配）；legacy 仍默认开启。
- `config.yaml`（见 `config.yaml.example`）：默认 `layout.web_layout_engine: screens`、`screen_plan_scope: day`、`mixed_proximity_seconds: 12`。
- `from-album` 的 `tripId` 优先用相册目录名（如 `kyoto-2025`），中文标题会 fallback 为 `demo-<hash>`。

真图 Demo 若要走 screens：`python -m travelogue demo "<相册>" --title "..." --layout web`，再执行 layout/render 的 `--web-layout screens`（见上）。

---

## 真图 Demo（相册 → HTML）— 一条命令

与正式管线相同：`ingest` → `curate`（含排版）→ `render`（含保存长图）。

### CLI 怎么敲（Windows）

`pip install -e .` 后若 **`travelogue` 命令找不到**（Scripts 目录不在 PATH），请一律用：

```powershell
python -m travelogue …
```

等价于 `python -m travelogue.cli …`。下文示例用 **`python -m travelogue`**；若你的环境已配置 PATH，也可直接写 `travelogue`。

```powershell
cd C:\Users\xiafe\Projects\travelogue
pip install -e ".[dev]"
copy config.yaml.example config.yaml   # 可选

# 预览（ingest → curate → render）
python -m travelogue demo "D:\Photos\kyoto-2025" --title "雨后京都" --place 京都 --layout mobile

# 一键出可分享 zip（含 lock → narrate → export）
python -m travelogue demo "D:\Photos\kyoto-2025" --title "雨后京都" --place 京都 --publish

cd trips\demo-雨后京都
python -m http.server 8766
# http://127.0.0.1:8766/index.html
```

- 至少 **4 张** JPG/PNG/WebP（HEIC：`pip install pillow-heif`）
- 默认 `trips/demo-{标题slug}/`；已存在时用 `--force` 覆盖
- `--publish` 自动确认隐私并剥离 EXIF；zip 在 trip 目录下 `trip-{id}.zip`
- 分步发布：`python -m travelogue lock … structure` → `narrate` → `export --confirm-privacy`
- 已有 trip：`python -m travelogue run <tripId> --from lock_structure --until exported --confirm-privacy`
- 根目录 `config.demo.yaml` 存在时 **demo 自动加载**（更快 WebP 档位）
- 验收：`python -m travelogue demo verify`
- Windows 脚本：`.\scripts\demo.ps1 "相册路径" -Title "雨后京都"`（内部同样用 `python -m travelogue`）

---

## 技术栈（计划）

- **Python 3.11+**：ingest、策展规则、编排 CLI  
- **Handlebars（或同类）**：`trip.json` → HTML  
- **ffmpeg**：短视频循环片段  
- **LLM API**：叙事填槽（可配置）  

详见 [docs/TECH-ARCHITECTURE.md](docs/TECH-ARCHITECTURE.md)。

---

## 许可证

待定（MVP 自用阶段未发布）。
