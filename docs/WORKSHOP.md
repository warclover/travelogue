# 本地工坊 · 一条龙与验收

| 属性 | 内容 |
|------|------|
| **关联** | `DEVELOPMENT.md`、`ACCEPTANCE.md`、`web-screens-ab-checklist.md` |

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

等价于：`from-album` → `lock structure` → `narrate` → `render --dual` → `validate`。

---

## 2. 已有 trip（如京都）

```powershell
.\scripts\g1-pipeline.ps1 trips\kyoto-2025
.\scripts\verify-trip.ps1 trips\kyoto-2025
.\scripts\verify-trip.ps1 trips\kyoto-2025 -Serve
```

---

## 3. 导入时低清提示

`ingest` 会在 CLI 报告中显示：

- **疑似缩略图**：原图短边 &lt; `min_short_edge_layout_px`（默认 600）
- **策展将剔除低分辨率**：按本批中位数预估（与 `curate` 一致）

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

自动化替身：`tests/test_portrait_heavy_workshop.py`（竖图 ingest → screens）。
