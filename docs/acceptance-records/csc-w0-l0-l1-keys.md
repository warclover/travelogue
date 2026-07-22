# CSC W0 · L0 / L1 键表草案（CSC-W0-06）

| 属性 | 内容 |
|------|------|
| **日期** | 2026-07-22 |
| **代码真相** | `travelogue/orchestrator/happy_path_recipe.py` · `L0_OPS_ROOTS` / `L1_RESULT_KEYS` / `ADVANCED_SETTINGS_KEYS` |
| **设置库存** | [csc-w0-settings-surface-inventory.md](./csc-w0-settings-surface-inventory.md) |

---

## L0 · 运维根（不计入 ≤10）

| 根 | 含义 | 设置 UI |
|----|------|---------|
| `trips_dir` | 作品目录 | 一般不暴露 |
| `llm` | 写作引擎 / Key | AI 文案区（可选） |
| `ffmpeg` | 占位/媒体工具 | 不进设置 |
| `geocode` | 地理编码 | 不进设置；默认关 |

## L1 · 结果旋钮（预算 ≤10 · 当前 3）

| 键 | 用户语言 | 默认 | W1 常用区 |
|----|----------|------|-----------|
| `clustering.enabled` | 行程识别 | `auto`（TriState str） | ✅ |
| `vision.enabled` | 场景分析 | `false` | ✅ |
| `ingest.copy_source_files` | 导入时复制源文件 | `true` | ✅ |

预留名额：7（配方 / 轻控制出口等，须替换预算，禁止净增超 10）。

## Advanced / Danger（可见但非 L1）

| 键 | 档 | 默认 |
|----|----|------|
| `layout.scoring.enabled` | Advanced | `false` |
| `studio.g1_confirm_structure` | Danger | `false` |

## 非 AppConfig

| 项 | 归类 |
|----|------|
| 首页配色 theme | UI-local |
| 清理磁盘 | Ops action |
