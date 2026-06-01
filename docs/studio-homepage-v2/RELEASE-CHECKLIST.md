# Studio 首页 v2 · 发布与 PR 清单

> P4-25 · 合入 main 前自检（**不**替代 CI）。

---

## 1. 分支与 PR

- [ ] 功能分支名含 `studio-homepage-v2` 或 `m20`
- [ ] PR 标题示例：`feat(studio): homepage v2 holdback + M20-j gate`
- [ ] PR body 含 **Test plan**（见 §2）
- [ ] 不提交 `.claude/`、本地 `项目总结*.md`、`* .local.json`

---

## 2. Test plan（复制进 PR）

```markdown
## Test plan
- [ ] `pytest tests/test_studio_home_v2_ac_playwright.py -q`
- [ ] `pytest tests/test_studio_home_v2.py -k gate -q`
- [ ] `pytest tests/test_studio_homepage_gate.py -q`
- [ ] `python scripts/studio_homepage_rollback_drill.py`
- [ ] `GET /` off 模式仍 v3（本地 serve）
- [ ] 设计切图（若本 PR 含素材）manifest schema 通过
```

---

## 3. CI 期望

| Job | 说明 |
|-----|------|
| `test-pr` | 单元 + 非 e2e |
| `test-e2e` | Playwright + gate e2e |
| `nightly-holdback` | 每日 funnel + LCP 审计 |

---

## 4. 文档同步

合入时确认已更新（若本 PR 触及）：

- [FEATURE-FLAG.md](./FEATURE-FLAG.md)
- [AC-VERIFICATION.md](./AC-VERIFICATION.md)
- [OPEN-QUESTIONS.md](./OPEN-QUESTIONS.md)
- [SIGNOFF-M20J.md](./SIGNOFF-M20J.md) 签字栏（仅 PM 合并后填）

---

## 5. 合入后（非本 PR 阻塞）

- [ ] Dogfood 按 [RUNBOOK-DOGFOOD.md](./RUNBOOK-DOGFOOD.md) 开 10% 观察窗
- [ ] 更新 `studio-homepage-v2-rollout-log.json` entries
- [ ] **勿** 默认生产 `TRAVELOGUE_STUDIO_HOMEPAGE_V2=on` 直至 SIGNOFF 全绿
