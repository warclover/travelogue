# SSG · look 层实拍未生效排查（2026-08-03）

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-03 |
| **PRD** | [PRD-SMART-SHOT-GROUPING-V1.md](../PRD-SMART-SHOT-GROUPING-V1.md) |
| **相关** | [ssg-local-dogfood-GUIDE.md](./ssg-local-dogfood-GUIDE.md) · [ssg-default-on-decision-2026-07-23.md](./ssg-default-on-decision-2026-07-23.md) |
| **结论** | **阻塞**：`demo-2025` 上 look 全员跳过（`lookEncoded=0`）；**根因是 live 人脸门**，不是 trip.json 缺 `faceCount` 直接导致 |

## 背景

本机 `config.yaml` 常驻 `vision.enabled` + `shotGrouping` + `look.enabled`。打算补实拍盲评时发现 look 组数为 0。

## 排查过程

1. `demo-2025`（东澳岛）ch-02 确有同景点换装语料。
2. `cluster reshotgroup --look` / `--no-look` 结果相同：`lookGroups=0`。
3. 调用 `compute_look_vectors_for_assets`：`lookSkippedNoFace=81` + `lookSkippedMulti=48` = 129，`lookEncoded=0`。
4. 初判：三个常测 trip 资产顶层 / `quality.faceCount` 多为缺失。

## 根因更正（代码核对 · 同日追记）

`travelogue/vision/look_appearance.py` **并不读取** trip 里的 `faceCount`。  
look 路径对每张图 **现场** `detect_faces_in_image`，再按：

- `max_faces_before_skip`（默认 4）→ 过多则 `lookSkippedMulti`
- `min_max_face_area_ratio`（默认 0.15）+ 主脸选择 → 失败则 `lookSkippedNoFace`

因此 `demo-2025` 的真实阻塞是：**OpenCV 人脸门把全部 129 张判成「无人脸」或「人脸过多」**，CLIP torso 从未编码。

### 另账：ingest `faceCount`

`travelogue/media/ingest.py` 仅在 `subj.face_count > 0` 时写入 `quality.faceCount`。  
字段缺失会影响 cohort / cull / 封面启发式等**其他**消费者，但 **不是** look 跳过的直接原因。  
三个常测 trip 缺该字段，说明历史 ingest 可能未跑通 subject_detect，或检测结果恒为 0 未落盘——应另开「补写 face 元数据」小修，与 look 标定解耦。

## 影响范围

| 项 | 状态 |
|----|------|
| 自动化 pytest（AC-SSG-10～17） | ✅ 注入 `look_vectors`，不受 live 人脸门影响 |
| scene 层（切条硬拒等） | 不受本阻塞 |
| look 实拍盲评 / 默认 on | ❌ 在代表性语料上 `lookEncoded=0`，无法评估 |
| LVP（一句话选风格） | V1 **不映射** look（见 [PRD-LAYOUT-VIBE-PICKER-V1](../PRD-LAYOUT-VIBE-PICKER-V1.md)） |

## 后续（未决）

1. **Look 标定**：~~在 `demo-2025` 抽 20 张人像…~~ → **已做**（见下「探针结果」）。  
2. **阈值狗粮**：优先试两刀（仍禁止改仓库默认前无盲评）：  
   - 计 multi 前先丢掉 `area_ratio < ~0.01` 的 Haar 噪点框；  
   - 将 `min_max_face_area_ratio` 狗粮试到 **0.02～0.04**（全身/环境人像常见主脸远小于 0.15）。  
3. **ingest 补写**：独立 CLI/重跑 subject_detect，把 `quality.faceCount` 写回旧 trip（服务非 look 消费者）。  
4. 未完成阈值狗粮 + 实拍 lookGroups>0 前：**不**改 SSG 默认 on；不排换装盲评列车。

## 探针结果（2026-08-03 · demo-2025 随机 20 张 personish）

阈值：`min_max_face_area_ratio=0.15` · `max_faces_before_skip=4`。

| bucket | 张数 | 含义 |
|--------|------|------|
| **ok** | **0** | 无一通过 look 人脸门 |
| **multi** | 11 | `n≥4`；但 top 面积多在 0.01～0.03，大量疑似 Haar 误检小框 |
| **tiny** | 9 | 有框但最大脸面积 ≪ 0.15（例 0.037 / 0.030 / 0.016） |
| no_face / missing | 0 | — |

**结论改写**：不是「图里没人」，而是 **(a) 0.15 面积门对旅行全身/半身过严** + **(b) 误检小框把人数抬过 4 触发 multi**。下一步应是狗粮阈值/噪点过滤，不是先重跑 ingest。
