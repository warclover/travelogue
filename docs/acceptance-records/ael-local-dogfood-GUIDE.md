# AEL · 本机狗粮 / 手测指南

| 属性 | 内容 |
|------|------|
| **对应** | [PRD-ALBUM-EDITORIAL-LAB-V1.md](../PRD-ALBUM-EDITORIAL-LAB-V1.md) · [ACCEPTANCE-ALBUM-EDITORIAL-LAB-V1.md](../ACCEPTANCE-ALBUM-EDITORIAL-LAB-V1.md) |
| **DOC-STATUS** | **active** |
| **日期** | 2026-08-13 |
| **语料（OQ-AEL-01）** | `demo-d6697c8dca`（混排）· `demo-2025`（东澳岛）· `demo-49cbe46479`（长途 / 近全单反） |

> 仓库默认 **关旗**。本机狗粮用 [config-ael-dogfood.example.yaml](../config-ael-dogfood.example.yaml) 覆盖，**不要**把 `enabled: true` 提交进 `config.yaml.example`。

---

## 0. 各波次开什么键

| 波次 | 配置 | 看什么 |
|------|------|--------|
| **L0** | 父开、子全关 **或** 父关 | 画册与关旗相同；小红书序列不变 |
| **L1** | `enabled` + `crop.enabled` | 少砍头/切天；允许槽内浅色边；卡数与模板序列不漂 |
| **L2** | 上 + `roles.enabled` + `crop.tighten` | 大图进大槽、脸不进扁槽、菜不占主槽；全身照留脚推近、不行再胸像 |
| **L3** | 上 + `probes.enabled` + 非空 **混出** allowlist（四 id，见下） | 每跨页最多 1 张探针；失败则仍是成熟卡 |
| **L3 本机狗粮（第 5 套）** | 上 + allowlist **另加** `probe-triptych`（只写本机 `config.yaml`，勿提交） | 三连瘦条也会出场；评测-only 合同不变 |
| **L3 评测** | 上 + allowlist **仅** `probe-triptych`（夹具 job，勿提交进仓库默认） | 三连瘦条裁切；不过门不升混出 |

封面/封底（ABE）**不**在本主题里评裁切。

---

## 1. 导出

只导出 **画册** `album_spread`。对照时再导出一次小红书，确认模板序列未变（L0/L1 回归）。

对比方法：把两次导出的诊断里 `templateIds[]`（或文件名旁记录）对齐。**不要**用 PNG 哈希。

---

## 2. L1 出门怎么看（AC-AEL-18）

1. 关 `crop` 出一册，开 `crop` 再出一册。打乱左右再评。  
2. **红线**：人像砍头切脚不可接受；合影缺人不可接受。  
3. **得体**：风景天际、3:2 进竖槽是否还在硬砍。合法浅边算通过，不是失败。  
4. **序列**：正文卡张数、模板 id 序应与 off 相同。  
5. 评委：1 产品 + 1 非作者。

用户若问「为什么有浅边」：答「为了不切到人或天」，不说失败、不说 AEL。

---

## 3. 明确不评

- 像不像那 40 页大标题册  
- 胶带 / 微倾  
- 预览 16:9 或微信长图是否一起变  
- 小红书是否「更好看」（只要求不变坏）
- p33 整页是否复刻（角色在 L2 看反例即可）

---

## 4. 探针 id（合码后）

混出 allowlist（L3 出门）：

```yaml
allowlist:
  - probe-square      # p22 2×2 真 1:1
  - probe-tall        # p21 两列瘦槽
  - probe-wide        # p08 16:9 条带
  - probe-hero-mix    # p12 大方 + 两竖
```

评测夹具（单独 job，不要提交进仓库默认 config）：

```yaml
allowlist:
  - probe-triptych    # p18 三连瘦条
```

