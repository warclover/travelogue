/**
 * L0 Hardening W2 · 首页轻状态条（T-CAP-06）
 * 未配置写作引擎时提示：基础能力可用；升级可选。
 * 与能力卡不同帧（D-DLLM-13 / D-L0G-06）。
 */
"use strict";

import { trackStudioEvent } from "./analytics.js";
import {
  isCapabilityCardSeen,
  isHomeStubBannerDismissed,
  markHomeStubBannerDismissed,
} from "./help-onboarding.js";
import { openLlmSettings } from "./llm-settings.js";
import { isCapabilityCardVisible } from "./capability-card.js";
import { V2 } from "../homepage-v2/store.js";

var ROOT_ID = "studio-home-stub-banner";
var _visible = false;
var _llmAvailable = null;
var _wired = false;

function ensureRoot() {
  var el = document.getElementById(ROOT_ID);
  if (el) return el;
  el = document.createElement("div");
  el.id = ROOT_ID;
  el.className = "studio-home-stub-banner";
  el.hidden = true;
  el.setAttribute("role", "status");
  el.innerHTML =
    '<div class="studio-home-stub-banner__inner">' +
    '<span class="studio-home-stub-banner__badge">本机文案</span>' +
    '<span class="studio-home-stub-banner__text">不配置 API 也可正常使用。</span>' +
    '<button type="button" class="studio-home-stub-banner__link" id="studio-home-stub-upgrade">升级 AI 文案 →</button>' +
    '<button type="button" class="studio-home-stub-banner__dismiss" id="studio-home-stub-dismiss" aria-label="关闭">×</button>' +
    "</div>";
  if (!document.getElementById("studio-home-stub-banner-style")) {
    var style = document.createElement("style");
    style.id = "studio-home-stub-banner-style";
    style.textContent =
      ".studio-home-stub-banner{margin:0 0 12px;width:100%;max-width:min(520px,92vw);}" +
      ".studio-home-stub-banner[hidden]{display:none!important;}" +
      ".studio-home-stub-banner__inner{display:flex;flex-wrap:wrap;align-items:center;gap:8px 12px;" +
      "padding:10px 12px;border-radius:10px;border:1px solid rgba(47,107,85,.28);" +
      "background:rgba(47,107,85,.08);color:var(--v2-ink,#1a2420);font-size:13px;line-height:1.4;}" +
      ".studio-home-stub-banner__badge{font-size:11px;font-weight:650;letter-spacing:.04em;" +
      "padding:2px 7px;border-radius:999px;background:rgba(47,107,85,.16);color:#2f6b55;}" +
      ".studio-home-stub-banner__text{flex:1 1 140px;color:inherit;opacity:.88;}" +
      ".studio-home-stub-banner__link{border:0;background:transparent;padding:0;color:#2f6b55;" +
      "font-size:13px;font-weight:600;cursor:pointer;text-decoration:underline;text-underline-offset:3px;}" +
      ".studio-home-stub-banner__dismiss{margin-left:auto;border:0;background:transparent;" +
      "font-size:18px;line-height:1;cursor:pointer;color:inherit;opacity:.45;padding:0 2px;}" +
      ".studio-home-stub-banner__dismiss:hover{opacity:.8;}";
    document.head.appendChild(style);
  }
  var cta = document.getElementById("v2-cta");
  if (cta && cta.parentNode) {
    cta.parentNode.insertBefore(el, cta);
  } else {
    document.body.appendChild(el);
  }
  return el;
}

function wireOnce() {
  if (_wired) return;
  _wired = true;
  var el = ensureRoot();
  var upgrade = el.querySelector("#studio-home-stub-upgrade");
  if (upgrade) {
    upgrade.addEventListener("click", function () {
      trackStudioEvent("home_stub_banner_click", { action: "upgrade" });
      openLlmSettings({
        source: "home_banner",
        onChange: function (st) {
          if (st && typeof st.llmAvailable === "boolean") {
            _llmAvailable = !!st.llmAvailable;
            syncHomeStubBanner();
          } else {
            refreshLlmAndSync();
          }
        },
      });
    });
  }
  var dismiss = el.querySelector("#studio-home-stub-dismiss");
  if (dismiss) {
    dismiss.addEventListener("click", function () {
      markHomeStubBannerDismissed();
      trackStudioEvent("home_stub_banner_click", { action: "dismiss" });
      hideBanner();
    });
  }
  window.addEventListener("travelogue:capability-card-done", function () {
    window.setTimeout(function () {
      syncHomeStubBanner();
    }, 200);
  });
  window.addEventListener("travelogue:llm-status", function (ev) {
    var d = ev && ev.detail;
    if (d && typeof d.llmAvailable === "boolean") {
      _llmAvailable = !!d.llmAvailable;
      syncHomeStubBanner();
    } else {
      refreshLlmAndSync();
    }
  });
}

function hideBanner() {
  var el = document.getElementById(ROOT_ID);
  if (el) el.hidden = true;
  _visible = false;
}

function canShow() {
  if (_llmAvailable === true) return false;
  if (_llmAvailable === null) return false;
  if (isHomeStubBannerDismissed()) return false;
  if (isCapabilityCardVisible()) return false;
  // 能力卡尚未看过：等卡结束后再出（避免同帧抢注意力）
  if (!isCapabilityCardSeen()) return false;
  if (V2 && (V2.state === "Importing" || V2.state === "FirstSuccess" || V2.state === "Loading")) {
    return false;
  }
  if (typeof document !== "undefined") {
    var fail = document.getElementById("v2-failure");
    if (fail && !fail.hidden) return false;
    var fs = document.getElementById("v2-first-success");
    if (fs && !fs.hidden) return false;
  }
  return true;
}

export function syncHomeStubBanner() {
  wireOnce();
  if (!canShow()) {
    hideBanner();
    return false;
  }
  var el = ensureRoot();
  el.hidden = false;
  if (!_visible) {
    _visible = true;
    trackStudioEvent("home_stub_banner_show", {});
  }
  return true;
}

function refreshLlmAndSync() {
  fetch("/__travelogue/llm/status")
    .then(function (r) {
      return r.ok ? r.json() : null;
    })
    .then(function (st) {
      _llmAvailable = !!(st && st.llmAvailable);
      syncHomeStubBanner();
    })
    .catch(function () {
      _llmAvailable = false;
      syncHomeStubBanner();
    });
}

/**
 * 首页 idle 后评估（能力卡之后）。
 */
export function maybeShowHomeStubBanner(opts) {
  opts = opts || {};
  wireOnce();
  var delay = typeof opts.delayMs === "number" ? opts.delayMs : 700;
  window.setTimeout(function () {
    refreshLlmAndSync();
  }, delay);
}

export function isHomeStubBannerVisible() {
  return _visible;
}
