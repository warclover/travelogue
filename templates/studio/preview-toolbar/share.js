/**
 * Preview toolbar · share preview minimal chrome.
 * Trust V1 · Share 真只读：零精修、零工程壳、强制 refine=off；保留「保存图片」。
 */
"use strict";

import { insertScreenplayControl } from "./dock.js";
import { setPreviewRefineMode } from "./preview-mode.js";
import { tripIdFromPath } from "./shell.js";
import {
  startLongshotJob,
  waitForLongshotJob,
  revealLongshotOutput,
  isJobBusyResponse,
} from "../js/longshot-client.js";
import { trackStudioEvent } from "../js/analytics.js";

export function isSharePreview() {
  var q = window.location.search || "";
  return q.indexOf("share=1") >= 0 || q.indexOf("mode=share") >= 0;
}

function setShareSaveStatus(root, text, isError) {
  var el = root.querySelector(".preview-toolbar__share-save-status");
  if (!el) return;
  el.hidden = !text;
  el.textContent = text || "";
  el.classList.toggle("preview-toolbar__share-save-status--error", !!isError);
}

function runShareSaveImages(root, btn) {
  var tripId = tripIdFromPath();
  if (!tripId) {
    setShareSaveStatus(root, "无法识别画册", true);
    return;
  }
  if (btn.disabled) return;
  btn.disabled = true;
  setShareSaveStatus(root, "正在保存图片…", false);
  trackStudioEvent("longshot_export_start", {
    platform: "wechat_chat",
    trip_id: tripId,
    surface: "share",
    from: "share_save",
  });

  startLongshotJob(tripId, {
    scale: 2,
    copyDisplay: "full",
    format: "png",
    platform: "wechat_chat",
    segmentMode: "auto",
  })
    .then(function (res) {
      if (isJobBusyResponse(res) || res.status === 409) {
        setShareSaveStatus(root, "排队中，请稍候…", false);
        btn.disabled = false;
        return null;
      }
      if (res.status !== 202 || !res.body || !res.body.jobId) {
        trackStudioEvent("longshot_export_fail", {
          platform: "wechat_chat",
          error_code: "E_LNG2_START_FAILED",
          trip_id: tripId,
          surface: "share",
        });
        setShareSaveStatus(root, "服务已停止，长图还没有导出", true);
        btn.disabled = false;
        return null;
      }
      return waitForLongshotJob(res.body.jobId, {
        onSlow: function () {
          setShareSaveStatus(root, "比预期久一些，请耐心等待…", false);
        },
      });
    })
    .then(function (job) {
      if (!job) return;
      if (job.status === "succeeded") {
        var result = job.result || {};
        var outputs = result.outputs || [];
        trackStudioEvent("longshot_export_success", {
          platform: "wechat_chat",
          output_count: outputs.length,
          trip_id: tripId,
          surface: "share",
        });
        trackStudioEvent("longshot_success_share_hint_shown", {
          trip_id: tripId,
          segment_count: outputs.length,
          surface: "share",
        });
        setShareSaveStatus(root, "已保存到本机 · 拖进微信群即可", false);
        if (outputs.length) {
          revealLongshotOutput(tripId, outputs[0]).catch(function () {});
        }
      } else {
        trackStudioEvent("longshot_export_fail", {
          platform: "wechat_chat",
          error_code: (job.error && job.error.code) || "failed",
          trip_id: tripId,
          surface: "share",
        });
        setShareSaveStatus(
          root,
          (job.error && job.error.message) || "保存失败，请重试",
          true
        );
      }
      btn.disabled = false;
    })
    .catch(function () {
      trackStudioEvent("longshot_export_fail", {
        platform: "wechat_chat",
        error_code: "disconnect",
        trip_id: tripId,
        surface: "share",
      });
      setShareSaveStatus(root, "服务已停止，长图还没有导出", true);
      btn.disabled = false;
    });
}

export function initShareMinimal() {
  document.documentElement.setAttribute("data-preview-share", "on");
  // Trust V1 · Share 强制验货/只读壳
  setPreviewRefineMode(false);

  var root = document.createElement("div");
  root.className = "preview-toolbar preview-toolbar--share-minimal";
  root.innerHTML =
    '<div class="preview-toolbar__body">' +
    '<div class="preview-toolbar__bar preview-toolbar__bar--minimal">' +
    '<div class="preview-toolbar__spacer" aria-hidden="true"></div>' +
    '<div class="preview-toolbar__cluster">' +
    '<a class="preview-toolbar__back" href="/" title="返回 Studio 首页">← 返回</a>' +
    '<button type="button" class="preview-toolbar__ctl preview-toolbar__share-save" ' +
    'id="preview-share-save" aria-label="保存图片">保存图片</button>' +
    '<span class="preview-toolbar__share-save-status" hidden aria-live="polite"></span>' +
    "</div>" +
    "</div>" +
    "</div>";
  document.body.insertBefore(root, document.body.firstChild);

  var shareCluster = root.querySelector(".preview-toolbar__cluster");
  insertScreenplayControl(shareCluster, shareCluster && shareCluster.firstChild);

  var saveBtn = root.querySelector("#preview-share-save");
  if (saveBtn) {
    saveBtn.addEventListener("click", function () {
      runShareSaveImages(root, saveBtn);
    });
  }

  // 禁用仍残留的可编辑提示 / contenteditable
  document.querySelectorAll("[data-editable]").forEach(function (el) {
    el.removeAttribute("contenteditable");
    el.removeAttribute("tabindex");
    el.removeAttribute("title");
    el.classList.remove("inline-edit__field--active");
  });
  document.querySelectorAll(".cover-opening__title--editable").forEach(function (el) {
    el.classList.remove("cover-opening__title--editable");
    el.removeAttribute("role");
    el.removeAttribute("tabindex");
  });

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

  // 底栏若仍写「点击文案可编辑」类文案则隐藏
  document.querySelectorAll(".footer-cta, .preview-edit-hint").forEach(function (el) {
    var text = el.textContent || "";
    if (text.indexOf("可编辑") >= 0 || text.indexOf("点击文案") >= 0) {
      el.hidden = true;
    }
  });
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
