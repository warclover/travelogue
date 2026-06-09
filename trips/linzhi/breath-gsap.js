/**
 * Travelogue · breath scrub engine (PRD-EXPERIENCE appendix B · E8)
 * Scroll-linked transforms · native scrub or optional GSAP ScrollTrigger (P5).
 * Modes: cinematic (cover/header parallax) · gallery (media-scroll pin).
 */
(function (global) {
  "use strict";

  var triggers = [];
  var pins = [];
  var gsapTriggers = [];
  var scrollHandler = null;
  var paused = false;

  function readingScroll() {
    return (global.__TRAVELOGUE_READING__ || {}).scroll || {};
  }

  function useGsapEngine() {
    return (
      readingScroll().breathEngine === "gsap" &&
      global.gsap &&
      global.ScrollTrigger
    );
  }

  function killGsapTriggers() {
    gsapTriggers.forEach(function (st) {
      if (st && typeof st.kill === "function") st.kill();
    });
    gsapTriggers = [];
  }

  function clamp(n, min, max) {
    return Math.max(min, Math.min(max, n));
  }

  function scrollProgress(el, startRatio, endRatio) {
    var rect = el.getBoundingClientRect();
    var vh = global.innerHeight || 1;
    var start = vh * startRatio;
    var end = vh * endRatio;
    var span = rect.height + vh - start - end;
    if (span <= 0) return rect.top <= vh ? 1 : 0;
    return clamp((start - rect.top) / span, 0, 1);
  }

  function clearTriggerStyles(t) {
    if (t.el) {
      t.el.style.transform = "";
      t.el.style.opacity = "";
    }
    if (t.inner) {
      t.inner.style.transform = "";
    }
  }

  function addTrigger(el, apply, opts) {
    triggers.push({ el: el, apply: apply, opts: opts || {} });
  }

  function shouldDegradeCinematic() {
    var screens = document.querySelectorAll('.layout-screen[data-block="layout-screen"]').length;
    var coarse = global.matchMedia && global.matchMedia("(pointer: coarse)").matches;
    var lowMem = global.navigator && global.navigator.deviceMemory && global.navigator.deviceMemory <= 4;
    return screens > 40 && coarse && lowMem;
  }

  function coverParallaxRoot() {
    return (
      document.querySelector('.cover-opening[data-block="cover-opening"]') ||
      document.querySelector('.cover-hero[data-block="cover-hero"]')
    );
  }

  function coverParallaxImg(root) {
    if (!root) return null;
    return (
      root.querySelector(".cover-hero__img--main") ||
      root.querySelector(".cover-hero__media img:last-of-type") ||
      root.querySelector("img")
    );
  }

  function clearCoverParallax(img) {
    if (!img) return;
    img.style.transform = "";
    img.style.willChange = "";
  }

  function coverPanel(root) {
    return root && root.querySelector(".cover-opening__panel");
  }

  function setCoverMotionActive(active) {
    document.documentElement.classList.toggle("cover-motion-active", !!active);
  }

  function clearCoverMotion(root, img) {
    clearCoverParallax(img);
    var panel = coverPanel(root);
    if (panel) {
      panel.style.opacity = "";
      panel.style.transform = "";
    }
    setCoverMotionActive(false);
  }

  function applyCoverScrollMotion(img, panel, p) {
    if (!img) return;
    img.style.willChange = "transform";
    img.style.transform =
      "translate3d(0," + p * 20 + "%,0) scale(" + (1 + p * 0.08) + ")";
    if (panel) {
      panel.style.opacity = String(Math.max(0, 1 - p * 0.35));
      panel.style.transform = "translate3d(0," + p * 14 + "px,0)";
    }
  }

  function setupCoverParallaxGsap() {
    var coverRoot = coverParallaxRoot();
    if (!coverRoot) return;
    var img = coverParallaxImg(coverRoot);
    if (!img) return;
    var panel = coverPanel(coverRoot);

    gsapTriggers.push(
      ScrollTrigger.create({
        trigger: coverRoot,
        start: "top top",
        end: "bottom top",
        scrub: 0.75,
        onEnter: function () {
          setCoverMotionActive(true);
        },
        onEnterBack: function () {
          setCoverMotionActive(true);
        },
        onUpdate: function (self) {
          applyCoverScrollMotion(img, panel, self.progress);
        },
        onLeave: function () {
          clearCoverMotion(coverRoot, img);
        },
        onLeaveBack: function () {
          clearCoverMotion(coverRoot, img);
        },
      })
    );
  }

  function setupCoverParallaxNative() {
    var coverRoot = coverParallaxRoot();
    if (!coverRoot) return;
    var img = coverParallaxImg(coverRoot);
    if (!img) return;
    var panel = coverPanel(coverRoot);

    addTrigger(
      coverRoot,
      function (p) {
        if (p >= 1) {
          clearCoverMotion(coverRoot, img);
          return;
        }
        if (p > 0.001) {
          setCoverMotionActive(true);
          applyCoverScrollMotion(img, panel, p);
        } else {
          clearCoverMotion(coverRoot, img);
        }
      },
      { start: 0, end: 0.22 }
    );
  }

  function setupCinematicGsap() {
    var gsap = global.gsap;
    var ScrollTrigger = global.ScrollTrigger;
    gsap.registerPlugin(ScrollTrigger);

    setupCoverParallaxGsap();
    Array.prototype.forEach.call(
      document.querySelectorAll('.chapter-header[data-block="chapter-header"]'),
      function (el) {
        gsapTriggers.push(
          ScrollTrigger.create({
            trigger: el,
            start: "top 92%",
            end: "top 52%",
            scrub: 0.85,
            onUpdate: function (self) {
              var p = self.progress;
              el.style.opacity = String(0.35 + p * 0.65);
              el.style.transform = "translate3d(0," + (1 - p) * 26 + "px,0)";
            },
          })
        );
      }
    );

    if (global.TravelogueImageBreath) {
      global.TravelogueImageBreath.setup(gsap, ScrollTrigger, function (st) {
        gsapTriggers.push(st);
      });
    }
  }

  function setupGalleryPinGsap(pin) {
    var ScrollTrigger = global.ScrollTrigger;
    gsapTriggers.push(
      ScrollTrigger.create({
        trigger: pin.wrapper,
        start: "top top",
        end: function () {
          return "+=" + pin.scrollDistance;
        },
        pin: pin.root,
        pinSpacing: false,
        scrub: true,
        onUpdate: function (self) {
          pin.track.style.transform =
            "translate3d(" + -self.progress * pin.maxX + "px,0,0)";
        },
      })
    );
  }

  function setupGalleryPinsGsap() {
    setupMediaScrollGalleryPins();
    setupGalleryScreenPins();
    pins.forEach(setupGalleryPinGsap);
  }

  function setupCinematic() {
    setupCoverParallaxNative();

    Array.prototype.forEach.call(
      document.querySelectorAll('.chapter-header[data-block="chapter-header"]'),
      function (el) {
        addTrigger(
          el,
          function (p) {
            el.style.opacity = String(0.7 + p * 0.3);
            el.style.transform = "translate3d(0," + (1 - p) * 10 + "px,0)";
          },
          { start: 0.08, end: 0.25 }
        );
      }
    );

    Array.prototype.forEach.call(document.querySelectorAll(".chapter"), function (ch) {
      var first = ch.querySelector('.layout-screen[data-block="layout-screen"]');
      if (!first) return;
      addTrigger(
        first,
        function (p) {
          first.style.transform = "translate3d(0," + (1 - p) * 18 + "px,0)";
        },
        { start: 0.1, end: 0.6 }
      );
    });
  }

  function setupGalleryPins() {
    setupMediaScrollGalleryPins();
    setupGalleryScreenPins();
  }

  function setupMediaScrollGalleryPins() {
    Array.prototype.forEach.call(
      document.querySelectorAll('.media-scroll[data-block="media-scroll"]'),
      function (root) {
        var chapter = root.closest(".chapter");
        if (chapter && chapter.getAttribute("data-pattern") !== "gallery") {
          return;
        }
        var track = root.querySelector(".media-scroll__track");
        if (!track) return;

        var maxX = Math.max(0, track.scrollWidth - root.clientWidth);
        if (maxX <= 0) return;

        root.classList.add("breath-gallery-pin-root");
        track.classList.add("breath-gallery-pin-track");

        var wrapper = document.createElement("div");
        wrapper.className = "breath-gallery-pin-spacer";
        var scrollDistance = maxX * 1.05 + global.innerHeight * 0.35;
        wrapper.style.height = scrollDistance + root.offsetHeight + "px";

        var parent = root.parentNode;
        parent.insertBefore(wrapper, root);
        wrapper.appendChild(root);

        root.style.position = "sticky";
        root.style.top = "0";

        pins.push({
          wrapper: wrapper,
          parent: parent,
          root: root,
          track: track,
          maxX: maxX,
          scrollDistance: scrollDistance,
        });
      }
    );
  }

  function setupGalleryScreenPins() {
    Array.prototype.forEach.call(
      document.querySelectorAll('.chapter[data-pattern="gallery"]'),
      function (chapter) {
        if (chapter.querySelector('.media-scroll[data-block="media-scroll"]')) {
          return;
        }
        var screens = Array.prototype.slice.call(
          chapter.querySelectorAll('.layout-screen[data-block="layout-screen"]')
        );
        if (screens.length < 2) return;

        var rail = document.createElement("div");
        rail.className = "breath-gallery-screens-rail breath-gallery-pin-root";
        var track = document.createElement("div");
        track.className = "breath-gallery-screens-track breath-gallery-pin-track";

        var anchor = screens[0];
        var parent = anchor.parentNode;
        parent.insertBefore(rail, anchor);
        rail.appendChild(track);
        screens.forEach(function (screen) {
          screen.classList.add("breath-gallery-screens-panel");
          track.appendChild(screen);
        });

        var maxX = Math.max(0, track.scrollWidth - rail.clientWidth);
        if (maxX <= 0) {
          screens.forEach(function (screen) {
            screen.classList.remove("breath-gallery-screens-panel");
            parent.insertBefore(screen, rail);
          });
          rail.remove();
          return;
        }

        var wrapper = document.createElement("div");
        wrapper.className = "breath-gallery-pin-spacer";
        var scrollDistance = maxX * 1.05 + global.innerHeight * 0.35;
        wrapper.style.height = scrollDistance + rail.offsetHeight + "px";

        parent.insertBefore(wrapper, rail);
        wrapper.appendChild(rail);

        rail.style.position = "sticky";
        rail.style.top = "0";

        pins.push({
          wrapper: wrapper,
          parent: parent,
          root: rail,
          track: track,
          maxX: maxX,
          scrollDistance: scrollDistance,
          galleryScreens: true,
          screens: screens,
        });
      }
    );
  }

  function updatePins() {
    pins.forEach(function (pin) {
      var rect = pin.wrapper.getBoundingClientRect();
      var vh = global.innerHeight || 1;
      var total = pin.scrollDistance + pin.root.offsetHeight;
      var progress = clamp((vh - rect.top) / total, 0, 1);
      pin.track.style.transform = "translate3d(" + -progress * pin.maxX + "px,0,0)";
    });
  }

  function tick() {
    if (paused) return;
    triggers.forEach(function (t) {
      var opts = t.opts || {};
      var p = scrollProgress(t.el, opts.start || 0, opts.end || 0.3);
      t.apply(p, t.el);
    });
    if (pins.length) updatePins();
  }

  function bindScroll() {
    if (scrollHandler) return;
    scrollHandler = tick;
    global.addEventListener("scroll", scrollHandler, { passive: true });
    global.addEventListener("resize", scrollHandler, { passive: true });
    tick();
  }

  function unbindScroll() {
    if (!scrollHandler) return;
    global.removeEventListener("scroll", scrollHandler);
    global.removeEventListener("resize", scrollHandler);
    scrollHandler = null;
  }

  function teardownPins() {
    pins.forEach(function (pin) {
      pin.root.style.position = "";
      pin.root.style.top = "";
      pin.root.classList.remove("breath-gallery-pin-root");
      pin.track.style.transform = "";
      pin.track.classList.remove("breath-gallery-pin-track");
      if (pin.galleryScreens && pin.screens && pin.parent && pin.wrapper) {
        pin.screens.forEach(function (screen) {
          screen.classList.remove("breath-gallery-screens-panel");
          pin.parent.insertBefore(screen, pin.wrapper);
        });
      }
      if (pin.parent && pin.wrapper) {
        if (!pin.galleryScreens) {
          pin.parent.insertBefore(pin.root, pin.wrapper);
        }
        pin.wrapper.remove();
      }
    });
    pins = [];
  }

  function destroy() {
    unbindScroll();
    killGsapTriggers();
    if (global.TravelogueImageBreath) {
      global.TravelogueImageBreath.clear();
    }
    triggers.forEach(clearTriggerStyles);
    triggers = [];
    teardownPins();
    paused = false;
    document.documentElement.classList.remove("breath-scrub-active");
  }

  function init(mode) {
    destroy();
    if (mode !== "cinematic" && mode !== "gallery") return;
    if (mode === "cinematic" && shouldDegradeCinematic()) {
      mode = "cinematic-lite";
    }
    document.documentElement.classList.add("breath-scrub-active");
    var gsapMode = useGsapEngine() && mode !== "cinematic-lite";
    if (mode === "cinematic" || mode === "cinematic-lite") {
      if (gsapMode) setupCinematicGsap();
      else setupCinematic();
    }
    if (mode === "gallery") {
      if (gsapMode) setupGalleryPinsGsap();
      else setupGalleryPins();
    }
    if (!gsapMode) bindScroll();
    else if (global.ScrollTrigger && typeof global.ScrollTrigger.refresh === "function") {
      global.ScrollTrigger.refresh();
    }
  }

  global.TravelogueScrub = {
    init: init,
    pause: function () {
      paused = true;
    },
    resume: function () {
      paused = false;
      if (useGsapEngine() && global.ScrollTrigger) {
        global.ScrollTrigger.update();
      } else {
        tick();
      }
    },
    destroy: destroy,
    refresh: tick,
  };
})(window);
