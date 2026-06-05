# Algorithm V2 · Kendall τ Report

- Source: `tests\fixtures\cover_v2_kendall_albums.json`
- Albums: **10**
- Mean Kendall τ: **1.0** (gate A-M1 ≥ 0.85)
- Cover changes (top-1): **0** (gate A-M7 ≤ 3/10)

> 故意 v1/v2 排序反转（如 `dateConfidence=low` 高清晰度图）不计入本报告；见 `test_v2_demotes_low_date_confidence_vs_v1`。

| albumId | τ | coverChanged | v1Top3 | v2Top3 |
|---------|---|--------------|--------|--------|
| kendall-mobile-sharp | 1.0 | False | ['m1', 'm2'] | ['m1', 'm2'] |
| kendall-mobile-color | 1.0 | False | ['vivid', 'dull'] | ['vivid', 'dull'] |
| kendall-mobile-thirds | 1.0 | False | ['thirds', 'center'] | ['thirds', 'center'] |
| kendall-mobile-tall | 1.0 | False | ['tall', 'port'] | ['tall', 'port'] |
| kendall-mobile-landscape-excluded | 1.0 | False | ['p1'] | ['p1'] |
| kendall-web-landscape | 1.0 | False | ['wide', 'pano'] | ['wide', 'pano'] |
| kendall-web-sharp | 1.0 | False | ['sharp16', 'soft16'] | ['sharp16', 'soft16'] |
| kendall-mobile-mixed5 | 1.0 | False | ['a', 'b', 'c'] | ['a', 'b', 'c'] |
| kendall-mobile-featured | 1.0 | False | ['feat'] | ['feat'] |
| kendall-mobile-balanced | 1.0 | False | ['x1', 'x2'] | ['x1', 'x2'] |
