/**
 * Desktop LLM Setup V1 · 写作引擎 / AI 文案设置（首页+预览共用）
 * WEA W1: 保存并测试 · 通义地域 · 四态 · 脚注
 * MF-02: 单一组件；预览内 Modal，不跳首页。
 */
import { studioAuthHeaders } from "./http.js";
import { trackStudioEvent } from "./analytics.js";

var ROOT_ID = "studio-llm-settings-root";
var _open = false;
var _source = "settings";
var _onChange = null;
var _statusCache = null;

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

/** 与后端 PROVIDER_PRESETS / DASHSCOPE_REGION 对齐 · 切换服务商时勿沿用另一家默认地址 */
var LLM_DEFAULT_BASE = {
  deepseek: "https://api.deepseek.com/v1",
  dashscope: "https://dashscope.aliyuncs.com/compatible-mode/v1",
  dashscope_intl: "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
};

var SETTINGS_ERR = {
  E_LLM_AUTH: "Key 无效或已失效。请回控制台重新创建并粘贴。",
  E_LLM_ENDPOINT: "当前地域与 Key 不匹配。请改选中国站/国际站，或检查自定义 API 地址。",
  E_LLM_MODEL: "模型不可用。请改选列表中的模型，或在高级中填写控制台可见的模型名。",
  E_LLM_QUOTA: "服务商返回余额或配额不足。请到控制台充值或检查限流。",
  E_LLM_RATE: "服务商繁忙，请稍后重试。",
  E_LLM_TIMEOUT: "无法连接服务商。请检查网络后重试。",
  E_LLM_NETWORK: "无法连接服务商。请检查网络后重试。",
  E_LLM_CONNECT: "无法连接服务商。请检查网络后重试。",
  E_LLM_BASE_URL: "自定义 API 地址仅支持 https。",
  E_LLM_PING: "连接测试失败，请检查 Key、地域或网络后重试。",
};

function normalizeBaseUrl(url) {
  return String(url || "")
    .trim()
    .replace(/\/+$/, "");
}

function allDefaultBases() {
  return Object.keys(LLM_DEFAULT_BASE).map(function (k) {
    return normalizeBaseUrl(LLM_DEFAULT_BASE[k]);
  });
}

