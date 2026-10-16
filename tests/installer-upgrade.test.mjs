/**
 * Installer upgrade behaviour: newer packaged -> "Upgraded a -> b" (no backup);
 * same version -> "Already up to date"; installed newer -> refused unless --force;
 * missing version -> upgrade; symlink mode replaces a previous plain-folder install
 * of the same skill but needs --force for unrelated folders.
 */
import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const installer = path.join(repoRoot, "bin", "install-skills.mjs");

function write(file, text) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, text, "utf8");
}
const skillMd = (name, ver) =>
  `---\nname: ${name}\ndescription: demo. Use when demo.\n${ver ? `metadata:\n  version: "${ver}"\n` : ""}---\n\nbody\n`;

function makePack(root, ver = "2.0.0") {
  write(path.join(root, "package.json"), JSON.stringify({ name: "@topmindspace/demo-pack", version: ver }));
  write(path.join(root, "demo-post", "SKILL.md"), skillMd("demo-post", ver));
}
function seed(dest, ver, name = "demo-post") {
  write(path.join(dest, "demo-post", "SKILL.md"), skillMd(name, ver));
  write(path.join(dest, "demo-post", "stale.txt"), "old\n");
}
function add(src, dest, ...extra) {
  const r = spawnSync(process.execPath, [installer, "add", src, "--dest", dest, ...extra], { encoding: "utf8" });
  return { ...r, out: (r.stdout || "") + (r.stderr || "") };
}
function withTmp(fn) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "tm-upg-"));
  try {
    const src = path.join(tmp, "src");
    const dest = path.join(tmp, "dest");
    makePack(src);
    fn({ tmp, src, dest });
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
}

test("older installed version is upgraded in place without backup", () =>
  withTmp(({ src, dest }) => {
    seed(dest, "1.0.0");
    const r = add(src, dest);
    assert.equal(r.status, 0, r.out);
    assert.match(r.out, /Upgraded demo-post 1\.0\.0 -> 2\.0\.0/);
    assert.equal(fs.existsSync(path.join(dest, "demo-post", "stale.txt")), false);
    assert.equal(fs.readdirSync(dest).some((n) => /bak|backup/i.test(n)), false);
  }));

test("missing installed version counts as upgrade", () =>
  withTmp(({ src, dest }) => {
    seed(dest, null);
    const r = add(src, dest);
    assert.equal(r.status, 0, r.out);
    assert.match(r.out, /Upgraded demo-post unknown -> 2\.0\.0/);
  }));

test("same version is skipped as up to date; --force reinstalls", () =>
  withTmp(({ src, dest }) => {
    seed(dest, "2.0.0");
    const r = add(src, dest);
    assert.equal(r.status, 0, r.out);
    assert.match(r.out, /Already up to date: demo-post 2\.0\.0/);
    assert.ok(fs.existsSync(path.join(dest, "demo-post", "stale.txt")));
    const r2 = add(src, dest, "--force");
    assert.equal(r2.status, 0, r2.out);
    assert.match(r2.out, /Reinstalled demo-post 2\.0\.0/);
    assert.equal(fs.existsSync(path.join(dest, "demo-post", "stale.txt")), false);
  }));

test("newer installed version is refused unless --force", () =>
  withTmp(({ src, dest }) => {
    seed(dest, "3.0.0");
    const r = add(src, dest);
    assert.notEqual(r.status, 0);
    assert.match(r.out, /newer than packaged \(demo-post 3\.0\.0 > 2\.0\.0\).*--force/);
    assert.ok(fs.existsSync(path.join(dest, "demo-post", "stale.txt")));
    const r2 = add(src, dest, "--force");
    assert.equal(r2.status, 0, r2.out);
    assert.equal(fs.existsSync(path.join(dest, "demo-post", "stale.txt")), false);
  }));

test("symlink mode replaces a previous plain-folder install of the same skill", () =>
  withTmp(({ src, dest }) => {
    seed(dest, "1.0.0");
    const r = add(src, dest, "--mode", "symlink");
    assert.equal(r.status, 0, r.out);
    assert.ok(fs.lstatSync(path.join(dest, "demo-post")).isSymbolicLink());
  }));

test("symlink mode needs --force for an unrelated folder", () =>
  withTmp(({ src, dest }) => {
    seed(dest, "1.0.0", "something-else");
    const r = add(src, dest, "--mode", "symlink");
    assert.notEqual(r.status, 0);
    assert.match(r.out, /unrelated folder \(no matching SKILL\.md name\) — pass --force to replace it/);
    assert.ok(fs.existsSync(path.join(dest, "demo-post", "stale.txt")));
    const r2 = add(src, dest, "--mode", "symlink", "--force");
    assert.equal(r2.status, 0, r2.out);
    assert.ok(fs.lstatSync(path.join(dest, "demo-post")).isSymbolicLink());
  }));
