/**
 * Travelogue · breath flow smooth scroll (PRD-EXPERIENCE appendix B · E6)
 * Lightweight lerp scroll — PRD params: lerp 0.1, wheelMultiplier 0.85, syncTouch false.
 */
(function (global) {
  "use strict";

  var instance = null;

  function maxScrollY() {
    return Math.max(
      0,
      (document.documentElement.scrollHeight || 0) - global.innerHeight
    );
  }

  function resolveScrollTarget(y) {
    if (y && typeof y === "object" && typeof y.getBoundingClientRect === "function") {
      return (global.scrollY || 0) + y.getBoundingClientRect().top;
    }
    return typeof y === "number" && !isNaN(y) ? y : global.scrollY || 0;
  }

  function clampPair(current, target) {
    var max = maxScrollY();
    return {
      current: Math.max(0, Math.min(current, max)),
      target: Math.max(0, Math.min(target, max)),
    };
  }

  function overflowAllowsScroll(style) {
    var oy = style.overflowY;
    return oy === "auto" || oy === "scroll" || oy === "overlay";
  }

  /** Let nested overflow containers (Sheet / drawer) consume wheel natively. */
  function canConsumeWheel(el, deltaY) {
    if (!el || el === document.body || el === document.documentElement) return false;
    var style = global.getComputedStyle(el);
    if (!overflowAllowsScroll(style)) return false;
    if (el.scrollHeight <= el.clientHeight + 1) return false;
    var maxScroll = el.scrollHeight - el.clientHeight;
    if (deltaY < 0) return el.scrollTop > 0;
    if (deltaY > 0) return el.scrollTop < maxScroll - 1;
    return false;
  }

  function wheelBypassTarget(target, deltaY) {
    var el = target;
    while (el && el !== document.documentElement) {
      if (canConsumeWheel(el, deltaY)) return el;
      el = el.parentElement;
    }
    return null;
  }

  var FLOW_TAIL_MS = 300;
  var FLOW_FRAME_MS = 1000 / 60;
  var EXTERNAL_SCROLL_EPS = 4;

  function FlowScroll(options) {
    options = options || {};
    this.lerp = typeof options.lerp === "number" ? options.lerp : 0.1;
    this.settleLerp =
      typeof options.settleLerp === "number" ? options.settleLerp : 0.28;
    this.wheelMultiplier =
      typeof options.wheelMultiplier === "number" ? options.wheelMultiplier : 0.85;
    this.wheelIdleMs =
      typeof options.wheelIdleMs === "number" ? options.wheelIdleMs : 90;
    this.tailMs =
      typeof options.tailMs === "number" ? options.tailMs : FLOW_TAIL_MS;
    this.paused = false;
    this.current = 0;
    this.target = 0;
    this.rafId = null;
    this.lastWheelAt = 0;
    this.coastStartedAt = 0;
    this.onWheel = this.onWheel.bind(this);
    this.onScroll = this.onScroll.bind(this);
    this.loop = this.loop.bind(this);
  }

  FlowScroll.prototype.syncFromViewport = function () {
    this.current = global.scrollY || 0;
    this.target = this.current;
  };

  FlowScroll.prototype.adoptExternalScroll = function (y) {
    this.current = y;
    this.target = y;
    this.coastStartedAt = 0;
    this.lastWheelAt = 0;
  };

  FlowScroll.prototype.onScroll = function () {
    if (this.paused) return;
    var y = global.scrollY || 0;
    if (
      Math.abs(y - this.current) > EXTERNAL_SCROLL_EPS &&
      Math.abs(y - this.target) > EXTERNAL_SCROLL_EPS
    ) {
      this.adoptExternalScroll(y);
    }
  };

  FlowScroll.prototype.onWheel = function (e) {
    if (this.paused) return;
    if (wheelBypassTarget(e.target, e.deltaY)) return;
    e.preventDefault();
    this.lastWheelAt = Date.now();
    this.coastStartedAt = 0;
    this.target += e.deltaY * this.wheelMultiplier;
    var clamped = clampPair(this.current, this.target);
    this.current = clamped.current;
    this.target = clamped.target;
  };

  FlowScroll.prototype.loop = function () {
    if (!this.paused) {
      var clamped = clampPair(this.current, this.target);
      this.current = clamped.current;
      this.target = clamped.target;
      var diff = this.target - this.current;
      if (Math.abs(diff) > 0.5) {
        var now = Date.now();
        var idle = now - this.lastWheelAt > this.wheelIdleMs;
        if (idle) {
          if (!this.coastStartedAt) {
            this.coastStartedAt = this.lastWheelAt + this.wheelIdleMs;
          }
          if (now - this.coastStartedAt >= this.tailMs - FLOW_FRAME_MS) {
            this.current = this.target;
          } else {
            this.current += diff * this.settleLerp;
          }
        } else {
          this.coastStartedAt = 0;
          this.current += diff * this.lerp;
        }
        global.scrollTo(0, this.current);
        if (
          global.ScrollTrigger &&
          typeof global.ScrollTrigger.update === "function"
        ) {
          global.ScrollTrigger.update();
        }
      } else if (Math.abs(diff) > 0.01) {
        this.current = this.target;
        global.scrollTo(0, this.current);
        if (
          global.ScrollTrigger &&
          typeof global.ScrollTrigger.update === "function"
        ) {
          global.ScrollTrigger.update();
        }
      }
    }
    this.rafId = global.requestAnimationFrame(this.loop);
  };

  FlowScroll.prototype.start = function () {
    this.syncFromViewport();
    global.addEventListener("wheel", this.onWheel, { passive: false });
    global.addEventListener("scroll", this.onScroll, { passive: true });
    this.rafId = global.requestAnimationFrame(this.loop);
    document.documentElement.classList.add("lenis-flow");
  };

  FlowScroll.prototype.pause = function () {
    this.paused = true;
  };

  FlowScroll.prototype.resume = function () {
    this.paused = false;
    this.syncFromViewport();
  };

  FlowScroll.prototype.scrollTo = function (y) {
    var clamped = clampPair(this.current, resolveScrollTarget(y));
    this.current = clamped.current;
    this.target = clamped.target;
  };

  FlowScroll.prototype.destroy = function () {
    if (this.rafId) {
      global.cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
    global.removeEventListener("wheel", this.onWheel);
    global.removeEventListener("scroll", this.onScroll);
    document.documentElement.classList.remove("lenis-flow");
  };

  global.TravelogueLenis = {
    FLOW_TAIL_MS: FLOW_TAIL_MS,
    FLOW_FRAME_MS: FLOW_FRAME_MS,
    estimateSettleMs: function (delta, options) {
      options = options || {};
      var lerp = typeof options.lerp === "number" ? options.lerp : 0.1;
      var settleLerp =
        typeof options.settleLerp === "number" ? options.settleLerp : 0.28;
      var wheelIdleMs =
        typeof options.wheelIdleMs === "number" ? options.wheelIdleMs : 90;
      var tailMs = typeof options.tailMs === "number" ? options.tailMs : FLOW_TAIL_MS;
      var current = 0;
      var target = Math.abs(delta);
      var t = 0;
      var coastStarted = null;
      while (Math.abs(target - current) > 0.5 && t < 2000) {
        if (t > wheelIdleMs) {
          if (coastStarted === null) coastStarted = wheelIdleMs;
          if (t - coastStarted >= tailMs - FLOW_FRAME_MS) {
            current = target;
            return Math.max(0, t - coastStarted);
          } else {
            current += (target - current) * settleLerp;
          }
        } else {
          coastStarted = null;
          current += (target - current) * lerp;
        }
        t += FLOW_FRAME_MS;
      }
      return coastStarted === null ? 0 : Math.max(0, t - coastStarted);
    },
    init: function (options) {
      if (instance) {
        instance.destroy();
      }
      instance = new FlowScroll(options || {});
      instance.start();
      return instance;
    },
    pause: function () {
      if (instance) instance.pause();
    },
    resume: function () {
      if (instance) instance.resume();
    },
    scrollTo: function (y) {
      if (instance) instance.scrollTo(y);
    },
    destroy: function () {
      if (instance) {
        instance.destroy();
        instance = null;
      }
    },
  };
})(window);