function clearForeignBaseUrl(provider) {
  var baseEl = $("#studio-llm-base");
  if (!baseEl) return;
  var cur = normalizeBaseUrl(baseEl.value);
  if (!cur) return;
  var own = [normalizeBaseUrl(LLM_DEFAULT_BASE[provider] || "")];
  if (provider === "dashscope") {
    own.push(normalizeBaseUrl(LLM_DEFAULT_BASE.dashscope_intl));
  }
  if (own.indexOf(cur) !== -1) {
    baseEl.value = "";
    return;
  }
  var foreign = allDefaultBases().filter(function (u) {
    return own.indexOf(u) === -1;
  });
  if (foreign.indexOf(cur) !== -1) {
    baseEl.value = "";
  }
}

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
    '<div class="studio-llm-settings__region" id="studio-llm-region-wrap" hidden>' +
    '<span class="studio-llm-settings__label" id="studio-llm-region-label">地域</span>' +
    '<div class="studio-llm-settings__radios" role="radiogroup" aria-labelledby="studio-llm-region-label">' +
    '<label class="studio-llm-settings__radio"><input type="radio" name="studio-llm-region" value="cn" checked /> 中国站</label>' +
    '<label class="studio-llm-settings__radio"><input type="radio" name="studio-llm-region" value="intl" /> 国际站</label>' +
    "</div>" +
    '<p class="studio-llm-settings__region-hint" id="studio-llm-region-hint" hidden>已使用自定义 API 地址，地域预设不生效。</p>' +
    "</div>" +
    '<label class="studio-llm-settings__label" for="studio-llm-key">API Key</label>' +
    '<div class="studio-llm-settings__keyrow">' +
    '<input id="studio-llm-key" class="studio-llm-settings__input" type="password" autocomplete="off" placeholder="粘贴你的 API Key" />' +
    '<button type="button" class="studio-llm-settings__linkbtn" id="studio-llm-toggle-key">显示</button>' +
    "</div>" +
    '<p class="studio-llm-settings__howto" id="studio-llm-howto"></p>' +
    '<details class="studio-llm-settings__advanced"><summary>高级</summary>' +
    '<label class="studio-llm-settings__label" for="studio-llm-base">自定义 API 地址（可选）</label>' +
    '<input id="studio-llm-base" class="studio-llm-settings__input" type="url" placeholder="留空则用默认地址（仅 https）" />' +
    "</details>" +
    '<p class="studio-llm-settings__msg" id="studio-llm-msg" hidden></p>' +
    '<div class="studio-llm-settings__actions">' +
    '<button type="button" class="studio-llm-settings__btn studio-llm-settings__btn--primary" id="studio-llm-save-ping">保存并测试</button>' +
    '<button type="button" class="studio-llm-settings__btn studio-llm-settings__btn--danger" id="studio-llm-clear">清除配置</button>' +
    "</div>" +
    '<p class="studio-llm-settings__secondary">' +
    '<button type="button" class="studio-llm-settings__linkbtn" id="studio-llm-ping">仅测试连接</button>' +
    "</p>" +
    '<div class="studio-llm-settings__resume" id="studio-llm-resume" hidden>' +
    '<p class="studio-llm-settings__resume-note" id="studio-llm-resume-note"></p>' +
    '<button type="button" class="studio-llm-settings__btn studio-llm-settings__btn--primary" id="studio-llm-resume-cta"></button>' +
    "</div>" +
    '<p class="studio-llm-settings__foot" id="studio-llm-foot">' +
    "API Key 只保存在你的电脑。调用写作引擎时，请求发往你选择的服务商，费用由该账户结算。导入与长图默认不依赖此项配置。" +
    "</p>" +
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
      ".studio-llm-settings__badge.is-warn{background:#f3ecd8;color:#6a5520;}" +
      ".studio-llm-settings__label{display:block;margin:10px 0 4px;font-size:12px;font-weight:600;color:#3d4f48;}" +
      ".studio-llm-settings__input{width:100%;box-sizing:border-box;padding:8px 10px;border:1px solid #b7c4bd;" +
      "border-radius:8px;font-size:14px;background:#fff;}" +
      ".studio-llm-settings__keyrow{display:flex;gap:8px;align-items:center;}" +
      ".studio-llm-settings__keyrow .studio-llm-settings__input{flex:1;}" +
      ".studio-llm-settings__linkbtn{border:0;background:transparent;color:#2f6b55;font-size:13px;cursor:pointer;white-space:nowrap;}" +
      ".studio-llm-settings__region{margin-top:4px;}" +
      ".studio-llm-settings__region[hidden]{display:none!important;}" +
      ".studio-llm-settings__radios{display:flex;gap:14px;flex-wrap:wrap;margin-top:4px;}" +
      ".studio-llm-settings__radio{font-size:13px;color:#2a3d35;display:flex;align-items:center;gap:6px;cursor:pointer;}" +
      ".studio-llm-settings__region-hint{margin:6px 0 0;font-size:11px;color:#6a5520;}" +
      ".studio-llm-settings__howto{margin:8px 0 0;font-size:12px;color:#4a5c55;line-height:1.5;}" +
      ".studio-llm-settings__howto a{color:#2f6b55;}" +
      ".studio-llm-settings__advanced{margin-top:10px;font-size:13px;color:#4a5c55;}" +
      ".studio-llm-settings__msg{margin:10px 0 0;font-size:13px;}" +
      ".studio-llm-settings__msg.is-ok{color:#1b5e3a;}" +
      ".studio-llm-settings__msg.is-err{color:#8a2b22;}" +
      ".studio-llm-settings__actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px;}" +
      ".studio-llm-settings__secondary{margin:8px 0 0;}" +
      ".studio-llm-settings__btn{border:1px solid #9aada3;background:#fff;border-radius:8px;padding:8px 12px;" +
      "font-size:13px;cursor:pointer;}" +
      ".studio-llm-settings__btn--primary{background:#2f6b55;border-color:#2f6b55;color:#fff;}" +
      ".studio-llm-settings__btn--danger{border-color:#c98a82;color:#8a2b22;}" +
      ".studio-llm-settings__btn:disabled{opacity:.55;cursor:not-allowed;}" +
      ".studio-llm-settings__resume{margin-top:14px;padding-top:12px;border-top:1px solid #d5ddd8;}" +
      ".studio-llm-settings__resume[hidden]{display:none!important;}" +
      ".studio-llm-settings__resume-note{margin:0 0 10px;font-size:12px;color:#4a5c55;line-height:1.45;}" +
      ".studio-llm-settings__resume .studio-llm-settings__btn{width:100%;}" +
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
  var r = readiness || "未配置";
  badge.textContent = r;
  badge.classList.toggle("is-ready", r === "已就绪");
  badge.classList.toggle("is-fail", r === "连接失败");
  badge.classList.toggle("is-warn", r === "已保存未验证" || r === "未配置");
}

