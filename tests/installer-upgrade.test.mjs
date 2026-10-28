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
function makeCorePack(root, ver) {
  write(path.join(root, "topmind-pack.json"), JSON.stringify({ name: "topmind", version: ver, skills: [{ id: "topmind" }] }));
  write(path.join(root, "topmind", "SKILL.md"), skillMd("topmind", ver));
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

test("symlink mode preserves an unrelated link without --force", () =>
  withTmp(({ tmp, src, dest }) => {
    const other = path.join(tmp, "other");
    write(path.join(other, "SKILL.md"), skillMd("something-else", "1.0.0"));
    fs.mkdirSync(dest, { recursive: true });
    fs.symlinkSync(other, path.join(dest, "demo-post"), "junction");
    const r = add(src, dest, "--mode", "symlink");
    assert.notEqual(r.status, 0);
    assert.ok(fs.lstatSync(path.join(dest, "demo-post")).isSymbolicLink());
    assert.equal(fs.realpathSync(path.join(dest, "demo-post")), fs.realpathSync(other));
  }));

test("matrix install checks private links before changing the canonical pack", () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "tm-core-link-"));
  try {
    const src = path.join(tmp, "src");
    const project = path.join(tmp, "project");
    const other = path.join(tmp, "other");
    const privateRoot = path.join(project, ".claude", "skills");
    fs.mkdirSync(privateRoot, { recursive: true });
    makeCorePack(src, "1.0.0");
    write(path.join(other, "SKILL.md"), skillMd("something-else", "1.0.0"));
    fs.symlinkSync(other, path.join(privateRoot, "topmind"), "junction");
    const env = { ...process.env, HOME: path.join(tmp, "home") };
    const r = spawnSync(process.execPath, [installer, "add", src, "-p", "-a", "claude-code"], { encoding: "utf8", cwd: project, env });
    assert.notEqual(r.status, 0);
    assert.match(r.stderr, /unrelated entry/);
    assert.equal(fs.existsSync(path.join(project, ".agents", "skills", "topmind")), false);
    assert.equal(fs.realpathSync(path.join(privateRoot, "topmind")), fs.realpathSync(other));
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});

test("matrix install preserves a host skills directory linked to the canonical directory", () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "tm-core-alias-"));
  try {
    const src = path.join(tmp, "src");
    const project = path.join(tmp, "project");
    const canonical = path.join(project, ".agents", "skills");
    const privateRoot = path.join(project, ".claude", "skills");
    makeCorePack(src, "1.0.0");
    fs.mkdirSync(canonical, { recursive: true });
    fs.mkdirSync(path.dirname(privateRoot), { recursive: true });
    fs.symlinkSync(canonical, privateRoot, "junction");
    const env = { ...process.env, HOME: path.join(tmp, "home") };
    const r = spawnSync(process.execPath, [installer, "add", src, "-p", "-a", "claude-code"], { encoding: "utf8", cwd: project, env });
    assert.equal(r.status, 0, r.stderr || r.stdout);
    assert.ok(fs.lstatSync(privateRoot).isSymbolicLink());
    assert.ok(fs.lstatSync(path.join(canonical, "topmind")).isDirectory());
    assert.match(fs.readFileSync(path.join(privateRoot, "topmind", "SKILL.md"), "utf8"), /1\.0\.0/);
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});

test("copy mode keeps an unrelated skill folder unless forced", () =>
  withTmp(({ src, dest }) => {
    seed(dest, "1.0.0", "something-else");
    const r = add(src, dest);
    assert.notEqual(r.status, 0);
    assert.match(r.out, /is not an installed demo-post skill/);
    assert.ok(fs.existsSync(path.join(dest, "demo-post", "stale.txt")));
  }));

test("installer refuses to replace its own source skill", () =>
  withTmp(({ src }) => {
    const original = fs.readFileSync(path.join(src, "demo-post", "SKILL.md"), "utf8");
    const r = add(src, src);
    assert.notEqual(r.status, 0);
    assert.match(r.out, /refusing to install demo-post into its own source tree/);
    assert.equal(fs.readFileSync(path.join(src, "demo-post", "SKILL.md"), "utf8"), original);
  }));

test("symlink installer refuses to replace its own source skill", () =>
  withTmp(({ src }) => {
    const original = fs.readFileSync(path.join(src, "demo-post", "SKILL.md"), "utf8");
    const r = add(src, src, "--mode", "symlink");
    assert.notEqual(r.status, 0);
    assert.match(r.out, /refusing to install demo-post into its own source tree/);
    assert.ok(fs.lstatSync(path.join(src, "demo-post")).isDirectory());
    assert.equal(fs.readFileSync(path.join(src, "demo-post", "SKILL.md"), "utf8"), original);
  }));

