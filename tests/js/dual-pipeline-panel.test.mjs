/**
 * DPI W0 · FE-DPI-04 · journal export panel snapshot stays stable
 * when portfolio panel options change.
 */
import test from "node:test";
import assert from "node:assert/strict";

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  buildPanelHtml,
  journalDockChrome,
  journalExportPanelSnapshot,
} from "../../templates/studio/js/longshot-export-panel.js";
import { journalDockCta } from "../../templates/studio/js/journal-dock-logic.js";
import { resolveTripEdition } from "../../templates/studio/js/portfolio-dock-logic.js";

const here = dirname(fileURLToPath(import.meta.url));
const dockSrc = readFileSync(
  join(here, "../../templates/studio/preview-toolbar/dock.js"),
  "utf8",
);
const longshotSrc = readFileSync(
  join(here, "../../templates/studio/preview-toolbar/longshot.js"),
  "utf8",
);

const JOURNAL_IDS = ["wechat_chat", "xiaohongshu", "album_spread"];
const PORTFOLIO_IDS = ["wechat_chat", "xiaohongshu", "album_spread", "portfolio_pages"];

test("DPI · journal snapshot is edition-stable and ignores pipeline flag", () => {
  const snap = journalExportPanelSnapshot(JOURNAL_IDS);
  assert.equal(snap.html, buildPanelHtml(JOURNAL_IDS));
  assert.equal(snap.html, buildPanelHtml(JOURNAL_IDS, { edition: "journal" }));
  assert.equal(
    snap.html,
    buildPanelHtml(JOURNAL_IDS, { edition: "journal", pipelineEnabled: true }),
  );
  assert.deepEqual(snap.dock, journalDockChrome());
  assert.equal(snap.title, "导出设置");
  assert.doesNotMatch(snap.html, /导出作品集/);
  assert.doesNotMatch(snap.html, /印刷跨页（现网画册）/);
});

test("DPI · changing portfolio panel does not change journal snapshot", () => {
  const before = journalExportPanelSnapshot(JOURNAL_IDS);
  const portfolio = buildPanelHtml(PORTFOLIO_IDS, {
    edition: "portfolio",
    pipelineEnabled: true,
  });
  assert.notEqual(portfolio, before.html);
  assert.match(portfolio, /data-portfolio-share-fold|导出作品集/);
  const after = journalExportPanelSnapshot(JOURNAL_IDS);
  assert.equal(after.html, before.html);
  assert.deepEqual(after.dock, before.dock);
});

test("DPI W3 · dock.js is mount + dispatch only", () => {
  const branches = dockSrc.match(
    /if\s*\([^)]*(?:isPortfolio|readToolbarEdition|isPortfolioEdition|data-edition)/g,
  ) || [];
  assert.ok(branches.length <= 2, branches.join(" | "));
  assert.match(dockSrc, /applyJournalDockLogic/);
  assert.match(dockSrc, /applyPortfolioDockLogic/);
  assert.equal(longshotSrc.includes("readToolbarEdition"), false);
  assert.match(longshotSrc, /shouldRunSocialBatchExport/);
  assert.match(
    longshotSrc,
    /_pendingSocialPlatforms = shouldRunSocialBatchExport/,
  );
  assert.match(
    longshotSrc,
    /shouldRunSocialBatchExport\(root && root\._edition, pendingSocial\)/,
  );
  assert.match(
    longshotSrc,
    /!isPortfolioEdition\(root && root\._edition\) &&\s*\n\s*!assertConfirmedPlatformPayload/,
  );
  assert.match(longshotSrc, /isPortfolioPrintOneShot/);
  assert.doesNotMatch(longshotSrc, /album_landscape:\s*"album_spread"/);
  assert.deepEqual(journalDockCta(), journalDockChrome());
  assert.equal(resolveTripEdition({ _edition: "journal" }, { edition: "portfolio" }), "portfolio");
  assert.equal(resolveTripEdition({ _edition: "portfolio" }, { edition: "journal" }), "journal");
});
