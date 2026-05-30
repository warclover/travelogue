/**
 * Travelogue Studio · v3 Photo-First Homepage Controller (ESM entry · P5-A1)
 * State machine: Loading → IdleEmpty / IdleReturning → Importing → FirstSuccess
 *                                                            → Failed → ...
 *                                                            → Offline
 *
 * This file is the module entry: it wires DOM events on DOMContentLoaded and
 * delegates to focused modules under ./js/. Shared mutable state lives in
 * ./js/state.js (the S object).
 */
import { S } from "./js/state.js";
import { LS, SS } from "./js/constants.js";
import { $ } from "./js/dom.js";
import { hideFailure, loadPipelineEstimates } from "./js/errors.js";
import { transitionTo } from "./js/navigation.js";
import "./js/render.js";
import { loadTrips, startHealthCheck, cancelActiveJob } from "./js/api.js";
import { renderSampleCards, renderHeroSampleStrip, initSampleModal, openSamplePreview } from "./js/samples.js";
import {
  initImportSheet, closeImportSheet, replayCoachMarks, renderRecentPaths, loadIntent,
} from "./js/sheet.js";
import { initAdvancedOptions } from "./js/advanced.js";
import {
  initFooter, initCopyAddr, initPathToggle, initScrollHint, initTripsMore,
} from "./js/init.js";
import {
  requestNativeFolder, submitPathImport, startImport, uploadAndImport,
  rememberCancelled, resumeActiveJobIfAny, clearSuccessTimer, clearSuccessLongshotPoll, startSuccessLongshot,
} from "./js/import-flow.js";

// ── Main init ──
document.addEventListener("DOMContentLoaded", function () {
  initFooter();
  initCopyAddr();
  var helpReplay = $("studio-help-replay");
  if (helpReplay) helpReplay.addEventListener("click", replayCoachMarks);
  initPathToggle();
  initScrollHint();
  initTripsMore();
  var openSamplesBtn = $("studio-open-samples");
  if (openSamplesBtn) openSamplesBtn.addEventListener("click", function () {
    openSamplePreview("kyoto");
  });
  initAdvancedOptions();
  loadPipelineEstimates();
  renderSampleCards();
  renderHeroSampleStrip();
  initSampleModal();
  initImportSheet();
  renderRecentPaths();
  loadIntent();

  transitionTo("Loading");
  if (!resumeActiveJobIfAny()) {
    loadTrips();
  } else {
    loadTrips({ keepLimit: true });
  }
  startHealthCheck();

  // Path row: browse → fill path + confirm in sheet
  var browse = $("studio-browse-folder");
  if (browse) browse.addEventListener("click", function () {
    requestNativeFolder(null, null, { autoStart: false });
  });

  // Path form submit
  var pathForm = $("studio-import-form");
  if (pathForm) pathForm.addEventListener("submit", function (ev) {
    ev.preventDefault();
    submitPathImport();
  });

  // Secondary: demo album
  var demoBtn = $("studio-demo-album");
  if (demoBtn) demoBtn.addEventListener("click", function () {
    localStorage.setItem(LS.demoTried, "1");
    closeImportSheet();
    startImport({ useDemoAlbum: true, title: "示例旅途", place: "示例", force: false });
  });

  // Secondary: browser upload
  var uploadInput = $("album-upload");
  if (uploadInput) uploadInput.addEventListener("change", function (ev) {
    closeImportSheet();
    uploadAndImport(
      ev.target.files,
      ($("trip-title") && $("trip-title").value) || "我的旅途",
      ($("trip-place") && $("trip-place").value) || "旅途"
    );
    ev.target.value = "";
  });

  // Cancel (modal first)
  var cancelBtn = $("studio-cancel");
  if (cancelBtn) cancelBtn.addEventListener("click", function () {
    var doCancel = function () {
      cancelActiveJob().then(function () {
        rememberCancelled();
        try { sessionStorage.removeItem(SS.activeJobId); sessionStorage.removeItem(SS.activePending); } catch (e) {}
        transitionTo(S.tripsData.length > 0 ? "IdleReturning" : "IdleEmpty");
      }).catch(function () { /* user cancel or network blip — stay on current UI */ });
    };
    if (typeof studioModal === "function") {
      studioModal({
        title: "确定取消？",
        body: "取消后将丢失当前进度。",
        confirmText: "确定取消",
        cancelText: "继续等待",
      }).then(function (confirmed) { if (confirmed) doCancel(); });
    } else if (window.confirm("确定取消导入？")) {
      doCancel();
    }
  });

  // Retry
  var retryBtn = $("studio-retry");
  if (retryBtn) retryBtn.addEventListener("click", function () {
    hideFailure();
    if (!S.pendingImport) {
      transitionTo(S.tripsData.length > 0 ? "IdleReturning" : "IdleEmpty");
      return;
    }
    if (S.pendingImport.uploadForm && S.pendingImport.files) {
      uploadAndImport(S.pendingImport.files, $("trip-title").value, $("trip-place").value);
      return;
    }
    startImport(S.pendingImport);
  });

  // Success: stay on home
  var stayBtn = $("studio-success-stay");
  if (stayBtn) stayBtn.addEventListener("click", function () {
    clearSuccessTimer();
    clearSuccessLongshotPoll();
    transitionTo(S.tripsData.length > 0 ? "IdleReturning" : "IdleEmpty");
  });
  var openBtn = $("studio-success-open");
  if (openBtn) openBtn.addEventListener("click", function () {
    clearSuccessTimer();
    clearSuccessLongshotPoll();
  });
  var longshotBtn = $("studio-success-longshot");
  if (longshotBtn) longshotBtn.addEventListener("click", function () {
    clearSuccessTimer();
    startSuccessLongshot();
  });
});
