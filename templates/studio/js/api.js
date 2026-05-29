/**
 * Travelogue Studio · HTTP/job layer + trips loading + health check.
 */
import {
  SLOW_JOB_MS, SLOW_JOB_VISION_MS, SLOW_JOB_VISION_LONG_MS, HEALTH_INTERVAL,
} from "./constants.js";
import { S } from "./state.js";
import {
  $, show, studioAuthHeaders, bumpImportGeneration, isImportGenerationStale,
} from "./dom.js";
import { humanizeStudioError, showSlowHint, hideSlowHint } from "./errors.js";
import { updateProgress } from "./progress.js";
import { render, transitionTo } from "./render.js";

export function pollJob(jobId) {
  return fetch("/__travelogue/status?jobId=" + encodeURIComponent(jobId))
    .then(function (r) { return r.json(); });
}

export function cancelActiveJob() {
  bumpImportGeneration();
  if (!S.activeJobId) return Promise.resolve();
  var jobId = S.activeJobId;
  return fetch("/__travelogue/cancel", {
    method: "POST",
    headers: studioAuthHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ jobId: jobId }),
  }).finally(function () {
    S.activeJobId = null;
    show($("studio-cancel"), false);
  });
}

export function refreshImportVisionFlag() {
  return fetch("/__travelogue/config")
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (!data || data.ok === false) return;
      var vis = data.vision && data.vision.enabled;
      S._importVisionEnabled = vis === "true" || vis === "auto";
    })
    .catch(function () { S._importVisionEnabled = false; });
}

export function postImport(body) {
  return fetch("/__travelogue/import", {
    method: "POST",
    headers: studioAuthHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  }).then(function (resp) {
    return resp.json().then(function (data) { return { status: resp.status, data: data }; });
  });
}

export function postMultipartImport(formData, options) {
  options = options || {};
  return new Promise(function (resolve, reject) {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/__travelogue/import");
    var token = (document.querySelector('meta[name="studio-token"]') || {}).content;
    if (token) xhr.setRequestHeader("X-Studio-Token", token);
    if (options.onUploadProgress) {
      xhr.upload.onprogress = options.onUploadProgress;
    }
    xhr.onload = function () {
      var data = {};
      try { data = JSON.parse(xhr.responseText || "{}"); } catch (e) {}
      resolve({ status: xhr.status, data: data });
    };
    xhr.onerror = function () {
      reject(new Error(
        "上传失败：网络中断或照片总量过大（浏览器上传上限约 200MB）。请改用「选择照片文件夹」或路径导入。"
      ));
    };
    xhr.send(formData);
  });
}

export function waitJob(jobId, gen) {
  S.activeJobId = jobId;
  var started = Date.now();
  var slowShown = 0;
  hideSlowHint();
  refreshImportVisionFlag();

  return new Promise(function (resolve, reject) {
    function finishCancel() {
      S.activeJobId = null;
      show($("studio-cancel"), false);
      hideSlowHint();
      reject(new Error("已取消"));
    }
    function tick() {
      if (isImportGenerationStale(gen)) {
        finishCancel();
        return;
      }
      pollJob(jobId).then(function (job) {
        if (isImportGenerationStale(gen)) {
          finishCancel();
          return;
        }
        if (S._importVisionEnabled && !slowShown && Date.now() - started > SLOW_JOB_VISION_LONG_MS) {
          slowShown = 3;
          showSlowHint(3);
        } else if (S._importVisionEnabled && slowShown < 2 && Date.now() - started > SLOW_JOB_VISION_MS) {
          slowShown = 2;
          showSlowHint(2);
        } else if (!slowShown && Date.now() - started > SLOW_JOB_MS) {
          slowShown = 1;
          showSlowHint(1);
        }
        if (job.status === "running" || job.status === "queued") {
          updateProgress(job);
          setTimeout(tick, 500);
          return;
        }
        S.activeJobId = null;
        show($("studio-cancel"), false);
        hideSlowHint();
        if (job.status === "succeeded") { updateProgress(job); resolve(job); return; }
        if (job.status === "cancelled") { reject(new Error("已取消")); return; }
        var err = job.error || {};
        reject(new Error(humanizeStudioError(err.code, err.message || err.code)));
      }).catch(reject);
    }
    tick();
  });
}

