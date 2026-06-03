# Studio 首页 v2 · 开发前契约包

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-STUDIO-HOMEPAGE-v2.md](../PRD-STUDIO-HOMEPAGE-v2.md) **v2.0.3** · 退役 v3：[PRD-M21-studio-homepage-v3-retirement.md](../PRD-M21-studio-homepage-v3-retirement.md) |
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
| [PRD-M21-studio-homepage-v3-retirement.md](../PRD-M21-studio-homepage-v3-retirement.md) | **v3 退役 · v2 唯一入口 · 浏览器上传** | **M21** |
| [M21-CUTOVER-CHECKLIST.md](./M21-CUTOVER-CHECKLIST.md) | M21 分阶段切换检查单（开发/QA/发布） | **M21** |
| [M21-ROLLBACK-CARD.md](./M21-ROLLBACK-CARD.md) | M21 值班回滚速查卡（5 分钟恢复） | **M21** |
| [M21-TEST-MATRIX.md](./M21-TEST-MATRIX.md) | M21 自动化 + 手工门禁矩阵 | **M21** |
| [M21-V3-FREEZE.md](./M21-V3-FREEZE.md) | M21-e1 v3 冻结规则与 `/classic` smoke 护栏 | **M21-e1** |
| [M21-E2-DEPENDENCY-AUDIT.md](./M21-E2-DEPENDENCY-AUDIT.md) | M21-e2 删除前依赖审计与 Go/No-Go 门禁 | **M21-e2** |
| [M21-E2-EXECUTION-CARD.md](./M21-E2-EXECUTION-CARD.md) | M21-e2 执行步骤、验证与回退卡 | **M21-e2** |
| [M21-E2-SNAPSHOT-SWITCH-PLAN.md](./M21-E2-SNAPSHOT-SWITCH-PLAN.md) | `/classic` 冻结快照切换与阻塞消解映射 | **M21-e2** |
| [M21-E2-CHANGESET-DRAFT.md](./M21-E2-CHANGESET-DRAFT.md) | M21-e2 分批删除草稿（不执行） | **M21-e2** |
| [M21-E2-COMMIT-DRAFT.md](./M21-E2-COMMIT-DRAFT.md) | M21-e2 提交级草案（commit 顺序与验证） | **M21-e2** |
| `scripts/studio_m21e2_delete_plan.py` | M21-e2 删除命令生成器（默认 dry-run） | **M21-e2** |
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
