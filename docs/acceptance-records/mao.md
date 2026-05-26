# 验收记录 · mao（微信相册）

| 属性 | 内容 |
|------|------|
| **tripId** | mao |
| **状态** | G1 全链路已跑通 · 待人工验收 |
| **更新** | 2026-05-26 |

---

## 素材

| 项 | 值 |
|----|-----|
| 相册路径 | `D:\Photos\mao` |
| 原始文件 | 43 张 JPG（微信图片，同日导出） |
| ingest 后 assets | **29** 张（跳过 14：连拍×6、连拍替换×7、phash×1） |
| 可排版 | **20** 张（`layoutEligible: true`） |
| 低分辨率剔除 | **9** 张（`excludeReason: low_resolution`） |
| 批次 | `batch-20260526-1447` |
| 耗时 | ~148s（ingest only） |

---

## Ingest 阶段产出（CLI 报告）

命令：

```powershell
python -m travelogue trip new mao --title "mao" --place "mao" --force
python -m travelogue ingest mao --from "D:\Photos\mao" --config config.demo.yaml
```

| 统计项 | mao 实测 | 含义 |
|--------|----------|------|
| 扫描 / 入选 | 43 / 43 | 目录内符合格式的图片数 |
| 导入 +N / 跳过 | +29 / 14 | 最终写入 trip 的新增 vs 去重丢弃 |
| 完全重复 (md5) | 0 | 字节级相同 |
| 相似图 (phash) | 1 | 近重复且新图不够清晰 → 丢弃 |
| 连拍 | 6 | 连拍且新图不够清晰 → 丢弃 |
| 连拍替换为更清晰 | 7 | 连拍保留更清晰一帧 |
| 日期来源 | exif=0 filename=36 | EXIF / 文件名 / mtime 解析 |
| 素材类型 mediaClass | photo=29 | photo / screenshot / thumbnail 等 |
| EXIF 旋转 | 25 | 按 EXIF Orientation 转正 |
| 低分辨率（不参与排版） | 9 张 | 见 `curation.excludedLowResAssetIds` |
| 检测到人脸 | 33 次计数 | 含同图多人；影响 focalPoint |
| 含 GPS | 0 | 微信图通常无 EXIF GPS |
| 构图 | 横17 竖12 | landscape / portrait / square / panorama |

---

## Ingest 写入 trip.json 的字段（每张 asset）

| 类别 | 字段 | mao 覆盖 |
|------|------|----------|
| 文件 | `sourceFile`, `displayFile`, `srcset[]` | 29/29，WebP w800+w1600 |
| 尺寸 | `nativeWidth/Height`, `width/height`, `aspectKind` | 29/29 |
| 时间 | `takenAt`, `dateSource`, `dateConfidence` | 29/29（均 filename / high） |
| 质量 | `quality.sharpness` | 29/29（803～3509，均值 ~1543） |
| 去重 | `dedupeGroupId`, `ingestBatchId` | 29/29 |
| 连拍 | `burstGroupId` | 29/29（本批仅 1 组：同日连拍） |
| 排版资格 | `layoutEligible`, `excludeReason` | 20 可排 / 9 低分辨率 |
| 人物 | `focalPoint`, tags `person`/`face` | 26/29 有人脸标签 |
| 启发式标签 | `tags[]`, `tagsSource: heuristic` | 29/29（横图/竖图/白天等） |
| 地理 | `geo`, `place.city` | 0（无 GPS，未 geocode） |
| 裁剪 | `cropMobile`, `cropWeb` | 按 config 生成 |

**trip 级（ingest 结束时）：**

- `meta.dateStart` / `dateEnd`：由 assets 日期聚合 → `2026-05-26`
- `coverAssetId`：首张可排版图 → `asset-004`
- `curation.excludedLowResAssetIds`：低分辨率 ID 列表
- `pipeline.status`：`ingest_ready`
- `pipeline.lastBatchId`：批次 ID

---

## mao 相册特点（ingest 视角）

1. **微信导出图**：文件名带时间戳，无 EXIF 日期 → 全靠 `filename` 解析；解析粒度较粗时 `takenAt` 可能相同（本批 29 张同为 `2026-05-26T12:00:00Z`），Curate 分章会受影响。
2. **连拍密集**：43 张压到 29 张，连拍替换 7 次；`burstGroupId` 合并为单组。
3. **混分辨率**：同目录含 5760×4320 原图与 1080×1919 缩略图 → 相对阈值剔除 9 张低分辨率。
4. **人物为主**：26/29 有人脸；focalPoint 已写入，供后续 screens 裁剪。
5. **无 GPS**：无法做 geocode / 按城市切段。

