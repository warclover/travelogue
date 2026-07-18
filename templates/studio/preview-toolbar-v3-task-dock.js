/**
 * Preview toolbar v3 · bottom task dock (export progress / success / layout pending).
 */
"use strict";

import { HELP_COPY, trackHelpEvent } from "./js/help-onboarding.js";
import { openHelpDrawer } from "./js/help-drawer.js";
import { trackStudioEvent } from "./js/analytics.js";

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
    main.textContent = opts.title || "正在生成可发微信的长图…";
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
    } else if (result.platform === "moments_grid") {
      var nGrid = result.pageCount || outputs.length;
      main.textContent = "✓ " + nGrid + " 张九宫格已就绪";
    } else if (result.platform === "wechat_moments") {
      var nMoments = result.pageCount || outputs.length;
      main.textContent = "✓ " + nMoments + " 张长图连读已就绪";
    } else if (result.platform === "xiaohongshu") {
      var nXhs = result.pageCount || outputs.length;
      main.textContent = "✓ " + nXhs + " 张 3:4 配图已就绪";
    } else {
      // FE-FST-04 / D-FST-13 · 默认微信群：已保存确认，不塞发群教学
      var displayTitle = String(
        result.displayTitle || result.title || ""
      ).trim();
      if (outputs.length > 1) {
        main.textContent = "长图已保存（共 " + outputs.length + " 段）";
      } else if (displayTitle) {
        main.textContent = "《" + displayTitle + "》长图已保存";
      } else {
        main.textContent = "长图已保存";
      }
    }
    textWrap.appendChild(main);
    if (job && job.status !== "failed") {
      var shareHint = document.createElement("small");
      shareHint.className = "preview-task-dock__share-hint";
      if (result.platform === "moments_grid") {
        shareHint.textContent =
          result.publishGuide ||
          ("已保存到本机 · 共 " + outputs.length + " 张 1:1，有几张发几张");
        textWrap.appendChild(shareHint);
      } else if (result.platform === "wechat_moments") {
        shareHint.textContent =
          outputs.length > 1
            ? "这不是九宫格 · 已保存到本机 · 共 " + outputs.length + " 张，按序发到朋友圈连读"
            : "这不是九宫格 · 已保存到本机 · 按序发到朋友圈连读";
        textWrap.appendChild(shareHint);
      } else if (result.platform === "xiaohongshu") {
        shareHint.textContent =
          outputs.length > 1
            ? "已保存到本机 · 共 " + outputs.length + " 张，导入小红书按序发布"
            : "已保存到本机 · 导入小红书发布即可";
        textWrap.appendChild(shareHint);
      } else {
        // Help H4 按需；默认面不展示发群三要素（First-Session Trust）
        trackStudioEvent("longshot_success_share_hint_shown", {
          platform: result.platform || "wechat_chat",
          source: "task_dock",
          guideKind: "saved_confirm",
        });
        var moreHelp = document.createElement("button");
        moreHelp.type = "button";
        moreHelp.className = "preview-task-dock__help-link";
        moreHelp.textContent = "怎么发到微信群？";
        moreHelp.addEventListener("click", function () {
          openHelpDrawer({ source: "deep_link", itemId: "H4" });
        });
        textWrap.appendChild(moreHelp);
      }
      if (
        (result.platform === "wechat_moments" ||
          result.platform === "xiaohongshu" ||
          result.platform === "moments_grid") &&
        result.publishGuide
      ) {
        // 非默认平台：backend publishGuide 优先覆盖短句
        shareHint.textContent = result.publishGuide;
      }
    }

    var actions = document.createElement("div");
    actions.className = "preview-task-dock__actions";

    // FE-SR-08 / USR-03 · 成功与失败均提供「换种分享方式」（禁止第二套成功面）
    if (typeof hooks.onSwitchShareMethod === "function") {
      var switchBtn = document.createElement("button");
      switchBtn.type = "button";
      switchBtn.className =
        job && job.status === "failed"
          ? "preview-task-dock__btn preview-task-dock__btn--accent"
          : "preview-task-dock__btn preview-task-dock__btn--ghost";
      var actionText = "换种分享方式";
      switchBtn.setAttribute("data-share-ready-switch", "1");
      switchBtn.textContent = actionText;
      switchBtn.addEventListener("click", function () {
        hooks.onSwitchShareMethod({ actionText: actionText, tripId: tripId });
      });
      actions.appendChild(switchBtn);
    }

    if (job && job.status !== "failed" && outputs.length && typeof hooks.onRevealFolder === "function") {
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
        } catch (_e) {}
        hooks.onRevealFolder(outputs[0], tripId);
      });
      actions.appendChild(revealBtn);
    }

    if (job && job.status !== "failed" && outputs.length && typeof hooks.onCopyPath === "function") {
      var copyBtn = document.createElement("button");
      copyBtn.type = "button";
      copyBtn.className = "preview-task-dock__btn preview-task-dock__btn--ghost";
      copyBtn.textContent = "复制路径";
      copyBtn.addEventListener("click", function () {
        hooks.onCopyPath(outputs.join("\n"));
      });
      actions.appendChild(copyBtn);
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
      scheduleAutoHide(SUCCESS_AUTO_HIDE_MS, hooks.onResultDismissed);
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
      opts.subtitle || "请浏览各章顺序后确认，将继续生成文案并排版";
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
    dock.className = "preview-task-dock preview-task-dock--warn";
    dock.innerHTML = "";

    var icon = document.createElement("span");
    icon.className = "preview-task-dock__icon";
    icon.textContent = "⚠";

    var textWrap = document.createElement("div");
    textWrap.className = "preview-task-dock__text";
    var main = document.createElement("span");
    main.className = "preview-task-dock__main";
    main.textContent = opts.title || "版面有改动";
    textWrap.appendChild(main);
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
    main.textContent = opts.title || "分享图需更新";
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
    showNextStepHint: showNextStepHint,
    showFeaturedRerankCue: showFeaturedRerankCue,
    showError: showError,
  };
}
