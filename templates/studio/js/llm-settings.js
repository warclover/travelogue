/**
 * Desktop LLM Setup V1 · 写作引擎 / AI 文案设置（首页+预览共用）
 * MF-02: 单一组件；预览内 Modal，不跳首页。
 */
import { studioAuthHeaders } from "./http.js";
import { trackStudioEvent } from "./analytics.js";

var ROOT_ID = "studio-llm-settings-root";
var _open = false;
var _source = "settings";
var _onChange = null;

/** 官方申请入口（简化指引：链到对方新手流程，不在应用内复述逐步教程） */
var LLM_KEY_LINKS = {
  deepseek: {
    href: "https://platform.deepseek.com/api_keys",
    label: "DeepSeek 创建 API Key",
  },
  dashscope: {
    href: "https://bailian.console.aliyun.com/",
    label: "通义百炼控制台",
    guideHref: "https://help.aliyun.com/zh/model-studio/get-api-key",
    guideLabel: "官方说明",
  },
};

function $(sel, root) {
  return (root || document).querySelector(sel);
}

function ensureRoot() {
  var el = document.getElementById(ROOT_ID);
  if (el) return el;
  el = document.createElement("div");
  el.id = ROOT_ID;
  el.className = "studio-llm-settings";
  el.hidden = true;
  el.setAttribute("role", "dialog");
  el.setAttribute("aria-modal", "true");
  el.setAttribute("aria-labelledby", "studio-llm-settings-title");
  el.innerHTML =
    '<div class="studio-llm-settings__scrim" data-llm-close="1"></div>' +
    '<div class="studio-llm-settings__panel">' +
    '<div class="studio-llm-settings__head">' +
    '<div><p id="studio-llm-settings-title" class="studio-llm-settings__title">AI 文案（可选）</p>' +
    '<p class="studio-llm-settings__desc">不配置也可以正常导入、排版和导出长图。配置后可在预览中生成杂志感文案。</p></div>' +
    '<button type="button" class="studio-llm-settings__close" data-llm-close="1" aria-label="关闭">×</button>' +
    "</div>" +
    '<p class="studio-llm-settings__badge" id="studio-llm-readiness">未配置</p>' +
    '<p class="studio-llm-settings__hint" id="studio-llm-userdata" hidden></p>' +
    '<label class="studio-llm-settings__label" for="studio-llm-provider">服务商</label>' +
    '<select id="studio-llm-provider" class="studio-llm-settings__input">' +
    '<option value="deepseek">DeepSeek</option>' +
    '<option value="dashscope">通义千问（DashScope）</option>' +
    "</select>" +
    '<label class="studio-llm-settings__label" for="studio-llm-key">API Key</label>' +
    '<div class="studio-llm-settings__keyrow">' +
    '<input id="studio-llm-key" class="studio-llm-settings__input" type="password" autocomplete="off" placeholder="粘贴你的 API Key" />' +
    '<button type="button" class="studio-llm-settings__linkbtn" id="studio-llm-toggle-key">显示</button>' +
    "</div>" +
    '<p class="studio-llm-settings__howto" id="studio-llm-howto"></p>' +
    '<details class="studio-llm-settings__advanced"><summary>高级</summary>' +
    '<label class="studio-llm-settings__label" for="studio-llm-base">自定义 API 地址（可选）</label>' +
    '<input id="studio-llm-base" class="studio-llm-settings__input" type="url" placeholder="留空则用默认地址" />' +
    "</details>" +
    '<p class="studio-llm-settings__msg" id="studio-llm-msg" hidden></p>' +
    '<div class="studio-llm-settings__actions">' +
    '<button type="button" class="studio-llm-settings__btn studio-llm-settings__btn--primary" id="studio-llm-ping">测试连接</button>' +
    '<button type="button" class="studio-llm-settings__btn" id="studio-llm-save">保存</button>' +
    '<button type="button" class="studio-llm-settings__btn studio-llm-settings__btn--danger" id="studio-llm-clear">清除配置</button>' +
    "</div>" +
    '<p class="studio-llm-settings__foot">配置后导入仍默认使用本机文案；在预览「更多工具」中点击「生成杂志感文案」才会升级。</p>' +
    "</div>";
  document.body.appendChild(el);
  if (!document.getElementById("studio-llm-settings-style")) {
    var style = document.createElement("style");
    style.id = "studio-llm-settings-style";
    style.textContent =
      ".studio-llm-settings{position:fixed;inset:0;z-index:12000;display:flex;align-items:center;justify-content:center;}" +
      ".studio-llm-settings[hidden]{display:none!important;}" +
      ".studio-llm-settings__scrim{position:absolute;inset:0;background:rgba(20,28,26,.45);}" +
      ".studio-llm-settings__panel{position:relative;z-index:1;width:min(440px,92vw);max-height:90vh;overflow:auto;" +
      "background:#f7f5f0;color:#1a2420;border-radius:12px;padding:20px 22px 18px;box-sizing:border-box;" +
      "border:1px solid #c5d0ca;}" +
      ".studio-llm-settings__head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;}" +
      ".studio-llm-settings__title{margin:0;font-size:17px;font-weight:650;}" +
      ".studio-llm-settings__desc{margin:6px 0 0;font-size:13px;color:#4a5c55;line-height:1.45;}" +
      ".studio-llm-settings__close{border:0;background:transparent;font-size:22px;line-height:1;cursor:pointer;color:#4a5c55;}" +
      ".studio-llm-settings__badge{display:inline-block;margin:12px 0 8px;padding:3px 10px;border-radius:999px;" +
      "font-size:12px;font-weight:600;background:#e8eee9;color:#2a3d35;}" +
      ".studio-llm-settings__badge.is-ready{background:#d9efe0;color:#1b5e3a;}" +
      ".studio-llm-settings__badge.is-fail{background:#fde8e6;color:#8a2b22;}" +
      ".studio-llm-settings__label{display:block;margin:10px 0 4px;font-size:12px;font-weight:600;color:#3d4f48;}" +
      ".studio-llm-settings__input{width:100%;box-sizing:border-box;padding:8px 10px;border:1px solid #b7c4bd;" +
      "border-radius:8px;font-size:14px;background:#fff;}" +
      ".studio-llm-settings__keyrow{display:flex;gap:8px;align-items:center;}" +
      ".studio-llm-settings__keyrow .studio-llm-settings__input{flex:1;}" +
      ".studio-llm-settings__linkbtn{border:0;background:transparent;color:#2f6b55;font-size:13px;cursor:pointer;white-space:nowrap;}" +
      ".studio-llm-settings__howto{margin:8px 0 0;font-size:12px;color:#4a5c55;line-height:1.5;}" +
      ".studio-llm-settings__howto a{color:#2f6b55;}" +
      ".studio-llm-settings__advanced{margin-top:10px;font-size:13px;color:#4a5c55;}" +
      ".studio-llm-settings__msg{margin:10px 0 0;font-size:13px;}" +
      ".studio-llm-settings__msg.is-ok{color:#1b5e3a;}" +
      ".studio-llm-settings__msg.is-err{color:#8a2b22;}" +
      ".studio-llm-settings__actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px;}" +
      ".studio-llm-settings__btn{border:1px solid #9aada3;background:#fff;border-radius:8px;padding:8px 12px;" +
      "font-size:13px;cursor:pointer;}" +
      ".studio-llm-settings__btn--primary{background:#2f6b55;border-color:#2f6b55;color:#fff;}" +
      ".studio-llm-settings__btn--danger{border-color:#c98a82;color:#8a2b22;}" +
      ".studio-llm-settings__foot{margin:12px 0 0;font-size:12px;color:#60756c;line-height:1.45;}" +
      ".studio-llm-settings__hint{margin:0 0 8px;font-size:11px;color:#60756c;word-break:break-all;}";
    document.head.appendChild(style);
  }
  wire(el);
  return el;
}

