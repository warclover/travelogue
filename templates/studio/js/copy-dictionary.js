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
