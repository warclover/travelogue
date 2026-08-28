/**
 * Frozen Studio UI terms (COPY-DICTIONARY-V1 · Sprint 0).
 * Keep in sync with travelogue/domain/copy_dictionary.py.
 */
"use strict";

export var COPY_DICTIONARY = {
  action: "导出",
  products: {
    longshot: "长图",
    card: "卡片",
    album: "画册",
  },
  intents: {
    daily_share: "日常分享",
    creator: "内容创作",
    album_preview: "画册跨页",
  },
  journalExportLabel: "长图",
  journalExportAria: "导出长图",
  portfolioExportLabel: "导出作品集",
  portfolioExportAria: "导出作品集",
  successVerb: "已导出",
  shelfReady: "长图已就绪",
  shelfStale: "长图需更新",
  forbiddenUmbrella: ["分享图"],
  forbiddenActionAlias: ["发微信群"],
  forbiddenPositionCopy: ["验货", "灰色按钮", "右上角"],
  helpSearchAliases: ["微信", "长图", "分享图", "发微信群", "验货"],
};

export function exportLabel(edition) {
  return String(edition || "").toLowerCase() === "portfolio"
    ? COPY_DICTIONARY.portfolioExportLabel
    : COPY_DICTIONARY.journalExportLabel;
}

export function exportAria(edition) {
  return String(edition || "").toLowerCase() === "portfolio"
    ? COPY_DICTIONARY.portfolioExportAria
    : COPY_DICTIONARY.journalExportAria;
}

export function purposeForPlatform(platformId) {
  var id = String(platformId || "").trim();
  if (id === "wechat_moments") return "朋友圈";
  if (id === "xiaohongshu") return "小红书";
  if (id === "wechat_official") return "公众号";
  if (id === "poster_bric") return "";
  if (id === "album_spread") return "";
  if (id === "wechat_chat") return "微信群";
  return "";
}

export function productForPlatform(platformId) {
  var id = String(platformId || "").trim();
  if (id === "poster_bric" || id === "xiaohongshu" || id === "wechat_official") {
    return COPY_DICTIONARY.products.card;
  }
  if (id === "album_spread") return COPY_DICTIONARY.products.album;
  return COPY_DICTIONARY.products.longshot;
}

export function successLine(count, purpose, product) {
  var n = Math.max(0, Number(count) || 0);
  var purposeText = String(purpose || "").trim();
  var productText = String(product || COPY_DICTIONARY.products.longshot).trim();
  if (purposeText) return COPY_DICTIONARY.successVerb + " " + n + " 张" + purposeText + productText;
  return COPY_DICTIONARY.successVerb + " " + n + " 张" + productText;
}

export function successLineForPlatform(platformId, count) {
  return successLine(
    count,
    purposeForPlatform(platformId),
    productForPlatform(platformId)
  );
}
