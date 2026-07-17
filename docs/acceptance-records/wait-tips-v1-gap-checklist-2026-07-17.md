# Wait Tips V1 · PRD 对照缺口清单（执行用）

| 属性 | 内容 |
|------|------|
| **对照** | [PRD-WAIT-TIPS-V1](../PRD-WAIT-TIPS-V1.md) **v0.2.0** · [ACCEPTANCE](../ACCEPTANCE-WAIT-TIPS-V1.md) · [IMPLEMENTATION](../IMPLEMENTATION-WAIT-TIPS-V1.md) |
| **日期** | 2026-07-17 |
| **分支** | `feat/wait-tips-v1-w0` |

> 编码合同已齐；本清单只列**仍开放或文档漂移**项，并标明谁执行。

---

## 总览

| 优先级 | ID | 项 | 类型 | 状态 |
|--------|-----|-----|------|------|
| P0 | G-01 | AC-WT-04 dismiss 持久化缺自动化 | 工程 | ✅ e2e |
| P0 | G-02 | AC-WT-08 reduced-motion 缺自动化 | 工程 | ✅ e2e |
| P1 | G-03 | AC-WT-02 手动翻页缺自动化 | 工程 | ✅ e2e |
| P1 | G-04 | PRD §9 缺 AC-WT-10（ACCEPTANCE 已有） | 文档 | ✅ 已回写 PRD |
| P1 | G-05 | Help PRD 缺「重播等待提示」W2 脚注（DOC-WT-12） | 文档 | ✅ Help v1.1.4 |
| P1 | G-06 | IMPLEMENTATION Kickoff 勾选未更新（分支已建） | 文档 | ✅ |
| P1 | G-07 | ACCEPTANCE 工程列未标 e2e 已绿项 | 文档 | ✅ |
| P2 | G-08 | 开 PR（相对 master 的 fix+test） | 流程 | ⏳ 分支已推送 · 本机无 `gh` · 用下方 Create PR 链接 |
| 人 | G-09 | QA-WT-03 / QA-WT-05 产品狗粮 | 手测 | ⏳ **非实现者** |
| 人 | G-10 | AC-WT-11 / AC-WT-12 主题完成门 | 观测 | ⏳ 编码后一周+手测签 |

---

## 已关闭（对照确认 · 不重复做）

| 范围 | 证据 |
|------|------|
| Doc / 评审 / 脚注 | Conditional Go · Help/FST/FTUE 脚注 |
| W0 FE-WT-01～10 | `wait-tips*.js` · `import-run` · overlays · analytics |
| W1 FE-WT-11～13 | `notifyWaitTipsJob` · reduced-motion · 埋点 |
| W2 FE-WT-14 | Help `replayWaitTips` |
| QA-WT-01/02/04 | 契约 + e2e mount/teardown |
| OQ-WT-01～05 | 已关闭 |

---

## 执行顺序（本轮）

1. G-01～G-03 扩 e2e  
2. G-04～G-07 文档回写  
3. 跑测试 · commit · push  
4. G-08 建 PR（或给出创建链接）  
5. G-09/G-10 **留给用户/非实现者**（清单内标明，不伪造签核）

---

## Create PR

https://github.com/warclover/travelogue/compare/master...feat/wait-tips-v1-w0?expand=1

相对 `master` 当前约 4 commits：viewed_count fix · e2e 扩面 · 文档缺口收口。
