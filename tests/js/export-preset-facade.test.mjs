import test from "node:test";
import assert from "node:assert/strict";
import {
  EXPORT_INTENTS,
  buildIntentPresetHtml,
  defaultPlatformForIntent,
  intentForPlatform,
} from "../../templates/studio/js/export-preset-facade.js";

test("journal intents cover daily / creator / album", () => {
  assert.equal(EXPORT_INTENTS.length, 3);
  assert.equal(intentForPlatform("wechat_moments").id, "daily_share");
  assert.equal(intentForPlatform("xiaohongshu").id, "creator");
  assert.equal(defaultPlatformForIntent("album_preview"), "album_spread");
  const html = buildIntentPresetHtml();
  assert.match(html, /日常分享/);
  assert.match(html, /内容创作/);
  assert.match(html, /画册跨页/);
  assert.doesNotMatch(html, /portfolio_pages/);
});
