/**
 * Import Wizard v3（PRD v3.0.1 · 两步向导 + 智能默认）。
 * 下游出口：startV2Import / startV2UploadImport（import-run.js）。
 */
import { SHEET_FOCUSABLE, UPLOAD_BYTES_SOFT_LIMIT, isDemoTrip } from "../js/constants.js";
import { postJson } from "../js/http.js";
import {
  trackStudioEvent,
  trackImportPhotoCullPref,
  trackImportKeepDupesPref,
  trackImportPhotoKeepMode,
} from "../js/analytics.js";
import { V2, $, show } from "./store.js";
import {
  startV2Import,
  startV2UploadImport,
  buildImportPayload,
  resolveDemoAlbumExists,
} from "./import-run.js";
import {
  isFineSnapshotDirty,
  isPhotoPrefsNonDefault,
  shouldConfirmCloseWizard,
  canLeavePickStep,
  derivePhotoPrefsFromMode,
  resolvePhotoKeepModeFromDraft,
  normalizeEdition,
  parsePortfolioPipelineConfig,
  shouldShowEditionSegment,
  shouldResetEditionToJournal,
  shouldShowHomepagePortfolioEntry,
  isPortfolioLowPhoto,
  portfolioEditionSubline,
  shouldConfirmLowPhoto,
  lowPhotoContinueConfirm,
  shouldShowPageSpec,
  pageSpecSentence,
  approxKeptSentence,
  buildPageCountFields,
} from "./import-wizard-logic.js";
import {
  isRadioNavKey,
  nextRadioId,
  radioTabIndex,
  pageCountChipOptions,
} from "../js/portfolio-edition-logic.js";
import { openHelpDrawer } from "../js/help-drawer.js";

var _open = false;
var _previousFocus = null;
var _trapHandler = null;
var _step = "pick";
var _activeEdition = "journal";
var _pipelineCfg = { enabled: false, homepageEntry: false, minKept: 12 };
var _pipelineHydrated = false;
var _pickInFlight = false;
var _uploadInFlight = false;
var _pendingAlbumPath = null;
var _pendingUploadFiles = null;
var _pendingPhotoCount = null;
var _pageCountSelected = "auto";
var _pageSpecOpen = false;
var _pendingFolderName = null;
var _previewThumbs = [];
var _previewThumbNames = [];
var _previewDateStart = null;
var _previewDateEnd = null;
/** 清点四态：idle | loading | ready | failed | degraded */
var _previewState = "idle";
var _previewGen = 0;
var PREVIEW_TIMEOUT_MS = 8000;
var _importStarted = false;
var _photoKeepModeTouched = false;
var _activeMode = "quick_share";
var PHOTO_KEEP_ALL_RISK_THRESHOLD = 150;
var _drawerOpen = false;
var _wired = false;
var _titleUserEdited = false;
var _dateUserEdited = false;
var _fineEntrySnapshot = null;
var _closeConfirmOpen = false;
var _lowPhotoConfirmOpen = false;
var _fineVisited = false;
var _countHintTrackedKey = null;

var IMPORT_DRAFT_KEY = "travelogue.studio.importDraft";
var IMPORT_MODE_KEY = "travelogue.studio.lastImportMode";
var FIRST_VISIT_KEY = "travelogue.studio.importWizardVisited";
var FIRST_TIP_KEY = "travelogue.studio.importWizardFirstTipDismissed";
var LAYOUT_DENSITY_VALUES = ["balanced", "hero_first", "collage_first"];

function setBackgroundInert(inert) {
  ["v2-bento-hero", "v2-shelf"].forEach(function (id) {
    var el = $(id);
    if (!el) return;
    if (inert) {
      el.setAttribute("inert", "");
      el.setAttribute("aria-hidden", "true");
    } else {
      el.removeAttribute("inert");
      el.removeAttribute("aria-hidden");
    }
  });
}

function setStepError(step, msg) {
  var id = step === "pick" ? "v2-wizard-error-pick"
    : step === "fine" ? "v2-wizard-error-fine"
      : "v2-wizard-error-confirm";
  var el = $(id);
  if (!el) return;
  el.textContent = msg || "";
  show(el, !!msg);
}

function clearErrors() {
  setStepError("pick", "");
  setStepError("confirm", "");
  setStepError("fine", "");
}

function focusableEls(container) {
  return Array.prototype.slice
    .call(container.querySelectorAll(SHEET_FOCUSABLE))
    .filter(function (el) {
      return el.offsetParent !== null || el === document.activeElement;
    });
}

function trapFocus(dialog) {
  _trapHandler = function (e) {
    if (e.key !== "Tab") return;
    var els = focusableEls(dialog);
    if (!els.length) return;
    var first = els[0];
    var last = els[els.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  };
  dialog.addEventListener("keydown", _trapHandler);
}

function releaseTrap(dialog) {
  if (_trapHandler && dialog) dialog.removeEventListener("keydown", _trapHandler);
  _trapHandler = null;
}

function basenameTitle(path) {
  var parts = String(path || "").replace(/[\\/]+$/, "").split(/[\\/]/);
  return (parts[parts.length - 1] || "").slice(0, 20);
}

function safeGet(id) {
  var el = $(id);
  if (!el) return "";
  return String(el.value || "").trim();
}

function safeSet(id, val) {
  var el = $(id);
  if (!el) return;
  el.value = val || "";
}

function readPhotoKeepMode() {
  var checked = document.querySelector('input[name="v2-wizard-photo-keep-mode"]:checked');
  var v = checked ? String(checked.value || "").trim().toLowerCase() : "recommended";
  if (v === "keep_bursts" || v === "keep_all") return v;
  return "recommended";
}

function setPhotoKeepMode(mode) {
  var m = String(mode || "recommended").trim().toLowerCase();
  if (m !== "keep_bursts" && m !== "keep_all") m = "recommended";
  document.querySelectorAll('input[name="v2-wizard-photo-keep-mode"]').forEach(function (input) {
    input.checked = input.value === m;
  });
}

function readPhotoCullEnabled() {
  return derivePhotoPrefsFromMode(readPhotoKeepMode()).photoCullEnabled;
}

function readKeepDupesEnabled() {
  return derivePhotoPrefsFromMode(readPhotoKeepMode()).keepNearDuplicates;
}

function readLayoutDensity() {
  var checked = document.querySelector('input[name="v2-wizard-layout-density"]:checked');
  var v = checked ? String(checked.value || "").trim() : "balanced";
  return LAYOUT_DENSITY_VALUES.indexOf(v) >= 0 ? v : "balanced";
}

function readTemplateParams() {
  var sel = $("v2-wizard-template-mode");
  if (!sel) return { template_mode: "smart" };
  var v = String(sel.value || "smart");
  if (v.indexOf("manual:") === 0) {
    return { template_mode: "manual", template_id: v.slice(7) || "visual-journal" };
  }
  return { template_mode: "smart" };
}

function updatePhotoSummary() {
  var mode = readPhotoKeepMode();
  var line = "照片处理：智能挑选已开启 · 连拍自动择优";
  var warn = false;
  if (mode === "keep_bursts") {
    line = "照片处理：智能挑选已开启 · 已保留连拍与近似照片";
    warn = true;
  } else if (mode === "keep_all") {
    line = "照片处理：全部保留（已跳过挑选 / 连拍去重 / 低清过滤）";
    warn = true;
  }
  var summary = $("v2-wizard-photo-summary");
  var summaryFine = $("v2-wizard-photo-summary-fine");
  [summary, summaryFine].forEach(function (el) {
    if (!el) return;
    el.textContent = line;
    el.classList.toggle("v2-wizard__photo-summary--warn", warn);
  });
}

function updatePhotoKeepModeUi() {
  var risk = $("v2-wizard-photo-keep-all-risk");
  if (risk) {
    var showRisk =
      readPhotoKeepMode() === "keep_all" &&
      _pendingPhotoCount != null &&
      _pendingPhotoCount >= PHOTO_KEEP_ALL_RISK_THRESHOLD;
    show(risk, showRisk);
  }
  updatePhotoSummary();
}

function updateLayoutDensityWarn() {
  var warn = $("v2-wizard-layout-warn");
  if (!warn) return;
  var collage = readLayoutDensity() === "collage_first";
  var fewPhotos = _pendingPhotoCount != null && _pendingPhotoCount < 35;
  show(warn, collage && fewPhotos);
}

function thumbLimit() {
  return window.innerWidth >= 1280 ? 6 : 4;
}

function truncateBasename(name, maxLen) {
  var s = String(name || "").trim();
  if (!s) return "";
  var max = maxLen || 16;
  if (s.length <= max) return s;
  return s.slice(0, Math.max(1, max - 1)) + "…";
}

function updateCountHint() {
  var hint = $("v2-wizard-count-hint");
  if (!hint) return;
  var n = _pendingPhotoCount;
  if (n == null || !Number.isFinite(n)) {
    hint.textContent = "";
    show(hint, false);
    syncPageSpecUi();
    return;
  }
  var bucket = null;
  var text = "";
  if (n < 4) {
    bucket = "few";
    text = "照片偏少，成册可能较短";
  } else if (n > 300) {
    bucket = "many";
    text = "照片较多，预计需要多几分钟";
  }
  if (!bucket) {
    hint.textContent = "";
    show(hint, false);
    syncPageSpecUi();
    return;
  }
  hint.textContent = text;
  show(hint, true);
  var trackKey = String(_pendingAlbumPath || _pendingFolderName || "") + "|" + bucket + "|" + n;
  if (_countHintTrackedKey !== trackKey) {
    _countHintTrackedKey = trackKey;
    trackStudioEvent("photo_count_hint_show", { bucket: bucket, photoCount: n });
  }
  syncPageSpecUi();
}

function renderThumbs(thumbs) {
  var host = $("v2-wizard-thumbs");
  if (!host) return;
  host.replaceChildren();
  var list = (thumbs || []).slice(0, thumbLimit());
  if (!list.length) {
    show(host, false);
    return;
  }
  list.forEach(function (url, idx) {
    var wrap = document.createElement("span");
    wrap.className = "v2-wizard__thumb-wrap";
    var name = truncateBasename(_previewThumbNames[idx] || "");
    var tip = name ? ("第 " + (idx + 1) + " 张 · " + name) : ("第 " + (idx + 1) + " 张");
    wrap.setAttribute("data-tip", tip);
    var img = document.createElement("img");
    img.className = "v2-wizard__thumb";
    img.src = url;
    img.alt = tip;
    img.title = tip;
    img.loading = "lazy";
    img.width = 56;
    img.height = 56;
    img.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
    });
    wrap.appendChild(img);
    host.appendChild(wrap);
  });
  show(host, true);
}

