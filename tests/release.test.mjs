import test from "node:test";
import assert from "node:assert/strict";
import { resolveRelease } from "../scripts/resolve-release.mjs";

const base = { version: "4.15.7", packageVersion: "4.15.7" };
test("tag releases resolve the pushed version", () => {
  assert.deepEqual(resolveRelease({ ...base, eventName: "push", refName: "v4.15.7", inputTag: "ignored" }), { version: "4.15.7", tag: "v4.15.7" });
});
test("manual drafts use the explicit tag instead of the branch", () => {
  assert.equal(resolveRelease({ ...base, eventName: "workflow_dispatch", refName: "main", inputTag: "v4.15.7" }).tag, "v4.15.7");
});
test("missing, mismatched and injected tags fail before publication", () => {
  for (const inputTag of [undefined, "main", "v4.15.6", "4.15.7", "v4.15.7\nother=value"]) {
    assert.throws(() => resolveRelease({ ...base, eventName: "workflow_dispatch", refName: "main", inputTag }), /Release tag/);
  }
  assert.throws(() => resolveRelease({ ...base, eventName: "push", refName: "main" }), /Release tag/);
});
test("version truth sources must agree before publication", () => {
  assert.throws(() => resolveRelease({ ...base, packageVersion: "4.15.6", refName: "v4.15.7" }), /same numeric release version/);
  assert.throws(() => resolveRelease({ ...base, version: "4.15.7\ntag=other", refName: "v4.15.7" }), /same numeric release version/);
});
