/**
 * 首页 v2 · 导入编排（M20-d）。
 *
 * 复用 v3 共享原语，不复制 v3 视图控制器：
 *  - http.js     postJson / withJobBusyRetry / isJobBusyResponse
 *  - job-poll.js pollJobUntilDone
 *  - constants.js SS / STAGE_LABELS / STUDIO_ERROR_MESSAGES / IMPORT_PHOTO_CAP
 *
 * sessionStorage 写入形状与 v3 完全一致（activeJobId / activePending），
 * 保证跨页 import 续跑（v3 ↔ v2）。Importing UI 为 M20-d 基础版，
 * 冷启动静帧 + 四阶段精修在 M20-g。
 */
import {
  SS, STAGE_LABELS, STAGE_HINT_LABELS, STUDIO_ERROR_MESSAGES, IMPORT_PHOTO_CAP,
  SLOW_JOB_MS, SLOW_JOB_VISION_MS, SLOW_JOB_VISION_LONG_MS,
} from "../js/constants.js";
import { postJson, withJobBusyRetry, isJobBusyResponse } from "../js/http.js";
import { pollJobUntilDone } from "../js/job-poll.js";
import {
  trackStudioEvent,
  trackImportPhotoCullPref,
  trackImportKeepDupesPref,
  readPhotoCullPrefSource,
} from "../js/analytics.js";
import { V2, $, show, setV2SkipLinkTarget } from "./store.js";
import { fetchTripsFirstPage } from "./trips-client.js";
import { renderColdStartBackground } from "./bento.js";
import {
  captureImportShell, showFirstSuccess,
} from "./first-success.js";
import { showImportFailed } from "./import-failed.js";
import { syncVariantGuard } from "./variant-guard.js";
import { syncAdvancedOptionsLock } from "./advanced-options.js";
import { syncHomeStubBanner } from "../js/home-stub-banner.js";

let _gen = 0;
let _activeJobId = null;
let _importStartedAt = 0;
let _slowHintLevel = 0;

/** T-M4-04 · 冻结三档慢安抚（与 errors.js showSlowHint 同源） */
var SLOW_HINT_COPY = {
  1: "比预期久一些，请耐心等待…",
  2: "照片较多，正在仔细分析行程与场景，首次可能较慢",
  3: "仍可继续等待，或在「高级 · 分析选项」中关闭场景分析以加快速度",
};

function humanizeError(code, fallback) {
  return STUDIO_ERROR_MESSAGES[code] || fallback || "导入失败，请重试";
}

/** FE-FTUE-02：示例已存在 → open | regenerate | cancel */
function resolveDemoAlbumExists(data) {
  var previewUrl =
    (data && data.result && data.result.previewUrl) ||
    (data && data.previewUrl) ||
    "/demo-album/index.html";
  if (typeof studioModal === "function") {
    return studioModal({
      title: "示例相册已在书架",
      body: "可以打开已有成品，或重新生成（将覆盖）。",
      confirmText: "打开已有示例 →",
      secondaryText: "重新生成（将覆盖）",
      cancelText: "取消",
      stacked: true,
    }).then(function (choice) {
      if (choice === "confirm") return "open";
      if (choice === "secondary") return "regenerate";
      return "cancel";
    });
  }
  var openFirst = window.confirm(
    (data && data.message) || "示例相册已存在。确定=打开已有示例；取消=放弃。"
  );
  if (openFirst) return Promise.resolve("open");
  return Promise.resolve("cancel");
}

function postMultipartImportV2(formData, options) {
  options = options || {};
  return new Promise(function (resolve, reject) {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/__travelogue/import");
    var token = (document.querySelector('meta[name="studio-token"]') || {}).content;
    if (token) xhr.setRequestHeader("X-Studio-Token", token);
    if (options.onUploadProgress) xhr.upload.onprogress = options.onUploadProgress;
    xhr.onload = function () {
      var body = {};
      try { body = JSON.parse(xhr.responseText || "{}"); } catch (e) {}
      resolve({ status: xhr.status, body: body });
    };
    xhr.onerror = function () {
      reject(new Error(
        "上传失败：网络中断或照片总量过大。建议改用「选择本次旅行的照片文件夹」。"
      ));
    };
    xhr.send(formData);
  });
}