function renderVerifyLine() {
  var line = $("v2-wizard-verify-line");
  var fineCtx = $("v2-wizard-fine-context");
  if (line) line.setAttribute("role", "status");
  var name = _pendingFolderName || basenameTitle(_pendingAlbumPath) || "已选文件夹";
  if (_pendingUploadFiles && _pendingUploadFiles.length) {
    var uploadText = "浏览器上传 · " + _pendingUploadFiles.length + " 张";
    if (line) line.textContent = uploadText;
    if (fineCtx) fineCtx.textContent = uploadText;
    show($("v2-wizard-thumbs"), false);
    return;
  }
  var verifyText = "📁 " + name;
  if (_previewState === "loading" && _pendingAlbumPath) {
    verifyText = "📁 " + name + " · 正在清点照片…";
  } else if (_previewState === "degraded" && _pendingAlbumPath) {
    verifyText = "📁 " + name + " · 照片较多，制作时将自动清点";
  } else if (_previewState === "failed" && _pendingAlbumPath) {
    verifyText = "📁 " + name + " · 未能清点照片，可更换文件夹或直接开始";
  } else if (_previewState === "ready" && _pendingPhotoCount != null) {
    verifyText = "📁 " + name + " · 已清点 " + _pendingPhotoCount + " 张";
  } else if (_pendingPhotoCount != null) {
    verifyText = "📁 " + name + " · 已清点 " + _pendingPhotoCount + " 张";
  }
  if (line) line.textContent = verifyText;
  if (fineCtx && _pendingPhotoCount != null && _previewState === "ready") {
    fineCtx.textContent = "📁 " + name + " · " + _pendingPhotoCount + " 张";
  } else if (fineCtx) {
    fineCtx.textContent = "📁 " + name;
  }
}

function fetchAlbumPreview(albumPath) {
  var gen = ++_previewGen;
  var started = Date.now();
  _previewState = "loading";
  _pendingPhotoCount = null;
  renderVerifyLine();
  updateCountHint();

  var settled = false;
  var timeoutId = setTimeout(function () {
    if (gen !== _previewGen || settled) return;
    _previewState = "degraded";
    _pendingPhotoCount = null;
    _previewThumbs = [];
    _previewThumbNames = [];
    renderVerifyLine();
    updateCountHint();
    trackStudioEvent("preview_timeout", {
      elapsedMs: Date.now() - started,
    });
  }, PREVIEW_TIMEOUT_MS);

  return postJson("/__travelogue/album-preview", { albumPath: albumPath, thumbCount: thumbLimit() })
    .then(function (res) {
      var data = res.body || {};
      if (res.status >= 400 || !data.ok) return null;
      return data;
    })
    .catch(function () { return null; })
    .then(function (data) {
      if (gen !== _previewGen) return;
      settled = true;
      clearTimeout(timeoutId);
      if (!data) {
        if (_previewState !== "degraded") {
          _previewState = "failed";
        }
        _pendingPhotoCount = null;
        _previewThumbs = [];
        _previewThumbNames = [];
        _previewDateStart = null;
        _previewDateEnd = null;
        renderVerifyLine();
        updateCountHint();
        trackStudioEvent("preview_failed", {
          elapsedMs: Date.now() - started,
          degraded: _previewState === "degraded",
        });
        return;
      }
      var n = Number(data.photoCount);
      _pendingPhotoCount = Number.isFinite(n) && n >= 0 ? n : null;
      _previewThumbs = Array.isArray(data.thumbs) ? data.thumbs : [];
      _previewThumbNames = Array.isArray(data.thumbNames) ? data.thumbNames : [];
      if (data.folderName) _pendingFolderName = String(data.folderName);
      _previewDateStart = data.dateStart ? String(data.dateStart) : null;
      _previewDateEnd = data.dateEnd ? String(data.dateEnd) : null;
      _previewState = _pendingPhotoCount != null ? "ready" : "degraded";
      renderVerifyLine();
      renderThumbs(_previewThumbs);
      updateCountHint();
      updatePhotoKeepModeUi();
      updateLayoutDensityWarn();
      syncEditionUi();
      if (_step === "fine") {
        maybePrefillFineFromPreview();
        syncFineSnapshotAfterPrefill();
      }
      updateDuplicateTitleNote();
      trackStudioEvent("preview_loaded", {
        photoCount: _pendingPhotoCount,
        thumbCount: Math.min(_previewThumbs.length, thumbLimit()),
        elapsedMs: Date.now() - started,
        degraded: _previewState === "degraded",
      });
    });
}

function resolveDefaultMode() {
  var firstVisit = false;
  try {
    firstVisit = !localStorage.getItem(FIRST_VISIT_KEY);
  } catch (_e) { /* ignore */ }
  if (firstVisit) return { mode: "quick_share", source: "first_visit" };
  var remembered = "";
  try {
    remembered = String(localStorage.getItem(IMPORT_MODE_KEY) || "").trim();
  } catch (_e) { /* ignore */ }
  if (remembered === "fine_craft") return { mode: "fine_craft", source: "remembered" };
  return { mode: "quick_share", source: "default" };
}

function setActiveMode(mode, source) {
  _activeMode = mode === "fine_craft" ? "fine_craft" : "quick_share";
  var quick = $("v2-wizard-mode-quick");
  var fine = $("v2-wizard-mode-fine");
  if (quick) {
    quick.setAttribute("aria-checked", _activeMode === "quick_share" ? "true" : "false");
    quick.tabIndex = _activeMode === "quick_share" ? 0 : -1;
  }
  if (fine) {
    fine.setAttribute("aria-checked", _activeMode === "fine_craft" ? "true" : "false");
    fine.tabIndex = _activeMode === "fine_craft" ? 0 : -1;
  }
  updateStartLabel();
  if (source) {
    trackStudioEvent("import_mode_view", { mode: _activeMode, source: source });
  }
}

