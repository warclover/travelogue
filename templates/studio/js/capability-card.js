/**
 * Desktop LLM Setup V1 · W2 首启能力卡（T-CAP-01 · MF-01 · D-DLLM-13）
 */
"use strict";

import { trackStudioEvent } from "./analytics.js";
import { SHEET_FOCUSABLE } from "./constants.js";
import {
  isHelpL1Blocked,
  markCapabilityCardSeen,
  isCapabilityCardSeen,
  markCapabilityCardSuppressHelpL1,
  isCapabilityCardSuppressingHelpL1,
} from "./help-onboarding.js";
import { openLlmSettings } from "./llm-settings.js";
import { V2 } from "../homepage-v2/store.js";

var ROOT_ID = "studio-capability-card-root";
var _visible = false;
var _scheduled = false;
var _trapHandler = null;

function focusableEls(container) {
  return Array.prototype.slice
    .call(container.querySelectorAll(SHEET_FOCUSABLE))
    .filter(function (el) {
      return !el.hidden && (el.offsetParent !== null || el === document.activeElement);
    });
}

function trapFocus(dialog) {
  releaseTrap(dialog);
  _trapHandler = function (e) {
    if (e.key !== "Tab") return;
    var els = focusableEls(dialog);
    if (!els.length) return;
    var first = els[0];
    var last = els[els.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  };
  dialog.addEventListener("keydown", _trapHandler);
}

function releaseTrap(dialog) {
  if (_trapHandler && dialog) dialog.removeEventListener("keydown", _trapHandler);
  _trapHandler = null;
}

function ensureRoot() {
  var el = document.getElementById(ROOT_ID);
  if (el) return el;
  el = document.createElement("div");
  el.id = ROOT_ID;
  el.className = "studio-capability-card";
  el.hidden = true;
  el.setAttribute("role", "dialog");
  el.setAttribute("aria-modal", "true");
  el.setAttribute("aria-labelledby", "studio-capability-card-title");
  el.innerHTML =
    '<div class="studio-capability-card__scrim" data-cap-dismiss="1"></div>' +
    '<div class="studio-capability-card__panel">' +
    '<button type="button" class="studio-capability-card__close" data-cap-dismiss="1" aria-label="关闭">×</button>' +
    '<p id="studio-capability-card-title" class="studio-capability-card__title">照片留在本机，也能做成可发的游记</p>' +
    '<p class="studio-capability-card__body">选一次旅行的照片，自动分章、排版；微信长图可直接发群。更好的文案可稍后自行升级（可选）。向导里可一键试用示例。</p>' +
    '<div class="studio-capability-card__actions">' +
    '<button type="button" class="studio-capability-card__primary" id="studio-capability-start">开始制作我的游记</button>' +
    "</div>" +
    '<p class="studio-capability-card__linkrow">' +
    '<button type="button" class="studio-capability-card__link" id="studio-capability-upgrade">以后再升级 AI 文案 →</button>' +
    "</p>" +
    "</div>";
  document.body.appendChild(el);
  /* Styles: capability-card.css via studio-home-v2.css（UI Detail Wave5） */
  el.addEventListener("click", function (ev) {
    var t = ev.target;
    if (t && t.getAttribute && t.getAttribute("data-cap-dismiss")) {
      dismissCapabilityCard("dismiss");
    }
  });
  document.addEventListener("keydown", function (ev) {
    if (_visible && ev.key === "Escape") dismissCapabilityCard("dismiss");
  });
  var start = document.getElementById("studio-capability-start");
  if (start) {
    start.addEventListener("click", function () {
      dismissCapabilityCard("import");
      var cta = document.getElementById("v2-cta");
      if (cta) {
        try {
          cta.focus();
        } catch (_e) {}
        cta.click();
      } else {
        try {
          cta = document.querySelector("[data-v2-import-open], #v2-cta");
          if (cta) cta.click();
        } catch (_e2) {}
      }
    });
  }
  var upgrade = document.getElementById("studio-capability-upgrade");
  if (upgrade) {
    upgrade.addEventListener("click", function () {
      dismissCapabilityCard("configure");
      openLlmSettings({ source: "card" });
    });
  }
  return el;
}

function dismissCapabilityCard(cta) {
  markCapabilityCardSeen();
  markCapabilityCardSuppressHelpL1();
  trackStudioEvent("capability_card_cta", {
    action: cta || "dismiss",
    cta: cta || "dismiss",
  });
  closeCapabilityCard();
  try {
    window.dispatchEvent(new CustomEvent("travelogue:capability-card-done", { detail: { cta: cta } }));
  } catch (_e) {
    /* ignore */
  }
}

export function closeCapabilityCard() {
  var el = document.getElementById(ROOT_ID);
  releaseTrap(el);
  if (el) el.hidden = true;
  _visible = false;
}

export function isCapabilityCardVisible() {
  return _visible;
}

function canShow() {
  if (isCapabilityCardSeen()) return false;
  if (V2 && (V2.state === "Importing" || V2.state === "FirstSuccess" || V2.state === "Loading")) {
    return false;
  }
  // 书架已有作品：不是真·首次，避免遮罩挡主 CTA、背后满书架仍弹卡
  if (V2) {
    if (typeof V2.tripsTotal === "number" && V2.tripsTotal > 0) return false;
    if (Array.isArray(V2.trips) && V2.trips.length > 0) return false;
  }
  if (isHelpL1Blocked()) return false;
  if (typeof document !== "undefined" && document.getElementById("v2-first-success")) {
    var fs = document.getElementById("v2-first-success");
    if (fs && !fs.hidden) return false;
  }
  return true;
}

export function showCapabilityCard() {
  if (!canShow()) return false;
  var el = ensureRoot();
  el.hidden = false;
  _visible = true;
  trapFocus(el);
  // D-DLLM-13：本会话压制非关键自动 Help L1
  markCapabilityCardSuppressHelpL1();
  trackStudioEvent("capability_card_show", {});
  var primary = document.getElementById("studio-capability-start");
  if (primary) {
    try {
      primary.focus();
    } catch (_e) {}
  }
  return true;
}

/**
 * 首页 idle 后评估一次（busy 则延后）。
 */
export function maybeShowCapabilityCard(opts) {
  opts = opts || {};
  if (_scheduled && !opts.force) return;
  if (isCapabilityCardSeen()) return;
  _scheduled = true;
  var delay = typeof opts.delayMs === "number" ? opts.delayMs : 480;
  window.setTimeout(function () {
    if (!canShow()) {
      // busy：idle 后再试一次
      if (isHelpL1Blocked() || (V2 && V2.state === "Importing")) {
        _scheduled = false;
        window.setTimeout(function () {
          maybeShowCapabilityCard({ force: true, delayMs: 600 });
        }, 1200);
      }
      return;
    }
    showCapabilityCard();
  }, delay);
}

/** 供 Help L1 仲裁：能力卡优先或本会话已压制 */
export function shouldDeferHelpL1ForCapabilityCard() {
  return _visible || isCapabilityCardSuppressingHelpL1();
}

// re-export for tests / docs
export { isCapabilityCardSuppressingHelpL1 };
