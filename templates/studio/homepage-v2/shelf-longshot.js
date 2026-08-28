/**
 * 首页 v2 · 书架「保存长图」Modal 流程（M14）。
 */
import { trackStudioEvent } from "../js/analytics.js";
import { markLongshotReady, isLongshotReady } from "../js/longshot-ready.js";
import {
  LONGSHOT_PRESETS,
  startLongshotJob,
  waitForLongshotJob,
  revealLongshotOutput,
  formatLongshotResult,
  isJobBusyResponse,
} from "../js/longshot-client.js";
import {
  clearSessionIntent,
  fetchServerRecipe,
  getCachedKeptN,
  INTENT_TO_PLATFORM,
  showAmbiguousIntentCard,
  writeSessionIntent,
} from "../js/output-recipe.js";
import {
  isComposePlatform,
  progressSynthesizingTitleForPlatform,
  progressTitleForPlatform,
} from "../js/longshot-export-panel.js";
import { V2 } from "./store.js";

// EOI · 需与 travelogue/export/longshot.py 的 EXPORT_OUTPUT_DIRNAME 保持一致——
// longshot-current.json 现在落在 trip 根目录下的这个子目录里，不再是根目录。
var EXPORT_OUTPUT_DIRNAME = "导出文件";

var _activeModal = null;
var _backgroundJob = null;

function toast(msg, opts) {
  if (typeof studioToast === "function") studioToast(msg, opts);
}

function focusNoScroll(el) {
  if (!el || !el.focus) return;
  try {
    el.focus({ preventScroll: true });
  } catch (_e) {
    el.focus();
  }
}

function closeActiveModal() {
  if (!_activeModal) return;
  _activeModal.close(false);
  _activeModal = null;
}

