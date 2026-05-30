/**
 * Travelogue Studio · preview page toolbar (ESM).
 */
"use strict";

import {
  postJson,
  patchJson,
  postJsonBusyRetry,
  isJobBusyResponse,
} from "./js/http.js";
import { startJobPollInterval, pollJobUntilDone } from "./js/job-poll.js";
import { STUDIO_USER_NOTES_MAX_LEN } from "./js/constants.js";

var isJobBusy409 = isJobBusyResponse;
var HINT_KEY = "travelogue.studio.editHint.dismissed";
var COLLAPSE_KEY = "travelogue.studio.previewToolbar.collapsed";
var LONGSHOT_SCALE = 2;
var SLOW_JOB_MS = 30000;
var pollCancel = null;
var longshotJobId = null;
var narrateJobId = null;
  var DRAWER_FOCUSABLE =
    'a[href],button:not([disabled]),input:not([disabled]),textarea:not([disabled]),select:not([disabled]),[tabindex="0"]';

  function trapDrawerFocus(container) {
    function onKeydown(e) {
      if (e.key !== "Tab") return;
      var items = container.querySelectorAll(DRAWER_FOCUSABLE);
      if (!items.length) return;
      var first = items[0];
      var last = items[items.length - 1];
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else if (document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
    container.addEventListener("keydown", onKeydown);
    return function () {
      container.removeEventListener("keydown", onKeydown);
    };
  }

  function tripIdFromPath() {
    var parts = window.location.pathname.replace(/^\/+|\/+$/g, "").split("/");
    return parts[0] || "";
  }

  function tripApiBase(tripId) {
    return "/" + encodeURIComponent(tripId) + "/__travelogue";
  }

  var _toastTimer = null;

  function toolbarConfirm(opts) {
    if (typeof studioModal === "function") {
      return studioModal(opts);
    }
    var msg = (opts.title ? opts.title + "\n\n" : "") + (opts.body || "");
    return Promise.resolve(window.confirm(msg));
  }

  function toolbarAlert(message, opts) {
    opts = opts || {};
    if (message) showToolbarToast(message, { error: !!opts.error });
  }

  function showToolbarToast(message, opts) {
    opts = opts || {};
    var el = document.getElementById("preview-toolbar-toast");
    if (!el) {
      el = document.createElement("p");
      el.id = "preview-toolbar-toast";
      el.className = "preview-toolbar__toast";
      el.setAttribute("role", "status");
      el.hidden = true;
      document.body.appendChild(el);
    }
    el.textContent = message;
    el.classList.toggle("preview-toolbar__toast--error", !!opts.error);
    el.hidden = false;
    clearTimeout(_toastTimer);
    _toastTimer = setTimeout(function () {
      el.hidden = true;
    }, opts.duration || (opts.error ? 5000 : 2800));
  }

  var _layoutPending = false;
  function setLayoutPending(on) {
    _layoutPending = !!on;
    document.querySelectorAll(".preview-toolbar__apply-layout").forEach(function (btn) {
      btn.hidden = !_layoutPending;
    });
  }

  function revealTripPath(tripId, relPath) {
    return postJson("/__travelogue/reveal", { tripId: tripId, relPath: relPath });
  }

  function pollJob(jobId, root, onDone, onSlow) {
    if (pollCancel) {
      pollCancel();
      pollCancel = null;
    }
    pollCancel = startJobPollInterval(jobId, {
      intervalMs: 800,
      slowMs: SLOW_JOB_MS,
      onSlow: onSlow,
      onTick: function (job) {
        if (job.status === "running" && job.stageHint && root) {
          setLongshotStatus(root, "正在生成长图… " + job.stageHint, true);
        }
      },
      onDone: function (job) {
        pollCancel = null;
        onDone(job);
      },
    });
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
        result.userHint ||
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
    toolbarConfirm({
      title: "导出 zip",
      body: "导出 zip 包用于自行托管或备份，不是微信分享主路径。继续？",
      confirmText: "继续",
    }).then(function (ok) {
      if (!ok) return;
      return postJson("/__travelogue/export", { tripId: tripId, confirmPrivacy: true });
    }).then(function (res) {
      if (!res) return;
      if (res.status !== 200 || !res.body.ok) {
        toolbarAlert((res.body && res.body.message) || "导出失败", { error: true });
        return;
      }
      var zipRel = res.body.zipRelPath;
      if (!zipRel) return;
      return toolbarConfirm({
        title: "zip 已生成",
        body: "是否在文件夹中显示？",
        confirmText: "显示",
        cancelText: "关闭",
      }).then(function (reveal) {
        if (reveal) revealTripPath(tripId, zipRel);
      });
    }).catch(function () {
      toolbarAlert("导出失败", { error: true });
    });
  }

  function startLongshot(root, tripId) {
    var btn = root.querySelector(".preview-toolbar__longshot");
    if (!btn || btn.disabled) return;
    setToolbarCollapsed(root, false, false);
    btn.disabled = true;
    setLongshotStatus(root, "正在生成长图…", true);
    setSlowHint(root, "", false);

    postJsonBusyRetry("/__travelogue/longshot", {
      tripId: tripId,
      scale: LONGSHOT_SCALE,
      format: "png",
    }, { onBusy: function () { showToolbarToast("排队中，请稍候…"); } })
      .then(function (res) {
        if (isJobBusy409(res)) {
          setLongshotStatus(root, "排队中，请稍候…", true);
          btn.disabled = false;
          return;
        }
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
          root,
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
    toolbarConfirm({
      title: "生成杂志感文案",
      body: "将调用 LLM 重写 hook、导语与图注，可能覆盖未锁定的文案。继续？",
      confirmText: "继续",
    }).then(function (ok) {
      if (!ok) return;
      setToolbarCollapsed(root, false, false);
      btn.disabled = true;
      setSlowHint(root, "", false);
      setLongshotStatus(root, "正在生成杂志感文案…", true);
      return postJson("/__travelogue/narrate", { tripId: tripId });
    }).then(function (res) {
      if (!res) return;
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
        root,
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
          toolbarAlert(err, { error: true });
        },
        function () {
          setSlowHint(root, "比预期久一些，请耐心等待…", true);
        }
      );
    }).catch(function () {
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

  function applyLayoutRerender(tripId, root) {
    var btn = root.querySelector(".preview-toolbar__apply-layout");
    if (btn) btn.disabled = true;
    return postJson(tripApiBase(tripId) + "/rerender", {})
      .then(function (res) {
        if (btn) btn.disabled = false;
        if (res.status !== 200 || !res.body.ok) {
          showToolbarToast((res.body && res.body.error) || "排版失败", { error: true });
          return;
        }
        setLayoutPending(false);
        showToolbarToast("排版已更新");
        window.location.reload();
      })
      .catch(function () {
        if (btn) btn.disabled = false;
        showToolbarToast("排版失败", { error: true });
      });
  }

  function initTitleEdit(root, tripId) {
    var wrap = root.querySelector(".preview-toolbar__title-wrap");
    if (!wrap) return;

    var display = document.createElement("button");
    display.type = "button";
    display.className = "preview-toolbar__title";
    display.title = "点击编辑杂志名";
    display.textContent = "我的旅途";
    wrap.appendChild(display);

    function setTitle(text) {
      var t = (text || "我的旅途").trim() || "我的旅途";
      display.textContent = t.length > 20 ? t.slice(0, 20) : t;
      display.dataset.title = t;
    }

    fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/entry")
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (data && data.intentSummary && data.intentSummary.title) {
          setTitle(data.intentSummary.title);
        }
      })
      .catch(function () {});

    display.addEventListener("click", function () {
      if (wrap.querySelector(".preview-toolbar__title-input")) return;
      var input = document.createElement("input");
      input.type = "text";
      input.className = "preview-toolbar__title-input";
      input.maxLength = 20;
      input.value = display.dataset.title || display.textContent || "";
      display.hidden = true;
      wrap.appendChild(input);
      input.focus();
      input.select();

      function finish(save) {
        var next = (input.value || "").trim();
        input.remove();
        display.hidden = false;
        if (!save) {
          setTitle(display.dataset.title || display.textContent);
          return;
        }
        if (next.length > 20) {
          showToolbarToast("杂志名最多 20 个字", { error: true });
          return;
        }
        if (!next) {
          showToolbarToast("杂志名不能为空", { error: true });
          return;
        }
        var prev = (display.dataset.title || "").trim();
        if (next === prev) {
          setTitle(next);
          return;
        }
        display.classList.add("preview-toolbar__title--saving");
        postJson(tripApiBase(tripId) + "/save-copy", {
          patches: [{ path: "meta.title", value: next }],
        })
          .then(function (res) {
            display.classList.remove("preview-toolbar__title--saving");
            if (res.status !== 200 || !res.body.ok) {
              showToolbarToast((res.body && res.body.error) || "保存失败", { error: true });
              return;
            }
            setTitle(next);
            showToolbarToast("杂志名已保存");
            try {
              window.dispatchEvent(new CustomEvent("travelogue:copy-saved"));
            } catch (e) {}
            if (res.body.rendered && res.body.rendered.length) {
              window.location.reload();
            }
          })
          .catch(function () {
            display.classList.remove("preview-toolbar__title--saving");
            showToolbarToast("保存失败", { error: true });
          });
      }

      input.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          e.preventDefault();
          finish(true);
        }
        if (e.key === "Escape") {
          e.preventDefault();
          finish(false);
        }
      });
      input.addEventListener("blur", function () {
        finish(true);
      });
    });
  }

  function fetchEntry(tripId) {
    return fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/entry")
      .then(function (r) { return r.ok ? r.json() : null; })
      .catch(function () { return null; });
  }

  function currentChapterId() {
    var sections = document.querySelectorAll("section.chapter[data-chapter-id]");
    var best = null;
    var bestVis = 0;
    sections.forEach(function (sec) {
      var rect = sec.getBoundingClientRect();
      var vis = Math.min(rect.bottom, window.innerHeight) - Math.max(rect.top, 0);
      if (vis > bestVis) {
        bestVis = vis;
        best = sec.getAttribute("data-chapter-id");
      }
    });
    return best;
  }

  function renderExplainBlock(container, title, block) {
    if (!container || !block || !block.summary) return;
    var head = document.createElement("h3");
    head.className = "preview-drawer__subhead";
    head.textContent = title;
    container.appendChild(head);
    var lead = document.createElement("p");
    lead.className = "preview-drawer__explain-lead";
    lead.textContent = block.summary;
    container.appendChild(lead);
    if (block.details && block.details.length) {
      var list = document.createElement("ul");
      list.className = "preview-drawer__explain-list";
      block.details.forEach(function (line) {
        var li = document.createElement("li");
        li.textContent = line;
        list.appendChild(li);
      });
      container.appendChild(list);
    }
  }

  function loadChapterExplain(tripId, container) {
    if (!container) return;
    fetch("/__travelogue/chapter-layout?tripId=" + encodeURIComponent(tripId))
      .then(function (resp) { return resp.json(); })
      .then(function (data) {
        if (!data || !data.ok || !data.summary) {
          container.textContent = "暂无分章说明";
          return;
        }
        container.innerHTML = "";
        renderExplainBlock(container, "为什么这样分章？", {
          summary: data.summary,
          details: data.details,
        });
        if (data.layoutExplain) {
          renderExplainBlock(container, "排版引擎", data.layoutExplain);
        }
      })
      .catch(function () {
        container.textContent = "无法加载分章说明";
      });
  }

  function initPreviewDrawers(root, tripId) {
    var shell = document.createElement("div");
    shell.className = "preview-drawer-root";
    shell.hidden = true;
    shell.innerHTML =
      '<div class="preview-drawer__scrim"></div>' +
      '<div class="preview-drawer" role="dialog" aria-modal="true" aria-labelledby="preview-drawer-title" hidden>' +
      '<div class="preview-drawer__handle" aria-hidden="true"></div>' +
      '<div class="preview-drawer__head">' +
      '<h2 id="preview-drawer-title" class="preview-drawer__title"></h2>' +
      '<button type="button" class="preview-drawer__close" aria-label="关闭">×</button>' +
      "</div>" +
      '<div class="preview-drawer__body"></div>' +
      "</div>";
    document.body.appendChild(shell);

    var drawer = shell.querySelector(".preview-drawer");
    var titleEl = shell.querySelector(".preview-drawer__title");
    var bodyEl = shell.querySelector(".preview-drawer__body");
    var scrim = shell.querySelector(".preview-drawer__scrim");
    var closeBtn = shell.querySelector(".preview-drawer__close");
    var entryCache = null;
    var drawerFocusRelease = null;
    var drawerPreviousFocus = null;

    var editTpl =
      '<label class="preview-drawer__label" for="preview-drawer-title-input">杂志名</label>' +
      '<input id="preview-drawer-title-input" class="preview-drawer__title-input" type="text" maxlength="20" autocomplete="off" placeholder="我的旅途">' +
      '<label class="preview-drawer__label" for="preview-drawer-notes">写给编辑的一句话</label>' +
      '<textarea id="preview-drawer-notes" class="preview-drawer__notes" maxlength="' +
      STUDIO_USER_NOTES_MAX_LEN +
      '" rows="3" placeholder="例如：带娃慢走，想突出雨后的京都"></textarea>' +
      '<p class="preview-drawer__chapter-label">当前章：<strong class="preview-drawer__chapter-name"></strong></p>' +
      '<p class="preview-drawer__label">记忆锚点（0–3 个）</p>' +
      '<div class="preview-drawer__anchors">' +
      '<input type="text" class="preview-drawer__anchor" maxlength="24" placeholder="锚点 1">' +
      '<input type="text" class="preview-drawer__anchor" maxlength="24" placeholder="锚点 2">' +
      '<input type="text" class="preview-drawer__anchor" maxlength="24" placeholder="锚点 3">' +
      "</div>" +
      '<p class="preview-drawer__hint">短词即可，会写进图说，不会瞎编</p>' +
      '<p class="preview-drawer__featured-help">★ 在任意一屏右下角可将照片标为精选，之后点「应用排版」生效</p>' +
      '<button type="button" class="preview-drawer__ghost preview-drawer__narrate-anchors">保存并重新生成文案</button>' +
      '<button type="button" class="preview-drawer__primary preview-drawer__save-edit">保存编辑</button>';

    var structTpl =
      '<div class="preview-drawer__g1"></div>' +
      '<div class="preview-drawer__g1-actions" hidden>' +
      '<button type="button" class="preview-drawer__g1-confirm">章节顺序 OK</button>' +
      '<button type="button" class="preview-drawer__g1-regenerate">重新生成结构</button>' +
      "</div>" +
      '<div class="preview-drawer__explain"></div>' +
      '<button type="button" class="preview-drawer__primary preview-drawer__apply-layout">应用排版</button>';

    function pollStudioJob(jobId, onDone) {
      pollJobUntilDone(jobId, { intervalMs: 800 })
        .then(onDone)
        .catch(function () {
          onDone({ status: "failed", error: { message: "网络错误" } });
        });
    }

    function confirmG1Structure() {
      return patchJson("/__travelogue/trips/" + encodeURIComponent(tripId) + "/pipeline", {
        status: "structure_locked",
        continuePipeline: true,
      });
    }

    function chapterRow(chId) {
      if (!entryCache || !entryCache.chapters) return null;
      for (var i = 0; i < entryCache.chapters.length; i++) {
        if (entryCache.chapters[i].id === chId) return entryCache.chapters[i];
      }
      return null;
    }

    function fillAnchors(chId) {
      var inputs = bodyEl.querySelectorAll(".preview-drawer__anchor");
      var row = chapterRow(chId);
      var anchors = (row && row.memoryAnchors) || [];
      for (var i = 0; i < inputs.length; i++) {
        inputs[i].value = anchors[i] || "";
      }
      var nameEl = bodyEl.querySelector(".preview-drawer__chapter-name");
      if (nameEl) nameEl.textContent = (row && row.title) || chId || "—";
    }

    function closeDrawer() {
      if (drawerFocusRelease) {
        drawerFocusRelease();
        drawerFocusRelease = null;
      }
      shell.hidden = true;
      drawer.hidden = true;
      document.body.classList.remove("preview-drawer-open");
      if (drawerPreviousFocus && drawerPreviousFocus.focus) {
        drawerPreviousFocus.focus();
      }
      drawerPreviousFocus = null;
    }

    function activateDrawerFocus() {
      drawerPreviousFocus = document.activeElement;
      if (drawerFocusRelease) drawerFocusRelease();
      closeBtn.focus();
      drawerFocusRelease = trapDrawerFocus(drawer);
    }

    function runG1Confirm(triggerBtn) {
      if (triggerBtn) triggerBtn.disabled = true;
      showToolbarToast("正在确认并继续制作…");
      return confirmG1Structure()
        .then(function (res) {
          if (res.status === 202 && res.body && res.body.jobId) {
            pollStudioJob(res.body.jobId, function (job) {
              if (triggerBtn) triggerBtn.disabled = false;
              if (job.status === "succeeded") {
                showToolbarToast("章节已确认，杂志已更新");
                window.location.reload();
                return;
              }
              var err = (job.error && (job.error.message || job.error.code)) || "确认失败";
              showToolbarToast(err, { error: true });
            });
            return;
          }
          if (triggerBtn) triggerBtn.disabled = false;
          showToolbarToast((res.body && res.body.error) || "确认失败", { error: true });
        })
        .catch(function () {
          if (triggerBtn) triggerBtn.disabled = false;
          showToolbarToast("确认失败", { error: true });
        });
    }

    function openDrawer(mode) {
      if (!entryCache) {
        fetchEntry(tripId).then(function (data) {
          entryCache = data || {};
          openDrawer(mode);
        });
        return;
      }
      shell.hidden = false;
      drawer.hidden = false;
      document.body.classList.add("preview-drawer-open");
      setToolbarCollapsed(root, false, false);
      requestAnimationFrame(activateDrawerFocus);

      if (mode === "edit") {
        titleEl.textContent = "编辑";
        bodyEl.innerHTML = editTpl;
        var titleInput = bodyEl.querySelector(".preview-drawer__title-input");
        var notes = bodyEl.querySelector(".preview-drawer__notes");
        if (titleInput && entryCache.intentSummary) {
          titleInput.value = entryCache.intentSummary.title || "";
        }
        if (notes && entryCache.intentSummary) {
          notes.value = entryCache.intentSummary.userNotes || "";
        }
        fillAnchors(currentChapterId());

        function persistEditDrawer(btn, opts) {
          opts = opts || {};
          var chId = currentChapterId();
          var titleVal = (titleInput && titleInput.value || "").trim();
          var notesVal = (notes.value || "").trim();
          var anchorInputs = bodyEl.querySelectorAll(".preview-drawer__anchor");
          var anchors = [];
          anchorInputs.forEach(function (inp) {
            var v = (inp.value || "").trim();
            if (v) anchors.push(v);
          });
          btn.disabled = true;
          if (titleVal.length > 20) {
            btn.disabled = false;
            showToolbarToast("杂志名最多 20 个字", { error: true });
            return Promise.resolve(false);
          }
          var tasks = [
            patchJson("/__travelogue/trips/" + encodeURIComponent(tripId) + "/intent", {
              title: titleVal || null,
              userNotes: notesVal || null,
            }),
          ];
          if (chId) {
            tasks.push(
              postJson(tripApiBase(tripId) + "/save-copy", {
                patches: [{
                  path: "chapters." + chId + ".curation.memoryAnchors",
                  value: anchors.join(", "),
                }],
              })
            );
          }
          return Promise.all(tasks)
            .then(function (results) {
              btn.disabled = false;
              var ok = results.every(function (r) { return r.status === 200 && r.body.ok; });
              if (!ok) {
                showToolbarToast("保存失败", { error: true });
                return false;
              }
              if (entryCache.intentSummary) {
                entryCache.intentSummary.userNotes = notesVal;
                if (titleVal) entryCache.intentSummary.title = titleVal;
              }
              if (chId && entryCache.chapters) {
                var row = chapterRow(chId);
                if (row) row.memoryAnchors = anchors;
              }
              if (!opts.skipToast) {
                showToolbarToast(
                  anchors.length > 0
                    ? "编辑已保存。可在 ⋯ 菜单中重新生成文案以写入锚点。"
                    : "编辑已保存"
                );
              }
              return true;
            })
            .catch(function () {
              btn.disabled = false;
              showToolbarToast("保存失败", { error: true });
              return false;
            });
        }

        bodyEl.querySelector(".preview-drawer__save-edit").addEventListener("click", function () {
          var btn = this;
          persistEditDrawer(btn).then(function (ok) {
            if (ok) closeDrawer();
          });
        });
        var narrateAnchorsBtn = bodyEl.querySelector(".preview-drawer__narrate-anchors");
        if (narrateAnchorsBtn) {
          narrateAnchorsBtn.addEventListener("click", function () {
            var btn = this;
            persistEditDrawer(btn, { skipToast: true }).then(function (ok) {
              if (!ok) return;
              closeDrawer();
              startLlmNarrate(root, tripId, btn);
            });
          });
        }
        return;
      }

      titleEl.textContent = "结构";
      bodyEl.innerHTML = structTpl;
      var g1 = bodyEl.querySelector(".preview-drawer__g1");
      var g1Actions = bodyEl.querySelector(".preview-drawer__g1-actions");
      var status = entryCache.pipelineStatus || "";
      var pending = entryCache.g1Pending || status === "structure_draft";
      if (pending) {
        g1.className = "preview-drawer__g1 preview-drawer__g1--warn";
        g1.textContent = "章节结构待确认：请浏览各章顺序，确认后将生成文案并完成排版。";
        if (g1Actions) g1Actions.hidden = false;
        var confirmBtn = bodyEl.querySelector(".preview-drawer__g1-confirm");
        var regenBtn = bodyEl.querySelector(".preview-drawer__g1-regenerate");
        if (confirmBtn) {
          confirmBtn.addEventListener("click", function () {
            runG1Confirm(confirmBtn);
          });
        }
        if (regenBtn) {
          regenBtn.addEventListener("click", function () {
            toolbarConfirm({
              title: "重新生成结构",
              body: "将重新生成章节结构，可能覆盖当前分章。继续？",
              confirmText: "继续",
              danger: true,
            }).then(function (ok) {
              if (!ok) return;
              regenBtn.disabled = true;
              return postJson("/__travelogue/trips/" + encodeURIComponent(tripId) + "/curate", { force: true });
            }).then(function (res) {
              if (!res) return;
              if (res.status === 202 && res.body && res.body.jobId) {
                pollStudioJob(res.body.jobId, function (job) {
                  regenBtn.disabled = false;
                  if (job.status === "succeeded") {
                    showToolbarToast("结构已重新生成");
                    window.location.reload();
                    return;
                  }
                  showToolbarToast("重新生成失败", { error: true });
                });
                return;
              }
              regenBtn.disabled = false;
              showToolbarToast("无法开始", { error: true });
            }).catch(function () {
              regenBtn.disabled = false;
              showToolbarToast("重新生成失败", { error: true });
            });
          });
        }
      } else {
        g1.className = "preview-drawer__g1 preview-drawer__g1--info";
        g1.textContent = "章节已按行程排好，可在预览中改字、锚点与精选。";
        if (g1Actions) g1Actions.hidden = true;
      }
      loadChapterExplain(tripId, bodyEl.querySelector(".preview-drawer__explain"));
      var applyBtn = bodyEl.querySelector(".preview-drawer__apply-layout");
      applyBtn.hidden = !_layoutPending;
      applyBtn.addEventListener("click", function () {
        closeDrawer();
        applyLayoutRerender(tripId, root);
      });
    }

    scrim.addEventListener("click", closeDrawer);
    closeBtn.addEventListener("click", closeDrawer);
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !shell.hidden) closeDrawer();
    });

    fetchEntry(tripId).then(function (data) {
      entryCache = data || {};
    });

    return {
      openEdit: function () { openDrawer("edit"); },
      openStructure: function () { openDrawer("structure"); },
      confirmStructure: function () { return runG1Confirm(null); },
      close: closeDrawer,
      refreshEntry: function () {
        return fetchEntry(tripId).then(function (data) {
          entryCache = data || {};
          return entryCache;
        });
      },
    };
  }

  function initG1Banner(root, tripId, drawers) {
    var body = toolbarBody(root);
    if (!body) return;
    Promise.all([
      fetch("/__travelogue/config").then(function (r) { return r.ok ? r.json() : null; }),
      fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/entry").then(function (r) {
        return r.ok ? r.json() : null;
      }),
    ])
      .then(function (rows) {
        var cfg = rows[0];
        var entry = rows[1];
        if (!cfg || !entry || !entry.g1Pending) return;
        if (!(cfg.studio && cfg.studio.g1ConfirmStructure)) return;
        if (body.querySelector(".preview-toolbar__g1-banner")) return;

        var banner = document.createElement("div");
        banner.className = "preview-toolbar__g1-banner";
        banner.setAttribute("role", "status");
        banner.innerHTML =
          '<p class="preview-toolbar__g1-banner-text">章节结构待确认（G1 已开启）</p>' +
          '<div class="preview-toolbar__g1-banner-actions">' +
          '<button type="button" class="preview-toolbar__g1-banner-open">查看结构</button>' +
          '<button type="button" class="preview-toolbar__g1-banner-confirm">确认并继续</button>' +
          "</div>";
        var bar = body.querySelector(".preview-toolbar__bar");
        if (bar && bar.nextSibling) {
          body.insertBefore(banner, bar.nextSibling);
        } else {
          body.appendChild(banner);
        }
        banner.querySelector(".preview-toolbar__g1-banner-open").addEventListener("click", function () {
          drawers.openStructure();
        });
        banner.querySelector(".preview-toolbar__g1-banner-confirm").addEventListener("click", function () {
          drawers.confirmStructure();
        });
      })
      .catch(function () {});
  }

  function startFeaturedPresent() {
    var toggle = document.getElementById("featured-present-toggle");
    var start = document.getElementById("screenplay-start");
    if (!start) {
      showToolbarToast("当前页面不支持放映", { error: true });
      return;
    }
    if (toggle && toggle.getAttribute("aria-pressed") !== "true") {
      toggle.click();
    }
    start.click();
    showToolbarToast("精选放映已开始");
  }

  function initFeaturedStars(tripId) {
    var screens = document.querySelectorAll('.layout-screen[data-block="layout-screen"][data-asset-ids]');
    screens.forEach(function (screen) {
      if (screen.querySelector(".preview-toolbar__featured-star")) return;
      var raw = screen.getAttribute("data-asset-ids") || "";
      var assetId = raw.split(",")[0];
      if (!assetId) return;

      var star = document.createElement("button");
      star.type = "button";
      star.className = "preview-toolbar__featured-star";
      star.setAttribute("aria-label", "标为精选");
      star.textContent = "★";
      if (screen.getAttribute("data-featured") === "true") {
        star.classList.add("preview-toolbar__featured-star--on");
        star.setAttribute("aria-pressed", "true");
      }
      star.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        if (star.disabled) return;
        star.disabled = true;
        postJson(tripApiBase(tripId) + "/promote-tier", {
          assetIds: [assetId],
          rerender: false,
        })
          .then(function (res) {
            star.disabled = false;
            if (res.status !== 200 || !res.body.ok) {
              showToolbarToast((res.body && res.body.error) || "标记失败", { error: true });
              return;
            }
            star.classList.add("preview-toolbar__featured-star--on");
            star.setAttribute("aria-pressed", "true");
            screen.setAttribute("data-featured", "true");
            setLayoutPending(true);
            showToolbarToast("已标为精选 · 点应用排版后生效");
          })
          .catch(function () {
            star.disabled = false;
            showToolbarToast("标记失败", { error: true });
          });
      });
      screen.style.position = screen.style.position || "relative";
      screen.appendChild(star);
    });
  }

  function revealTripFolder(tripId) {
    fetch("/__travelogue/trips")
      .then(function (resp) { return resp.json(); })
      .then(function (data) {
        var trips = data.trips || [];
        var trip = trips.filter(function (t) { return t.tripId === tripId; })[0];
        var rel = (trip && trip.previewRelPath) || "index.html";
        return revealTripPath(tripId, rel);
      })
      .catch(function () {
        showToolbarToast("无法打开文件夹", { error: true });
      });
  }

  function initToolbar(root) {
    var tripId = tripIdFromPath();
    if (!tripId) return;

    var bar = root.querySelector(".preview-toolbar__bar");
    var actions = root.querySelector(".preview-toolbar__actions") || bar;
    var menuBtn = root.querySelector(".preview-toolbar__menu-btn");
    var menu = root.querySelector(".preview-toolbar__more-menu");
    var revealBtn = root.querySelector(".preview-toolbar__reveal-folder");

    var drawers = initPreviewDrawers(root, tripId);
    initG1Banner(root, tripId, drawers);

    var longshotBtn = document.createElement("button");
    longshotBtn.type = "button";
    longshotBtn.className = "preview-toolbar__longshot preview-toolbar__longshot--primary";
    longshotBtn.textContent = "保存长图";
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

    longshotBtn.addEventListener("click", function () {
      startLongshot(root, tripId);
    });

    if (revealBtn) {
      revealBtn.addEventListener("click", function () {
        revealTripFolder(tripId);
      });
    }

    if (window.location.search.indexOf("focus=longshot") >= 0) {
      setToolbarCollapsed(root, false, false);
      requestAnimationFrame(function () {
        longshotBtn.scrollIntoView({ behavior: "smooth", block: "center" });
        longshotBtn.focus();
        longshotBtn.classList.add("preview-toolbar__longshot--focus");
      });
    }

    if (menu && menuBtn) {
      var applyBtn = menu.querySelector(".preview-toolbar__apply-layout");
      var editBtn = menu.querySelector(".preview-toolbar__open-edit");
      var structBtn = menu.querySelector(".preview-toolbar__open-structure");
      var presentBtn = menu.querySelector(".preview-toolbar__present-featured");
      var llmSlot = menu.querySelector(".preview-toolbar__llm-slot");
      var zipBtn = menu.querySelector(".preview-toolbar__export-zip");

      function closeMenu() {
        menu.hidden = true;
        menuBtn.setAttribute("aria-expanded", "false");
      }

      menuBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        var open = !menu.hidden;
        menu.hidden = open;
        menuBtn.setAttribute("aria-expanded", open ? "false" : "true");
      });

      if (applyBtn) {
        applyBtn.hidden = true;
        applyBtn.addEventListener("click", function () {
          closeMenu();
          applyLayoutRerender(tripId, root);
        });
      }
      if (editBtn) {
        editBtn.addEventListener("click", function () {
          closeMenu();
          drawers.openEdit();
        });
      }
      if (structBtn) {
        structBtn.addEventListener("click", function () {
          closeMenu();
          drawers.openStructure();
        });
      }
      if (presentBtn) {
        drawers.refreshEntry().then(function (data) {
          var count = (data && data.intentSummary && data.intentSummary.featuredCount) || 0;
          if (count < 1) presentBtn.hidden = true;
        });
        presentBtn.addEventListener("click", function () {
          closeMenu();
          startFeaturedPresent();
        });
      }
      if (zipBtn) {
        zipBtn.addEventListener("click", function () {
          closeMenu();
          exportZip(tripId);
        });
      }

      fetch("/__travelogue/config")
        .then(function (resp) { return resp.json(); })
        .then(function (cfg) {
          if (!cfg.llmAvailable || !llmSlot) return;
          var llmBtn = document.createElement("button");
          llmBtn.type = "button";
          llmBtn.className = "preview-toolbar__llm";
          llmBtn.textContent = "生成杂志感文案";
          llmBtn.addEventListener("click", function () {
            closeMenu();
            startLlmNarrate(root, tripId, llmBtn);
          });
          llmSlot.appendChild(llmBtn);
        })
        .catch(function () {});

      document.addEventListener("click", function (ev) {
        if (!menu.contains(ev.target) && ev.target !== menuBtn) {
          closeMenu();
        }
      });
    }

    refreshStaleHint(root, tripId);
    refreshPreviewCover(root, tripId);
    initFeaturedStars(tripId);

    window.addEventListener("travelogue:copy-saved", function () {
      showStaleHint(root);
    });
  }

  function init() {
    if (
      window.location.search.indexOf("share=1") >= 0 ||
      window.location.search.indexOf("mode=share") >= 0
    ) {
      document.documentElement.setAttribute("data-preview-share", "on");
      return;
    }

    document.documentElement.setAttribute("data-preview-toolbar", "on");

    var root = document.createElement("div");
    root.className = "preview-toolbar";
    root.innerHTML =
      '<button type="button" class="preview-toolbar__handle" aria-expanded="false">' +
      '<span class="preview-toolbar__handle-icon" aria-hidden="true">▾</span>' +
      '<span class="preview-toolbar__handle-label">显示工具栏</span>' +
      "</button>" +
      '<div class="preview-toolbar__body">' +
      '<div class="preview-toolbar__bar preview-toolbar__bar--minimal">' +
      '<a class="preview-toolbar__back" href="/">← 返回</a>' +
      '<div class="preview-toolbar__actions"></div>' +
      '<button type="button" class="preview-toolbar__reveal-folder">在文件夹中显示</button>' +
      '<button type="button" class="preview-toolbar__menu-btn" aria-haspopup="true" aria-expanded="false">更多编辑…</button>' +
      '<div class="preview-toolbar__more-menu" hidden role="menu">' +
      '<button type="button" class="preview-toolbar__open-edit" role="menuitem">编辑感受与锚点</button>' +
      '<button type="button" class="preview-toolbar__open-structure" role="menuitem">结构与分章</button>' +
      '<button type="button" class="preview-toolbar__apply-layout" role="menuitem">应用排版</button>' +
      '<button type="button" class="preview-toolbar__present-featured" role="menuitem">放映精选</button>' +
      '<span class="preview-toolbar__llm-slot" role="none"></span>' +
      '<button type="button" class="preview-toolbar__export-zip" role="menuitem">导出 zip（自行托管）</button>' +
      "</div>" +
      '<button type="button" class="preview-toolbar__collapse" aria-expanded="true" aria-label="收起工具栏">' +
      '<span aria-hidden="true">▴</span>' +
      "</button>" +
      "</div>" +
      "</div>";

    var body = root.querySelector(".preview-toolbar__body");

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
