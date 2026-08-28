# B-03 · 损坏验收图放弃签字

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-28 |
| **决定** | 放弃恢复；不改扩展名、不补 CR、不重导 |
| **影响** | 无。全部在 `docs/`，不进 Studio / 导入 / 渲染 / 导出运行时 |
| **G2** | 清单 + 本签字即放行 |

## 扫描结果

`python scripts/lint_binary_assets.py` 对 Git 跟踪的 png/jpg/webp：

| 类别 | 数量 | 处置 |
|------|------|------|
| 签名无法识别（多为 PNG 被 text/eol 改写） | **216** | 放弃 |
| 扩展名 `.png`、内容是 JPEG | 51 | 放弃（文档草图，无运行时引用） |
| **合计** | **267** | 见 [b03-abandoned-binary-assets.txt](./b03-abandoned-binary-assets.txt) |

分布：`docs/acceptance-records` 206 · `docs/templates` 44 · `docs/wireframes` 17。`docs/` 以外 0。

## 门禁

B-04 `--strict` 只拦 **清单外的新漂移**。已放弃路径继续允许存在。