---

## 全链路结果（2026-05-26）

| 阶段 | 结果 |
|------|------|
| ingest | 29 assets，20 可排版 |
| curate (auto/screens) | 3 章 · 10 屏 · 18 张进 screens |
| narrate (deepseek) | hook + 3 章 lead + 18 条 caption |
| render --dual | OK |
| validate | OK（修 schema：`slot.role` 增加 `main`） |
| longshot-smoke | OK（3 章 / 18 cards） |

| 项 | 值 |
|----|-----|
| 章 | ch-01 open(9) · ch-02 moment(5) · ch-03 close(5) |
| layoutPlanSummary | landscape-1×5, mosaic-5×2, portrait-1×3 |
| 封面 hero | ch-01 asset-017 · ch-02 asset-006 · ch-03 asset-028 |
| hook | 马尔代夫一样的红墙与海风。（DeepSeek） |

**产出：**

- `trips/mao/index.html`（web）
- `trips/mao/index-mobile.html`
- `trips/mao/index-longshot.html`

**本地预览：**

```powershell
python -m travelogue serve trips/mao
# web:     http://127.0.0.1:8080/
# mobile:  http://127.0.0.1:8080/index-mobile.html
# 长图:    http://127.0.0.1:8080/index-longshot.html
```

---

## Phase-1 排版等价（2026-05-26）

| 项 | 值 |
|----|-----|
| 命令 | `python scripts/phase1_layout_equivalence.py mao` |
| 配置 | `layout.scoring.enabled=true`，`weights.aspect_match=1.0` |
| 结果 | **PASS** — 3 章 / 15 屏，与 legacy 组屏签名一致 |
| 记录 | `docs/acceptance-records/phase1-layout-equivalence.json` |

---

## Phase-2 beam + 多信号（2026-05-26）

| 项 | 值 |
|----|-----|
| 命令 | `python scripts/phase2_layout_compare.py mao` |
| 权重 | `PHASE2_WEIGHTS`（aspect 0.15 + sharpness + time + burst + diversity + arc + hero，归一化 Σ=1） |
| 结果 | **SAME** — 15 屏与 legacy 一致；客观指标 Δ=0 |
| 记录 | `docs/acceptance-records/phase2-layout-compare.json` |

**Phase-3 验收（2026-05-26）**

| 项 | 值 |
|----|-----|
| 色彩回填 | `python scripts/backfill_color_metrics.py mao` → 29/29 |
| 验收 | `python scripts/phase3_layout_acceptance.py mao` → **SAME**（15 屏） |
| 预设 | `phase3b` + `arc_mode=v2_adaptive` → **dynamic** |
| 记录 | `docs/acceptance-records/phase3-layout-acceptance.json` |
| 预览 | `python -m travelogue serve trips/mao` |

**Phase-3 盲评 A/B（2026-05-26）**

| 项 | 值 |
|----|-----|
| 命令 | `python scripts/phase3_blind_review.py mao --seed 42` |
| 客观 | **SAME** — 15 屏布局签名一致（A/B 视觉应相同） |
| 入口 | `trips/mao/_blind-review/index.html` |
| 评分模板 | `_blind-review/subjective_eval.template.json` |
| 密钥（打分后揭晓） | `_blind-review/key.json` |
| 记录 | `docs/acceptance-records/phase3-blind-review.json` |

```powershell
python -m travelogue serve trips/mao
# → http://127.0.0.1:8766/_blind-review/index.html
```

**salientBox 回填（2026-05-26）**

| trip | 命令 | 结果 |
|------|------|------|
| mao | `python scripts/backfill_salient_box.py mao` | 27/29 有 salientBox |
| linzhi | `python scripts/backfill_salient_box.py linzhi` | 108/231 有 salientBox |

**主观盲评清单（I-G4）**

| # | 问题 | A | B | 备注 |
|---|------|---|---|------|
| 1 | 首章节奏是否自然 | | | |
| 2 | 横竖混排是否协调 | | | |
| 3 | 连拍/同场景是否成组 | | | |
| 4 | 整体是否愿分享 | | | |

---

## 下一步（可选）

```powershell
python -m travelogue curate mao --layout auto
python -m travelogue render trips/mao/trip.json --dual
```
