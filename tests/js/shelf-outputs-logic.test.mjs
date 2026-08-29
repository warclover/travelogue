/**
 * OLT M2 · 票根副券纯函数（QA-OLT-03 / AC-OLT-15/17/19/26）。
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  ZERO_OUTPUT_TICKET_SHAPE,
  allowReadyBadge,
  chipTextHasNoDigits,
  deleteConfirmCopy,
  manageRows,
  outputChips,
  overflowAriaLabel,
  readyConflictsOutdated,
  lastRecipeRequest,
  reexportRequest,
  revealFailToast,
  shouldInsertOutputStubs,
  sortOutputs,
  ticketChipLabel,
  ticketOpenMetaShape,
  visibleCopyIsClean,
} from "../../templates/studio/homepage-v2/shelf-outputs-logic.js";

function rec(partial) {
  return Object.assign(
    {
      outputId: "xiaohongshu",
      profile: "xiaohongshu",
      surface: "card",
      label: "小红书",
      createdAt: "2026-08-20T00:00:00Z",
      state: "ready",
      files: ["a.png"],
      fileCount: 12,
    },
    partial
  );
}

describe("sortOutputs", function () {
  it("puts folio first then scroll/card, newest within a surface", function () {
    var rows = sortOutputs([
      rec({ outputId: "xiaohongshu", surface: "card", createdAt: "2026-08-24T00:00:00Z" }),
      rec({ outputId: "wechat_moments", surface: "scroll", label: "朋友圈", createdAt: "2026-08-25T00:00:00Z" }),
      rec({ outputId: "portfolio_pages", surface: "folio", label: "作品集页图", createdAt: "2026-08-20T00:00:00Z" }),
      rec({ outputId: "poster_bric", surface: "card", label: "单张海报", createdAt: "2026-08-26T00:00:00Z" }),
    ]);
    assert.deepEqual(
      rows.map(function (r) { return r.outputId; }),
      ["portfolio_pages", "wechat_moments", "poster_bric", "xiaohongshu"]
    );
  });
});

describe("outputChips", function () {
  it("hides zip/pdf from ticket chips but counts them in overflow", function () {
    var view = outputChips({
      outputs: [
        rec({ outputId: "portfolio_pages", surface: "folio", label: "作品集页图" }),
        rec({ outputId: "xiaohongshu", surface: "card", label: "小红书" }),
        rec({ outputId: "wechat_moments", surface: "scroll", label: "朋友圈" }),
        rec({ outputId: "poster_bric", surface: "card", label: "单张海报" }),
        rec({ outputId: "share_zip", surface: "bundle", label: "分享包" }),
        rec({ outputId: "pdf", surface: "bundle", label: "PDF" }),
      ],
    });
    assert.equal(view.chips.length, 3);
    assert.equal(view.chips[0].label, "作品集");
    assert.equal(view.chips[0].text, "作品集");
    assert.equal(view.overflow, 3);
    view.chips.forEach(function (chip) {
      assert.equal(chipTextHasNoDigits(chip.text), true);
      assert.equal(visibleCopyIsClean(chip.title), true);
      assert.equal(visibleCopyIsClean(chip.ariaLabel), true);
      assert.match(chip.text, /^[^\d]+$/);
    });
  });

  it("uses server summary as-is and computes +N from total", function () {
    var view = outputChips({
      outputSummary: {
        total: 5,
        chips: [
          { outputId: "portfolio_pages", label: "作品集页图", state: "ready", revealRelPath: "导出文件/a.png" },
          { outputId: "xiaohongshu", label: "小红书", state: "outdated", revealRelPath: "导出文件/b.png" },
        ],
      },
    });
    assert.equal(view.chips.length, 2);
    assert.equal(view.overflow, 3);
    assert.equal(view.chips[1].title, "小红书 · 内容有更新，可重新导出");
    assert.equal(overflowAriaLabel(view.overflow), "还有 3 种成品，点击查看");
  });

  it("renders nothing when there are no outputs", function () {
    var view = outputChips({});
    assert.equal(view.chips.length, 0);
    assert.equal(view.overflow, 0);
  });
});

describe("ticketOpenMetaShape", function () {
  it("keeps the pre-OLT ticket children when there are no outputs (AC-OLT-14)", function () {
    assert.equal(shouldInsertOutputStubs({}), false);
    assert.deepEqual(ticketOpenMetaShape({}), ZERO_OUTPUT_TICKET_SHAPE);
    assert.deepEqual(ticketOpenMetaShape({ outputSummary: { total: 0, chips: [] } }), ZERO_OUTPUT_TICKET_SHAPE);
    assert.equal(ticketOpenMetaShape({}).openMetaClass.includes("stub--chips"), false);
    assert.equal(ticketOpenMetaShape({}).children.includes("v2-shelf__stubs"), false);
  });

  it("inserts the stubs row after the title block", function () {
    var shape = ticketOpenMetaShape({
      outputSummary: {
        total: 1,
        chips: [{ outputId: "xiaohongshu", label: "小红书", state: "ready" }],
      },
    });
    assert.deepEqual(shape.children, [
      "v2-shelf__stub-main",
      "v2-shelf__stubs",
    ]);
    assert.match(shape.openMetaClass, /stub--chips/);
  });
});

describe("readyConflictsOutdated", function () {
  it("is false when longshotStale already matches outdated chips", function () {
    assert.equal(
      readyConflictsOutdated({
        longshotStale: true,
        outputSummary: {
          total: 1,
          chips: [{ outputId: "xiaohongshu", label: "小红书", state: "outdated" }],
        },
      }),
      false
    );
  });

  it("flags the forbidden ready + outdated pair", function () {
    assert.equal(
      readyConflictsOutdated({
        longshotStale: false,
        outputSummary: {
          total: 1,
          chips: [{ outputId: "xiaohongshu", label: "小红书", state: "outdated" }],
        },
      }),
      true
    );
  });

  it("hides 分享图已就绪 when outdated chips leak through (AC-OLT-26)", function () {
    var leaked = {
      longshotStale: false,
      outputSummary: {
        total: 1,
        chips: [{ outputId: "xiaohongshu", label: "小红书", state: "outdated" }],
      },
    };
    assert.equal(allowReadyBadge(leaked), false);
    assert.equal(allowReadyBadge({ longshotStale: false, outputSummary: { total: 0, chips: [] } }), true);
    assert.equal(
      allowReadyBadge({
        longshotStale: true,
        outputSummary: {
          total: 1,
          chips: [{ outputId: "xiaohongshu", label: "小红书", state: "outdated" }],
        },
      }),
      true
    );
  });
});

describe("ticketChipLabel", function () {
  it("shortens 作品集页图 on the ticket only", function () {
    assert.equal(ticketChipLabel("作品集页图"), "作品集");
    assert.equal(ticketChipLabel("小红书"), "小红书");
    assert.equal(ticketChipLabel(""), "");
  });
});

describe("manageRows and copy", function () {
  it("puts numbers only in the manage list", function () {
    var rows = manageRows([
      rec({ fileCount: 32, createdAt: "2026-08-26T03:00:00Z", state: "ready", label: "作品集页图" }),
    ]);
    assert.equal(rows[0].label, "作品集页图");
    assert.equal(rows[0].sub, "32 个文件 · 2026 · 08 · 26");
    assert.equal(rows[0].stateLabel, "最新");
    assert.equal(visibleCopyIsClean(rows[0].label), true);
    assert.equal(visibleCopyIsClean(rows[0].stateLabel), true);
    assert.equal(
      deleteConfirmCopy("珠海东澳", "小红书"),
      "删除《珠海东澳》的小红书？只删这份成品，不影响这本书本身。"
    );
    assert.equal(revealFailToast(), "没找到这份文件，可能已被移动或删除。");
    assert.equal(visibleCopyIsClean(revealFailToast()), true);
  });

  it("maps wechat whole/chapter to existing export entry", function () {
    assert.deepEqual(reexportRequest({ outputId: "wechat_chat:whole" }), {
      platform: "wechat_chat",
      segmentMode: "full",
    });
    assert.deepEqual(reexportRequest({ outputId: "wechat_chat:chapter" }), {
      platform: "wechat_chat",
      segmentMode: "chapter",
    });
  });

  it("lastRecipeRequest prefers outdated chip then first ticket", function () {
    assert.deepEqual(lastRecipeRequest({}), { platform: "wechat_chat" });
    assert.deepEqual(
      lastRecipeRequest({
        outputSummary: {
          total: 2,
          chips: [
            rec({ outputId: "xiaohongshu", profile: "xiaohongshu", state: "ready" }),
            rec({ outputId: "wechat_chat:whole", profile: "wechat_chat", state: "outdated" }),
          ],
        },
      }),
      { platform: "wechat_chat", segmentMode: "full" }
    );
  });
});
