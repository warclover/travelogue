# Travelogue · 开发手册

| 属性 | 内容 |
|------|------|
| **文档版本** | v0.1 |
| **阶段** | P0（实现进行中） |
| **关联** | `TECH-ARCHITECTURE.md`、`DATA-MODEL.md` |
| **更新日期** | 2026-05-19 |

---

## 1. 前置条件

| 工具 | 版本 | 用途 |
|------|------|------|
| Git | 任意 | 版本管理 |
| Python | **3.11+** | CLI 与 Agent |
| ffmpeg | 4.x+ | 短视频处理（可选至有视频素材） |
| 现代浏览器 | Chrome / Edge / Safari | 预览 golden 与输出 HTML |

**可选**：Node.js 18+（若采用 Node 渲染器）、LLM API Key。

---

## 2. 获取代码

```powershell
cd C:\Users\xiafe\projects\travelogue
git status
```

---

## 3. 配置

### 3.1 复制配置样例

```powershell
copy config.yaml.example config.yaml
```

编辑 `config.yaml`（**勿提交**）。API Key 建议只放在环境变量：

```powershell
$env:OPENAI_API_KEY = "sk-..."
```

#### narrative.scope（文案范围）

自 v0.2 起默认 `narrative.scope: frame`（仅生成 hook + epilogue，不生成中间章导语/图注）。

| 值 | 行为 |
|----|------|
| `frame` | hook + epilogue；封面不叠标题 |
| `frame_chapters` | 上述 + 首章/末章 lead |
| `full` | 全章 lead + 图注（旧版行为） |

**从旧项目升级**：若需要保留全章导语与图注，在 `config.yaml` 中显式设置 `narrative.scope: full` 后再运行 `narrate --regenerate`。`frame` 模式下 narrate 会清理 scope 不允许的中间文案（用户手动 `edited` 的字段除外）。

**二次 ingest 去重**：2026-05 起新 ingest 会写入 `assets[].contentSig`。老 trip 可先运行：

```powershell
python scripts/backfill_content_sig.py linzhi mao
```

### 3.2 环境变量（推荐）

| 变量 | 说明 |
|------|------|
| `OPENAI_API_KEY` | 或你在 config 里指定的 `api_key_env` |
| `TRAVELogue_TRIPS_DIR` | 覆盖 trips 目录（可选） |

---

## 4. Python 环境（实现落地后）

> 以下命令在 `pyproject.toml` 与 `travelogue` 包提交后生效；当前可先用于预览模板与文档。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### 4.1 Windows：`travelogue` 命令找不到

安装时 pip 可能提示：`travelogue.exe is installed in '...\Python\Scripts' which is not on PATH`。

| 方式 | 做法 |
|------|------|
| **A（推荐）** | 始终用 `python -m travelogue demo …`（或 `python -m travelogue.cli …`） |
| **B** | 把 Python `Scripts` 目录加入用户 PATH，然后新开 PowerShell 再试 `travelogue --help` |
| **C** | 使用虚拟环境并 `Activate.ps1` 后，venv 的 `Scripts` 通常在 PATH 内，可直接 `travelogue` |

查看 Scripts 路径：

```powershell
python -c "import sysconfig; print(sysconfig.get_path('scripts'))"
```

预期依赖（见 `pyproject.toml`）：`typer`、`jsonschema`、`Pillow`、`pyyaml`；可选 `pillow-heif`、`piexif`（测试）。

---

## 5. 预览金样例（无需后端）

```powershell
# 直接用浏览器打开
start templates\visual-journal\golden.html
```

或使用本地静态服务（避免部分浏览器对 file:// 限制）：

```powershell
cd templates\visual-journal
python -m http.server 8765
# 访问 http://127.0.0.1:8765/golden.html
```

重新生成 golden HTML（修改生成脚本后）：

```powershell
python scripts\gen_golden_html.py
```

---

## 6. Trip 目录约定

手动创建示例（调试 schema 用）：

```powershell
mkdir trips\demo-kyoto\source
mkdir trips\demo-kyoto\assets
```

将一份符合 [trip.schema.json](../schemas/trip.schema.json) 的 `trip.json` 放入 `trips/demo-kyoto/`。可复制 [schemas/fixtures/trip.example.json](../schemas/fixtures/trip.example.json)。

---

## 7. CLI 命令（目标接口）

