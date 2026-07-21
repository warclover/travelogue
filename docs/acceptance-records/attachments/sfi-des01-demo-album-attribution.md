# 长图归因表 · demo-album

- **展示名**：京都雨季漫游
- **样本**：`C:\Users\xiafe\Projects\travelogue\trips\demo-album` · `index-longshot.html`
- **方法**：playwright-y-union-css-px · 逻辑宽 428px
- **资产数（trip.json）**：6

## 纵向像素

| 指标 | 值 |
|------|-----|
| main 滚动高（CSS px） | 5657 |
| 照片 Y 并集高 | 4757 |
| 非照片纵向高 | 900 |
| **非照片纵向占比** | **15.9%** |
| 照片元素数 | 8 |
| 最大照片宽（CSS） | 428 |
| 章数 | 3 |

## 密度杠杆（默认档基线）

| 杠杆 | 观测 |
|------|------|
| 章头带 | count=3 · Σheight≈327px |
| 章名列表 | 05月27日, 5月27日, 5月27日 · 晚上 |
| 封面题名出现次数 | 1 · maxDup=1 |
| 封面题名文本 | ['京都雨季漫游'] |
| 复用资产（>1 次入屏） | 2 / unique=5 |
| 屏缝 | 合同保持 4px（CSS `--longshot-gap` / journal） |

## 处方对照（D-SFI-11）

| 杠杆 | 默认档现状 | 紧凑档处方 |
|------|------------|------------|
| 章头带 | 每章全头（见 Σheight） | 首章全头；第 2 章起 ≤48px |
| 封面文案 | 题名重复见 maxDup | 题名/日期各一次 |
| moment 复用 | reusedAssetCount | 代表图 + N 徽标 |
| 屏缝 | 4px | **保持 4px** |

> 非照片纵向占比 = 1 − (照片元素 Y 并集高度 / main.scrollHeight)；逻辑宽 428；与 PNG 逐行扫描同构（CSS px）