function setActiveEdition(edition, source) {
  var next = normalizeEdition(edition);
  if (
    next === "portfolio" &&
    shouldConfirmLowPhoto(
      _pendingPhotoCount,
      _pipelineCfg.minKept,
      source,
      _activeEdition
    )
  ) {
    requestLowPhotoContinue(next);
    return;
  }
  applyEditionChoice(next, source);
}

function requestLowPhotoContinue(next) {
  if (_lowPhotoConfirmOpen) return;
  var copy = lowPhotoContinueConfirm(_pipelineCfg.minKept);
  if (typeof studioModal === "function") {
    _lowPhotoConfirmOpen = true;
    studioModal({
      title: copy.title,
      body: copy.body,
      confirmText: copy.confirmText,
      cancelText: copy.cancelText,
    }).then(function (ok) {
      _lowPhotoConfirmOpen = false;
      if (ok === true || ok === "confirm") applyEditionChoice(next, "user");
    });
    return;
  }
  if (window.confirm(copy.body)) applyEditionChoice(next, "user");
}

function focusEditionRadio(id) {
  var el = $(id === "portfolio" ? "v2-wizard-edition-portfolio" : "v2-wizard-edition-journal");
  if (el && typeof el.focus === "function") el.focus();
}

function applyEditionChoice(next, source) {
  _activeEdition = normalizeEdition(next);
  syncEditionUi();
  updateStartLabel();
  saveDraft();
  if (source === "user") focusEditionRadio(_activeEdition);
}

function syncEditionUi() {
  var row = $("v2-wizard-edition");
  var journal = $("v2-wizard-edition-journal");
  var portfolio = $("v2-wizard-edition-portfolio");
  var show = shouldShowEditionSegment(_pipelineCfg);
  if (row) row.hidden = !show;
  var homeLink = $("v2-cta-portfolio");
  if (homeLink) homeLink.hidden = !shouldShowHomepagePortfolioEntry(_pipelineCfg);
  if (shouldResetEditionToJournal(_pipelineCfg, _pipelineHydrated)) {
    _activeEdition = "journal";
  }
  var low = isPortfolioLowPhoto(_pendingPhotoCount, _pipelineCfg.minKept);
  if (journal) {
    journal.setAttribute("aria-checked", _activeEdition === "journal" ? "true" : "false");
    journal.tabIndex = radioTabIndex(_activeEdition, "journal");
  }
  if (portfolio) {
    portfolio.setAttribute("aria-checked", _activeEdition === "portfolio" ? "true" : "false");
    portfolio.tabIndex = radioTabIndex(_activeEdition, "portfolio");
    portfolio.classList.toggle("is-dim", low);
    var sub = portfolio.querySelector("span");
    if (sub) sub.textContent = portfolioEditionSubline(low);
  }
  var desc = $("v2-wizard-mode-quick-desc");
  if (desc) {
    desc.textContent = _activeEdition === "portfolio"
      ? "按杂志页编排，做完能点开翻。发群请选游记。"
      : "优先出微信长图，适合马上分享";
  }
  syncPageSpecUi();
}

function syncPageSpecUi() {
  var host = $("v2-wizard-page-spec");
  var line = $("v2-wizard-page-spec-line");
  var detail = $("v2-wizard-page-spec-detail");
  var chipsHost = $("v2-wizard-page-spec-chips");
  var toggle = $("v2-wizard-page-spec-toggle");
  var show = shouldShowPageSpec(_activeEdition, _pipelineCfg);
  if (host) host.hidden = !show;
  if (!show) {
    _pageCountSelected = "auto";
    _pageSpecOpen = false;
    if (detail) {
      detail.textContent = "";
      detail.hidden = true;
    }
    return;
  }
  if (line) {
    line.textContent = pageSpecSentence(
      _pendingPhotoCount,
      _pipelineCfg.pageCountChipDetails
    );
  }
  if (detail) {
    var approx = approxKeptSentence(
      _pendingPhotoCount,
      _pipelineCfg.keptEstimateRatio
    );
    detail.textContent = approx;
    detail.hidden = !_pageSpecOpen || !approx;
  }
  if (toggle) {
    toggle.setAttribute("aria-expanded", _pageSpecOpen ? "true" : "false");
    toggle.textContent = _pageSpecOpen ? "收起厚度选项" : "换一本更厚 / 更薄";
  }
  if (chipsHost) {
    chipsHost.hidden = !_pageSpecOpen;
    if (_pageSpecOpen) renderWizardPageChips(chipsHost);
  }
}

function renderWizardPageChips(row) {
  if (!row) return;
  row.innerHTML = "";
  pageCountChipOptions(_pipelineCfg.pageCountChipDetails || []).forEach(function (opt) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "v2-wizard__page-spec-chip";
    btn.setAttribute("data-page-count", opt.id);
    btn.setAttribute("aria-pressed", opt.id === _pageCountSelected ? "true" : "false");
    btn.textContent = opt.id === "auto" ? opt.label : (opt.hint || (opt.label + " 页"));
    if (opt.id === _pageCountSelected) btn.classList.add("is-on");
    btn.addEventListener("click", function () {
      _pageCountSelected = opt.id;
      syncPageSpecUi();
    });
    row.appendChild(btn);
  });
}

function hydratePortfolioPipeline() {
  return fetch("/__travelogue/config", { headers: { Accept: "application/json" } })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (data) {
      _pipelineCfg = parsePortfolioPipelineConfig(data && data.studio);
      _pipelineHydrated = true;
      syncEditionUi();
    })
    .catch(function () {
      // Keep last successful config. Do not mark hydrated on failure —
      // otherwise a pending homepage/draft portfolio choice is wiped.
      syncEditionUi();
    });
}

function updateStartLabel() {
  var start = $("v2-wizard-start");
  if (!start) return;
  if (_pendingUploadFiles && _pendingUploadFiles.length) {
    start.textContent = "开始上传";
    return;
  }
  if (_activeMode === "fine_craft") {
    start.textContent = _fineVisited ? "定制画册细节 →" : "填写细节 →";
  } else if (_activeEdition === "portfolio") {
    start.textContent = "开始制作作品集 →";
  } else {
    start.textContent = "开始制作 →";
  }
}

function syncChipPressedState() {
  var notes = safeGet("v2-wizard-user-notes");
  document.querySelectorAll(".v2-wizard__chip[data-fill='v2-wizard-user-notes']").forEach(function (chip) {
    var text = String(chip.textContent || "").trim();
    chip.setAttribute("aria-pressed", notes && notes === text ? "true" : "false");
  });
}

function findDuplicateTripTitle(title) {
  var needle = String(title || "").trim();
  if (!needle) return null;
  var trips = (typeof V2 !== "undefined" && V2.trips) ? V2.trips : [];
  for (var i = 0; i < trips.length; i++) {
    var t = trips[i];
    if (!t || isDemoTrip(t)) continue;
    var existing = String(t.title || "").trim();
    if (existing && existing === needle) return existing;
  }
  return null;
}

function updateDuplicateTitleNote() {
  var title = "";
  if (_titleUserEdited) title = safeGet("v2-wizard-trip-title");
  if (!title) {
    title = _pendingFolderName || safeGet("v2-wizard-trip-title") || basenameTitle(_pendingAlbumPath);
  }
  var match = findDuplicateTripTitle(title);
  var text = match ? ("将新建一本，不会覆盖《" + match + "》") : "";
  ["v2-wizard-dup-note", "v2-wizard-dup-note-fine"].forEach(function (id) {
    var el = $(id);
    if (!el) return;
    el.textContent = text;
    show(el, !!text);
  });
}

function shouldShowFirstTip() {
  try {
    return !localStorage.getItem(FIRST_TIP_KEY);
  } catch (_e) {
    return false;
  }
}

function dismissFirstTip() {
  try { localStorage.setItem(FIRST_TIP_KEY, "1"); } catch (_e) { /* ignore */ }
  var tip = $("v2-wizard-first-tip");
  if (tip) show(tip, false);
}

function refreshFirstTip() {
  var tip = $("v2-wizard-first-tip");
  if (!tip) return;
  show(tip, _step === "pick" && shouldShowFirstTip());
}