实现后 Orchestrator 暴露以下子命令（名称可微调，以代码为准）：

| 命令 | Agent | 说明 |
|------|-------|------|
| `travelogue trip new <tripId> --from <folder>` | — | 建目录 + 初始 json |
| `travelogue ingest <tripId> [--batch]` | 0 | EXIF + WebP |
| `travelogue curate <tripId>` | 1 | 分章提案 |
| `travelogue lock structure <tripId>` | — | G1 确认 |
| `travelogue narrate <tripId> [--tone relaxed] [--provider stub\|deepseek\|dashscope]` | 2 | 生成文案（LLM 或 stub） |
| `travelogue llm ping [--provider deepseek]` | — | 验证 API 连通 |
| `travelogue lock copy <tripId>` | — | G2 确认 |
| `travelogue render <tripId>` | 3 | 输出 index.html |
| `travelogue export <tripId> [--confirm-privacy]` | 3 | zip + preview.jpg |
| `travelogue status <tripId>` | — | 打印 pipeline.status |
| `travelogue validate <tripId>` | — | schema + manifest |

**一条龙（实现后）**：

```powershell
travelogue trip new kyoto-2025-04 --from D:\Photos\Kyoto
travelogue ingest kyoto-2025-04
travelogue curate kyoto-2025-04
# 人工编辑 trip.json 或后续 UI → lock structure
travelogue lock structure kyoto-2025-04
travelogue narrate kyoto-2025-04
travelogue lock copy kyoto-2025-04
travelogue render kyoto-2025-04
travelogue export kyoto-2025-04 --confirm-privacy
```

---

## 8. 校验 trip.json

```powershell
pip install jsonschema
python scripts\validate_trip.py schemas\fixtures\trip.copy_locked.json --level all
python scripts\validate_trip.py trips\demo-kyoto\trip.json --level all
```

规则说明：`docs/VALIDATION-RULES.md`。

---

## 9. 预览生成的游记

```powershell
cd trips\kyoto-2025-04
python -m http.server 8766
# http://127.0.0.1:8766/index.html
```

微信测试：将 zip 发到手机解压，或用内网穿透托管静态目录（P1 见计划中的 `SHARING.md`）。

---

## 9b. 真图 Demo（相册导入）

在完整 Agent 0 ingest 之前，可用 demo 验证裁切与版式：

```powershell
travelogue demo from-album .\album --title "我的旅途" --place 京都
cd trips\demo-我的旅途
python -m http.server 8766
```

| 项 | Demo | 正式 ingest |
|----|------|-------------|
| WebP 多档 | w800 + w1600 | + w2400、cropMobile |
| EXIF | 仅排序/日期 | 完整解析 + GPS |
| 章结构 | 规则粗分 | Agent 1 策展 |
| pipeline | structure_draft | ingest_ready → … |

---

## 10. 开发顺序（建议）

| 顺序 | 任务 | 验收 |
|------|------|------|
| 1 | `TripService` 读写 + schema 校验 | validate 通过 |
| 2 | Agent 3 渲染 golden 数据 → HTML | 与 golden 视觉一致 |
| 3 | Agent 0 ingest 单文件夹 | assets + EXIF |
| 4 | Agent 1 规则策展 | 3–5 章 json |
| 5 | Agent 2 叙事 + 校验 | 文案入 json |
| 6 | Orchestrator + export | AC-01 单条 trip |

---

## 11. 调试技巧

| 问题 | 处理 |
|------|------|
| HTML 与 golden 不一致 | 对比 `data-layout`、CSS 是否复制完整 |
| schema 失败 | `travelogue validate` 看字段路径 |
| 图片不显示 | 检查相对路径是否相对 `index.html` |
| HEIC 无法读 | `pip install pillow-heif` |
| ffmpeg 找不到 | 在 `config.yaml` 写绝对路径 |

---

## 12. Git 忽略

`trips/`、`config.yaml`、`.venv/`、`__pycache__/` 不应提交。见仓库 `.gitignore`。

---

## 13. 相关文档

- [TECH-ARCHITECTURE.md](./TECH-ARCHITECTURE.md)  
- [ACCEPTANCE.md](./ACCEPTANCE.md)  
- [AGENT-ARCHITECTURE.md](./AGENT-ARCHITECTURE.md)  

---

## 14. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-05-19 | P0 开发手册；CLI 待实现标注 |
