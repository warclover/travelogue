# Shot Grouping fixtures (SSG)

| Fixture | Purpose | Status |
|---------|---------|--------|
| `mixed-scenes-synthetic/` | P-SSG-01 · ≥2 scenes · AC-01/02 | ✅ neighborPairs golden |
| `outfit-change-synthetic/` | P-SSG-02 · same place ≥3 looks + flash | ✅ PR-E 合成向量 + golden（锁 delta=0.28） |

Expected artifacts per trip dir (when added):

```
assets-manifest.json
shot-groups-golden.json   # { groups: [{ id, kind, assetIds }] }
README.md
```
