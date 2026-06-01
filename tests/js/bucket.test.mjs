/**
 * holdback 分桶 · 与服务端 studio_homepage_gate.stable_bucket 公式对齐。
 */
import { createHash } from "node:crypto";
import test from "node:test";
import assert from "node:assert/strict";

const BUCKET_SALT = "travelogue-studio-homepage-v2";

function serverBucket(userAgent) {
  const hex = createHash("sha256")
    .update(`${BUCKET_SALT}:${userAgent || "unknown"}`)
    .digest("hex");
  return parseInt(hex.slice(0, 8), 16) % 100;
}

test("M20jTest/5 → bucket 3（10% holdback 进组）", () => {
  assert.equal(serverBucket("M20jTest/5"), 3);
});

test("M20jTest/1 → bucket 70（10% holdback 对照组）", () => {
  assert.equal(serverBucket("M20jTest/1"), 70);
});

test("deterministic", () => {
  assert.equal(serverBucket("Mozilla/Drill"), serverBucket("Mozilla/Drill"));
});