function openShelfLongshotModal(opts) {
  closeActiveModal();
  opts = opts || {};

  var backdrop = document.createElement("div");
  backdrop.className = "studio__modal-backdrop";

  var modal = document.createElement("div");
  modal.className = "studio__modal";
  modal.setAttribute("role", "dialog");
  modal.setAttribute("aria-modal", "true");

  var titleEl = document.createElement("h3");
  titleEl.textContent = opts.title || "";

  var bodyEl = document.createElement("div");
  bodyEl.className = "studio__modal-body v2-shelf-longshot__body";

  var actions = document.createElement("div");
  actions.className = "studio__modal-actions";

  var primaryBtn = document.createElement("button");
  primaryBtn.type = "button";
  primaryBtn.className = "studio__btn studio__btn--sm studio__btn--primary";
  primaryBtn.textContent = opts.primaryText || "关闭";
  primaryBtn.hidden = opts.primaryHidden !== false;

  var secondaryBtn = document.createElement("button");
  secondaryBtn.type = "button";
  secondaryBtn.className = "studio__btn studio__btn--ghost studio__btn--sm";
  secondaryBtn.textContent = opts.secondaryText || "关闭";
  secondaryBtn.hidden = !!opts.secondaryHidden;

  // FE-SR-08 / USR-03 · 成功面「换种分享方式」（与预览 Dock 同合同）
  var switchBtn = document.createElement("button");
  switchBtn.type = "button";
  switchBtn.className = "studio__btn studio__btn--ghost studio__btn--sm";
  switchBtn.setAttribute("data-share-ready-switch", "1");
  switchBtn.textContent = "换种分享方式";
  switchBtn.hidden = true;

  if (!switchBtn.hidden) actions.appendChild(switchBtn);
  if (!secondaryBtn.hidden) actions.appendChild(secondaryBtn);
  if (!primaryBtn.hidden) actions.appendChild(primaryBtn);
  modal.appendChild(titleEl);
  modal.appendChild(bodyEl);
  modal.appendChild(actions);
  backdrop.appendChild(modal);
  document.body.appendChild(backdrop);
  document.body.classList.add("studio-modal-open");

  var previousFocus = document.activeElement;
  var closed = false;

  function setBodyLines(lines) {
    bodyEl.textContent = "";
    (lines || []).forEach(function (line) {
      var p = document.createElement("p");
      p.textContent = line;
      bodyEl.appendChild(p);
    });
  }

  function cleanup() {
    if (closed) return;
    closed = true;
    backdrop.remove();
    if (!document.querySelector(".studio__modal-backdrop")) {
      document.body.classList.remove("studio-modal-open");
    }
    if (previousFocus && previousFocus.focus) focusNoScroll(previousFocus);
  }

  secondaryBtn.addEventListener("click", function () { controller.close(false); });
  primaryBtn.addEventListener("click", function () {
    if (typeof controller._onPrimary === "function") controller._onPrimary();
    else controller.close(true);
  });
  backdrop.addEventListener("click", function (e) {
    if (e.target === backdrop) controller.close(false);
  });

  var controller = {
    el: modal,
    setTitle: function (text) { titleEl.textContent = text; },
    setBodyLines: setBodyLines,
    setProgress: function (hint) {
      setBodyLines([
        "「" + (opts.tripTitle || "") + "」",
        LONGSHOT_PRESETS.shelf.label,
        hint || progressSynthesizingTitleForPlatform(opts.platform),
      ]);
    },
    showResult: function (formatted, tripId) {
      controller.setTitle(formatted.ok ? formatted.title : formatted.title);
      // FE-FTUE-04 · 发群句在第一可读行；preset / 路径次之
      var lines = [];
      if (formatted.ok) {
        lines.push("「" + (opts.tripTitle || "") + "」");
        (formatted.lines || []).forEach(function (line) {
          lines.push(line);
        });
        lines.push(LONGSHOT_PRESETS.shelf.label);
        try {
          trackStudioEvent("longshot_success_share_hint_shown", {
            trip_id: tripId,
            source: "shelf",
            platform: formatted.platform || "wechat_chat",
          });
        } catch (_e) {}
      } else {
        lines = [LONGSHOT_PRESETS.shelf.label].concat(formatted.lines || []);
      }
      setBodyLines(lines);
      primaryBtn.hidden = false;
      primaryBtn.textContent = formatted.ok ? "在文件夹中显示" : "关闭";
      secondaryBtn.hidden = !formatted.ok;
      secondaryBtn.textContent = "关闭";
      // 成功/失败均可换种分享（对齐预览 task-dock）
      switchBtn.hidden = false;
      if (!actions.contains(switchBtn)) {
        actions.insertBefore(switchBtn, secondaryBtn.hidden ? primaryBtn : secondaryBtn);
      }
      switchBtn.onclick = function () {
        offerShelfSwitchShare(tripId, opts.tripTitle || tripId, controller);
      };
      controller._onPrimary = formatted.ok
        ? function () {
            trackStudioEvent("shelf_longshot_reveal", { trip_id: tripId });
            trackStudioEvent("ftue_reveal_folder", {
              trip_id: tripId,
              source: "shelf",
            });
            revealLongshotOutput(tripId, formatted.revealPath).catch(function () {
              toast("无法打开文件夹", { duration: 3200 });
            });
            controller.close(true);
          }
        : function () { controller.close(false); };
      focusNoScroll(primaryBtn);
    },
    close: function () {
      cleanup();
      if (_activeModal === controller) _activeModal = null;
    },
  };

  if (opts.initialLines) setBodyLines(opts.initialLines);
  _activeModal = controller;
  focusNoScroll(secondaryBtn.hidden ? primaryBtn : secondaryBtn);
  return controller;
}

/** FE-SR-08 · 书架成功面换种分享 → 意图卡；可选立即再导出。 */
function offerShelfSwitchShare(tripId, tripTitle, resultModal) {
  clearSessionIntent(tripId);
  var recipePromise = fetchServerRecipe(tripId, "shelf").then(function (res) {
    var cached = getCachedKeptN(tripId);
    var keptN =
      res && res.ok && res.keptN != null
        ? res.keptN
        : cached != null
          ? cached
          : 12;
    var hints = res && res.ok && res.tipRecipe ? res.tipRecipe.userHints : null;
    return { keptN: keptN, userHints: hints };
  });
  return recipePromise.then(function (meta) {
    return showAmbiguousIntentCard(meta.keptN, meta.userHints).then(function (choice) {
      if (!choice || !choice.intent) return;
      writeSessionIntent(tripId, choice.intent);
      var platform = INTENT_TO_PLATFORM[choice.intent] || "wechat_chat";
      trackStudioEvent("shelf_switch_share_method", {
        trip_id: tripId,
        intent: choice.intent,
        export_now: !!choice.exportNow,
      });
      if (resultModal) resultModal.close(true);
      if (choice.exportNow) {
        runShelfLongshot(
          { tripId: tripId, title: tripTitle },
          { surface: "switch_share", platform: platform, intent: choice.intent }
        );
      } else {
        toast("已换种分享方式 · 下次导出生效", { duration: 2800 });
      }
    });
  });
}

