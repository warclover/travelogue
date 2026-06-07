# Collage detector fixtures (Phase 16 · PRD §3.4)

Committed JPEG samples for `scripts/collage_detect_eval.py` (`kind: file`).

| File | Role |
|------|------|
| `collage-app-2x2.jpg` | 正例 · 2×2 网格拼图（像素级合成） |
| `exif-picsart-file.jpg` | 正例 · EXIF Software 白名单 |
| `photo-group-wide.jpg` | 负例 · 宽幅合影（纯色代理） |
| `building-facade.jpg` | 负例 · 规则建筑立面（纯色代理） |

Add real App 产物时：放入本目录并在 `docs/acceptance-records/collage-detect-fixtures.json` 增加 `{ "kind": "file", "path": "your.jpg", "expect": "collage"|"photo" }`。