function basenameTitle(path) {
  if (!path) return "我的旅途";
  var parts = String(path).replace(/[\\/]+$/, "").split(/[\\/]/);
  var name = parts[parts.length - 1] || "我的旅途";
  return name.slice(0, 20);
}

function basenameFromRelativePath(rel) {
  if (!rel) return "";
  var parts = String(rel).split(/[\\/]/);
  return (parts[0] || "").trim();
}

function guessUploadTitle(files) {
  if (!files || !files.length) return "我的旅途";
  var title = basenameFromRelativePath(files[0].webkitRelativePath);
  if (!title) return "我的旅途";
  return title.slice(0, 20);
}

function buildUploadForm(files, opts) {
  opts = opts || {};
  var form = new FormData();
  var title = (opts.title || guessUploadTitle(files) || "我的旅途").slice(0, 20);
  form.append("title", title);
  var place = String(opts.place || "旅途").trim() || "旅途";
  form.append("place", place);
  var placeUserSet = opts.placeUserSet === true ||
    (opts.placeUserSet !== false && place && place !== "旅途");
  form.append("placeUserSet", placeUserSet ? "true" : "false");
  var mode = String(opts.mode || "quick_share");
  form.append("mode", mode);
  if (mode === "fine_craft" && opts.layoutDensity) {
    form.append("layoutDensity", String(opts.layoutDensity));
  }
  var tplMode = opts.template_mode || opts.templateMode;
  var tplId = opts.template_id || opts.templateId;
  if (!tplMode) {
    var tpl = readTemplateParams();
    tplMode = tpl.template_mode;
    tplId = tpl.template_id;
  }
  form.append("template_mode", tplMode || "smart");
  if (tplId) form.append("template_id", tplId);
  if (opts.userNotes) form.append("userNotes", String(opts.userNotes).slice(0, 200));
  if (opts.travelNotes) form.append("travelNotes", String(opts.travelNotes).slice(0, 500));
  var dateRange = opts.dateRange;
  if (dateRange && typeof dateRange === "object") {
    if (dateRange.start) form.append("dateRangeStart", String(dateRange.start));
    if (dateRange.end) form.append("dateRangeEnd", String(dateRange.end));
  }
  if (opts.featuredDir) form.append("featuredDir", String(opts.featuredDir));
  if (opts.materialDir) form.append("materialDir", String(opts.materialDir));
  if (opts.force) form.append("force", "true");
  if (opts.forceStub) form.append("forceStub", "true");
  form.append("photoCullEnabled", opts.photoCullEnabled === false ? "false" : "true");
  form.append("keepNearDuplicates", opts.keepNearDuplicates === true ? "true" : "false");
  for (var i = 0; i < files.length; i++) {
    form.append("files[]", files[i], files[i].webkitRelativePath || files[i].name);
  }
  return form;
}

/** 与 import-wizard.js 同源：读 Wizard 模板控件（勿回退到已退役 #v2-template-mode）。 */
function readTemplateParams() {
  var sel = $("v2-wizard-template-mode");
  if (!sel) return { template_mode: "smart" };
  var v = String(sel.value || "smart");
  if (v.indexOf("manual:") === 0) {
    return { template_mode: "manual", template_id: v.slice(7) || "visual-journal" };
  }
  return { template_mode: "smart" };
}

export function buildImportPayload(albumPath, title) {
  return Object.assign(
    {
      albumPath: albumPath,
      title: (title || basenameTitle(albumPath)).slice(0, 20) || "我的旅途",
      place: "旅途",
      placeUserSet: false,
      mode: "quick_share",
      force: false,
    },
    readTemplateParams()
  );
}

function setStage(text, fillPct) {
  var stage = $("v2-import-stage");
  if (stage && text) stage.textContent = text;
  var progress = $("v2-import-progress");
  var fill = $("v2-import-fill");
  if (fill && typeof fillPct === "number") {
    var pct = Math.max(0, Math.min(100, fillPct));
    fill.style.width = pct + "%";
    if (progress) progress.setAttribute("aria-valuenow", String(Math.round(pct)));
  }
  if (progress && text) {
    progress.setAttribute("aria-valuetext", text);
  }
}

function setSlowHintLevel(level) {
  if (level <= _slowHintLevel) return;
  _slowHintLevel = level;
  var hint = $("v2-import-slow-hint");
  if (!hint) return;
  var copy = SLOW_HINT_COPY[level] || "";
  hint.textContent = copy;
  hint.hidden = !copy;
}

