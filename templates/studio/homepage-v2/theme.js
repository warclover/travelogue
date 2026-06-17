/**
 * 首页 v2 · 主题皮肤切换。
 */
import {
  $,
  applyTheme,
  persistTheme,
  readThemePreference,
} from "./store.js";

export function initThemeSettings() {
  var select = $("v2-theme-select");
  var initialTheme = applyTheme(readThemePreference());
  var THEME_LABEL = {
    sky: "清新浅蓝",
    classic: "经典深色",
    dawn: "暖阳珊瑚",
  };
  if (!select) return;

  persistTheme(initialTheme);
  select.value = initialTheme;
  select.addEventListener("change", function () {
    var next = applyTheme(select.value);
    persistTheme(next);
    if (typeof studioToast === "function") {
      studioToast("已切换到" + (THEME_LABEL[next] || "清新浅蓝"), {
        duration: 1600,
      });
    }
  });
}
