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
    return Array.prototype.slice.call(
      document.querySelectorAll(SCREEN_SEL + "," + EXTRA_SEL)
    );
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
    destroyHighlight();
    collectTargets().forEach(function (el) {
      el.classList.remove("breath-reveal", "is-visible", "breath-reveal--featured");
      el.style.opacity = "";
      el.style.transform = "";
    });
    var coverImg = document.querySelector('.cover-hero[data-block="cover-hero"] img');
    if (coverImg) coverImg.style.transform = "";
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
    initReveal();
    initFlowScroll();
    initScrubMotion();
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
