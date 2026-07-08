/**
 * Preview toolbar · share preview minimal chrome.
 */
"use strict";

import { insertScreenplayControl } from "./dock.js";

export function isSharePreview() {
  var q = window.location.search || "";
  return q.indexOf("share=1") >= 0 || q.indexOf("mode=share") >= 0;
}

export function initShareMinimal() {
  document.documentElement.setAttribute("data-preview-share", "on");

  var root = document.createElement("div");
  root.className = "preview-toolbar preview-toolbar--share-minimal";
  root.innerHTML =
    '<div class="preview-toolbar__body">' +
    '<div class="preview-toolbar__bar preview-toolbar__bar--minimal">' +
    '<div class="preview-toolbar__spacer" aria-hidden="true"></div>' +
    '<div class="preview-toolbar__cluster">' +
    '<a class="preview-toolbar__back" href="/" title="返回 Studio 首页">← 返回</a>' +
    "</div>" +
    "</div>" +
    "</div>";
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

export function ensureCoverMobileFootnote() {
  if (isSharePreview()) return;
  if (document.getElementById("preview-toolbar-cover-footnote")) return;
  var note = document.createElement("p");
  note.id = "preview-toolbar-cover-footnote";
  note.className = "preview-toolbar__cover-footnote";
  note.setAttribute("role", "note");
  note.textContent = "手机预览封面版式与电脑不同，以手机效果为准";
  document.body.appendChild(note);
}
