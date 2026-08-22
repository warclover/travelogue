/**
 * PFM · 精修成册类型 / 书架弱标纯函数（FE-PFM-07 / 08 / 11）。
 * 用户可见文案不得出现 edition / PFM / page-*（AC-PFM-23）。
 */
"use strict";

import { isPortfolioEdition, overflowJournalCta } from "./portfolio-export-logic.js";

export { overflowJournalCta };

export var EDITION_COPY_LOCK = "你手动改过的文字可能无法全部保留。";
export var PORTFOLIO_FLAG_OFF_TEXT = "作品集编排暂时关闭 · 这一本仍可翻阅";
export var PORTFOLIO_FLAG_OFF_CTA = "改为游记重排";

/** 关旗后打开存量作品集：横幅 + 可改回游记（AC-PFM-07 后半）。 */
export function shouldShowPortfolioFlagOffBanner(edition, pipelineEnabled) {
  return isPortfolioEdition(edition) && pipelineEnabled === false;
}

/** 关旗时游记不露成册类型；存量作品集仍露，以便改回。 */
export function shouldMountEditionType(edition, pipelineEnabled) {
  if (pipelineEnabled === true) return true;
  return isPortfolioEdition(edition);
}

export function editionCardOptionsForPipeline(pipelineEnabled) {
  var all = editionCardOptions();
  if (pipelineEnabled === true) return all;
  return all.filter(function (opt) {
    return opt.id === "journal";
  });
}

export function portfolioFlagOffBannerCopy() {
  return { text: PORTFOLIO_FLAG_OFF_TEXT, cta: PORTFOLIO_FLAG_OFF_CTA };
}

/** FE-PFM-15 · WAI-ARIA radio 方向键（水平/垂直同一套）。 */
export function isRadioNavKey(key) {
  return (
    key === "ArrowLeft" ||
    key === "ArrowRight" ||
    key === "ArrowUp" ||
    key === "ArrowDown" ||
    key === "Home" ||
    key === "End"
  );
}

export function nextRadioId(ids, current, key) {
  var list = Array.isArray(ids) ? ids.filter(Boolean) : [];
  if (!list.length) return current || "";
  if (key === "Home") return list[0];
  if (key === "End") return list[list.length - 1];
  var i = list.indexOf(current);
  if (i < 0) i = 0;
  if (key === "ArrowLeft" || key === "ArrowUp") {
    return list[i <= 0 ? list.length - 1 : i - 1];
  }
  if (key === "ArrowRight" || key === "ArrowDown") {
    return list[i >= list.length - 1 ? 0 : i + 1];
  }
  return current || list[0];
}

export function radioTabIndex(selectedId, optionId) {
  return selectedId === optionId ? 0 : -1;
}

export function normalizeEdition(raw) {
  return isPortfolioEdition(raw) ? "portfolio" : "journal";
}

/**
 * @param {string} from
 * @param {string} to
 */
export function editionSwitchConfirm(from, to) {
  var next = normalizeEdition(to);
  var toPortfolio = next === "portfolio";
  var body =
    "精选和分组会保留，页面将按另一套版式重排。" + EDITION_COPY_LOCK;
  if (toPortfolio) {
    body += "页数可能变少，照片可能收录不全；发群请改用「换种分享」。";
  }
  return {
    title: toPortfolio ? "改成「作品集」？" : "改回「游记」？",
    body: body,
    confirmText: "重排页面",
    cancelText: "取消",
  };
}

/**
 * 作品集票面弱标。游记返回空串，避免每张都写「游记」。
 * @param {{ edition?: string, pageCount?: number }|null} trip
 */
export function shelfEditionLine(trip) {
  if (!trip || !isPortfolioEdition(trip.edition)) return "";
  var n = Number(trip.pageCount);
  if (n > 0) return "作品集 · " + n + " 页";
  return "作品集";
}

export function editionCardOptions() {
  return [
    {
      id: "journal",
      label: "游记",
      consequence: "卷轴 + 长图，适合发群",
    },
    {
      id: "portfolio",
      label: "作品集",
      consequence: "杂志页 + 可翻阅的一本",
    },
  ];
}

/** 无目录投影时只出「自动」；数字档必须由现网系列库投影。 */
export var PAGE_COUNT_CHIPS = [];
export var THIN_TIER_RATIO = 0.6;

export function chipCapacity(entry) {
  if (entry && typeof entry === "object") {
    var cap = Number(entry.capacity);
    return cap > 0 ? cap : 0;
  }
  return 0;
}

export function chipPages(entry) {
  if (entry && typeof entry === "object") {
    return Number(entry.pages || entry.pageCount || 0);
  }
  return Number(entry);
}

export function pageCountChipHint(pages, capacity) {
  var n = Number(pages);
  var cap = Number(capacity);
  if (!(n > 0)) return "";
  if (!(cap > 0)) return String(n);
  return n + " 页 · 约 " + cap + " 张";
}

export function normalizeChipDetails(chips) {
  var raw = Array.isArray(chips) ? chips : PAGE_COUNT_CHIPS;
  var out = [];
  raw.forEach(function (entry) {
    var pages = chipPages(entry);
    if (!(pages > 0)) return;
    out.push({ pages: pages, capacity: chipCapacity(entry) });
  });
  return out;
}

