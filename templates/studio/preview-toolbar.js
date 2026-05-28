(function () {
  "use strict";

  var HINT_KEY = "travelogue.studio.editHint.dismissed";
  var COLLAPSE_KEY = "travelogue.studio.previewToolbar.collapsed";
  var LONGSHOT_SCALE = 2;
  var SLOW_JOB_MS = 30000;
  var pollTimer = null;
  var longshotJobId = null;
  var narrateJobId = null;

  function tripIdFromPath() {
    var parts = window.location.pathname.replace(/^\/+|\/+$/g, "").split("/");
    return parts[0] || "";
  }

  function studioAuthHeaders() {
    var headers = { "Content-Type": "application/json" };
    var meta = document.querySelector('meta[name="studio-token"]');
    var token = meta && meta.getAttribute("content");
    if (token) {
      headers["X-Studio-Token"] = token;
    }
    return headers;
  }

  function postJson(url, payload) {
    return fetch(url, {
      method: "POST",
      headers: studioAuthHeaders(),
      body: JSON.stringify(payload || {}),
    }).then(function (resp) {
      return resp.json().then(function (body) {
        return { status: resp.status, body: body };
      });
    });
  }

  function revealTripPath(tripId, relPath) {
    return postJson("/__travelogue/reveal", { tripId: tripId, relPath: relPath });
  }

  function pollJob(jobId, onDone, onSlow) {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
    var started = Date.now();
    var slowShown = false;
    pollTimer = setInterval(function () {
      if (onSlow && !slowShown && Date.now() - started > SLOW_JOB_MS) {
        slowShown = true;
        onSlow();
      }
      fetch("/__travelogue/status?jobId=" + encodeURIComponent(jobId))
        .then(function (resp) { return resp.json(); })
        .then(function (job) {
          if (
            job.status === "succeeded" ||
            job.status === "failed" ||
            job.status === "cancelled"
          ) {
            clearInterval(pollTimer);
            pollTimer = null;
            onDone(job);
          }
        })
        .catch(function () {});
    }, 800);
  }

  function setLongshotStatus(root, text, visible) {
    var status = root.querySelector(".preview-toolbar__longshot-status");
    if (!status) return;
    status.hidden = !visible;
    status.textContent = text || "";
  }

  function setSlowHint(root, text, visible) {
    var el = root.querySelector(".preview-toolbar__slow-hint");
    if (!el) {
      el = document.createElement("span");
      el.className = "preview-toolbar__slow-hint";
      el.hidden = true;
      var bar = root.querySelector(".preview-toolbar__bar");
      if (bar) bar.appendChild(el);
    }
    el.hidden = !visible;
    el.textContent = text || "";
  }

  function toolbarBody(root) {
    return root.querySelector(".preview-toolbar__body") || root;
  }

  function syncToolbarHeight(root) {
    var collapsed = root.classList.contains("preview-toolbar--collapsed");
    var handle = root.querySelector(".preview-toolbar__handle");
    if (collapsed) {
      var hh = (handle && handle.offsetHeight) || 32;
      root.style.height = hh + "px";
      document.documentElement.style.setProperty("--preview-toolbar-h", hh + "px");
      return;
    }
    root.style.height = "";
    document.documentElement.style.setProperty(
      "--preview-toolbar-h",
      (root.offsetHeight || 56) + "px"
    );
  }

  function setToolbarCollapsed(root, collapsed, persist) {
    root.classList.toggle("preview-toolbar--collapsed", collapsed);
    document.documentElement.setAttribute(
      "data-preview-toolbar-collapsed",
      collapsed ? "on" : "off"
    );
    var handle = root.querySelector(".preview-toolbar__handle");
    var collapseBtn = root.querySelector(".preview-toolbar__collapse");
    if (handle) {
      handle.setAttribute("aria-expanded", collapsed ? "false" : "true");
    }
    if (collapseBtn) {
      collapseBtn.setAttribute("aria-expanded", collapsed ? "false" : "true");
    }
    if (persist !== false) {
      try {
        localStorage.setItem(COLLAPSE_KEY, collapsed ? "1" : "0");
      } catch (e) {}
    }
    requestAnimationFrame(function () {
      syncToolbarHeight(root);
    });
  }

  function toggleToolbarCollapsed(root) {
    setToolbarCollapsed(root, !root.classList.contains("preview-toolbar--collapsed"));
  }

  function bindToolbarCollapse(root) {
    var handle = root.querySelector(".preview-toolbar__handle");
    var collapseBtn = root.querySelector(".preview-toolbar__collapse");
    if (handle) {
      handle.addEventListener("click", function () {
        setToolbarCollapsed(root, false);
      });
    }
    if (collapseBtn) {
      collapseBtn.addEventListener("click", function () {
        setToolbarCollapsed(root, true);
      });
    }
    if (typeof ResizeObserver !== "undefined") {
      var ro = new ResizeObserver(function () {
        syncToolbarHeight(root);
      });
      ro.observe(root);
    }
    window.addEventListener("resize", function () {
      syncToolbarHeight(root);
    });
  }

  function showLongshotPanel(root, job) {
    var tripId = tripIdFromPath();
    var body = toolbarBody(root);
    var panel = body.querySelector(".preview-toolbar__longshot-panel");
    if (!panel) {
      panel = document.createElement("div");
      panel.className = "preview-toolbar__longshot-panel";
      body.appendChild(panel);
    }
    setToolbarCollapsed(root, false, false);
    panel.hidden = false;
    panel.textContent = "";

    if (job.status === "failed") {
      var err = (job.error && (job.error.message || job.error.code)) || "导出失败";
      var errEl = document.createElement("p");
      errEl.className = "preview-toolbar__longshot-error";
      errEl.textContent = err;
      panel.appendChild(errEl);
      return;
    }

    var result = job.result || {};
    var outputs = result.outputs || [];
    var method = result.captureMethod || "p0";
    var segmented = result.segmented || outputs.length > 1;

    var okEl = document.createElement("p");
    okEl.className = "preview-toolbar__longshot-ok";
    okEl.textContent = "长图已保存";
    panel.appendChild(okEl);

    if (segmented && outputs.length > 1) {
      var segEl = document.createElement("p");
      segEl.className = "preview-toolbar__longshot-compat";
      segEl.textContent =
        "已按章导出 " + outputs.length + " 张，底部含页码（如 2/5）便于微信按序发送。";
      panel.appendChild(segEl);
    }
    if (method === "p1") {
      var compatEl = document.createElement("p");
      compatEl.className = "preview-toolbar__longshot-compat";
      compatEl.textContent = "已使用兼容模式导出，与预览可能有细微差异。";
      panel.appendChild(compatEl);
    }
    if (outputs.length) {
      var list = document.createElement("ul");
      list.className = "preview-toolbar__longshot-paths";
      outputs.forEach(function (rel) {
        var li = document.createElement("li");
        li.textContent = rel;
        list.appendChild(li);
      });
      panel.appendChild(list);

      var revealBtn = document.createElement("button");
      revealBtn.type = "button";
      revealBtn.className = "preview-toolbar__reveal";
      revealBtn.textContent = "在文件夹中显示";
      revealBtn.addEventListener("click", function () {
        revealTripPath(tripId, outputs[0]);
      });
      panel.appendChild(revealBtn);
    }
    hideStaleHint(root);
  }

  function staleHintEl(root) {
    return root.querySelector(".preview-toolbar__stale");
  }

  function showStaleHint(root) {
    var el = staleHintEl(root);
    if (el) el.hidden = false;
  }

  function hideStaleHint(root) {
    var el = staleHintEl(root);
    if (el) el.hidden = true;
  }

  function refreshStaleHint(root, tripId) {
    fetch("/__travelogue/trips")
      .then(function (resp) { return resp.json(); })
      .then(function (data) {
        var trips = data.trips || [];
        var trip = trips.filter(function (t) { return t.tripId === tripId; })[0];
        if (trip && trip.longshotStale) {
          showStaleHint(root);
        }
      })
      .catch(function () {});
  }

  function toggleAdvancedMenu(root) {
    var menu = root.querySelector(".preview-toolbar__menu");
    if (!menu) return;
    menu.hidden = !menu.hidden;
  }

  function exportZip(tripId) {
    if (!window.confirm("导出 zip 包用于自行托管或备份，不是微信分享主路径。继续？")) {
      return;
    }
    postJson("/__travelogue/export", { tripId: tripId, confirmPrivacy: true })
      .then(function (res) {
        if (res.status !== 200 || !res.body.ok) {
          window.alert((res.body && res.body.message) || "导出失败");
          return;
        }
        var zipRel = res.body.zipRelPath;
        if (zipRel && window.confirm("zip 已生成。在文件夹中显示？")) {
          revealTripPath(tripId, zipRel);
        }
      })
      .catch(function () {
        window.alert("导出失败");
      });
  }

  function startLongshot(root, tripId) {
    var btn = root.querySelector(".preview-toolbar__longshot");
    if (!btn || btn.disabled) return;
    setToolbarCollapsed(root, false, false);
    btn.disabled = true;
    setLongshotStatus(root, "正在生成长图…", true);
    setSlowHint(root, "", false);

    postJson("/__travelogue/longshot", {
      tripId: tripId,
      scale: LONGSHOT_SCALE,
      format: "png",
    })
      .then(function (res) {
        if (res.status === 409) {
          setLongshotStatus(root, (res.body && res.body.message) || "请稍候再试", true);
          btn.disabled = false;
          return;
        }
        if (res.status !== 202 || !res.body.jobId) {
          setLongshotStatus(root, "无法开始导出", true);
          btn.disabled = false;
          return;
        }
        longshotJobId = res.body.jobId;
        pollJob(
          res.body.jobId,
          function (job) {
            btn.disabled = false;
            setLongshotStatus(root, "", false);
            setSlowHint(root, "", false);
            if (job.status === "succeeded") {
              showLongshotPanel(root, job);
            } else if (job.status === "failed") {
              showLongshotPanel(root, job);
            }
          },
          function () {
            setSlowHint(root, "比预期久一些，请耐心等待…", true);
          }
        );
      })
      .catch(function () {
        btn.disabled = false;
        setLongshotStatus(root, "网络错误", true);
      });
  }

  function startLlmNarrate(root, tripId, btn) {
    if (!btn || btn.disabled) return;
    if (
      !window.confirm(
        "将调用 LLM 重写 hook、导语与图注，可能覆盖未锁定的文案。继续？"
      )
    ) {
      return;
    }
    setToolbarCollapsed(root, false, false);
    btn.disabled = true;
    setSlowHint(root, "", false);
    setLongshotStatus(root, "正在生成杂志感文案…", true);

    postJson("/__travelogue/narrate", { tripId: tripId })
      .then(function (res) {
        if (res.status === 409 || res.status === 400) {
          setLongshotStatus(root, (res.body && res.body.message) || "无法开始", true);
          btn.disabled = false;
          return;
        }
        if (res.status !== 202 || !res.body.jobId) {
          setLongshotStatus(root, "无法开始文案生成", true);
          btn.disabled = false;
          return;
        }
        narrateJobId = res.body.jobId;
        pollJob(
          res.body.jobId,
          function (job) {
            btn.disabled = false;
            narrateJobId = null;
            setLongshotStatus(root, "", false);
            setSlowHint(root, "", false);
            if (job.status === "succeeded") {
              window.location.reload();
              return;
            }
            var err = (job.error && (job.error.message || job.error.code)) || "文案生成失败";
            window.alert(err);
          },
          function () {
            setSlowHint(root, "比预期久一些，请耐心等待…", true);
          }
        );
      })
      .catch(function () {
        btn.disabled = false;
        setLongshotStatus(root, "网络错误", true);
      });
  }

  function refreshPreviewCover(root, tripId) {
    fetch("/__travelogue/trips")
      .then(function (resp) { return resp.json(); })
      .then(function (data) {
        var trips = data.trips || [];
        var trip = trips.filter(function (t) { return t.tripId === tripId; })[0];
        if (!trip || !trip.previewRelPath) return;

        var body = toolbarBody(root);
        var card = body.querySelector(".preview-toolbar__preview-card");
        if (!card) {
          card = document.createElement("div");
          card.className = "preview-toolbar__preview-card";
          body.appendChild(card);
        }
        card.hidden = false;
        card.textContent = "";

        var title = document.createElement("p");
        title.className = "preview-toolbar__preview-title";
        title.textContent = "封面引流图 preview.jpg（9:16）";
        card.appendChild(title);

        var pathEl = document.createElement("p");
        pathEl.className = "preview-toolbar__preview-path";
        pathEl.textContent = trip.previewRelPath;
        card.appendChild(pathEl);

        var revealBtn = document.createElement("button");
        revealBtn.type = "button";
        revealBtn.className = "preview-toolbar__reveal preview-toolbar__preview-reveal";
        revealBtn.textContent = "在文件夹中显示";
        revealBtn.addEventListener("click", function () {
          revealTripPath(tripId, trip.previewRelPath);
        });
        card.appendChild(revealBtn);
      })
      .catch(function () {});
  }

  function initToolbar(root) {
    var tripId = tripIdFromPath();
    if (!tripId) return;

    var bar = root.querySelector(".preview-toolbar__bar");
    var actions = root.querySelector(".preview-toolbar__actions") || bar;

    fetch("/__travelogue/config")
      .then(function (resp) { return resp.json(); })
      .then(function (cfg) {
        if (cfg.llmAvailable) {
          var llmBtn = document.createElement("button");
          llmBtn.type = "button";
          llmBtn.className = "preview-toolbar__llm";
          llmBtn.textContent = "生成杂志感文案";
          llmBtn.addEventListener("click", function () {
            startLlmNarrate(root, tripId, llmBtn);
          });
          actions.appendChild(llmBtn);
        }
      })
      .catch(function () {});

    var longshotBtn = document.createElement("button");
    longshotBtn.type = "button";
    longshotBtn.className = "preview-toolbar__longshot";
    longshotBtn.innerHTML =
      '保存长图 <span class="preview-toolbar__scale-badge">推荐 · 适合手机</span>';
    actions.appendChild(longshotBtn);

    var status = document.createElement("span");
    status.className = "preview-toolbar__longshot-status";
    status.hidden = true;
    actions.appendChild(status);

    var stale = document.createElement("span");
    stale.className = "preview-toolbar__stale";
    stale.hidden = true;
    stale.textContent = "内容已更新，请重新生成长图";
    actions.appendChild(stale);

    var advancedWrap = document.createElement("div");
    advancedWrap.className = "preview-toolbar__advanced";
    advancedWrap.innerHTML =
      '<button type="button" class="preview-toolbar__advanced-btn">高级</button>' +
      '<div class="preview-toolbar__menu" hidden>' +
      '<button type="button" class="preview-toolbar__export-zip">导出 zip（自行托管）</button>' +
      "</div>";
    actions.appendChild(advancedWrap);

    longshotBtn.addEventListener("click", function () {
      startLongshot(root, tripId);
    });

    // Focus longshot button when navigating from stale "更新长图" CTA
    if (window.location.search.indexOf("focus=longshot") >= 0) {
      setToolbarCollapsed(root, false, false);
      requestAnimationFrame(function () {
        longshotBtn.scrollIntoView({ behavior: "smooth", block: "center" });
        longshotBtn.focus();
        longshotBtn.classList.add("preview-toolbar__longshot--focus");
      });
    }

    advancedWrap.querySelector(".preview-toolbar__advanced-btn").addEventListener("click", function () {
      toggleAdvancedMenu(root);
    });
    advancedWrap.querySelector(".preview-toolbar__export-zip").addEventListener("click", function () {
      toggleAdvancedMenu(root);
      exportZip(tripId);
    });

    document.addEventListener("click", function (ev) {
      if (!advancedWrap.contains(ev.target)) {
        var menu = root.querySelector(".preview-toolbar__menu");
        if (menu) menu.hidden = true;
      }
    });

    refreshStaleHint(root, tripId);
    refreshPreviewCover(root, tripId);

    window.addEventListener("travelogue:copy-saved", function () {
      showStaleHint(root);
    });
  }

  function init() {
    document.documentElement.setAttribute("data-preview-toolbar", "on");

    var root = document.createElement("div");
    root.className = "preview-toolbar";
    root.innerHTML =
      '<button type="button" class="preview-toolbar__handle" aria-expanded="false">' +
      '<span class="preview-toolbar__handle-icon" aria-hidden="true">▾</span>' +
      '<span class="preview-toolbar__handle-label">显示工具栏</span>' +
      "</button>" +
      '<div class="preview-toolbar__body">' +
      '<div class="preview-toolbar__bar">' +
      '<a class="preview-toolbar__back" href="/">← 返回工作台</a>' +
      '<div class="preview-toolbar__actions"></div>' +
      '<button type="button" class="preview-toolbar__collapse" aria-expanded="true" aria-label="收起工具栏">' +
      '<span aria-hidden="true">▴</span>' +
      "</button>" +
      "</div>" +
      "</div>";

    var body = root.querySelector(".preview-toolbar__body");

    var hintHidden = false;
    try {
      hintHidden = localStorage.getItem(HINT_KEY) === "1";
    } catch (e) {}

    if (!hintHidden) {
      var hint = document.createElement("div");
      hint.className = "preview-toolbar__hint";
      hint.innerHTML =
        '<span>点击标题、导语、图注即可修改 · 修改后自动保存</span>' +
        '<button type="button" class="preview-toolbar__dismiss" aria-label="关闭提示">知道了</button>';
      hint.querySelector(".preview-toolbar__dismiss").addEventListener("click", function () {
        hint.hidden = true;
        try { localStorage.setItem(HINT_KEY, "1"); } catch (e2) {}
        syncToolbarHeight(root);
      });
      body.appendChild(hint);
    }

    document.body.insertBefore(root, document.body.firstChild);
    bindToolbarCollapse(root);
    initToolbar(root);

    var startCollapsed = false;
    try {
      startCollapsed = localStorage.getItem(COLLAPSE_KEY) === "1";
    } catch (e3) {}
    if (window.location.search.indexOf("focus=longshot") >= 0) {
      startCollapsed = false;
    }
    setToolbarCollapsed(root, startCollapsed, false);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
