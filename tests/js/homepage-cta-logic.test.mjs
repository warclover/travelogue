/**
 * UX-01 · 首页状态主按钮判定（node --test）。
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  CTA_DELIVERED,
  CTA_EMPTY,
  CTA_RESUME_EXPORT,
  CTA_RESUME_MAKE,
  pickResumeTrip,
  previewHref,
  resolveHomepageCta,
} from "../../templates/studio/homepage-v2/homepage-cta-logic.js";

describe("pickResumeTrip", function () {
  it("skips demo-album and uses the first user trip", function () {
    var trip = pickResumeTrip([
      { tripId: "demo-album", title: "斯里兰卡见闻录" },
      { tripId: "kyoto", title: "京都五日", edition: "journal" },
    ]);
    assert.equal(trip.tripId, "kyoto");
  });

  it("returns null when only demo trips exist", function () {
    assert.equal(pickResumeTrip([{ tripId: "demo-album" }]), null);
  });
});

describe("resolveHomepageCta", function () {
  it("empty state uses folder pick + demo trial", function () {
    var cta = resolveHomepageCta([]);
    assert.equal(cta.state, CTA_EMPTY);
    assert.equal(cta.primaryLabel, "选择照片文件夹");
    assert.equal(cta.primaryAction, "import");
    assert.equal(cta.secondaryLabel, "试用示例");
    assert.equal(cta.secondaryAction, "demo");
    assert.equal(cta.chip, "");
  });

  it("never-exported trip resumes making with edition chip", function () {
    var cta = resolveHomepageCta([
      { tripId: "kyoto", title: "京都五日", edition: "journal" },
    ]);
    assert.equal(cta.state, CTA_RESUME_MAKE);
    assert.equal(cta.primaryLabel, "继续制作《京都五日》");
    assert.equal(cta.primaryAction, "preview");
    assert.equal(cta.secondaryLabel, "选择照片文件夹");
    assert.equal(cta.chip, "游记");
  });

  it("stale export resumes check-and-export for portfolio", function () {
    var cta = resolveHomepageCta([
      {
        tripId: "tokyo",
        title: "东京街拍",
        edition: "portfolio",
        hasLongshotExport: true,
        longshotStale: true,
        previewUrl: "/tokyo/index.html",
      },
    ]);
    assert.equal(cta.state, CTA_RESUME_EXPORT);
    assert.equal(cta.primaryLabel, "继续检查并导出");
    assert.equal(cta.primaryAction, "preview_export");
    assert.equal(cta.chip, "作品集");
    assert.equal(previewHref(cta.trip, true), "/tokyo/index.html?exportPanel=1");
  });

  it("delivered trip uses plan A: new folder primary, open last secondary", function () {
    var cta = resolveHomepageCta([
      {
        tripId: "kyoto",
        title: "京都五日",
        edition: "journal",
        hasLongshotExport: true,
        longshotStale: false,
      },
    ]);
    assert.equal(cta.state, CTA_DELIVERED);
    assert.equal(cta.primaryLabel, "选择照片文件夹");
    assert.equal(cta.primaryAction, "import");
    assert.equal(cta.secondaryLabel, "打开《京都五日》");
    assert.equal(cta.secondaryAction, "preview");
    assert.equal(cta.chip, "");
  });
});