function selectedRegion() {
  var checked = document.querySelector('input[name="studio-llm-region"]:checked');
  return checked && checked.value === "intl" ? "intl" : "cn";
}

function setRegion(region) {
  var want = region === "intl" ? "intl" : "cn";
  var radios = document.querySelectorAll('input[name="studio-llm-region"]');
  for (var i = 0; i < radios.length; i++) {
    radios[i].checked = radios[i].value === want;
  }
}

function syncRegionVisibility() {
  var wrap = $("#studio-llm-region-wrap");
  var hint = $("#studio-llm-region-hint");
  var sel = $("#studio-llm-provider");
  var base = normalizeBaseUrl(($("#studio-llm-base") || {}).value || "");
  if (!wrap || !sel) return;
  var isDash = sel.value === "dashscope";
  wrap.hidden = !isDash;
  var custom =
    !!base &&
    allDefaultBases().indexOf(base) === -1;
  if (hint) hint.hidden = !(isDash && custom);
}

function errMessage(j) {
  if (!j) return "连接失败";
  var code = j.error || j.code;
  if (code && SETTINGS_ERR[code]) return SETTINGS_ERR[code];
  return j.message || "连接失败";
}

function applyStatus(st) {
  if (!st) return;
  _statusCache = st;
  setBadge(st.readiness || (st.llmAvailable ? "已就绪" : "未配置"));
  var provider = st.llmProvider && st.llmProvider !== "stub" ? st.llmProvider : "deepseek";
  if (st.configured && st.llmProvider) {
    provider = st.llmProvider === "dashscope" ? "dashscope" : "deepseek";
  }
  var sel = $("#studio-llm-provider");
  if (sel) sel.value = provider === "dashscope" ? "dashscope" : "deepseek";
  if (st.region) setRegion(st.region);
  else if (provider === "dashscope") setRegion("cn");
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
  syncRegionVisibility();
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
    "</a>，按其页面指引创建并复制，粘贴到上方后点「保存并测试」。";
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
  clearForeignBaseUrl(provider);
  var keyEl = $("#studio-llm-key");
  var apiKey = ((keyEl && keyEl.value) || "").trim();
  var base = normalizeBaseUrl(($("#studio-llm-base") || {}).value || "");
  if (
    requireKey &&
    !apiKey &&
    !(
      _statusCache &&
      _statusCache.configured &&
      _statusCache.llmProvider === provider
    )
  ) {
    return null;
  }
  var body = { provider: provider };
  if (apiKey) body.apiKey = apiKey;
  if (provider === "dashscope") {
    body.region = selectedRegion();
  }
  var ownDefaults = [normalizeBaseUrl(LLM_DEFAULT_BASE[provider] || "")];
  if (provider === "dashscope") {
    ownDefaults.push(normalizeBaseUrl(LLM_DEFAULT_BASE.dashscope_intl));
  }
  if (base && ownDefaults.indexOf(base) === -1) {
    var foreign = allDefaultBases().filter(function (u) {
      return ownDefaults.indexOf(u) === -1;
    });
    if (foreign.indexOf(base) === -1) {
      body.baseUrl = base;
    }
  }
  return body;
}

