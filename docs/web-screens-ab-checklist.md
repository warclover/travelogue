# Web screens A/B 验收清单

对照同一 `trip.json` 的两份输出：

```powershell
.\scripts\compare-web-layout.ps1 trips\<tripId>
# 可选 -Serve → http://127.0.0.1:8766/index-legacy.html vs index-screens.html
```

## 相册建议（≥3 套）

| # | 相册 | tripId | 横/竖倾向 | 通过 |
|---|------|--------|-----------|------|
| 1 | 京都雨后 | `demo-kyoto-2025` | 横多 | ☐ |
| 2 | （竖图为主） | | 竖多 | ☐ |
| 3 | （连拍/九宫格） | | 同主题多图 | ☐ |

## 每套检查项

- [ ] **T-08** 章内为 `layout-screen--16x9`，无 legacy `media-row` 混入 screens 页
- [ ] **T-09** 竖×3 为 cover 拼满，无明显竖缝
- [ ] **T-10** 横/竖 4·9 宫格在素材足够时出现
- [ ] **T-11** `layout` 输出含屏级摘要（pattern 统计）
- [ ] **T-12** legacy 页仍可开、长图按钮行为符合预期
- [ ] 单竖为 **cover 满屏**，非 contain 信箱
- [ ] 若有 `P+L+L` 邻近序列，出现 **screen-portrait-1-landscape-2**
- [ ] 裁切可接受（人脸/主体未严重切掉）
- [ ] 章标题与叙事节奏仍合理

## 结论

| 项 | 填写 |
|----|------|
| 是否将默认引擎保持 `screens` | ☐ 是 / ☐ 回退 legacy |
| 备注 | |
