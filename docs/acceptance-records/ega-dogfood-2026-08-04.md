# EGA 狗粮 · 2026-08-04（PR-A/B/C 收口 · 实册实测）

| 项 | 值 |
|----|-----|
| 范围 | EGA PR-A/B/C · 观测 SHD-01/02 · 文档收口 |
| EGA enabled | true（仓库默认） |
| 册 | `demo-0ebda73294`（锚点）· `demo-2019`（AC-08） |
| SSG / MEGC | 保持 on |
| Studio | http://127.0.0.1:8766/demo-0ebda73294/index.html |

---

## AC-05（锚点）

- [x] **A** 成册 ≥1 L4 — 实测 **1×** `screen-landscape-4`（`ch-03-sc-10` · asset-085…088）
- [x] **B 进池无 hard 拒**（091–094 / 096–099 候选池仍绿）

### A · 成册胜出证据

| screenId | pattern | winnerReasonCodes（摘） |
|----------|---------|-------------------------|
| ch-03-sc-10 | `screen-landscape-4` | `R_EGA_FLAT_BONUS` · `R_EGA_CLONE_SOFT` · `R_MEGC_PEAK_MISMATCH` · `R_LTE_WEIGHT_UP` |

对照：仍有 1× `hero-70`（带 `R_EGA_WASTED_HERO` / `R_MAIN_NOT_WINDOW_BEST`）→ 符合「不强制」。

### B · 原四横窗候选池（历史微探针）

| 窗 | L4 进池 | L4 hard anti_slice/clone |
|----|---------|--------------------------|
| asset-091…094 | ✅ 1 | `[]` |
| asset-096…099 | ✅ 1 | `[]` |

---

## AC-06 / PR-B · size=6 / L6

| 项 | 结果 |
|----|------|
| 成册 `landscape-6` | **0**（胜出非必须） |
| 持久化 log | 可见 `six_hero_precheck`；SHD-01 后 summary 保留 `egaEqualSixKept` / `egaEnabled` |
| 单测 / 微探针 | L6 进入 try 集 · hero `ega_equal_six_only` |

---

## AC-07 / PR-C

| 项 | 结果 |
|----|------|
| 单测 flat 4L · L4 ≥ hero-70 | ✅ `test_ega_pr_c` |
| 成册 | L4 胜出带 `R_EGA_FLAT_BONUS`；hero 带 `R_EGA_WASTED_HERO` |

---

## AC-08 / BLK-EGA-06

- 单测：cross 硬拒 + MEGC 16:9 `gate_allow` ✅  
- demo-2019 冻结 L4：2× `sixteen_nine` 仍 `gate_allow` ✅  

---

## 直方图（锚点实测 · 节选）

| pattern | count |
|---------|------:|
| landscape-4 | **1** |
| landscape-6 | 0 |
| mosaic-4-hero-70-sidebar | 1 |
| landscape-1 | 多 |

---

## 四问

1. 等权四宫进池 / 胜出 — **Pass（A+B）**
2. 假切条回潮 — cross 单测绿 — **Pass**
3. 有主图仍可选 hero — 成册仍有 hero-70 — **Pass**
4. 3:2 观感 — L4 带 MEGC soft 仍可胜；更多 3:2 四宫属 M3 — **持平**

## 结论

**PR-A/B/C 实册收口通过**（G-06 A+B）。M3 / AC-09 仍延期。观测 SHD-01/02 已接线；下次 re-layout 后 trip log 应可见 `egaEnabled` / `egaEqualSixKept`。