function notifyChange(st) {
  try {
    window.dispatchEvent(new CustomEvent("travelogue:llm-status", { detail: st || {} }));
  } catch (_) {}
  if (typeof _onChange === "function") {
    try {
      _onChange(st);
    } catch (_) {}
  }
}

function hideResumePanel() {
  var box = document.getElementById("studio-llm-resume");
  if (box) box.hidden = true;
}

function resumeKindForSource(source) {
  if (source === "import_fail") return "continue_stub";
  if (source === "card" || source === "home_banner") return "start_import";
  return null;
}

function showResumeAfterSave(source) {
  var kind = resumeKindForSource(source);
  var box = document.getElementById("studio-llm-resume");
  var note = document.getElementById("studio-llm-resume-note");
  var cta = document.getElementById("studio-llm-resume-cta");
  if (!box || !note || !cta || !kind) {
    hideResumePanel();
    return;
  }
  if (kind === "continue_stub") {
    note.textContent =
      "API 用于预览里升级杂志感文案，不会在本步自动改写导入文案。请继续生成本机游记，稍后在预览中升级。";
    cta.textContent = "继续生成本机游记";
  } else {
    note.textContent =
      "已保存。导入仍使用本机文案；杂志感可在预览中升级。下一步：开始导入照片。";
    cta.textContent = "开始导入";
  }
  box.hidden = false;
  cta.dataset.resumeKind = kind;
  try {
    cta.focus();
  } catch (_) {}
}

function runResumeAfterLlmSettings() {
  var cta = document.getElementById("studio-llm-resume-cta");
  var kind = (cta && cta.dataset.resumeKind) || resumeKindForSource(_source);
  trackStudioEvent("llm_settings_resume", { source: _source, kind: kind || "none" });
  closeLlmSettings();
  if (kind === "continue_stub") {
    import("/__studio/homepage-v2/import-failed.js").then(function (mod) {
      if (mod && typeof mod.continueWithStub === "function") mod.continueWithStub();
    });
    return;
  }
  if (kind === "start_import") {
    import("/__studio/homepage-v2/import-entry.js").then(function (mod) {
      if (mod && typeof mod.openImportSheet === "function") {
        mod.openImportSheet();
      } else {
        var homeCta = document.getElementById("v2-cta");
        if (homeCta) homeCta.click();
      }
    });
  }
}

function setBusy(busy) {
  var ids = ["studio-llm-save-ping", "studio-llm-ping", "studio-llm-clear"];
  ids.forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.disabled = !!busy;
  });
}

function runPing(body) {
  return fetch("/__travelogue/llm/ping", {
    method: "POST",
    headers: studioAuthHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  }).then(function (r) {
    return r.json().then(function (j) {
      return { ok: r.ok, j: j };
    });
  });
}

