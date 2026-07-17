# 写作引擎 API 配置加固 V1 · 跨职能评审会结论

| 属性 | 内容 |
|------|------|
| **会议日期** | 2026-07-17 |
| **材料** | [PRD-WRITING-ENGINE-API-HARDENING-V1.md](../PRD-WRITING-ENGINE-API-HARDENING-V1.md) **v1.0.0 → v1.1.0** |
| **形式** | 跨职能书面评审（产品 · UI/UX · 用户体验 · 前端 · 后端 · 架构 · 典型用户代表×2） |
| **结论状态** | **有条件通过（Conditional Go）** · Must-Fix 已回写 PRD v1.1 · **可开 W1** |
| **记录人** | 产品 / UX / 工程联合纪要 |
| **前置** | Desktop LLM Setup V1 Conditional Go 且 W1a 已落地；2026-07-17 通义串 DeepSeek 配置实测；coerce 热修已合入待验收锁死 |

---

## 1. 与会角色

| 角色 | 关注点 |
|------|--------|
| **产品（拍板）** | 是否扩分槽；保存并测试是否改铁律；与 L0 边界 |
| **UI / UX** | Modal 按钮预算；地域控件；线框挡门 |
| **用户体验** | 通义用户能否自助配通；切换是否吓到人 |
| **前端开发** | 状态机 · save→ping 串行 · zone meta 同词 |
| **后端开发** | coerce 合同 · region · 错误码扩展 · env 残留 |
| **架构师** | 单槽 vs 分槽；secrets schema 兼容；不扩 PATCH llm 白名单 |
| **典型用户 · 分享者** | 别逼我懂 API；失败别吓人 |
| **典型用户 · 进阶创作者** | 通义国内/国际、模型可选、配完点哪里生效 |

---

## 2. 总评（一句话）

> **问题真实、热修方向正确；阻塞不在「要不要加固」，而在把「保存≠就绪」、通义地域、可行动错误写成可验收合同。默认包可开 W1；分槽与 OS 凭据库明确不进本波。**

**表决**：八席一致 **Conditional Go**。

| 角色 | 表决 | 一句话 |
|------|------|--------|
| 产品 | Conditional Go | 保存并测试是对的；分槽留 V1.1 |
| UI / UX | Conditional Go | 要独立线框 F2；三按钮改一主一危 |
| 用户体验 | Conditional Go | 通义地域必须可见；失败要说人话 |
| 前端 | Conditional Go | zone/Modal 同词；切换确认别丢表单 |
| 后端 | Conditional Go | coerce 单测锁死；错误码进 ERROR-CODES |
| 架构 | Conditional Go | region 进 secrets 可接受；分槽另开 schema |
| 用户 · 分享者 | Conditional Go | 「配不上别骂我笨」 |
| 用户 · 创作者 | Conditional Go | 「告诉我中国站还是国际站」 |

**对齐评分（主观）**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题定义 | 9 | 实测根因清楚 |
| 范围克制 | 8 | 非目标清楚；分槽外置 |
| 体验合同 | 7 | 状态机已写；线框补后到 8 |
| API/数据可开工性 | 8 | coerce + region 足够开工 |
| AC 可测性 | 8 | AC-WEA + 回归命令齐 |
| 与相邻 PRD 仲裁 | 8 | 不碰 L0 / 手风琴 IA |

---

## 3. §12.4 评审清单拍板

| 项 | 决议 |
|----|------|
| 默认包 D-WEA-01～04、07～10 | **采纳** |
| D-WEA-05 确认覆盖（非分槽） | **采纳** · 分槽 → V1.1 候选 |
| D-WEA-06 模型下拉 | **采纳 · 排 W2** |
| O-WEA-01 失败仍落盘 Key | **采纳**（标连接失败，不标就绪） |
| 独立线框 HTML | **要** · `writing-engine-api-hardening-v1-wireframe.html` |
| 同步 ACCEPTANCE-DESKTOP-LLM-SETUP | **指针专节** + 独立 ACCEPTANCE-WEA |

### 3.1 冻结确认（D-WEA-*）

