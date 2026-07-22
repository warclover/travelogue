# NAS · e2e / DOC 收口记录（2026-07-22）

| 属性 | 内容 |
|------|------|
| **主题** | [PRD-NO-AI-SURFACE-V1](../PRD-NO-AI-SURFACE-V1.md) · [ACCEPTANCE](../ACCEPTANCE-NO-AI-SURFACE-V1.md) |
| **范围** | DOC-NAS-02 + 默认面 Playwright + 审计扩面 + shareCopyPack OUT-04 抽检 |
| **不含** | UI Detail 波次；dark 全套手测冒烟（仍 ☑） |

---

## 交付

### DOC-NAS-02

| 文档 | 变更 |
|------|------|
| `ERROR-CODES.md` | 已有 `E_AI_SURFACE_DISABLED`（既有） |
| `PRD-HELP-ONBOARDING-V1.md` §12.4 | H7 / 能力卡默认面 supersede → NAS |
| `PRD-SHARE-FACE-INTEGRITY-V1.md` + IMPLEMENTATION FE-SFI-04 | 默认面「重新生成文案」入口废止指针 |
| `csc-w1-happy-path-user-copy.md` | 去掉 AI bullet |
| `PRD-DESKTOP-LLM-SETUP` / WEA + 两份 ACCEPTANCE | 文首用户面 superseded |
| PRD §13 checklist | SFI/Help/CSC 责任人：产品合同 · 工程门控 |

### e2e

- 新增 `tests/e2e/test_studio_no_ai_surface_playwright.py`（AC-01/02/03/04/05/06/13/14/15/16）
- `test_studio_settings_observability_playwright.py`：默认面不再点开 AI zone → Modal

### 门禁

- `scripts/studio_no_ai_surface_audit.py`：扩 C.2 禁词 + W2 路径；剥离注释
- `tests/unit/domain/test_share_copy_pack_sfi.py`：OUT-04 / S6 禁词断言

---

## 仍开（非阻塞发版默认面）

- AC-NAS-07 / S8 整链狗粮手测
- AC-NAS-09 / 17b / D1–D5 dark 月度冒烟
- AC-NAS-12 全会话 Key 明文抽样

---

## 命令

```powershell
python scripts/studio_no_ai_surface_audit.py --wave w2
python -m pytest tests/unit/web/test_ai_surface_gate.py tests/unit/web/test_studio_no_ai_surface_audit.py tests/unit/domain/test_share_copy_pack_sfi.py -q
python -m pytest tests/e2e/test_studio_no_ai_surface_playwright.py -q
```
