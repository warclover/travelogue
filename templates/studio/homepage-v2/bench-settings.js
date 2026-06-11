/**
 * 首页 v2 · Bench 设置入口（配色 + 高级选项 · M-P1b）。
 */
import { trackStudioEvent } from "../js/analytics.js";
import { $ } from "./store.js";
import { initThemeSettings } from "./theme.js";
import { initAdvancedOptionsPanel } from "./advanced-options.js";

var PRIMARY_THEMES = ["sky", "classic", "dawn", "mint", "navy"];
var MORE_THEMES = ["olive", "fjord", "sage", "taupe", "grove"];

function syncThemeOptionVisibility(select, popover) {
  if (!select) return;
  var showMore = popover && popover.getAttribute("data-theme-more") === "1";
  var current = select.value;
  if (MORE_THEMES.indexOf(current) >= 0) showMore = true;
  Array.prototype.forEach.call(select.options, function (opt) {
    if (PRIMARY_THEMES.indexOf(opt.value) >= 0) {
      opt.hidden = false;
      return;
    }
    if (MORE_THEMES.indexOf(opt.value) >= 0) {
      opt.hidden = !showMore;
    }
  });
}

export function initBenchSettings() {
  var btn = $("v2-bench-settings");
  var popover = $("v2-settings-popover");
  if (!btn || !popover) return;

  initThemeSettings();
  initAdvancedOptionsPanel();

  var themeSelect = $("v2-theme-select");
  var moreToggle = $("v2-theme-more-toggle");
  if (themeSelect) {
    syncThemeOptionVisibility(themeSelect, popover);
    themeSelect.addEventListener("change", function () {
      syncThemeOptionVisibility(themeSelect, popover);
    });
  }
  if (moreToggle) {
    moreToggle.addEventListener("click", function () {
      var open = popover.getAttribute("data-theme-more") === "1";
      popover.setAttribute("data-theme-more", open ? "0" : "1");
      moreToggle.setAttribute("aria-expanded", open ? "false" : "true");
      if (themeSelect) syncThemeOptionVisibility(themeSelect, popover);
    });
  }

  function close() {
    popover.hidden = true;
    btn.setAttribute("aria-expanded", "false");
  }

  function open() {
    popover.hidden = false;
    btn.setAttribute("aria-expanded", "true");
    trackStudioEvent("bench_settings_open", {});
    if (themeSelect) syncThemeOptionVisibility(themeSelect, popover);
  }

  btn.addEventListener("click", function (e) {
    e.stopPropagation();
    if (popover.hidden) open();
    else close();
  });

  document.addEventListener("click", function (e) {
    if (popover.hidden) return;
    if (popover.contains(e.target) || btn.contains(e.target)) return;
    close();
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !popover.hidden) close();
  });
}
