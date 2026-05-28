/**
 * Travelogue Studio — M12 Homepage Controller
 * State machine: Loading → IdleEmpty / IdleReturning → Importing → FirstSuccess → Preview
 *                                                       → Failed → Importing/IdleEmpty
 *                                                       → Offline
 */
(function () {
  "use strict";

  // ── Stage user-facing labels (§8.2) ──
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
  };

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
  var HEALTH_INTERVAL = 30000;

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
      if (progressEl) {
        progressEl.textContent = msg;
        show(progressEl, true);
      }
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
    if (!msg) { show(el, false); el.textContent = ""; return; }
    el.textContent = msg;
    show(el, true);
  }

  function showFailure(msg, echoPath) {
    show($("studio-failure"), true);
    show($("studio-progress-section"), false);
    $("studio-failure-msg").textContent = msg || "导入失败";
    var echoEl = $("studio-failure-echo");
    if (echoPath) {
      echoEl.textContent = echoPath;
      show(echoEl, true);
    } else {
      show(echoEl, false);
    }
    setTitle("导入失败");
  }

  function hideFailure() {
    show($("studio-failure"), false);
    $("studio-failure-msg").textContent = "";
    show($("studio-failure-echo"), false);
    setTitle();
  }

  function setBusy(busy) {
    var ids = ["studio-pick-folder", "studio-pick-folder-returning",
               "studio-submit-path", "studio-submit-path-returning",
               "studio-demo-album", "studio-demo-album-returning"];
    ids.forEach(function (id) {
      var el = $(id);
      if (el) el.disabled = busy || isOffline;
    });
    // Also disable file inputs when offline
    var uploadInputs = document.querySelectorAll(".studio__import-section input[type=file]");
    for (var i = 0; i < uploadInputs.length; i++) {
      uploadInputs[i].disabled = isOffline;
    }
  }

  // ── State machine ──
  function transitionTo(state) {
    currentState = state;
    render();
  }

  function render() {
    var hasTrips = tripsData.length > 0;
    var isImporting = currentState === "Importing";
    var isFailed = currentState === "Failed";

    // Title
    if (currentState === "Importing") setTitle("正在生成…");
    else if (currentState === "Failed") setTitle("导入失败");
    else setTitle();

    // Offline banner
    show($("studio-offline"), isOffline);

    // Disable import actions when offline (AC-HP-13)
    var offlineIds = ["studio-pick-folder", "studio-pick-folder-returning",
                      "studio-submit-path", "studio-submit-path-returning",
                      "studio-demo-album", "studio-demo-album-returning"];
    offlineIds.forEach(function (id) {
      var el = $(id);
      if (el) el.disabled = isOffline;
    });
    // Also disable file inputs so wrapped <label> clicks are inert
    var uploadInputs = document.querySelectorAll(".studio__import-section input[type=file]");
    for (var ui = 0; ui < uploadInputs.length; ui++) {
      uploadInputs[ui].disabled = isOffline;
    }

    // Status dot
    var dot = $("studio-status-dot");
    var statusText = $("studio-status-text");
    if (isOffline) {
      dot.className = "studio__topbar-dot studio__topbar-dot--offline";
      statusText.textContent = "未连接";
    } else {
      dot.className = "studio__topbar-dot";
      statusText.textContent = "本地运行中";
    }

    // Hero
    show($("studio-hero-magazine"), !hasTrips && !isImporting && !isFailed);
    show($("studio-hero-compact"), hasTrips && !isImporting && !isFailed);

    // C · Recent (show during loading + returning)
    var showRecent = hasTrips && !isImporting && !isFailed;
    show($("studio-recent"), showRecent || currentState === "Loading");
    var recentTitle = $("studio-recent-title");
    if (currentState === "Loading") {
      // Hide title during loading — skeleton alone is enough
      if (recentTitle) show(recentTitle, false);
      show($("studio-recent-skeleton"), true);
      show($("studio-recent-list"), false);
    } else if (showRecent) {
      if (recentTitle) show(recentTitle, true);
      show($("studio-recent-skeleton"), false);
      show($("studio-recent-list"), true);
      renderRecentTrips();
    }

    // D' (empty) / D (returning) / skeleton
    var showImportEmpty = !hasTrips && !isImporting && !isFailed && currentState !== "Loading";
    var showImportReturning = hasTrips && !isImporting && !isFailed;
    show($("studio-import-empty"), showImportEmpty);
    show($("studio-import-returning"), showImportReturning);
    show($("studio-import-skeleton"), currentState === "Loading" && !hasTrips);

    // Gallery
    var showGallery = !hasTrips && !isImporting && !isFailed;
    show($("studio-gallery"), showGallery);
    if (showGallery) {
      // Ensure reveal animation fires after hidden→visible transition
      requestAnimationFrame(function () {
        var g = $("studio-gallery");
        if (g && !g.classList.contains("is-revealed")) g.classList.add("is-revealed");
      });
    }
    show($("studio-gallery-compact"), hasTrips && !isImporting && !isFailed);
    if (hasTrips && !isImporting && !isFailed) {
      requestAnimationFrame(function () {
        var gc = $("studio-gallery-compact");
        if (gc && !gc.classList.contains("is-revealed")) gc.classList.add("is-revealed");
      });
    }

    // F · All trips
    show($("studio-trips"), hasTrips && tripsData.length >= 2 && !isImporting && !isFailed);
    if (hasTrips && !isImporting && !isFailed) {
      renderAllTrips();
    }

    // Progress
    show($("studio-progress-section"), isImporting);
    // Failure
    show($("studio-failure"), isFailed);
  }

  // ── Trip card rendering ──
  function formatUpdatedAt(ts) {
    if (!ts) return "";
    var d = new Date(ts * 1000);
    return d.toLocaleDateString("zh-CN");
  }

  function createThumbPlaceholder() {
    var div = document.createElement("div");
    div.className = "studio__trip-thumb studio__trip-thumb--placeholder";
    div.textContent = "preview";
    return div;
  }

  function renderTripCard(trip, options) {
    options = options || {};
    var wrap = document.createElement("div");
    wrap.className = "studio__trip-card-wrap";

    // Highlight for first return (most recent trip only)
    var needsHighlight = false;
    if (options.highlight &&
        localStorage.getItem(LS.firstPreviewDone) === "1" &&
        !localStorage.getItem(LS.firstReturnHighlight) &&
        currentState === "IdleReturning") {
      needsHighlight = true;
    }

    if (needsHighlight) {
      wrap.classList.add("studio__trip-card-wrap--highlight");
      var tooltip = document.createElement("span");
      tooltip.className = "studio__trip-highlight-tooltip";
      tooltip.textContent = "你的游记在这里，点击继续编辑";
      wrap.appendChild(tooltip);
      setTimeout(function () {
        wrap.classList.remove("studio__trip-card-wrap--highlight");
        if (tooltip.parentNode) tooltip.remove();
        localStorage.setItem(LS.firstReturnHighlight, "1");
      }, 5000);
      wrap.addEventListener("click", function dismiss() {
        wrap.classList.remove("studio__trip-card-wrap--highlight");
        if (tooltip.parentNode) tooltip.remove();
        localStorage.setItem(LS.firstReturnHighlight, "1");
        wrap.removeEventListener("click", dismiss);
      });
    }

    var card = document.createElement("div");
    card.className = "studio__trip-card";

    // Thumbnail: use <div> placeholder when no preview, <img> otherwise
    var thumb;
    if (trip.previewRelPath) {
      thumb = document.createElement("img");
      thumb.className = "studio__trip-thumb";
      thumb.alt = trip.title || "游记";
      thumb.loading = "lazy";
      thumb.src = "/" + trip.tripId + "/" + trip.previewRelPath;
      thumb.onerror = function () {
        // Replace broken <img> with placeholder <div>
        var placeholder = createThumbPlaceholder();
        thumb.parentNode.replaceChild(placeholder, thumb);
      };
    } else {
      thumb = createThumbPlaceholder();
    }

    // Info
    var info = document.createElement("div");
    info.className = "studio__trip-info";

    var name = document.createElement("p");
    name.className = "studio__trip-name";
    name.textContent = trip.title || trip.tripId;
    name.title = trip.title || trip.tripId;

    // Check if demo trip
    var isDemo = trip.tripId && trip.tripId.indexOf("demo") >= 0;
    if (isDemo) {
      var demoBadge = document.createElement("span");
      demoBadge.className = "studio__badge studio__badge--demo";
      demoBadge.textContent = "示例";
      name.appendChild(document.createTextNode(" "));
      name.appendChild(demoBadge);
    }

    var meta = document.createElement("p");
    meta.className = "studio__trip-meta";
    var parts = [];
    if (trip.photoCount) parts.push(trip.photoCount + " 张");
    if (trip.updatedAt) parts.push(formatUpdatedAt(trip.updatedAt));
    meta.textContent = parts.join(" · ");
    if (trip.longshotStale) {
      var staleBadge = document.createElement("span");
      staleBadge.className = "studio__badge studio__badge--stale";
      staleBadge.textContent = "长图待更新";
      meta.appendChild(document.createTextNode(" · "));
      meta.appendChild(staleBadge);
    }

    var actions = document.createElement("div");
    actions.className = "studio__trip-actions";

    // Primary button: "更新长图" if stale, "继续编辑" otherwise
    var primaryBtn = document.createElement("a");
    primaryBtn.className = "studio__btn studio__btn--primary studio__btn--sm";
    if (trip.longshotStale) {
      primaryBtn.textContent = "更新长图";
      primaryBtn.href = "/" + trip.tripId + "/index.html?focus=longshot";
    } else {
      primaryBtn.textContent = "继续编辑";
      primaryBtn.href = trip.previewUrl || ("/" + trip.tripId + "/index.html");
    }

    var revealBtn = document.createElement("button");
    revealBtn.type = "button";
    revealBtn.className = "studio__btn studio__btn--ghost studio__btn--sm";
    revealBtn.textContent = "显示封面";
    revealBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      if (trip.previewRelPath) {
        fetch("/__travelogue/reveal", {
          method: "POST",
          headers: studioAuthHeaders({ "Content-Type": "application/json" }),
          body: JSON.stringify({ tripId: trip.tripId, relPath: trip.previewRelPath }),
        });
      }
    });

    actions.appendChild(primaryBtn);
    actions.appendChild(revealBtn);

    info.appendChild(name);
    info.appendChild(meta);
    info.appendChild(actions);

    // Chevron
    var chevron = document.createElement("span");
    chevron.className = "studio__trip-chevron";
    chevron.textContent = "→";

    card.appendChild(thumb);
    card.appendChild(info);
    card.appendChild(chevron);
    wrap.appendChild(card);

    // Whole card clickable
    wrap.addEventListener("click", function (e) {
      if (e.target.closest("a") || e.target.closest("button")) return;
      window.location.href = primaryBtn.href;
    });

    return wrap;
  }

  function renderRecentTrips() {
    var container = $("studio-recent-list");
    container.innerHTML = "";
    var recent = tripsData.slice(0, 3);
    recent.forEach(function (trip, index) {
      container.appendChild(renderTripCard(trip, { highlight: index === 0 }));
    });

    // Demo nudge: if only demo trips
    var hasUserTrips = tripsData.some(function (t) {
      return !t.tripId || t.tripId.indexOf("demo") < 0;
    });
    var hasDemoTrips = tripsData.some(function (t) {
      return t.tripId && t.tripId.indexOf("demo") >= 0;
    });
    if (hasDemoTrips && !hasUserTrips) {
      var nudge = document.createElement("a");
      nudge.className = "studio__demo-nudge";
      nudge.href = "#studio-import-returning";
      nudge.textContent = "试试用自己的照片做一篇 →";
      container.appendChild(nudge);
    }
  }

  function renderAllTrips() {
    var list = $("studio-trips-list");
    list.innerHTML = "";
    tripsData.forEach(function (trip) {
      var li = document.createElement("li");
      li.style.marginBottom = "12px";
      li.appendChild(renderTripCard(trip));
      list.appendChild(li);
    });
    // Show "more" button when backend may have truncated (limit 20)
    var moreBtn = $("studio-trips-more");
    if (moreBtn) {
      show(moreBtn, tripsData.length < tripsTotalCount);
    }
  }

  // ── Progress ──
  function stageText(job) {
    var label = STAGE_LABELS[job.stage] || "处理中…";
    var idx = job.stageIndex || 0;
    var total = job.stageCount || 4;
    var hint = job.stageHint ? "（" + job.stageHint + "）" : "";
    return idx + "/" + total + " " + label + hint;
  }

  function updateProgress(job) {
    show($("studio-progress-section"), true);
    hideFailure();
    $("studio-stage").textContent = stageText(job);
    var pct = ((job.stageIndex || 0) / (job.stageCount || 4)) * 100;
    $("studio-bar-fill").style.width = pct + "%";
    show($("studio-cancel"), job.status === "running" || job.status === "queued");
  }

  // ── Job polling ──
  function pollJob(jobId) {
    return fetch("/__travelogue/status?jobId=" + encodeURIComponent(jobId))
      .then(function (r) { return r.json(); });
  }

  function cancelActiveJob() {
    if (!activeJobId) return Promise.resolve();
    return fetch("/__travelogue/cancel", {
      method: "POST",
      headers: studioAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ jobId: activeJobId }),
    }).finally(function () {
      activeJobId = null;
      show($("studio-cancel"), false);
      setBusy(false);
    });
  }

  function showSlowHint() {
    var el = $("studio-slow-hint");
    if (!el) {
      el = document.createElement("p");
      el.id = "studio-slow-hint";
      el.className = "studio__slow-hint";
      $("studio-progress").appendChild(el);
    }
    el.textContent = "比预期久一些，请耐心等待…";
    show(el, true);
  }

  function hideSlowHint() {
    var el = $("studio-slow-hint");
    if (el) show(el, false);
  }

  function isFirstTime() {
    return !localStorage.getItem(LS.firstPreviewDone);
  }

  function markFirstPreviewDone(tripId) {
    localStorage.setItem(LS.firstPreviewDone, "1");
    if (tripId) localStorage.setItem("travelogue.studio.firstTripId", tripId);
  }

  function waitJob(jobId) {
    activeJobId = jobId;
    var started = Date.now();
    var slowShown = false;
    hideSlowHint();

    return new Promise(function (resolve, reject) {
      function tick() {
        pollJob(jobId).then(function (job) {
          if (!slowShown && Date.now() - started > SLOW_JOB_MS) {
            slowShown = true;
            showSlowHint();
          }
          if (job.status === "running" || job.status === "queued") {
            updateProgress(job);
            setTimeout(tick, 500);
            return;
          }
          activeJobId = null;
          show($("studio-cancel"), false);
          hideSlowHint();
          if (job.status === "succeeded") {
            updateProgress(job);
            resolve(job);
            return;
          }
          if (job.status === "cancelled") {
            reject(new Error("已取消"));
            return;
          }
          var msg = (job.error && (job.error.message || job.error.code)) || "导入失败";
          reject(new Error(msg));
        }).catch(reject);
      }
      tick();
    });
  }

  // ── Import flows ──
  function postImport(body) {
    return fetch("/__travelogue/import", {
      method: "POST",
      headers: studioAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(body),
    }).then(function (resp) {
      return resp.json().then(function (data) {
        return { status: resp.status, data: data };
      });
    });
  }

  function handleImportSuccess(job) {
    var url = job.result && job.result.previewUrl;
    var tripId = job.result && job.result.tripId;
    var first = isFirstTime();

    if (first) {
      markFirstPreviewDone(tripId);
      if (typeof studioToast === "function") {
        studioToast("你的第一篇游记已生成，正在打开预览…", { duration: 5000, large: true });
      }
      setTimeout(function () {
        if (url) window.location.href = url;
      }, 800);
    } else {
      if (typeof studioToast === "function") {
        studioToast("生成完成，正在打开…", { duration: 3000 });
      }
      setTimeout(function () {
        if (url) window.location.href = url;
      }, 300);
    }
  }

  function startImport(body) {
    pendingImport = body;
    setError("");
    hideFailure();
    setBusy(true);
    transitionTo("Importing");
    show($("studio-progress-section"), true);
    $("studio-stage").textContent = "准备导入…";
    $("studio-bar-fill").style.width = "0%";

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
      return waitJob(result.data.jobId);
    }).then(function (job) {
      handleImportSuccess(job);
      loadTrips();
    }).catch(function (err) {
      if ((err.message || "") === "已取消") {
        setError("已取消导入");
        transitionTo(tripsData.length > 0 ? "IdleReturning" : "IdleEmpty");
        return;
      }
      if ((err.message || "") === "已取消覆盖") {
        transitionTo(tripsData.length > 0 ? "IdleReturning" : "IdleEmpty");
        return;
      }
      // Build echo path for failure
      var echoPath = "";
      if (pendingImport && pendingImport.albumPath) {
        echoPath = pendingImport.albumPath;
      }
      transitionTo("Failed");
      showFailure(err.message || String(err), echoPath);
    }).finally(function () {
      setBusy(false);
    });
  }

  function uploadAndImport(files, titleVal, placeVal) {
    if (!files || !files.length) return;
    if (files.length > 100) {
      setWarning("照片较多（" + files.length + " 张），建议精选后导入，效果更佳。");
    } else {
      setWarning("");
    }

    var form = new FormData();
    form.append("title", titleVal || "我的旅途");
    form.append("place", placeVal || "旅途");
    for (var i = 0; i < files.length; i++) {
      form.append("files[]", files[i], files[i].webkitRelativePath || files[i].name);
    }

    pendingImport = { uploadForm: true, files: files, fileCount: files.length };
    setError("");
    hideFailure();
    setBusy(true);
    transitionTo("Importing");
    show($("studio-progress-section"), true);
    var progress = $("upload-progress");
    show(progress, true);
    progress.value = 0;

    return new Promise(function (resolve, reject) {
      var xhr = new XMLHttpRequest();
      xhr.open("POST", "/__travelogue/import");
      var token = (document.querySelector('meta[name="studio-token"]') || {}).content;
      if (token) xhr.setRequestHeader("X-Studio-Token", token);
      xhr.upload.onprogress = function (ev) {
        if (ev.lengthComputable) {
          progress.value = Math.round((ev.loaded / ev.total) * 100);
        }
      };
      xhr.onload = function () {
        var data = {};
        try { data = JSON.parse(xhr.responseText || "{}"); } catch (e) {}
        resolve({ status: xhr.status, data: data });
      };
      xhr.onerror = function () { reject(new Error("上传失败")); };
      xhr.send(form);
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
          return uploadAndImportWithForce(files, titleVal, placeVal);
        });
      }
      if (result.status !== 202) {
        throw new Error(result.data.message || result.data.error || "上传失败");
      }
      return waitJob(result.data.jobId);
    }).then(function (job) {
      handleImportSuccess(job);
      loadTrips();
    }).catch(function (err) {
      if ((err.message || "") === "已取消" || (err.message || "") === "已取消覆盖") {
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
      setBusy(false);
      show(progress, false);
    });
  }

  function uploadAndImportWithForce(files, titleVal, placeVal) {
    var retryForm = new FormData();
    retryForm.append("title", titleVal || "我的旅途");
    retryForm.append("place", placeVal || "旅途");
    retryForm.append("force", "true");
    for (var j = 0; j < files.length; j++) {
      retryForm.append("files[]", files[j], files[j].webkitRelativePath || files[j].name);
    }
    return new Promise(function (resolve, reject) {
      var xhr = new XMLHttpRequest();
      xhr.open("POST", "/__travelogue/import");
      var token = (document.querySelector('meta[name="studio-token"]') || {}).content;
      if (token) xhr.setRequestHeader("X-Studio-Token", token);
      xhr.onload = function () {
        var data = {};
        try { data = JSON.parse(xhr.responseText || "{}"); } catch (e) {}
        resolve({ status: xhr.status, data: data });
      };
      xhr.onerror = function () { reject(new Error("上传失败")); };
      xhr.send(retryForm);
    }).then(function (retryResult) {
      if (retryResult.status !== 202) {
        throw new Error(retryResult.data.message || retryResult.data.error || "上传失败");
      }
      return waitJob(retryResult.data.jobId);
    });
  }

  // ── Load trips (with timeout handling per §6.12) ──
  function loadTrips(options) {
    options = options || {};
    if (options.more) {
      tripsListLimit += 20;
    } else if (options.keepLimit !== true) {
      tripsListLimit = 20;
    }

    var slowToastShown = false;
    var failToastShown = false;
    var slowTimer = setTimeout(function () {
      slowToastShown = true;
      if (typeof studioToast === "function") {
        studioToast("加载较慢，请稍候", { duration: 4000 });
      }
    }, 3000);
    var failTimer = setTimeout(function () {
      failToastShown = true;
      if (typeof studioToast === "function") {
        studioToast("加载失败，请检查 Studio 是否运行", { duration: 5000 });
      }
    }, 10000);

    fetch("/__travelogue/trips?limit=" + encodeURIComponent(String(tripsListLimit)))
      .then(function (r) {
        if (!r.ok) throw new Error("trips unavailable");
        return r.json();
      })
      .then(function (data) {
        clearTimeout(slowTimer);
        clearTimeout(failTimer);
        tripsData = data.trips || [];
        tripsTotalCount = typeof data.total === "number" ? data.total : tripsData.length;
        if (currentState === "Loading" || currentState === "IdleEmpty" || currentState === "IdleReturning") {
          transitionTo(tripsData.length > 0 ? "IdleReturning" : "IdleEmpty");
        } else {
          render();
        }
      })
      .catch(function () {
        clearTimeout(slowTimer);
        clearTimeout(failTimer);
        isOffline = true;
        render();
        if (tripsData.length === 0) {
          transitionTo("IdleEmpty");
          if (!failToastShown && !slowToastShown) {
            if (typeof studioToast === "function") {
              studioToast("加载失败，请检查 Studio 是否运行", { duration: 5000 });
            }
          }
        }
      });
  }

  // ── Health check / Offline detection ──
  function startHealthCheck() {
    function check() {
      fetch("/__travelogue/trips", { method: "GET" })
        .then(function (r) {
          var wasOffline = isOffline;
          isOffline = !r.ok;
          if (wasOffline && !isOffline) {
            if (typeof studioToast === "function") {
              studioToast("服务已恢复", { duration: 2000 });
            }
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

  // ── Gallery initialization ──
  function initGallery() {
    var carousel = $("studio-gallery-carousel");
    if (carousel && typeof studioGallery === "function") {
      studioGallery(carousel, {
        prevBtn: $("studio-gallery-prev"),
        nextBtn: $("studio-gallery-next"),
        indicator: $("studio-gallery-indicator"),
      });
    }
    var carouselCompact = $("studio-gallery-carousel-compact");
    if (carouselCompact && typeof studioGallery === "function") {
      studioGallery(carouselCompact);
    }
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
        toggle.textContent = visible ? "了解如何发微信 ▸" : "了解如何发微信 ▾";
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
          if (typeof studioToast === "function") {
            studioToast("已复制", { duration: 1500 });
          }
        });
      }
    });
  }

  // ── Path form toggles ──
  function initPathToggles() {
    var toggle = $("studio-path-toggle");
    var form = $("studio-import-form");
    if (toggle && form) {
      toggle.addEventListener("click", function () {
        form.classList.toggle("is-visible");
      });
    }

    var toggleR = $("studio-path-toggle-returning");
    var formR = $("studio-import-form-returning");
    if (toggleR && formR) {
      toggleR.addEventListener("click", function () {
        formR.classList.toggle("is-visible");
      });
    }
  }

  // ── "View more" trips ──
  function initTripsMore() {
    var moreBtn = $("studio-trips-more");
    if (!moreBtn) return;
    moreBtn.addEventListener("click", function () {
      loadTrips({ more: true });
    });
  }

  // ── Main init ──
  document.addEventListener("DOMContentLoaded", function () {
    initGallery();
    initFooter();
    initCopyAddr();
    initPathToggles();
    initTripsMore();

    // Start loading
    transitionTo("Loading");
    loadTrips();
    startHealthCheck();

    // ── Event bindings ──

    // Primary folder pick (Hero)
    $("studio-pick-folder").addEventListener("click", function () {
      $("studio-folder-input").click();
    });
    $("studio-folder-input").addEventListener("change", function (ev) {
      var files = ev.target.files;
      if (!files || !files.length) return;
      uploadAndImport(files, $("trip-title").value, $("trip-place").value);
      ev.target.value = "";
    });

    // Primary folder pick (Returning)
    $("studio-pick-folder-returning").addEventListener("click", function () {
      $("studio-folder-input-returning").click();
    });
    $("studio-folder-input-returning").addEventListener("change", function (ev) {
      var files = ev.target.files;
      if (!files || !files.length) return;
      uploadAndImport(files, $("trip-title-returning").value, $("trip-place-returning").value);
      ev.target.value = "";
    });

    // Path form submit (empty)
    $("studio-import-form").addEventListener("submit", function (ev) {
      ev.preventDefault();
      var path = ($("album-path").value || "").trim();
      if (!path) { setError("请填写照片文件夹路径"); return; }
      startImport({
        albumPath: path,
        title: $("trip-title").value || "我的旅途",
        place: $("trip-place").value || "旅途",
        force: false,
      });
    });

    // Path form submit (returning)
    $("studio-import-form-returning").addEventListener("submit", function (ev) {
      ev.preventDefault();
      var path = ($("album-path-returning").value || "").trim();
      if (!path) { setError("请填写照片文件夹路径"); return; }
      startImport({
        albumPath: path,
        title: $("trip-title-returning").value || "我的旅途",
        place: $("trip-place-returning").value || "旅途",
        force: false,
      });
    });

    // Demo album (empty)
    $("studio-demo-album").addEventListener("click", function () {
      localStorage.setItem(LS.demoTried, "1");
      startImport({
        useDemoAlbum: true,
        title: "示例旅途",
        place: "示例",
        force: false,
      });
    });

    // Demo album (returning)
    $("studio-demo-album-returning").addEventListener("click", function () {
      localStorage.setItem(LS.demoTried, "1");
      startImport({
        useDemoAlbum: true,
        title: "示例旅途",
        place: "示例",
        force: false,
      });
    });

    // Browser upload (empty)
    $("album-upload").addEventListener("change", function (ev) {
      uploadAndImport(ev.target.files, $("trip-title").value, $("trip-place").value);
      ev.target.value = "";
    });

    // Browser upload (returning)
    $("album-upload-returning").addEventListener("change", function (ev) {
      uploadAndImport(ev.target.files, $("trip-title-returning").value, $("trip-place-returning").value);
      ev.target.value = "";
    });

    // Cancel: confirm first, then cancel job
    $("studio-cancel").addEventListener("click", function () {
      var doCancel = function () {
        cancelActiveJob().then(function () {
          transitionTo(tripsData.length > 0 ? "IdleReturning" : "IdleEmpty");
        });
      };
      if (typeof studioModal === "function") {
        studioModal({
          title: "确定取消？",
          body: "取消后将丢失当前进度。",
          confirmText: "确定取消",
          cancelText: "继续等待",
        }).then(function (confirmed) {
          if (confirmed) doCancel();
        });
      } else if (window.confirm("确定取消导入？")) {
        doCancel();
      }
    });

    // Retry
    $("studio-retry").addEventListener("click", function () {
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
  });
})();
