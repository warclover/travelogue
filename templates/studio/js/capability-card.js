/**
 * Desktop LLM Setup V1 · W2 首启能力卡（T-CAP-01 · MF-01 · D-DLLM-13）
 */
"use strict";

import { trackStudioEvent } from "./analytics.js";
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
    '<p id="studio-capability-card-title" class="studio-capability-card__title">照片留在本机，也能做成杂志游记</p>' +
    '<p class="studio-capability-card__body">选一次旅行的照片，自动分章、排版；微信长图可直接发群。更好的文案可稍后自行升级（可选）。向导里可一键试用示例。</p>' +
    '<div class="studio-capability-card__actions">' +
    '<button type="button" class="studio-capability-card__primary" id="studio-capability-start">开始制作</button>' +
    "</div>" +
    '<p class="studio-capability-card__linkrow">' +
    '<button type="button" class="studio-capability-card__link" id="studio-capability-upgrade">以后再升级 AI 文案 →</button>' +
    "</p>" +
    "</div>";
  document.body.appendChild(el);
  if (!document.getElementById("studio-capability-card-style")) {
    var style = document.createElement("style");
    style.id = "studio-capability-card-style";
    style.textContent =
      ".studio-capability-card{position:fixed;inset:0;z-index:11000;display:flex;align-items:center;justify-content:center;}" +
      ".studio-capability-card[hidden]{display:none!important;}" +
      ".studio-capability-card__scrim{position:absolute;inset:0;background:rgba(20,28,26,.4);}" +
      ".studio-capability-card__panel{position:relative;z-index:1;width:min(400px,92vw);background:#f7f5f0;color:#1a2420;" +
      "border-radius:14px;padding:22px 22px 18px;border:1px solid #c5d0ca;box-sizing:border-box;}" +
      ".studio-capability-card__close{position:absolute;top:10px;right:12px;border:0;background:transparent;" +
      "font-size:22px;line-height:1;cursor:pointer;color:#4a5c55;}" +
      ".studio-capability-card__title{margin:0 28px 8px 0;font-size:17px;font-weight:650;line-height:1.35;}" +
      ".studio-capability-card__body{margin:0;font-size:13px;color:#4a5c55;line-height:1.5;}" +
      ".studio-capability-card__actions{margin-top:16px;}" +
      ".studio-capability-card__primary{border:0;border-radius:10px;padding:10px 16px;font-size:14px;font-weight:600;" +
      "cursor:pointer;background:#2f6b55;color:#fff;}" +
      ".studio-capability-card__linkrow{margin:12px 0 0;}" +
      ".studio-capability-card__link{border:0;background:transparent;padding:0;color:#2f6b55;font-size:13px;cursor:pointer;}";
    document.head.appendChild(style);
  }
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