/**
 * @param {object} trip
 * @param {{ surface?: string, platform?: string, intent?: string }} opts
 */
export function runShelfLongshot(trip, opts) {
  opts = opts || {};
  var surface = opts.surface || "grid";
  var tripId = trip.tripId;
  var title = trip.title || tripId;
  var preset = Object.assign({}, LONGSHOT_PRESETS.shelf);
  if (opts.platform) preset.platform = opts.platform;
  if (opts.intent) preset.intent = opts.intent;
  if (opts.segmentMode) preset.segmentMode = opts.segmentMode;
  if (opts.includeZip === true || opts.includeZip === false) {
    preset.includeZip = opts.includeZip;
  }
  if (opts.includePages === true || opts.includePages === false) {
    preset.includePages = opts.includePages;
  }
  if (opts.portfolioPiece) preset.portfolioPiece = opts.portfolioPiece;

  trackStudioEvent("shelf_longshot_start", {
    trip_id: tripId,
    surface: surface,
    scale: preset.scale,
    copy_display: preset.copyDisplay,
    platform: preset.platform || null,
  });

  var modal = openShelfLongshotModal({
    title: isComposePlatform(preset.platform)
      ? progressTitleForPlatform(preset.platform)
      : "正在保存长图",
    tripTitle: title,
    platform: preset.platform,
    initialLines: [
      "「" + title + "」",
      preset.label,
      "正在提交任务…",
    ],
    primaryHidden: true,
    secondaryHidden: false,
    secondaryText: "关闭",
  });

  var dismissed = false;
  var originalClose = modal.close.bind(modal);
  modal.close = function () {
    dismissed = true;
    originalClose();
  };

  return startLongshotJob(tripId, preset, {
    onBusy: function () {
      modal.setProgress("排队中，请稍候…");
    },
  }).then(function (res) {
    if (dismissed) return null;
    if (isJobBusyResponse(res)) {
      trackStudioEvent("shelf_longshot_busy", { trip_id: tripId, surface: surface });
      modal.close();
      toast("已有长图任务进行中，请稍候", { duration: 3200 });
      return null;
    }
    if (res.status === 409) {
      modal.close();
      toast((res.body && res.body.message) || "请稍候再试", { duration: 3200 });
      return null;
    }
    if (res.status !== 202 || !res.body.jobId) {
      modal.close();
      var body = res.body || {};
      var hints = (body.recipe && body.recipe.userHints) || body.userHints || [];
      var soft =
        (Array.isArray(hints) && hints[0]) ||
        body.message ||
        "无法开始导出";
      // AC-OR-03b · 书架不弹意图卡；弱提示引导去预览换分享方式
      if (soft.indexOf("预览") < 0 && soft.indexOf("分享") < 0) {
        soft = soft + " · 可到预览选择其他分享方式";
      }
      toast(soft, { duration: 3600 });
      return null;
    }

    modal.setProgress(progressSynthesizingTitleForPlatform(preset.platform));
    var jobId = res.body.jobId;
    _backgroundJob = waitForLongshotJob(jobId, {
      onProgress: function (job) {
        if (dismissed) return;
        if (job.status === "running" && job.stageHint) {
          modal.setProgress(job.stageHint);
        }
      },
      onSlow: function () {
        if (dismissed) {
          toast("比预期久一些，请耐心等待…", { duration: 4000 });
          return;
        }
        modal.setProgress("比预期久一些，请耐心等待…");
      },
    }).then(function (job) {
      _backgroundJob = null;
      if (dismissed) {
        if (job.status === "succeeded") {
          markLongshotReady(tripId);
          toast("长图已保存", { duration: 3000 });
          if (typeof V2.reroute === "function") V2.reroute();
        }
        return job;
      }

      var formatted = formatLongshotResult(job);
      if (job.status === "succeeded") {
        markLongshotReady(tripId);
        trackStudioEvent("shelf_longshot_success", {
          trip_id: tripId,
          surface: surface,
          segmented: !!formatted.segmented,
          capture_method: formatted.captureMethod,
          output_count: formatted.outputs.length,
        });
        if (typeof V2.reroute === "function") V2.reroute();
        // FE-FST-05 / D-FST-13 · 禁止自动 reveal；主钮「在文件夹中显示」才打开
      } else {
        trackStudioEvent("shelf_longshot_fail", {
          trip_id: tripId,
          surface: surface,
          error_code: job.error && job.error.code,
        });
      }
      modal.showResult(formatted, tripId);
      return job;
    }).catch(function () {
      _backgroundJob = null;
      if (dismissed) return null;
      modal.close();
      toast("网络错误，请重试", { duration: 3200 });
      trackStudioEvent("shelf_longshot_fail", { trip_id: tripId, surface: surface, error_code: "network" });
      return null;
    });

    return _backgroundJob;
  }).catch(function () {
    if (!dismissed) {
      modal.close();
      toast("网络错误，请重试", { duration: 3200 });
    }
    return null;
  });
}

