/**
 * L0 Hardening W2 · 首页轻状态条（T-CAP-06）
 * NAS：默认可达面永不展示（D-NAS-20）。
 */
"use strict";

import { trackStudioEvent } from "./analytics.js";
import {
  isCapabilityCardSeen,
  isHomeStubBannerDismissed,
  markHomeStubBannerDismissed,
} from "./help-onboarding.js";
import { isCapabilityCardVisible } from "./capability-card.js";
import { isAiSurfaceEnabled } from "./ai-surface.js";
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
  // NAS：DOM 保留中性占位；升级条永不展示（D-NAS-20）
  el.innerHTML =
    '<div class="studio-home-stub-banner__inner">' +
    '<span class="studio-home-stub-banner__badge">本机</span>' +
    '<span class="studio-home-stub-banner__text">选夹即可导入、预览与导出长图。</span>' +
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
  // NAS · FE-NAS-02 / D-NAS-20：stub banner 默认关闭（dark 亦不恢复）
  if (!isAiSurfaceEnabled()) {
    hideBanner();
    return false;
  }
  // 产品决议：升级条永久关闭；保留函数供测试
  hideBanner();
  return false;
}

function refreshLlmAndSync() {
  // NAS · S3：默认面不拉 /llm/status
  if (!isAiSurfaceEnabled()) {
    hideBanner();
    return;
  }
  hideBanner();
}

/**
 * 首页 idle 后评估（能力卡之后）。
 */
export function maybeShowHomeStubBanner(_opts) {
  hideBanner();
}

export function isHomeStubBannerVisible() {
  return _visible;
}
