# Travelogue · 媒体管线（Agent 0）

| 属性 | 内容 |
|------|------|
| **Agent** | Media Lab（Agent 0） |
| **文档版本** | v0.1 |
| **关联** | `ADAPTIVE-LAYOUT.md`、`config.yaml.example`、`adr/001-delivery-and-media.md` |
| **更新日期** | 2026-05-19 |

---

## 1. 输入输出

| 输入 | 输出 |
|------|------|
| 用户目录中的 jpg/png/heic/webp/mp4/mov | `source/` 原文件拷贝 |
| | `assets/*` WebP、视频循环、poster、语音副本 |
| | `trip.json` → `assets[]` 元数据更新 |

---

## 2. 支持格式

| 类型 | 扩展名 | 处理 |
|------|--------|------|
| 图片 | jpg, jpeg, png, webp, heic | Pillow；HEIC 需 pillow-heif |
| 视频 | mp4, mov | ffprobe 元数据 + ffmpeg 转码 |
| 语音 | m4a, aac, mp3, wav | 拷贝到 assets；触发 ASR（可选） |

单文件失败 → 记录 `E_INGEST_FILE_CORRUPT`，**不阻断**整批。

---

## 3. 图片管线

### 3.1 拷贝

- 目标：`trips/{tripId}/source/{originalName}`  
- 若重名：追加 `_2`、`_3`…  
- 不修改用户相册原路径文件。

### 3.2 EXIF

读取（有则写，无则 null）：

- `DateTimeOriginal` → `takenAt`（ISO8601，保留时区）  
- GPS → 仅内部用于反查；`place.city` 城市级  
- `ImageWidth` / `ImageHeight`

无时间 → `takenAt: null`，策展按文件名序或导入序。

### 3.3 WebP 多档

默认宽度（`config.ingest.webp_widths`）：**800, 1600, 2400**。

| 输出文件 | 说明 |
|----------|------|
| `assets/{id}-w800.webp` | 慢网 |
| `assets/{id}-w1600.webp` | 主展示 `displayFile` |
| `assets/{id}-w2400.webp` | 可选 |

质量：WebP quality **82**（可配置）。长边缩放，不放大。

### 3.4 构图裁切（可选 · 默认关闭）

**默认** `config.ingest.generate_crops: false`：ingest 仅 **等比缩放** WebP，不预裁 9:16 / 16:9。展示层用 CSS `object-fit: contain`，完整保留用户构图。

`generate_crops: true` 时（旧行为 / 特殊导出）：

| 文件 | 比例 | 算法 |
|------|------|------|
| `{id}-m.webp` | 9:16 | 中心裁切，中心点 `focalPoint` 默认 (0.5, 0.45) |
| `{id}-w.webp` | 16:9 | 同上 |

> **Demo / MVP 默认**：`config.demo.yaml` 与 `from-album` 均 `generate_crops: false`；`displayFile` 指向 `-w1600.webp`，渲染不再引用 `cropMobile` / `cropWeb`。

### 3.5 `assets[]` 图片条目

```json
{
  "id": "asset-001",
  "type": "image",
  "sourceFile": "source/IMG_001.heic",
  "displayFile": "assets/asset-001-w1600.webp",
  "srcset": [
    { "file": "assets/asset-001-w800.webp", "width": 800 },
    { "file": "assets/asset-001-w1600.webp", "width": 1600 }
  ],
  "cropMobile": "assets/asset-001-m.webp",
  "cropWeb": "assets/asset-001-w.webp",
  "focalPoint": { "x": 0.5, "y": 0.45 },
  "ingestBatchId": "batch-20250402-1430"
}
```

---

## 4. 去重

| 策略 | 说明 |
|------|------|
| 主 | perceptual hash（phash），汉明距离 < 8 视为同组 |
| 备 | 3 秒内同尺寸连拍 |

同组保留 **得分最高** 1–2 张（清晰度启发式 + 人脸可选 P1）。  
写入 `dedupeGroupId`；跳过写入 `assets` 的标记在日志，不删 source 拷贝。

---

## 5. 视频管线

### 5.1 限制

- 源文件 **≤15s**（超出 `E_INGEST_VIDEO_TOO_LONG`，提示用户裁剪）  
- 每 trip **≤3** 条

### 5.2 ffmpeg

```bash
# 循环片段 3–8s，静音，H.264
ffmpeg -y -i "{source}" -t 6 -an -vf "scale=1280:-2" \
  -c:v libx264 -pix_fmt yuv420p -movflags +faststart \
  "assets/{id}-clip.mp4"

# poster
ffmpeg -y -i "{source}" -ss 1 -vframes 1 \
  "assets/{id}-poster.jpg"
```

