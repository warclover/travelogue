/**
 * 首页 v2 · Lightbox（M20-c · §6.7）。
 *
 * - scroll 模式：按 manifest.pages[] 顺序纵向拼接全部 webp（DATA-CONTRACT §1.3）
 * - longshot 模式：9:16 长图竖滚
 * - focus trap + Esc + 关闭归还焦点；不进 editor preview
 * - 打开入口已移除（Bento 内仅内联预览）；保留模块供后续复用
 * 复用：constants.js SHEET_FOCUSABLE、共享 analytics（lightbox_open 待 M20-h 入 ALLOWED）。
 */
import { SHEET_FOCUSABLE } from "../js/constants.js";
import { trackStudioEvent } from "../js/analytics.js";
import { V2, $, show } from "./store.js";
import { pageImageUrl, manifestAssetUrl, longshotPages, longshotPageUrl } from "./manifest.js";

let _open = false;
let _previousFocus = null;
let _trapHandler = null;

function pagePlaceholder(page) {
  if (!page) return "";
  if (page.role === "cover") return "雨后 · 封面";
  if (page.role === "epilogue") return "— 尾声 —";
  return page.label || "";
}

function appendImage(host, url, alt, phText, phClass) {
  var ph = document.createElement("div");
  ph.className = phClass || "v2-lightbox__page-ph";
  ph.textContent = phText || "";
  host.appendChild(ph);
  if (!url) return;
  var img = new Image();
  img.alt = alt || "";
  img.onload = function () {
    if (ph.parentNode) ph.parentNode.replaceChild(img, ph);
  };
  img.src = url; // onerror：保留 placeholder
}

function buildScrollContent(scroll, manifest) {
  var pages = (manifest && manifest.pages) || [];
  pages.forEach(function (page) {
    appendImage(scroll, pageImageUrl(manifest, page), page.label, pagePlaceholder(page));
  });
}

function buildLongshotContent(scroll, manifest) {
  var pages = longshotPages(manifest);
  if (!pages.length) {
    appendImage(scroll, "", "微信长图样张", "长图样张加载中…");
    return;
  }
  pages.forEach(function (page) {
    appendImage(
      scroll,
      longshotPageUrl(manifest, page),
      page.label || "微信长图",
      page.label || "长图加载中…"
    );
  });
}

function focusableEls(container) {
  return Array.prototype.slice
    .call(container.querySelectorAll(SHEET_FOCUSABLE))
    .filter(function (el) { return el.offsetParent !== null; });
}

function trapFocus(box) {
  _trapHandler = function (e) {
    if (e.key !== "Tab") return;
    var els = focusableEls(box);
    if (!els.length) return;
    var first = els[0];
    var last = els[els.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault(); last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault(); first.focus();
    }
  };
  box.addEventListener("keydown", _trapHandler);
}

export function openLightbox(payload) {
  payload = payload || {};
  var type = payload.type === "longshot" ? "longshot" : "scroll";
  var lb = $("v2-lightbox");
  var inner = $("v2-lightbox-inner");
  var scroll = $("v2-lightbox-scroll");
  var caption = $("v2-lightbox-caption");
  if (!lb || !scroll) return;

  scroll.innerHTML = "";
  scroll.scrollTop = 0;
  if (inner) inner.classList.toggle("v2-lightbox__inner--phone", type === "longshot");

  var title = (V2.manifest && V2.manifest.title) || "示例作品";
  var isUser = V2.manifest && V2.manifest.source === "user";
  if (type === "longshot") {
    buildLongshotContent(scroll, V2.manifest);
    if (caption) {
      caption.textContent = (isUser ? "竖版长图 · " : "竖版长图 · 只读 · ") + title;
    }
  } else {
    buildScrollContent(scroll, V2.manifest);
    if (caption) {
      caption.textContent = (isUser ? "画册预览 · " : "完整画册 · 只读 · ") + title;
    }
  }

  _previousFocus = document.activeElement;
  show(lb, false); // 清 hidden 属性由 class 控制
  lb.hidden = false;
  lb.classList.add("is-open");
  _open = true;
  trapFocus(lb);
  var closeBtn = $("v2-lightbox-close");
  if (closeBtn) closeBtn.focus();
  trackStudioEvent("lightbox_open", { type: type, surface: "bento" });
}

export function closeLightbox() {
  var lb = $("v2-lightbox");
  if (!lb) return;
  lb.classList.remove("is-open");
  lb.hidden = true;
  _open = false;
  if (_trapHandler) lb.removeEventListener("keydown", _trapHandler);
  _trapHandler = null;
  if (_previousFocus && typeof _previousFocus.focus === "function") {
    _previousFocus.focus();
  }
}

export function initLightbox() {
  var lb = $("v2-lightbox");
  if (lb) {
    lb.addEventListener("click", function (e) {
      if (e.target && e.target.hasAttribute && e.target.hasAttribute("data-close")) {
        closeLightbox();
      }
    });
  }
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && _open) closeLightbox();
  });
}
