# PRD-COVER-CALLIGRAPHY-TITLE-V1 · AC-CAL-01/02/10 验收记录

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-COVER-CALLIGRAPHY-TITLE-V1.md](../PRD-COVER-CALLIGRAPHY-TITLE-V1.md)（**CAL**） |
| **分支** | `feat/cover-calligraphy-title-v1` |
| **覆盖验收项** | **AC-CAL-01 / AC-CAL-02 / AC-CAL-10**（此前 §11 W2 写「已补齐」但 §12.3 未打勾、无专项留痕——本次正式钉死） |
| **日期** | 2026-08-08 |
| **方式** | 解析层合同单测 + 固定金样感知哈希（SHD-CAL-01）+ 真实 trip `index.html` / `index-longshot.html` 同源核对 |
| **结论** | **通过** |

---

## 0. 一句话结论

对照 PRD 清账时发现：§11 W2 里程碑把 AC-CAL-01～06 写成「全部已补齐」，但 §12.3 里 **AC-CAL-01 / 02 / 10** 从未打 ✅，也没有验收记录。本次补齐：`enabled=false`/无字段不叠加贴纸；干净管线相对固定 fixture 的 aHash 容差门禁；Web 预览与长图引用同一 `assetPath`。三项均 **通过**。

---

## 1. AC-CAL-01 · `enabled=false`（或无字段）时 Opening ≡ 现网 HTML 标题路径

断言口径：不叠加 `<img class="cover-opening__title-art">`（`hasTitleArt=false`），封面继续走原生 `<h1>`。

| 场景 | 结果 |
|------|------|
| 无 `titleArt` 字段 | PASS（`has=False`） |
| `enabled=false` | PASS |
| `enabled=true` 但 `stale=true` | PASS（按 §7 禁止展示旧贴纸） |
| `enabled=true` + 白名单 + 有效 `assetPath` | PASS（叠加，且带回 §10 归因文案） |

脚本：[`scripts/verify_title_art_ac01_02_10.py`](../../scripts/verify_title_art_ac01_02_10.py)  
单测：`tests/unit/cover_engine/test_title_art_ac01_02_10.py`

**结论：✅ 通过。**

---

## 2. AC-CAL-02 · 干净管线输出 + 固定 fixture 感知哈希（SHD-CAL-01）

| 项 | 内容 |
|----|------|
| 金样 | `tests/fixtures/title_art/ac02_clean_pipeline_golden.png`（`render_title_art("拾光")`，无风格衬底） |
| 算法 | 256-bit average hash（透明层先合成白底）；实现见 `travelogue/cover_engine/title_art/phash.py` |
| 容差 | Hamming ≤ 16（约 6%） |
| 实测 | Hamming **0** |

证据②（`02-clean-composite-sample.png`，1024×1024 RGB）是历史 demo 整幅合成参考，与现网「透明裁边 PNG」构图不同，**不参与门禁**；正式门禁以 fixture 金样为准（呼应七席 SHD-CAL-01）。

当前渲染副本：[`attachments/.../ac02-current-render.png`](./attachments/cover-calligraphy-title-v1-ac01-02-10-2026-08-08/ac02-current-render.png)

**结论：✅ 通过；SHD-CAL-01 落地。**

---

## 3. AC-CAL-10 · Web 预览与长图引用同一 `assetPath`

| 项 | 内容 |
|----|------|
| 真实 trip | `demo-0ebda73294` |
| `trip.json` | `trip-derived/title-art/39f0ae9b75b0.png` |
| `index.html` | 同上 |
| `index-longshot.html` | 同上 |

两侧 HTML 都经 `build_render_context` → `_resolve_title_art_src`，无第二套路径。

**结论：✅ 通过。**

---

## 4. 回归

```text
tests/unit/cover_engine/test_title_art_ac01_02_10.py + contract/models  20 passed
scripts/verify_title_art_ac01_02_10.py                                 OVERALL PASS
```

落盘：[`attachments/.../verify-output.txt`](./attachments/cover-calligraphy-title-v1-ac01-02-10-2026-08-08/verify-output.txt)
