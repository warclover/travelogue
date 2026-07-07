/**
 * 首页 v2 · manifest URL 派生单测（node --test）。
 * 覆盖 demo 相对路径不得解析到站点根（HP22-02a）。
 */
import test from "node:test";
import assert from "node:assert/strict";

import {
  assetUrl,
  longshotPageUrl,
  pageImageUrl,
  resolvePageAssetUrl,
} from "../../templates/studio/homepage-v2/manifest.js";

const DEMO_MANIFEST = {
  version: "test",
  title: "test",
  assets: {
    background: "background-PLACEHOLDER.webp",
    longshot: "longshot-PLACEHOLDER.webp",
  },
  pages: [],
};

test("resolvePageAssetUrl demo 相对路径走 demo-showcase 前缀", () => {
  assert.equal(
    resolvePageAssetUrl("longshot-PLACEHOLDER.webp"),
    "/__studio/assets/demo-showcase/longshot-PLACEHOLDER.webp",
  );
});

test("resolvePageAssetUrl trip 绝对路径仍编码", () => {
  assert.equal(
    resolvePageAssetUrl("/trips/demo/longshot.webp"),
    "/trips/demo/longshot.webp",
  );
});

test("longshotPageUrl longshotPages 相对 url 不泄漏到站点根", () => {
  var page = { id: "longshot", url: "longshot-PLACEHOLDER.webp" };
  assert.equal(
    longshotPageUrl(DEMO_MANIFEST, page),
    assetUrl("longshot-PLACEHOLDER.webp"),
  );
});

test("pageImageUrl 相对 url 与 webp 同源", () => {
  assert.equal(
    pageImageUrl(DEMO_MANIFEST, { url: "scroll/cover-PLACEHOLDER.webp" }),
    assetUrl("scroll/cover-PLACEHOLDER.webp"),
  );
  assert.equal(
    pageImageUrl(DEMO_MANIFEST, { webp: "scroll/cover-PLACEHOLDER.webp" }),
    assetUrl("scroll/cover-PLACEHOLDER.webp"),
  );
});