function tickSlowHint() {
  if (!_importStartedAt) return;
  var elapsed = Date.now() - _importStartedAt;
  if (elapsed >= SLOW_JOB_VISION_LONG_MS) setSlowHintLevel(3);
  else if (elapsed >= SLOW_JOB_VISION_MS) setSlowHintLevel(2);
  else if (elapsed >= SLOW_JOB_MS) setSlowHintLevel(1);
}

export function renderImportingPanel(source) {
  captureImportShell();
  var host = $("v2-importing");
  show($("v2-loading"), false);
  show($("v2-headline"), false);
  show($("v2-frame"), false);
  show($("v2-shelf"), false);
  // §9.2 冷启动：无 Import 前壳层背景时铺 demo 静帧（幂等，暖启动不覆盖）。
  renderColdStartBackground(V2.demoManifest || V2.manifest);
  if (!host) return;
  host.replaceChildren();

  var panel = document.createElement("div");
  panel.className = "v2-import-panel";

  var sourceP = document.createElement("p");
  sourceP.className = "v2-import-panel__source";
  sourceP.textContent = "来源 · " + (source || "本机文件夹");
  panel.appendChild(sourceP);

  var title = document.createElement("h2");
  title.className = "v2-import-panel__title";
  title.textContent = "正在生成你的游记画册…";
  panel.appendChild(title);

  var estimate = document.createElement("p");
  estimate.className = "v2-import-panel__estimate";
  estimate.textContent = "自动分章 · 配文 · 排版 · 可离开稍后回来";
  panel.appendChild(estimate);

  var bar = document.createElement("div");
  bar.className = "v2-import-panel__bar";
  bar.id = "v2-import-progress";
  bar.setAttribute("role", "progressbar");
  bar.setAttribute("aria-label", "导入进度");
  bar.setAttribute("aria-valuemin", "0");
  bar.setAttribute("aria-valuemax", "100");
  bar.setAttribute("aria-valuenow", "0");
  bar.setAttribute("aria-valuetext", "准备导入…");
  var fill = document.createElement("div");
  fill.className = "v2-import-panel__bar-fill";
  fill.id = "v2-import-fill";
  bar.appendChild(fill);
  panel.appendChild(bar);

  var stage = document.createElement("p");
  stage.className = "v2-import-panel__stage";
  stage.id = "v2-import-stage";
  stage.textContent = "准备导入…";
  panel.appendChild(stage);

  var slowHint = document.createElement("p");
  slowHint.className = "v2-import-panel__slow-hint";
  slowHint.id = "v2-import-slow-hint";
  slowHint.setAttribute("role", "status");
  slowHint.hidden = true;
  panel.appendChild(slowHint);

  var cancelBtn = document.createElement("button");
  cancelBtn.type = "button";
  cancelBtn.className = "v2-import-panel__cancel";
  cancelBtn.id = "v2-import-cancel";
  cancelBtn.textContent = "取消";
  panel.appendChild(cancelBtn);

  host.appendChild(panel);
  show(host, true);
  V2.state = "Importing";
  _importStartedAt = Date.now();
  _slowHintLevel = 0;
  setV2SkipLinkTarget("v2-import-cancel");
  syncVariantGuard();
  syncAdvancedOptionsLock();
  syncHomeStubBanner();
  cancelBtn.addEventListener("click", cancelImport);
}

function performCancelImport() {
  _gen += 1; // 使进行中的 poll 作废
  var jobId = _activeJobId;
  try {
    sessionStorage.removeItem(SS.activeJobId);
    sessionStorage.removeItem(SS.activePending);
  } catch (e) { /* ignore */ }
  _activeJobId = null;
  if (jobId) {
    postJson("/__travelogue/cancel", { jobId: jobId }).catch(function () {});
  }
  if (typeof studioToast === "function") {
    studioToast("已清理未完成草稿", { duration: 2000 });
  }
  syncVariantGuard();
  if (typeof V2.reroute === "function") V2.reroute();
}

export function cancelImport() {
  var doCancel = function () { performCancelImport(); };
  if (typeof studioModal === "function") {
    studioModal({
      title: "确定取消？",
      body: "取消后将删除未完成的草稿。",
      confirmText: "确定取消",
      cancelText: "继续等待",
      danger: true,
    }).then(function (confirmed) { if (confirmed) doCancel(); });
  } else if (window.confirm("取消后将删除未完成的草稿。确定取消？")) {
    doCancel();
  }
}

