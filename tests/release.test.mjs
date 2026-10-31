import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { resolveRelease } from "../scripts/resolve-release.mjs";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

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

test("shipped pack, package, skill metadata and changelog name one version", () => {
  const pack = JSON.parse(fs.readFileSync(path.join(repoRoot, "topmind-pack.json"), "utf8"));
  const pkg = JSON.parse(fs.readFileSync(path.join(repoRoot, "package.json"), "utf8"));
  const evals = JSON.parse(fs.readFileSync(path.join(repoRoot, "evals/evals.json"), "utf8"));
  assert.equal(pkg.version, pack.version);
  assert.equal(evals.version, pack.version);
  assert.match(pack.version, /^\d+\.\d+\.\d+$/u);
  const changelog = fs.readFileSync(path.join(repoRoot, "CHANGELOG.md"), "utf8");
  assert.match(changelog, new RegExp(`^## ${pack.version} — `, "mu"));
  const skills = fs.readdirSync(repoRoot, { withFileTypes: true }).filter((entry) => entry.isDirectory());
  let checked = 0;
  for (const entry of skills) {
    const skillMd = path.join(repoRoot, entry.name, "SKILL.md");
    if (!fs.existsSync(skillMd)) continue;
    const text = fs.readFileSync(skillMd, "utf8");
    const version = text.match(/^\s*version:\s*["']?([^"'\n]+?)["']?\s*$/mu);
    assert.ok(version, `${entry.name}/SKILL.md missing version`);
    assert.equal(version[1].trim(), pack.version, entry.name);
    checked += 1;
  }
  assert.ok(checked >= 9);
});
