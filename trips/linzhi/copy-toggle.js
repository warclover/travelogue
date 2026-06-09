/**
 * Travelogue · 浏览时切换叙事文案 / 纯照片模式
 * 依赖 HTML 内保留完整文案；通过 html[data-*] + CSS 隐藏。
 */
(function (global) {
  "use strict";

  var STORAGE_KEY = "travelogue:copyDisplay";
  var PHOTOS_ONLY_KEY = "travelogue:photosOnly";
  var MODE_FULL = "full";
  var MODE_PHOTOS = "photos";

  function readStorage(key) {
    try {
      return sessionStorage.getItem(key);
    } catch (_e) {
      return null;
    }
  }

  function writeStorage(key, value) {
    try {
      if (value == null) {
        sessionStorage.removeItem(key);
      } else {
        sessionStorage.setItem(key, value);
      }
    } catch (_e) {
      /* ignore */
    }
  }

  function serverDefaultMode() {
    var v = document.documentElement.getAttribute("data-copy-display");
    return v === MODE_PHOTOS ? MODE_PHOTOS : MODE_FULL;
  }

  function resolveInitialMode() {
    var stored = readStorage(STORAGE_KEY);
    if (stored === MODE_FULL || stored === MODE_PHOTOS) return stored;
    return serverDefaultMode();
  }

  function applyCopyMode(mode) {
    var root = document.documentElement;
    var btn = document.getElementById("copy-display-toggle");
    if (mode === MODE_PHOTOS) {
      root.setAttribute("data-copy-display", MODE_PHOTOS);
    } else {
      root.removeAttribute("data-copy-display");
    }
    if (!btn) return;
    if (mode === MODE_PHOTOS) {
      btn.textContent = btn.getAttribute("data-copy-label-show") || "显示导语";
      btn.setAttribute("aria-pressed", "true");
    } else {
      btn.textContent = btn.getAttribute("data-copy-label-hide") || "隐藏导语";
      btn.setAttribute("aria-pressed", "false");
    }
  }

  function restoreCaptionDisplay() {
    if (global.TravelogueLongshot && global.TravelogueLongshot.applyCaptionDisplay) {
      global.TravelogueLongshot.applyCaptionDisplay(true);
      return;
    }
    document.documentElement.removeAttribute("data-caption-display");
    writeStorage("travelogue:captionDisplay", null);
  }

  function tripIdFromDom() {
    return document.documentElement.getAttribute("data-trip-id") || "";
  }

  function recordCopyTelemetry(event) {
    var tripId = tripIdFromDom();
    if (!tripId) return;
    try {
      fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/copy-telemetry", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ event: event }),
      }).catch(function () {});
    } catch (_e) {
      /* ignore */
    }
  }

  function applyPhotosOnly(on) {
    var root = document.documentElement;
    var btn = document.getElementById("photos-only-toggle");
    if (on) {
      root.setAttribute("data-photos-only", "on");
    } else {
      root.removeAttribute("data-photos-only");
    }
    if (!btn) return;
    if (on) {
      btn.textContent = btn.getAttribute("data-label-off") || "显示文案";
      btn.setAttribute("aria-pressed", "true");
    } else {
      btn.textContent = btn.getAttribute("data-label-on") || "纯照片";
      btn.setAttribute("aria-pressed", "false");
    }
  }

  function init() {
    if (document.documentElement.getAttribute("data-copy-toggle") !== "on") {
      return;
    }

    var copyBtn = document.getElementById("copy-display-toggle");
    var photosBtn = document.getElementById("photos-only-toggle");

    if (readStorage(PHOTOS_ONLY_KEY) === "on") {
      applyPhotosOnly(true);
    } else {
      applyCopyMode(resolveInitialMode());
    }
    recordCopyTelemetry("preview_open");

    if (copyBtn && !copyBtn.dataset.bound) {
      copyBtn.dataset.bound = "1";
      copyBtn.addEventListener("click", function () {
        applyPhotosOnly(false);
        writeStorage(PHOTOS_ONLY_KEY, null);
        var current =
          document.documentElement.getAttribute("data-copy-display") === MODE_PHOTOS
            ? MODE_PHOTOS
            : MODE_FULL;
        var next = current === MODE_PHOTOS ? MODE_FULL : MODE_PHOTOS;
        applyCopyMode(next);
        writeStorage(STORAGE_KEY, next);
      });
    }

    if (photosBtn && !photosBtn.dataset.bound) {
      photosBtn.dataset.bound = "1";
      photosBtn.addEventListener("click", function () {
        var on = document.documentElement.getAttribute("data-photos-only") === "on";
        var next = !on;
        applyPhotosOnly(next);
        if (next) {
          applyCopyMode(MODE_FULL);
          writeStorage(STORAGE_KEY, MODE_FULL);
          writeStorage(PHOTOS_ONLY_KEY, "on");
          if (global.TravelogueLongshot && global.TravelogueLongshot.applyCaptionDisplay) {
            global.TravelogueLongshot.applyCaptionDisplay(false);
          } else {
            document.documentElement.setAttribute("data-caption-display", "off");
            writeStorage("travelogue:captionDisplay", "off");
          }
        } else {
          writeStorage(PHOTOS_ONLY_KEY, null);
          restoreCaptionDisplay();
        }
        recordCopyTelemetry(next ? "photos_only_on" : "photos_only_off");
      });
    }
  }

  global.travelogueApplyPhotosOnly = applyPhotosOnly;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})(window);