| ID | 状态 |
|----|------|
| D-WEA-01 服务商隔离 | **冻结** · W1 验收锁死（含热修） |
| D-WEA-02 保存并测试 | **冻结** · W1 |
| D-WEA-03 失败可保留 Key | **冻结** |
| D-WEA-04 通义中国站/国际站 | **冻结** · W1 |
| D-WEA-05 切换确认覆盖 | **冻结** · W2（可与模型同波，但不阻塞 W1 冒烟） |
| D-WEA-06 模型下拉 | **冻结** · W2 |
| D-WEA-07 错误矩阵 | **冻结** · W1 核心码；其余 W2 |
| D-WEA-08 脚注隐私费用 | **冻结** · W1 |
| D-WEA-09 Provider 仍两家 | **冻结** |
| D-WEA-10 导入仍 stub | **冻结** |

---

## 4. Must-Fix（回写 v1.1 / 挡 W1 开工）

| ID | 项 | 责任 | 回写 |
|----|-----|------|------|
| **MF-WEA-01** | 「已就绪」定义写进 ACCEPTANCE：仅 `last_ping_ok=true` | 产品+后端 | ACCEPTANCE + PRD §4.3 |
| **MF-WEA-02** | 通义两站官方 URL 冻结表进线框与 IMPLEMENTATION | UX+后端 | 线框 F2 · IMPL |
| **MF-WEA-03** | ERROR-CODES 预留 `E_LLM_ENDPOINT` / `E_LLM_QUOTA` / `E_LLM_RATE` / `E_LLM_MODEL` / `E_LLM_BASE_URL` | 后端 | ERROR-CODES.md |
| **MF-WEA-04** | W1 实机冒烟：DeepSeek + 通义中国站各 1 Key | 产品狗粮 | ACCEPTANCE 手工表 |
| **MF-WEA-05** | 清除后进程内他商 env 不得让 resolve「假绿」 | 后端 | IMPL BE 任务 |

非阻塞（W2）：切换确认文案润色、模型列表探活、`deepseek-reasoner` 是否上架。

---

## 5. 分角色意见摘要

### 产品
- 赞成：不扩第三家；保存并测试消除假配置。  
- 拍板：V1 单槽+确认；分槽不进本波排期。  
- 指标：通义配置成功率（狗粮）相对热修前显著上升即可，不设虚高转化 KPI。

### UI / UX
- Modal 主按钮仅「保存并测试」；清除为危险次要；「仅测试」降为文案链（可 W1.1）。  
- 地域用 radio，勿藏进高级。  
- 独立线框挡 UI 软门。

### 用户体验 / 用户代表
- 分享者：失败别出现英文堆栈；一句人话+下一步。  
- 创作者：中国站/国际站比「自定义 URL」好懂；模型下拉 W2 可接受。

### 前端
- `payloadFromForm` 已清 foreign base；W1 接 region + 主按钮改文案。  
- AI zone meta 与徽章同词表（四态）。

### 后端 / 架构
- coerce 单测已有，纳入发布门。  
- `region` 字段缺省=`cn`。  
- 不新增 PATCH `llm.*` 白名单；继续走 llm/settings API。

---

## 6. 里程碑确认

| 波次 | 范围 | 门禁 |
|------|------|------|
| **W0** | 本文档包 + 线框 + ERROR-CODES 预留 | ✅ 本评审后关闭 |
| **W1** | 隔离验收 · 保存并测试 · 地域 · 核心错误文案 · 脚注 · https | 双 Key 冒烟 |
| **W2** | 模型下拉 · 切换确认 · H7 · meta 同词 | 狗粮 N≥3 |
| **W3** | 分槽调研 / Keychain 纪要 | 不阻塞发版 |

---

## 7. 文档动作（本评审会交付）

| 文档 | 动作 |
|------|------|
| PRD | 升 **v1.1.0** Conditional Go；勾选 §12.4 |
| IMPLEMENTATION | 新建 W0–W2 任务表 |
| ACCEPTANCE | 新建 AC-WEA 表 |
| 线框 | 新建 WEA F1–F4 |
| ERROR-CODES | 预留扩展码 |
| README | 索引补齐 |
| ACCEPTANCE-DESKTOP-LLM-SETUP | 增「WEA 指针」专节 |

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-17 | 初稿 · Conditional Go · 默认包拍板 |
