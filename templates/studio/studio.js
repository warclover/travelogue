/**
 * Travelogue Studio · v3 Photo-First Homepage Controller
 * State machine: Loading → IdleEmpty / IdleReturning → Importing → FirstSuccess
 *                                                            → Failed → ...
 *                                                            → Offline
 */
(function () {
  "use strict";

  // ── Stage labels (§8.2) ──
  var STAGE_LABELS = {
    ingest: "正在准备你的照片…",
    curate: "正在智能排版…",
    narrate: "正在撰写游记文字…",
    render: "正在生成游记预览…",
  };

  // ── localStorage keys (§9.3) ──
  var LS = {
    firstPreviewDone: "travelogue.studio.firstPreviewDone",
    firstReturnHighlight: "travelogue.studio.firstReturnHighlight",
    demoTried: "travelogue.studio.demoTried",
    recentPaths: "travelogue.studio.recentPaths",
    lastCancelled: "travelogue.studio.lastCancelled",
    studioIntent: "travelogue.studio.intent",
    coachImportV1: "travelogue.studio.coachImportV1",
  };
  var SS = {
    activeJobId: "travelogue.studio.activeJobId",
    activePending: "travelogue.studio.activePending",
  };
  var SAMPLE_LONGSHOTS = {
    kyoto: {
      title: "京都 · 雨后",
      meta: "86 张 · 4 章 · 静谧",
      paper: "#fbf6ee",
      ink: "#2a2520",
      colors: ["#b04331", "#3a4b3f", "#c9a85d", "#6c4a32"],
      chapters: ["雨夜抵达", "庙宇晨光", "竹林深处", "归途"],
    },
    iceland: {
      title: "冰岛 · 极光",
      meta: "120 张 · 5 章 · 壮阔",
      paper: "#f0f3f6",
      ink: "#1a1f2e",
      colors: ["#2a2a4a", "#7cc1a8", "#5d7a9e", "#b8c5d6", "#3a4862"],
      chapters: ["落地", "黑沙滩", "极光夜", "蓝冰洞", "告别"],
    },
    linzhi: {
      title: "林芝 · 桃花",
      meta: "64 张 · 3 章 · 抒情",
      paper: "#fef3f5",
      ink: "#3a2530",
      colors: ["#e6a6b5", "#7a8a72", "#d68aa0"],
      chapters: ["桃花初放", "雪山之下", "夜话"],
    },
  };

  function _pad2(n) { return (n < 10 ? "0" : "") + n; }

  // Build inline SVG that mimics a printed long screenshot page.
  function buildSampleSVG(key, mode) {
    var s = SAMPLE_LONGSHOTS[key];
    if (!s) return "";
    var W = 300;
    var H = mode === "full" ? 1320 : 440;
    var ink = s.ink, paper = s.paper, colors = s.colors;
    var parts = [];
    parts.push(
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + W + ' ' + H + '" ' +
      'preserveAspectRatio="xMidYMid slice" role="img" aria-label="' + s.title + ' 长图样张">'
    );
    parts.push(
      '<defs><linearGradient id="sh-' + key + '" x1="0" y1="0" x2="0" y2="1">' +
      '<stop offset="0" stop-color="#000" stop-opacity="0"/>' +
      '<stop offset="1" stop-color="#000" stop-opacity=".35"/>' +
      '</linearGradient></defs>'
    );
    parts.push('<rect width="' + W + '" height="' + H + '" fill="' + paper + '"/>');

    var y = mode === "full" ? 58 : 28;
    parts.push(
      '<text x="' + (W / 2) + '" y="' + y + '" text-anchor="middle" ' +
      'font-family="Georgia,Songti SC,serif" font-size="' + (mode === "full" ? 22 : 14) + '" ' +
      'fill="' + ink + '">' + s.title + '</text>'
    );
    y += mode === "full" ? 18 : 11;
    parts.push(
      '<text x="' + (W / 2) + '" y="' + y + '" text-anchor="middle" ' +
      'font-family="Segoe UI,PingFang SC,sans-serif" font-size="' + (mode === "full" ? 9 : 6) + '" ' +
      'fill="' + ink + '" opacity=".55">' + s.meta + '</text>'
    );
    y += mode === "full" ? 32 : 16;

    var chapterCount = s.chapters.length;
    var photoH = mode === "full" ? 210 : 60;
    var textRows = mode === "full" ? 4 : 2;
    var rowH = mode === "full" ? 7 : 3;
    var bottomPad = mode === "full" ? 24 : 8;

    for (var i = 0; i < chapterCount; i++) {
      if (y + photoH + textRows * (rowH + 4) + 30 > H) break;
      parts.push(
        '<text x="32" y="' + y + '" font-family="Segoe UI,sans-serif" ' +
        'font-size="' + (mode === "full" ? 9 : 5.5) + '" fill="' + ink + '" ' +
        'opacity=".5" letter-spacing="2">CHAPTER ' + _pad2(i + 1) + '</text>'
      );
      y += mode === "full" ? 14 : 8;
      parts.push(
        '<text x="32" y="' + y + '" font-family="Georgia,Songti SC,serif" ' +
        'font-size="' + (mode === "full" ? 14 : 7.5) + '" font-weight="600" fill="' + ink + '">' +
        s.chapters[i] + '</text>'
      );
      y += mode === "full" ? 14 : 7;
      var color = colors[i % colors.length];
      parts.push(
        '<rect x="32" y="' + y + '" width="' + (W - 64) + '" height="' + photoH + '" ' +
        'rx="3" fill="' + color + '"/>' +
        '<rect x="32" y="' + y + '" width="' + (W - 64) + '" height="' + photoH + '" ' +
        'rx="3" fill="url(#sh-' + key + ')"/>'
      );
      y += photoH + (mode === "full" ? 14 : 7);
      for (var r = 0; r < textRows; r++) {
        var w = (W - 64) * (r === textRows - 1 ? 0.5 : 0.92);
        parts.push(
          '<rect x="32" y="' + y + '" width="' + w + '" height="' + rowH + '" ' +
          'rx="1" fill="' + ink + '" opacity=".5"/>'
        );
        y += rowH + (mode === "full" ? 8 : 4);
      }
      y += bottomPad;
    }
    if (mode === "full") {
      parts.push(
        '<text x="' + (W / 2) + '" y="' + (H - 40) + '" text-anchor="middle" ' +
        'font-family="Georgia,serif" font-size="11" fill="' + ink + '" opacity=".4" letter-spacing="6">— end —</text>'
      );
    }
    parts.push('</svg>');
    return parts.join("");
  }

  function renderSampleCards() {
    var container = $("studio-samples");
    if (!container) return;
    container.innerHTML = "";
    Object.keys(SAMPLE_LONGSHOTS).forEach(function (key) {
      var s = SAMPLE_LONGSHOTS[key];
      var card = document.createElement("article");
      card.className = "studio-longshot-card";
      card.setAttribute("data-sample", key);
      card.setAttribute("tabindex", "0");
      card.setAttribute("role", "button");
      card.setAttribute("aria-label", s.title + " 长图样张");
      var paper = document.createElement("div");
      paper.className = "studio-longshot-card__paper";
      paper.innerHTML = buildSampleSVG(key, "thumb");
      card.appendChild(paper);
      var meta = document.createElement("div");
      meta.className = "studio-longshot-card__meta";
      var h = document.createElement("h3"); h.textContent = s.title;
      var p = document.createElement("p"); p.textContent = s.meta;
      meta.appendChild(h); meta.appendChild(p);
      card.appendChild(meta);
      container.appendChild(card);
    });
  }

  // ── State ──
  var currentState = "Loading";
  var pendingImport = null;
  var activeJobId = null;
  var tripsData = [];
  var tripsListLimit = 20;
  var tripsTotalCount = 0;
  var isOffline = false;
  var healthTimer = null;
  var SLOW_JOB_MS = 30000;
  var SLOW_JOB_VISION_MS = 180000;
  var SLOW_JOB_VISION_LONG_MS = 480000;
  var _importVisionEnabled = false;
  var HEALTH_INTERVAL = 30000;
  var _pickInFlight = false;
  var _importGen = 0;
  var _thumbObjectUrls = [];
  var _tripsLoadSeq = 0;
  var _sheetOpen = false;
  var _pendingAlbumPath = null;

  // ── Helpers ──
  function $(id) { return document.getElementById(id); }
  function show(el, visible) { if (el) el.hidden = !visible; }

  function studioAuthHeaders(extra) {
    var headers = extra || {};
    var meta = document.querySelector('meta[name="studio-token"]');
    var token = meta && meta.getAttribute("content");
    if (token) headers["X-Studio-Token"] = token;
    return headers;
  }

  function setTitle(suffix) {
    document.title = suffix ? suffix + " · Travelogue Studio" : "Travelogue Studio";
  }

  function formatUpdatedAt(ts) {
    if (!ts) return "";
    var d = new Date(ts * 1000);
    var now = new Date();
    var diffMs = now - d;
    var dayMs = 24 * 3600 * 1000;
    if (diffMs < 60 * 1000) return "刚刚";
    if (diffMs < 3600 * 1000) return Math.floor(diffMs / 60000) + " 分钟前";
    if (diffMs < dayMs) return Math.floor(diffMs / 3600000) + " 小时前";
    if (diffMs < 7 * dayMs) return Math.floor(diffMs / dayMs) + " 天前";
    return d.toLocaleDateString("zh-CN");
  }

  // ── Error / Warning ──
  function setError(msg) {
    var progressEl = $("studio-error");
    var idleEl = $("studio-import-error");
    if (!msg) {
      if (progressEl) { show(progressEl, false); progressEl.textContent = ""; }
      if (idleEl) { show(idleEl, false); idleEl.textContent = ""; }
      return;
    }
    if (currentState === "Importing") {
      if (progressEl) { progressEl.textContent = msg; show(progressEl, true); }
      if (idleEl) show(idleEl, false);
    } else if (idleEl) {
      idleEl.textContent = msg;
      show(idleEl, true);
      if (progressEl) show(progressEl, false);
    } else if (progressEl) {
      progressEl.textContent = msg;
      show(progressEl, true);
    }
  }

  function setWarning(msg) {
    var el = $("studio-warning");
    if (!el) return;
    if (!msg) { show(el, false); el.textContent = ""; return; }
    el.textContent = msg;
    show(el, true);
  }

  function showFailure(msg, echoPath) {
    show($("studio-failure"), true);
    var msgEl = $("studio-failure-msg");
    if (msgEl) msgEl.textContent = msg || "导入失败";
    var echoEl = $("studio-failure-echo");
    if (echoEl) {
      if (echoPath) { echoEl.textContent = echoPath; show(echoEl, true); }
      else show(echoEl, false);
    }
    setTitle("导入失败");
  }

  function hideFailure() {
    show($("studio-failure"), false);
    var msg = $("studio-failure-msg"); if (msg) msg.textContent = "";
    show($("studio-failure-echo"), false);
    setTitle();
  }

  function setImportUiDisabled(disabled) {
    var ids = [
      "studio-open-sheet", "studio-open-sheet-returning", "studio-sheet-pick",
      "studio-sheet-start", "studio-sheet-skip", "studio-browse-folder",
      "studio-submit-path", "studio-demo-album", "studio-path-toggle",
      "studio-sample-cta",
    ];
    ids.forEach(function (id) { var el = $(id); if (el) el.disabled = disabled; });
    var uploadInput = $("album-upload");
    if (uploadInput) uploadInput.disabled = disabled;
  }

  function basenameTitleFromPath(path) {
    if (!path) return "我的旅途";
    var base = String(path).replace(/[/\\]+$/, "").split(/[/\\]/).pop() || "";
    base = base.replace(/\.[^.]+$/, "").trim();
    if (!base) return "我的旅途";
    return base.length > 20 ? base.slice(0, 20) : base;
  }

  function saveIntent() {
    try {
      localStorage.setItem(LS.studioIntent, JSON.stringify({
        title: ($("trip-title") && $("trip-title").value) || "",
        place: ($("trip-place") && $("trip-place").value) || "",
        feeling: ($("trip-feeling") && $("trip-feeling").value) || "",
      }));
    } catch (e) {}
  }

  function loadIntent() {
    try {
      var raw = localStorage.getItem(LS.studioIntent);
      if (!raw) return;
      var data = JSON.parse(raw);
      if ($("trip-title") && data.title) $("trip-title").value = data.title;
      if ($("trip-place") && data.place) $("trip-place").value = data.place;
      if ($("trip-feeling") && data.feeling) $("trip-feeling").value = data.feeling;
    } catch (e) {}
  }

  function validateTitleField() {
    var input = $("trip-title");
    var err = $("trip-title-error");
    if (!input || !err) return true;
    var v = (input.value || "").trim();
    if (v.length > 20) {
      err.textContent = "杂志名最多 20 个字";
      show(err, true);
      return false;
    }
    show(err, false);
    return true;
  }

  function resetSheetConfirm() {
    _pendingAlbumPath = null;
    show($("studio-sheet-confirm"), false);
    show($("studio-sheet-picked"), false);
    var picked = $("studio-sheet-picked");
    if (picked) picked.textContent = "";
    var pickBtn = $("studio-sheet-pick");
    if (pickBtn) {
      pickBtn.disabled = false;
      pickBtn.textContent = "选择照片文件夹";
    }
  }

  function showSheetConfirm(albumPath) {
    _pendingAlbumPath = albumPath;
    var picked = $("studio-sheet-picked");
    if (picked) {
      picked.textContent = "已选择：" + albumPath;
      show(picked, true);
    }
    var pickBtn = $("studio-sheet-pick");
    if (pickBtn) {
      pickBtn.disabled = true;
      pickBtn.textContent = "已选择文件夹";
    }
    var titleInput = $("trip-title");
    if (titleInput) titleInput.value = basenameTitleFromPath(albumPath);
    show($("studio-sheet-confirm"), true);
    validateTitleField();
    if (titleInput) titleInput.focus();
  }

  function isSheetOpen() { return _sheetOpen; }

  function openImportSheet() {
    if (currentState === "Importing") {
      if (typeof studioToast === "function") {
        studioToast("正在制作杂志，请稍候", { duration: 2500 });
      }
      return;
    }
    loadIntent();
    resetSheetConfirm();
    var root = $("studio-sheet-root");
    if (root) show(root, true);
    _sheetOpen = true;
    document.body.classList.add("studio-sheet-open");
    setError("");
    var pick = $("studio-sheet-pick");
    if (pick) pick.focus();
    maybeShowCoach(1);
  }

  function closeImportSheet() {
    saveIntent();
    var root = $("studio-sheet-root");
    if (root) show(root, false);
    _sheetOpen = false;
    document.body.classList.remove("studio-sheet-open");
  }

  function buildImportPayload(extra) {
    extra = extra || {};
    var title = ($("trip-title") && $("trip-title").value.trim()) || "我的旅途";
    var place = ($("trip-place") && $("trip-place").value.trim()) || "旅途";
    var feeling = ($("trip-feeling") && $("trip-feeling").value.trim()) || "";
    var body = {
      albumPath: extra.albumPath || _pendingAlbumPath,
      title: title.slice(0, 20),
      place: place,
      force: !!extra.force,
    };
    if (feeling) body.userNotes = feeling.slice(0, 200);
    return body;
  }

  function submitSheetImport(skipTitleEdit) {
    if (!_pendingAlbumPath) {
      setError("请先选择照片文件夹");
      return;
    }
    if (!skipTitleEdit && !validateTitleField()) return;
    saveIntent();
    closeImportSheet();
    var body = buildImportPayload({ albumPath: _pendingAlbumPath });
    if (typeof studioToast === "function") {
      studioToast("将新建一篇杂志 · 开始制作", { duration: 2200 });
    }
    startImport(body);
  }

  function renderContinueCard() {
    var host = $("studio-continue-card");
    if (!host || !tripsData.length) {
      show(host, false);
      return;
    }
    var trip = tripsData[0];
    host.innerHTML = "";
    show(host, true);
    var titleAfter = $("studio-hero-returning");
    var h1 = titleAfter && titleAfter.querySelector(".studio-hero__title--after-card");
    if (h1) show(h1, false);

    var thumb = document.createElement("div");
    thumb.className = "studio-continue-card__thumb";
    if (trip.previewRelPath) {
      var img = document.createElement("img");
      img.alt = trip.title || "";
      img.src = "/" + trip.tripId + "/" + trip.previewRelPath;
      img.onerror = function () { img.remove(); };
      thumb.appendChild(img);
    }
    host.appendChild(thumb);

    var t = document.createElement("p");
    t.className = "studio-continue-card__title";
    t.textContent = trip.title || trip.tripId;
    host.appendChild(t);

    var sub = document.createElement("p");
    sub.className = "studio-continue-card__sub";
    sub.textContent = formatUpdatedAt(trip.updatedAt) || "继续上次的杂志";
    host.appendChild(sub);

    var actions = document.createElement("div");
    actions.className = "studio-continue-card__actions";

    var cont = document.createElement("a");
    cont.className = "studio-btn studio-btn--gold";
    cont.href = trip.previewUrl || ("/" + trip.tripId + "/index.html");
    cont.textContent = "继续编辑";
    actions.appendChild(cont);

    if (trip.longshotStale) {
      var lng = document.createElement("a");
      lng.className = "studio-btn studio-btn--ghost-inverse";
      lng.href = "/" + trip.tripId + "/index.html?focus=longshot";
      lng.textContent = "更新长图";
      actions.appendChild(lng);
    }
    host.appendChild(actions);
  }

  function maybeShowCoach(step) {
    var done = parseInt(localStorage.getItem(LS.coachImportV1) || "0", 10);
    if (done >= 2) return;
    if (step === 1 && done >= 1) return;
    var coach = $("studio-coach");
    var text = $("studio-coach-text");
    if (!coach || !text) return;
    var messages = [
      "从这里开始 · 照片留在本机，不上传云端",
      "选一次旅行的文件夹即可",
    ];
    text.textContent = messages[step - 1] || messages[0];
    coach.style.top = step === 1 ? "auto" : "auto";
    coach.style.bottom = step === 1 ? "120px" : "280px";
    coach.style.left = step === 1 ? "clamp(20px, 4vw, 48px)" : "50%";
    coach.style.transform = step === 1 ? "none" : "translateX(-50%)";
    show(coach, true);
    localStorage.setItem(LS.coachImportV1, String(Math.max(done, step)));
  }

  function dismissCoach() {
    show($("studio-coach"), false);
    localStorage.setItem(LS.coachImportV1, "2");
  }

  function syncImportUiDisabled() {
    setImportUiDisabled(isOffline || currentState === "Importing" || _pickInFlight);
  }

  function bumpImportGeneration() { _importGen += 1; }
  function isImportGenerationStale(gen) { return gen !== _importGen; }

  function setBusy() { syncImportUiDisabled(); }

  // ── Hero background (LCP-friendly: try small variant first when available) ──
  var lastHeroSrc = "";
  function updateHeroBackground() {
    var img = $("studio-hero-image");
    if (!img) return;
    if (tripsData.length > 0) {
      var trip = tripsData[0];
      var rel = trip.previewRelPath;
      if (rel) {
        var url = "/" + trip.tripId + "/" + rel;
        if (url === lastHeroSrc) return;
        lastHeroSrc = url;
        var pre = new Image();
        pre.onload = function () {
          img.style.backgroundImage = 'url("' + url + '")';
          img.classList.remove("studio-hero__image--default");
        };
        pre.onerror = function () {
          img.style.backgroundImage = "";
          img.classList.add("studio-hero__image--default");
        };
        pre.src = url;
        return;
      }
    }
    lastHeroSrc = "";
    img.style.backgroundImage = "";
    img.classList.add("studio-hero__image--default");
  }

  // ── State machine ──
  function transitionTo(state) { currentState = state; render(); }

  function render() {
    var hasTrips = tripsData.length > 0;
    var isImporting = currentState === "Importing";
    var isFailed = currentState === "Failed";
    var isSuccess = currentState === "Success";
    var isLoading = currentState === "Loading";

    if (isImporting) setTitle("正在生成…");
    else if (isFailed) setTitle("导入失败");
    else setTitle();

    show($("studio-offline"), isOffline);
    syncImportUiDisabled();

    // Hero variant data attribute (controls veil / blur)
    var hero = $("studio-hero");
    var variant;
    if (isImporting) variant = "importing";
    else if (isFailed) variant = "failed";
    else if (isSuccess) variant = "success";
    else if (hasTrips) variant = "returning";
    else variant = "empty";
    if (hero) hero.setAttribute("data-variant", variant);

    updateHeroBackground();

    show($("studio-hero-empty"), !hasTrips && !isImporting && !isFailed && !isSuccess && !isLoading);
    show($("studio-hero-returning"), hasTrips && !isImporting && !isFailed && !isSuccess);
    show($("studio-hero-importing"), isImporting);
    show($("studio-failure"), isFailed);
    show($("studio-success"), isSuccess);

    var quietOverlay = isImporting || isFailed || isSuccess || isLoading;
    show($("studio-hero-secondary"), !quietOverlay);
    var secondaryLabel = $("studio-secondary-label");
    if (secondaryLabel) {
      secondaryLabel.textContent = hasTrips ? "或者" : "还没自己的照片？";
    }

    if (quietOverlay) closeImportSheet();
    show($("studio-import-form"), false);
    show($("studio-advanced-options"), !quietOverlay);

    show($("studio-scroll-hint"), !quietOverlay);
    var scrollText = $("studio-scroll-hint-text");
    if (scrollText) {
      if (hasTrips) {
        var count = tripsTotalCount || tripsData.length;
        scrollText.textContent = "向下 · 全部 " + count + " 篇游记";
      } else {
        scrollText.textContent = "向下 · 看看别人做的";
      }
    }

    var dot = $("studio-status-dot");
    var statusText = $("studio-status-text");
    if (dot && statusText) {
      dot.classList.remove("studio-topbar__dot--offline", "studio-topbar__dot--importing");
      if (isOffline) { dot.classList.add("studio-topbar__dot--offline"); statusText.textContent = "未连接"; }
      else if (isImporting) { dot.classList.add("studio-topbar__dot--importing"); statusText.textContent = "正在装帧中…"; }
      else { statusText.textContent = "本地运行中"; }
    }

    if (hasTrips && !isImporting && !isFailed && !isSuccess) {
      renderContinueCard();
      renderHybridHero();
    } else {
      show($("studio-continue-card"), false);
      var h1 = document.querySelector(".studio-hero__title--after-card");
      if (h1) show(h1, true);
    }

    show($("studio-gallery"), !hasTrips && !isImporting && !isFailed && !isSuccess && !isLoading);
    show($("studio-trips"), hasTrips && !isImporting && !isFailed && !isSuccess);
    if (hasTrips && !isImporting && !isFailed && !isSuccess) renderAllTrips();

    var below = $("studio-below");
    if (below) {
      var anyBelow = !isImporting && !isFailed && !isSuccess && !isLoading;
      below.style.display = anyBelow ? "" : "none";
    }

    renderFooterStats();
    renderCancelNotice();
  }

  // ── Returning hero: left text + right 3 recent cards ──
  function renderHybridHero() {
    var eyebrow = $("studio-recent-eyebrow");
    if (eyebrow && tripsData[0] && tripsData[0].updatedAt) {
      eyebrow.textContent = "最近编辑 · " + formatUpdatedAt(tripsData[0].updatedAt);
    } else if (eyebrow) {
      eyebrow.textContent = "最近编辑";
    }

    var list = $("studio-hero-recent-list");
    if (!list) return;
    list.innerHTML = "";

    var recent = tripsData.slice(0, 3);
    recent.forEach(function (trip, idx) {
      var card = document.createElement("a");
      card.className = "studio-hero__recent-card";
      var href = trip.previewUrl || ("/" + trip.tripId + "/index.html");
      if (trip.longshotStale) href = "/" + trip.tripId + "/index.html?focus=longshot";
      card.href = href;
      card.title = (trip.title || trip.tripId) + (trip.longshotStale ? " · 长图待更新" : "");

      if (idx === 0 &&
          localStorage.getItem(LS.firstPreviewDone) === "1" &&
          !localStorage.getItem(LS.firstReturnHighlight) &&
          currentState === "IdleReturning") {
        card.classList.add("studio-hero__recent-card--highlight");
        setTimeout(function () {
          card.classList.remove("studio-hero__recent-card--highlight");
          localStorage.setItem(LS.firstReturnHighlight, "1");
        }, 5000);
      }

      if (trip.previewRelPath) {
        var img = document.createElement("img");
        img.alt = trip.title || "游记封面";
        img.loading = idx === 0 ? "eager" : "lazy";
        img.src = "/" + trip.tripId + "/" + trip.previewRelPath;
        img.onerror = function () { img.remove(); };
        card.appendChild(img);
      }

      if (trip.longshotStale) {
        var stale = document.createElement("span");
        stale.className = "studio-hero__recent-card__stale";
        stale.textContent = "长图待更新";
        card.appendChild(stale);
      }

      var meta = document.createElement("div");
      meta.className = "studio-hero__recent-card__meta";
      var t = document.createElement("p");
      t.className = "studio-hero__recent-card__title";
      t.textContent = trip.title || trip.tripId;
      meta.appendChild(t);
      var sub = document.createElement("p");
      sub.className = "studio-hero__recent-card__sub";
      var subParts = [];
      if (trip.photoCount) subParts.push(trip.photoCount + " 张");
      if (trip.updatedAt) subParts.push(formatUpdatedAt(trip.updatedAt));
      sub.textContent = subParts.join(" · ");
      meta.appendChild(sub);
      card.appendChild(meta);

      list.appendChild(card);
    });
  }

  // ── Trip cards (all trips grid) ──
  function renderTripCard(trip, options) {
    options = options || {};
    var isDemo = trip.tripId && trip.tripId.indexOf("demo") >= 0;
    var href = trip.previewUrl || ("/" + trip.tripId + "/index.html");
    if (trip.longshotStale) {
      href = "/" + trip.tripId + "/index.html?focus=longshot";
    }

    var card = document.createElement("a");
    card.className = "studio-trip-card";
    card.href = href;
    card.title = trip.title || trip.tripId;

    // Highlight first return (only on the latest trip)
    var needsHighlight = false;
    if (options.highlight &&
        localStorage.getItem(LS.firstPreviewDone) === "1" &&
        !localStorage.getItem(LS.firstReturnHighlight) &&
        currentState === "IdleReturning") {
      needsHighlight = true;
    }
    if (needsHighlight) {
      card.classList.add("studio-trip-card--highlight");
      setTimeout(function () {
        card.classList.remove("studio-trip-card--highlight");
        localStorage.setItem(LS.firstReturnHighlight, "1");
      }, 5000);
    }

    if (trip.previewRelPath) {
      var img = document.createElement("img");
      img.alt = trip.title || "游记封面";
      img.loading = options.eager ? "eager" : "lazy";
      if (options.eager) img.setAttribute("fetchpriority", "high");
      img.src = "/" + trip.tripId + "/" + trip.previewRelPath;
      img.onerror = function () {
        img.remove();
        var ph = document.createElement("div");
        ph.className = "studio-trip-card__placeholder";
        ph.textContent = trip.title || trip.tripId;
        card.insertBefore(ph, card.firstChild);
      };
      card.appendChild(img);
    } else {
      var placeholder = document.createElement("div");
      placeholder.className = "studio-trip-card__placeholder";
      placeholder.textContent = trip.title || trip.tripId;
      card.appendChild(placeholder);
    }

    if (isDemo) {
      var badge = document.createElement("span");
      badge.className = "studio-trip-card__demo";
      badge.textContent = "示例";
      card.appendChild(badge);
    }

    var meta = document.createElement("div");
    meta.className = "studio-trip-card__meta";

    var name = document.createElement("p");
    name.className = "studio-trip-card__title";
    name.textContent = trip.title || trip.tripId;
    meta.appendChild(name);

    var sub = document.createElement("p");
    sub.className = "studio-trip-card__sub";
    var subParts = [];
    if (trip.photoCount) subParts.push(trip.photoCount + " 张");
    if (trip.updatedAt) subParts.push(formatUpdatedAt(trip.updatedAt));
    sub.textContent = subParts.join(" · ");
    if (trip.longshotStale) {
      var stale = document.createElement("span");
      stale.className = "studio-trip-card__stale";
      stale.textContent = "长图待更新";
      sub.appendChild(document.createTextNode(" "));
      sub.appendChild(stale);
    }
    meta.appendChild(sub);

    card.appendChild(meta);
    return card;
  }

  function renderAllTrips() {
    var list = $("studio-trips-list");
    var count = $("studio-trips-count");
    if (!list) return;
    list.innerHTML = "";

    tripsData.forEach(function (trip, i) {
      list.appendChild(renderTripCard(trip, { highlight: i === 0, eager: i < 8 }));
    });

    var addCard = document.createElement("button");
    addCard.type = "button";
    addCard.className = "studio-trip-card studio-trip-card--add";
    addCard.textContent = "新建游记";
    addCard.addEventListener("click", function () {
      requestNativeFolder($("trip-title").value, $("trip-place").value);
    });
    list.appendChild(addCard);

    if (count) {
      var total = tripsTotalCount || tripsData.length;
      count.textContent = "共 " + total + " 篇";
    }

    var moreBtn = $("studio-trips-more");
    if (moreBtn) show(moreBtn, tripsData.length < tripsTotalCount);
  }

  function renderFooterStats() {
    var el = $("studio-footer-stats");
    if (!el) return;
    if (tripsData.length === 0) {
      el.textContent = "照片与游记保存在本机 · 不上传云端";
      return;
    }
    var total = tripsTotalCount || tripsData.length;
    var photos = tripsData.reduce(function (s, t) { return s + (t.photoCount || 0); }, 0);
    el.textContent = "已生成 " + total + " 篇 · 累计 " + photos + " 张照片 · 全部保存在本机";
  }

  function renderCancelNotice() {
    var raw = "";
    try { raw = localStorage.getItem(LS.lastCancelled) || ""; } catch (e) {}
    var data = null;
    if (raw) { try { data = JSON.parse(raw); } catch (e) { data = null; } }

    function applyTo(el) {
      if (!el) return;
      if (!data || !data.echo) { show(el, false); return; }
      el.innerHTML = "";
      var label = document.createElement("span");
      label.textContent = "上次取消：" + data.echo;
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "studio-cancel-notice__action";
      btn.textContent = "重新开始";
      btn.addEventListener("click", function () {
        if (data.body) startImport(data.body);
        try { localStorage.removeItem(LS.lastCancelled); } catch (e) {}
      });
      var dismiss = document.createElement("button");
      dismiss.type = "button";
      dismiss.className = "studio-cancel-notice__action";
      dismiss.textContent = "忽略";
      dismiss.style.opacity = ".6";
      dismiss.addEventListener("click", function () {
        try { localStorage.removeItem(LS.lastCancelled); } catch (e) {}
        show(el, false);
      });
      el.appendChild(label);
      el.appendChild(btn);
      el.appendChild(dismiss);
      show(el, true);
    }
    applyTo($("studio-cancel-notice"));
    applyTo($("studio-cancel-notice-returning"));
  }

  // ── Recent paths memory ──
  function getRecentPaths() {
    try { return JSON.parse(localStorage.getItem(LS.recentPaths) || "[]"); }
    catch (e) { return []; }
  }
  function pushRecentPath(p) {
    if (!p) return;
    var list = getRecentPaths().filter(function (x) { return x !== p; });
    list.unshift(p);
    if (list.length > 5) list = list.slice(0, 5);
    try { localStorage.setItem(LS.recentPaths, JSON.stringify(list)); } catch (e) {}
    renderRecentPaths();
  }
  function renderRecentPaths() {
    var dl = $("studio-recent-paths");
    if (!dl) return;
    dl.innerHTML = "";
    getRecentPaths().forEach(function (p) {
      var opt = document.createElement("option");
      opt.value = p;
      dl.appendChild(opt);
    });
  }

  // ── Import thumbs (real selected photos) ──
  function revokeThumbUrls() {
    _thumbObjectUrls.forEach(function (u) {
      try { URL.revokeObjectURL(u); } catch (e) { /* ignore */ }
    });
    _thumbObjectUrls = [];
  }

  function setImportThumbs(urls) {
    var c = $("studio-import-thumbs");
    if (!c) return;
    var spans = c.querySelectorAll("span");
    var defaults = [
      "/__studio/assets/demo-album/demo-01.jpg",
      "/__studio/assets/demo-album/demo-02.jpg",
      "/__studio/assets/demo-album/demo-03.jpg",
      "/__studio/assets/demo-album/demo-04.jpg",
    ];
    for (var i = 0; i < spans.length; i++) {
      var u = (urls && urls[i]) || defaults[i];
      spans[i].style.backgroundImage = 'url("' + u + '")';
    }
  }
  function readImportThumbsFromFiles(files) {
    if (!files || !files.length || !window.URL || !URL.createObjectURL) return;
    revokeThumbUrls();
    var picked = [];
    for (var i = 0; i < files.length && picked.length < 4; i++) {
      var f = files[i];
      var name = (f.webkitRelativePath || f.name || "").toLowerCase();
      if (/\.(jpe?g|png|webp|heic|heif)$/i.test(name)) picked.push(f);
    }
    _thumbObjectUrls = picked.map(function (f) { return URL.createObjectURL(f); });
    setImportThumbs(_thumbObjectUrls);
  }

  // ── Progress ──
  function stageText(job) {
    var label = STAGE_LABELS[job.stage] || "处理中…";
    var idx = job.stageIndex || 0;
    var total = job.stageCount || 4;
    var hint = job.stageHint ? "（" + job.stageHint + "）" : "";
    return idx + "/" + total + " · " + label + hint;
  }

  function updateProgress(job) {
    hideFailure();
    var stage = $("studio-stage");
    var line = stageText(job);
    if (job.result && job.result.intentLine && (job.stageIndex || 0) >= 2) {
      line = line + "\n" + job.result.intentLine;
    }
    if (stage) stage.textContent = line;
    var pct = Math.round(((job.stageIndex || 0) / (job.stageCount || 4)) * 100);
    var bar = $("studio-bar-fill"); if (bar) bar.style.width = pct + "%";
    var pctEl = $("studio-pct");
    if (pctEl) { pctEl.textContent = pct + "%"; show(pctEl, true); }
    show($("studio-cancel"), job.status === "running" || job.status === "queued");
  }

  // ── Job polling ──
  function pollJob(jobId) {
    return fetch("/__travelogue/status?jobId=" + encodeURIComponent(jobId))
      .then(function (r) { return r.json(); });
  }

  function cancelActiveJob() {
    bumpImportGeneration();
    if (!activeJobId) return Promise.resolve();
    var jobId = activeJobId;
    return fetch("/__travelogue/cancel", {
      method: "POST",
      headers: studioAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ jobId: jobId }),
    }).finally(function () {
      activeJobId = null;
      show($("studio-cancel"), false);
    });
  }

  function showSlowHint(level) {
    if (level === 3) {
      setWarning("仍可继续等待，或在「高级 · 分析选项」中关闭场景分析以加快速度");
      return;
    }
    if (level === 2) {
      setWarning("照片较多，正在仔细分析行程与场景，首次可能较慢");
      return;
    }
    setWarning("比预期久一些，请耐心等待…");
  }
  function hideSlowHint() { setWarning(""); }

  function refreshImportVisionFlag() {
    return fetch("/__travelogue/config")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (!data || data.ok === false) return;
        var vis = data.vision && data.vision.enabled;
        _importVisionEnabled = vis === "true" || vis === "auto";
      })
      .catch(function () { _importVisionEnabled = false; });
  }

  // ── Advanced · analysis options (Phase 3 M12-7) ──
  function initAdvancedOptions() {
    var details = $("studio-advanced-options");
    var cluSelect = $("studio-cfg-clustering");
    var visSelect = $("studio-cfg-vision");
    if (!details || !cluSelect || !visSelect) return;

    var _patchPending = false;

    function applyConfig(data) {
      if (!data || data.ok === false) return;
      if (data.clustering && data.clustering.enabled) {
        cluSelect.value = data.clustering.enabled;
      }
      if (data.vision && data.vision.enabled) {
        visSelect.value = data.vision.enabled;
      }
    }

    function fetchConfig() {
      return fetch("/__travelogue/config")
        .then(function (r) { return r.json(); })
        .then(applyConfig)
        .catch(function () { /* silent — defaults in HTML */ });
    }

    details.addEventListener("toggle", function () {
      if (details.open) fetchConfig();
    });

    function patchConfig() {
      if (_patchPending) return;
      _patchPending = true;
      fetch("/__travelogue/config", {
        method: "PATCH",
        headers: studioAuthHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          clustering: { enabled: cluSelect.value },
          vision: { enabled: visSelect.value },
        }),
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          applyConfig(data);
          if (typeof studioToast === "function") {
            studioToast("分析选项已保存", { duration: 2000 });
          }
        })
        .catch(function () {
          if (typeof studioToast === "function") {
            studioToast("保存失败，请重试", { duration: 2500 });
          }
        })
        .finally(function () { _patchPending = false; });
    }

    cluSelect.addEventListener("change", patchConfig);
    visSelect.addEventListener("change", patchConfig);
  }

  function isFirstTime() { return !localStorage.getItem(LS.firstPreviewDone); }
  function markFirstPreviewDone(tripId) {
    localStorage.setItem(LS.firstPreviewDone, "1");
    if (tripId) localStorage.setItem("travelogue.studio.firstTripId", tripId);
  }

  function waitJob(jobId, gen) {
    activeJobId = jobId;
    var started = Date.now();
    var slowShown = 0;
    hideSlowHint();
    refreshImportVisionFlag();

    return new Promise(function (resolve, reject) {
      function finishCancel() {
        activeJobId = null;
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
          if (_importVisionEnabled && !slowShown && Date.now() - started > SLOW_JOB_VISION_LONG_MS) {
            slowShown = 3;
            showSlowHint(3);
          } else if (_importVisionEnabled && slowShown < 2 && Date.now() - started > SLOW_JOB_VISION_MS) {
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
          activeJobId = null;
          show($("studio-cancel"), false);
          hideSlowHint();
          if (job.status === "succeeded") { updateProgress(job); resolve(job); return; }
          if (job.status === "cancelled") { reject(new Error("已取消")); return; }
          var msg = (job.error && (job.error.message || job.error.code)) || "导入失败";
          reject(new Error(msg));
        }).catch(reject);
      }
      tick();
    });
  }

  // ── Import flows ──
  function focusPathImport(message) {
    var form = $("studio-import-form");
    var input = $("album-path");
    show(form, true);
    if (message) setError(message);
    if (input) {
      input.focus();
      input.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }

  function submitPathImport() {
    var path = ($("album-path").value || "").trim();
    if (!path) {
      setError("请填写照片文件夹路径，例如 D:\\Photos\\Kyoto2025");
      openImportSheet();
      return;
    }
    pushRecentPath(path);
    if (!_sheetOpen) openImportSheet();
    showSheetConfirm(path);
    setError("");
  }

  function requestNativeFolder(titleVal, placeVal, options) {
    options = options || {};
    var autoStart = options.autoStart === true;
    if (_pickInFlight) {
      if (typeof studioToast === "function") {
        studioToast("文件夹选择器已打开，请在其窗口中操作", { duration: 2500 });
      }
      return Promise.resolve();
    }
    _pickInFlight = true;
    syncImportUiDisabled();
    setError("");
    var pickToastEl = null;
    if (typeof studioToast === "function") {
      pickToastEl = studioToast("正在打开文件夹选择器…", { duration: 0 });
    }
    return fetch("/__travelogue/pick-folder", {
      method: "POST",
      headers: studioAuthHeaders({ "Content-Type": "application/json" }),
      body: "{}",
    }).then(function (resp) {
      return resp.json().then(function (data) { return { status: resp.status, data: data }; });
    }).then(function (result) {
      if (result.data && result.data.cancelled) return;
      if (!result.data || result.data.ok === false || result.status >= 400) {
        var msg = (result.data && (result.data.message || result.data.detail))
          || "无法打开本机选文件夹。请粘贴路径，或重启 Studio 后重试。";
        focusPathImport(msg);
        return;
      }
      if (result.status === 200 && result.data && result.data.albumPath) {
        var pathInput = $("album-path");
        if (pathInput) pathInput.value = result.data.albumPath;
        if (titleVal && $("trip-title")) $("trip-title").value = titleVal;
        if (placeVal && $("trip-place")) $("trip-place").value = placeVal;
        if (!_sheetOpen) openImportSheet();
        showSheetConfirm(result.data.albumPath);
        maybeShowCoach(2);
        dismissCoach();
        if (autoStart) submitSheetImport(true);
        return;
      }
      openImportSheet();
      setError("无法打开本机选文件夹。请用「其他导入方式」粘贴路径。");
    }).catch(function () {
      openImportSheet();
      setError("无法连接选文件夹服务。请粘贴路径，或确认 Studio 正在运行。");
    }).finally(function () {
      if (pickToastEl && pickToastEl.parentNode) {
        pickToastEl.parentNode.removeChild(pickToastEl);
      }
      _pickInFlight = false;
      syncImportUiDisabled();
    });
  }

  function postImport(body) {
    return fetch("/__travelogue/import", {
      method: "POST",
      headers: studioAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(body),
    }).then(function (resp) {
      return resp.json().then(function (data) { return { status: resp.status, data: data }; });
    });
  }

  var _successTimer = null;
  function clearSuccessTimer() {
    if (_successTimer) { clearInterval(_successTimer); _successTimer = null; }
  }

  function handleImportSuccess(job) {
    var result = job.result || {};
    var url = result.previewUrl;
    var tripId = result.tripId;
    var notice = result.clusterNotice;
    if (notice && typeof studioToast === "function") {
      studioToast(notice, { duration: 4500 });
    }
    var first = isFirstTime();
    if (first) markFirstPreviewDone(tripId);

    var openLink = $("studio-success-open");
    var msg = $("studio-success-msg");
    if (openLink && url) openLink.href = url;
    var title = result.title || ($("trip-title") && $("trip-title").value) || "我的旅途";
    var featured = result.featuredCount;
    var segments = result.segmentCount;
    if (msg) {
      if (featured > 0) {
        msg.textContent = "《" + title + "》已生成 · " + featured + " 张精选已用于封面与章首";
      } else {
        msg.textContent = "《" + title + "》已生成 · 可在预览中标记精选照片";
      }
      if (segments > 0) msg.textContent += " · " + segments + " 段行程";
    }

    var chipsHost = $("studio-success-chips");
    if (chipsHost) {
      chipsHost.innerHTML = "";
      if (featured > 0) {
        var c1 = document.createElement("span");
        c1.className = "studio-success__chip";
        c1.textContent = "精选 " + featured + " 张";
        chipsHost.appendChild(c1);
      }
      if (segments > 0) {
        var c2 = document.createElement("span");
        c2.className = "studio-success__chip";
        c2.textContent = "行程 " + segments + " 段";
        chipsHost.appendChild(c2);
      }
      show(chipsHost, chipsHost.childElementCount > 0);
    }

    transitionTo("Success");

    var autoOpen = first || !localStorage.getItem(LS.firstPreviewDone + ".noAuto");
    var sec = (result.intentLine || featured > 0) ? 8 : 5;
    if (!first && localStorage.getItem(LS.firstPreviewDone) === "1") {
      autoOpen = false;
      sec = 0;
    }
    var secEl = $("studio-success-sec");
    var countdownP = document.querySelector(".studio-success__countdown");
    if (secEl) secEl.textContent = String(sec);
    if (countdownP) show(countdownP, autoOpen && sec > 0);
    clearSuccessTimer();
    if (autoOpen && sec > 0) {
      _successTimer = setInterval(function () {
        sec -= 1;
        if (secEl) secEl.textContent = String(Math.max(0, sec));
        if (sec <= 0) {
          clearSuccessTimer();
          if (url) window.location.href = url;
        }
      }, 1000);
    }
  }

  function startImport(body) {
    var gen = ++_importGen;
    pendingImport = body;
    try {
      if (!body.uploadForm) {
        sessionStorage.setItem(SS.activePending, JSON.stringify(body));
      } else {
        sessionStorage.removeItem(SS.activePending);
      }
    } catch (e) {}
    if (body && body.albumPath) pushRecentPath(body.albumPath);
    setError("");
    hideFailure();
    transitionTo("Importing");
    revokeThumbUrls();
    setImportThumbs(null);
    var stage = $("studio-stage"); if (stage) stage.textContent = "准备导入…";
    var bar = $("studio-bar-fill"); if (bar) bar.style.width = "0%";
    var pctEl = $("studio-pct"); if (pctEl) show(pctEl, false);

    return postImport(body).then(function (result) {
      if (result.status === 409 && result.data.error === "E_DEMO_EXISTS") {
        return (typeof studioModal === "function"
          ? studioModal({
              title: "该游记已存在",
              body: "是否覆盖已有内容？覆盖后无法撤销。",
              confirmText: "覆盖并重新导入",
              cancelText: "取消",
            })
          : Promise.resolve(window.confirm(result.data.message || "该游记已存在。是否覆盖？"))
        ).then(function (confirmed) {
          if (!confirmed) throw new Error("已取消覆盖");
          body.force = true;
          return startImport(body);
        });
      }
      if (result.status !== 202) {
        throw new Error(result.data.message || result.data.error || "导入失败");
      }
      try { sessionStorage.setItem(SS.activeJobId, result.data.jobId); } catch (e) {}
      return waitJob(result.data.jobId, gen);
    }).then(function (job) {
      try { sessionStorage.removeItem(SS.activeJobId); sessionStorage.removeItem(SS.activePending); } catch (e) {}
      handleImportSuccess(job);
      loadTrips();
    }).catch(function (err) {
      try { sessionStorage.removeItem(SS.activeJobId); } catch (e) {}
      if ((err.message || "") === "已取消") {
        setError("已取消导入");
        rememberCancelled();
        transitionTo(tripsData.length > 0 ? "IdleReturning" : "IdleEmpty");
        return;
      }
      if ((err.message || "") === "已取消覆盖") {
        transitionTo(tripsData.length > 0 ? "IdleReturning" : "IdleEmpty");
        return;
      }
      var echoPath = "";
      if (pendingImport && pendingImport.albumPath) echoPath = pendingImport.albumPath;
      transitionTo("Failed");
      showFailure(err.message || String(err), echoPath);
    }).finally(function () {
      setBusy();
    });
  }

  function rememberCancelled() {
    if (!pendingImport) return;
    var echo = "";
    if (pendingImport.albumPath) echo = pendingImport.albumPath;
    else if (pendingImport.fileCount) echo = "浏览器上传（" + pendingImport.fileCount + " 张照片）";
    else if (pendingImport.useDemoAlbum) echo = "示例相册";
    var data = { echo: echo, body: pendingImport.uploadForm ? null : pendingImport };
    try { localStorage.setItem(LS.lastCancelled, JSON.stringify(data)); } catch (e) {}
  }

  function postMultipartImport(formData, options) {
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

  function uploadAndImport(files, titleVal, placeVal) {
    if (!files || !files.length) return;
    var gen = ++_importGen;
    if (files.length > 100) {
      setWarning("照片较多（" + files.length + " 张），建议精选后导入，效果更佳。");
    } else {
      setWarning("");
    }

    var form = new FormData();
    form.append("title", titleVal || ($("trip-title") && $("trip-title").value) || "我的旅途");
    form.append("place", placeVal || ($("trip-place") && $("trip-place").value) || "旅途");
    var feeling = ($("trip-feeling") && $("trip-feeling").value.trim()) || "";
    if (feeling) form.append("userNotes", feeling.slice(0, 200));
    for (var i = 0; i < files.length; i++) {
      form.append("files[]", files[i], files[i].webkitRelativePath || files[i].name);
    }

    pendingImport = { uploadForm: true, files: files, fileCount: files.length };
    try { sessionStorage.removeItem(SS.activePending); } catch (e) {}
    setError("");
    hideFailure();
    transitionTo("Importing");
    readImportThumbsFromFiles(files);
    var stage = $("studio-stage"); if (stage) stage.textContent = "上传照片中…";
    var bar = $("studio-bar-fill"); if (bar) bar.style.width = "0%";
    var progress = $("upload-progress");
    show(progress, true);
    if (progress) progress.value = 0;

    return postMultipartImport(form, {
      onUploadProgress: function (ev) {
        if (ev.lengthComputable && progress) {
          progress.value = Math.round((ev.loaded / ev.total) * 100);
        }
      },
    }).then(function (result) {
      show(progress, false);
      if (result.status === 409 && result.data.error === "E_DEMO_EXISTS") {
        return (typeof studioModal === "function"
          ? studioModal({
              title: "该游记已存在",
              body: "是否覆盖已有内容？覆盖后无法撤销。",
              confirmText: "覆盖并重新导入",
              cancelText: "取消",
            })
          : Promise.resolve(window.confirm(result.data.message || "该游记已存在。是否覆盖？"))
        ).then(function (confirmed) {
          if (!confirmed) throw new Error("已取消覆盖");
          return uploadAndImportWithForce(files, titleVal, placeVal, gen);
        });
      }
      if (result.status !== 202) {
        throw new Error(result.data.message || result.data.error || "上传失败");
      }
      try { sessionStorage.setItem(SS.activeJobId, result.data.jobId); } catch (e) {}
      return waitJob(result.data.jobId, gen);
    }).then(function (job) {
      try { sessionStorage.removeItem(SS.activeJobId); } catch (e) {}
      handleImportSuccess(job);
      loadTrips();
    }).catch(function (err) {
      try { sessionStorage.removeItem(SS.activeJobId); } catch (e) {}
      if ((err.message || "") === "已取消" || (err.message || "") === "已取消覆盖") {
        rememberCancelled();
        transitionTo(tripsData.length > 0 ? "IdleReturning" : "IdleEmpty");
        return;
      }
      transitionTo("Failed");
      var echo = "";
      if (pendingImport && pendingImport.fileCount) {
        echo = "浏览器上传（" + pendingImport.fileCount + " 张照片）";
      }
      showFailure(err.message || String(err), echo);
    }).finally(function () {
      revokeThumbUrls();
      setBusy();
      show(progress, false);
    });
  }

  function uploadAndImportWithForce(files, titleVal, placeVal, gen) {
    var retryForm = new FormData();
    retryForm.append("title", titleVal || "我的旅途");
    retryForm.append("place", placeVal || "旅途");
    retryForm.append("force", "true");
    for (var j = 0; j < files.length; j++) {
      retryForm.append("files[]", files[j], files[j].webkitRelativePath || files[j].name);
    }
    return postMultipartImport(retryForm).then(function (retryResult) {
      if (retryResult.status !== 202) {
        throw new Error(retryResult.data.message || retryResult.data.error || "上传失败");
      }
      try { sessionStorage.setItem(SS.activeJobId, retryResult.data.jobId); } catch (e) {}
      return waitJob(retryResult.data.jobId, gen);
    });
  }

  // ── Load trips (with timeout handling per §6.12) ──
  function loadTrips(options) {
    options = options || {};
    if (options.more) tripsListLimit += 20;
    else if (options.keepLimit !== true) tripsListLimit = 20;

    var seq = ++_tripsLoadSeq;
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

    fetch("/__travelogue/trips?limit=" + encodeURIComponent(String(tripsListLimit)))
      .then(function (r) { if (!r.ok) throw new Error("trips unavailable"); return r.json(); })
      .then(function (data) {
        if (seq !== _tripsLoadSeq) return;
        clearTimeout(slowTimer); clearTimeout(failTimer);
        tripsData = data.trips || [];
        tripsTotalCount = typeof data.total === "number" ? data.total : tripsData.length;
        if (currentState === "Loading" || currentState === "IdleEmpty" || currentState === "IdleReturning") {
          transitionTo(tripsData.length > 0 ? "IdleReturning" : "IdleEmpty");
        } else {
          render();
        }
      })
      .catch(function () {
        if (seq !== _tripsLoadSeq) return;
        clearTimeout(slowTimer); clearTimeout(failTimer);
        isOffline = true;
        render();
        if (tripsData.length === 0) {
          transitionTo("IdleEmpty");
          if (!failToastShown && !slowToastShown && typeof studioToast === "function") {
            studioToast("加载失败，请检查 Studio 是否运行", { duration: 5000 });
          }
        }
      });
  }

  // ── Health check / Offline ──
  function startHealthCheck() {
    function check() {
      fetch("/__travelogue/trips", { method: "GET" })
        .then(function (r) {
          var wasOffline = isOffline;
          isOffline = !r.ok;
          if (wasOffline && !isOffline) {
            if (typeof studioToast === "function") studioToast("服务已恢复", { duration: 2000 });
            loadTrips();
          }
          render();
        })
        .catch(function () {
          var wasOffline = isOffline;
          isOffline = true;
          if (!wasOffline) render();
        });
    }
    check();
    healthTimer = setInterval(check, HEALTH_INTERVAL);
  }

  // ── Footer toggle ──
  function initFooter() {
    var toggle = $("studio-footer-toggle");
    var checklist = $("studio-footer-checklist");
    if (toggle && checklist) {
      toggle.addEventListener("click", function (e) {
        e.preventDefault();
        var visible = !checklist.hidden;
        show(checklist, !visible);
        toggle.textContent = visible ? "如何发到微信 ▸" : "如何发到微信 ▾";
      });
    }
  }

  // ── Copy address ──
  function initCopyAddr() {
    var addr = $("studio-copy-addr");
    if (!addr) return;
    addr.addEventListener("click", function () {
      var text = addr.textContent;
      if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(function () {
          if (typeof studioToast === "function") studioToast("已复制", { duration: 1500 });
        });
      }
    });
  }

  // ── Path form toggle ──
  function initPathToggle() {
    /* studio-path-toggle → openImportSheet (initImportSheet) */
  }

  // ── Scroll hint ──
  function initScrollHint() {
    var hint = $("studio-scroll-hint");
    var below = $("studio-below");
    if (hint && below) {
      hint.addEventListener("click", function () {
        below.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    }
  }

  // ── Trips "more" button ──
  function initTripsMore() {
    var moreBtn = $("studio-trips-more");
    if (!moreBtn) return;
    moreBtn.addEventListener("click", function () { loadTrips({ more: true }); });
  }

  // ── Resume in-flight import after page reload ──
  function resumeActiveJobIfAny() {
    var jobId = "";
    var pendingRaw = "";
    try {
      jobId = sessionStorage.getItem(SS.activeJobId) || "";
      pendingRaw = sessionStorage.getItem(SS.activePending) || "";
    } catch (e) {}
    if (!jobId) return false;
    if (pendingRaw) {
      try {
        pendingImport = JSON.parse(pendingRaw);
        if (pendingImport && pendingImport.uploadForm) {
          try {
            sessionStorage.removeItem(SS.activeJobId);
            sessionStorage.removeItem(SS.activePending);
          } catch (e) {}
          return false;
        }
      } catch (e) { pendingImport = null; }
    }
    var gen = ++_importGen;
    transitionTo("Importing");
    setImportThumbs(null);
    var stage = $("studio-stage"); if (stage) stage.textContent = "恢复上次导入…";
    waitJob(jobId, gen).then(function (job) {
      try { sessionStorage.removeItem(SS.activeJobId); sessionStorage.removeItem(SS.activePending); } catch (e) {}
      handleImportSuccess(job);
      loadTrips({ keepLimit: true });
    }).catch(function (err) {
      try { sessionStorage.removeItem(SS.activeJobId); } catch (e) {}
      if ((err.message || "") === "已取消") {
        rememberCancelled();
        transitionTo(tripsData.length > 0 ? "IdleReturning" : "IdleEmpty");
        return;
      }
      transitionTo("Failed");
      var echo = (pendingImport && pendingImport.albumPath) || "";
      showFailure(err.message || String(err), echo);
    }).finally(function () { setBusy(); });
    return true;
  }

  // ── Sample longshot modal ──
  function initSampleModal() {
    var modal = $("studio-sample-modal");
    var pages = $("studio-sample-pages");
    var titleEl = $("studio-sample-title");
    var cta = $("studio-sample-cta");
    if (!modal || !pages || !titleEl) return;

    function open(key) {
      var sample = SAMPLE_LONGSHOTS[key];
      if (!sample) return;
      titleEl.textContent = sample.title;
      pages.innerHTML = buildSampleSVG(key, "full");
      show(modal, true);
      document.body.style.overflow = "hidden";
      var sc = document.querySelector(".studio-sample-modal__scroll");
      if (sc) sc.scrollTop = 0;
    }
    function close() {
      show(modal, false);
      document.body.style.overflow = "";
    }

    var samplesHost = $("studio-samples");
    if (samplesHost) {
      samplesHost.addEventListener("click", function (e) {
        var card = e.target.closest(".studio-longshot-card");
        if (card) open(card.getAttribute("data-sample"));
      });
      samplesHost.addEventListener("keydown", function (e) {
        if (e.key !== "Enter" && e.key !== " ") return;
        var card = e.target.closest(".studio-longshot-card");
        if (card) { e.preventDefault(); open(card.getAttribute("data-sample")); }
      });
    }
    modal.querySelectorAll("[data-close]").forEach(function (el) {
      el.addEventListener("click", close);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !modal.hidden) close();
    });
    if (cta) cta.addEventListener("click", function () {
      close();
      openImportSheet();
      localStorage.setItem(LS.demoTried, "1");
    });
  }

  function initImportSheet() {
    ["studio-open-sheet", "studio-open-sheet-returning", "studio-path-toggle"].forEach(function (id) {
      var el = $(id);
      if (el) el.addEventListener("click", function () { openImportSheet(); });
    });
    var scrim = $("studio-sheet-scrim");
    if (scrim) scrim.addEventListener("click", function () {
      if (currentState !== "Importing") closeImportSheet();
    });
    var closeBtn = $("studio-sheet-close");
    if (closeBtn) closeBtn.addEventListener("click", closeImportSheet);
    var pick = $("studio-sheet-pick");
    if (pick) pick.addEventListener("click", function () {
      requestNativeFolder(null, null, { autoStart: false });
    });
    var startBtn = $("studio-sheet-start");
    if (startBtn) startBtn.addEventListener("click", function () { submitSheetImport(false); });
    var skipBtn = $("studio-sheet-skip");
    if (skipBtn) skipBtn.addEventListener("click", function () { submitSheetImport(true); });
    var titleInput = $("trip-title");
    if (titleInput) {
      titleInput.addEventListener("blur", saveIntent);
      titleInput.addEventListener("input", validateTitleField);
    }
    ["trip-place", "trip-feeling"].forEach(function (id) {
      var el = $(id);
      if (el) el.addEventListener("blur", saveIntent);
    });
    var help = $("studio-sheet-help");
    if (help) help.addEventListener("click", function () {
      if (typeof studioToast === "function") {
        studioToast(
          "同一次旅行的照片放一个文件夹（50–100 张最佳）。可建「精选」「素材」子文件夹。照片不会被移动或修改。",
          { duration: 6000 }
        );
      }
    });
    var coachSkip = $("studio-coach-skip");
    if (coachSkip) coachSkip.addEventListener("click", dismissCoach);
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && _sheetOpen && currentState !== "Importing") closeImportSheet();
    });
  }

  // ── Main init ──
  document.addEventListener("DOMContentLoaded", function () {
    initFooter();
    initCopyAddr();
    initPathToggle();
    initScrollHint();
    initTripsMore();
    initAdvancedOptions();
    renderSampleCards();
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
          transitionTo(tripsData.length > 0 ? "IdleReturning" : "IdleEmpty");
        });
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
      if (!pendingImport) {
        transitionTo(tripsData.length > 0 ? "IdleReturning" : "IdleEmpty");
        return;
      }
      if (pendingImport.uploadForm && pendingImport.files) {
        uploadAndImport(pendingImport.files, $("trip-title").value, $("trip-place").value);
        return;
      }
      startImport(pendingImport);
    });

    // Success: stay on home
    var stayBtn = $("studio-success-stay");
    if (stayBtn) stayBtn.addEventListener("click", function () {
      clearSuccessTimer();
      transitionTo(tripsData.length > 0 ? "IdleReturning" : "IdleEmpty");
    });
    var openBtn = $("studio-success-open");
    if (openBtn) openBtn.addEventListener("click", function () { clearSuccessTimer(); });
  });
})();
