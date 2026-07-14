# 精修意图可感知闭环 V1 · 验收清单

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-REFINE-FEEDBACK-LOOP-V1.md](./PRD-REFINE-FEEDBACK-LOOP-V1.md) v0.1.2 |
| **实施清单** | [IMPLEMENTATION-REFINE-FEEDBACK-LOOP-V1.md](./IMPLEMENTATION-REFINE-FEEDBACK-LOOP-V1.md) |
| **线框** | [wireframes/refine-feedback-loop-v1-wireframe.html](./wireframes/refine-feedback-loop-v1-wireframe.html) |
| **状态** | **工程可合入 master（Conditional Go）** · M1+M2+P0 编码+静态门禁 ✅ · **AC-FEED-02 N≥5 真人待补** · M3 未开 · 正式评审纪要待补 |
| **日期** | 2026-07-14 |
| **静态门禁** | `tests/unit/web/test_refine_feedback_loop_v1.py` |

---

## 1. 里程碑完成度

| 里程碑 | 状态 | 说明 |
|--------|------|------|
| **M1** | ✅ | 首尾 tip/区头；★ 诚实文案；纯 ★ 不拦导出；分词对齐 |
| **M2** | ✅ | demote；「按精选重排」→确认→`/curate`；structure_locked 风险文案 |
| **P0 收口** | ✅ | Dock 次 CTA；★ toast→H2；放映空池说明；重排成功封面 toast；文档回写 |
| **M3** | ⏳ | `curate?scope=tier`；正式 N≥5 手测 AC-FEED-02 |

---

## 2. AC-FEED 手测清单

| ID | 用例 | 期望 | 工程狗粮 | 产品手测 |
|----|------|------|----------|----------|
| **AC-FEED-01** | 清 `bookendsPickSeen`；精修→这本→展开首尾 | tip + 区头含「点选」 | ✅ | ⏳ |
| **AC-FEED-02** | 无旁白新手换封面/封底 | ≤10s 成功（N≥5 建议 ≥4/5） | ⏳ | ⏳ |
| **AC-FEED-03** | 点候选缩略图 | 预览变；「已换封面/封底」；无工程 ID | ✅ | ⏳ |
| **AC-FEED-04** | 正文点 ★ | toast 无「点更新版面后生效」；可点「了解更多 →」开 H2 | ✅ | ⏳ |
| **AC-FEED-05** | 打开「这页」 | 精选语义常驻行 +「按精选重排」CTA | ✅ | ⏳ |
| **AC-FEED-06** | 帮助 H2 | 精选≠立刻重排；更新版面≠按精选重排 | ✅ | ⏳ |
| **AC-FEED-07** | 仅改拼图 | pending；更新版面后可感知变化 | ✅ | ⏳ |
| **AC-FEED-08** | 仅标 ★ | **不**弹「版面尚未更新」导出拦截 | ✅ | ⏳ |
| **AC-FEED-09** | media pending | Dock 主 CTA「更新版面」；不承诺精选换构图 | ✅ | ⏳ |
| **AC-FEED-10** | Dock/这页「按精选重排」 | 确认 Modal → 进度 → 刷新；busy 无教学 tip | ✅ | ⏳ |
| **AC-FEED-11** | 抽检 toast / Modal / H2 / hint | 分词表零冲突 | ✅ | ⏳ |
| **AC-FEED-12** | 导出中 / 更新版面中 | 不弹 T-BE-OPEN | ✅ | ⏳ |
| **AC-FEED-13** | 取消精选 | ★ 灭；可再标 | ✅ | ⏳ |
| **AC-FEED-14** | structure_locked 下重排 | Modal 有风险说明；取消不调 curate | ✅ | ⏳ |
| **AC-FEED-15** | 重播操作提示 | 可再出现 T-BE-OPEN | ✅ | ⏳ |
| **AC-FEED-P0a** | 标 ★ 后 | Dock 出现「按精选重排」次路径 | ✅ | ⏳ |
| **AC-FEED-P0b** | 导出 Tab「放映精选」空池 | 可见说明「先在正文点 ★」；按钮禁用 | ✅ | ⏳ |
| **AC-FEED-P0c** | 重排后封面 asset 变化 | toast「排版已更新 · 封面已更换」 | ✅ | ⏳ |

---

## 3. 工程静态门禁

```text
python -m pytest tests/unit/web/test_refine_feedback_loop_v1.py -q
```

关键断言：首尾 tip 合同、★ 诚实文案与 3a、拦截文案去精选、demote/重排 markers、Dock cue、放映空池、toast→H2、封面 diff toast。

---

## 4. 文档回写

| 文档 | 项 | 状态 |
|------|----|------|
| 精修 V1 §4.2 | ★ ≠ 立刻重排；更新版面 vs 按精选重排 | ✅ |
| 精修 V1 §4.3.1 | 拦截正文改为拼图/版式 | ✅ |
| 附录 A §6 | Studio 预览升格注记 | ✅ |
| IMPLEMENTATION | P0 收口勾选 | ✅ |
