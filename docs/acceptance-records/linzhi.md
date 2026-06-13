# 验收记录 · linzhi（林芝）

| 属性 | 内容 |
|------|------|
| **tripId** | linzhi |
| **状态** | G1 全链路已跑通 · AC-07 待发群确认 |
| **更新** | 2026-06-13（全链路重跑 · Integration Sprint W1） |

---

## 素材与流水线

| 项 | 值 |
|----|-----|
| 相册路径 | `D:\Photos\林芝` |
| 素材总数 | 232 assets（ingest 跳过 17：md5×15、phash×1、burst×1） |
| 进 screens / 长图 | 207 张 layout · **125 屏** · longshot **84 cards** |
| 章数 | 5（ch-01～ch-05） |
| layoutEngine | screens |
| 构图 | 横 169 / 竖 15 / 方 3 / 全景 20 |
| mediaClass | photo 224 / collage 5 / screenshot 1 / thumbnail 2 |
| 低分辨率剔除 | 20（`curation.excludedLowResAssetIds`） |
| 叙事 | DeepSeek narrate（209 条 caption + 5 章 lead + hook/epilogue） |
| 输出 | `index.html` + `index-mobile.html` + `index-longshot.html` |
| export zip | 未重跑（上次 ~112 MB） |

---

## 耗时（2026-06-13 · 全链路）

| 阶段 | 耗时 |
|------|------|
| workshop（from-album + lock + narrate + render + validate） | **~177s（~3 min）** |
| export-longshot（5 章 PNG） | ~14s |
| longshot-smoke | OK · 5 章 / 84 cards |

命令：

```powershell
powershell -File scripts/workshop-pipeline.ps1 -AlbumPath "D:\Photos\林芝" -TripId linzhi -Title "林芝" -Place "林芝" -Force
python -m travelogue export-longshot linzhi
python -m travelogue longshot-smoke trips/linzhi
```

> 日志：`docs/acceptance-records/linzhi-pipeline-2026-06-13.log`

---

## 耗时（2026-05-26 · 历史）

| 阶段 | 耗时 |
|------|------|
| from-album（ingest + curate + layout） | ~277s |
| lock structure | <1s |
| narrate（deepseek） | ~57s |
| render --dual | ~3s |
| validate + longshot-smoke | ~9s |
| media reexport asset-031（补救） | ~5s |
| **导入 → 可浏览** | **~352s（~6 min）** |

> 备注：首次 render 因 `asset-031` 缺 WebP 衍生图失败；`media reexport` 单张修复后通过。根因：ingest 连拍/pHash **替换**时 `_upsert_asset` 在 `_build_asset_entry` 写入 WebP 后又按同一 `asset_id` 删除了衍生图（已修：`ingest.py` + 收尾校验 `E_INGEST_DERIVATIVE_MISSING`）。

---

## 自动化检查（2026-06-13 · 全链路重跑）

| 命令 | 结果 |
|------|------|
| `workshop-pipeline.ps1`（`-Force`） | OK · ~177s |
| `validate trips/linzhi/trip.json` | OK |
| `export-longshot linzhi` | OK · 5 章 PNG |
| `longshot-smoke trips/linzhi` | OK（5 章 / 84 cards） |
| `quality_gate.py` | OK（schema 同步后） |

> **schema 修复**：`trip.schema.json` 补齐 `collage` mediaClass · LTE `layoutGeometry` / slot `rect` · mosaic log 扩展字段（否则 render 前 validate 失败）。

---

## 自动化检查（2026-06-13 · smoke only）

| 命令 | 结果 |
|------|------|
| `validate trips/linzhi/trip.json` | OK（修复 `pipeline.runs` 末条缺 `startedAt`） |
| `longshot-smoke trips/linzhi` | OK（5 章 / 160 cards） |
| `quality_gate.py` | OK |
| `e2e_studio_smoke.ps1` | OK |

> **未重跑全链路 ingest/curate**（需本机 `D:\Photos\林芝`）。结构/渲染 smoke 已在 master 最新代码下通过。

---

## 自动化检查（2026-05-26）

| 命令 | 结果 |
|------|------|
| `validate trips/linzhi/trip.json` | OK |
| `longshot-smoke trips/linzhi` | OK（5 章 / 209 cards） |
| 新字段抽检 | 231/231 有 `quality.sharpness`、`burstGroupId`、`layoutEligible`、heuristic `tags`；`chapterPlan`×5、`chapterHeroAssetIds`、`layoutPlanSummary` 均存在 |
| **Phase-1 排版等价** | `scripts/phase1_layout_equivalence.py linzhi` → **PASS**（5 章 / 75 屏，`aspect_match=1.0` ≡ legacy） |
| **Phase-2 beam 对比** | `scripts/phase2_layout_compare.py linzhi` → **SAME**（75 屏；beam 候选未优于 legacy，见 `phase2-layout-compare.json`） |
| **Phase-3 自适应+色彩** | `backfill_color_metrics.py linzhi` → 231/231；`phase3_layout_acceptance.py linzhi` → **SAME**（75 屏，arc=**dynamic**，preset=phase3b） |

## AC 自检

| ID | 项 | 状态 | 备注 |
|----|-----|------|------|
| AC-07 | 长图发微信群 | ☐ | 推荐：按章 2× + 隐藏不准图注 |
| AC-05 | 另一台手机开 zip | ☐ | |
| AC-06 | 导出图无精确 GPS | ☐ | |
| AC-03 | 愿分享给朋友 | ☐ | 图注需人工微调 |

---

## G2 文案修正工作流

```powershell
python -m travelogue serve trips/linzhi
# index-longshot.html：图注：关 / 编辑图注 / 删空图注 → skipCaption
python -m travelogue narrate linzhi --chapter-id ch-02 --regenerate --provider deepseek
```

- 删空图注 → `assets[].skipCaption=true`，narrate 不再重写
- inline 保存 → 自动 re-render sidecar（F-ED-03）

---

## 发群反馈（待填）

| 问题 | 反馈 |
|------|------|
| 能否读完 | |
| 图注是否干扰 | |
| 文件是否过大 | |
| 其他 | |