function refreshTripsForImportSuccess(result) {
  return fetchTripsFirstPage().then(function (data) {
    V2.trips = data.trips || [];
    V2.tripsTotal = typeof data.total === "number" ? data.total : V2.trips.length;
    V2.isOffline = false;
  }).catch(function () {
    /* 保留已有 trips；FirstSuccess 后 reroute 会再拉 */
  });
}

function pollImport(jobId, gen, source) {
  _activeJobId = jobId;
  if (!_importStartedAt) _importStartedAt = Date.now();
  try {
    sessionStorage.setItem(SS.activeJobId, jobId);
  } catch (e) { /* ignore */ }

  return pollJobUntilDone(jobId, {
    intervalMs: 500,
    shouldAbort: function () { return gen !== _gen; },
    onTick: function (job) {
      if (gen !== _gen) return;
      tickSlowHint();
      if (job.status === "running" || job.status === "queued") {
        var idx = job.stageIndex || 0;
        var count = job.stageCount || 4;
        var rawHint = job.stageHint || "";
        var hint =
          STAGE_HINT_LABELS[rawHint] ||
          rawHint ||
          STAGE_LABELS[job.stage] ||
          "处理中…";
        setStage(hint, count ? (idx / count) * 100 : 0);
      }
    },
  }).then(function (job) {
    if (gen !== _gen) return null;
    _importStartedAt = 0;
    _slowHintLevel = 0;
    var pending = null;
    try {
      var pendingRaw = sessionStorage.getItem(SS.activePending);
      if (pendingRaw) pending = JSON.parse(pendingRaw);
    } catch (e) { /* ignore */ }
    _activeJobId = null;
    try {
      sessionStorage.removeItem(SS.activeJobId);
    } catch (e) { /* ignore */ }
    // L0 resume: only clear pending on success/cancel — keep on failure for
    // 「继续生成本机游记」/ retry (AC-L0G-05).
    if (job.status === "succeeded") {
      try {
        sessionStorage.removeItem(SS.activePending);
      } catch (e) { /* ignore */ }
      setStage("完成", 100);
      var result = job.result || {};
      trackStudioEvent("import_success", {
        tripId: result.tripId || null,
        templateId: result.resolvedTemplateId || null,
        layoutDensity: result.layoutDensity || null,
        layoutDensityEffect: result.layoutDensityEffect || null,
      });
      var viaDemo =
        !!(pending && pending.useDemoAlbum) ||
        String(result.tripId || "") === "demo-album";
      if (viaDemo) {
        trackStudioEvent("ftue_demo_album_success", {
          tripId: result.tripId || null,
          source: "wizard",
        });
      }
      trackImportPhotoCullPref({
        enabled: result.photoCullEnabled !== false,
        mode: (pending && pending.mode) || result.importMode || "quick_share",
        photo_count: result.photoCount,
        layout_eligible_final: result.layoutEligibleCount,
        cull_user_line_present: !!(result.cullUserLine),
        pref_source: readPhotoCullPrefSource(),
      });
      trackImportKeepDupesPref({
        enabled: result.keepNearDuplicates === true,
        mode: (pending && pending.mode) || result.importMode || "quick_share",
        photo_count: result.photoCount,
        assets_written: result.assetsWritten,
        pref_source: readPhotoCullPrefSource(),
      });
      return refreshTripsForImportSuccess(result).then(function () {
        showFirstSuccess({ result: result });
        return job;
      });
    }
    if (job.status === "cancelled") {
      try {
        sessionStorage.removeItem(SS.activePending);
      } catch (e) { /* ignore */ }
      if (typeof V2.reroute === "function") V2.reroute();
      return null;
    }
    var err = job.error || {};
    throw {
      code: err.code,
      message: humanizeError(err.code, err.message),
      recoverableWithStub: err.recoverableWithStub === true,
    };
  });
}

/**
 * 启动一次导入。返回 Promise；调用方（Sheet）负责捕获错误显示。
 * @param {{albumPath:string,title?:string,force?:boolean}} body
 * @param {{source?:string}} [opts]
 */