function showPanel(step) {
  _step = step;
  ["pick", "confirm", "fine"].forEach(function (s) {
    var panel = $("v2-wizard-step-" + (s === "fine" ? "fine" : s));
    if (panel) show(panel, s === step);
  });
  var dialog = $("v2-import-wizard");
  if (dialog) {
    var titleId = step === "pick" ? "v2-wizard-title-pick"
      : step === "fine" ? "v2-wizard-title-fine"
        : "v2-wizard-title-confirm";
    dialog.setAttribute("aria-labelledby", titleId);
  }
  trackStudioEvent("wizard_step_view", { step: step === "fine" ? "fine" : step });
}

function toggleDrawer(open) {
  _drawerOpen = open === true;
  var drawer = $("v2-wizard-photo-drawer");
  if (drawer) show(drawer, _drawerOpen);
  ["v2-wizard-photo-adjust", "v2-wizard-photo-adjust-fine"].forEach(function (id) {
    var btn = $(id);
    if (btn) btn.setAttribute("aria-expanded", _drawerOpen ? "true" : "false");
  });
}

function expandFallbackImport() {
  var details = $("v2-wizard-more-import");
  if (details) details.open = true;
  var pathInput = $("v2-wizard-album-path");
  var upload = $("v2-wizard-album-upload");
  if (pathInput) {
    try { pathInput.focus(); } catch (_e) { /* ignore */ }
  } else if (upload) {
    try { upload.focus(); } catch (_e) { /* ignore */ }
  }
}

/** 换夹后清掉会污染新导入的预填字段（名称 / 日期）。 */
function resetPrefillableFieldsForNewFolder() {
  safeSet("v2-wizard-trip-title", "");
  safeSet("v2-wizard-date-start", "");
  safeSet("v2-wizard-date-end", "");
  _titleUserEdited = false;
  _dateUserEdited = false;
  _countHintTrackedKey = null;
  _fineEntrySnapshot = null;
}

function maybePrefillFineFromPreview() {
  if (!_titleUserEdited) {
    var name = _pendingFolderName || basenameTitle(_pendingAlbumPath);
    if (name) safeSet("v2-wizard-trip-title", name.slice(0, 20));
    else safeSet("v2-wizard-trip-title", "");
  }
  if (!_dateUserEdited) {
    safeSet("v2-wizard-date-start", _previewDateStart || "");
    safeSet("v2-wizard-date-end", _previewDateEnd || "");
  }
}

/** preview 异步回填后，只同步系统预填字段进快照，避免误报 dirty。 */
function syncFineSnapshotAfterPrefill() {
  if (!_fineEntrySnapshot || _step !== "fine") return;
  var cur = snapshotFineFields();
  if (!_titleUserEdited) _fineEntrySnapshot.title = cur.title;
  if (!_dateUserEdited) {
    _fineEntrySnapshot.dateStart = cur.dateStart;
    _fineEntrySnapshot.dateEnd = cur.dateEnd;
  }
}

function snapshotFineFields() {
  return {
    title: safeGet("v2-wizard-trip-title"),
    place: safeGet("v2-wizard-trip-place"),
    dateStart: safeGet("v2-wizard-date-start"),
    dateEnd: safeGet("v2-wizard-date-end"),
    userNotes: safeGet("v2-wizard-user-notes"),
    travelNotes: safeGet("v2-wizard-travel-notes"),
    featuredDir: safeGet("v2-wizard-featured-dir"),
    materialDir: safeGet("v2-wizard-material-dir"),
    layoutDensity: readLayoutDensity(),
    templateMode: (function () {
      var sel = $("v2-wizard-template-mode");
      return sel ? String(sel.value || "smart") : "smart";
    })(),
    planFileName: (function () {
      var input = $("v2-wizard-plan-file");
      if (!input || !input.files || !input.files[0]) return "";
      return String(input.files[0].name || "");
    })(),
  };
}

function fineFieldsDirty() {
  return isFineSnapshotDirty(_fineEntrySnapshot, snapshotFineFields());
}

function photoPrefsNonDefault() {
  return isPhotoPrefsNonDefault({
    photoKeepMode: readPhotoKeepMode(),
    photoCullEnabled: readPhotoCullEnabled(),
    keepNearDuplicates: readKeepDupesEnabled(),
  });
}

function shouldConfirmClose() {
  return shouldConfirmCloseWizard({
    step: _step,
    fineDirty: fineFieldsDirty(),
    photoPrefsNonDefault: photoPrefsNonDefault(),
  });
}

function clearFineDraftFields() {
  safeSet("v2-wizard-trip-title", "");
  safeSet("v2-wizard-trip-place", "");
  safeSet("v2-wizard-date-start", "");
  safeSet("v2-wizard-date-end", "");
  safeSet("v2-wizard-user-notes", "");
  safeSet("v2-wizard-travel-notes", "");
  safeSet("v2-wizard-featured-dir", "");
  safeSet("v2-wizard-material-dir", "");
  var plan = $("v2-wizard-plan-file");
  if (plan) plan.value = "";
  var planName = $("v2-wizard-plan-file-name");
  if (planName) planName.textContent = "";
  document.querySelectorAll('input[name="v2-wizard-layout-density"]').forEach(function (input) {
    input.checked = input.value === "balanced";
  });
  var sel = $("v2-wizard-template-mode");
  if (sel) sel.value = "smart";
  setPhotoKeepMode("recommended");
  _photoKeepModeTouched = false;
  _titleUserEdited = false;
  _dateUserEdited = false;
  _fineEntrySnapshot = null;
  updatePhotoKeepModeUi();
  try { sessionStorage.removeItem(IMPORT_DRAFT_KEY); } catch (_e) { /* ignore */ }
}

function requestCloseWizard(reason) {
  if (_closeConfirmOpen) return;
  if (!shouldConfirmClose()) {
    closeImportWizard(reason || "dismiss");
    return;
  }
  _closeConfirmOpen = true;
  var run = function (action) {
    _closeConfirmOpen = false;
    trackStudioEvent("close_confirm", { action: action });
    if (action === "keep") {
      saveDraft();
      closeImportWizard(reason || "dismiss", { persistDraft: false });
    } else if (action === "discard") {
      // 丢弃须清 pending + 回 Step1，且关闭时不再 saveDraft（否则会把路径写回草稿）
      clearFineDraftFields();
      _fineVisited = false;
      setActiveMode("quick_share", null);
      goToStep1(true);
      closeImportWizard(reason || "dismiss", { persistDraft: false });
    }
  };
  if (typeof studioModal === "function") {
    studioModal({
      title: "保留这次的填写？",
      body: "关闭后可从首页再次打开导入向导。选择保留会记住本次填写；丢弃则清空相关草稿。",
      confirmText: "保留并关闭",
      secondaryText: "丢弃并关闭",
      cancelText: "继续填写",
      stacked: true,
    }).then(function (result) {
      if (result === "confirm" || result === true) run("keep");
      else if (result === "secondary") run("discard");
      else {
        _closeConfirmOpen = false;
        trackStudioEvent("close_confirm", { action: "cancel" });
      }
    });
    return;
  }
  // studioModal 不可用时：二次 confirm 覆盖 keep / discard / cancel
  if (window.confirm("保留这次的填写并关闭？\n确定=保留并关闭，取消=查看其他选项")) {
    run("keep");
  } else if (window.confirm("丢弃这次的填写并关闭？\n确定=丢弃并关闭，取消=继续填写")) {
    run("discard");
  } else {
    _closeConfirmOpen = false;
    trackStudioEvent("close_confirm", { action: "cancel" });
  }
}

function goToStep1(clearPending) {
  if (clearPending !== false) {
    _pendingAlbumPath = null;
    _pendingUploadFiles = null;
    _pendingPhotoCount = null;
    _pageCountSelected = "auto";
    _pageSpecOpen = false;
    _pendingFolderName = null;
    _previewThumbs = [];
    _previewThumbNames = [];
    _previewDateStart = null;
    _previewDateEnd = null;
  }
  toggleDrawer(false);
  clearErrors();
  updateCountHint();
  showPanel("pick");
  refreshFirstTip();
  var pick = $("v2-wizard-pick");
  if (pick) pick.focus();
}

function syncStorageTrustNotes() {
  var uploadNote = $("v2-wizard-storage-upload-note");
  var isUpload = !!(
    _pendingUploadFiles && _pendingUploadFiles.length
  );
  if (uploadNote) {
    uploadNote.hidden = !isUpload;
  }
  return Promise.resolve();
}

