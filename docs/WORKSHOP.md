# 本地工坊 · 一条龙与验收

| 属性 | 内容 |
|------|------|
| **关联** | [PRD-PHASE2.md](./PRD-PHASE2.md)、[IMPLEMENTATION-PHASE2.md](./IMPLEMENTATION-PHASE2.md)、`DEVELOPMENT.md`、`ACCEPTANCE.md`、[PRD-EXPERIENCE.md](./PRD-EXPERIENCE.md) |
| **更新日期** | 2026-05-27 |

---

## 1. 新相册（推荐 · Phase 2）

**旅行者 / 非开发者** — 双击启动（AC-P2-03）：

```text
双击  scripts\start-studio.bat
```

或命令行（开发者）：

```powershell
cd C:\Users\xiafe\Projects\travelogue
pip install -e ".[dev]"

python -m travelogue studio
python -m travelogue studio --pick-folder "D:\Photos\某次旅行"

python -m travelogue export-longshot trips\<tripId>
python -m travelogue export-longshot trips\<tripId> --scale 2
```

- 相册默认上限 **250 张**（`config.yaml` · Studio 不收紧至 MVP PRD 的 30）
- 浏览器：**Chrome 90+ / Edge 90+（Windows）**
- 验收：[ACCEPTANCE-PHASE2.md](./ACCEPTANCE-PHASE2.md)

---

## 1b. 开发者一条龙（MVP · 仍可用）

```powershell
.\scripts\workshop-pipeline.ps1 -AlbumPath "D:\Photos\某次旅行" -TripId my-trip-2025 -Title "标题" -Place "城市"
```

可选导出 zip（高级 / 路径 B 预埋）：

```powershell
.\scripts\workshop-pipeline.ps1 -AlbumPath "D:\Photos\..." -TripId my-trip-2025 -Export -ConfirmPrivacy
```

等价于：`from-album` → `lock structure` → `narrate` → `render --dual` → `validate`；加 `-Export -ConfirmPrivacy` 时再 `lock copy` → `export`。

> Phase 2 产品默认 **不引导** zip；长图 PNG 为主分享物。见 [SHARING.md](./SHARING.md)。

---

## 2. 已有 trip（如京都）

```powershell
# 单 trip 预览 + inline edit（开发者）
python -m travelogue serve trips\kyoto-2025

# 或 Studio 工作台打开最近列表
python -m travelogue studio
```

```powershell
.\scripts\g1-pipeline.ps1 trips\kyoto-2025
.\scripts\verify-trip.ps1 trips\kyoto-2025
.\scripts\verify-trip.ps1 trips\kyoto-2025 -Serve
```

---

## 3. 导入提示（低清 · 日期 · 素材类型）

`ingest` / `curate` 会在 CLI 报告中显示：

- **疑似缩略图**：原图短边 &lt; `min_short_edge_layout_px`（默认 600）
- **策展将剔除低分辨率**：按本批中位数预估（与 `curate` 一致）
- **日期来源**：exif / filename / mtime 计数；mtime 占比高时警告
- **素材类型**：`photo` / `screenshot` / `archive` 等（见 [老图.md](./老图.md)）
- **多时间段**：`curate` 写入 `curation.segments[]`，按段分章（间隔默认 14 天）

Studio 失败时显示 **中文** 提示（见 [ERROR-CODES.md](./ERROR-CODES.md) Phase 2 附录）。

---

## 4. 自动化验收

```powershell
python -m pytest tests/ -q
python scripts\validate_trip.py schemas\fixtures\trip.example.json --level all
```

Phase 2 专项（实现后）：

```powershell
python -m pytest tests/test_studio_server.py tests/test_export_longshot.py -q
```

CI：`.github/workflows/ci.yml`（push/PR 时跑 pytest + fixture validate）。

---

## 5. 三套相册清单

见 [web-screens-ab-checklist.md](web-screens-ab-checklist.md)。

| # | tripId | 说明 |
|---|--------|------|
| 1 | `kyoto-2025` | 横多 · Web 版式已修 |
| 2 | 自建竖图册 | Studio / workshop + 竖图相册 |
| 3 | 连拍/九宫格 | 同主题多图 |
| 4 | `linzhi` | 林芝 · 大批量 · **>45 张长图分段** 验收 |

自动化替身：`tests/test_portrait_heavy_workshop.py`（竖图 ingest → screens）。

---

## 6. 阅读体验自检（PRD-EXPERIENCE · E0–E2）

工坊 draft 默认 profile 为 **`default_hybrid`**（见 [experience-matrix.yaml](./experience-matrix.yaml)）。`serve` 或 Studio 预览后按下列清单人工过一遍：

| # | 检查项 | 通过标准 |
|---|--------|----------|
| 1 | 三模式入口 | toolbar 可见 **浏览 / 放映 / 长图**；长图跳转 `index-longshot.html` |
| 2 | 屏序一致 | 同一章在 scroll 与 present 切换时 asset 顺序一致（AC-EXP-01） |
| 3 | Hybrid 默认 | web `index.html`：`scroll-snap` 生效、章间有 gentle reveal（breath soft）、folio lite 顶栏/页码可见 |
| 4 | longshot 捕获 | **Phase 2 主路径**：`export-longshot`；客户端 html2canvas 仍作回归 |
| 5 | mobile 降级 | `index-mobile.html` 无 breath/folio（`legacy` profile） |
| 6 | share zip | `export` 产物 profile 为 `performance`；Studio 主 UI 不突出 zip |

**双文件夹（附录 A · 可选）**：`from-album` 双源 ingest 后，`trip.json` 含 `userTierSummary`；cover / hero 优先 `userTier: featured`。

**回归基线**：将 `export.reading.profile` 设为 `legacy`，应与 2026-05 现版 scroll 行为一致。

---

## 7. 版本记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | Phase 2：Studio bat 入口；250 张；服务端长图分段双轨 |
