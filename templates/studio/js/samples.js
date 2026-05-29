/**
 * Travelogue Studio · sample longshot cards + preview modal.
 */
import { SAMPLE_LONGSHOTS, LS } from "./constants.js";
import { $, show } from "./dom.js";
import { openImportSheet } from "./sheet.js";

function _pad2(n) { return (n < 10 ? "0" : "") + n; }

export function buildSampleThumb(key) {
  var s = SAMPLE_LONGSHOTS[key];
  if (!s) return "";
  if (s.thumbSrc) {
    return (
      '<img src="' + s.thumbSrc + '" alt="' + s.title + ' 长图样张" ' +
      'loading="lazy" decoding="async" class="studio-longshot-card__img"/>'
    );
  }
  return buildSampleSVG(key, "thumb");
}

export function buildSampleFull(key) {
  var s = SAMPLE_LONGSHOTS[key];
  if (!s) return "";
  if (s.fullSrc) {
    return (
      '<img src="' + s.fullSrc + '" alt="' + s.title + ' 长图样张" ' +
      'class="studio-sample-modal__longshot" decoding="async"/>'
    );
  }
  return buildSampleSVG(key, "full");
}

// Build inline SVG that mimics a printed long screenshot page (fallback).
export function buildSampleSVG(key, mode) {
  var s = SAMPLE_LONGSHOTS[key];
  if (!s) return "";
  var W = 300;
  var H = mode === "full" ? 1320 : 440;
  var ink = s.ink, paper = s.paper, colors = s.colors;
  var parts = [];
  parts.push(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + W + ' ' + H + '" ' +
    'preserveAspectRatio="xMidYMid slice" role="img" aria-label="' + s.title + ' 长图样张">'
  );
  parts.push(
    '<defs><linearGradient id="sh-' + key + '" x1="0" y1="0" x2="0" y2="1">' +
    '<stop offset="0" stop-color="#000" stop-opacity="0"/>' +
    '<stop offset="1" stop-color="#000" stop-opacity=".35"/>' +
    '</linearGradient></defs>'
  );
  parts.push('<rect width="' + W + '" height="' + H + '" fill="' + paper + '"/>');

  var y = mode === "full" ? 58 : 28;
  parts.push(
    '<text x="' + (W / 2) + '" y="' + y + '" text-anchor="middle" ' +
    'font-family="Georgia,Songti SC,serif" font-size="' + (mode === "full" ? 22 : 14) + '" ' +
    'fill="' + ink + '">' + s.title + '</text>'
  );
  y += mode === "full" ? 18 : 11;
  parts.push(
    '<text x="' + (W / 2) + '" y="' + y + '" text-anchor="middle" ' +
    'font-family="Segoe UI,PingFang SC,sans-serif" font-size="' + (mode === "full" ? 9 : 6) + '" ' +
    'fill="' + ink + '" opacity=".55">' + s.meta + '</text>'
  );
  y += mode === "full" ? 32 : 16;

  var chapterCount = s.chapters.length;
  var photoH = mode === "full" ? 210 : 60;
  var textRows = mode === "full" ? 4 : 2;
  var rowH = mode === "full" ? 7 : 3;
  var bottomPad = mode === "full" ? 24 : 8;

  for (var i = 0; i < chapterCount; i++) {
    if (y + photoH + textRows * (rowH + 4) + 30 > H) break;
    parts.push(
      '<text x="32" y="' + y + '" font-family="Segoe UI,sans-serif" ' +
      'font-size="' + (mode === "full" ? 9 : 5.5) + '" fill="' + ink + '" ' +
      'opacity=".5" letter-spacing="2">CHAPTER ' + _pad2(i + 1) + '</text>'
    );
    y += mode === "full" ? 14 : 8;
    parts.push(
      '<text x="32" y="' + y + '" font-family="Georgia,Songti SC,serif" ' +
      'font-size="' + (mode === "full" ? 14 : 7.5) + '" font-weight="600" fill="' + ink + '">' +
      s.chapters[i] + '</text>'
    );
    y += mode === "full" ? 14 : 7;
    var color = colors[i % colors.length];
    parts.push(
      '<rect x="32" y="' + y + '" width="' + (W - 64) + '" height="' + photoH + '" ' +
      'rx="3" fill="' + color + '"/>' +
      '<rect x="32" y="' + y + '" width="' + (W - 64) + '" height="' + photoH + '" ' +
      'rx="3" fill="url(#sh-' + key + ')"/>'
    );
    y += photoH + (mode === "full" ? 14 : 7);
    for (var r = 0; r < textRows; r++) {
      var w = (W - 64) * (r === textRows - 1 ? 0.5 : 0.92);
      parts.push(
        '<rect x="32" y="' + y + '" width="' + w + '" height="' + rowH + '" ' +
        'rx="1" fill="' + ink + '" opacity=".5"/>'
      );
      y += rowH + (mode === "full" ? 8 : 4);
    }
    y += bottomPad;
  }
  if (mode === "full") {
    parts.push(
      '<text x="' + (W / 2) + '" y="' + (H - 40) + '" text-anchor="middle" ' +
      'font-family="Georgia,serif" font-size="11" fill="' + ink + '" opacity=".4" letter-spacing="6">— end —</text>'
    );
  }
  parts.push('</svg>');
  return parts.join("");
}

