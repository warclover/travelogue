# Shot Grouping fixtures (SSG)

| Fixture | Purpose | Status |
|---------|---------|--------|
| `mixed-scenes-*` | P-SSG-01 · ≥2 scenes mixed import | Contract: use / extend `tests/fixtures/clustering/golden-mixed-scenes` + expected shotGroups JSON (M0) |
| `outfit-change-synthetic/` | P-SSG-02 · same place ≥3 looks + flash | ✅ PR-E 合成向量 + golden（锁 delta=0.28） |

Expected artifacts per trip dir (when added):

```
assets-manifest.json
shot-groups-golden.json   # { groups: [{ id, kind, assetIds }] }
README.md
```
