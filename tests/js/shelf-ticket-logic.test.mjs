/**
 * 书架票根装饰编号 · 撞码回归（node --test）。
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  stubCode,
  stubFactsLine,
  stubFingerprint,
  stubSerial,
} from "../../templates/studio/homepage-v2/shelf-ticket-logic.js";

describe("stubCode", function () {
  it("different tripIds that collided under the old mixer now diverge", function () {
    // Real shelf collisions observed 2026-08-10 (MHQERHUN / KKJQFTNY).
    var trips = [
      { tripId: "demo-20ecc928d6", title: "武大 米娜", photoCount: 25 },
      { tripId: "demo-65db8fd377", title: "凯哥拍摄精选 · 旅行", photoCount: 58 },
      { tripId: "demo-1d4f92d534", title: "旅行 · 6月30–7月1日", photoCount: 250 },
      { tripId: "demo-3ee2727aea", title: "夏睿彤年度精选", photoCount: 82 },
      { tripId: "demo-album", title: "斯里兰卡见闻录", photoCount: 16 },
      { tripId: "demo-0ebda73294", title: "初中毕业照", photoCount: 135 },
      { tripId: "demo-49cbe46479", title: "张智慧仲夏日漫游斯里兰卡", photoCount: 249 },
    ];
    var codes = trips.map(stubCode);
    assert.equal(new Set(codes).size, codes.length);
    assert.equal(codes[0].length, 8);
    assert.match(codes[0], /^[A-Z2-9]+$/);
  });

  it("accepts bare tripId string for backward-compatible callers", function () {
    var code = stubCode("demo-album");
    assert.equal(code.length, 8);
    assert.equal(code, stubCode({ tripId: "demo-album", title: "", photoCount: 0 }));
  });
});

describe("stubSerial", function () {
  it("mixes title so same-year books are less likely to share NO. suffix", function () {
    var s1 = stubSerial({
      tripId: "demo-20ecc928d6",
      title: "武大 米娜",
      photoCount: 25,
      updatedAt: 1720000000,
    });
    var s2 = stubSerial({
      tripId: "demo-65db8fd377",
      title: "凯哥拍摄精选 · 旅行",
      photoCount: 58,
      updatedAt: 1720000000,
    });
    assert.match(s1, /^NO\.\d{8}$/);
    assert.notEqual(s1, s2);
  });
});

describe("stubFactsLine", function () {
  it("keeps date and count off the edition words", function () {
    var line = stubFactsLine({
      title: "华农油菜花",
      edition: "portfolio",
      pageCount: 13,
      photoCount: 31,
      updatedAt: 1756406400,
    });
    assert.match(line, /31 张/);
    assert.equal(line.includes("游记"), false);
    assert.equal(line.includes("作品集"), false);
  });
});

describe("stubFingerprint", function () {
  it("is stable for the same string", function () {
    assert.equal(stubFingerprint("demo-album"), stubFingerprint("demo-album"));
    assert.notEqual(stubFingerprint("a"), stubFingerprint("b"));
  });
});
