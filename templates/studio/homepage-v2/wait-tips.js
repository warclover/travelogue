// @ts-nocheck
/**
 * Wait Tips V1 · Importing 壳内可关闭教育轮播（W0+W1）
 * 铁律：次于进度主句；不写 Help seen；失败静默。
 */
import { trackStudioEvent } from "../js/analytics.js";
import {
  COPY_VERSION,
  DISMISS_KEY,
  VERSION_KEY,
  WAIT_TIPS_CARDS,
} from "./wait-tips-copy.js";

var SHOW_DELAY_MS = 2000;
var FIRST_DWELL_MS = 12000;
var DWELL_MS = 10000;

var _root = null;
var _timer = null;
var _showTimer = null;
var _index = 0;
var _paused = false;
var _pauseReasons = Object.create(null);
var _mountedAt = 0;
var _viewed = Object.create(null);
var _jobStage = null;
var _importStartedAt = 0;
var _suppressAdvance = false;
var _alive = false;
var _firstDwellDone = false;

function _lsGet(key) {
  try {
    return localStorage.getItem(key);
  } catch (_e) {
    return null;
  }
}

function _lsSet(key, value) {
  try {
    localStorage.setItem(key, value);
    return true;
  } catch (_e) {
    return false;
  }
}

export function isWaitTipsDismissed() {
  return _lsGet(DISMISS_KEY) === "1";
}

export function clearWaitTipsDismissed() {
  try {
    localStorage.removeItem(DISMISS_KEY);
  } catch (_e) {
    /* ignore */
  }
}

function prefersReducedMotion() {
  try {
    return (
      typeof matchMedia === "function" &&
      matchMedia("(prefers-reduced-motion: reduce)").matches
    );
  } catch (_e) {
    return false;
  }
}

function clearAdvanceTimer() {
  if (_timer) {
    clearTimeout(_timer);
    _timer = null;
  }
}

function clearShowTimer() {
  if (_showTimer) {
    clearTimeout(_showTimer);
    _showTimer = null;
  }
}

function markViewed(id) {
  if (id) _viewed[id] = true;
}

function viewedCount() {
  return Object.keys(_viewed).filter(function (k) {
    return k.indexOf("WT-") === 0;
  }).length;
}

function currentCard() {
  return WAIT_TIPS_CARDS[_index] || WAIT_TIPS_CARDS[0];
}

function renderCard() {
  if (!_root) return;
  var card = currentCard();
  markViewed(card.id);
  var label = _root.querySelector(".v2-wait-tips__label");
  var title = _root.querySelector(".v2-wait-tips__title");
  var body = _root.querySelector(".v2-wait-tips__body");
  if (label) {
    label.textContent = card.label;
    label.setAttribute("data-tone", card.tone);
  }
  if (title) title.textContent = card.title;
  if (body) body.textContent = card.body;
  var dots = _root.querySelectorAll(".v2-wait-tips__dot");
  for (var i = 0; i < dots.length; i++) {
    dots[i].classList.toggle("is-active", i === _index);
    dots[i].setAttribute("aria-current", i === _index ? "true" : "false");
  }
}

function scheduleAdvance() {
  clearAdvanceTimer();
  if (!_alive || !_root || _paused || _suppressAdvance || prefersReducedMotion()) {
    return;
  }
  var dwell = !_firstDwellDone ? FIRST_DWELL_MS : DWELL_MS;
  _firstDwellDone = true;
  _timer = setTimeout(function () {
    if (!_alive || _paused || _suppressAdvance) return;
    var from = currentCard().id;
    goTo((_index + 1) % WAIT_TIPS_CARDS.length, "auto");
    trackStudioEvent("wait_tips_auto_advance", {
      from_id: from,
      to_id: currentCard().id,
    });
  }, dwell);
}

function goTo(nextIndex, via) {
  if (!_root || !WAIT_TIPS_CARDS.length) return;
  var from = currentCard().id;
  var n = WAIT_TIPS_CARDS.length;
  var prevIdx = _index;
  _index = ((nextIndex % n) + n) % n;
  renderCard();
  if (via === "manual" || via === "dot") {
    var dir = "dot";
    if (via === "manual") {
      dir = (_index - prevIdx + n) % n === 1 ? "next" : "prev";
    }
    trackStudioEvent("wait_tips_manual_nav", {
      from_id: from,
      to_id: currentCard().id,
      dir: dir,
    });
  }
  scheduleAdvance();
}

function setPaused(reason, on) {
  if (on) _pauseReasons[reason] = true;
  else delete _pauseReasons[reason];
  var was = _paused;
  _paused = Object.keys(_pauseReasons).length > 0;
  if (_paused && !was) {
    clearAdvanceTimer();
    trackStudioEvent("wait_tips_pause", {
      card_id: currentCard().id,
      reason: reason,
    });
  } else if (!_paused && was) {
    scheduleAdvance();
  }
}