function goToStep2(opts) {
  opts = opts || {};
  clearErrors();
  toggleDrawer(false);
  if (!opts.modeSource) {
    var def = resolveDefaultMode();
    setActiveMode(def.mode, def.source);
  }
  renderVerifyLine();
  renderThumbs(_previewThumbs);
  updateCountHint();
  updatePhotoKeepModeUi();
  updateStartLabel();
  syncEditionUi();
  showPanel("confirm");
  refreshFirstTip();
  updateDuplicateTitleNote();
  syncStorageTrustNotes();
  if (_pendingAlbumPath && _pendingPhotoCount == null && !_pendingUploadFiles) {
    fetchAlbumPreview(_pendingAlbumPath);
  }
  if (!_titleUserEdited) {
    var titleInput = $("v2-wizard-trip-title");
    if (titleInput && _pendingAlbumPath) {
      var nextTitle = (_pendingFolderName || basenameTitle(_pendingAlbumPath) || "").slice(0, 20);
      titleInput.value = nextTitle;
    }
  }
  if (!_dateUserEdited && !_previewDateStart && !_previewDateEnd) {
    safeSet("v2-wizard-date-start", "");
    safeSet("v2-wizard-date-end", "");
  }
  var start = $("v2-wizard-start");
  if (start) start.focus();
}

function goToStep2b() {
  clearErrors();
  toggleDrawer(false);
  _fineVisited = true;
  maybePrefillFineFromPreview();
  renderVerifyLine();
  updatePhotoSummary();
  syncChipPressedState();
  updateDuplicateTitleNote();
  var advanced = $("v2-wizard-advanced");
  if (advanced) advanced.open = false;
  showPanel("fine");
  refreshFirstTip();
  _fineEntrySnapshot = snapshotFineFields();
  var titleInput = $("v2-wizard-trip-title");
  if (titleInput) titleInput.focus();
}

function afterFolderPicked(albumPath, via) {
  _pendingAlbumPath = albumPath;
  _pendingUploadFiles = null;
  _pendingFolderName = basenameTitle(albumPath);
  _pendingPhotoCount = null;
  _previewState = "loading";
  _previewThumbs = [];
  _previewThumbNames = [];
  _previewDateStart = null;
  _previewDateEnd = null;
  resetPrefillableFieldsForNewFolder();
  trackStudioEvent("pick_folder", { via: via || "native" });
  trackStudioEvent("folder_picked", { via: via || "native" });
  goToStep2({});
  fetchAlbumPreview(albumPath);
  saveDraft();
}

function saveDraft() {
  var draft = {
    wizardStep: _step,
    mode: _activeMode,
    albumPath: _pendingAlbumPath || "",
    title: safeGet("v2-wizard-trip-title"),
    place: safeGet("v2-wizard-trip-place"),
    dateStart: safeGet("v2-wizard-date-start"),
    dateEnd: safeGet("v2-wizard-date-end"),
    userNotes: safeGet("v2-wizard-user-notes"),
    travelNotes: safeGet("v2-wizard-travel-notes"),
    featuredDir: safeGet("v2-wizard-featured-dir"),
    materialDir: safeGet("v2-wizard-material-dir"),
    layoutDensity: readLayoutDensity(),
    photoKeepMode: readPhotoKeepMode(),
    photoCullEnabled: readPhotoCullEnabled(),
    photoKeepModeTouched: _photoKeepModeTouched,
    keepNearDuplicates: readKeepDupesEnabled(),
    photoCount: _pendingPhotoCount,
    pageCountSelected: _pageCountSelected,
    pageSpecOpen: _pageSpecOpen,
    edition: _activeEdition === "portfolio" ? "portfolio" : undefined,
    planFileName: (function () {
      var input = $("v2-wizard-plan-file");
      if (!input || !input.files || !input.files[0]) return "";
      return String(input.files[0].name || "");
    })(),
  };
  try {
    sessionStorage.setItem(IMPORT_DRAFT_KEY, JSON.stringify(draft));
    sessionStorage.setItem(IMPORT_MODE_KEY, _activeMode);
  } catch (_e) { /* ignore */ }
}

