# 验收记录 · maomi

| 属性 | 内容 |
|------|------|
| **tripId** | maomi |
| **状态** | G1 全链路已跑通 · 待人工验收 |
| **更新** | 2026-05-26 |

---

## 素材

| 项 | 值 |
|----|-----|
| 相册路径 | `D:\Photos\maomi` |
| 原始文件 | 33 张 JPG |
| ingest 后 assets | **33** 张（跳过 0） |
| 可排版 | **33** 张（`layoutEligible: true`） |
| 低分辨率剔除 | **0** 张 |
| 批次 | `batch-20260526-1527` |
| 耗时 | ~280s（ingest only） |

---

## Ingest 阶段产出（CLI 报告）

命令：

```powershell
python -m travelogue trip new maomi --title "maomi" --place "maomi" --force
python -m travelogue ingest maomi --from "D:\Photos\maomi" --config config.demo.yaml
```

| 统计项 | maomi 实测 | 含义 |
|--------|----------|------|
| 扫描 / 入选 | 33 / 33 | 目录内符合格式的图片数 |
| 导入 +N / 跳过 | +33 / 0 | 全部写入，无去重丢弃 |
| 完全重复 (md5) | 0 | 字节级相同 |
| 相似图 (phash) | 0 | 首批无近重复丢弃 |
| 连拍丢弃 / 替换 | 0 / 0 | 无密集连拍合并 |
| 日期来源 | **exif=33** filename=0 mtime=0 | 全部 EXIF 日期（精度到秒） |
| 素材类型 mediaClass | photo=33 | 均为照片 |
| EXIF 旋转 | 33 | 按 EXIF Orientation 转正 |
| 低分辨率（不参与排版） | 0 张 | — |
| 检测到人脸 | 33 张 | 全部写入 focalPoint |
| 含 GPS | 33 张 | EXIF 有 GPS 字段（坐标均为 0,0，未 geocode） |
| 构图 | 横21 竖12 | landscape / portrait |

**多段旅行提示（ingest 启发）：**

> 检测到可能包含 4 次旅行（11月–12月·maomi、12月28日·maomi、2月22日·maomi、3月–4月·maomi）；默认合成一本游记，可在 G1 合并段或拆成多本。

**按月分布：** 2025-11×8 · 2025-12×6 · 2026-02×1 · 2026-03×13 · 2026-04×5（共 11 个拍摄日）

---

## Ingest 写入 trip.json 的字段（每张 asset）

| 类别 | 字段 | maomi 覆盖 |
|------|------|----------|
| 文件 | `sourceFile`, `displayFile`, `srcset[]` | 33/33，WebP w800+w1600 |
| 裁剪 | `cropMobile`, `cropWeb` | 33/33 |
| 尺寸 | `nativeWidth/Height`, `width/height`, `aspectKind` | 33/33（1854×2640～5760×5760） |
| 时间 | `takenAt`, `dateSource=exif`, `dateConfidence=high` | 33/33 |
| 质量 | `quality.sharpness` | 803～3753，均值 ~1533 |
| 去重 | `dedupeGroupId`, `ingestBatchId` | 33/33（33 个独立组） |
| 连拍 | `burstGroupId` | 33/33（每组 1 张） |
| 排版资格 | `layoutEligible` | 33/33 |
| 人物 | `focalPoint`, tags `person`/`face` | 33/33 |
| 启发式标签 | `tags[]`, `tagsSource: heuristic` | 白天29 · 横图21 · 竖图12 · 夜景3 · 傍晚1 |
| 地理 | `geo`, `place.city` | geo 字段存在但 lat/lon=0,0，无城市 |
| 裁剪衍生 | 磁盘 WebP | ~132 个文件（每 asset 4 份衍生） |

**trip 级（ingest 结束时）：**

- `meta.dateStart` / `dateEnd`：`2025-11-15` — `2026-04-04`
- `coverAssetId`：`asset-001`
- `pipeline.status`：`ingest_ready`

---

## maomi 相册特点（ingest 视角）