function buildDom() {
  var root = document.createElement("div");
  root.className = "v2-wait-tips";
  root.id = "v2-wait-tips";
  root.setAttribute("role", "region");
  root.setAttribute("aria-roledescription", "轮播");
  root.setAttribute("aria-label", "等待时小提示");
  root.hidden = true;

  var head = document.createElement("div");
  head.className = "v2-wait-tips__head";
  var label = document.createElement("span");
  label.className = "v2-wait-tips__label";
  label.setAttribute("data-tone", "outcome");
  var close = document.createElement("button");
  close.type = "button";
  close.className = "v2-wait-tips__close";
  close.setAttribute("aria-label", "关闭提示");
  close.textContent = "×";
  head.appendChild(label);
  head.appendChild(close);

  var title = document.createElement("p");
  title.className = "v2-wait-tips__title";
  title.id = "v2-wait-tips-title";
  title.setAttribute("aria-live", "polite");

  var body = document.createElement("p");
  body.className = "v2-wait-tips__body";

  var nav = document.createElement("div");
  nav.className = "v2-wait-tips__nav";
  var prev = document.createElement("button");
  prev.type = "button";
  prev.className = "v2-wait-tips__nav-btn";
  prev.setAttribute("aria-label", "上一张");
  prev.textContent = "‹";
  var dots = document.createElement("div");
  dots.className = "v2-wait-tips__dots";
  dots.setAttribute("role", "tablist");
  dots.setAttribute("aria-label", "提示页码");
  for (var i = 0; i < WAIT_TIPS_CARDS.length; i++) {
    (function (idx) {
      var d = document.createElement("button");
      d.type = "button";
      d.className = "v2-wait-tips__dot";
      d.setAttribute("role", "tab");
      d.setAttribute("aria-label", "第 " + (idx + 1) + " 张");
      d.addEventListener("click", function () {
        goTo(idx, "dot");
      });
      dots.appendChild(d);
    })(i);
  }
  var next = document.createElement("button");
  next.type = "button";
  next.className = "v2-wait-tips__nav-btn";
  next.setAttribute("aria-label", "下一张");
  next.textContent = "›";
  nav.appendChild(prev);
  nav.appendChild(dots);
  nav.appendChild(next);

  root.appendChild(head);
  root.appendChild(title);
  root.appendChild(body);
  root.appendChild(nav);

  close.addEventListener("click", function () {
    dismissWaitTips();
  });
  prev.addEventListener("click", function () {
    goTo(_index - 1, "manual");
  });
  next.addEventListener("click", function () {
    goTo(_index + 1, "manual");
  });

  root.addEventListener("mouseenter", function () {
    setPaused("hover", true);
  });
  root.addEventListener("mouseleave", function () {
    setPaused("hover", false);
  });
  root.addEventListener("focusin", function () {
    setPaused("focus", true);
  });
  root.addEventListener("focusout", function (ev) {
    if (root.contains(ev.relatedTarget)) return;
    setPaused("focus", false);
  });

  return root;
}

/**
 * @param {HTMLElement} panel · .v2-import-panel
 * @param {{ importStartedAt?: number, beforeEl?: HTMLElement|null, force?: boolean }} opts
 *   force：忽略/清除 dismiss，立即显现（帮助「重播」或面板内恢复入口）
 */
export function scheduleWaitTips(panel, opts) {
  try {
    unmountWaitTips();
    opts = opts || {};
    var force = opts.force === true;
    if (force) clearWaitTipsDismissed();
    if (!panel || (!force && isWaitTipsDismissed())) return;
    removeWaitTipsRestoreChip(panel);
    _importStartedAt = opts.importStartedAt || Date.now();
    _alive = true;
    _index = 0;
    _paused = false;
    _pauseReasons = Object.create(null);
    _viewed = Object.create(null);
    _suppressAdvance = false;
    _jobStage = null;
    _firstDwellDone = false;

    var root = buildDom();
    _root = root;
    var before = opts.beforeEl;
    if (before && before.parentNode === panel) {
      panel.insertBefore(root, before);
    } else {
      panel.appendChild(root);
    }

    var elapsed = Date.now() - _importStartedAt;
    var delay = force ? 0 : Math.max(0, SHOW_DELAY_MS - elapsed);
    clearShowTimer();
    _showTimer = setTimeout(function () {
      _showTimer = null;
      if (!_alive || !_root) return;
      if (!force && isWaitTipsDismissed()) return;
      _root.hidden = false;
      _mountedAt = Date.now();
      renderCard();
      trackStudioEvent("wait_tips_show", {
        card_id: currentCard().id,
        job_stage: _jobStage,
        elapsed_ms: Date.now() - _importStartedAt,
        copy_version: COPY_VERSION,
        force: force || undefined,
      });
      scheduleAdvance();
    }, delay);
  } catch (_e) {
    try {
      unmountWaitTips();
    } catch (_e2) {
      /* ignore */
    }
  }
}