// ── Load trips (with timeout handling per §6.12) ──
export function renderTripsSkeleton(n) {
  // F-P4-HP-07 / HP-GAP-08: F-area grid skeleton during the initial /trips load.
  var list = $("studio-trips-list");
  var section = $("studio-trips");
  if (!list || !section) return;
  list.innerHTML = "";
  for (var i = 0; i < (n || 6); i++) {
    var card = document.createElement("div");
    card.className = "studio-trip-card studio-skeleton-card";
    card.setAttribute("aria-hidden", "true");
    var thumb = document.createElement("div");
    thumb.className = "studio-skeleton-card__thumb";
    var line = document.createElement("div");
    line.className = "studio-skeleton-card__line";
    var line2 = document.createElement("div");
    line2.className = "studio-skeleton-card__line studio-skeleton-card__line--short";
    card.appendChild(thumb);
    card.appendChild(line);
    card.appendChild(line2);
    list.appendChild(card);
  }
  section.hidden = false;
}

export function loadTrips(options) {
  options = options || {};
  if (options.more) S.tripsListLimit += 20;
  else if (options.keepLimit !== true) S.tripsListLimit = 20;

  var seq = ++S._tripsLoadSeq;
  // Show skeleton only on the first load (no data yet) so refreshes don't flash.
  if (S.tripsData.length === 0 && !options.more) renderTripsSkeleton(6);
  var slowToastShown = false;
  var failToastShown = false;
  var slowTimer = setTimeout(function () {
    slowToastShown = true;
    if (typeof studioToast === "function") studioToast("加载较慢，请稍候", { duration: 4000 });
  }, 3000);
  var failTimer = setTimeout(function () {
    failToastShown = true;
    if (typeof studioToast === "function") studioToast("加载失败，请检查 Studio 是否运行", { duration: 5000 });
  }, 10000);

  fetch("/__travelogue/trips?limit=" + encodeURIComponent(String(S.tripsListLimit)))
    .then(function (r) { if (!r.ok) throw new Error("trips unavailable"); return r.json(); })
    .then(function (data) {
      if (seq !== S._tripsLoadSeq) return;
      clearTimeout(slowTimer); clearTimeout(failTimer);
      S.tripsData = data.trips || [];
      S.tripsTotalCount = typeof data.total === "number" ? data.total : S.tripsData.length;
      if (S.currentState === "Loading" || S.currentState === "IdleEmpty" || S.currentState === "IdleReturning") {
        transitionTo(S.tripsData.length > 0 ? "IdleReturning" : "IdleEmpty");
      } else {
        render();
      }
    })
    .catch(function () {
      if (seq !== S._tripsLoadSeq) return;
      clearTimeout(slowTimer); clearTimeout(failTimer);
      S.isOffline = true;
      render();
      if (S.tripsData.length === 0) {
        transitionTo("IdleEmpty");
        if (!failToastShown && !slowToastShown && typeof studioToast === "function") {
          studioToast("加载失败，请检查 Studio 是否运行", { duration: 5000 });
        }
      }
    });
}

// ── Health check / Offline ──
export function startHealthCheck() {
  function check() {
    fetch("/__travelogue/trips", { method: "GET" })
      .then(function (r) {
        var wasOffline = S.isOffline;
        S.isOffline = !r.ok;
        if (wasOffline && !S.isOffline) {
          if (typeof studioToast === "function") studioToast("服务已恢复", { duration: 2000 });
          loadTrips();
        }
        render();
      })
      .catch(function () {
        var wasOffline = S.isOffline;
        S.isOffline = true;
        if (!wasOffline) render();
      });
  }
  check();
  S.healthTimer = setInterval(check, HEALTH_INTERVAL);
}
