/**
 * title-humanize 与 Python travelogue.domain.title_humanize 对齐。
 */
import test from "node:test";
import assert from "node:assert/strict";

import {
  extractPlaceLabel,
  humanizeFolderTitle,
  isFolderTitleNoise,
  resolveDisplayTitle,
} from "../../templates/studio/js/title-humanize.js";

test("strips hash / handtest noise", () => {
  assert.equal(humanizeFolderTitle("linzhi_a1b2c3d4e5f6"), "linzhi");
  assert.equal(humanizeFolderTitle("ux-handtest-photos-v2"), "我的旅途");
  assert.equal(humanizeFolderTitle("京都雨后"), "京都雨后");
});

test("preserves dots in folder names", () => {
  assert.equal(humanizeFolderTitle("2024.10 京都"), "2024 10 京都");
  assert.equal(humanizeFolderTitle("Day1.出发"), "Day1 出发");
});

test("strips known media suffixes only", () => {
  assert.equal(humanizeFolderTitle("京都雨后.zip"), "京都雨后");
  assert.equal(humanizeFolderTitle("photos.jpg"), "photos");
});

test("empty / noise / limit", () => {
  assert.equal(humanizeFolderTitle(""), "我的旅途");
  assert.equal(humanizeFolderTitle("新建文件夹"), "我的旅途");
  const longName = "一二三四五六七八九十一二三四五六七八九十";
  assert.equal(humanizeFolderTitle(longName), longName.slice(0, 20));
});

test("SFC · double dash and place extract", () => {
  assert.equal(humanizeFolderTitle("武大--米娜"), "武大 米娜");
  assert.equal(isFolderTitleNoise("武大--米娜"), true);
  assert.equal(extractPlaceLabel("2025东澳岛9"), "东澳岛");
});

test("SFC · resolveDisplayTitle matches BE fallbacks", () => {
  assert.equal(resolveDisplayTitle({ title: "武大--米娜" }), "武大 米娜");
  assert.equal(
    resolveDisplayTitle({ title: "2025东澳岛9" }),
    "东澳岛 · 旅行"
  );
  // 清洗后可读则保留，不得残留 --
  assert.equal(
    resolveDisplayTitle({ displayTitle: "武大--米娜", title: "武大--米娜" }),
    "武大 米娜"
  );
});
