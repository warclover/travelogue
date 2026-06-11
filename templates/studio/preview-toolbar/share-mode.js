/**
 * Preview toolbar · share / minimal chrome (M-P2b · R-P2-03).
 */
"use strict";

import { SHARE_TOOLBAR_HTML } from "./templates.js";

export function presentPreviewUrl() {
  return document.documentElement.getAttribute("data-present-preview-url") || "";
}

export function presentAutoplayHref(opts) {
  var url = presentPreviewUrl();
  if (!url) return "";
  var href = url;
  if (opts && opts.featured) {
    href += (href.indexOf("?") >= 0 ? "&" : "?") + "presentFeatured=1";
  }
  return href + "#present/1";
}

function insertScreenplayControl(parent, beforeNode) {
  if (!parent) return null;
  if (document.documentElement.getAttribute("data-screenplay") === "on") {
    var screenplayBtn = document.createElement("button");
    screenplayBtn.type = "button";
    screenplayBtn.className = "preview-toolbar__ctl preview-toolbar__screenplay";
    screenplayBtn.setAttribute("data-screenplay-trigger", "start");
    screenplayBtn.setAttribute("data-screenplay-label", "▶ 放映");
    screenplayBtn.setAttribute("data-screenplay-busy", "退出放映");
    screenplayBtn.setAttribute("aria-pressed", "false");
    screenplayBtn.setAttribute("aria-label", "全屏放映，逐屏展示");
    screenplayBtn.title = "全屏逐屏放映";
    screenplayBtn.textContent = "▶ 放映";
    parent.insertBefore(screenplayBtn, beforeNode || null);
    return screenplayBtn;
  }
  var href = presentAutoplayHref();
  if (!href) return null;
  var autoplayLink = document.createElement("a");
  autoplayLink.className = "preview-toolbar__ctl preview-toolbar__screenplay";
  autoplayLink.href = href;
  autoplayLink.textContent = "▶ 放映";
  autoplayLink.setAttribute("aria-label", "全屏放映，逐屏展示");
  autoplayLink.title = "全屏逐屏放映";
  parent.insertBefore(autoplayLink, beforeNode || null);
  return autoplayLink;
}

export function isSharePreview() {
  var q = window.location.search || "";
  return q.indexOf("share=1") >= 0 || q.indexOf("mode=share") >= 0;
}

/** share 态极简顶栏：左返回 + 放映入口；页内 longshot/screenplay FAB 由 CSS 隐藏。 */
export function initShareMinimal() {
  document.documentElement.setAttribute("data-preview-share", "on");

  var root = document.createElement("div");
  root.className = "preview-toolbar preview-toolbar--share-minimal";
  root.innerHTML = SHARE_TOOLBAR_HTML;
  document.body.insertBefore(root, document.body.firstChild);

  var shareCluster = root.querySelector(".preview-toolbar__cluster");
  insertScreenplayControl(shareCluster, shareCluster && shareCluster.firstChild);

  var footerHomes = document.querySelectorAll(".footer-cta__studio-home");
  if (footerHomes.length) {
    footerHomes.forEach(function (row) {
      row.hidden = false;
    });
  } else {
    var footer = document.querySelector(".footer-cta");
    if (footer) {
      var homeRow = document.createElement("p");
      homeRow.className = "footer-cta__studio-home";
      homeRow.innerHTML =
        '<a class="footer-cta__studio-home-link" href="/">← 返回 Studio 首页</a>';
      footer.insertBefore(homeRow, footer.firstChild);
    }
  }
}
