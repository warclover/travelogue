(function () {
  "use strict";

  var STAGE_LABELS = {
    ingest: "正在导入",
    curate: "正在排版",
    narrate: "正在生成文案",
    render: "正在渲染",
  };

  var pendingImport = null;
  var activeJobId = null;
  var SLOW_JOB_MS = 30000;

  function studioAuthHeaders(extra) {
    var headers = extra || {};
    var meta = document.querySelector('meta[name="studio-token"]');
    var token = meta && meta.getAttribute("content");
    if (token) {
      headers["X-Studio-Token"] = token;
    }
    return headers;
  }

  function $(id) {
    return document.getElementById(id);
  }

  function show(el, visible) {
    if (!el) return;
    el.hidden = !visible;
  }

  function setError(msg) {
    var el = $("studio-error");
    if (!msg) {
      show(el, false);
      el.textContent = "";
      return;
    }
    el.textContent = msg;
    show(el, true);
  }

  function setWarning(msg) {
    var el = $("studio-warning");
    if (!msg) {
      show(el, false);
      el.textContent = "";
      return;
    }
    el.textContent = msg;
    show(el, true);
  }

  function showFailure(msg) {
    show($("studio-failure"), true);
    $("studio-failure-msg").textContent = msg || "导入失败";
    show($("studio-progress"), false);
    show($("studio-cancel"), false);
  }

  function hideFailure() {
    show($("studio-failure"), false);
    $("studio-failure-msg").textContent = "";
  }

  function setBusy(busy) {
    $("studio-submit-path").disabled = busy;
    var demoBtn = $("studio-demo-album");
    if (demoBtn) demoBtn.disabled = busy;
  }

  function formatUpdatedAt(ts) {
    if (!ts) return "";
    var d = new Date(ts * 1000);
    return d.toLocaleDateString("zh-CN");
  }

  function stageText(job) {
    var label = STAGE_LABELS[job.stage] || job.stage || "处理中";
    var idx = job.stageIndex || 0;
    var total = job.stageCount || 4;
    var hint = job.stageHint ? "（" + job.stageHint + "）" : "";
    return idx + "/" + total + " " + label + hint + "…";
  }

  function updateProgress(job) {
    show($("studio-progress"), true);
    hideFailure();
    $("studio-stage").textContent = stageText(job);
    var pct = ((job.stageIndex || 0) / (job.stageCount || 4)) * 100;
    $("studio-bar-fill").style.width = pct + "%";
    show($("studio-cancel"), job.status === "running" || job.status === "queued");
  }

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
      var progress = $("studio-progress");
      if (progress) progress.appendChild(el);
    }
    el.textContent = "比预期久一些，请耐心等待…";
    show(el, true);
  }

  function hideSlowHint() {
    var el = $("studio-slow-hint");
    if (el) show(el, false);
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

  function startImport(body) {
    pendingImport = body;
    setError("");
    hideFailure();
    setBusy(true);
    show($("studio-progress"), true);
    $("studio-stage").textContent = "准备导入…";
    $("studio-bar-fill").style.width = "0%";

    return postImport(body).then(function (result) {
      if (result.status === 409 && result.data.error === "E_DEMO_EXISTS") {
        var msg = result.data.message || "该游记已存在。是否覆盖？";
        if (window.confirm(msg)) {
          body.force = true;
          return startImport(body);
        }
        throw new Error("已取消覆盖");
      }
      if (result.status !== 202) {
        throw new Error(result.data.message || result.data.error || "导入失败");
      }
      return waitJob(result.data.jobId);
    }).then(function (job) {
      var url = job.result && job.result.previewUrl;
      if (url) {
        window.location.href = url;
      }
      loadTrips();
    }).catch(function (err) {
      if ((err.message || "") === "已取消") {
        setError("已取消导入");
        show($("studio-progress"), false);
        return;
      }
      showFailure(err.message || String(err));
    }).finally(function () {
      setBusy(false);
    });
  }

  function uploadAndImport(files) {
    if (!files || !files.length) return;
    if (files.length > 100) {
      setWarning("照片较多（" + files.length + " 张），建议精选后导入，效果更佳。");
    } else {
      setWarning("");
    }

    var form = new FormData();
    form.append("title", $("trip-title").value || "我的旅途");
    form.append("place", $("trip-place").value || "旅途");
    for (var i = 0; i < files.length; i++) {
      form.append("files[]", files[i], files[i].webkitRelativePath || files[i].name);
    }

    pendingImport = { uploadForm: true, files: files };
    setError("");
    hideFailure();
    setBusy(true);
    show($("studio-progress"), true);
    var progress = $("upload-progress");
    show(progress, true);
    progress.value = 0;

    return new Promise(function (resolve, reject) {
      var xhr = new XMLHttpRequest();
      xhr.open("POST", "/__travelogue/import");
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
        if (window.confirm(result.data.message || "该游记已存在。是否覆盖？")) {
          return uploadAndImportWithForce(files);
        }
        throw new Error("已取消覆盖");
      }
      if (result.status !== 202) {
        throw new Error(result.data.message || result.data.error || "上传失败");
      }
      return waitJob(result.data.jobId);
    }).then(function (job) {
      var url = job.result && job.result.previewUrl;
      if (url) window.location.href = url;
      loadTrips();
    }).catch(function (err) {
      if ((err.message || "") === "已取消") {
        setError("已取消导入");
        show($("studio-progress"), false);
        return;
      }
      showFailure(err.message || String(err));
    }).finally(function () {
      setBusy(false);
      show(progress, false);
    });
  }

  function uploadAndImportWithForce(files) {
    var retryForm = new FormData();
    retryForm.append("title", $("trip-title").value || "我的旅途");
    retryForm.append("place", $("trip-place").value || "旅途");
    retryForm.append("force", "true");
    for (var j = 0; j < files.length; j++) {
      retryForm.append("files[]", files[j], files[j].webkitRelativePath || files[j].name);
    }
    return new Promise(function (resolve, reject) {
      var xhr = new XMLHttpRequest();
      xhr.open("POST", "/__travelogue/import");
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

  function renderTripItem(trip) {
    var li = document.createElement("li");
    li.className = "studio__trip-item";
    var meta = document.createElement("div");
    meta.className = "studio__trip-meta";
    var title = document.createElement("strong");
    title.textContent = trip.title || trip.tripId;
    var sub = document.createElement("span");
    sub.className = "studio__trip-sub";
    var parts = [];
    if (trip.photoCount) parts.push(trip.photoCount + " 张");
    if (trip.updatedAt) parts.push(formatUpdatedAt(trip.updatedAt));
    if (trip.longshotStale) parts.push("长图待更新");
    sub.textContent = parts.join(" · ");
    meta.appendChild(title);
    meta.appendChild(sub);

    var actions = document.createElement("div");
    actions.className = "studio__trip-actions";
    var open = document.createElement("a");
    open.className = "studio__btn studio__btn--link";
    open.href = trip.previewUrl || ("/" + trip.tripId + "/index.html");
    open.textContent = "继续编辑";
    actions.appendChild(open);

    if (trip.previewRelPath) {
      var previewBtn = document.createElement("button");
      previewBtn.type = "button";
      previewBtn.className = "studio__btn studio__btn--ghost";
      previewBtn.textContent = "封面 preview.jpg";
      previewBtn.addEventListener("click", function () {
        fetch("/__travelogue/reveal", {
          method: "POST",
          headers: studioAuthHeaders({ "Content-Type": "application/json" }),
          body: JSON.stringify({ tripId: trip.tripId, relPath: trip.previewRelPath }),
        });
      });
      actions.appendChild(previewBtn);
    }

    li.appendChild(meta);
    li.appendChild(actions);
    return li;
  }

  function loadTrips() {
    fetch("/__travelogue/trips")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var trips = data.trips || [];
        if (!trips.length) {
          show($("studio-trips"), false);
          show($("studio-recent"), false);
          return;
        }

        show($("studio-trips"), true);
        show($("studio-recent"), false);
        var list = $("studio-trips-list");
        list.innerHTML = "";
        trips.forEach(function (trip) {
          list.appendChild(renderTripItem(trip));
        });
      })
      .catch(function () {});
  }

  document.addEventListener("DOMContentLoaded", function () {
    loadTrips();

    $("studio-import-form").addEventListener("submit", function (ev) {
      ev.preventDefault();
      var path = ($("album-path").value || "").trim();
      if (!path) {
        setError("请填写照片文件夹路径");
        return;
      }
      startImport({
        albumPath: path,
        title: $("trip-title").value || "我的旅途",
        place: $("trip-place").value || "旅途",
        force: false,
      });
    });

    $("studio-demo-album").addEventListener("click", function () {
      startImport({
        useDemoAlbum: true,
        title: "示例旅途",
        place: "示例",
        force: false,
      });
    });

    $("album-upload").addEventListener("change", function (ev) {
      var files = ev.target.files;
      uploadAndImport(files);
      ev.target.value = "";
    });

    $("studio-cancel").addEventListener("click", function () {
      cancelActiveJob().then(function () {
        setError("正在取消…");
      });
    });

    $("studio-retry").addEventListener("click", function () {
      hideFailure();
      if (!pendingImport) return;
      if (pendingImport.uploadForm && pendingImport.files) {
        uploadAndImport(pendingImport.files);
        return;
      }
      startImport(pendingImport);
    });
  });
})();
