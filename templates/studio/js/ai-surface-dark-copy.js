/**
 * nas-allow: dark-only AI surface copy strings (NAS D-NAS-21)
 * 仅 aiSurfaceEnabled===true 路径引用；默认面禁词审计跳过本文件。
 */
"use strict";

/** BAI W3 · AC-BAI-14：dark 帮助 H7。默认帮助列表不得出现此条（NAS AC-NAS-03）。 */
export var DARK_HELP_H7 = {
  id: "H7",
  title: "模型API 配置",
  body: [
    "一把通义百炼 Key，用于文案和封面字体。无需选择模型。",
    "打开通义百炼控制台创建 API Key，粘贴后点「保存并测试」。成功后显示「已连接通义百炼」。",
    "未连接或封面生图暂时不可用时，改用本机字库，不影响文案和导出。",
    "密钥只保存在本机。不配置也可以导入、排版和导出。",
  ],
};

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
