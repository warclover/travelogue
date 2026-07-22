/**
 * 首页 v2 · UnsupportedViewport（M20-f · §10.3）+ 视口监听。
 *
 * - 按 viewport-logic 分类；不支持 → 显示壳层提示，隐藏 Bento
 * - D-20：phone 态提供小程序码（可降级）+ 复制电脑打开地址
 * - narrow 态 lead 含当前宽度；rotate / narrow 拉宽后自动进入（resize 监听）
 * - 首次进入支持态时调用一次性 onSupportedStart（加载数据 + 路由）
 */
import { V2, $, show } from "./store.js";
import { trackStudioEvent } from "../js/analytics.js";
import {
  classifyViewport, isSupported, unsupportedCopy,
} from "./viewport-logic.js";

var _lastUnsupportedLayout = null;
var _actionHandlersBound = false;

function coarsePointer() {
  try {
    return window.matchMedia("(pointer: coarse)").matches;
  } catch (e) {
    return false;
  }
}

export function currentLayout() {
  var w = window.innerWidth || document.documentElement.clientWidth || 0;
  var h = window.innerHeight || document.documentElement.clientHeight || 0;
  return classifyViewport(w, h, coarsePointer());
}

function viewportWidth() {
  return window.innerWidth || document.documentElement.clientWidth || 0;
}

function copyPageUrl() {
  var url = window.location.origin + window.location.pathname + window.location.search;
  var done = function () {
    if (typeof studioToast === "function") {
      studioToast("已复制，请在电脑浏览器打开", { duration: 2200 });
    }
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(url).then(done, done);
  } else {
    done();
  }
  trackStudioEvent("unsupported_action_click", { action: "copy_link" });
}

function onQrError() {
  try {
    trackStudioEvent("mobile_gate_qr_error", {
      src: ($("v2-unsupported-qr") && $("v2-unsupported-qr").getAttribute("src")) || null,
      layout: V2.layout || "unsupported_phone",
    });
  } catch (_e) {}
  var qrFallback = $("v2-unsupported-qr-fallback");
  showMiniappQrFallback($("v2-unsupported-qr"), qrFallback, qrFallback && qrFallback.textContent);
}

function miniappQrAssetAvailable() {
  var body = document.body;
  return !!(body && body.getAttribute("data-miniapp-qr") === "1");
}

function showMiniappQrFallback(qrImg, qrFallback, text) {
  if (qrImg) {
    qrImg.removeAttribute("src");
    show(qrImg, false);
  }
  if (qrFallback) {
    if (text) qrFallback.textContent = text;
    show(qrFallback, true);
  }
}

function ensureActionHandlers() {
  if (_actionHandlersBound) return;
  _actionHandlersBound = true;

  var copyBtn = $("v2-unsupported-copy");
  if (copyBtn) {
    copyBtn.addEventListener("click", copyPageUrl);
  }

  var qrImg = $("v2-unsupported-qr");
  if (qrImg) {
    qrImg.addEventListener("error", onQrError);
  }
}

function renderActions(actions) {
  ensureActionHandlers();

  var host = $("v2-unsupported-actions");
  var qrWrap = $("v2-unsupported-qr-wrap");
  var qrImg = $("v2-unsupported-qr");
  var qrFallback = $("v2-unsupported-qr-fallback");
  var copyBtn = $("v2-unsupported-copy");
  if (!host) return;

  var list = Array.isArray(actions) ? actions : [];
  var qrAction = null;
  var copyAction = null;
  list.forEach(function (action) {
    if (!action) return;
    if (action.type === "miniapp_qr") qrAction = action;
    if (action.type === "copy_link") copyAction = action;
  });

  show(host, list.length > 0);

  if (qrWrap) {
    // FE-DFX-40 · 无 QR action 或无能力 → 整位移除；仅有能力时才加载图 / onerror 降级
    var canShowQr = !!qrAction && miniappQrAssetAvailable();
    show(qrWrap, canShowQr);
    if (canShowQr) {
      var fallbackText = qrAction.fallback || "小程序即将上线";
      if (qrFallback) qrFallback.textContent = fallbackText;
      if (qrImg && qrAction.src) {
        show(qrImg, true);
        show(qrFallback, false);
        qrImg.alt = "微信小程序";
        qrImg.src = qrAction.src;
      } else {
        showMiniappQrFallback(qrImg, qrFallback, fallbackText);
      }
    } else if (qrImg) {
      qrImg.removeAttribute("src");
      show(qrImg, false);
      if (qrFallback) show(qrFallback, false);
    }
  }

  if (copyBtn) {
    show(copyBtn, !!copyAction);
    if (copyAction) {
      copyBtn.textContent = copyAction.label || "复制电脑打开地址";
    }
  }
}

function trackUnsupportedView(layout) {
  if (_lastUnsupportedLayout === layout) return;
  _lastUnsupportedLayout = layout;
  var key = String(layout || "").replace(/^unsupported_/, "");
  trackStudioEvent("unsupported_view", { layout: key || "unknown" });
}

function renderUnsupported(layout) {
  // FE-DFX-40 · 无 QR 资产时不渲染二维码位（删位，非占位降级）
  var copy = unsupportedCopy(layout, {
    width: viewportWidth(),
    miniappQrAvailable: miniappQrAssetAvailable(),
  });
  var titleEl = $("v2-unsupported-title");
  var leadEl = $("v2-unsupported-lead");
  if (titleEl) titleEl.textContent = copy.title;
  if (leadEl) leadEl.textContent = copy.lead;
  renderActions(copy.actions);
  trackUnsupportedView(layout);
  show($("v2-unsupported"), true);
  show($("v2-bento-main"), false);
}

function hideUnsupported() {
  _lastUnsupportedLayout = null;
  show($("v2-unsupported"), false);
  show($("v2-bento-main"), true);
}

/**
 * 应用当前视口；支持态首次进入时触发 onSupportedStart（仅一次）。
 * @param {function} onSupportedStart
 */
export function applyViewport(onSupportedStart) {
  var layout = currentLayout();
  V2.layout = layout;
  try {
    document.documentElement.setAttribute("data-v2-layout", layout);
  } catch (_e) { /* ignore */ }
  if (!isSupported(layout)) {
    renderUnsupported(layout);
    return;
  }
  hideUnsupported();
  if (!V2._started) {
    V2._started = true;
    if (typeof onSupportedStart === "function") onSupportedStart();
  }
}

export function initViewportWatch(onSupportedStart) {
  applyViewport(onSupportedStart);
  var handler = function () { applyViewport(onSupportedStart); };
  window.addEventListener("resize", handler);
  window.addEventListener("orientationchange", handler);
}
