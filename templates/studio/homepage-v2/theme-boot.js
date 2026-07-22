/**
 * 首屏主题闪屏抑制：在 CSS 解析前恢复 localStorage 中的 data-v2-theme。
 * 须与 store.js 中 V2_THEME_IDS / V2_THEME_DEFAULT 保持同步。
 */
(function () {
  var KEY = "travelogue.studio.v2.theme";
  var DEFAULT_THEME = "mist";
  var ALLOWED = { classic: 1, dawn: 1, mist: 1, folio: 1, atelier: 1 };
  try {
    var raw = localStorage.getItem(KEY);
    if (!raw) {
      document.documentElement.setAttribute("data-v2-theme", DEFAULT_THEME);
      return;
    }
    if (raw === "sky") {
      document.documentElement.setAttribute("data-v2-theme", "sky");
      return;
    }
    if (!ALLOWED[raw]) {
      document.documentElement.setAttribute("data-v2-theme", DEFAULT_THEME);
      return;
    }
    document.documentElement.setAttribute("data-v2-theme", raw);
  } catch (e) {
    /* ignore */
  }
})();
