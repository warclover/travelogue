# Output Recipe Phase A · H-A 手测记录 · 2026-07-16

| 属性 | 内容 |
|------|------|
| **日期** | 2026-07-16 |
| **范围** | ACCEPTANCE-OUTPUT-RECIPE-V1.md §4 H-A-01～09 + NR-EXP-C1～C3 |
| **环境** | 本机 Studio `http://127.0.0.1:8766`（重启后新进程）；`studio.output_recipe.enabled=true` |
| **执行** | Agent 浏览器走查 + 实时 API/导出 Job + persona Playwright（8） |
| **对照** | [ACCEPTANCE-OUTPUT-RECIPE-V1.md](../ACCEPTANCE-OUTPUT-RECIPE-V1.md) |

---

## 1. 前置

| 检查 | 结果 |
|------|------|
| Studio 重启（替换旧 8766 进程） | ✅ |
| `GET /__travelogue/config` → `outputRecipe.enabled` | ✅ `true` |
| `GET /__travelogue/output-recipe?tripId=demo-album` | ✅ 200 · band=`sparse` · kept_n=6 |
| persona e2e `test_output_recipe_persona_playwright.py` | ✅ **8 passed** |

---

## 2. H-A 矩阵

| ID | 步骤 | 方法 / 证据 | 结果 |
|----|------|-------------|------|
| **H-A-01** | T-sparse 预览 · 无 pending · 主 CTA | 预览 `demo-album`：按钮 `aria-label="导出长图 · 发微信群"`；单击 → `POST /longshot` **202** → job 成功 → `demo-album-longshot.png`（356 904 B，19:01:50） | ✅ |
| **H-A-02** | T-amb 预览首次导出 | 合成 trip `ha-amb-18`（kept_n=18）：recipe `band=ambiguous` · `needs_intent=true`；无 intent 时 **400** `E_OR_INTENT_REQUIRED`；意图卡可见「微信群 / 九宫格 / 长图连读」+「选择并导出」（Writer 已开 → 对齐 H-B-01） | ✅ |
| **H-A-03** | 选「微信群长图」· 选择并导出 | `intent=chat_longshot` → **202** `job-e2a7914cde99`；产物 `ha-amb-18-longshot.png` | ✅ |
| **H-A-04** | 选「长图连读」· 选择并导出 | `intent=moments_scroll` → job **succeeded** · `platform=wechat_moments`；产物 `ha-amb-18-moments-01.png`…`07.png`；product/cta **不含「九宫格」** | ✅ |
| **H-A-05** | layoutPending 时点导出 | `preview-toolbar/longshot.js`：`if (_getLayoutPending())` 拦截块（约 L1725）在 `showAmbiguousIntentCard`（约 L1841）之前；persona/guards 已锁顺序 | ✅ |
| **H-A-06** | T-amb 书架保存长图（无 intent） | 客户端 shelf：`needsIntent=false` · hint「可到预览选择其他分享方式」；`LONGSHOT_PRESETS.shelf.entrypoint="shelf"`；服务端 `entrypoint=shelf` **202**（非 `E_OR_INTENT_REQUIRED`） | ✅ |
| **H-A-07** | T-deep ≥50 主 CTA | `resolveClientRecipe(55)` → band=`narrative` · CTA「按章导出长图 · 发微信群」；`needsFullExportConfirm(55,'full')===true` | ✅ |
| **H-A-08** | flag 关闭 | `enabled=false` → `needsIntent=false` · source=`flag_disabled` · CTA 回退「导出长图」；persona flag 用例绿 | ✅ |
| **H-A-09** | 失败后「换种分享方式」 | `longshot.js` 含「换种分享方式」+ `offerSwitchShareMethod`；与意图卡/高级入口接线存在 | ✅（接线级） |

---

## 3. 非回归（导出门面）

| ID | 标准 | 结果 |
|----|------|------|
| **NR-EXP-C1** | Sparse 无 pending → 1 次点击开始导出 | ✅ H-A-01 |
| **NR-EXP-C2** | pending 禁止静默旧长图 | ✅ H-A-05 静态顺序 |
| **NR-EXP-C3** | 用户可见词不回潮「应用排版」等旧词 | ✅ Trust/facade 合同已跟「长图连读」口径；本次扫描未见旧词回潮 |

---

## 4. Go / No-Go（本轮）

| 闸门 | 结论 |
|------|------|
| H-A-01～09 | **Go（签字级 · Agent 手测）** |
| NR-EXP-C1～C3 | **Go** |
| Phase A → B（文档 §8） | **Conditional Go** — 自动化+本轮手测齐；建议再补 ≥1 名非作者真人走 H-A-02～04 |
| 九宫格（Phase B） | Writer 已开，意图卡已露出可点「九宫格」→ 可开 H-B 清单；本轮未签 H-B-01～05 真人分名 |

---

## 5. 产物与辅助

- Sparse：`trips/demo-album/demo-album-longshot.png`
- Ambiguous：`trips/ha-amb-18/`（`*-longshot.png` · `*-moments-0N.png`）
- 自动化：`python -m pytest tests/e2e/test_output_recipe_persona_playwright.py -q` → 8 passed
- 实时 harness（可选）：`scripts/_ha_handtest_live.py`

---

## 6. 签字

| 角色 | 签字 | 日期 |
|------|------|------|
| 执行（Agent） | ✅ H-A-01～09 / NR-EXP-C1～C3 | 2026-07-16 |
| 产品 / 非实现者复核 | ☐ 建议补 1 次真人 Ambiguous 发群 | |

**结论**：Output Recipe Phase A 手测清单 **H-A-01～09 本轮通过**；发布前仍建议 1 名非作者复测 Ambiguous 意图卡 → 发群路径。
