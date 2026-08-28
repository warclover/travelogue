/**
 * EXP-01 · journal 导出三意图（EPF 最小面）。
 * edition !== journal 时调用方不得挂载。
 */
"use strict";

export var EXPORT_INTENTS = [
  {
    id: "daily_share",
    label: "日常分享",
    sub: "发群聊或朋友圈，手机直接查看。",
    platforms: ["wechat_chat", "wechat_moments"],
    defaultPlatform: "wechat_chat",
  },
  {
    id: "creator",
    label: "内容创作",
    sub: "做海报、小红书或公众号配图。",
    platforms: ["poster_bric", "xiaohongshu", "wechat_official"],
    defaultPlatform: "poster_bric",
  },
  {
    id: "album_preview",
    label: "画册跨页",
    sub: "留下可预览或送印的跨页。",
    platforms: ["album_spread"],
    defaultPlatform: "album_spread",
  },
];

export function intentForPlatform(platformId) {
  var id = String(platformId || "").trim();
  for (var i = 0; i < EXPORT_INTENTS.length; i++) {
    if (EXPORT_INTENTS[i].platforms.indexOf(id) >= 0) return EXPORT_INTENTS[i];
  }
  return EXPORT_INTENTS[0];
}

export function defaultPlatformForIntent(intentId) {
  for (var i = 0; i < EXPORT_INTENTS.length; i++) {
    if (EXPORT_INTENTS[i].id === intentId) return EXPORT_INTENTS[i].defaultPlatform;
  }
  return "wechat_chat";
}

export function buildIntentPresetHtml() {
  return (
    '<div class="preview-toolbar__export-intent-grid" role="radiogroup" aria-label="导出用途">' +
    EXPORT_INTENTS.map(function (intent) {
      return (
        '<button type="button" class="preview-toolbar__export-intent-card" data-export-intent="' +
        intent.id +
        '" role="radio" aria-checked="false">' +
        '<span class="preview-toolbar__export-intent-card__title">' +
        intent.label +
        "</span>" +
        '<span class="preview-toolbar__export-intent-card__sub">' +
        intent.sub +
        "</span></button>"
      );
    }).join("") +
    "</div>"
  );
}
