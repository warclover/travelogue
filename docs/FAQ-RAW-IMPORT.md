# 导入 FAQ · RAW 原片格式

> Phase 7 · [PRD-PHASE7-RAW-GATE.md](./PRD-PHASE7-RAW-GATE.md)

## 为什么导入失败并提示 RAW？

Travelogue 当前版本 **不支持** 相机 RAW 原片（如 `.CR3`、`.NEF`、`.ARW`、`.DNG` 等）的直接解码。若在文件夹扫描阶段检测到 RAW 文件，会立即返回错误码 `E_INGEST_RAW_UNSUPPORTED`，避免进入长时间 ingest 后才失败。

## 我应该怎么做？

1. 在 Lightroom、Capture One、相机厂商工具或系统相册中，将 RAW **导出/转换为 JPG**（建议 sRGB、长边 3000–6000px 即可）。
2. 重新选择 **仅含 JPG/HEIC 等支持格式** 的文件夹导入。
3. Studio 弹窗与 CLI 均会提示「先转 JPG 后重试」。

## 混合文件夹（RAW + JPG）会怎样？

默认 **整批阻断**。这样可避免「只导入了部分照片」的隐形风险。若文件夹中同时有 RAW 与 JPG，请先移除或转换 RAW 后再导入。

## HEIC / HEIF 会被误拦吗？

不会。HEIC/HEIF 走现有支持路径，不受 RAW 后缀清单影响。

## 如何关闭 RAW 拦截？（不推荐）

配置 `ingest.reject_raw: false` 可关闭拦截，但 RAW 仍无法在后续管线中正常处理，仅用于调试。

## 常见 RAW 后缀（首版清单）

`.cr2` `.cr3` `.nef` `.nrw` `.arw` `.srf` `.sr2` `.orf` `.rw2` `.pef` `.ptx` `.raf` `.dng` `.3fr` `.fff` `.mef` `.mos` `.raw` `.rwl` `.x3f`

完整列表见 `config.yaml.example` 中 `ingest.raw_blocklist_suffixes`。
