// @ts-nocheck
/**
 * LIVE · Preview toolbar task dock (export progress / success / layout pending).
 * Loaded by: init-v3.js. Filename v3 ≠ frozen.
 */
"use strict";

import { HELP_COPY, trackHelpEvent } from "./js/help-onboarding.js";
import { openHelpDrawer } from "./js/help-drawer.js";
import { trackStudioEvent } from "./js/analytics.js";
import { isAiSurfaceEnabled } from "./js/ai-surface.js";
import { DARK_COPY } from "./js/ai-surface-dark-copy.js";
import {
  portfolioRevealTargets,
  portfolioSuccessCopy,
} from "./js/portfolio-export-logic.js";
import { formatLongshotResult } from "./js/longshot-client.js";
import { COPY_DICTIONARY } from "./js/copy-dictionary.js";

var SUCCESS_AUTO_HIDE_MS = 8000;

export function mountPreviewTaskDock(root, hooks) {
  hooks = hooks || {};
  var dock = document.createElement("div");
  dock.className = "preview-task-dock";
  dock.hidden = true;
  dock.setAttribute("role", "status");
  dock.setAttribute("aria-live", "polite");
  document.body.appendChild(dock);

  var autoHideTimer = null;
  var dismissTimer = null;
  var _successShownAt = 0;
  var _progressModeTracked = "";

  function appendHelpDeepLink(textWrap, itemId, label) {
    var moreHelp = document.createElement("button");
    moreHelp.type = "button";
    moreHelp.className = "preview-task-dock__help-link";
    moreHelp.textContent = label || HELP_COPY.helpDeepLinkH3 || "了解更多 →";
    moreHelp.addEventListener("click", function () {
      openHelpDrawer({ source: "deep_link", itemId: itemId || "H3" });
    });
    textWrap.appendChild(moreHelp);
  }

  function clearTimers() {
    if (autoHideTimer) {
      clearTimeout(autoHideTimer);
      autoHideTimer = null;
    }
    if (dismissTimer) {
      clearTimeout(dismissTimer);
      dismissTimer = null;
    }
  }

  function emitSuccessVisibleMs() {
    if (!_successShownAt) return;
    var ms = Date.now() - _successShownAt;
    _successShownAt = 0;
    try {
      trackStudioEvent("longshot_success_visible_ms", { ms: ms });
    } catch (_e) {}
  }

  function hide() {
    emitSuccessVisibleMs();
    clearTimers();
    dock.hidden = true;
    dock.className = "preview-task-dock";
    dock.removeAttribute("aria-busy");
    dock.innerHTML = "";
    _progressModeTracked = "";
  }

  /**
   * 生成一条细进度条（0–1 比例），用于批量导出清单的总进度 / 单项进度。
   * 纯 DOM 结构 + 内联 width（CSS 里已有 transition 负责平滑动画，见
   * task-dock.css `__batch-*-bar__fill`），不依赖任何外部状态。
   */
  function _buildProgressBar(ratio, className) {
    var pct = Math.max(0, Math.min(1, Number(ratio) || 0)) * 100;
    var wrap = document.createElement("div");
    wrap.className = className;
    wrap.setAttribute("role", "progressbar");
    wrap.setAttribute("aria-valuemin", "0");
    wrap.setAttribute("aria-valuemax", "100");
    wrap.setAttribute("aria-valuenow", String(Math.round(pct)));
    var fill = document.createElement("div");
    fill.className = className + "__fill";
    fill.style.width = pct + "%";
    wrap.appendChild(fill);
    return wrap;
  }

  function scheduleAutoHide(ms, after) {
    clearTimers();
    autoHideTimer = setTimeout(function () {
      hide();
      if (typeof after === "function") after();
    }, ms || SUCCESS_AUTO_HIDE_MS);
  }

  function focusDockPrimary() {
    requestAnimationFrame(function () {
      var primary =
        dock.querySelector(".preview-task-dock__btn--primary") ||
        dock.querySelector(".preview-task-dock__btn--close") ||
        dock;
      if (primary && typeof primary.focus === "function") {
        try {
          primary.focus({ preventScroll: true });
        } catch (_e) {
          try {
            primary.focus();
          } catch (_e2) {}
        }
      }
    });
  }

  function buildCloseBtn(afterHide) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "preview-task-dock__btn preview-task-dock__btn--ghost preview-task-dock__btn--close";
    btn.setAttribute("aria-label", "关闭");
    btn.textContent = "×";
    btn.addEventListener("click", function () {
      hide();
      if (typeof afterHide === "function") afterHide();
      if (typeof hooks.onDismiss === "function") hooks.onDismiss();
    });
    return btn;
  }

  function trackProgressMode(pct) {
    var mode = typeof pct === "number" ? "percent" : "indeterminate";
    if (mode === _progressModeTracked) return;
    _progressModeTracked = mode;
    try {
      trackStudioEvent("longshot_progress_mode", {
        mode: mode,
        pct: typeof pct === "number" ? pct : null,
      });
    } catch (_e) {}
  }

  function showExporting(opts) {
    opts = opts || {};
    clearTimers();
    _successShownAt = 0;
    dock.hidden = false;
    dock.className = "preview-task-dock preview-task-dock--exporting";
    dock.setAttribute("aria-busy", "true");
    dock.innerHTML = "";

    var icon = document.createElement("span");
    icon.className = "preview-task-dock__icon";
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = "⏳";

    var textWrap = document.createElement("div");
    textWrap.className = "preview-task-dock__text";
    var main = document.createElement("span");
    main.className = "preview-task-dock__main";
    // P0 · 兜底文案保持平台中立；真实标题始终由调用方按 platform 传入
    // （见 preview-toolbar/longshot.js · humanExportProgress）。
    main.textContent = opts.title || "正在导出中…";
    textWrap.appendChild(main);
    if (opts.subtitle) {
      var sub = document.createElement("small");
      sub.textContent = opts.subtitle;
      textWrap.appendChild(sub);
    }

    var progress = document.createElement("div");
    progress.className = "preview-task-dock__progress";
    progress.innerHTML = "<i></i>";
    // FE-FST-03 · 未知进度用 indeterminate，禁假 0%
    if (typeof opts.pct === "number") {
      progress.querySelector("i").style.width = Math.max(0, Math.min(100, opts.pct)) + "%";
    } else {
      progress.classList.add("preview-task-dock__progress--indeterminate");
    }
    trackProgressMode(opts.pct);

    var actions = document.createElement("div");
    actions.className = "preview-task-dock__actions";
    // LCC V1 · 真协作取消：提供「取消导出」；× 仅关面板不取消 Job
    if (typeof hooks.onCancelExport === "function") {
      var cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.className = "preview-task-dock__btn preview-task-dock__btn--ghost";
      cancelBtn.textContent = "取消导出";
      cancelBtn.addEventListener("click", function () {
        hooks.onCancelExport();
      });
      actions.appendChild(cancelBtn);
    }
    actions.appendChild(buildCloseBtn());

    dock.appendChild(icon);
    dock.appendChild(textWrap);
    dock.appendChild(progress);
    dock.appendChild(actions);
    dock._progressEl = progress;
    dock._progressFill = progress.querySelector("i");
    dock._mainEl = main;
    dock._subEl = textWrap.querySelector("small");
  }

  function updateExporting(opts) {
    opts = opts || {};
    if (dock.hidden || !dock.classList.contains("preview-task-dock--exporting")) {
      showExporting(opts);
      return;
    }
    if (dock._mainEl && opts.title) dock._mainEl.textContent = opts.title;
    if (opts.subtitle) {
      if (!dock._subEl) {
        dock._subEl = document.createElement("small");
        dock.querySelector(".preview-task-dock__text").appendChild(dock._subEl);
      }
      dock._subEl.textContent = opts.subtitle;
    }
    if (!dock._progressFill || !dock._progressEl) return;
    if (typeof opts.pct === "number") {
      dock._progressEl.classList.remove("preview-task-dock__progress--indeterminate");
      dock._progressFill.style.width = Math.max(0, Math.min(100, opts.pct)) + "%";
    } else {
      dock._progressEl.classList.add("preview-task-dock__progress--indeterminate");
      dock._progressFill.style.width = "";
    }
    trackProgressMode(opts.pct);
  }

  function showSuccess(job, tripId) {
    clearTimers();
    var result = (job && job.result) || {};
    var outputs = result.outputs || [];

    dock.hidden = false;
    dock.className = "preview-task-dock preview-task-dock--success";
    dock.setAttribute("aria-busy", "false");
    dock.innerHTML = "";
    _progressModeTracked = "";
    _successShownAt = Date.now();

    var icon = document.createElement("span");
    icon.className = "preview-task-dock__icon";
    icon.textContent = job && job.status === "failed" ? "!" : "✓";

    var textWrap = document.createElement("div");
    textWrap.className = "preview-task-dock__text";
    var main = document.createElement("span");
    main.className = "preview-task-dock__main";
    if (job && job.status === "failed") {
      main.textContent =
        (job.error && (job.error.message || job.error.code)) || "导出失败";
    } else if (result.platform === "portfolio_pages") {
      var packCopy = portfolioSuccessCopy(result, root && root._portfolio);
      main.textContent = packCopy.title;
    } else {
      main.textContent = formatLongshotResult(job).title;
    }
    textWrap.appendChild(main);
    if (job && job.status !== "failed") {
      var shareHint = document.createElement("small");
      shareHint.className = "preview-task-dock__share-hint";
      if (result.platform === "moments_grid") {
        shareHint.textContent =
          result.publishGuide ||
          ("已保存到此画册文件夹 · 共 " + outputs.length + " 张 1:1，有几张发几张");
        textWrap.appendChild(shareHint);
      } else if (result.platform === "wechat_moments") {
        shareHint.textContent =
          outputs.length > 1
            ? "这不是九宫格 · 已保存到此画册文件夹 · 共 " + outputs.length + " 张，按序发到朋友圈连读"
            : "这不是九宫格 · 已保存到此画册文件夹 · 按序发到朋友圈连读";
        textWrap.appendChild(shareHint);
      } else if (result.platform === "xiaohongshu") {
        shareHint.textContent =
          outputs.length > 1
            ? "已保存到此画册文件夹 · 共 " + outputs.length + " 张竖版拼贴海报，导入小红书按序发布"
            : "已保存到此画册文件夹 · 竖版拼贴海报，导入小红书发布即可";
        textWrap.appendChild(shareHint);
      } else if (result.platform === "wechat_official") {
        shareHint.textContent =
          outputs.length > 1
            ? "已保存到此画册文件夹 · 共 " + outputs.length + " 张配图，依次插入公众号图文正文即可"
            : "已保存到此画册文件夹 · 插入公众号图文正文即可";
        textWrap.appendChild(shareHint);
      } else if (result.platform === "poster_bric") {
        shareHint.textContent = "已保存到此画册文件夹 · 3:4 拼贴海报";
        textWrap.appendChild(shareHint);
      } else if (result.platform === "album_spread") {
        shareHint.textContent =
          "已保存到此画册文件夹 · 两卡跨页拼贴（约 1.53:1），可预览或送印";
        textWrap.appendChild(shareHint);
      } else if (result.platform === "portfolio_pages") {
        var packHint = portfolioSuccessCopy(result, root && root._portfolio);
        shareHint.textContent = packHint.hint;
        textWrap.appendChild(shareHint);
        if (packHint.overflowLine) {
          var overflowEl = document.createElement("small");
          overflowEl.className = "preview-task-dock__share-hint";
          overflowEl.textContent = packHint.overflowLine;
          if (packHint.overflowCta) {
            overflowEl.appendChild(document.createTextNode(" · "));
            var exitBtn = document.createElement("button");
            exitBtn.type = "button";
            exitBtn.className = "preview-task-dock__help-link";
            exitBtn.textContent = packHint.overflowCta;
            exitBtn.addEventListener("click", function () {
              if (root && typeof root._onPortfolioToJournal === "function") {
                root._onPortfolioToJournal();
              }
            });
            overflowEl.appendChild(exitBtn);
          }
          textWrap.appendChild(overflowEl);
        }
      } else {
        // FE-DFX-30 · 稳定成功面副文案（此画册文件夹）
        shareHint.textContent = "已保存到此画册文件夹";
        textWrap.appendChild(shareHint);
        trackStudioEvent("longshot_success_share_hint_shown", {
          platform: result.platform || "wechat_chat",
          source: "task_dock",
          guideKind: "saved_confirm",
        });
      }
      if (
        (result.platform === "wechat_moments" ||
          result.platform === "xiaohongshu" ||
          result.platform === "wechat_official" ||
          result.platform === "poster_bric" ||
          result.platform === "album_spread" ||
          result.platform === "moments_grid") &&
        result.publishGuide
      ) {
        // 非默认平台：backend publishGuide 优先覆盖短句
        shareHint.textContent = result.publishGuide;
      }
    }

    // FE-SFI-12 · 小红书/公众号文案包（dock 展开，不塞单行 bar）
    if (
      job &&
      job.status !== "failed" &&
      (result.platform === "xiaohongshu" || result.platform === "wechat_official") &&
      tripId
    ) {
      var packHost = document.createElement("div");
      packHost.className = "preview-task-dock__copy-pack";
      packHost.hidden = true;
      var packToggle = document.createElement("button");
      packToggle.type = "button";
      packToggle.className = "preview-task-dock__btn preview-task-dock__btn--ghost";
      packToggle.textContent = "复制文案包 ▾";
      packToggle.addEventListener("click", function () {
        if (!packHost.hidden) {
          packHost.hidden = true;
          packToggle.textContent = "复制文案包 ▾";
          return;
        }
        packToggle.disabled = true;
        fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/entry")
          .then(function (r) {
            return r.ok ? r.json() : null;
          })
          .then(function (entry) {
            packToggle.disabled = false;
            var pack = (entry && entry.shareCopyPack) || {};
            var title = String(pack.title || "").trim() || "旅行日记";
            var body = String(pack.body || "").trim();
            var topics = String(pack.topics || "#旅行日记").trim();
            var lines = ["标题　" + title];
            if (body) lines.push("正文　" + body);
            else lines.push("正文　（可粘贴后自填）");
            lines.push("话题　" + topics);
            packHost.innerHTML = "";
            var hint = document.createElement("p");
            hint.className = "preview-task-dock__copy-pack-hint";
            hint.textContent = body
              ? "标题、正文与话题可一键复制"
              : "标题和话题已备好 · 正文可粘贴后自填";
            packHost.appendChild(hint);
            var pre = document.createElement("pre");
            pre.className = "preview-task-dock__copy-pack-body";
            pre.textContent = lines.join("\n");
            packHost.appendChild(pre);
            var copyAll = document.createElement("button");
            copyAll.type = "button";
            copyAll.className =
              "preview-task-dock__btn preview-task-dock__btn--primary";
            copyAll.textContent = "一键复制";
            copyAll.addEventListener("click", function () {
              var blob = title + "\n\n" + (body ? body + "\n\n" : "") + topics;
              if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(blob).then(
                  function () {
                    copyAll.textContent = "已复制";
                  },
                  function () {
                    copyAll.textContent = "复制失败";
                  }
                );
              }
            });
            packHost.appendChild(copyAll);
            packHost.hidden = false;
            packToggle.textContent = "收起文案包 ▴";
          })
          .catch(function () {
            packToggle.disabled = false;
          });
      });
      textWrap.appendChild(packToggle);
      textWrap.appendChild(packHost);
    }

    var actions = document.createElement("div");
    actions.className = "preview-task-dock__actions";

    var isPortfolioPack = result.platform === "portfolio_pages";

    // Sprint 2 · 失败面只留一个重试（不改 confirmed platform）
    if (job && job.status === "failed" && typeof hooks.onReExport === "function") {
      var retryBtn = document.createElement("button");
      retryBtn.type = "button";
      retryBtn.className = "preview-task-dock__btn preview-task-dock__btn--primary";
      retryBtn.textContent = "重试";
      retryBtn.addEventListener("click", function () {
        hooks.onReExport({ tripId: tripId, source: "task_dock_retry" });
      });
      actions.appendChild(retryBtn);
    }

    if (job && job.status !== "failed" && isPortfolioPack) {
      var packActions = portfolioSuccessCopy(result, root && root._portfolio);
      if (typeof hooks.onOpenBook === "function") {
        var openBookBtn = document.createElement("button");
        openBookBtn.type = "button";
        openBookBtn.className = "preview-task-dock__btn preview-task-dock__btn--primary";
        openBookBtn.textContent = packActions.primary;
        openBookBtn.addEventListener("click", function () {
          hooks.onOpenBook(tripId);
        });
        actions.appendChild(openBookBtn);
      }
      var revealTargets = portfolioRevealTargets(result);
      var revealZip = hooks.onRevealZip || hooks.onRevealFolder;
      if (revealTargets.zipRel && typeof revealZip === "function") {
        var zipBtn = document.createElement("button");
        zipBtn.type = "button";
        zipBtn.className = "preview-task-dock__btn preview-task-dock__btn--ghost";
        zipBtn.textContent = packActions.secondaryZip;
        zipBtn.addEventListener("click", function () {
          revealZip(revealTargets.zipRel, tripId);
        });
        actions.appendChild(zipBtn);
      }
      if (typeof hooks.onRevealFolder === "function") {
        var folderBtn = document.createElement("button");
        folderBtn.type = "button";
        folderBtn.className = "preview-task-dock__btn preview-task-dock__btn--ghost";
        folderBtn.textContent = packActions.secondaryFolder;
        folderBtn.addEventListener("click", function () {
          hooks.onRevealFolder(revealTargets.folderRel, tripId);
        });
        actions.appendChild(folderBtn);
      }
    }

    // FE-SR-08 · 成功面保留「换用途」；失败面不给第二条恢复路径
    if (
      job &&
      job.status !== "failed" &&
      typeof hooks.onSwitchShareMethod === "function" &&
      !isPortfolioPack
    ) {
      var switchBtn = document.createElement("button");
      switchBtn.type = "button";
      switchBtn.className = "preview-task-dock__btn preview-task-dock__btn--ghost";
      var actionText = COPY_DICTIONARY.switchPurpose;
      switchBtn.setAttribute("data-share-ready-switch", "1");
      switchBtn.textContent = actionText;
      switchBtn.addEventListener("click", function () {
        hooks.onSwitchShareMethod({ actionText: actionText, tripId: tripId });
      });
      actions.appendChild(switchBtn);
    }

    if (
      job &&
      job.status !== "failed" &&
      !isPortfolioPack &&
      outputs.length &&
      typeof hooks.onRevealFolder === "function"
    ) {
      var revealBtn = document.createElement("button");
      revealBtn.type = "button";
      // FE-FST-04 / D-FST-14 · 唯一实心主钮
      revealBtn.className = "preview-task-dock__btn preview-task-dock__btn--primary";
      revealBtn.textContent = "在文件夹中显示";
      revealBtn.addEventListener("click", function () {
        try {
          trackHelpEvent("help_funnel_reveal_folder", {
            tripId: tripId || null,
          });
          trackStudioEvent("ftue_reveal_folder", {
            tripId: tripId || null,
            source: "task_dock",
          });
          trackStudioEvent("export_open_folder_clicked", {
            tripId: tripId || null,
            source: "task_dock",
          });
        } catch (_e) {}
        hooks.onRevealFolder(outputs[0], tripId);
      });
      actions.appendChild(revealBtn);
    }

    actions.appendChild(
      buildCloseBtn(job && job.status !== "failed" ? hooks.onResultDismissed : null)
    );

    dock.appendChild(icon);
    dock.appendChild(textWrap);
    dock.appendChild(actions);

    if (job && job.status !== "failed") {
      // D-FST-13 · 成功面展示时未自动 reveal（观测）
      try {
        trackStudioEvent("longshot_reveal_auto_blocked", {
          tripId: tripId || null,
          platform: result.platform || "wechat_chat",
        });
      } catch (_e) {}
      focusDockPrimary();
      if (result.platform !== "portfolio_pages") {
        scheduleAutoHide(SUCCESS_AUTO_HIDE_MS, hooks.onResultDismissed);
      }
    } else {
      focusDockPrimary();
    }
  }

  function showG1(opts) {
    opts = opts || {};
    clearTimers();
    dock.hidden = false;
    dock.className = "preview-task-dock preview-task-dock--g1";
    dock.innerHTML = "";

    var icon = document.createElement("span");
    icon.className = "preview-task-dock__icon";
    icon.textContent = "📋";

    var textWrap = document.createElement("div");
    textWrap.className = "preview-task-dock__text";
    var main = document.createElement("span");
    main.className = "preview-task-dock__main";
    main.textContent = opts.title || "章节结构待确认";
    textWrap.appendChild(main);
    var sub = document.createElement("small");
    sub.textContent =
      opts.subtitle || "请浏览各章顺序后确认，将继续排版成册";
    textWrap.appendChild(sub);

    var actions = document.createElement("div");
    actions.className = "preview-task-dock__actions";

    if (typeof hooks.onOpenStructure === "function") {
      var openBtn = document.createElement("button");
      openBtn.type = "button";
      openBtn.className = "preview-task-dock__btn preview-task-dock__btn--accent";
      openBtn.textContent = "去确认";
      openBtn.addEventListener("click", function () {
        hooks.onOpenStructure();
      });
      actions.appendChild(openBtn);
    }
    if (typeof hooks.onConfirmStructure === "function") {
      var confirmBtn = document.createElement("button");
      confirmBtn.type = "button";
      confirmBtn.className = "preview-task-dock__btn preview-task-dock__btn--primary";
      confirmBtn.textContent = "章节顺序 OK";
      confirmBtn.addEventListener("click", function () {
        hooks.onConfirmStructure();
      });
      actions.appendChild(confirmBtn);
    }

    var laterBtn = document.createElement("button");
    laterBtn.type = "button";
    laterBtn.className = "preview-task-dock__btn preview-task-dock__btn--ghost";
    laterBtn.textContent = "稍后";
    laterBtn.addEventListener("click", function () {
      hide();
      if (typeof hooks.onDismissG1 === "function") hooks.onDismissG1();
    });
    actions.appendChild(laterBtn);

    dock.appendChild(icon);
    dock.appendChild(textWrap);
    dock.appendChild(actions);
  }

  function showPending(opts) {
    opts = opts || {};
    clearTimers();
    dock.hidden = false;
    var titleText = opts.title || "版面有改动";
    // FE-DFX-41 · 「预览需更新」在窄屏走 compact（≤48px）
    var compact =
      opts.compact === true ||
      (typeof titleText === "string" && titleText.indexOf("预览需更新") !== -1);
    dock.className =
      "preview-task-dock preview-task-dock--warn" +
      (compact ? " preview-task-dock--compact" : "");
    dock.innerHTML = "";

    var icon = document.createElement("span");
    icon.className = "preview-task-dock__icon";
    icon.textContent = "⚠";

    var textWrap = document.createElement("div");
    textWrap.className = "preview-task-dock__text";
    var main = document.createElement("span");
    main.className = "preview-task-dock__main";
    main.textContent = compact ? "预览需更新" : titleText;
    textWrap.appendChild(main);
    if (!compact) {
      var sub = document.createElement("small");
      sub.textContent =
        opts.subtitle || "改过拼图或版式后，请先更新版面再导出";
      textWrap.appendChild(sub);
      // F-EXP-08 / SF-EXP-02 · 稍后 dismiss 后再见，仍提示导出会拦
      if (opts.remindExport !== false) {
        var remind = document.createElement("small");
        remind.className = "preview-task-dock__remind";
        remind.textContent = opts.remindText || "导出时仍会提醒";
        textWrap.appendChild(remind);
      }
      if (opts.helpLink !== false) {
        appendHelpDeepLink(
          textWrap,
          "H3",
          HELP_COPY.helpDeepLinkPending || "「分享图需更新」是什么意思 →"
        );
      }
    }

    var actions = document.createElement("div");
    actions.className = "preview-task-dock__actions";

    if (typeof hooks.onApplyLayout === "function") {
      var applyBtn = document.createElement("button");
      applyBtn.type = "button";
      applyBtn.className = "preview-task-dock__btn preview-task-dock__btn--primary";
      applyBtn.textContent = "更新版面";
      applyBtn.addEventListener("click", function () {
        hooks.onApplyLayout();
      });
      actions.appendChild(applyBtn);
    }

    var laterBtn = document.createElement("button");
    laterBtn.type = "button";
    laterBtn.className = "preview-task-dock__btn preview-task-dock__btn--ghost";
    laterBtn.textContent = "稍后";
    laterBtn.addEventListener("click", function () {
      hide();
      if (typeof hooks.onDismissPending === "function") hooks.onDismissPending();
    });
    actions.appendChild(laterBtn);

    dock.appendChild(icon);
    dock.appendChild(textWrap);
    dock.appendChild(actions);
  }

  function showStale(opts) {
    opts = opts || {};
    clearTimers();
    dock.hidden = false;
    dock.className = "preview-task-dock preview-task-dock--warn";
    dock.innerHTML = "";

    var icon = document.createElement("span");
    icon.className = "preview-task-dock__icon";
    icon.textContent = "↻";

    var textWrap = document.createElement("div");
    textWrap.className = "preview-task-dock__text";
    var main = document.createElement("span");
    main.className = "preview-task-dock__main";
    main.textContent = opts.title || "长图需更新";
    textWrap.appendChild(main);
    var sub = document.createElement("small");
    sub.textContent =
      opts.subtitle || "改过版面或照片后，导出最新图再发";
    textWrap.appendChild(sub);
    if (opts.helpLink !== false) {
      appendHelpDeepLink(textWrap, "H3", HELP_COPY.helpDeepLinkH3);
    }

    var actions = document.createElement("div");
    actions.className = "preview-task-dock__actions";

    if (typeof hooks.onReExport === "function") {
      var exportBtn = document.createElement("button");
      exportBtn.type = "button";
      exportBtn.className = "preview-task-dock__btn preview-task-dock__btn--primary";
      exportBtn.textContent = "重新导出";
      exportBtn.addEventListener("click", function () {
        hooks.onReExport();
      });
      actions.appendChild(exportBtn);
    }

    var laterBtn = document.createElement("button");
    laterBtn.type = "button";
    laterBtn.className = "preview-task-dock__btn preview-task-dock__btn--ghost";
    laterBtn.textContent = "稍后";
    laterBtn.addEventListener("click", function () {
      hide();
      if (typeof hooks.onDismissStale === "function") hooks.onDismissStale();
    });
    actions.appendChild(laterBtn);

    dock.appendChild(icon);
    dock.appendChild(textWrap);
    dock.appendChild(actions);
  }

  /** FE-SFI-05 · 文案刷新提示（高于 longshotStale；导出/成功面外层不进此栈） */
  function showCopyRefresh(opts) {
    opts = opts || {};
    // NAS · FE-NAS-09：默认面不渲染 copyRefresh
    if (!isAiSurfaceEnabled()) return;
    clearTimers();
    dock.hidden = false;
    dock.className = "preview-task-dock preview-task-dock--info";
    dock.innerHTML = "";

    var icon = document.createElement("span");
    icon.className = "preview-task-dock__icon";
    icon.textContent = "✎";

    var textWrap = document.createElement("div");
    textWrap.className = "preview-task-dock__text";
    var main = document.createElement("span");
    main.className = "preview-task-dock__main";
    main.textContent = opts.title || DARK_COPY.dockCopyRefreshTitle;
    textWrap.appendChild(main);

    var actions = document.createElement("div");
    actions.className = "preview-task-dock__actions";

    trackStudioEvent("copy_refresh_shown", {
      stub_hits: opts.stubHits != null ? opts.stubHits : undefined,
    });

    if (typeof hooks.onCopyRefresh === "function") {
      var refreshBtn = document.createElement("button");
      refreshBtn.type = "button";
      refreshBtn.className = "preview-task-dock__btn preview-task-dock__btn--primary";
      refreshBtn.textContent = DARK_COPY.dockCopyRefreshBtn;
      refreshBtn.addEventListener("click", function () {
        trackStudioEvent("copy_refresh_clicked", {});
        hooks.onCopyRefresh();
      });
      actions.appendChild(refreshBtn);
    }

    var dismissBtn = document.createElement("button");
    dismissBtn.type = "button";
    dismissBtn.className = "preview-task-dock__btn preview-task-dock__btn--ghost";
    dismissBtn.textContent = "不再提示";
    dismissBtn.addEventListener("click", function () {
      hide();
      if (typeof hooks.onDismissCopyRefresh === "function") {
        hooks.onDismissCopyRefresh({ persistent: true });
      }
    });
    actions.appendChild(dismissBtn);

    dock.appendChild(icon);
    dock.appendChild(textWrap);
    dock.appendChild(actions);
  }

  function showNextStepHint(opts) {
    opts = opts || {};
    clearTimers();
    dock.hidden = false;
    dock.className = "preview-task-dock preview-task-dock--next-hint";
    dock.innerHTML = "";

    var icon = document.createElement("span");
    icon.className = "preview-task-dock__icon";
    icon.textContent = "✓";

    var textWrap = document.createElement("div");
    textWrap.className = "preview-task-dock__text";
    var main = document.createElement("span");
    main.className = "preview-task-dock__main";
    main.textContent = opts.title || "版面已更新";
    textWrap.appendChild(main);
    var sub = document.createElement("small");
    sub.textContent = opts.subtitle || "再点「长图」即可导出";
    textWrap.appendChild(sub);
    if (opts.helpLink !== false) {
      appendHelpDeepLink(textWrap, "H3", HELP_COPY.helpDeepLinkH3);
    }

    var actions = document.createElement("div");
    actions.className = "preview-task-dock__actions";
    actions.appendChild(
      buildCloseBtn(function () {
        if (typeof hooks.onResultDismissed === "function") hooks.onResultDismissed();
      })
    );

    dock.appendChild(icon);
    dock.appendChild(textWrap);
    dock.appendChild(actions);
    // 残留：不自动隐藏，直到用户关闭或再点长图
  }

  /** D-FEED-04 · 标精选后 Dock 次路径：按精选重排 */
  function showFeaturedRerankCue(opts) {
    opts = opts || {};
    clearTimers();
    dock.hidden = false;
    dock.className = "preview-task-dock preview-task-dock--next-hint";
    dock.innerHTML = "";

    var icon = document.createElement("span");
    icon.className = "preview-task-dock__icon";
    icon.textContent = "★";

    var textWrap = document.createElement("div");
    textWrap.className = "preview-task-dock__text";
    var main = document.createElement("span");
    main.className = "preview-task-dock__main";
    main.textContent = opts.title || "已记下精选";
    textWrap.appendChild(main);
    var sub = document.createElement("small");
    sub.textContent =
      opts.subtitle ||
      HELP_COPY.featuredPageHint ||
      "不会立刻重排整本；若要改构图可按精选重排";
    textWrap.appendChild(sub);

    var actions = document.createElement("div");
    actions.className = "preview-task-dock__actions";
    var rerankBtn = document.createElement("button");
    rerankBtn.type = "button";
    rerankBtn.className = "preview-task-dock__btn preview-task-dock__btn--primary";
    rerankBtn.textContent =
      opts.cta || HELP_COPY.featuredRerankCta || "按精选重排";
    rerankBtn.addEventListener("click", function () {
      hide();
      if (typeof hooks.onResultDismissed === "function") hooks.onResultDismissed();
      if (typeof hooks.onFeaturedRerank === "function") hooks.onFeaturedRerank();
    });
    actions.appendChild(rerankBtn);
    actions.appendChild(
      buildCloseBtn(function () {
        if (typeof hooks.onResultDismissed === "function") hooks.onResultDismissed();
      })
    );

    dock.appendChild(icon);
    dock.appendChild(textWrap);
    dock.appendChild(actions);
  }

  /**
   * PRD-BATCH-EXPORT-MULTISELECT-V1 Stage 3 · 批量导出清单化进度/完成面。
   * 进行中（`opts.done` 为假）与完成（真，成功/部分失败混在一起——D-BEX-05
   * 不整体判失败）复用同一份渲染逻辑，仅动作区/自动隐藏策略不同。
   * @param {object} opts
   * @param {string} opts.title 顶部标题（如「批量导出中（1/2）」/「已完成 1/2 个模式（1 个失败）」）
   * @param {{label:string, status:'queued'|'running'|'done'|'failed', detail?:string}[]} opts.items
   * @param {boolean} [opts.done]
   * @param {string} [opts.tripId]
   * @param {string} [opts.firstOutput] 完成态「在文件夹中显示」用的首个成功产物路径
   * @param {Function} [opts.onDismiss]
   */
  function showBatchChecklist(opts) {
    opts = opts || {};
    clearTimers();
    dock.hidden = false;
    dock.className =
      "preview-task-dock preview-task-dock--batch" +
      (opts.done ? " preview-task-dock--success" : " preview-task-dock--exporting");
    dock.setAttribute("aria-busy", opts.done ? "false" : "true");
    dock.innerHTML = "";
    _progressModeTracked = "";
    _successShownAt = opts.done ? Date.now() : 0;

    var failedCount = (opts.items || []).filter(function (it) {
      return it.status === "failed";
    }).length;

    var icon = document.createElement("span");
    icon.className = "preview-task-dock__icon";
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = opts.done ? (failedCount ? "!" : "✓") : "⏳";

    var textWrap = document.createElement("div");
    textWrap.className = "preview-task-dock__text";
    var main = document.createElement("span");
    main.className = "preview-task-dock__main";
    main.textContent = opts.title || (opts.done ? "批量导出已完成" : "批量导出中…");
    textWrap.appendChild(main);

    // 总进度条（按「第几个平台/共几个平台」+ 当前平台内部细进度折算，见
    // batchOverallProgressRatio）；只在进行中态渲染，完成态清单本身已是终态。
    if (!opts.done && typeof opts.overallProgress === "number") {
      textWrap.appendChild(_buildProgressBar(opts.overallProgress, "preview-task-dock__batch-overall-bar"));
    }

    var list = document.createElement("ul");
    list.className = "preview-task-dock__batch-list";
    (opts.items || []).forEach(function (item) {
      var li = document.createElement("li");
      li.className =
        "preview-task-dock__batch-item preview-task-dock__batch-item--" +
        (item.status || "queued");
      var mark = document.createElement("span");
      mark.className = "preview-task-dock__batch-mark";
      mark.setAttribute("aria-hidden", "true");
      mark.textContent =
        item.status === "done"
          ? "✅"
          : item.status === "failed"
            ? "✗"
            : item.status === "running"
              ? "⏳"
              : "・";
      li.appendChild(mark);
      var label = document.createElement("span");
      label.className = "preview-task-dock__batch-label";
      label.textContent = item.label + (item.detail ? " · " + item.detail : "");
      li.appendChild(label);
      // 2026-08-06 用户实测：只保留顶部总进度条。单项细进度条在不同管线
      // （拼贴有页进度、微信长图未必有）下忽有忽无，清单显得乱，也多一次 DOM。
      list.appendChild(li);
    });
    textWrap.appendChild(list);

    var actions = document.createElement("div");
    actions.className = "preview-task-dock__actions";
    if (!opts.done) {
      if (typeof hooks.onCancelExport === "function") {
        var cancelBtn = document.createElement("button");
        cancelBtn.type = "button";
        cancelBtn.className = "preview-task-dock__btn preview-task-dock__btn--ghost";
        cancelBtn.textContent = "取消导出";
        cancelBtn.addEventListener("click", function () {
          hooks.onCancelExport();
        });
        actions.appendChild(cancelBtn);
      }
      actions.appendChild(buildCloseBtn());
    } else {
      // FE-SR-08 / USR-03 同款：成功/部分失败均提供「换用途」
      if (typeof hooks.onSwitchShareMethod === "function") {
        var switchBtn = document.createElement("button");
        switchBtn.type = "button";
        switchBtn.className = "preview-task-dock__btn preview-task-dock__btn--ghost";
        switchBtn.setAttribute("data-share-ready-switch", "1");
        switchBtn.textContent = COPY_DICTIONARY.switchPurpose;
        switchBtn.addEventListener("click", function () {
          hooks.onSwitchShareMethod({ actionText: COPY_DICTIONARY.switchPurpose, tripId: opts.tripId });
        });
        actions.appendChild(switchBtn);
      }
      if (
        opts.firstOutput &&
        typeof hooks.onRevealFolder === "function"
      ) {
        var revealBtn = document.createElement("button");
        revealBtn.type = "button";
        revealBtn.className = "preview-task-dock__btn preview-task-dock__btn--primary";
        revealBtn.textContent = "在文件夹中显示";
        revealBtn.addEventListener("click", function () {
          hooks.onRevealFolder(opts.firstOutput, opts.tripId);
        });
        actions.appendChild(revealBtn);
      }
      actions.appendChild(buildCloseBtn(opts.onDismiss));
    }

    dock.appendChild(icon);
    dock.appendChild(textWrap);
    dock.appendChild(actions);

    if (opts.done) {
      // 与 showSuccess 一致：完成态才夺焦/自动隐藏；进行中态每次 tick 都会
      // 重渲染（renderBatchProgress 轮询回调），不能像 showSuccess 那样抢焦点。
      focusDockPrimary();
      scheduleAutoHide(SUCCESS_AUTO_HIDE_MS, opts.onDismiss);
    }
  }

  function showError(messageOrOpts) {
    var opts =
      messageOrOpts && typeof messageOrOpts === "object"
        ? messageOrOpts
        : { title: messageOrOpts || "导出失败" };
    var title = opts.title || opts.message || "导出失败";
    clearTimers();
    dock.hidden = false;
    dock.className = "preview-task-dock preview-task-dock--success";
    dock.innerHTML = "";

    var icon = document.createElement("span");
    icon.className = "preview-task-dock__icon";
    icon.textContent = "!";

    var textWrap = document.createElement("div");
    textWrap.className = "preview-task-dock__text";
    var main = document.createElement("span");
    main.className = "preview-task-dock__main";
    main.textContent = title;
    textWrap.appendChild(main);
    if (opts.subtitle) {
      var sub = document.createElement("small");
      sub.textContent = opts.subtitle;
      textWrap.appendChild(sub);
    }

    var actions = document.createElement("div");
    actions.className = "preview-task-dock__actions";
    if (typeof hooks.onReExport === "function" && opts.retry !== false) {
      var errRetry = document.createElement("button");
      errRetry.type = "button";
      errRetry.className = "preview-task-dock__btn preview-task-dock__btn--primary";
      errRetry.textContent = "重试";
      errRetry.addEventListener("click", function () {
        hooks.onReExport({ source: "task_dock_error_retry" });
      });
      actions.appendChild(errRetry);
    }
    if (opts.linkHref && opts.linkText) {
      var link = document.createElement("a");
      link.className = "preview-task-dock__btn preview-task-dock__btn--ghost";
      link.href = opts.linkHref;
      link.textContent = opts.linkText;
      actions.appendChild(link);
    }
    actions.appendChild(buildCloseBtn(null));

    dock.appendChild(icon);
    dock.appendChild(textWrap);
    dock.appendChild(actions);
  }

  return {
    hide: hide,
    showExporting: showExporting,
    updateExporting: updateExporting,
    showSuccess: showSuccess,
    showG1: showG1,
    showPending: showPending,
    showStale: showStale,
    showCopyRefresh: showCopyRefresh,
    showNextStepHint: showNextStepHint,
    showFeaturedRerankCue: showFeaturedRerankCue,
    showBatchChecklist: showBatchChecklist,
    showError: showError,
  };
}
