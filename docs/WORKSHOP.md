# 本地工坊 · 一条龙与验收

| 属性 | 内容 |
|------|------|
| **关联** | `DEVELOPMENT.md`、`ACCEPTANCE.md`、`web-screens-ab-checklist.md`、[PRD-EXPERIENCE.md](./PRD-EXPERIENCE.md) |

---

## 1. 新相册（推荐）

```powershell
cd C:\Users\xiafe\Projects\travelogue
.\scripts\workshop-pipeline.ps1 -AlbumPath "D:\Photos\某次旅行" -TripId my-trip-2025 -Title "标题" -Place "城市"
```

可选导出 zip：

```powershell
.\scripts\workshop-pipeline.ps1 -AlbumPath "D:\Photos\..." -TripId my-trip-2025 -Export -ConfirmPrivacy
```

等价于：`from-album` → `lock structure` → `narrate` → `render --dual` → `validate`；加 `-Export -ConfirmPrivacy` 时再 `lock copy` → `export`。

---

## 2. 已有 trip（如京都）

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

---

## 4. 自动化验收

```powershell
python -m pytest tests/ -q
python scripts\validate_trip.py schemas\fixtures\trip.example.json --level all
```

CI：`.github/workflows/ci.yml`（push/PR 时跑 pytest + fixture validate）。

---

## 5. 三套相册清单

见 [web-screens-ab-checklist.md](web-screens-ab-checklist.md)。

| # | tripId | 说明 |
|---|--------|------|
| 1 | `kyoto-2025` | 横多 · Web 版式已修 |
| 2 | 自建竖图册 | `workshop-pipeline` + 竖图相册 |
| 3 | 连拍/九宫格 | 同主题多图 |
| 4 | `linzhi` | 林芝 · `D:\Photos\林芝` · 大批量验收 |

自动化替身：`tests/test_portrait_heavy_workshop.py`（竖图 ingest → screens）。

---

## 6. 阅读体验自检（PRD-EXPERIENCE · E0–E2）

工坊 draft 默认 profile 为 **`default_hybrid`**（见 [experience-matrix.yaml](./experience-matrix.yaml)）。`serve` 后按下列清单人工过一遍：

| # | 检查项 | 通过标准 |
|---|--------|----------|
| 1 | 三模式入口 | toolbar 可见 **浏览 / 放映 / 长图**；长图跳转 `index-longshot.html` |
| 2 | 屏序一致 | 同一章在 scroll 与 present 切换时 asset 顺序一致（AC-EXP-01） |
| 3 | Hybrid 默认 | web `index.html`：`scroll-snap` 生效、章间有 gentle reveal（breath soft）、folio lite 顶栏/页码可见 |
| 4 | longshot 捕获 | 长图导出前无 Lenis 残留；>45 张时完整长图禁用提示仍在 |
| 5 | mobile 降级 | `index-mobile.html` 无 breath/folio（`legacy` profile） |
| 6 | share zip | `export` 产物 profile 为 `performance`；无 inline-edit |

**双文件夹（附录 A · 可选）**：`from-album` 双源 ingest 后，`trip.json` 含 `userTierSummary`；cover / hero 优先 `userTier: featured`。

**回归基线**：将 `export.reading.profile` 设为 `legacy`，应与 2026-05 现版 scroll 行为一致。
