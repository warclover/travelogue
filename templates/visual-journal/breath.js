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
  var closingMotionState = null;
  var closingRevealObserver = null;

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
        if (
          el.matches('.epilogue[data-block="epilogue"]') &&
          el.closest('.cover-closing[data-block="cover-closing"]')
        ) {
          return false;
        }
        if (
          el.matches('.epilogue-screen[data-block="epilogue-screen"]') &&
          coverClosingPresentationActive()
        ) {
          return false;
        }
        return true;
      }
    );
  }

  function coverClosingRoot() {
    return document.querySelector('.cover-closing[data-block="cover-closing"]');
  }

  function coverClosingPresentationActive() {
    if (!coverClosingRoot()) return false;
    if (!global.matchMedia) return true;
    return global.matchMedia("(min-width: 48rem)").matches;
  }

  function coverClosingImg(root) {
    if (!root) return null;
    return (
      root.querySelector(".closing-hero__img--main") ||
      root.querySelector(".closing-hero__media img") ||
      root.querySelector("img")
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

  function clearBoundaryMotionStyles(state, activeClass) {
    if (!state) return;
    if (state.img) {
      state.img.style.transform = "";
      state.img.style.willChange = "";
    }
    if (state.panel) {
      state.panel.style.opacity = "";
      state.panel.style.transform = "";
    }
    if (activeClass) {
      document.documentElement.classList.remove(activeClass);
    }
  }

  function clearCoverMotionStyles() {
    clearBoundaryMotionStyles(coverMotionState, "cover-motion-active");
  }

  function clearClosingMotionStyles() {
    clearBoundaryMotionStyles(closingMotionState, "closing-motion-active");
  }

  function applyBoundaryMotionStyles(state, p, activeClass) {
    if (!state) return;
    var img = state.img;
    var panel = state.panel;
    var motion = state.motion;
    if (!img) return;
    if (p <= 0.001) {
      clearBoundaryMotionStyles(state, activeClass);
      return;
    }
    document.documentElement.classList.add(activeClass);
    img.style.willChange = "transform";
    img.style.transform =
      "translate3d(0," + p * motion.translate + "%,0) scale(" + (1 + p * motion.scale) + ")";
    if (panel) {
      panel.style.opacity = String(Math.max(0, 1 - p * 0.35));
      panel.style.transform = "translate3d(0," + p * 14 + "px,0)";
    }
  }

  function applyCoverMotionStyles(p) {
    applyBoundaryMotionStyles(coverMotionState, p, "cover-motion-active");
  }

  function applyClosingMotionStyles(p) {
    applyBoundaryMotionStyles(closingMotionState, p, "closing-motion-active");
  }

  function coverMotionTick() {
    if (paused) return;
    if (coverMotionState) {
      applyCoverMotionStyles(coverScrollProgress(coverMotionState.root));
    }
    if (closingMotionState) {
      applyClosingMotionStyles(coverScrollProgress(closingMotionState.root));
    }
  }

  function stopBoundaryMotionLoop() {
    if (coverMotionRaf) {
      cancelAnimationFrame(coverMotionRaf);
      coverMotionRaf = null;
    }
  }

  function boundaryMotionLoop() {
    coverMotionTick();
    if (coverMotionState || closingMotionState) {
      coverMotionRaf = global.requestAnimationFrame(boundaryMotionLoop);
    }
  }

  function destroyCoverMotion() {
    stopBoundaryMotionLoop();
    clearCoverMotionStyles();
    clearClosingMotionStyles();
    coverMotionState = null;
    closingMotionState = null;
  }

  function initCoverMotion() {
    if (prefersReducedMotion() || breathLevel() === "off") return;
    if (scrubStarted && (breathLevel() === "cinematic" || breathLevel() === "gallery")) {
      return;
    }
    var needLoop = false;
    var openingRoot = coverOpeningRoot();
    var openingImg = coverOpeningImg(openingRoot);
    if (openingRoot && openingImg) {
      coverMotionState = {
        root: openingRoot,
        img: openingImg,
        panel: openingRoot.querySelector(".cover-opening__panel"),
        motion: coverMotionIntensity(),
      };
      needLoop = true;
    }
    var closingRoot = coverClosingRoot();
    var closingImg = coverClosingImg(closingRoot);
    if (closingRoot && closingImg && coverClosingPresentationActive()) {
      closingMotionState = {
        root: closingRoot,
        img: closingImg,
        panel: closingRoot.querySelector(".cover-closing__panel"),
        motion: coverMotionIntensity(),
      };
      needLoop = true;
    }
    if (needLoop) boundaryMotionLoop();
  }

  function closingRevealInView(root) {
    if (!root || !global.getBoundingClientRect) return false;
    var rect = root.getBoundingClientRect();
    var vh = global.innerHeight || 0;
    return rect.top < vh * 0.94 && rect.bottom > 0;
  }

  function initCoverClosingReveal() {
    var root = coverClosingRoot();
    if (!root || breathLevel() === "off" || !coverClosingPresentationActive()) return;

    var hero = root.querySelector('.closing-hero[data-block="closing-hero"]');
    var panel = root.querySelector(".cover-closing__panel");
    var parts = [hero, panel].filter(Boolean);
    if (!parts.length) return;

    parts.forEach(function (el) {
      el.classList.add("breath-reveal", "closing-breath-reveal");
    });

    if (prefersReducedMotion() || closingRevealInView(root)) {
      parts.forEach(function (el) {
        el.classList.add("is-visible");
      });
      return;
    }

    closingRevealObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting && !paused) {
            parts.forEach(markVisible);
            if (closingRevealObserver) {
              closingRevealObserver.disconnect();
              closingRevealObserver = null;
            }
          }
        });
      },
      revealObserverOpts()
    );
    closingRevealObserver.observe(root);
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
    if (closingRevealObserver) {
      closingRevealObserver.disconnect();
      closingRevealObserver = null;
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
    var closingRoot = coverClosingRoot();
    if (closingRoot) {
      closingRoot.querySelectorAll(".closing-breath-reveal").forEach(function (el) {
        el.classList.remove("breath-reveal", "is-visible", "closing-breath-reveal");
        el.style.opacity = "";
        el.style.transform = "";
      });
      var closingPanel = closingRoot.querySelector(".cover-closing__panel");
      if (closingPanel) {
        closingPanel.style.opacity = "";
        closingPanel.style.transform = "";
      }
    }
    var closingImg = coverClosingImg(closingRoot);
    if (closingImg) {
      closingImg.style.transform = "";
      closingImg.style.willChange = "";
    }
    document.documentElement.classList.remove("cover-motion-active", "closing-motion-active");
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
    initCoverClosingReveal();
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