export function pageCountChipOptions(chips) {
  var list = normalizeChipDetails(chips);
  return [{ id: "auto", label: "自动", hint: "", capacity: 0 }].concat(
    list.map(function (row) {
      return {
        id: String(row.pages),
        label: String(row.pages),
        hint: pageCountChipHint(row.pages, row.capacity),
        capacity: row.capacity,
      };
    })
  );
}

export function recommendPageCount(chips, kept) {
  var list = normalizeChipDetails(chips).filter(function (row) {
    return row.capacity > 0;
  });
  var n = Number(kept);
  if (!list.length || !(n > 0)) return 0;
  var windowHits = list.filter(function (row) {
    var ratio = n / row.capacity;
    return ratio >= 0.85 && ratio <= 1.05;
  });
  if (windowHits.length) {
    return windowHits.reduce(function (a, b) {
      return a.pages <= b.pages ? a : b;
    }).pages;
  }
  var under = list.filter(function (row) {
    return row.capacity >= n;
  });
  if (under.length) {
    return under.reduce(function (a, b) {
      return a.capacity <= b.capacity ? a : b;
    }).pages;
  }
  return list.reduce(function (a, b) {
    return a.pages >= b.pages ? a : b;
  }).pages;
}

export function shouldConfirmThinTier(capacity, kept) {
  var cap = Number(capacity);
  var n = Number(kept);
  return cap > 0 && n > 0 && cap < n * THIN_TIER_RATIO;
}

export function thinTierConfirm(capacity, kept, recommendPages) {
  var rec = Number(recommendPages);
  var body =
    "这一档只收 " +
    Number(capacity) +
    " 张，你有 " +
    Number(kept) +
    " 张。";
  if (rec > 0) body += "要更厚的一本吗？";
  return {
    title: "这一档会少收很多照片",
    body: body,
    confirmText: rec > 0 ? "改用 " + rec + " 页" : "仍用这一档",
    cancelText: rec > 0 ? "仍用这一档" : "取消",
    recommendPages: rec > 0 ? rec : 0,
  };
}

/**
 * Fill the page-count chip row (FE-DPI-03). features.js keeps the card shell.
 * @param {HTMLElement|null} pageHost
 * @param {HTMLElement|null} pageRow
 * @param {HTMLElement|null} pageHint
 * @param {object|null|undefined} portfolio
 * @param {{ selectedId?: string, onRequest?: function(string, object): void }} [handlers]
 * @returns {string} selected chip id
 */
export function renderPortfolioPageCountChips(pageHost, pageRow, pageHint, portfolio, handlers) {
  handlers = handlers || {};
  var onRequest = handlers.onRequest;
  if (!pageHost || !pageRow) return "auto";
  pageHost.hidden = false;
  var chips =
    (portfolio && (portfolio.pageCountChipDetails || portfolio.pageCountChips)) || [];
  pageRow.innerHTML = "";
  pageCountChipOptions(chips).forEach(function (opt) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "preview-sheet__chip";
    btn.setAttribute("data-page-count", opt.id);
    btn.setAttribute("role", "radio");
    btn.setAttribute("aria-label", opt.hint || opt.label);
    btn.innerHTML =
      '<span class="preview-sheet__chip-label">' +
      opt.label +
      "</span>" +
      (opt.hint
        ? '<span class="preview-sheet__chip-hint">' + opt.hint + "</span>"
        : "");
    btn.addEventListener("click", function () {
      if (typeof onRequest === "function") onRequest(opt.id, opt);
    });
    btn.addEventListener("keydown", function (e) {
      if (!isRadioNavKey(e.key)) return;
      e.preventDefault();
      var ids = pageCountChipOptions(chips).map(function (o) {
        return o.id;
      });
      var current = handlers.selectedId || selectedPageCountChip(portfolio);
      var next = nextRadioId(ids, current, e.key);
      if (!next || next === current) return;
      var hit = pageCountChipOptions(chips).filter(function (o) {
        return o.id === next;
      })[0];
      if (typeof onRequest === "function") onRequest(next, hit || { id: next });
    });
    pageRow.appendChild(btn);
  });
  var selected = handlers.selectedId || selectedPageCountChip(portfolio);
  pageRow.querySelectorAll("[data-page-count]").forEach(function (btn) {
    var on = btn.getAttribute("data-page-count") === selected;
    btn.classList.toggle("is-on", on);
    btn.setAttribute("aria-pressed", on ? "true" : "false");
  });
  var hint = portfolio && portfolio.pageCountHint;
  if (pageHint) {
    pageHint.hidden = !hint;
    pageHint.textContent = hint || "";
  }
  return selected;
}

/** @param {{ pageCountSource?: string, pageCount?: number, pageCountRequested?: number }} portfolio */
export function selectedPageCountChip(portfolio) {
  if (!portfolio || String(portfolio.pageCountSource || "auto") !== "user") {
    return "auto";
  }
  var requested = Number(portfolio.pageCountRequested);
  if (requested > 0) return String(requested);
  var used = Number(portfolio.pageCount);
  if (used > 0) return String(used);
  return "auto";
}

