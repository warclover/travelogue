/**
 * 首页 v2 · demo-showcase manifest 加载与 URL 派生。
 * 契约：docs/studio-homepage-v2/DATA-CONTRACT.md §1 + §2.5
 */
import { STUDIO_DEMO_SHOWCASE_BASE } from "./store.js";

const MANIFEST_URL = STUDIO_DEMO_SHOWCASE_BASE + "manifest.json";

/** 将 demo manifest 相对路径拼成可访问的静态 URL。 */
export function assetUrl(relPath) {
  if (!relPath) return "";
  return STUDIO_DEMO_SHOWCASE_BASE + String(relPath).replace(/^\/+/, "");
}

/** 单页图片 URL（demo webp 或 user trip 绝对 url）。 */
export function pageImageUrl(manifest, page) {
  if (!page) return "";
  if (page.url) return String(page.url);
  return assetUrl(page.webp);
}

/** 背景 / 长图 asset URL。 */
export function manifestAssetUrl(manifest, key) {
  if (!manifest || !manifest.assets) return "";
  var rel = manifest.assets[key];
  if (!rel) return "";
  if (String(rel).startsWith("/")) return rel;
  return assetUrl(rel);
}

/** 基本结构校验（轻量；权威 schema 见 manifest.schema.json）。 */
export function isValidManifest(m) {
  if (!m || typeof m !== "object") return false;
  if (!m.version || !m.title) return false;
  if (!m.assets || !m.assets.background || !m.assets.longshot) return false;
  if (!Array.isArray(m.pages) || m.pages.length < 1) return false;
  return m.pages.every(function (p) {
    return p && p.id && p.role && p.label && (p.webp || p.url);
  });
}

/**
 * 加载 demo manifest。失败 / 不合法时 resolve(null)，由调用方走 §11.4 降级。
 */
export function loadManifest() {
  return fetch(MANIFEST_URL)
    .then(function (r) {
      if (!r.ok) throw new Error("manifest unavailable");
      return r.json();
    })
    .then(function (m) {
      if (isValidManifest(m)) {
        m.source = m.source || "demo";
        return m;
      }
      return null;
    })
    .catch(function () {
      return null;
    });
}
