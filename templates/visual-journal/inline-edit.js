/**
 * Travelogue · draft 文案点击编辑（保存到 trip.json via travelogue serve）
 */
(function (global) {
  "use strict";

  var SAVE_URL = "/__travelogue/save-copy";

  function isDraft() {
    return document.documentElement.getAttribute("data-export") === "draft";
  }

  function isEditableEnabled() {
    return document.documentElement.getAttribute("data-inline-edit") === "on";
  }

  function getToast() {
    var el = document.getElementById("inline-edit-toast");
    if (!el) {
      el = document.createElement("p");
      el.id = "inline-edit-toast";
      el.className = "inline-edit-toast";
      el.setAttribute("role", "status");
      el.hidden = true;
      document.body.appendChild(el);
    }
    return el;
  }

  var toastTimer = null;

  function showToast(message, isError) {
    var el = getToast();
    el.textContent = message;
    el.classList.toggle("inline-edit-toast--error", !!isError);
    el.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
      el.hidden = true;
    }, isError ? 5000 : 2200);
  }

  function savePatch(path, value, el) {
    el.classList.add("inline-edit__field--saving");
    return fetch(SAVE_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ patches: [{ path: path, value: value }] }),
    })
      .then(function (res) {
        return res.json().then(function (body) {
          return { ok: res.ok, body: body };
        });
      })
      .then(function (result) {
        el.classList.remove("inline-edit__field--saving");
        if (result.ok && result.body && result.body.ok) {
          el.classList.add("inline-edit__field--saved");
          showToast("已保存到 trip.json");
          return;
        }
        var msg =
          (result.body && result.body.error) ||
          "保存失败，请使用 python -m travelogue serve 打开页面";
        showToast(msg, true);
      })
      .catch(function () {
        el.classList.remove("inline-edit__field--saving");
        showToast("无法保存：请运行 python -m travelogue serve trips/<id>", true);
      });
  }

  function bindField(el) {
    var path = el.getAttribute("data-edit-path");
    if (!path) return;

    el.setAttribute("tabindex", "0");
    el.setAttribute("title", "点击编辑");

    el.addEventListener("click", function (e) {
      if (el.getAttribute("contenteditable") === "true") return;
      e.preventDefault();
      el.setAttribute("contenteditable", "true");
      el.classList.add("inline-edit__field--active");
      el.focus();
      try {
        var range = document.createRange();
        range.selectNodeContents(el);
        range.collapse(false);
        var sel = global.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
      } catch (_err) {
        /* ignore */
      }
    });

    el.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        el.blur();
      }
      if (e.key === "Escape") {
        e.preventDefault();
        el.removeAttribute("contenteditable");
        el.classList.remove("inline-edit__field--active");
        el.blur();
      }
    });

    el.addEventListener("blur", function () {
      if (el.getAttribute("contenteditable") !== "true") return;
      el.removeAttribute("contenteditable");
      el.classList.remove("inline-edit__field--active");
      var next = (el.textContent || "").replace(/\s+/g, " ").trim();
      var prev = (el.getAttribute("data-edit-initial") || "").trim();
      if (next === prev) return;
      el.setAttribute("data-edit-initial", next);
      savePatch(path, next, el);
    });

    el.setAttribute("data-edit-initial", (el.textContent || "").trim());
  }

  function init() {
    if (!isDraft() || !isEditableEnabled()) return;
    var fields = document.querySelectorAll("[data-editable][data-edit-path]");
    for (var i = 0; i < fields.length; i++) {
      bindField(fields[i]);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})(window);
