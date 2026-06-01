# linzhi · 体验样例（版本库内仅跟踪覆盖层）

本目录为本地生成的完整 trip；**Git 只跟踪** 阅读体验相关的 HTML/JS/CSS 覆盖文件，不跟踪相册原图、渲染产物与缓存。

## 源文件 vs 生成物

| 类型 | 说明 | 版本库 |
|------|------|--------|
| **覆盖层** | `index*.html`、`journal*.css`、`longshot.js` 等阅读/动效定制 | 跟踪 |
| **数据面** | `trip.json`、章节图、`assets/`、`source/` 原片 | 不跟踪（本地或 CI 生成） |
| **渲染产物** | `runs/`、`preview.jpg`、章节 PNG | 不跟踪 |
| **第三方** | `vendor/`（如 html2canvas） | 不跟踪 |

`index.html` / `index-mobile.html` 由 pipeline 渲染后可在本目录覆盖；改样式/脚本请只动 Git 跟踪的文件，避免手改生成 HTML 后再被 render 覆盖（除非你明确要冻结一版体验快照）。

## 纳入版本控制

- `*.js`、`*.css`
- `index.html`、`index-mobile.html`、`index-longshot.html`
- 本 `README.md`

## 不纳入版本控制（保持本地）

- `source/`、`assets/`、`runs/`、`.cache/`、`vendor/`
- `trip.json`、`preview.jpg`、`*.png`、`*.zip`

首次克隆后需在本机用 Studio/CLI 生成完整 trip，或将已有 `trips/linzhi` 从备份恢复。
