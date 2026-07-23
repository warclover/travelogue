# ACCEPTANCE · 日更质量修复包 V1（QFX）

| 属性 | 内容 |
|------|------|
| **文档版本** | **v1.0.0** |
| **对应 PRD** | [PRD-QUALITY-FIXPACK-V1.md](./PRD-QUALITY-FIXPACK-V1.md) **v0.2.1** |
| **实施** | [IMPLEMENTATION-QUALITY-FIXPACK-V1.md](./IMPLEMENTATION-QUALITY-FIXPACK-V1.md) |
| **状态** | **Closed**（PR-A/B/C 已合；C2/D 本分支结案 · 2026-07-23） |
| **聚合门禁** | `python scripts/quality_fixpack_gate.py` |

## AC 勾选

| ID | 断言 | 状态 |
|----|------|------|
| AC-01 | recipe baseline | ✅ |
| AC-02 | god-module（留痕→预处理降 LOC） | ✅ |
| AC-03 | facade 扩扫 + grandfather | ✅ |
| AC-04 | FE 只读 AI surface | ✅ |
| AC-05/23 | status 403 早拒 | ✅ |
| AC-06/16/17 | 能力卡真 DI + trap 不 skip | ✅（wave11 DI） |
| AC-07/18 | 空测量 P0 | ✅ |
| AC-08/19 | bare `--strict`→all | ✅ |
| AC-09/10/21/22 | hydration 三态 + gate schema | ✅ |
| AC-11/25 | 长图 mtime + current + 分段完整批 | ✅ |
| AC-12 | keep-all 合同向量 | ✅ |
| AC-13/26 | 预处理回填/清标/条件硬丢 | ✅ |
| AC-14 | 复制三态 | ✅ |
| AC-15 | L1 DOM == l1Keys | ✅ |
| AC-20 | token 块内接线 | ✅ |
| AC-24 | quality_fixpack_gate | ✅ |
| AC-27 | config 投影 | ✅ |

## 结案指针

- QFX 非长期 SSOT；条款归还 [NAS](./PRD-NO-AI-SURFACE-V1.md) / [Keep-All](./PRD-KEEP-ALL-PHOTOS-V1.md) / CSC。
- 门禁入口：`scripts/quality_fixpack_gate.py` · CI lint job。

## CQA 邻接回写（2026-07-23）

| 项 | 说明 |
|----|------|
| `longshot-current.json` | schema 仍以 QFX D-QFX-06 / AC-11/25 为 SSOT |
| 乱序分段 | CQA 只改触发：齐套即写 current（不依赖最后一段最后到达）· [AC-CQA-19](./ACCEPTANCE-CODE-QUALITY-AUDIT-FIXPACK-V1.md) |
