/**
 * 首页 v2 · 主题皮肤切换。
 */
import {
  $,
  V2_THEME_LABELS,
  applyTheme,
  persistTheme,
  readThemePreference,
} from "./store.js";

export function initThemeSettings() {
  var select = $("v2-theme-select");
  var initialTheme = applyTheme(readThemePreference());
  if (!select) return;

  persistTheme(initialTheme);
  select.value = initialTheme;
  select.addEventListener("change", function () {
    var next = applyTheme(select.value);
    persistTheme(next);
    select.value = next;
    if (typeof studioToast === "function") {
      studioToast("已切换到" + (V2_THEME_LABELS[next] || V2_THEME_LABELS.sky), {
        duration: 1600,
      });
    }
  });
}
