/**
 * Travelogue · breath (PRD-EXPERIENCE appendix B · E2/E6/E8)
 * soft: IO reveal · flow: + Lenis · cinematic/gallery: + TravelogueScrub
 */
(function (global) {
  "use strict";

  var SCREEN_SEL = '.layout-screen[data-block="layout-screen"]';
  var EXTRA_SEL =
    '.cover-hero[data-block="cover-hero"], .hook-line[data-block="hook-line"], .chapter-header[data-block="chapter-header"], .chapter-separator[data-block="chapter-separator"], .breath-pause-screen[data-block="breath-pause-screen"], .foreword-spread[data-block="foreword-spread"], .trip-index[data-block="trip-index"], .featured-grid[data-block="featured-grid"], .screen-spread[data-block="screen-spread"]';
  var observer = null;
  var paused = false;
  var lenisStarted = false;
  var scrubStarted = false;
  var coverMotionRaf = null;
  var coverMotionState = null;

  var FLOW_OPTS = {
    lerp: 0.065,
    settleLerp: 0.18,
    wheelMultiplier: 0.82,
    wheelIdleMs: 130,
    tailMs: 420,
  };

  function flowOptsForLevel() {
    if (breathLevel() === "cinematic" || breathLevel() === "gallery") {
      return FLOW_OPTS;
    }
    return { lerp: 0.1, wheelMultiplier: 0.85 };
  }

  function reading() {
    return global.__TRAVELOGUE_READING__ || {};
  }

  function breathLevel() {
    return (reading().scroll || {}).breath || "off";
  }

  function prefersReducedMotion() {
    return (
      global.matchMedia &&
      global.matchMedia("(prefers-reduced-motion: reduce)").matches
    );
  }

  function revealObserverOpts() {
    var level = breathLevel();
    if (level === "cinematic" || level === "gallery") {
      return { threshold: 0.08, rootMargin: "0px 0px -4% 0px" };
    }
    return { threshold: 0.12, rootMargin: "0px 0px -8% 0px" };
  }

  function collectTargets() {
    return Array.prototype.filter.call(
      document.querySelectorAll(SCREEN_SEL + "," + EXTRA_SEL),
      function (el) {
        if (
          el.matches('.cover-hero[data-block="cover-hero"]') &&
          el.closest('.cover-opening[data-block="cover-opening"]')
        ) {
          return false;
        }
        if (
          el.matches('.hook-line[data-block="hook-line"]') &&
          el.closest('.cover-opening[data-block="cover-opening"]')
        ) {
          return false;
        }
        return true;
      }
    );
  }

  function coverOpeningRoot() {
    return document.querySelector('.cover-opening[data-block="cover-opening"]');
  }

  function coverOpeningImg(root) {
    if (!root) return null;
    return (
      root.querySelector(".cover-hero__img--main") ||
      root.querySelector(".cover-hero__media img") ||
      root.querySelector("img")
    );
  }

  function coverMotionIntensity() {
    var level = breathLevel();
    if (level === "soft") return { translate: 10, scale: 0.04 };
    if (level === "flow") return { translate: 14, scale: 0.06 };
    return { translate: 20, scale: 0.08 };
  }

  function coverScrollProgress(root) {
    var rect = root.getBoundingClientRect();
    var vh = global.innerHeight || 1;
    var span = Math.max(rect.height, vh);
    if (span <= 0) return 0;
    return Math.max(0, Math.min(1, -rect.top / span));
  }

  function clearCoverMotionStyles() {
    if (!coverMotionState) return;
    var img = coverMotionState.img;
    var panel = coverMotionState.panel;
    if (img) {
      img.style.transform = "";
      img.style.willChange = "";
    }
    if (panel) {
      panel.style.opacity = "";
      panel.style.transform = "";
    }
    document.documentElement.classList.remove("cover-motion-active");
  }

  function applyCoverMotionStyles(p) {
    if (!coverMotionState) return;
    var img = coverMotionState.img;
    var panel = coverMotionState.panel;
    var motion = coverMotionState.motion;
    if (!img) return;
    if (p <= 0.001) {
      clearCoverMotionStyles();
      return;
    }
    document.documentElement.classList.add("cover-motion-active");
    img.style.willChange = "transform";
    img.style.transform =
      "translate3d(0," + p * motion.translate + "%,0) scale(" + (1 + p * motion.scale) + ")";
    if (panel) {
      panel.style.opacity = String(Math.max(0, 1 - p * 0.35));
      panel.style.transform = "translate3d(0," + p * 14 + "px,0)";
    }
  }

  function coverMotionTick() {
    if (paused || !coverMotionState) return;
    applyCoverMotionStyles(coverScrollProgress(coverMotionState.root));
  }

  function stopCoverMotionLoop() {
    if (coverMotionRaf) {
      cancelAnimationFrame(coverMotionRaf);
      coverMotionRaf = null;
    }
  }

  function coverMotionLoop() {
    coverMotionTick();
    if (coverMotionState) {
      coverMotionRaf = global.requestAnimationFrame(coverMotionLoop);
    }
  }

  function destroyCoverMotion() {
    stopCoverMotionLoop();
    clearCoverMotionStyles();
    coverMotionState = null;
  }

  function initCoverMotion() {
    if (prefersReducedMotion() || breathLevel() === "off") return;
    if (scrubStarted && (breathLevel() === "cinematic" || breathLevel() === "gallery")) {
      return;
    }
    var root = coverOpeningRoot();
    var img = coverOpeningImg(root);
    if (!root || !img) return;

    coverMotionState = {
      root: root,
      img: img,
      panel: root.querySelector(".cover-opening__panel"),
      motion: coverMotionIntensity(),
    };
    coverMotionLoop();
  }

  function initCoverOpeningReveal() {
    var root = coverOpeningRoot();
    if (!root || prefersReducedMotion() || breathLevel() === "off") return;

    var hero = root.querySelector('.cover-hero[data-block="cover-hero"]');
    var panel = root.querySelector(".cover-opening__panel");
    var parts = [hero, panel].filter(Boolean);

    parts.forEach(function (el) {
      el.classList.add("breath-reveal", "cover-breath-reveal");
    });

    global.requestAnimationFrame(function () {
      global.requestAnimationFrame(function () {
        parts.forEach(function (el) {
          el.classList.add("is-visible");
        });
      });
    });
  }

  function markVisible(el) {
    el.classList.add("is-visible");
  }

  function pauseLenis() {
    if (global.TravelogueLenis && typeof global.TravelogueLenis.pause === "function") {
      global.TravelogueLenis.pause();
    }
  }

  function resumeLenis() {
    if (global.TravelogueLenis && typeof global.TravelogueLenis.resume === "function") {
      global.TravelogueLenis.resume();
    }
  }

  function destroyLenis() {
    if (global.TravelogueLenis && typeof global.TravelogueLenis.destroy === "function") {
      global.TravelogueLenis.destroy();
    }
    lenisStarted = false;
  }

  function pauseScrub() {
    if (global.TravelogueScrub && typeof global.TravelogueScrub.pause === "function") {
      global.TravelogueScrub.pause();
    }
  }

  function resumeScrub() {
    if (global.TravelogueScrub && typeof global.TravelogueScrub.resume === "function") {
      global.TravelogueScrub.resume();
    }
  }

  function destroyScrub() {
    if (global.TravelogueScrub && typeof global.TravelogueScrub.destroy === "function") {
      global.TravelogueScrub.destroy();
    }
    scrubStarted = false;
  }

  function usesFlowScroll() {
    var level = breathLevel();
    return level === "flow" || level === "cinematic" || level === "gallery";
  }

  function initFlowScroll() {
    if (lenisStarted || !usesFlowScroll()) return;
    if (prefersReducedMotion()) return;
    if (!global.TravelogueLenis || typeof global.TravelogueLenis.init !== "function") return;
    global.TravelogueLenis.init(flowOptsForLevel());
    lenisStarted = true;
    if (paused) pauseLenis();
  }

  function initHighlight() {
    if (
      global.TravelogueHighlight &&
      typeof global.TravelogueHighlight.init === "function"
    ) {
      global.TravelogueHighlight.init();
    }
  }

  function destroyHighlight() {
    if (
      global.TravelogueHighlight &&
      typeof global.TravelogueHighlight.destroy === "function"
    ) {
      global.TravelogueHighlight.destroy();
    }
  }

  function initScrubMotion() {
    var level = breathLevel();
    if (scrubStarted || (level !== "cinematic" && level !== "gallery")) return;
    if (prefersReducedMotion()) return;
    if (!global.TravelogueScrub || typeof global.TravelogueScrub.init !== "function") return;
    global.TravelogueScrub.init(level);
    scrubStarted = true;
    if (paused) pauseScrub();
  }

  function destroy() {
    if (observer) {
      observer.disconnect();
      observer = null;
    }
    destroyLenis();
    destroyScrub();
    destroyCoverMotion();
    destroyHighlight();
    collectTargets().forEach(function (el) {
      el.classList.remove("breath-reveal", "is-visible", "breath-reveal--featured");
      el.style.opacity = "";
      el.style.transform = "";
    });
    var coverRoot = coverOpeningRoot();
    if (coverRoot) {
      coverRoot.querySelectorAll(".cover-breath-reveal").forEach(function (el) {
        el.classList.remove("breath-reveal", "is-visible", "cover-breath-reveal");
        el.style.opacity = "";
        el.style.transform = "";
      });
      var panel = coverRoot.querySelector(".cover-opening__panel");
      if (panel) {
        panel.style.opacity = "";
        panel.style.transform = "";
      }
    }
    var coverImg = coverOpeningImg(coverRoot);
    if (coverImg) {
      coverImg.style.transform = "";
      coverImg.style.willChange = "";
    }
    document.documentElement.classList.remove("cover-motion-active");
    paused = false;
  }

  function pause() {
    paused = true;
    pauseLenis();
    pauseScrub();
  }

  function resume() {
    paused = false;
    resumeLenis();
    resumeScrub();
  }

  function initReveal() {
    var targets = collectTargets();
    if (!targets.length) return;

    if (prefersReducedMotion()) {
      targets.forEach(function (el) {
        el.classList.add("breath-reveal", "is-visible");
      });
      return;
    }

    targets.forEach(function (el) {
      el.classList.add("breath-reveal");
      if (el.getAttribute("data-featured") === "true") {
        el.classList.add("breath-reveal--featured");
      }
    });

    observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting && !paused) {
            markVisible(entry.target);
            observer.unobserve(entry.target);
          }
        });
      },
      revealObserverOpts()
    );

    targets.forEach(function (el) {
      var rect = el.getBoundingClientRect();
      if (rect.top < global.innerHeight * 0.92 && rect.bottom > 0) {
        markVisible(el);
        return;
      }
      observer.observe(el);
    });
  }

  function init() {
    if (breathLevel() === "off") return;
    if (document.documentElement.getAttribute("data-breath") === "off") return;
    initCoverOpeningReveal();
    initReveal();
    initFlowScroll();
    initScrubMotion();
    initCoverMotion();
    initHighlight();
  }

  global.TravelogueBreath = {
    init: init,
    destroy: destroy,
    pause: pause,
    resume: resume,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})(window);