test("matrix install rejects an unusable private root before installing canonical skills", () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "tm-core-root-"));
  try {
    const src = path.join(tmp, "src");
    const project = path.join(tmp, "project");
    makeCorePack(src, "1.0.0");
    write(path.join(project, ".claude", "skills"), "not a directory\n");
    const env = { ...process.env, HOME: path.join(tmp, "home") };
    const r = spawnSync(process.execPath, [installer, "add", src, "-p", "-a", "claude-code"], { encoding: "utf8", cwd: project, env });
    assert.notEqual(r.status, 0);
    assert.match(r.stderr, /cannot use agent skills directory/);
    assert.equal(fs.existsSync(path.join(project, ".agents", "skills", "topmind")), false);
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});

test("core pack rejects a skill id that escapes the install root", () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "tm-core-id-"));
  try {
    const src = path.join(tmp, "src");
    const dest = path.join(tmp, "dest");
    makeCorePack(src, "1.0.0");
    write(path.join(src, "topmind-pack.json"), JSON.stringify({ name: "topmind", version: "1.0.0", skills: [{ id: "../outside" }] }));
    const r = add(src, dest);
    assert.notEqual(r.status, 0);
    assert.match(r.out, /invalid skill id in pack/);
    assert.equal(fs.existsSync(path.join(tmp, "outside")), false);
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});

test("single-directory update follows its receipt and stays in that directory", () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "tm-core-update-"));
  try {
    const src = path.join(tmp, "src");
    const dest = path.join(tmp, "dest");
    const project = path.join(tmp, "project");
    fs.mkdirSync(project);
    makeCorePack(src, "1.0.0");
    const env = { ...process.env, HOME: path.join(tmp, "home") };
    const first = spawnSync(process.execPath, [installer, "add", src, "--dest", dest], { encoding: "utf8", cwd: project, env });
    assert.equal(first.status, 0, first.stderr || first.stdout);
    makeCorePack(src, "2.0.0");
    const updated = spawnSync(process.execPath, [installer, "update", "--dest", dest], { encoding: "utf8", cwd: project, env });
    assert.equal(updated.status, 0, updated.stderr || updated.stdout);
    assert.match(fs.readFileSync(path.join(dest, "topmind", "SKILL.md"), "utf8"), /2\.0\.0/);
    assert.equal(fs.existsSync(path.join(project, ".agents", "skills", "topmind")), false);
    const receipt = JSON.parse(fs.readFileSync(path.join(dest, ".topmind-skills-install.json"), "utf8"));
    assert.equal(receipt.install_kind, "single");
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});

test("global update never falls back to a project receipt", () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "tm-core-scope-"));
  try {
    const src = path.join(tmp, "src");
    const project = path.join(tmp, "project");
    const dest = path.join(project, ".agents", "skills");
    fs.mkdirSync(project);
    makeCorePack(src, "1.0.0");
    const env = { ...process.env, HOME: path.join(tmp, "home") };
    const first = spawnSync(process.execPath, [installer, "add", src, "--dest", dest], { encoding: "utf8", cwd: project, env });
    assert.equal(first.status, 0, first.stderr || first.stdout);
    makeCorePack(src, "2.0.0");
    const updated = spawnSync(process.execPath, [installer, "update", "-g"], { encoding: "utf8", cwd: project, env });
    assert.notEqual(updated.status, 0);
    assert.match(updated.stderr, /no \.topmind-skills-install\.json/);
    assert.match(updated.stderr, /add topmindspace\/topmind-skills -g/);
    assert.match(fs.readFileSync(path.join(dest, "topmind", "SKILL.md"), "utf8"), /1\.0\.0/);
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});

test("matrix copy update keeps private agent copies instead of switching to links", () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "tm-core-matrix-"));
  try {
    const src = path.join(tmp, "src");
    const project = path.join(tmp, "project");
    fs.mkdirSync(project);
    makeCorePack(src, "1.0.0");
    const env = { ...process.env, HOME: path.join(tmp, "home") };
    const args = [installer, "add", src, "-p", "--copy", "-a", "claude-code"];
    const first = spawnSync(process.execPath, args, { encoding: "utf8", cwd: project, env });
    assert.equal(first.status, 0, first.stderr || first.stdout);
    assert.match(first.stdout, /update -p/);
    const privateSkill = path.join(project, ".claude", "skills", "topmind");
    assert.equal(fs.lstatSync(privateSkill).isSymbolicLink(), false);
    makeCorePack(src, "2.0.0");
    const updated = spawnSync(process.execPath, [installer, "update", "-p"], { encoding: "utf8", cwd: project, env });
    assert.equal(updated.status, 0, updated.stderr || updated.stdout);
    assert.equal(fs.lstatSync(privateSkill).isSymbolicLink(), false);
    assert.match(fs.readFileSync(path.join(privateSkill, "SKILL.md"), "utf8"), /2\.0\.0/);
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});
