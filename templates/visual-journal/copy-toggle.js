/**
 * Travelogue · 浏览时切换叙事文案显示（export.copyDisplay 的交互版）
 * 依赖 HTML 内保留完整文案；通过 html[data-copy-display] + CSS 隐藏。
 */
(function (global) {
  "use strict";

  var STORAGE_KEY = "travelogue:copyDisplay";
  var MODE_FULL = "full";
  var MODE_PHOTOS = "photos";

  function readStorage() {
    try {
      var v = sessionStorage.getItem(STORAGE_KEY);
      if (v === MODE_FULL || v === MODE_PHOTOS) return v;
    } catch (_e) {
      /* private mode */
    }
    return null;
  }

  function writeStorage(mode) {
    try {
      sessionStorage.setItem(STORAGE_KEY, mode);
    } catch (_e) {
      /* ignore */
    }
  }

  function serverDefaultMode() {
    var v = document.documentElement.getAttribute("data-copy-display");
    return v === MODE_PHOTOS ? MODE_PHOTOS : MODE_FULL;
  }

  function resolveInitialMode() {
    var stored = readStorage();
    if (stored) return stored;
    return serverDefaultMode();
  }

  function applyMode(mode) {
    var root = document.documentElement;
    var btn = document.getElementById("copy-display-toggle");
    if (mode === MODE_PHOTOS) {
      root.setAttribute("data-copy-display", MODE_PHOTOS);
    } else {
      root.setAttribute("data-copy-display", MODE_FULL);
    }
    if (!btn) return;
    if (mode === MODE_PHOTOS) {
      btn.textContent = btn.getAttribute("data-copy-label-show") || "显示文案";
      btn.setAttribute("aria-pressed", "true");
    } else {
      btn.textContent = btn.getAttribute("data-copy-label-hide") || "隐藏文案";
      btn.setAttribute("aria-pressed", "false");
    }
  }

  function init() {
    var btn = document.getElementById("copy-display-toggle");
    if (!btn) return;
    if (document.documentElement.getAttribute("data-copy-toggle") !== "on") {
      btn.hidden = true;
      return;
    }

    applyMode(resolveInitialMode());

    btn.addEventListener("click", function () {
      var current =
        document.documentElement.getAttribute("data-copy-display") === MODE_PHOTOS
          ? MODE_PHOTOS
          : MODE_FULL;
      var next = current === MODE_PHOTOS ? MODE_FULL : MODE_PHOTOS;
      applyMode(next);
      writeStorage(next);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})(window);