export function startV2Import(body, opts) {
  opts = opts || {};
  var gen = ++_gen;
  var source = opts.source || "本机文件夹";
  var tpl = readTemplateParams();
  trackStudioEvent("import_start", {
    via: "path",
    surface: "v2_sheet",
    template_mode: tpl.template_mode,
    mode: String((body && body.mode) || "quick_share"),
    layoutDensity: body && body.layoutDensity ? body.layoutDensity : null,
    eligibleCount: body && body.eligibleCount != null ? body.eligibleCount : null,
    photoCullEnabled: body && body.photoCullEnabled !== false,
  });
  trackStudioEvent("template_create_submitted", {
    template_mode: tpl.template_mode,
    template_id: tpl.template_id || null,
  });
  try {
    sessionStorage.setItem(SS.activePending, JSON.stringify(body));
  } catch (e) { /* ignore */ }

  renderImportingPanel(source);

  return withJobBusyRetry(function () {
    return postJson("/__travelogue/import", body);
  }).then(function (res) {
    var data = res.body || {};
    if (res.status === 409 && data.error === "E_DEMO_EXISTS") {
      // FE-FTUE-02 / BLK-07：示例已存在 → 默认打开；次要才覆盖重生成
      if (body && body.useDemoAlbum) {
        return resolveDemoAlbumExists(data).then(function (choice) {
          if (choice === "open") {
            var previewUrl =
              (data.result && data.result.previewUrl) ||
              data.previewUrl ||
              "/demo-album/index.html";
            window.location.href = previewUrl;
            return null;
          }
          if (choice === "regenerate") {
            var forcedDemo = Object.assign({}, body, { force: true });
            return startV2Import(forcedDemo, opts);
          }
          if (typeof V2.reroute === "function") V2.reroute();
          return null;
        });
      }
      var confirmOverwrite = typeof studioModal === "function"
        ? studioModal({
            title: "该游记已存在",
            body: "是否覆盖已有内容？覆盖后无法撤销。",
            confirmText: "覆盖并重新导入",
            cancelText: "取消",
          })
        : Promise.resolve(window.confirm(data.message || "该游记已存在。是否覆盖？"));
      return confirmOverwrite.then(function (ok) {
        if (!ok) {
          if (typeof V2.reroute === "function") V2.reroute();
          return null;
        }
        var forced = Object.assign({}, body, { force: true });
        return startV2Import(forced, opts);
      });
    }
    if (isJobBusyResponse(res)) {
      throw { code: "E_STUDIO_JOB_BUSY", message: humanizeError("E_STUDIO_JOB_BUSY") };
    }
    if (res.status !== 202 || !data.jobId) {
      throw { code: data.error, message: humanizeError(data.error, data.message) };
    }
    return pollImport(data.jobId, gen, source);
  }).catch(function (err) {
    if (gen !== _gen) return; // 已被取消/新导入覆盖
    try { sessionStorage.removeItem(SS.activeJobId); } catch (e) { /* ignore */ }
    _activeJobId = null;
    showImportFailed(err);
    throw err;
  });
}

/**
 * 浏览器目录上传导入（建议 ≤200MB，非硬限制）。
 * 仅保存上传元信息到 sessionStorage；文件对象本身不可跨刷新持久化。
 * @param {FileList|File[]} files
 * @param {{title?:string, source?:string}} [opts]
 */
