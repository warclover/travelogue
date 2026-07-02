/**
 * 首页 v2 · 高级导入选项绑定（控件迁入设置 Popover · v2.1）。
 */
import { $, V2 } from "./store.js";
import { closeSettings, syncSettingsLock } from "./settings-panel.js";

export function syncAdvancedOptionsLock() {
  syncSettingsLock();
}

export function initAdvancedOptionsPanel() {
  // 绑定由 settings-panel.js 在 initSettingsPanel 中完成。
}