1. **EXIF 完整**：日期、旋转信息齐全，Curate 可按真实时间切段（与 mao 微信图不同）。
2. **无去重损耗**：33 张全部保留，无连拍/phash 压缩。
3. **全量可排版**：无低分辨率剔除；人物图为主，focalPoint 全覆盖。
4. **跨月多段**：ingest / curate 均提示 4 个时间段，默认合成 4 章一本。
5. **GPS 占位**：报告「含 GPS」但坐标为 0,0，暂无法 geocode 分城。

---

## 全链路结果（2026-05-26）

| 阶段 | 结果 |
|------|------|
| ingest | 33 assets，33 可排版 |
| curate (`--layout auto`) | **4 章** · **17 Web 屏** · **31 张进 screens** |
| lock structure | OK |
| narrate (`rule-stub`) | hook + 4 章 lead + epilogue + 图注（未配置 LLM 时用 stub） |
| render `--dual` | OK |
| validate | OK |
| longshot-smoke | OK（4 章 / 31 cards；图多跳过 capture） |

命令：

```powershell
python -m travelogue curate maomi --layout auto
python -m travelogue lock maomi structure
python -m travelogue narrate maomi --config config.demo.yaml --regenerate
python -m travelogue render maomi --dual
python -m travelogue validate maomi
python -m travelogue longshot-smoke maomi
```

| 项 | 值 |
|----|-----|
| 章 | ch-01 open(9) · ch-02 moment(6) · ch-03 gallery(14) · ch-04 close(3) |
| Web layoutPlanSummary | landscape-1×10, portrait-3×2, portrait-2×2, landscape-6×1, portrait-1×1, **landscape-4×1** |
| 策展封面 | `asset-023` |
| hook | 在maomi的2025年11月15日，33 张碎片拼成这一页。（stub） |
| epilogue | 下次再见，maomi。（stub） |
| Curate WARN | 4 时间段合成一本；1 章跨段合并 |

**产出：**

- `trips/maomi/index.html`（web · `data-layout-engine="screens"`）
- `trips/maomi/index-mobile.html`
- `trips/maomi/index-longshot.html`

**本地预览：**

```powershell
python -m travelogue serve trips/maomi
# web:     http://127.0.0.1:8766/
# mobile:  http://127.0.0.1:8766/index-mobile.html
# 长图:    http://127.0.0.1:8766/index-longshot.html
```

---

## 与 mao 对比（参考）

| 维度 | mao | maomi |
|------|-----|-------|
| 原始 → 入库 | 43 → 29 | 33 → 33 |
| 日期 | 文件名 | EXIF |
| 可排版率 | 20/29 | 33/33 |
| 章 / Web 屏 | 3 / 10 | **4 / 17** |
| narrate | DeepSeek | **rule-stub**（本机未走 LLM） |

---

## 下一步（可选）

```powershell
# 换 DeepSeek 重写文案（需 config 中 LLM API）
python -m travelogue narrate maomi --provider deepseek --regenerate
python -m travelogue render maomi --dual

# 若希望拆成多本游记：在 G1 按时间段拆分后再 curate
```

---

## Phase 9 · Quality Gate（cull-on 基线 · 2026-06-02）

| 项 | cull-off（2026-05-26） | cull-on（NR-P9-04） |
|----|------------------------|---------------------|
| 扫描 assets | 33 | 33 |
| layoutEligible | **33** | **26** |
| cull 层 eligible | — | **27**（Pass 3 剔 6 · `cull_quota`） |
| 非 featured 保留率（cull 层） | — | **81.8%**（27/33，≥ 80%） |
| 最终保留率 | — | 78.8%（26/33，low_res 再剔 1） |
| curate smoke | 4 章 | **4 章** ✅ |
| cullUserLine | — | 经挑选 27 张进入排版 |

命令：

```powershell
python scripts/phase9_golden_cull_signoff.py --trip maomi --write docs/acceptance-records/phase9-golden-cull-signoff.json
```

**说明**：AC-P9-02 地板按 **cull 层**计量（27/33）；最终 26 张因 cull 后 `asset_quality` 低分辨率剔除 `asset-023`，与 cull 职责分离，无需调 Pass 3。

记录：`docs/acceptance-records/phase9-golden-cull-signoff.json` · `phase9-quality-gate.json`