export function renderSampleCards() {
  var container = $("studio-samples");
  if (!container) return;
  container.innerHTML = "";
  Object.keys(SAMPLE_LONGSHOTS).forEach(function (key) {
    var s = SAMPLE_LONGSHOTS[key];
    var card = document.createElement("article");
    card.className = "studio-longshot-card";
    card.setAttribute("data-sample", key);
    card.setAttribute("tabindex", "0");
    card.setAttribute("role", "button");
    card.setAttribute("aria-label", s.title + " 长图样张");
    var paper = document.createElement("div");
    paper.className = "studio-longshot-card__paper";
    paper.innerHTML = buildSampleThumb(key);
    card.appendChild(paper);
    var meta = document.createElement("div");
    meta.className = "studio-longshot-card__meta";
    var h = document.createElement("h3"); h.textContent = s.title;
    var p = document.createElement("p"); p.textContent = s.meta;
    meta.appendChild(h); meta.appendChild(p);
    card.appendChild(meta);
    container.appendChild(card);
  });
}

// ── Sample longshot modal ──
export function initSampleModal() {
  var modal = $("studio-sample-modal");
  var pages = $("studio-sample-pages");
  var titleEl = $("studio-sample-title");
  var cta = $("studio-sample-cta");
  if (!modal || !pages || !titleEl) return;

  function open(key) {
    var sample = SAMPLE_LONGSHOTS[key];
    if (!sample) return;
    titleEl.textContent = sample.title;
    pages.innerHTML = buildSampleFull(key);
    show(modal, true);
    document.body.style.overflow = "hidden";
    var sc = document.querySelector(".studio-sample-modal__scroll");
    if (sc) sc.scrollTop = 0;
  }
  function close() {
    show(modal, false);
    document.body.style.overflow = "";
  }

  var samplesHost = $("studio-samples");
  if (samplesHost) {
    samplesHost.addEventListener("click", function (e) {
      var card = e.target.closest(".studio-longshot-card");
      if (card) open(card.getAttribute("data-sample"));
    });
    samplesHost.addEventListener("keydown", function (e) {
      if (e.key !== "Enter" && e.key !== " ") return;
      var card = e.target.closest(".studio-longshot-card");
      if (card) { e.preventDefault(); open(card.getAttribute("data-sample")); }
    });
  }
  modal.querySelectorAll("[data-close]").forEach(function (el) {
    el.addEventListener("click", close);
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !modal.hidden) close();
  });
  if (cta) cta.addEventListener("click", function () {
    close();
    openImportSheet();
    localStorage.setItem(LS.demoTried, "1");
  });
}
