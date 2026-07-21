# SFI · 已完成波次补漏记录（2026-07-21）

| 属性 | 内容 |
|------|------|
| 分支 | `feat/share-face-integrity-w0` |
| 范围 | W0/W1 宣称完成后对照 PRD 的遗漏补齐（非 W2 紧凑档） |
| 相关 | [IMPLEMENTATION](../IMPLEMENTATION-SHARE-FACE-INTEGRITY-V1.md) · [ACCEPTANCE](../ACCEPTANCE-SHARE-FACE-INTEGRITY-V1.md) |

## 工程补齐

| 项 | 结果 |
|----|------|
| **FX-SFI-03 产物债** | 本机 `demo-1d4f92d534` 重 curate + 重渲；章名 `6月30日` / `6月30日 · 傍晚` / `7月1日`；长图无「2018–2020」；`asset-250`（2020-11-30）标 `timeOutlier`（单张不剥附录） |
| **rerender 长图假写** | 修复 `rerender_draft_trip`：不再仅因文件存在而宣称已写；screens / 既有 longshot 必调 `write_longshot_sidecar`（根因：`exportLayout=mobile` 时 bridge 门禁跳过 sidecar） |
| **精修单张移回原章** | 精修 sheet「这页」在 `data-appendix=1` 屏增加「移回原章」→ `restoreTimeOutlier` + 单 `assetId` |
| **D-SFI-06 矛盾抑年** | `format_moment_exif_line(..., day_span=)`；与章 `daySpan` 矛盾时抑绝对年份 |
| **§6 刷新失败句** | toast「这次没写完，稍后再试 · 原文案保持不变」 |
| **§7 埋点** | `copy_refresh_*` · `outlier_isolated` · `export_renamed` · `album_rerender_batch` 入 FE/BE allowlist 并接线 |
| **IME 防抖** | 分章行内改名 composition 保护 |
| **QA-SFI-03** | `tests/unit/web/test_sfi_qa03_contracts.py`（含 AC-SFI-11 FST 忙碌态前置核验） |

## 仍开（非本轮）

- 产品手测列 / 线框 F0–F3 手测对照 / 狗粮签字  
- W2：FE-SFI-09～12 · QA-SFI-06 盲评模板 · AC-SFI-15 真人门  

## 核验命令（本机）

```text
python -m travelogue curate demo-1d4f92d534
python scripts/sfi_rerender_trips.py --only demo-1d4f92d534
python -m pytest tests/unit/web/test_sfi_qa03_contracts.py tests/unit/curation/test_time_outlier_sfi.py tests/unit/render/test_serve_rerender.py tests/unit/web/test_ftue_telemetry.py -q
```
