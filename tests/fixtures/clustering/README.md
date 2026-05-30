# Phase 3 · M12-0 Golden Fixtures

| Trip ID | 目录 | GPS | 用途 |
|---------|------|-----|------|
| `golden-kyoto-gps` | `golden-kyoto-gps/` | ✅ | SP-C01 多日 stay |
| `golden-no-gps` | `golden-no-gps/` | ❌ | date_fallback |
| `golden-mixed-scenes` | `golden-mixed-scenes/` | ✅ | SP-C01 + SP-C02 |
| `synthetic-gps` | `synthetic-gps/` | ✅ | 同日双城 smoke |
| `golden-gap-edge` | `golden-gap-edge/` | ✅ | AC-P6-03 午餐间隔 / auto gap |
| `golden-cluster-noise` | `golden-cluster-noise/` | ❌ | AC-P6-02 DBSCAN vs HDBSCAN 噪声 |

## 从本地 trip 导出

```bash
python scripts/export_clustering_fixture.py trips/linzhi --trip-id golden-kyoto-gps
python scripts/export_clustering_fixture.py trips/mao --trip-id golden-no-gps --strip-geo
```

导出后 **必须** 手工编辑 `segments-golden.json` 标注 event 边界。

## 验收

```bash
pytest tests/test_clustering_spike.py -q
```
