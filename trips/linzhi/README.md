# linzhi · 体验样例（版本库内仅跟踪覆盖层）

本目录为本地生成的完整 trip；**Git 只跟踪** 阅读体验相关的 HTML/JS/CSS 覆盖文件，不跟踪相册原图、渲染产物与缓存。

## 纳入版本控制

- `*.js`、`*.css`
- `index.html`、`index-mobile.html`、`index-longshot.html`
- 本 `README.md`

## 不纳入版本控制（保持本地）

- `source/`、`assets/`、`runs/`、`.cache/`、`vendor/`
- `trip.json`、`preview.jpg`、`*.png`、`*.zip`

首次克隆后需在本机用 Studio/CLI 生成完整 trip，或将已有 `trips/linzhi` 从备份恢复。