/** 书架 ⋯ · 是否可打开已导出长图（磁盘或本会话刚导出）。 */
export function canOpenShelfLongshotFolder(trip) {
  trip = trip || {};
  if (trip.longshotRevealRelPath || trip.hasLongshotExport) return true;
  return isLongshotReady(trip.tripId);
}

/**
 * 解析可 reveal 的长图相对路径：trips 行 → longshot-current.json → /trips 刷新。
 * @param {object} trip
 * @returns {Promise<string|null>}
 */
function resolveShelfLongshotRevealRel(trip) {
  var tripId = trip && trip.tripId;
  if (!tripId) return Promise.resolve(null);
  if (trip.longshotRevealRelPath) {
    return Promise.resolve(String(trip.longshotRevealRelPath));
  }
  return fetch(
    "/" +
      encodeURIComponent(tripId) +
      "/" +
      encodeURIComponent(EXPORT_OUTPUT_DIRNAME) +
      "/longshot-current.json?t=" +
      String(Date.now())
  )
    .then(function (resp) {
      if (!resp.ok) return null;
      return resp.json();
    })
    .then(function (data) {
      var files = data && data.files;
      if (!Array.isArray(files) || !files.length) return null;
      var name = String(files[0] || "").trim();
      // 清单里存的是裸文件名（与清单同层的约定），拼回子目录前缀才是可 reveal 的相对路径。
      return name ? EXPORT_OUTPUT_DIRNAME + "/" + name : null;
    })
    .catch(function () {
      return null;
    })
    .then(function (fromManifesto) {
      if (fromManifesto) return fromManifesto;
      return fetch("/__travelogue/trips?limit=100&offset=0")
        .then(function (resp) {
          if (!resp.ok) return null;
          return resp.json();
        })
        .then(function (payload) {
          var rows = (payload && payload.trips) || [];
          for (var i = 0; i < rows.length; i++) {
            if (rows[i] && rows[i].tripId === tripId && rows[i].longshotRevealRelPath) {
              return String(rows[i].longshotRevealRelPath);
            }
          }
          return null;
        })
        .catch(function () {
          return null;
        });
    });
}

/**
 * 书架 ⋯ · 打开已导出长图所在文件夹（选中首张 PNG）。
 * @param {object} trip
 * @param {{ surface?: string }} [opts]
 */
export function openShelfLongshotFolder(trip, opts) {
  opts = opts || {};
  var tripId = trip && trip.tripId;
  if (!tripId) {
    toast("无法打开文件夹", { duration: 3200 });
    return Promise.resolve(false);
  }
  if (!canOpenShelfLongshotFolder(trip)) {
    toast("尚未导出长图，请先「保存长图」", { duration: 3200 });
    return Promise.resolve(false);
  }
  trackStudioEvent("shelf_open_longshot_folder", {
    trip_id: tripId,
    surface: opts.surface || "grid",
  });
  return resolveShelfLongshotRevealRel(trip).then(function (rel) {
    if (!rel) {
      toast("长图文件已不在，请重新「保存长图」", { duration: 3600 });
      return false;
    }
    return revealLongshotOutput(tripId, rel)
      .then(function () {
        return true;
      })
      .catch(function () {
        toast("无法打开文件夹，文件可能已移动或删除", { duration: 3600 });
        return false;
      });
  });
}
