/**
 * 首页 v2 · UnsupportedViewport（M20-f · §10.3）+ 视口监听。
 *
 * - 按 viewport-logic 分类；不支持 → 显示壳层提示，隐藏 Bento
 * - 监听 resize / orientationchange 动态重判
 * - 首次进入支持态时调用一次性 onSupportedStart（加载数据 + 路由）
 */
import { V2, $, show } from "./store.js";
import {
  classifyViewport, isSupported, unsupportedCopy,
} from "./viewport-logic.js";

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

function renderUnsupported(layout) {
  var copy = unsupportedCopy(layout);
  var titleEl = $("v2-unsupported-title");
  var leadEl = $("v2-unsupported-lead");
  if (titleEl) titleEl.textContent = copy.title;
  if (leadEl) leadEl.textContent = copy.lead;
  show($("v2-unsupported"), true);
  show($("v2-bento-main"), false);
}

function hideUnsupported() {
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
