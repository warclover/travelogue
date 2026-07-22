# CSC · 合入前轻测记录 · 2026-07-22

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | **active** |
| **分支** | `feat/csc-w0-recipe` |
| **Studio** | `http://127.0.0.1:8766/`（已运行进程） |
| **结论** | **Pass · 可合 master** |

---

## 1. 本地棘轮 / 单测

| 检查 | 结果 |
|------|------|
| `lint_layout_engine_facade.py` | Pass · 0 |
| `lint_csc_god_module_ratchet.py` | Pass · curate 1830 / pipeline 1127 |
| `lint_csc_debt_table.py` | Pass · 24 |
| `lint_csc_recipe_baseline.py` | Pass · 97 True / 53 False · L1=3 |
| `test_happy_path_recipe.py` | Pass · 5 |

## 2. UI · H0（F-CSC-3）

| 步骤 | 结果 |
|------|------|
| `/?help=H0` 打开帮助抽屉并展开 H0 | **Pass** |
| 设置 → 导入与分析 →「默认这一趟做什么 →」 | **Pass**（`data-cscHelpBound=1`） |
| 实验选项 `#v2-settings-experimental` 默认折叠 | **Pass** |

## 3. 主路径烟测（未开实验选项）

| 步骤 | 结果 |
|------|------|
| 首页主 CTA 可见；无 admin 锚点 | **Pass** |
| 打开既有画册预览（demo-815dc906d3 · 张智慧精选） | **Pass** |
| 点「发微信群/长图」导出 | **Pass** · ~12s 完成 |
| 预览页无 G1 设置控件 | **Pass** |
| L1 设置点击（本会话） | **0**（≤2） |

## 4. Admin HAR / 资源

| 检查 | 结果 |
|------|------|
| 首页 DOM 含 `templates-admin` / `lse-flags-admin` | **无** |
| `performance` 资源名匹配 admin | **0 次** |
| Network filter `admin`（首页→预览） | **无命中** |

---

## 狗粮勾选（回写 CSC-W1-05）

- [x] 空态/`?help=H0` 能看到 H0  
- [x] 设置 →「默认这一趟做什么 →」打开 H0  
- [x] 预览→长图：**未**打开实验选项也能完成  
- [x] 首趟相关 L1 设置点击 ≤2（本测 = 0）  
- [x] Network/资源：无 `templates-admin` / `lse-flags-admin`  

> 说明：本测用既有 demo 画册验证「预览→长图」主路径，未重跑冷启动全量导入；导入主 CTA 与设置隔离已单独检视。
