// @ts-nocheck
/**
 * QFX D-QFX-12 · 复制三态：pending → 原生/fallback 成功 → 最终失败。
 */
"use strict";

export var COPY_PENDING = "正在复制…";
export var COPY_OK = "地址已复制，请在电脑浏览器打开";
export var COPY_DONE = "已复制";
export var COPY_FAIL = "无法自动复制。请长按选择下方地址并复制。";
export var COPY_RETRY = "重新复制";

function toast(msg, ms) {
  if (typeof studioToast === "function") {
    studioToast(msg, { duration: ms || 2200 });
  }
}

function fallbackCopy(text) {
  try {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.left = "-9999px";
    document.body.appendChild(ta);
    ta.select();
    var ok = document.execCommand("copy");
    document.body.removeChild(ta);
    return !!ok;
  } catch (_e) {
    return false;
  }
}

/**
 * @returns {Promise<"ok"|"fail">}
 */
export function copyTextThreeState(text) {
  var value = String(text || "");
  if (!value) return Promise.resolve("fail");
  toast(COPY_PENDING, 1200);
  if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
    return navigator.clipboard.writeText(value).then(
      function () {
        return "ok";
      },
      function () {
        return fallbackCopy(value) ? "ok" : "fail";
      }
    );
  }
  return Promise.resolve(fallbackCopy(value) ? "ok" : "fail");
}

/**
 * @param {{
 *   button: HTMLElement,
 *   urlInput?: HTMLInputElement|null,
 *   getUrl: () => string,
 *   defaultLabel?: string,
 *   onTrack?: (result: string) => void
 * }} opts
 */
export function bindCopyPageUrlControl(opts) {
  var button = opts && opts.button;
  if (!button || button.dataset.copyBound === "1") return;
  button.dataset.copyBound = "1";
  var defaultLabel =
    opts.defaultLabel || button.textContent || "复制电脑打开地址";
  var restoreTimer = null;
  function restoreDefaultLabel() {
    if (restoreTimer) {
      clearTimeout(restoreTimer);
      restoreTimer = null;
    }
    restoreTimer = setTimeout(function () {
      button.textContent = defaultLabel;
      restoreTimer = null;
    }, 2200);
  }
  button.addEventListener("click", function () {
    var url = typeof opts.getUrl === "function" ? opts.getUrl() : "";
    var input = opts.urlInput || null;
    button.textContent = COPY_PENDING;
    copyTextThreeState(url).then(function (result) {
      if (typeof opts.onTrack === "function") opts.onTrack(result);
      if (result === "ok") {
        toast(COPY_OK, 2200);
        button.textContent = COPY_DONE;
        restoreDefaultLabel();
        if (input) {
          input.hidden = true;
          input.setAttribute("hidden", "");
        }
        return;
      }
      toast(COPY_FAIL, 3200);
      button.textContent = COPY_RETRY;
      if (input) {
        input.hidden = false;
        input.removeAttribute("hidden");
        input.value = url;
        try {
          input.focus();
          input.select();
        } catch (_e) {
          /* ignore */
        }
      }
    });
  });
}