function readDraft() {
  try {
    var raw = sessionStorage.getItem(IMPORT_DRAFT_KEY);
    if (!raw) return {};
    var parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch (_e) {
    return {};
  }
}

function restoreDraftFields(draft) {
  safeSet("v2-wizard-trip-title", draft.title || "");
  safeSet("v2-wizard-trip-place", draft.place || "");
  safeSet("v2-wizard-date-start", draft.dateStart || "");
  safeSet("v2-wizard-date-end", draft.dateEnd || "");
  safeSet("v2-wizard-user-notes", draft.userNotes || "");
  safeSet("v2-wizard-travel-notes", draft.travelNotes || "");
  safeSet("v2-wizard-featured-dir", draft.featuredDir || "");
  safeSet("v2-wizard-material-dir", draft.materialDir || "");
  _titleUserEdited = !!(draft.title && String(draft.title).trim());
  _dateUserEdited = !!(draft.dateStart || draft.dateEnd);
  setPhotoKeepMode(resolvePhotoKeepModeFromDraft(draft));
  _photoKeepModeTouched = !!(draft.photoKeepModeTouched || draft.photoCullTouched || draft.keepDupesTouched);
  _pendingPhotoCount = typeof draft.photoCount === "number" ? draft.photoCount : null;
  _pageCountSelected = draft.pageCountSelected ? String(draft.pageCountSelected) : "auto";
  _pageSpecOpen = draft.pageSpecOpen === true;
  _previewState = _pendingPhotoCount != null ? "ready" : "idle";
  var density = draft.layoutDensity || "balanced";
  document.querySelectorAll('input[name="v2-wizard-layout-density"]').forEach(function (input) {
    input.checked = input.value === density;
  });
  updateLayoutDensityWarn();
  updatePhotoKeepModeUi();
  syncPageSpecUi();
}

function validateFineFields() {
  var start = safeGet("v2-wizard-date-start");
  var end = safeGet("v2-wizard-date-end");
  if (start && !/^\d{4}-\d{2}-\d{2}$/.test(start)) return "开始日期格式无效，请使用 YYYY-MM-DD";
  if (end && !/^\d{4}-\d{2}-\d{2}$/.test(end)) return "结束日期格式无效，请使用 YYYY-MM-DD";
  if (start && end && start > end) return "开始日期不能晚于结束日期";
  return "";
}

function readPlanFileText() {
  var input = $("v2-wizard-plan-file");
  if (!input || !input.files || !input.files[0]) return Promise.resolve(null);
  var file = input.files[0];
  var name = String(file.name || "");
  var lower = name.toLowerCase();
  if (!(lower.endsWith(".txt") || lower.endsWith(".md"))) {
    return Promise.reject(new Error("计划文件仅支持 .txt / .md"));
  }
  if ((file.size || 0) > 32 * 1024) {
    return Promise.reject(new Error("计划文件不能超过 32KB"));
  }
  return new Promise(function (resolve, reject) {
    var reader = new FileReader();
    reader.onload = function () {
      resolve(String(reader.result || "").trim() || null);
    };
    reader.onerror = function () { reject(new Error("读取计划文件失败，请重试")); };
    reader.readAsText(file, "utf-8");
  });
}

function buildWizardPayload() {
  var title = safeGet("v2-wizard-trip-title");
  var body = buildImportPayload(_pendingAlbumPath, title, {
    titleUserSet: !!_titleUserEdited && !!title,
  });
  body.mode = _activeMode;
  if (_activeEdition === "portfolio") body.edition = "portfolio";
  Object.assign(body, readTemplateParams());
  var place = safeGet("v2-wizard-trip-place");
  var userNotes = safeGet("v2-wizard-user-notes");
  var travelNotes = safeGet("v2-wizard-travel-notes");
  var dateStart = safeGet("v2-wizard-date-start");
  var dateEnd = safeGet("v2-wizard-date-end");
  var featuredDir = safeGet("v2-wizard-featured-dir");
  var materialDir = safeGet("v2-wizard-material-dir");
  if (_activeMode === "fine_craft") {
    var err = validateFineFields();
    if (err) {
      setStepError("fine", err);
      return null;
    }
  }
  if (place) body.place = place;
  if (userNotes) body.userNotes = userNotes.slice(0, 200);
  if (travelNotes) body.travelNotes = travelNotes.slice(0, 500);
  if (dateStart || dateEnd) {
    body.dateRange = { source: "user" };
    if (dateStart) body.dateRange.start = dateStart;
    if (dateEnd) body.dateRange.end = dateEnd;
  }
  if (featuredDir) body.featuredDir = featuredDir;
  if (materialDir) body.materialDir = materialDir;
  if (_activeMode === "fine_craft") body.layoutDensity = readLayoutDensity();
  body.photoKeepMode = readPhotoKeepMode();
  body.photoCullEnabled = readPhotoCullEnabled();
  body.keepNearDuplicates = readKeepDupesEnabled();
  if (_pendingPhotoCount != null) body.eligibleCount = _pendingPhotoCount;
  Object.assign(body, buildPageCountFields(_activeEdition, _pageCountSelected));
  return body;
}

function markVisited() {
  try { localStorage.setItem(FIRST_VISIT_KEY, "1"); } catch (_e) { /* ignore */ }
}

function pickFolder() {
  if (_pickInFlight) {
    if (typeof studioToast === "function") {
      studioToast("文件夹选择器已打开，请在其窗口中操作", { duration: 2200 });
    }
    return;
  }
  _pickInFlight = true;
  setStepError("pick", "");
  var pickToast = typeof studioToast === "function"
    ? studioToast("正在打开文件夹选择器…", { duration: 0 })
    : null;
  postJson("/__travelogue/pick-folder", {})
    .then(function (res) {
      var data = res.body || {};
      if (data.cancelled) return;
      if (res.status >= 400 || data.ok === false || !data.albumPath) {
        var msg = data.message || data.detail ||
          "无法打开本机选文件夹。请在「其他导入方式」粘贴路径。";
        setStepError("pick", msg);
        expandFallbackImport();
        return;
      }
      afterFolderPicked(data.albumPath, "native");
    })
    .catch(function () {
      setStepError("pick", "无法连接选文件夹服务。请粘贴路径，或确认 Studio 正在运行。");
      expandFallbackImport();
    })
    .finally(function () {
      if (pickToast && pickToast.parentNode) pickToast.parentNode.removeChild(pickToast);
      _pickInFlight = false;
    });
}

function submitWithPath() {
  var path = safeGet("v2-wizard-album-path");
  if (!path) {
    setStepError("pick", "请填写照片文件夹路径，例如 D:\\Photos\\Kyoto2025");
    expandFallbackImport();
    return;
  }
  afterFolderPicked(path, "path");
}

function estimateUploadBytes(files) {
  var total = 0;
  for (var i = 0; i < files.length; i++) total += files[i].size || 0;
  return total;
}

function formatBytes(bytes) {
  if (!bytes || bytes <= 0) return "0B";
  var units = ["B", "KB", "MB", "GB"];
  var val = bytes;
  var idx = 0;
  while (val >= 1024 && idx < units.length - 1) {
    val /= 1024;
    idx += 1;
  }
  return (val >= 10 || idx === 0 ? Math.round(val) : Math.round(val * 10) / 10) + units[idx];
}

function confirmLargeUpload(files) {
  var bytes = estimateUploadBytes(files);
  if (bytes <= UPLOAD_BYTES_SOFT_LIMIT) return Promise.resolve(true);
  var body =
    "已选约 " + formatBytes(bytes) + "（" + files.length + " 个文件）。" +
    " 建议总量≤200MB，超过后可能变慢或失败。";
  if (typeof studioModal === "function") {
    return studioModal({
      title: "照片总量较大",
      body: body,
      confirmText: "仍要上传",
      cancelText: "改用文件夹",
    });
  }
  return Promise.resolve(window.confirm(body + "\n\n仍要上传？"));
}

function showUploadConfirm(files) {
  _pendingAlbumPath = null;
  _pendingUploadFiles = files ? Array.prototype.slice.call(files) : [];
  _pendingPhotoCount = _pendingUploadFiles.length;
  _pendingFolderName = null;
  _previewThumbs = [];
  setActiveMode("quick_share", "default");
  goToStep2({ modeSource: true });
  saveDraft();
}

function handleUploadInput() {
  if (_uploadInFlight) return;
  var input = $("v2-wizard-album-upload");
  var files = input && input.files ? Array.prototype.slice.call(input.files) : [];
  if (!files.length) return;
  _uploadInFlight = true;
  setStepError("pick", "");
  confirmLargeUpload(files).then(function (proceed) {
    if (proceed) showUploadConfirm(files);
    else expandFallbackImport();
  }).finally(function () {
    if (input) input.value = "";
    _uploadInFlight = false;
  });
}

function startUploadFromWizard() {
  var files = _pendingUploadFiles ? Array.prototype.slice.call(_pendingUploadFiles) : [];
  if (!files.length) {
    setStepError("confirm", "请先选择要上传的照片");
    return;
  }
  if (_activeMode === "fine_craft") {
    var fineErr = validateFineFields();
    if (fineErr) {
      setStepError("fine", fineErr);
      return;
    }
  }
  var title = safeGet("v2-wizard-trip-title");
  var place = safeGet("v2-wizard-trip-place");
  var userNotes = safeGet("v2-wizard-user-notes");
  var travelNotes = safeGet("v2-wizard-travel-notes");
  var dateStart = safeGet("v2-wizard-date-start");
  var dateEnd = safeGet("v2-wizard-date-end");
  var featuredDir = safeGet("v2-wizard-featured-dir");
  var materialDir = safeGet("v2-wizard-material-dir");
  var tpl = readTemplateParams();
  var trimmedTitle = (title || "").trim();
  var uploadOpts = {
    source: "浏览器上传",
    mode: _activeMode,
    edition: _activeEdition === "portfolio" ? "portfolio" : undefined,
    title: trimmedTitle || undefined,
    titleUserSet: !!_titleUserEdited && !!trimmedTitle,
    place: place || "旅途",
    placeUserSet: !!place,
    photoKeepMode: readPhotoKeepMode(),
    photoCullEnabled: readPhotoCullEnabled(),
    keepNearDuplicates: readKeepDupesEnabled(),
    template_mode: tpl.template_mode,
    template_id: tpl.template_id,
  };
  if (userNotes) uploadOpts.userNotes = userNotes.slice(0, 200);
  if (travelNotes) uploadOpts.travelNotes = travelNotes.slice(0, 500);
  if (dateStart || dateEnd) {
    uploadOpts.dateRange = { source: "user" };
    if (dateStart) uploadOpts.dateRange.start = dateStart;
    if (dateEnd) uploadOpts.dateRange.end = dateEnd;
  }
  if (featuredDir) uploadOpts.featuredDir = featuredDir;
  if (materialDir) uploadOpts.materialDir = materialDir;
  if (_activeMode === "fine_craft") uploadOpts.layoutDensity = readLayoutDensity();
  Object.assign(uploadOpts, buildPageCountFields(_activeEdition, _pageCountSelected));

  markVisited();
  try { localStorage.setItem(IMPORT_MODE_KEY, _activeMode); } catch (_e) { /* ignore */ }
  _importStarted = true;
  _pendingUploadFiles = null;
  // 已开始制作：清草稿，避免完成后「再新建」仍停在旧文件夹确认页
  try { sessionStorage.removeItem(IMPORT_DRAFT_KEY); } catch (_e2) { /* ignore */ }
  closeImportWizard("start_upload", { persistDraft: false });
  if (typeof studioToast === "function") {
    studioToast("将新建一本画册 · 已选择 " + files.length + " 张", { duration: 2200 });
  }
  return startV2UploadImport(files, uploadOpts).catch(function () { /* import-run handles */ });
}

function startImportFromWizard() {
  if (_pendingUploadFiles && _pendingUploadFiles.length) {
    return startUploadFromWizard();
  }
  if (!canLeavePickStep(_pendingAlbumPath)) {
    setStepError(_step === "fine" ? "fine" : "confirm", "请先选择照片文件夹");
    return;
  }
  var body = buildWizardPayload();
  if (!body) return;
  readPlanFileText().then(function (planText) {
    if (planText) body.planText = planText;
    markVisited();
    try { localStorage.setItem(IMPORT_MODE_KEY, _activeMode); } catch (_e) { /* ignore */ }
    _importStarted = true;
    // 已开始制作：清草稿，避免完成后「再新建」仍停在旧文件夹确认页
    try { sessionStorage.removeItem(IMPORT_DRAFT_KEY); } catch (_e2) { /* ignore */ }
    closeImportWizard("start", { persistDraft: false });
    if (typeof studioToast === "function") {
      var nPhotos =
        (body && typeof body.eligibleCount === "number" && body.eligibleCount) ||
        (body && typeof body.photoCount === "number" && body.photoCount) ||
        0;
      var toastMsg =
        _activeMode === "fine_craft"
          ? "已按个性化定制画册启动"
          : nPhotos > 0
            ? "将新建一本画册 · 已选择 " + nPhotos + " 张"
            : "将新建一本画册 · 开始制作";
      studioToast(toastMsg, { duration: 2000 });
    }
    return startV2Import(body, { source: "本机文件夹" }).catch(function () { /* handled */ });
  }).catch(function (err) {
    setStepError("fine", err && err.message ? err.message : "读取计划文件失败，请重试");
  });
}

function onWizardStartClick() {
  if (_activeMode === "fine_craft" && _step === "confirm") {
    goToStep2b();
    return;
  }
  startImportFromWizard();
}

function restoreSessionIfAny(opts) {
  opts = opts || {};
  var draft = readDraft();
  restoreDraftFields(draft);
  if (opts.forceStep === "pick" || !draft.albumPath) {
    goToStep1(true);
    return;
  }
  _pendingAlbumPath = String(draft.albumPath);
  _pendingFolderName = basenameTitle(_pendingAlbumPath);
  var step = draft.wizardStep === "fine" ? "fine"
    : draft.wizardStep === "confirm" ? "confirm" : "confirm";
  setActiveMode(draft.mode === "fine_craft" ? "fine_craft" : "quick_share", "draft");
  if (draft.edition) {
    setActiveEdition(draft.edition, "draft");
  }
  if (step === "fine") {
    _fineVisited = true;
    goToStep2({ modeSource: true });
    goToStep2b();
  } else {
    if (draft.wizardStep === "fine" || draft.mode === "fine_craft") {
      _fineVisited = !!draft.title || !!draft.userNotes || !!draft.place;
    }
    goToStep2({ modeSource: true });
  }
  if (_pendingAlbumPath) {
    fetchAlbumPreview(_pendingAlbumPath).then(function () {
      if (_pendingPhotoCount == null && _pendingAlbumPath) {
        /* path may be invalid — stay on confirm but user can re-pick */
      }
    });
  }
}

export function isImportWizardOpen() {
  return _open;
}

export function openImportWizard(opts) {
  opts = opts || {};
  if (V2.state === "Importing") {
    if (typeof studioToast === "function") studioToast("正在制作中", { duration: 2200 });
    return;
  }
  if (_open) return;
  var root = $("v2-wizard-root");
  var dialog = $("v2-import-wizard");
  if (!root || !dialog) return;
  _previousFocus = document.activeElement;
  _importStarted = false;
  show(root, true);
  document.body.classList.add("v2-wizard-open");
  setBackgroundInert(true);
  _open = true;
  clearErrors();
  trapFocus(dialog);
  trackStudioEvent("open_sheet", { state: V2.state, surface: "bench" });
  if (opts.forceStep === "pick") {
    goToStep1(true);
  } else {
    restoreSessionIfAny(opts);
    if (_step === "pick") goToStep1(false);
  }
  if (opts.edition) {
    setActiveEdition(opts.edition, "homepage");
  }
  var pick = $("v2-wizard-pick");
  if (_step === "pick" && pick) pick.focus();
}

/**
 * @param {string} [reason]
 * @param {{persistDraft?: boolean}} [opts] persistDraft 默认 true；丢弃/保留确认后已自行处理草稿时传 false
 */
export function closeImportWizard(reason, opts) {
  opts = opts || {};
  if (!_open) return;
  var root = $("v2-wizard-root");
  var dialog = $("v2-import-wizard");
  if (root) show(root, false);
  document.body.classList.remove("v2-wizard-open");
  setBackgroundInert(false);
  _open = false;
  toggleDrawer(false);
  releaseTrap(dialog);
  trackStudioEvent("sheet_close", { reason: reason || "dismiss" });
  if (!_importStarted) {
    trackStudioEvent("sheet_abandon", { step: _step });
  }
  if (opts.persistDraft !== false) {
    saveDraft();
  }
  if (_previousFocus && typeof _previousFocus.focus === "function") {
    _previousFocus.focus();
  } else {
    var cta = $("v2-cta");
    if (cta) cta.focus();
  }
}

function loadTemplateSelectOptions() {
  var sel = $("v2-wizard-template-mode");
  if (!sel) return;
  fetch("/__travelogue/templates")
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (!data || !data.ok) return;
      var smart = document.createElement("option");
      smart.value = "smart";
      smart.textContent = data.smartLabel || "智能匹配（推荐）";
      sel.innerHTML = "";
      sel.appendChild(smart);
      (data.templates || []).forEach(function (t) {
        var opt = document.createElement("option");
        opt.value = "manual:" + (t.templateId || "");
        opt.textContent = (t.label || t.templateId) + "（手动指定）";
        sel.appendChild(opt);
      });
      sel.value = "smart";
      updateTemplateModeHint(data, sel.value);
    })
    .catch(function () { /* keep static */ });
}