- 检测原声：`ffprobe` → `hasAudio`  
- `duration` 记录源时长；`displayFile` 指向 clip。

### 5.3 条目示例

```json
{
  "id": "vid-001",
  "type": "video",
  "sourceFile": "source/CLIP.mov",
  "displayFile": "assets/vid-001-clip.mp4",
  "posterFile": "assets/vid-001-poster.jpg",
  "duration": 12.5,
  "hasAudio": true
}
```

---

## 6. 语音与 ASR

| 步骤 | 说明 |
|------|------|
| 拷贝 | `assets/{assetId}-voice.m4a` |
| ASR | MVP 可配置关闭；开启则写 `voice.transcript` |
| 预览 | `transcriptPreview` 前 40 字 |

**不在此阶段写 caption**（属 Agent 2）。

---

## 7. 地理反查

- `config.geocode.enabled: false` 时：`place.city = "未知"` 或省略。  
- 启用时：GPS → 城市级；**不写入**街道、门牌。  
- 反查结果缓存：`trips/.geocode-cache.json`（本地）。

---

## 8. 隐私（ingest 阶段）

- `trip.json` 可保留精确 GPS 供策展；**展示与导出**由 export 剥离。  
- 日志禁止打印经纬度。

---

## 9. 批次 `ingestBatchId`

格式：`batch-YYYYMMDD-HHMM` 或 CLI `--batch-id`。  
写入每个新 asset；更新 `pipeline.lastBatchId`。

---

## 10. 完成后状态

- `pipeline.status = ingest_ready`  
- `pipeline.pendingAssets`：若结构已锁，新 asset id 列入

---

## 11. 体积预算（ADR-001 · 强制）

> MVP **不**采用 Base64 内嵌大图；通过 ingest 控制 **zip 包** 总体积。

| 项目 | 目标 | 说明 |
|------|------|------|
| 单张 WebP w1600 | 约 200–400KB | quality ~82，长边 1600 |
| 单张 WebP w800 | 约 80–150KB | 慢网 / srcset |
| 单段循环视频 | **≤1.5MB** | 3–8s，H.264，宽 ~1280，无音轨 |
| 整包 zip | **≤25MB** | 30 图 + 3 视频 + 语音（可配置） |
| 单 HTML 文件 | **<500KB** | 仅 markup + 外链 css，无内联大图 |

### 11.1 视频 ffmpeg 推荐参数

```bash
ffmpeg -y -i "{source}" -t 6 -an \
  -vf "scale=min(1280\,iw):-2" \
  -c:v libx264 -crf 28 -preset medium \
  -pix_fmt yuv420p -movflags +faststart \
  "assets/{id}-clip.mp4"
```

若超出 1.5MB：提高 `crf` 或缩短 `-t`，记录警告。

### 11.2 与「单文件 HTML」的关系

| 方案 | MVP |
|------|-----|
| 相对路径 + zip | ✅ 默认 |
| Base64 自包含 | ❌ P2 可选 |

---

## 12. 视觉语义标签（ADR-001）

**职责**：为 Agent 2 提供「图里有什么」，**禁止**在 Agent 0 写 caption/正文。

### 12.1 输出字段

```json
{
  "tags": ["雨天", "石板路", "夜景", "纸伞"],
  "tagsSource": "heuristic"
}
```

| `tagsSource` | 阶段 |
|--------------|------|
| `heuristic` | P0：文件名、连拍、时段、城市 |
| `clip` | P0.5：本地 CLIP 零样本/标签表 |
| `vlm` | P1：本地 Moondream2 等，仅输出标签列表 |
| `user` | 用户在 G1 修改/追加 |

每图 **3–5 个** 标签为宜；最多 8 个（schema）。

### 12.2 实现原则

- **不**调用云端 Vision API（MVP 默认）。  
- **不**把原图发给云端 LLM。  
- 可选：对 w800 缩略图跑本地模型，失败则降级 `heuristic`。  
- 标签语言：中文优先，与 `NARRATIVE-PROMPTS` 一致。

### 12.3 配置（`config.yaml`）

```yaml
vision:
  enabled: false
  provider: clip  # clip | vlm | none
  max_tags_per_asset: 5
```

---

## 13. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-05-19 | 初稿 |
| v0.2 | 2026-05-19 | ADR-001：体积预算、视觉标签 |