function runSave(body) {
  return fetch("/__travelogue/llm/settings", {
    method: "POST",
    headers: studioAuthHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  }).then(function (r) {
    return r.json().then(function (j) {
      return { ok: r.ok, j: j };
    });
  });
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
  if (prov) {
    prov.addEventListener("change", function () {
      clearForeignBaseUrl(prov.value);
      syncRegionVisibility();
      updateHowto();
      setMsg("", true);
    });
  }
  var baseEl = $("#studio-llm-base", root);
  if (baseEl) {
    baseEl.addEventListener("input", syncRegionVisibility);
  }
  var regionWrap = $("#studio-llm-region-wrap", root);
  if (regionWrap) {
    regionWrap.addEventListener("change", function () {
      setMsg("", true);
    });
  }

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
    var body = payloadFromForm(false) || {
      provider: ($("#studio-llm-provider") || {}).value || "deepseek",
    };
    if (body.provider === "dashscope" && !body.region) {
      body.region = selectedRegion();
    }
    setBusy(true);
    setMsg("正在测试连接…", true);
    runPing(body)
      .then(function (res) {
        trackStudioEvent("llm_ping", { ok: !!res.ok, provider: body.provider, source: _source });
        if (res.ok) {
          setMsg(res.j.message || "已连通", true);
          applyStatus(res.j);
          notifyChange(res.j);
        } else {
          setMsg(errMessage(res.j), false);
          applyStatus(res.j);
          notifyChange(res.j);
        }
      })
      .catch(function () {
        setMsg("网络异常，请重试", false);
      })
      .then(function () {
        setBusy(false);
      });
  });

  $("#studio-llm-save-ping", root).addEventListener("click", function () {
    var body = payloadFromForm(true);
    if (!body) {
      setMsg("请先粘贴 API Key", false);
      return;
    }
    if (!body.apiKey && !(_statusCache && _statusCache.configured)) {
      setMsg("请先粘贴 API Key", false);
      return;
    }
    setBusy(true);
    setMsg("正在保存并测试…", true);
    runSave(body)
      .then(function (saveRes) {
        trackStudioEvent("llm_settings_save", {
          ok: !!saveRes.ok,
          provider: body.provider,
          source: _source,
        });
        if (!saveRes.ok) {
          setMsg(errMessage(saveRes.j) || "保存失败", false);
          return null;
        }
        applyStatus(saveRes.j);
        var key = $("#studio-llm-key");
        if (key) key.value = "";
        // 保存后用已落盘 Key 再 ping（不带明文 Key）
        var pingBody = {
          provider: body.provider,
        };
        if (body.region) pingBody.region = body.region;
        if (body.baseUrl) pingBody.baseUrl = body.baseUrl;
        return runPing(pingBody).then(function (pingRes) {
          trackStudioEvent("llm_ping", {
            ok: !!pingRes.ok,
            provider: body.provider,
            source: _source,
            via: "save_and_ping",
          });
          if (pingRes.ok) {
            setMsg(pingRes.j.message || "已就绪", true);
            applyStatus(pingRes.j);
            notifyChange(pingRes.j);
            showResumeAfterSave(_source);
          } else {
            setMsg(errMessage(pingRes.j), false);
            applyStatus(pingRes.j);
            notifyChange(pingRes.j);
          }
        });
      })
      .catch(function () {
        setMsg("保存或测试失败，请重试", false);
      })
      .then(function () {
        setBusy(false);
      });
  });

  $("#studio-llm-clear", root).addEventListener("click", function () {
    function doClear() {
      fetch("/__travelogue/llm/settings", {
        method: "DELETE",
        headers: studioAuthHeaders({}),
      })
        .then(function (r) {
          return r.json().then(function (j) {
            return { ok: r.ok, j: j };
          });
        })
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

  var resumeCta = $("#studio-llm-resume-cta", root);
  if (resumeCta) {
    resumeCta.addEventListener("click", function () {
      runResumeAfterLlmSettings();
    });
  }
}

export function openLlmSettings(opts) {
  opts = opts || {};
  _source = opts.source || "settings";
  _onChange = opts.onChange || null;
  var root = ensureRoot();
  _open = true;
  root.hidden = false;
  setMsg("", true);
  hideResumePanel();
  trackStudioEvent("llm_settings_open", { source: _source });
  fetch("/__travelogue/llm/status", { headers: studioAuthHeaders({}) })
    .then(function (r) {
      return r.ok ? r.json() : null;
    })
    .then(function (st) {
      applyStatus(st);
    })
    .catch(function () {});
  var key = $("#studio-llm-key");
  if (key) {
    try {
      key.focus();
    } catch (_) {}
  }
}

export function closeLlmSettings() {
  var root = document.getElementById(ROOT_ID);
  if (root) root.hidden = true;
  _open = false;
}

export function initLlmSettingsEntry() {
  // Home settings: 静态 AI zone CTA（手风琴）；不再动态注入 section
  var entry = document.getElementById("studio-llm-settings-entry");
  if (entry && entry.dataset.llmBound !== "1") {
    entry.dataset.llmBound = "1";
    entry.addEventListener("click", function () {
      openLlmSettings({ source: "settings" });
    });
  }
  var helpBtn = document.getElementById("studio-llm-settings-help");
  if (helpBtn && helpBtn.dataset.llmHelpBound !== "1") {
    helpBtn.dataset.llmHelpBound = "1";
    helpBtn.addEventListener("click", function (ev) {
      ev.preventDefault();
      openHelpH7();
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