function setMsg(text, ok) {
  var msg = $("#studio-llm-msg");
  if (!msg) return;
  if (!text) {
    msg.hidden = true;
    msg.textContent = "";
    return;
  }
  msg.hidden = false;
  msg.textContent = text;
  msg.classList.toggle("is-ok", !!ok);
  msg.classList.toggle("is-err", !ok);
}

function setBadge(readiness) {
  var badge = $("#studio-llm-readiness");
  if (!badge) return;
  badge.textContent = readiness || "未配置";
  badge.classList.toggle("is-ready", readiness === "已就绪");
  badge.classList.toggle("is-fail", readiness === "连接失败");
}

function applyStatus(st) {
  if (!st) return;
  setBadge(st.readiness || (st.llmAvailable ? "已就绪" : "未配置"));
  var provider = st.llmProvider && st.llmProvider !== "stub" ? st.llmProvider : "deepseek";
  var sel = $("#studio-llm-provider");
  if (sel) sel.value = provider === "dashscope" ? "dashscope" : "deepseek";
  var key = $("#studio-llm-key");
  if (key && st.maskedKey && !key.value) {
    key.placeholder = "已保存 " + st.maskedKey + " · 留空则保持原 Key";
  }
  var ud = $("#studio-llm-userdata");
  if (ud && (st.userDataDir || st.tripsDir)) {
    ud.hidden = false;
    var lines = [];
    if (st.userDataDir) lines.push("配置位置：" + st.userDataDir);
    if (st.tripsDir) lines.push("相册位置：" + st.tripsDir);
    ud.textContent = lines.join("\n");
    ud.style.whiteSpace = "pre-line";
  }
  updateHowto();
}

