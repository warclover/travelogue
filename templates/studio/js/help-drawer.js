/**
 * 帮助抽屉 L2（W2）· 首页与预览共用。
 * 固定 H1–H7；重播；深链 ?help=H2 / #help=H2。
 */
"use strict";

import {
  HELP_COPY,
  getHelpItem,
  replayHelpHints,
  trackHelpEvent,
  hasRefineSaveSeen,
  markRefineSaveSeen,
} from "./help-onboarding.js";

var FOCUSABLE =
  'a[href],button:not([disabled]),input:not([disabled]),textarea:not([disabled]),select:not([disabled]),[tabindex="0"]';

var _root = null;
var _panel = null;
var _scrim = null;
var _openBtn = null;
var _focusRelease = null;
var _previousFocus = null;
var _escHandler = null;
var _opts = {};
var _replayNoteEl = null;

function _trapFocus(container) {
  function onKeydown(e) {
    if (e.key !== "Tab") return;
    var items = container.querySelectorAll(FOCUSABLE);
    if (!items.length) return;
    var first = items[0];
    var last = items[items.length - 1];
    if (e.shiftKey) {
      if (document.activeElement === first) {
        e.preventDefault();
        last.focus();
      }
    } else if (document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }
  container.addEventListener("keydown", onKeydown);
  return function () {
    container.removeEventListener("keydown", onKeydown);
  };
}

function _ensureDom() {
  if (_root) return;
  _root = document.createElement("div");
  _root.id = "studio-help-drawer-root";
  _root.className = "studio-help-drawer-root";
  _root.hidden = true;

  _scrim = document.createElement("div");
  _scrim.className = "studio-help-drawer__scrim";
  _scrim.setAttribute("aria-hidden", "true");

  _panel = document.createElement("aside");
  _panel.className = "studio-help-drawer";
  _panel.setAttribute("role", "dialog");
  _panel.setAttribute("aria-modal", "true");
  _panel.setAttribute("aria-labelledby", "studio-help-drawer-title");

  var head = document.createElement("div");
  head.className = "studio-help-drawer__head";
  var title = document.createElement("h2");
  title.id = "studio-help-drawer-title";
  title.className = "studio-help-drawer__title";
  title.textContent = HELP_COPY.helpTitle;
  var closeBtn = document.createElement("button");
  closeBtn.type = "button";
  closeBtn.className = "studio-help-drawer__close";
  closeBtn.setAttribute("aria-label", "关闭");
  closeBtn.textContent = "×";
  head.appendChild(title);
  head.appendChild(closeBtn);

  var body = document.createElement("div");
  body.className = "studio-help-drawer__body";
  body.id = "studio-help-drawer-body";

  (HELP_COPY.helpItems || []).forEach(function (item) {
    var details = document.createElement("details");
    details.className = "studio-help-drawer__item";
    details.id = "studio-help-item-" + item.id;
    details.setAttribute("data-help-item", item.id);
    var summary = document.createElement("summary");
    summary.textContent = item.id + " · " + item.title;
    var list = document.createElement("ul");
    list.className = "studio-help-drawer__points";
    (item.body || []).forEach(function (line) {
      var li = document.createElement("li");
      li.textContent = line;
      list.appendChild(li);
    });
    details.appendChild(summary);
    details.appendChild(list);
    details.addEventListener("toggle", function () {
      if (details.open) {
        trackHelpEvent("help_drawer_item", { itemId: item.id });
      }
    });
    body.appendChild(details);
  });

  var replay = document.createElement("div");
  replay.className = "studio-help-drawer__replay";
  var replayBtn = document.createElement("button");
  replayBtn.type = "button";
  replayBtn.className = "studio-help-drawer__replay-btn";
  replayBtn.textContent = HELP_COPY.replayButton;
  _replayNoteEl = document.createElement("p");
  _replayNoteEl.className = "studio-help-drawer__replay-note";
  _replayNoteEl.hidden = true;
  replay.appendChild(replayBtn);
  replay.appendChild(_replayNoteEl);
  body.appendChild(replay);

  _panel.appendChild(head);
  _panel.appendChild(body);
  _root.appendChild(_scrim);
  _root.appendChild(_panel);
  document.body.appendChild(_root);

  closeBtn.addEventListener("click", function () {
    closeHelpDrawer();
  });
  _scrim.addEventListener("click", function () {
    closeHelpDrawer();
  });
  replayBtn.addEventListener("click", function () {
    var msg = replayHelpHints();
    _replayNoteEl.textContent = msg;
    _replayNoteEl.hidden = false;
    if (typeof _opts.onReplay === "function") {
      _opts.onReplay(msg);
    }
    window.setTimeout(function () {
      closeHelpDrawer();
      if (typeof _opts.showToast === "function") {
        _opts.showToast(msg, { duration: 5200 });
      } else if (typeof studioToast === "function") {
        studioToast(msg, { duration: 5200 });
      }
    }, 600);
  });
}

function _highlightItem(itemId) {
  var id = String(itemId || "").toUpperCase();
  if (!id || !getHelpItem(id)) return;
  var items = _panel.querySelectorAll(".studio-help-drawer__item");
  items.forEach(function (el) {
    var match = el.getAttribute("data-help-item") === id;
    el.open = match;
    el.classList.toggle("is-active", match);
    if (match) {
      try {
        el.scrollIntoView({ block: "nearest", behavior: "smooth" });
      } catch (_e) {
        el.scrollIntoView(true);
      }
    }
  });
}

function _readDeepLink() {
  try {
    var q = new URLSearchParams(window.location.search || "");
    var fromQ = q.get("help");
    if (fromQ) return String(fromQ).toUpperCase();
    var hash = String(window.location.hash || "");
    var m = hash.match(/help=([Hh]\d)/);
    if (m) return m[1].toUpperCase();
  } catch (_e) {
    /* ignore */
  }
  return null;
}

/**
 * @param {{
 *   getOpenButton?: () => HTMLElement|null,
 *   beforeOpen?: (done: (ok?: boolean) => void) => void,
 *   canOpenRefineSheet?: () => boolean,
 *   onOpen?: () => void,
 *   onClose?: () => void,
 *   onReplay?: (msg: string) => void,
 *   showToast?: (msg: string, opts?: object) => void,
 * }} [opts]
 */
export function configureHelpDrawer(opts) {
  _opts = opts || {};
}

export function isHelpDrawerOpen() {
  return !!(_root && !_root.hidden);
}

export function closeHelpDrawer() {
  if (!_root || _root.hidden) return;
  if (_escHandler) {
    document.removeEventListener("keydown", _escHandler, true);
    _escHandler = null;
  }
  if (_focusRelease) {
    _focusRelease();
    _focusRelease = null;
  }
  _root.hidden = true;
  _root.classList.remove("is-open");
  document.body.classList.remove("studio-help-open");
  if (_openBtn) {
    _openBtn.setAttribute("aria-expanded", "false");
  }
  if (_previousFocus && typeof _previousFocus.focus === "function") {
    try {
      _previousFocus.focus();
    } catch (_e) {
      /* ignore */
    }
  } else if (_openBtn && typeof _openBtn.focus === "function") {
    _openBtn.focus();
  }
  _previousFocus = null;
  if (typeof _opts.onClose === "function") _opts.onClose();
}

/**
 * @param {{ source?: string, itemId?: string }} [openOpts]
 */
export function openHelpDrawer(openOpts) {
  openOpts = openOpts || {};
  _ensureDom();
  if (_replayNoteEl) {
    _replayNoteEl.hidden = true;
    _replayNoteEl.textContent = "";
  }

  function doOpen() {
    _previousFocus = document.activeElement;
    _openBtn =
      (typeof _opts.getOpenButton === "function" && _opts.getOpenButton()) ||
      document.getElementById("studio-help-open") ||
      document.querySelector("[data-help-open]");
    _root.hidden = false;
    requestAnimationFrame(function () {
      _root.classList.add("is-open");
    });
    document.body.classList.add("studio-help-open");
    if (_openBtn) _openBtn.setAttribute("aria-expanded", "true");
    if (_focusRelease) _focusRelease();
    _focusRelease = _trapFocus(_panel);
    _escHandler = function (e) {
      if (e.key !== "Escape") return;
      e.preventDefault();
      e.stopPropagation();
      closeHelpDrawer();
    };
    document.addEventListener("keydown", _escHandler, true);
    var closeBtn = _panel.querySelector(".studio-help-drawer__close");
    if (closeBtn) closeBtn.focus();
    var itemId = openOpts.itemId || _readDeepLink();
    if (itemId) _highlightItem(itemId);
    trackHelpEvent("help_drawer_open", {
      source: openOpts.source || "icon",
      itemId: itemId || null,
    });
    if (typeof _opts.onOpen === "function") _opts.onOpen();
  }

  if (typeof _opts.beforeOpen === "function") {
    _opts.beforeOpen(function (ok) {
      if (ok === false) return;
      doOpen();
    });
  } else {
    doOpen();
  }
}

/**
 * 创建幽灵「?」按钮。
 * @param {{ className?: string, id?: string }} [btnOpts]
 */
export function createHelpOpenButton(btnOpts) {
  btnOpts = btnOpts || {};
  var btn = document.createElement("button");
  btn.type = "button";
  btn.id = btnOpts.id || "studio-help-open";
  btn.className =
    btnOpts.className || "studio-help-open studio-help-open--ghost";
  btn.setAttribute("aria-label", HELP_COPY.helpAria);
  btn.setAttribute("aria-haspopup", "dialog");
  btn.setAttribute("aria-expanded", "false");
  btn.setAttribute("aria-controls", "studio-help-drawer-root");
  btn.title = HELP_COPY.helpAria;
  btn.textContent = "?";
  btn.setAttribute("data-help-open", "1");
  btn.addEventListener("click", function (e) {
    e.preventDefault();
    e.stopPropagation();
    if (isHelpDrawerOpen()) {
      closeHelpDrawer();
      return;
    }
    openHelpDrawer({ source: "icon" });
  });
  return btn;
}

/** 首次打开精修 Sheet 顶 hint（T-REFINE-SAVE）。 */
export function maybeInjectRefineSaveHint(bodyEl) {
  if (!bodyEl || hasRefineSaveHintIn(bodyEl)) return false;
  if (hasRefineSaveSeen()) return false;

  var box = document.createElement("div");
  box.className = "preview-sheet__help-hint";
  box.setAttribute("role", "status");
  box.setAttribute("data-help-refine-save", "1");

  var line1 = document.createElement("p");
  line1.textContent = HELP_COPY.refineSaveLines[0];
  var line2 = document.createElement("p");
  line2.textContent = HELP_COPY.refineSaveLines[1];

  var actions = document.createElement("div");
  actions.className = "preview-sheet__help-hint-actions";
  var more = document.createElement("button");
  more.type = "button";
  more.className = "preview-sheet__help-hint-more";
  more.textContent = HELP_COPY.refineSaveMore;
  var dismiss = document.createElement("button");
  dismiss.type = "button";
  dismiss.className = "preview-sheet__help-hint-dismiss";
  dismiss.textContent = "知道了";

  actions.appendChild(more);
  actions.appendChild(dismiss);
  box.appendChild(line1);
  box.appendChild(line2);
  box.appendChild(actions);

  bodyEl.insertBefore(box, bodyEl.firstChild);
  markRefineSaveSeen();
  trackHelpEvent("help_coach_show", { touchpoint: "T-REFINE-SAVE" });

  more.addEventListener("click", function () {
    openHelpDrawer({ source: "deep_link", itemId: "H2" });
  });
  dismiss.addEventListener("click", function () {
    if (box.parentNode) box.parentNode.removeChild(box);
    trackHelpEvent("help_coach_dismiss", {
      touchpoint: "T-REFINE-SAVE",
      reason: "got_it",
    });
  });
  return true;
}

function hasRefineSaveHintIn(bodyEl) {
  return !!(bodyEl && bodyEl.querySelector("[data-help-refine-save]"));
}

/** 启动时若 URL 含 help= 深链则打开 */
export function maybeOpenHelpFromDeepLink() {
  var id = _readDeepLink();
  if (!id) return;
  window.setTimeout(function () {
    openHelpDrawer({ source: "deep_link", itemId: id });
  }, 200);
}
