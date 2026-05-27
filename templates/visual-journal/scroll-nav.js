/**
 * Travelogue · Scroll 键盘 snap（← → ↑ ↓ Space PageUp/Down）
 * 仅在 scroll.keyboardNav 启用且非放映模式时生效。
 */
(function (global) {
  "use strict";

  var SCREEN_SELECTOR = '.layout-screen[data-block="layout-screen"]';

  function readingConfig() {
    return global.__TRAVELOGUE_READING__ || {};
  }

  function keyboardNavEnabled() {
    var scroll = readingConfig().scroll || {};
    return scroll.keyboardNav === true;
  }

  function collectScreens() {
    return Array.prototype.slice.call(document.querySelectorAll(SCREEN_SELECTOR));
  }

  function currentScreenIndex(screens) {
    if (!screens.length) return -1;
    var mid = global.innerHeight * 0.35;
    var best = 0;
    var bestDist = Infinity;
    for (var i = 0; i < screens.length; i++) {
      var rect = screens[i].getBoundingClientRect();
      var dist = Math.abs(rect.top - mid);
      if (dist < bestDist) {
        bestDist = dist;
        best = i;
      }
    }
    return best;
  }

  function isTypingTarget(el) {
    if (!el || !el.tagName) return false;
    var tag = el.tagName;
    return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || el.isContentEditable;
  }

  function scrollToScreen(screen) {
    if (!screen || typeof screen.scrollIntoView !== "function") return;
    var behavior =
      global.matchMedia && global.matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "auto"
        : "smooth";
    try {
      screen.scrollIntoView({ behavior: behavior, block: "start", inline: "nearest" });
    } catch (_e) {
      screen.scrollIntoView(true);
    }
    if (global.TravelogueLenis && typeof global.TravelogueLenis.scrollTo === "function") {
      global.TravelogueLenis.scrollTo(screen);
    }
  }

  function onKeyDown(e) {
    if (!keyboardNavEnabled()) return;
    if (document.body.classList.contains("screenplay-active")) return;
    if (isTypingTarget(e.target)) return;

    var nextKeys = ["ArrowRight", "ArrowDown", " ", "PageDown"];
    var prevKeys = ["ArrowLeft", "ArrowUp", "PageUp"];
    var isNext = nextKeys.indexOf(e.key) !== -1;
    var isPrev = prevKeys.indexOf(e.key) !== -1;
    if (!isNext && !isPrev) return;

    var screens = collectScreens();
    if (!screens.length) return;

    var idx = currentScreenIndex(screens);
    if (idx < 0) return;

    var target = isNext ? idx + 1 : idx - 1;
    if (target < 0 || target >= screens.length) return;

    e.preventDefault();
    scrollToScreen(screens[target]);
  }

  document.addEventListener("keydown", onKeyDown);
})(window);