function updateHowto() {
  var howto = $("#studio-llm-howto");
  var sel = $("#studio-llm-provider");
  if (!howto || !sel) return;
  var link =
    sel.value === "dashscope" ? LLM_KEY_LINKS.dashscope : LLM_KEY_LINKS.deepseek;
  var html =
    '获取 Key：打开 <a href="' +
    link.href +
    '" target="_blank" rel="noopener">' +
    link.label +
    "</a>，按其页面指引创建并复制，粘贴到上方后点「测试连接」。";
  if (link.guideHref) {
    html +=
      ' <a href="' +
      link.guideHref +
      '" target="_blank" rel="noopener">' +
      (link.guideLabel || "官方说明") +
      "</a>";
  }
  html +=
    ' · <button type="button" class="studio-llm-settings__linkbtn" data-llm-help-h7="1">了解更多</button>';
  howto.innerHTML = html;
}

function openHelpH7() {
  import("/__studio/js/help-drawer.js").then(function (mod) {
    if (mod && typeof mod.openHelpDrawer === "function") {
      mod.openHelpDrawer({ source: "llm_settings", itemId: "H7" });
    }
  });
}

function payloadFromForm(requireKey) {
  var provider = ($("#studio-llm-provider") || {}).value || "deepseek";
  var keyEl = $("#studio-llm-key");
  var apiKey = (keyEl && keyEl.value || "").trim();
  var base = (($("#studio-llm-base") || {}).value || "").trim();
  if (requireKey && !apiKey) {
    return null;
  }
  var body = { provider: provider };
  if (apiKey) body.apiKey = apiKey;
  if (base) body.baseUrl = base;
  return body;
}

function notifyChange(st) {
  try {
    window.dispatchEvent(new CustomEvent("travelogue:llm-status", { detail: st || {} }));
  } catch (_) {}
  if (typeof _onChange === "function") {
    try { _onChange(st); } catch (_) {}
  }
}

