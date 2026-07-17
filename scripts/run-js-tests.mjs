/**
 * SFH W0a · 跨平台 JS 单测入口（D-SFH-11）。
 * 扫描 tests/js/*.test.mjs 后交给 node --test，避免 shell 通配与目录模式差异。
 */
import { spawnSync } from "node:child_process";
import { readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const jsDir = join(repoRoot, "tests", "js");
const files = readdirSync(jsDir)
  .filter((name) => name.endsWith(".test.mjs"))
  .sort()
  .map((name) => join(jsDir, name));

if (files.length === 0) {
  console.error("SFH: tests/js 下没有 *.test.mjs");
  process.exit(1);
}

const result = spawnSync(process.execPath, ["--test", ...files], {
  cwd: repoRoot,
  stdio: "inherit",
  env: process.env,
});

if (result.error) {
  console.error(result.error);
  process.exit(1);
}

process.exit(result.status == null ? 1 : result.status);