export function startV2UploadImport(files, opts) {
  opts = opts || {};
  var list = files ? Array.prototype.slice.call(files) : [];
  if (!list.length) return Promise.resolve();
  if (list.length > IMPORT_PHOTO_CAP) {
    var capErr = {
      code: "E_IMPORT_PHOTO_CAP",
      message: "照片过多（最多 " + IMPORT_PHOTO_CAP + " 张），建议先精选后再试。",
    };
    showImportFailed(capErr);
    return Promise.reject(capErr);
  }

  var gen = ++_gen;
  var source = opts.source || "浏览器上传";
  var uploadMode = String(opts.mode || "quick_share");
  var forceStub = !!opts.forceStub;
  try {
    if (sessionStorage.getItem(SS.forceStubNextUpload) === "1") {
      forceStub = true;
      sessionStorage.removeItem(SS.forceStubNextUpload);
    }
  } catch (e) { /* ignore */ }
  trackStudioEvent("import_start", {
    via: "upload",
    surface: "v2_sheet",
    mode: uploadMode,
    photoCullEnabled: opts.photoCullEnabled !== false,
    forceStub: forceStub || undefined,
  });
  try {
    sessionStorage.setItem(SS.activePending, JSON.stringify({
      uploadForm: true,
      fileCount: list.length,
      title: (opts.title || guessUploadTitle(list) || "我的旅途").slice(0, 20),
      mode: uploadMode,
      photoCullEnabled: opts.photoCullEnabled !== false,
      forceStub: forceStub,
    }));
  } catch (e) { /* ignore */ }

  renderImportingPanel(source);
  setStage("上传照片中…", 0);

  var submit = function (force) {
    var form = buildUploadForm(list, {
      title: opts.title,
      place: opts.place,
      placeUserSet: opts.placeUserSet,
      force: !!force,
      forceStub: forceStub,
      photoCullEnabled: opts.photoCullEnabled,
      keepNearDuplicates: opts.keepNearDuplicates,
      mode: uploadMode,
      layoutDensity: opts.layoutDensity,
      template_mode: opts.template_mode || opts.templateMode,
      template_id: opts.template_id || opts.templateId,
      userNotes: opts.userNotes,
      travelNotes: opts.travelNotes,
      dateRange: opts.dateRange,
      featuredDir: opts.featuredDir,
      materialDir: opts.materialDir,
    });
    return withJobBusyRetry(function () {
      return postMultipartImportV2(form, {
        onUploadProgress: function (ev) {
          if (!ev || !ev.lengthComputable) return;
          var pct = Math.max(0, Math.min(22, Math.round((ev.loaded / ev.total) * 22)));
          setStage("上传照片中…", pct);
        },
      });
    });
  };

  return submit(false).then(function (res) {
    var data = res.body || {};
    if (res.status === 409 && data.error === "E_DEMO_EXISTS") {
      var confirmOverwrite = typeof studioModal === "function"
        ? studioModal({
            title: "该游记已存在",
            body: "是否覆盖已有内容？覆盖后无法撤销。",
            confirmText: "覆盖并重新导入",
            cancelText: "取消",
          })
        : Promise.resolve(window.confirm(data.message || "该游记已存在。是否覆盖？"));
      return confirmOverwrite.then(function (ok) {
        if (!ok) {
          if (typeof V2.reroute === "function") V2.reroute();
          return null;
        }
        return submit(true).then(function (retryRes) {
          var retryData = retryRes.body || {};
          if (retryRes.status !== 202 || !retryData.jobId) {
            throw { code: retryData.error, message: humanizeError(retryData.error, retryData.message) };
          }
          return pollImport(retryData.jobId, gen, source);
        });
      });
    }
    if (isJobBusyResponse(res)) {
      throw { code: "E_STUDIO_JOB_BUSY", message: humanizeError("E_STUDIO_JOB_BUSY") };
    }
    if (res.status !== 202 || !data.jobId) {
      throw { code: data.error, message: humanizeError(data.error, data.message) };
    }
    return pollImport(data.jobId, gen, source);
  }).catch(function (err) {
    if (gen !== _gen) return;
    try { sessionStorage.removeItem(SS.activeJobId); } catch (e) { /* ignore */ }
    _activeJobId = null;
    showImportFailed(err);
    throw err;
  });
}

/**
 * 跨页恢复：若存在 activeJobId，渲染 Importing 并续 poll（不闪 Idle）。
 * 返回是否恢复了一次导入。
 */
export function resumeV2ImportIfAny() {
  var jobId = null;
  var pendingRaw = null;
  var pending = null;
  try {
    jobId = sessionStorage.getItem(SS.activeJobId);
    pendingRaw = sessionStorage.getItem(SS.activePending);
  } catch (e) { /* ignore */ }
  try {
    if (pendingRaw) pending = JSON.parse(pendingRaw);
  } catch (e) {
    pending = null;
  }
  if (!jobId) {
    if (pending && pending.uploadForm) {
      try { sessionStorage.removeItem(SS.activePending); } catch (e) { /* ignore */ }
    }
    return false;
  }
  var source = "本机文件夹";
  if (pending && pending.uploadForm) source = "浏览器上传";
  else if (pending && pending.albumPath) source = "本机文件夹";
  var gen = ++_gen;
  renderImportingPanel(source);
  setStage("恢复上次导入…", 0);
  pollImport(jobId, gen, source).catch(function (err) {
    if (gen !== _gen) return;
    showImportFailed(err);
  });
  return true;
}