function wire(root) {
  root.addEventListener("click", function (ev) {
    var t = ev.target;
    if (t && t.getAttribute && t.getAttribute("data-llm-close")) {
      closeLlmSettings();
    }
  });
  document.addEventListener("keydown", function (ev) {
    if (_open && ev.key === "Escape") closeLlmSettings();
  });
  var toggle = $("#studio-llm-toggle-key", root);
  if (toggle) {
    toggle.addEventListener("click", function () {
      var key = $("#studio-llm-key", root);
      if (!key) return;
      var show = key.type === "password";
      key.type = show ? "text" : "password";
      toggle.textContent = show ? "隐藏" : "显示";
    });
  }
  var prov = $("#studio-llm-provider", root);
  if (prov) prov.addEventListener("change", updateHowto);

  var howto = $("#studio-llm-howto", root);
  if (howto && howto.dataset.helpBound !== "1") {
    howto.dataset.helpBound = "1";
    howto.addEventListener("click", function (ev) {
      var t = ev.target;
      if (t && t.getAttribute && t.getAttribute("data-llm-help-h7")) {
        ev.preventDefault();
        openHelpH7();
      }
    });
  }
  updateHowto();

  $("#studio-llm-ping", root).addEventListener("click", function () {
    var body = payloadFromForm(true);
    if (!body || !body.apiKey) {
      // Allow ping with saved key only
      body = payloadFromForm(false) || { provider: ($("#studio-llm-provider") || {}).value };
      if (!body.apiKey) {
        // still ok — server uses saved key
      }
    }
    setMsg("正在测试连接…", true);
    fetch("/__travelogue/llm/ping", {
      method: "POST",
      headers: studioAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(body),
    })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        trackStudioEvent("llm_ping", { ok: !!res.ok, provider: body.provider, source: _source });
        if (res.ok) {
          setMsg(res.j.message || "连接成功", true);
          applyStatus(res.j);
          notifyChange(res.j);
        } else {
          setMsg((res.j && res.j.message) || "连接失败", false);
          applyStatus(res.j);
        }
      })
      .catch(function () {
        setMsg("网络异常，请重试", false);
      });
  });

  $("#studio-llm-save", root).addEventListener("click", function () {
    var body = payloadFromForm(true);
    if (!body || !body.apiKey) {
      setMsg("请先粘贴 API Key", false);
      return;
    }
    fetch("/__travelogue/llm/settings", {
      method: "POST",
      headers: studioAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(body),
    })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        trackStudioEvent("llm_settings_save", { ok: !!res.ok, provider: body.provider, source: _source });
        if (res.ok) {
          setMsg("已保存。建议再点「测试连接」确认可用。", true);
          applyStatus(res.j);
          notifyChange(res.j);
          var key = $("#studio-llm-key");
          if (key) key.value = "";
        } else {
          setMsg((res.j && res.j.message) || "保存失败", false);
        }
      })
      .catch(function () {
        setMsg("保存失败，请重试", false);
      });
  });

  $("#studio-llm-clear", root).addEventListener("click", function () {
    function doClear() {
      fetch("/__travelogue/llm/settings", {
        method: "DELETE",
        headers: studioAuthHeaders({}),
      })
        .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
        .then(function (res) {
          trackStudioEvent("llm_settings_clear", { source: _source });
          if (res.ok) {
            setMsg("已清除，当前为本机文案", true);
            var key = $("#studio-llm-key");
            if (key) {
              key.value = "";
              key.placeholder = "粘贴你的 API Key";
            }
            applyStatus(res.j);
            notifyChange(res.j);
          } else {
            setMsg((res.j && res.j.message) || "清除失败", false);
          }
        })
        .catch(function () {
          setMsg("清除失败，请重试", false);
        });
    }
    var confirmOpts = {
      title: "清除写作引擎配置？",
      body: "清除后回到本机文案。已有游记不会删除。",
      confirmText: "清除",
      cancelText: "取消",
      danger: true,
      focusCancel: true,
    };
    if (typeof studioModal === "function") {
      studioModal(confirmOpts).then(function (ok) {
        if (ok) doClear();
      });
      return;
    }
    if (window.confirm("清除写作引擎配置并回到本机文案？")) doClear();
  });
}

export function openLlmSettings(opts) {
  opts = opts || {};
  _source = opts.source || "settings";
  _onChange = opts.onChange || null;
  var root = ensureRoot();
  _open = true;
  root.hidden = false;
  setMsg("", true);
  trackStudioEvent("llm_settings_open", { source: _source });
  fetch("/__travelogue/llm/status", { headers: studioAuthHeaders({}) })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (st) {
      applyStatus(st);
    })
    .catch(function () {});
  var key = $("#studio-llm-key");
  if (key) {
    try { key.focus(); } catch (_) {}
  }
}

export function closeLlmSettings() {
  var root = document.getElementById(ROOT_ID);
  if (root) root.hidden = true;
  _open = false;
}

export function initLlmSettingsEntry() {
  // Home settings: add CTA row if popover exists
  var pop = document.getElementById("v2-settings-popover");
  if (pop && !document.getElementById("studio-llm-settings-entry")) {
    var title = document.getElementById("v2-settings-title");
    if (title) title.textContent = "设置";
    var desc = document.getElementById("v2-settings-desc");
    if (desc) desc.textContent = "导入偏好与可选的 AI 文案升级";
    var sec = document.createElement("section");
    sec.className = "v2-settings-popover__section";
    sec.setAttribute("aria-label", "AI 文案");
    sec.innerHTML =
      '<p class="v2-settings-popover__section-label">AI 文案（可选）</p>' +
      '<p class="v2-advanced-popover__note">不配置也可以正常导入、排版和导出长图。配置后可在预览中生成杂志感文案。</p>' +
      '<button type="button" class="v2-settings-popover__dev-btn" id="studio-llm-settings-entry">配置写作引擎…</button>';
    var importSec = pop.querySelector('[aria-label="导入选项"]');
    if (importSec && importSec.parentNode) {
      importSec.parentNode.insertBefore(sec, importSec.nextSibling);
    } else {
      pop.appendChild(sec);
    }
    $("#studio-llm-settings-entry").addEventListener("click", function () {
      openLlmSettings({ source: "settings" });
    });
  }
  // Deep link ?llmSetup=1
  try {
    var q = new URLSearchParams(window.location.search || "");
    if (q.get("llmSetup") === "1") {
      openLlmSettings({ source: "deeplink" });
    }
  } catch (_) {}
}
