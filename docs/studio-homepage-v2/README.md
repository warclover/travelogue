# Studio 首页 v2 · 开发前契约包

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-STUDIO-HOMEPAGE-v2.md](../PRD-STUDIO-HOMEPAGE-v2.md) **v2.0.3** |
| **线框** | [studio-homepage-output-first-v1.6.html](../wireframes/studio-homepage-output-first-v1.6.html)（Web/iPad/书架；Mobile Tab = 小程序参考） |
| **状态** | **开工前冻结** — M20-a 起工程以本目录为 API/素材/开关权威 |

## 文档索引

| 文档 | 用途 | M20 阻塞 |
|------|------|----------|
| [DATA-CONTRACT.md](./DATA-CONTRACT.md) | `manifest.json` schema + 首页只读 API 字段 | **M20-a/b** |
| [FEATURE-FLAG.md](./FEATURE-FLAG.md) | `studio.homepage.v2_bento` 门控与 v3 共存 | **M20-a** |
| [config-holdback.example.yaml](./config-holdback.example.yaml) | holdback `percent` yaml 片段（dogfood 10%） | **M20-i/j** |
| [TELEMETRY.md](./TELEMETRY.md) | 埋点管道 + holdback 看板前置 | **M20-i** |
| [RUNBOOK-HOLDBACK.md](./RUNBOOK-HOLDBACK.md) | §17.2 回滚演练 + nightly 命令 | **M20-i/j** |
| [lcp-baseline.json](./lcp-baseline.json) | LCP P95 参考基线（nightly ≥10 runs） | **M20-i** |
| [DEMO-ASSETS-BRIEF.md](./DEMO-ASSETS-BRIEF.md) | 京都·雨后统一切图派单 | **M20-a** |
| [DEV-HARNESS.md](./DEV-HARNESS.md) | dev-only 状态切换器 + fixtures | M20-g/h |
| [AC-VERIFICATION.md](./AC-VERIFICATION.md) | §16 验收 + 验证方式 | M20-h |
| [PRE-DEV.md](./PRE-DEV.md) | 开工清单 · spike · 浏览器矩阵 | 开工前 |
| [OPEN-QUESTIONS.md](./OPEN-QUESTIONS.md) | 未闭环项（owner + due） | 持续 |
| [SIGNOFF-M20J.md](./SIGNOFF-M20J.md) | P2 观察窗 + PM/工程签字 + 切主站 | **M20-j** |
| [RUNBOOK-DOGFOOD.md](./RUNBOOK-DOGFOOD.md) | dogfood holdback 部署与验证 | **M20-i/j** |
| [VISUAL-SIGNOFF.md](./VISUAL-SIGNOFF.md) | AC-03/08/12/17/18 截图签字 | **M20-j** |
| [USABILITY-AC01.md](./USABILITY-AC01.md) | AC-01 五被试协议 | **M20-j** |
| [DEVICE-MATRIX-IPAD.md](./DEVICE-MATRIX-IPAD.md) | iPad Safari 实机清单 | **M20-j** |
| [EDITOR-LINKS-M20J.md](./EDITOR-LINKS-M20J.md) | 切主站后 editor 链评估 | **M20-j** |
| [RELEASE-CHECKLIST.md](./RELEASE-CHECKLIST.md) | PR / 合入自检 | 合入前 |

## 机器可读契约

- Schema: [`templates/studio/assets/demo-showcase/manifest.schema.json`](../../templates/studio/assets/demo-showcase/manifest.schema.json)
- 示例: [`templates/studio/assets/demo-showcase/manifest.example.json`](../../templates/studio/assets/demo-showcase/manifest.example.json)

## 里程碑硬依赖（摘要）

```
M20-a  ← manifest schema ✓ · demo 素材交期 · flag 默认值
M20-b  ← manifest pages[] · spread/clamp 映射
M20-h  ← dev harness · 事件 ALLOWED 扩展
M20-i  ← TELEMETRY 真实聚合 + holdback 看板（非 localStorage-only）
M20-j  ← flag 默认 v2 + 回滚演练通过
```
