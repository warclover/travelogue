/**
 * 首页 v2 · demo-showcase manifest 加载与 URL 派生。
 * 契约：docs/studio-homepage-v2/DATA-CONTRACT.md §1 + §2.5
 */
import { STUDIO_DEMO_SHOWCASE_BASE } from "./store.js";

const MANIFEST_URL = STUDIO_DEMO_SHOWCASE_BASE + "manifest.json";

/** 编码 trip 静态资源 URL（中文文件名等 · 与 serve.py unquote 对称）。 */
export function encodeTripAssetUrl(url) {
  if (!url) return "";
  var s = String(url);
  if (/^https?:\/\//i.test(s)) return s;
  if (s.charAt(0) !== "/") return s;
  var slash = s.indexOf("/", 1);
  if (slash < 0) return s;
  var base = s.slice(0, slash);
  var tail = s.slice(slash + 1);
  if (!tail) return s;
  return base + "/" + tail.split("/").map(function (seg) {
    if (!seg) return seg;
    try {
      return encodeURIComponent(decodeURIComponent(seg));
    } catch (_e) {
      return encodeURIComponent(seg);
    }
  }).join("/");
}

/** 将 demo manifest 相对路径拼成可访问的静态 URL。 */
export function assetUrl(relPath) {
  if (!relPath) return "";
  return STUDIO_DEMO_SHOWCASE_BASE + String(relPath).replace(/^\/+/, "");
}

/** demo 相对路径或 trip 绝对 / 外链 URL（禁止裸相对路径泄漏到站点根）。 */
export function resolvePageAssetUrl(spec) {
  if (!spec) return "";
  var s = String(spec);
  if (/^https?:\/\//i.test(s)) return s;
  if (s.charAt(0) === "/") return encodeTripAssetUrl(s);
  return assetUrl(s);
}

/** 单页图片 URL（demo webp 或 user trip 绝对 url）。 */
export function pageImageUrl(manifest, page) {
  if (!page) return "";
  if (page.url) return resolvePageAssetUrl(page.url);
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

/** 手机框竖滚序列（longshotPages 或单张 assets.longshot）。 */
export function longshotPages(manifest) {
  if (!manifest) return [];
  var rows = manifest.longshotPages;
  if (Array.isArray(rows) && rows.length) {
    return rows.filter(function (p) { return p && p.url; });
  }
  var url = manifestAssetUrl(manifest, "longshot");
  if (!url) return [];
  return [{ id: "longshot", label: "微信长图", url: url, scrollPreview: true }];
}

/** longshotPages 条目 URL。 */
export function longshotPageUrl(manifest, page) {
  if (!page) return "";
  if (page.url) return resolvePageAssetUrl(page.url);
  return manifestAssetUrl(manifest, "longshot");
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
