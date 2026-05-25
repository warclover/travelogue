/**
 * Travelogue · Web screens 自动播放
 * 全屏逐屏展示 layout-screen，每屏停留 2s，淡入淡出切换。
 */
(function (global) {
  "use strict";

  var DWELL_MS = 2000;
  var FADE_MS = 700;
  var SELECTOR = '.layout-screen[data-block="layout-screen"]';

  function prefersReducedMotion() {
    return global.matchMedia && global.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function collectSlides() {
    return Array.prototype.slice.call(document.querySelectorAll(SELECTOR));
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
    this.sources = sources;
    this.trigger = trigger;
    this.index = 0;
    this.timer = null;
    this.activeLayer = this.layerA;
    this.idleLayer = this.layerB;
    this.running = false;
    this.fadeMs = prefersReducedMotion() ? 0 : FADE_MS;
    this.dwellMs = prefersReducedMotion() ? 1500 : DWELL_MS;
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

  ScreenplayPlayer.prototype.setTriggerLabel = function (playing) {
    var triggers = document.querySelectorAll(
      "#screenplay-start, [data-screenplay-trigger=\"start\"]"
    );
    for (var i = 0; i < triggers.length; i++) {
      var el = triggers[i];
      if (playing) {
        el.textContent =
          el.getAttribute("data-screenplay-busy") || "退出播放";
        el.setAttribute("aria-pressed", "true");
      } else {
        el.textContent =
          el.getAttribute("data-screenplay-label") || "自动播放";
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

  ScreenplayPlayer.prototype.advance = function () {
    if (!this.running) return;

    var nextIndex = this.index + 1;
    if (nextIndex >= this.sources.length) {
      this.stop(false);
      return;
    }

    var self = this;
    this.mountSlide(this.idleLayer, this.sources[nextIndex]);

    var afterTransition = function () {
      self.index = nextIndex;
      self.updateProgress();
      self.schedule(function () {
        self.advance();
      }, self.dwellMs);
    };

    if (this.fadeMs === 0) {
      this.showLayer(this.idleLayer);
      afterTransition();
      return;
    }

    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        self.showLayer(self.idleLayer);
        self.schedule(afterTransition, self.fadeMs);
      });
    });
  };

  ScreenplayPlayer.prototype.start = function () {
    var self = this;
    this.running = true;
    this.index = 0;
    this.mountSlide(this.activeLayer, this.sources[0]);
    this.activeLayer.classList.add("is-visible");
    this.idleLayer.classList.remove("is-visible");
    this.updateProgress();
    this.root.hidden = false;
    document.body.classList.add("screenplay-active");
    this.setTriggerLabel(true);

    requestFullscreen(this.root)
      .catch(function () {
        /* 用户拒绝或环境不支持时仍可在页面内播放 */
      })
      .then(function () {
        self.schedule(function () {
          self.advance();
        }, self.dwellMs);
      });
  };

  ScreenplayPlayer.prototype.stop = function (fromUser) {
    if (!this.running && this.root.hidden) return;
    this.running = false;
    this.clearTimer();
    document.body.classList.remove("screenplay-active");
    this.root.hidden = true;
    this.layerA.innerHTML = "";
    this.layerB.innerHTML = "";
    this.layerA.classList.remove("is-visible");
    this.layerB.classList.remove("is-visible");
    this.setTriggerLabel(false);
    if (fromUser || isFullscreen()) {
      exitFullscreen();
    }
  };

  function init() {
    var sources = collectSlides();
    var triggers = document.querySelectorAll(
      "#screenplay-start, [data-screenplay-trigger=\"start\"]"
    );
    var toolbar = document.querySelector(".screenplay-toolbar");
    var root = document.getElementById("screenplay-root");
    var primaryTrigger = document.getElementById("screenplay-start") || triggers[0];

    if (!sources.length || !triggers.length || !root) {
      if (toolbar) toolbar.hidden = true;
      var coverPlay = document.querySelector(".cover-hero__play");
      if (coverPlay) coverPlay.hidden = true;
      return;
    }

    var player = new ScreenplayPlayer(root, sources, primaryTrigger);

    for (var i = 0; i < triggers.length; i++) {
      triggers[i].addEventListener("click", function () {
        if (player.running) {
          player.stop(true);
        } else {
          player.start();
        }
      });
    }

    var stopBtn = root.querySelector("[data-screenplay-action=stop]");
    if (stopBtn) {
      stopBtn.addEventListener("click", function () {
        player.stop(true);
      });
    }

    root.addEventListener("click", function (e) {
      if (e.target.closest("[data-screenplay-action=stop]")) return;
      if (player.running) player.stop(true);
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && player.running) {
        player.stop(true);
      }
    });

    document.addEventListener("fullscreenchange", onFullscreenEnd);
    document.addEventListener("webkitfullscreenchange", onFullscreenEnd);

    function onFullscreenEnd() {
      if (player.running && !isFullscreen()) {
        player.stop(false);
      }
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})(window);
