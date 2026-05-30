# ADR-011 · 延迟导入策略

| 属性 | 内容 |
|------|------|
| **状态** | 已采纳 |
| **日期** | 2026-05-30 |
| **影响范围** | `travelogue/media/`、`travelogue/render/`、`travelogue/web/`、`travelogue/curation/` |

---

## 背景

模块间存在合理循环依赖（例如 `media.ingest` ↔ `media.user_tier`）。审查报告指出延迟导入策略不统一，增加阅读成本。

---

## 决策

### 默认：模块顶层 import

适用于 **无循环依赖** 的稳定依赖（`color_metrics`、`media_classify`、`vision.cache`、`studio_constants` 等）。

### 允许延迟 import 的场景

| 场景 | 示例 | 放置位置 |
|------|------|----------|
| 打破循环依赖 | `user_tier` ← → `ingest` | 函数体首行，附一行注释 `# breaks ingest ↔ user_tier cycle` |
| 可选/重型依赖 | `pillow_heif`、`playwright` | 仅在使用前 import |
| 避免 CLI 冷启动成本 | 少数 `cli.py` 子命令 | 命令函数内 import |

### 禁止

- 在 **热循环**（每张照片、每个 slot）内重复 import — 应提到模块顶或循环外一次。
- 无注释的「神秘」延迟 import。

---

## 后果

- `ingest.py`：`user_tier` 仍在 `_scan_photos_for_ingest` / `_process_one_ingest_photo` / `_build_asset_entry` 内延迟导入；其余 ingest 依赖已顶层化。
- 新代码审查时先查 import 图，再决定顶层或延迟。

---

## 关联

- [ADR-010](./010-tech-debt-sprint.md)（handlers / render 分层）
