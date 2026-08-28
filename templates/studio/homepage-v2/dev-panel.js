/**
 * 首页 v2 · Dev Panel（DEV-HARNESS.md §4 · M20-h）。
 *
 * loopback 或 ?dev=1 时注入面板；默认隐藏，经设置 Popover 唤起（v2.1 · D-15）。
 */
import { harnessEnabled } from "./harness.js";
import { initVariantGuard, syncVariantGuard } from "./variant-guard.js";

var STATES = [
  { v: "", label: "（正常路由）" },
  { v: "loading", label: "Loading" },
  { v: "idle-empty", label: "IdleEmpty" },
  { v: "idle-returning", label: "IdleReturning" },
  { v: "importing", label: "Importing" },
  { v: "importing-cold", label: "Importing 冷启动" },
  { v: "importing-resume", label: "Importing 续 poll" },
  { v: "first-success", label: "FirstSuccess" },
  { v: "failed", label: "Failed" },
  { v: "sheet-open", label: "Sheet 打开" },
  { v: "offline", label: "Offline" },
];

var FIXTURES = [
  { v: "", label: "（真实 /trips）" },
  { v: "empty", label: "empty" },
  { v: "single-stale", label: "single-stale" },
  { v: "single-algorithm-stale", label: "single-algorithm-stale" },
  { v: "multi", label: "multi" },
  { v: "delivered", label: "delivered" },
  { v: "many", label: "many (25)" },
  { v: "demo-only", label: "demo-only" },
  { v: "error", label: "error" },
];

var JOBS = [
  { v: "", label: "（真实 job）" },
  { v: "running", label: "running" },
  { v: "succeeded", label: "succeeded" },
];

function params() {
  try {
    return new URLSearchParams(window.location.search);
  } catch (e) {
    return new URLSearchParams("");
  }
}

function buildReproUrl(next) {
  var p = new URLSearchParams(window.location.search);
  Object.keys(next).forEach(function (key) {
    if (next[key]) p.set(key, next[key]);
    else p.delete(key);
  });
  if (!p.has("dev")) p.set("dev", "1");
  var qs = p.toString();
  return window.location.pathname + (qs ? "?" + qs : "");
}

function wireSelect(id, paramName, options) {
  var sel = document.getElementById(id);
  if (!sel) return;
  var cur = params().get(paramName) || "";
  sel.value = cur;
  sel.addEventListener("change", function () {
    var patch = {};
    patch[paramName] = sel.value;
    window.location.href = buildReproUrl(patch);
  });
}

function wireToggle(id, paramName) {
  var el = document.getElementById(id);
  if (!el) return;
  el.checked = params().get(paramName) === "1";
  el.addEventListener("change", function () {
    var patch = {};
    patch[paramName] = el.checked ? "1" : "";
    window.location.href = buildReproUrl(patch);
  });
}

/** 由设置 Popover「打开 Dev 面板」唤起。 */
export function openDevPanelFromSettings() {
  var panel = document.getElementById("v2-dev-panel");
  if (!panel) return;
  panel.hidden = false;
  panel.classList.add("is-visible");
  var body = document.getElementById("v2-dev-panel-body");
  var toggle = document.getElementById("v2-dev-panel-toggle");
  if (body) body.hidden = false;
  if (toggle) {
    toggle.setAttribute("aria-expanded", "true");
    toggle.focus();
  }
}

export function initDevPanel() {
  if (!harnessEnabled()) return;
  if (document.getElementById("v2-dev-panel")) return;

  var panel = document.createElement("aside");
  panel.id = "v2-dev-panel";
  panel.className = "v2-dev-panel";
  panel.hidden = true;
  panel.innerHTML =
    '<button type="button" class="v2-dev-panel__toggle" id="v2-dev-panel-toggle" aria-expanded="false">Dev</button>' +
    '<div class="v2-dev-panel__body" id="v2-dev-panel-body">' +
    '<p class="v2-dev-panel__title">Studio v2 Harness</p>' +
    '<label class="v2-dev-panel__field">studioState<select id="v2-dev-state"></select></label>' +
    '<label class="v2-dev-panel__field">studioFixture<select id="v2-dev-fixture"></select></label>' +
    '<label class="v2-dev-panel__field">studioJob<select id="v2-dev-job"></select></label>' +
    '<label class="v2-dev-panel__check"><input type="checkbox" id="v2-dev-assets-fail" /> studioAssetsFail</label>' +
    '<label class="v2-dev-panel__check"><input type="checkbox" id="v2-dev-slow-net" /> studioSlowNet</label>' +
    '<button type="button" class="v2-dev-panel__copy" id="v2-dev-copy">Copy repro URL</button>' +
    '<a href="/classic" class="v2-dev-panel__classic" id="v2-classic-link" hidden>经典首页 →</a>' +
    "</div>";

  document.body.appendChild(panel);

  function fillOptions(id, options) {
    var sel = document.getElementById(id);
    if (!sel) return;
    options.forEach(function (opt) {
      var o = document.createElement("option");
      o.value = opt.v;
      o.textContent = opt.label;
      sel.appendChild(o);
    });
  }

  fillOptions("v2-dev-state", STATES);
  fillOptions("v2-dev-fixture", FIXTURES);
  fillOptions("v2-dev-job", JOBS);

  wireSelect("v2-dev-state", "studioState", STATES);
  wireSelect("v2-dev-fixture", "studioFixture", FIXTURES);
  wireSelect("v2-dev-job", "studioJob", JOBS);
  wireToggle("v2-dev-assets-fail", "studioAssetsFail");
  wireToggle("v2-dev-slow-net", "studioSlowNet");

  var copyBtn = document.getElementById("v2-dev-copy");
  if (copyBtn) {
    copyBtn.addEventListener("click", function () {
      var url = window.location.origin + window.location.pathname + window.location.search;
      var done = function () {
        if (typeof studioToast === "function") {
          studioToast("已复制 repro URL", { duration: 1800 });
        }
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(done, done);
      }
    });
  }

  var toggle = document.getElementById("v2-dev-panel-toggle");
  var body = document.getElementById("v2-dev-panel-body");
  if (toggle && body) {
    toggle.addEventListener("click", function () {
      var open = body.hidden;
      body.hidden = !open;
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  initVariantGuard();
  syncVariantGuard();
}