function updateTemplateModeHint(data, value) {
  var hint = $("v2-wizard-template-hint");
  if (!hint) return;
  var hints = (data && data.modeHints) || {};
  var v = String(value || "smart");
  if (v.indexOf("manual:") === 0) {
    hint.textContent = hints.manual || "全程使用你指定的模板。";
    return;
  }
  hint.textContent = hints.smart || hint.textContent;
}

function wireTemplateSelect() {
  var sel = $("v2-wizard-template-mode");
  if (!sel || sel.dataset.wired === "1") return;
  sel.dataset.wired = "1";
  trackStudioEvent("template_selector_impression", { surface: "v2_sheet" });
  sel.addEventListener("change", function () {
    var v = String(sel.value || "smart");
    trackStudioEvent("template_mode_changed", { value: v });
    if (v.indexOf("manual:") === 0) {
      trackStudioEvent("template_manual_selected", { template_id: v.slice(7) });
    }
    fetch("/__travelogue/templates")
      .then(function (r) { return r.json(); })
      .then(function (data) { updateTemplateModeHint(data, v); })
      .catch(function () {});
  });
}

/** FE-FTUE-02 / FE-DFX-44：向导 pick · 一键试用示例相册（先判重再 import）。 */
function startDemoAlbumImport() {
  if (V2.state === "Importing") {
    if (typeof studioToast === "function") studioToast("正在制作中", { duration: 2200 });
    return;
  }
  trackStudioEvent("ftue_demo_album_click", { source: "wizard" });
  markVisited();

  var existing = (V2.trips || []).find(function (t) {
    return t && t.tripId === "demo-album";
  });
  // PMX D1 · 与后端 DEMO_ALBUM_DISPLAY_TITLE 对齐；禁止「示例游记」
  var DEMO_ALBUM_DISPLAY_TITLE = "斯里兰卡见闻录";
  var body = {
    useDemoAlbum: true,
    title: DEMO_ALBUM_DISPLAY_TITLE,
    place: "旅途",
    mode: "quick_share",
  };

  function kickoff(force) {
    _importStarted = true;
    try { sessionStorage.removeItem(IMPORT_DRAFT_KEY); } catch (_e) { /* ignore */ }
    closeImportWizard("start_demo_album", { persistDraft: false });
    if (typeof studioToast === "function") {
      studioToast(
        force ? "正在重新生成示例…" : "正在用示例照片试做一本…",
        { duration: 2200 }
      );
    }
    var payload = force ? Object.assign({}, body, { force: true }) : body;
    return startV2Import(payload, { source: "示例相册" }).catch(function () {
      /* import-run handles */
    });
  }

  if (existing) {
    // PMX D4 · 复用卡前先关 Wizard，取消则重开
    closeImportWizard("demo_exists_prompt");
    return resolveDemoAlbumExists({
      previewUrl: "/" + (existing.tripId || "demo-album") + "/index.html",
      result: { previewUrl: "/" + (existing.tripId || "demo-album") + "/index.html" },
    }).then(function (choice) {
      if (choice === "open") {
        window.location.href =
          "/" + (existing.tripId || "demo-album") + "/index.html";
        return null;
      }
      if (choice === "regenerate") return kickoff(true);
      openImportWizard();
      return null;
    });
  }
  return kickoff(false);
}