/** 已 dismiss 时在进度壳提供恢复入口（长等待仍可看功能介绍/技巧） */
export function mountWaitTipsRestoreChip(panel, beforeEl) {
  try {
    if (!panel || !isWaitTipsDismissed()) return;
    if (panel.querySelector("[data-wait-tips-restore]")) return;
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "v2-wait-tips-restore";
    btn.setAttribute("data-wait-tips-restore", "1");
    btn.textContent = "查看功能介绍与使用技巧";
    btn.addEventListener("click", function () {
      scheduleWaitTips(panel, {
        importStartedAt: _importStartedAt || Date.now() - SHOW_DELAY_MS,
        beforeEl: beforeEl,
        force: true,
      });
    });
    if (beforeEl && beforeEl.parentNode === panel) {
      panel.insertBefore(btn, beforeEl);
    } else {
      panel.appendChild(btn);
    }
  } catch (_e) {
    /* ignore */
  }
}

export function removeWaitTipsRestoreChip(panel) {
  if (!panel) return;
  var chip = panel.querySelector("[data-wait-tips-restore]");
  if (chip && chip.parentNode) chip.parentNode.removeChild(chip);
}

/** 帮助抽屉「重播等待提示」：若正在 Importing，当场重新挂上 Tips */
export function remountWaitTipsIfImporting() {
  try {
    var host = document.getElementById("v2-importing");
    var panel = host && !host.hidden ? host.querySelector(".v2-import-panel") : null;
    var cancel = document.getElementById("v2-import-cancel");
    if (!panel) return false;
    scheduleWaitTips(panel, {
      importStartedAt: _importStartedAt || Date.now() - SHOW_DELAY_MS,
      beforeEl: cancel,
      force: true,
    });
    return !!document.getElementById("v2-wait-tips");
  } catch (_e) {
    return false;
  }
}

export function unmountWaitTips() {
  clearAdvanceTimer();
  clearShowTimer();
  _alive = false;
  _paused = false;
  _pauseReasons = Object.create(null);
  if (_root && _root.parentNode) {
    try {
      _root.parentNode.removeChild(_root);
    } catch (_e) {
      /* ignore */
    }
  }
  _root = null;
}

export function pauseWaitTips(reason) {
  if (!_alive) return;
  setPaused(reason || "external", true);
}

export function resumeWaitTips(reason) {
  if (!_alive) return;
  setPaused(reason || "external", false);
}

export function dismissWaitTips() {
  if (!_root && !_alive) return;
  var card = currentCard();
  trackStudioEvent("wait_tips_dismiss", {
    card_id: card ? card.id : null,
    viewed_count: viewedCount(),
    elapsed_ms: _mountedAt ? Date.now() - _mountedAt : 0,
  });
  _lsSet(DISMISS_KEY, "1");
  _lsSet(VERSION_KEY, COPY_VERSION);
  unmountWaitTips();
}

/**
 * W1 · D-WT-07：短尾或末段不再 auto-advance
 * @param {{ stage?: string, stageIndex?: number, stageCount?: number, status?: string }} job
 */
export function notifyWaitTipsJob(job) {
  if (!_alive || !job) return;
  _jobStage = job.stage || null;
  if (job.status && job.status !== "running" && job.status !== "queued") {
    unmountWaitTips();
    return;
  }
  var idx = typeof job.stageIndex === "number" ? job.stageIndex : 0;
  var count = typeof job.stageCount === "number" ? job.stageCount : 0;
  var stage = String(job.stage || "").toLowerCase();
  var late =
    stage.indexOf("render") !== -1 ||
    stage.indexOf("export") !== -1 ||
    (count > 0 && idx >= count - 1);
  var elapsed = _importStartedAt ? Date.now() - _importStartedAt : 0;
  // 启发式：已跑较久且末段，或可见剩余偏短 → 抑制切下一张
  var shortTail = late && elapsed > 20000;
  if (!shortTail && late && count > 0) {
    shortTail = true;
  }
  if (shortTail && !_suppressAdvance) {
    _suppressAdvance = true;
    clearAdvanceTimer();
    trackStudioEvent("wait_tips_suppress_short_wait", {
      job_stage: _jobStage,
    });
  }
}

/** 测试钩子 */
export function _waitTipsTestApi() {
  return {
    DISMISS_KEY: DISMISS_KEY,
    COPY_VERSION: COPY_VERSION,
    cards: WAIT_TIPS_CARDS,
    isAlive: function () {
      return _alive;
    },
    getIndex: function () {
      return _index;
    },
  };
}
