/**
 * nas-allow: dark-only AI surface copy strings (NAS D-NAS-21)
 * 仅 aiSurfaceEnabled===true 路径引用；默认面禁词审计跳过本文件。
 */
"use strict";

export var DARK_COPY = {
  sheetLlmStart: "重新生成文案",
  sheetLlmUnavailable: "当前为本机文案 · 配置写作引擎后可升级",
  sheetLlmSetup: "配置写作引擎",
  sheetLlmExpect:
    "AI 文案已就绪；重新生成不会自动覆盖你的手动修改。",
  drawerNarrate: "按新感觉重写这段",
  drawerNarrateConfirmTitle: "按新感觉重写这段",
  drawerNarrateConfirmBody:
    "将按当前词与本章感觉重新生成文案，可能覆盖未锁定的内容。继续？",
  drawerNarrateBusy: "正在按新感觉重写这段…",
  dockCopyRefreshTitle: "AI 文案已就绪，可为这本重新生成文案",
  dockCopyRefreshBtn: "重新生成文案",
  settingsManage: "管理连接…",
  settingsConfigure: "去连接",
  llmExpectReady: "AI 文案已就绪；重新生成不会自动覆盖你的手动修改。",
  llmExpectStub: "当前为本机文案 · 配置写作引擎后可升级",
  narrateBusy: "正在重新生成文案…",
  narrateConfirmTitle: "重新生成文案",
  narrateConfirmText: "重新生成文案",
  narrateFailTitle: "连接写作引擎失败",
  narrateFailBody: "仍保留本机文案。可检查 API Key、网络或服务商余额后重试。",
};
