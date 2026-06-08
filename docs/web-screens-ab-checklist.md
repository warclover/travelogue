# Web screens A/B 验收清单

对照同一 `trip.json` 的两份输出：

```powershell
.\scripts\compare-web-layout.ps1 trips\<tripId>
# 可选 -Serve → http://127.0.0.1:8766/index-legacy.html vs index-screens.html
```

## 相册建议（≥3 套）

| # | 相册 | tripId | 横/竖倾向 | 通过 |
|---|------|--------|-----------|------|
| 1 | 京都雨后 | `kyoto-2025` | 横多 | ☑ 2026-05 Web 原生比例 + 缩略图剔除 |
| 2 | （竖图为主） | 自建 tripId | 竖多 | ☐ · `workshop-pipeline.ps1` 或 `test_portrait_heavy_workshop` |
| 3 | （连拍/九宫格） | | 同主题多图 | ☐ |
| 4 | 林芝 | `linzhi` · `D:\Photos\林芝` | 大批量（≈250） | ☐ |

## 每套检查项

- [ ] **T-08** 章内为 `layout-screen--16x9`，无 legacy `media-row` 混入 screens 页
- [ ] **T-09** 竖×3 为 cover 拼满，无明显竖缝
- [ ] **T-10** 横/竖 4·9 宫格在素材足够时出现
- [ ] **T-11** `layout` 输出含屏级摘要（pattern 统计）
- [ ] **T-12** legacy 页仍可开、长图按钮行为符合预期
- [x] 单竖为 **cover 满屏** / 竖屏 **3:4 舞台**（`--screen-aspect`）
- [x] 单张横图 **原生比例**，非扁条 stack
- [ ] 若有 `P+L+L` 邻近序列，出现 **screen-portrait-1-landscape-2**
- [ ] 裁切可接受（人脸/主体未严重切掉）
- [ ] 章标题与叙事节奏仍合理

## BSP 页面优化（仙本那 `demo-d66fe642a9` · 必测双视口）

| 视口 | 配置 | 检查 |
|------|------|------|
| **P0 笔记本 3:2** | Playwright `1440×960` · `deviceScaleFactor: 2` | AC-BSP-02a：full-frame 横图高度 ≥62vh · 无左右信箱 |
| **P1 外接 16:9** | `2560×1440` 最大化 | AC-BSP-02b：同屏高度 ≥58vh · 全出血 |
| **S3 节奏** | breath-pause index 5/10 | AC-BSP-01：与相邻 `layout-screen` 同宽（±1px）· 无穿帮线 |

- [ ] 重跑 render（或应用排版）后打开 `trips/demo-d66fe642a9/index.html`
- [x] 自动化：`pytest tests/test_bsp_surface_playwright.py`（AC-BSP-01～04 · S1 · 林芝 026–028）
- [x] 报告脚本：`python scripts/bsp_surface_report.py`
- [ ] 人工盲评：Surface 四维度 ≥4/5（见 ROADMAP §8.3）
- [ ] Studio preview-toolbar **展开**状态下测 vh（分母 `window.innerHeight`）

## 结论

| 项 | 填写 |
|----|------|
| 是否将默认引擎保持 `screens` | ☐ 是 / ☐ 回退 legacy |
| 备注 | |
