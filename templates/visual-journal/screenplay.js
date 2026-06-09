/**
 * Travelogue · Web screens 放映（present）
 * 全屏逐屏展示 layout-screen，停留时长由 __TRAVELOGUE_READING__.present.dwellMs 配置。
 * Deep links: screenplay-hash.js · Bookmarks: screenplay-bookmarks.js
 */
(function (global) {
  "use strict";

  var DEFAULT_DWELL_MS = 2000;
  var FADE_MS = 700;
  var SELECTOR = '.layout-screen[data-block="layout-screen"]';
  var AUX_SELECTOR =
    'header[data-block="cover-hero"], .foreword-spread[data-block="foreword-spread"], .trip-index[data-block="trip-index"], .featured-grid[data-block="featured-grid"], .screen-spread[data-block="screen-spread"], section[data-block="cover-closing"], .epilogue-screen[data-block="epilogue-screen"], .epilogue[data-block="epilogue"]';
  var featuredOnlyOverride = null;
  var presentHash = global.TraveloguePresentHash || {};
  var presentBookmarks = global.TraveloguePresentBookmarks || {};

  function readingConfig() {
    return global.__TRAVELOGUE_READING__ || {};
  }

  function presentConfig() {
    return readingConfig().present || {};
  }

  function skipAuxBlocksEnabled() {
    return presentConfig().skipAuxBlocks === true;
  }

  function resolveDwellMs() {
    var ms = presentConfig().dwellMs;
    if (typeof ms === "number" && ms >= 500) return ms;
    return DEFAULT_DWELL_MS;
  }

  function syncScrollOnExitEnabled() {
    if (typeof presentConfig().syncScrollOnExit === "boolean") {
      return presentConfig().syncScrollOnExit;
    }
    return true;
  }

  function featuredOnlyEnabled() {
    if (featuredOnlyOverride !== null) {
      return featuredOnlyOverride === true;
    }
    return presentConfig().featuredOnly === true;
  }

  function autoAdvanceEnabled() {
    return presentConfig().autoAdvance !== false;
  }

  function manualControlsEnabled() {
    return presentConfig().manualControls !== false;
  }

  function tapZoneNavEnabled() {
    return presentConfig().tapZoneNav !== false;
  }

  function loopEnabled() {
    return presentConfig().loop === true;
  }

  function clickStageMode() {
    var mode = presentConfig().clickStage;
    if (mode === "stop" || mode === "pause" || mode === "none") return mode;
    return "pause";
  }

  function featuredAssetIds() {
    var ids = readingConfig().featuredAssetIds;
    return Array.isArray(ids) ? ids : [];
  }

  function featuredRequestedFromQuery() {
    var q = global.location.search || "";
    return /(?:^|[?&])presentFeatured=1(?:&|$)/.test(q);
  }

  function prefersReducedMotion() {
    return global.matchMedia && global.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function isLayoutScreen(el) {
    return el.matches && el.matches(SELECTOR);
  }

  function isTypingTarget(el) {
    if (!el || !el.tagName) return false;
    var tag = el.tagName;
    return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || el.isContentEditable;
  }

  function hasCoverClosingSlide() {
    return !!document.querySelector('section[data-block="cover-closing"]');
  }

  function presentSlideSelector() {
    if (skipAuxBlocksEnabled()) {
      return SELECTOR;
    }
    return AUX_SELECTOR + ", " + SELECTOR;
  }

  function collectSlides() {
    var all = Array.prototype.slice.call(document.querySelectorAll(presentSlideSelector()));
    if (hasCoverClosingSlide()) {
      all = all.filter(function (el) {
        if (el.matches('[data-block="epilogue-screen"]')) return false;
        if (
          el.matches('[data-block="epilogue"]') &&
          !el.closest('[data-block="cover-closing"]')
        ) {
          return false;
        }
        return true;
      });
    }
    if (!featuredOnlyEnabled()) {
      return all;
    }
    return all.filter(function (el) {
      return isLayoutScreen(el) && el.getAttribute("data-featured") === "true";
    });
  }

  function parseAspectRatio(el) {
    var raw = (el.style.getPropertyValue("--screen-aspect") || "").trim();
    if (raw) {
      var parts = raw.split("/");
      if (parts.length === 2) {
        var w = parseFloat(parts[0]);
        var h = parseFloat(parts[1]);
        if (w > 0 && h > 0) return w / h;
      }
    }
    return 16 / 9;
  }

  function cloneSlide(el) {
    if (!isLayoutScreen(el)) {
      var aux = el.cloneNode(true);
      aux.classList.add("screenplay-aux-slide");
      aux.querySelectorAll(
        ".cover-hero__play, [data-screenplay-trigger], [data-screenplay-action]"
      ).forEach(function (btn) {
        btn.remove();
      });
      return aux;
    }
    var clone = el.cloneNode(true);
    clone.classList.add("layout-screen--screenplay");
    var tone = el.style.getPropertyValue("--screen-tone");
    var aspect = el.style.getPropertyValue("--screen-aspect");
    clone.removeAttribute("style");
    if (tone) {
      clone.style.setProperty("--screen-tone", tone);
    }
    if (aspect) {
      clone.style.setProperty("--screen-aspect", aspect);
    }
    var hint = el.getAttribute("data-layout-hint");
    if (!hint) {
      clone.style.setProperty("--screenplay-fit-ar", String(parseAspectRatio(el)));
    }
    return clone;
  }

  function requestFullscreen(el) {
    var fn = el.requestFullscreen || el.webkitRequestFullscreen || el.msRequestFullscreen;
    if (!fn) return Promise.resolve();
    try {
      return Promise.resolve(fn.call(el));
    } catch (e) {
      return Promise.reject(e);
    }
  }

  function exitFullscreen() {
    var fn =
      document.exitFullscreen ||
      document.webkitExitFullscreen ||
      document.msExitFullscreen;
    if (fn && (document.fullscreenElement || document.webkitFullscreenElement)) {
      fn.call(document);
    }
  }

  function isFullscreen() {
    return !!(document.fullscreenElement || document.webkitFullscreenElement);
  }

  function ScreenplayPlayer(root, sources, trigger) {
    this.root = root;
    this.layerA = root.querySelector('[data-screenplay-layer="a"]');
    this.layerB = root.querySelector('[data-screenplay-layer="b"]');
    this.progressBar = root.querySelector(".screenplay-progress__bar");
    this.counter = root.querySelector(".screenplay-counter");
    this.pauseBtn = root.querySelector('[data-screenplay-action="pause"]');
    this.navWrap = root.querySelector(".screenplay-chrome__nav");
    this.sources = sources;
    this.trigger = trigger;
    this.index = 0;
    this.timer = null;
    this.activeLayer = this.layerA;
    this.idleLayer = this.layerB;
    this.running = false;
    this.autoAdvancePaused = false;
    this.fadeMs = prefersReducedMotion() ? 0 : FADE_MS;
    this.dwellMs = prefersReducedMotion() ? 1500 : resolveDwellMs();
  }

  ScreenplayPlayer.prototype.clearTimer = function () {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  };

  ScreenplayPlayer.prototype.schedule = function (fn, ms) {
    this.clearTimer();
    this.timer = setTimeout(fn, ms);
  };

  ScreenplayPlayer.prototype.scheduleAdvance = function () {
    if (!this.running || !autoAdvanceEnabled() || this.autoAdvancePaused) return;
    var self = this;
    this.schedule(function () {
      self.advance();
    }, this.dwellMs);
  };

  ScreenplayPlayer.prototype.updatePauseButton = function () {
    if (!this.pauseBtn) return;
    var paused = this.autoAdvancePaused;
    this.pauseBtn.setAttribute("aria-pressed", paused ? "true" : "false");
    this.pauseBtn.textContent = paused
      ? this.pauseBtn.getAttribute("data-label-play") || "继续"
      : this.pauseBtn.getAttribute("data-label-pause") || "暂停";
  };

  ScreenplayPlayer.prototype.updateChrome = function () {
    if (this.navWrap) {
      this.navWrap.hidden = !manualControlsEnabled();
    }
    if (this.pauseBtn) {
      this.pauseBtn.hidden = !autoAdvanceEnabled();
      this.updatePauseButton();
    }
  };

  ScreenplayPlayer.prototype.setTriggerLabel = function (playing) {
    var triggers = document.querySelectorAll(
      "#screenplay-start, [data-screenplay-trigger=\"start\"]"
    );
    for (var i = 0; i < triggers.length; i++) {
      var el = triggers[i];
      if (playing) {
        el.textContent =
          el.getAttribute("data-screenplay-busy") || "退出放映";
        el.setAttribute("aria-pressed", "true");
      } else {
        el.textContent =
          el.getAttribute("data-screenplay-label") || "放映";
        el.setAttribute("aria-pressed", "false");
      }
    }
  };

  ScreenplayPlayer.prototype.updateProgress = function () {
    if (this.progressBar) {
      var pct =
        this.sources.length <= 1
          ? 100
          : (this.index / (this.sources.length - 1)) * 100;
      this.progressBar.style.width = pct + "%";
    }
    if (this.counter) {
      this.counter.textContent =
        this.index + 1 + " / " + this.sources.length;
    }
  };

  ScreenplayPlayer.prototype.mountSlide = function (layer, source) {
    layer.innerHTML = "";
    layer.appendChild(cloneSlide(source));
    layer.classList.remove("is-visible");
    void layer.offsetWidth;
  };

  ScreenplayPlayer.prototype.showLayer = function (layer) {
    this.activeLayer.classList.remove("is-visible");
    layer.classList.add("is-visible");
    this.idleLayer = this.activeLayer;
    this.activeLayer = layer;
  };

  ScreenplayPlayer.prototype.goToIndex = function (nextIndex, animate) {
    if (!this.running || nextIndex < 0 || nextIndex >= this.sources.length) return;
    this.clearTimer();
    var self = this;

    var finish = function () {
      self.index = nextIndex;
      self.updateProgress();
      if (presentHash.set) presentHash.set(self.index);
      self.scheduleAdvance();
    };

    if (nextIndex === this.index) {
      finish();
      return;
    }

    if (animate === false || this.fadeMs === 0) {
      this.mountSlide(this.activeLayer, this.sources[nextIndex]);
      this.activeLayer.classList.add("is-visible");
      this.idleLayer.classList.remove("is-visible");
      finish();
      return;
    }

    this.mountSlide(this.idleLayer, this.sources[nextIndex]);
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        self.showLayer(self.idleLayer);
        self.schedule(finish, self.fadeMs);
      });
    });
  };

  ScreenplayPlayer.prototype.advance = function () {
    if (!this.running) return;

    var nextIndex = this.index + 1;
    if (nextIndex >= this.sources.length) {
      if (loopEnabled()) {
        nextIndex = 0;
      } else {
        this.stop(false);
        return;
      }
    }

    this.goToIndex(nextIndex, true);
  };

  ScreenplayPlayer.prototype.next = function () {
    if (!this.running || !manualControlsEnabled()) return;
    var nextIndex = this.index + 1;
    if (nextIndex >= this.sources.length) {
      if (loopEnabled()) nextIndex = 0;
      else return;
    }
    this.goToIndex(nextIndex, true);
  };

  ScreenplayPlayer.prototype.prev = function () {
    if (!this.running || !manualControlsEnabled()) return;
    var prevIndex = this.index - 1;
    if (prevIndex < 0) {
      if (loopEnabled()) prevIndex = this.sources.length - 1;
      else return;
    }
    this.goToIndex(prevIndex, true);
  };

  ScreenplayPlayer.prototype.togglePause = function () {
    if (!this.running || !autoAdvanceEnabled()) return;
    this.autoAdvancePaused = !this.autoAdvancePaused;
    this.updatePauseButton();
    if (this.autoAdvancePaused) {
      this.clearTimer();
    } else {
      this.scheduleAdvance();
    }
  };

  ScreenplayPlayer.prototype.goTo = function (index) {
    if (!this.running || index < 0 || index >= this.sources.length) return;
    this.goToIndex(index, false);
  };

  function pauseBreath() {
    if (global.TravelogueBreath && typeof global.TravelogueBreath.pause === "function") {
      global.TravelogueBreath.pause();
    }
  }

  function resumeBreath() {
    if (global.TravelogueBreath && typeof global.TravelogueBreath.resume === "function") {
      global.TravelogueBreath.resume();
    }
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

  function syncLenisToViewport() {
    if (global.TravelogueLenis && typeof global.TravelogueLenis.scrollTo === "function") {
      global.TravelogueLenis.scrollTo(global.scrollY || 0);
    }
  }

  ScreenplayPlayer.prototype.syncScrollToSlide = function (slideIndex) {
    if (!syncScrollOnExitEnabled()) return;
    var target = this.sources[slideIndex];
    if (!target || typeof target.scrollIntoView !== "function") return;
    var behavior = prefersReducedMotion() ? "auto" : "smooth";
    try {
      target.scrollIntoView({
        behavior: behavior,
        block: "start",
        inline: "nearest",
      });
    } catch (_e) {
      target.scrollIntoView(true);
    }
    if (target.classList && target.classList.contains("breath-reveal")) {
      target.classList.add("is-visible");
    }
    syncLenisToViewport();
  };

  ScreenplayPlayer.prototype.start = function (startIndex) {
    var self = this;
    pauseBreath();
    pauseLenis();
    this.sources = collectSlides();
    if (!this.sources.length) {
      resumeBreath();
      resumeLenis();
      return;
    }
    var initialIndex = 0;
    if (typeof startIndex === "number" && startIndex >= 0) {
      initialIndex = Math.min(startIndex, this.sources.length - 1);
    }
    this.running = true;
    this.autoAdvancePaused = false;
    this.index = initialIndex;
    this.mountSlide(this.activeLayer, this.sources[initialIndex]);
    this.activeLayer.classList.add("is-visible");
    this.idleLayer.classList.remove("is-visible");
    this.updateProgress();
    this.updateChrome();
    if (presentHash.set) presentHash.set(this.index);
    this.root.hidden = false;
    document.body.classList.add("screenplay-active");
    this.setTriggerLabel(true);

    requestFullscreen(this.root)
      .catch(function () {
        /* 用户拒绝或环境不支持时仍可在页面内播放 */
      })
      .then(function () {
        self.scheduleAdvance();
      });
  };

  ScreenplayPlayer.prototype.stop = function (fromUser) {
    if (!this.running && this.root.hidden) return;
    var slideIndex = this.index;
    this.running = false;
    this.autoAdvancePaused = false;
    this.clearTimer();
    document.body.classList.remove("screenplay-active");
    this.root.hidden = true;
    this.layerA.innerHTML = "";
    this.layerB.innerHTML = "";
    this.layerA.classList.remove("is-visible");
    this.layerB.classList.remove("is-visible");
    this.setTriggerLabel(false);

    var self = this;
    var finishExit = function () {
      if (presentHash.clear) presentHash.clear();
      self.syncScrollToSlide(slideIndex);
      resumeBreath();
      resumeLenis();
    };

    if (fromUser || isFullscreen()) {
      exitFullscreen();
      setTimeout(finishExit, 80);
    } else {
      finishExit();
    }
  };

  function updateFeaturedToggleButton(btn, active) {
    if (!btn) return;
    btn.setAttribute("aria-pressed", active ? "true" : "false");
    btn.textContent = active
      ? btn.getAttribute("data-label-off") || "全部放映"
      : btn.getAttribute("data-label-on") || "精选放映";
  }

  function init() {
    var sources = collectSlides();
    var triggers = document.querySelectorAll(
      "#screenplay-start, [data-screenplay-trigger=\"start\"]"
    );
    var toolbar = document.querySelector(".screenplay-toolbar");
    var root = document.getElementById("screenplay-root");
    var primaryTrigger = document.getElementById("screenplay-start") || triggers[0];
    var featuredToggle = document.getElementById("featured-present-toggle");

    if (featuredAssetIds().length && featuredRequestedFromQuery()) {
      featuredOnlyOverride = true;
      sources = collectSlides();
    }

    if (featuredToggle && featuredAssetIds().length) {
      var initialFeatured =
        featuredOnlyOverride !== null
          ? featuredOnlyOverride
          : presentConfig().featuredOnly === true;
      featuredOnlyOverride = initialFeatured;
      updateFeaturedToggleButton(featuredToggle, initialFeatured);
      sources = collectSlides();
      featuredToggle.addEventListener("click", function () {
        featuredOnlyOverride = !featuredOnlyEnabled();
        updateFeaturedToggleButton(featuredToggle, featuredOnlyOverride);
      });
    }

    if (!sources.length || !triggers.length || !root) {
      if (toolbar) toolbar.hidden = true;
      var coverPlay = document.querySelector(".cover-hero__play");
      if (coverPlay) coverPlay.hidden = true;
      return;
    }

    var player = new ScreenplayPlayer(root, sources, primaryTrigger);
    player.updateChrome();
    if (presentBookmarks.wire) {
      presentBookmarks.wire(root, player);
    }

    for (var i = 0; i < triggers.length; i++) {
      triggers[i].addEventListener("click", function () {
        if (player.running) {
          player.stop(true);
        } else {
          player.start();
        }
      });
    }

    root.querySelectorAll("[data-screenplay-action]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.stopPropagation();
        var action = btn.getAttribute("data-screenplay-action");
        if (action === "stop") player.stop(true);
        else if (action === "prev") player.prev();
        else if (action === "next") player.next();
        else if (action === "pause") player.togglePause();
      });
    });

    root.addEventListener("click", function (e) {
      if (e.target.closest("[data-screenplay-action]")) return;
      if (!player.running) return;

      if (tapZoneNavEnabled() && e.target.closest(".screenplay-stage")) {
        var stage = root.querySelector(".screenplay-stage");
        if (stage) {
          var rect = stage.getBoundingClientRect();
          var x = e.clientX - rect.left;
          var third = rect.width / 3;
          if (x < third) {
            player.prev();
            return;
          }
          if (x > third * 2) {
            player.next();
            return;
          }
        }
      }

      var mode = clickStageMode();
      if (mode === "stop") {
        player.stop(true);
      } else if (mode === "pause") {
        player.togglePause();
      }
    });

    document.addEventListener("keydown", function (e) {
      if (!player.running) return;
      if (e.key === "Escape") {
        player.stop(true);
        return;
      }
      if (!manualControlsEnabled() || isTypingTarget(e.target)) return;

      if (
        e.key === "ArrowRight" ||
        e.key === "ArrowDown" ||
        e.key === " " ||
        e.key === "PageDown"
      ) {
        e.preventDefault();
        player.next();
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp" || e.key === "PageUp") {
        e.preventDefault();
        player.prev();
      } else if ((e.key === "p" || e.key === "P") && autoAdvanceEnabled()) {
        e.preventDefault();
        player.togglePause();
      }
    });

    document.addEventListener("fullscreenchange", onFullscreenEnd);
    document.addEventListener("webkitfullscreenchange", onFullscreenEnd);

    function onFullscreenEnd() {
      if (player.running && !isFullscreen()) {
        player.stop(false);
      }
    }

    function startFromHash() {
      if (player.running || !presentHash.parse) return;
      var idx = presentHash.parse();
      if (idx === null) return;
      player.start(idx);
    }

    if (presentHash.enabled && presentHash.enabled() && presentHash.parse && presentHash.parse() !== null) {
      startFromHash();
    }

    global.addEventListener("hashchange", function () {
      if (!presentHash.enabled || !presentHash.enabled()) return;
      var idx = presentHash.parse ? presentHash.parse() : null;
      if (idx === null) {
        if (player.running) player.stop(true);
        return;
      }
      if (player.running) {
        player.goTo(idx);
      } else {
        player.start(idx);
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})(window);
