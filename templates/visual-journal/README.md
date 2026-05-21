# Visual Journal 模板 v0.2.1

## 文档

- 文档索引：`docs/README.md`
- 模板 PRD：`docs/TEMPLATE-visual-journal.md`（主规格）
- 数据模型：`docs/DATA-MODEL.md` · `schemas/trip.schema.json`
- 终端自适应：`docs/ADAPTIVE-LAYOUT.md`
- 金样例清单：`GOLDEN-CHECKLIST.md`
- 规则：`manifest.json`

## 金样例文件

| 文件 | 说明 |
|------|------|
| `golden.html` + `golden.css` + `longshot.js` | 开发预览（顶栏切换 + **一键保存长图**） |
| `golden-web-screens.html` | **layoutEngine=screens** 静态预览（对照 golden.html） |
| `longshot.js` + `longshot.css` + `vendor/html2canvas.min.js` | 用户可选：保存整页竖版 PNG |
| `golden-share.html` | 分享导出形态（仅 `journal.css`，无预览脚本） |
| `golden-minimal.html` | 空状态（无 hook、无 voice 等） |
| `cover-share.html` | `preview.jpg` 版式对照画布 |
| `journal.css` | 用户 zip 交付样式 |
| `assets/demo/*.webp` | 演示图（`gen_demo_assets.py` 生成） |

## 预览

```powershell
start "" "C:\Users\xiafe\projects\travelogue\templates\visual-journal\golden.html"
```

顶栏可切换 **自适应 / 朋友圈 9:16 / Web 16:9**；也可拖拽浏览器宽度（断点 **768px / 48rem**）。详见 `docs/ADAPTIVE-LAYOUT.md`。

**保存长图**（**P0**）：右下角 FAB / 金样例顶栏；9:16 竖版 PNG，适合 **微信群直发**（见 `docs/SHARING.md`）。默认 draft/share/zip 均开启；`export.longShot: false` 或 `export --no-longshot` 可关。需 `python -m http.server` 打开页面。私密完整 HTML → 小程序鉴权（P2，与长图分流）。

## 生成 / 更新

```powershell
python C:\Users\xiafe\projects\travelogue\scripts\gen_demo_assets.py
python C:\Users\xiafe\projects\travelogue\scripts\gen_golden_variants.py
```

**不要**运行 `gen_golden_html.py`（已废弃，会提示退出）。

修改 `golden.html` 后请运行 `gen_golden_variants.py` 同步 `golden-share.html`。

## 从 trip.json 渲染

```powershell
pip install -e ".[dev]"
# 将 trip.json 与 assets/ 放在同一目录后：
travelogue render path\to\trip.json
travelogue render path\to\trip.json --mode share
travelogue preview path\to\trip.json
travelogue export path\to\trip.json --confirm-privacy
travelogue publish path\to\trip.json
```

模板入口：`journal.hbs` · 规格见 `docs/RENDER-CONTRACT.md`。

## v0.2.1 要点

| 形态 | 比例 | 表现 |
|------|------|------|
| 手机 | 9:16 | 全宽出血、深色底、标题叠在图下缘 |
| Web | 16:9 | 横图大图、浅色底、标题在图下 |

- 主图：`<img srcset>` + `media-card--bleed` + `media-card--fill` + `media-card--overlay`
- 四章 pattern + 附录 `media-row`
- 语音在图下 `voice-bar`（CSS 图标），转写默认折叠
- 导出：`data-export="share"` + `data-layout="mobile|web"`
