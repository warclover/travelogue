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
    mint: "森系薄荷",
    navy: "夜航蓝调",
    olive: "深林橄榄",
    fjord: "北欧雾蓝",
    sage: "雾炭鼠尾草",
    taupe: "板岩暖灰",
    grove: "午夜桉树",
  };
  if (!select) return;

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