export function initImportWizard() {
  if (_wired) return;
  _wired = true;
  loadTemplateSelectOptions();
  wireTemplateSelect();
  hydratePortfolioPipeline();

  var folderHelpMore = $("v2-wizard-folder-help-more");
  if (folderHelpMore) {
    folderHelpMore.addEventListener("click", function () {
      openHelpDrawer({ source: "deep_link", itemId: "H1" });
    });
  }

  var pick = $("v2-wizard-pick");
  if (pick) pick.addEventListener("click", pickFolder);

  var demoBtn = $("v2-wizard-demo-album");
  if (demoBtn) {
    demoBtn.addEventListener("click", function () {
      startDemoAlbumImport();
    });
  }

  ["v2-wizard-close-pick", "v2-wizard-close-confirm", "v2-wizard-close-fine"].forEach(function (id) {
    var btn = $(id);
    if (btn) btn.addEventListener("click", function () { requestCloseWizard("close_btn"); });
  });

  var scrim = $("v2-wizard-scrim");
  if (scrim) scrim.addEventListener("click", function () {
    if (V2.state !== "Importing") requestCloseWizard("scrim");
  });

  var changeFolder = $("v2-wizard-change-folder");
  if (changeFolder) changeFolder.addEventListener("click", function () { goToStep1(true); });

  ["v2-wizard-back-fine", "v2-wizard-back-fine-action"].forEach(function (id) {
    var btn = $(id);
    if (btn) btn.addEventListener("click", function () {
      setActiveMode("fine_craft", "user");
      goToStep2({ modeSource: true });
      updateStartLabel();
    });
  });

  var start = $("v2-wizard-start");
  if (start) start.addEventListener("click", onWizardStartClick);
  var startFine = $("v2-wizard-start-fine");
  if (startFine) startFine.addEventListener("click", function () {
    setActiveMode("fine_craft", "user");
    startImportFromWizard();
  });

  var quick = $("v2-wizard-mode-quick");
  var fine = $("v2-wizard-mode-fine");
  if (quick) quick.addEventListener("click", function () {
    setActiveMode("quick_share", "user");
    saveDraft();
  });
  if (fine) fine.addEventListener("click", function () {
    setActiveMode("fine_craft", "user");
    saveDraft();
  });

  var editionJournal = $("v2-wizard-edition-journal");
  var editionPortfolio = $("v2-wizard-edition-portfolio");
  if (editionJournal) editionJournal.addEventListener("click", function () {
    setActiveEdition("journal", "user");
  });
  if (editionPortfolio) editionPortfolio.addEventListener("click", function () {
    setActiveEdition("portfolio", "user");
  });
  var pageSpecToggle = $("v2-wizard-page-spec-toggle");
  if (pageSpecToggle) {
    pageSpecToggle.addEventListener("click", function () {
      _pageSpecOpen = !_pageSpecOpen;
      syncPageSpecUi();
    });
  }

  function onEditionKeydown(e) {
    if (!isRadioNavKey(e.key)) return;
    e.preventDefault();
    var next = nextRadioId(["journal", "portfolio"], _activeEdition, e.key);
    setActiveEdition(next, "user");
  }
  if (editionJournal) editionJournal.addEventListener("keydown", onEditionKeydown);
  if (editionPortfolio) editionPortfolio.addEventListener("keydown", onEditionKeydown);

  function onModeKeydown(e) {
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
    e.preventDefault();
    setActiveMode(e.key === "ArrowLeft" ? "quick_share" : "fine_craft", "user");
    saveDraft();
    if (_activeMode === "quick_share" && quick) quick.focus();
    else if (fine) fine.focus();
  }
  if (quick) quick.addEventListener("keydown", onModeKeydown);
  if (fine) fine.addEventListener("keydown", onModeKeydown);

  ["v2-wizard-photo-adjust", "v2-wizard-photo-adjust-fine"].forEach(function (id) {
    var btn = $(id);
    if (btn) btn.addEventListener("click", function () { toggleDrawer(!_drawerOpen); });
  });

  document.querySelectorAll('input[name="v2-wizard-photo-keep-mode"]').forEach(function (input) {
    input.addEventListener("change", function () {
      _photoKeepModeTouched = true;
      updatePhotoKeepModeUi();
      saveDraft();
      var keepMode = readPhotoKeepMode();
      var derived = derivePhotoPrefsFromMode(keepMode);
      trackImportPhotoKeepMode({
        photo_keep_mode: keepMode,
        mode: _activeMode,
        photo_count: _pendingPhotoCount,
        pref_source: "draft",
      });
      trackImportPhotoCullPref({
        enabled: derived.photoCullEnabled,
        mode: _activeMode,
        photo_count: _pendingPhotoCount,
        pref_source: "draft",
        derived_from_mode: true,
      });
      trackImportKeepDupesPref({
        enabled: derived.keepNearDuplicates,
        mode: _activeMode,
        photo_count: _pendingPhotoCount,
        pref_source: "draft",
        derived_from_mode: true,
      });
    });
  });

  var pathBtn = $("v2-wizard-path-submit");
  if (pathBtn) pathBtn.addEventListener("click", submitWithPath);
  var pathInput = $("v2-wizard-album-path");
  if (pathInput) pathInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") { e.preventDefault(); submitWithPath(); }
  });
  var uploadInput = $("v2-wizard-album-upload");
  if (uploadInput) uploadInput.addEventListener("change", handleUploadInput);

  [
    "v2-wizard-trip-title", "v2-wizard-trip-place", "v2-wizard-date-start",
    "v2-wizard-date-end", "v2-wizard-user-notes", "v2-wizard-travel-notes",
    "v2-wizard-featured-dir", "v2-wizard-material-dir",
  ].forEach(function (id) {
    var el = $(id);
    if (!el) return;
    el.addEventListener("input", function () {
      if (id === "v2-wizard-trip-title") {
        _titleUserEdited = true;
        updateDuplicateTitleNote();
      }
      if (id === "v2-wizard-date-start" || id === "v2-wizard-date-end") _dateUserEdited = true;
      if (id === "v2-wizard-user-notes") syncChipPressedState();
      clearErrors();
      saveDraft();
    });
    el.addEventListener("change", function () {
      if (id === "v2-wizard-trip-title") {
        _titleUserEdited = true;
        updateDuplicateTitleNote();
      }
      if (id === "v2-wizard-date-start" || id === "v2-wizard-date-end") _dateUserEdited = true;
      if (id === "v2-wizard-user-notes") syncChipPressedState();
      saveDraft();
    });
  });

  var advanced = $("v2-wizard-advanced");
  if (advanced) {
    advanced.addEventListener("toggle", function () {
      trackStudioEvent("advanced_fields_toggle", { open: !!advanced.open });
    });
  }

  var firstTipDismiss = $("v2-wizard-first-tip-dismiss");
  if (firstTipDismiss) firstTipDismiss.addEventListener("click", dismissFirstTip);

  document.querySelectorAll('input[name="v2-wizard-layout-density"]').forEach(function (input) {
    input.addEventListener("change", function () {
      saveDraft();
      updateLayoutDensityWarn();
    });
  });

  document.querySelectorAll(".v2-wizard__chip[data-fill]").forEach(function (chip) {
    chip.addEventListener("click", function () {
      var targetId = chip.getAttribute("data-fill") || "";
      var target = $(targetId);
      if (!target) return;
      target.value = chip.textContent || "";
      if (targetId === "v2-wizard-user-notes") syncChipPressedState();
      saveDraft();
      target.focus();
    });
  });

  var planInput = $("v2-wizard-plan-file");
  var planName = $("v2-wizard-plan-file-name");
  if (planInput) {
    planInput.addEventListener("change", function () {
      var file = planInput.files && planInput.files[0] ? planInput.files[0] : null;
      if (planName) planName.textContent = file ? ("已选计划文件：" + file.name) : "";
      saveDraft();
    });
  }

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && _open && !_closeConfirmOpen && V2.state !== "Importing") {
      requestCloseWizard("esc");
    }
  });
}
