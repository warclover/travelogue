# 本地工坊 · 一条龙与验收

| 属性 | 内容 |
|------|------|
| **关联** | [PRD-PHASE2.md](./PRD-PHASE2.md)、[IMPLEMENTATION-PHASE2.md](./IMPLEMENTATION-PHASE2.md)、`DEVELOPMENT.md`、`ACCEPTANCE.md`、[PRD-EXPERIENCE.md](./PRD-EXPERIENCE.md) |
| **更新日期** | 2026-07-16 |

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

### 1.0 可选依赖一览

| 能力 | 安装 | 说明 |
|------|------|------|
| **长图（Playwright）** | `pip install -e ".[playwright]"` + `playwright install chromium` | 缺省常见 `E_LNG_PLAYWRIGHT` |
| **HEIC** | `pip install pillow-heif` | iPhone 照片 |
| **Vision / CLIP** | `pip install -e ".[vision]"`；`config.yaml` 中 `vision.enabled` | 默认 **关**；开启后首次可能下载模型 |

### 1.0b 空态 FTUE 狗粮（`--trips-dir`）

空书架测试优先用 **CLI `--trips-dir`**。W2 起也可设 `TRAVELOGUE_TRIPS_DIR`（优先级低于 CLI，高于 `config.yaml`）。

```powershell
$empty = Join-Path $env:TEMP "travelogue-ftue-trips"
New-Item -ItemType Directory -Force -Path $empty | Out-Null
$env:TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM = "1"
python -m travelogue studio --no-open --host 127.0.0.1 --port 8771 --trips-dir $empty
# 浏览器打开 http://127.0.0.1:8771/ 后清 localStorage 再刷新
# 优先级：--trips-dir > TRAVELOGUE_TRIPS_DIR > config.yaml trips_dir > 默认
# 启动日志：studio trips_dir source=… path=…
```

见 [PRD-FTUE-OPTIMIZATION-V1.md](./PRD-FTUE-OPTIMIZATION-V1.md) · [IMPLEMENTATION-FTUE-OPTIMIZATION-V1.md](./IMPLEMENTATION-FTUE-OPTIMIZATION-V1.md)。

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

## 8. Phase 3 聚类验收（M12–M14）

关联：[ACCEPTANCE-PHASE3.md](./ACCEPTANCE-PHASE3.md)、[PRD-PHASE3.md](./PRD-PHASE3.md)

```powershell
# 聚类 golden + spike
python -m pytest tests/test_clustering_spike.py tests/test_cluster_eval.py -q

# I-G2 布局对比（fixture 或本地 trips）
python scripts/phase3_ig2_report.py golden-mixed-scenes --fixture
python scripts/phase3_ig2_report.py mao maomi linzhi

# 性能 bench（400 张）
python scripts/phase3_cluster_bench.py --assets 400 --geo-only    # PF-P3-01
python scripts/phase3_cluster_bench.py --assets 400 --vision      # PF-P3-02 / AC-P3-C05

# 真实 CLIP 验收（需 pip install -e ".[clip]"）
python scripts/phase3_clip_acceptance.py
python scripts/phase3_e2e_bench.py --assets 150 --record-real trips/linzhi
python scripts/diff_curate.py golden-mixed-scenes --fixture
python -m pytest tests/test_studio_ux_p3.py tests/test_layout_golden.py -q -m "not vision"
```

验收记录目录：`docs/acceptance-records/phase3-*.json`

**配置**：`config.yaml` 中 `clustering.enabled` / `vision.enabled`；Studio 高级折叠可 PATCH `/__travelogue/config`。

### 8.1 聚类 config 调参（M14-1）

`config.yaml` 常用项（详见 `config.yaml.example`）：

| 键 | 说明 | 默认 |
|----|------|------|
| `clustering.enabled` | `true` / `false` / `auto` | `auto` |
| `clustering.sceneClusterMode` | `run_aware` / `off` | `run_aware` |
| `clustering.scene.clusterEps` | DBSCAN ε | `0.07` |
| `vision.enabled` | CLIP 场景分析 | `false` |

布局权重实验：`scripts/phase3_ig2_report.py` + `docs/acceptance-records/phase3-weight-experiment.json`。

NR-P3-01 可选对比：`python scripts/diff_curate.py golden-mixed-scenes --fixture`

### 8.2 GPU / CLIP（M13-4b · 可选）

安装 `pip install -e ".[clip]"` 后，有 NVIDIA GPU 时 PyTorch 会自动使用 CUDA；无 GPU 时走 CPU（400 张 warm ~40s 本机验收）。首次运行需下载 OpenCLIP 权重（不计入 PF-P3-02 预算）。

---

## 9. 版本记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | Phase 2：Studio bat 入口；250 张；服务端长图分段双轨 |
| 2026-05-28 | Phase 3：§8 聚类验收命令与 bench / I-G2 脚本 |
