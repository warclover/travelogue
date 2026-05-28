# golden-kyoto-gps

CI 用 · 3 日 3 stay（大阪 → 京都 → 东京），全 GPS。

- `assets-manifest.json` — 18 张
- `segments-golden.json` — 人工 event 边界（SP-C01）

本地真实相册导出：

```bash
python scripts/export_clustering_fixture.py trips/linzhi --trip-id golden-kyoto-gps --title "关西关东样本"
# 然后手工编辑 segments-golden.json
```
