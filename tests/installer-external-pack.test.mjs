/**
 * Installer: external single-skill packs (e.g. topmind-writing-skills) must not
 * spread repo-level evals/ / LICENSE / README into the host skills root, and must
 * not overwrite the topmind pack receipt.
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

function makeExternalPack(root, { linkShared = false } = {}) {
  write(path.join(root, "package.json"), JSON.stringify({ name: "@topmindspace/demo-writing-skills", version: "0.1.2" }));
  write(path.join(root, "LICENSE"), "MIT\n");
  write(path.join(root, "README.md"), "# demo\n");
  write(path.join(root, "evals", "evals.json"), "{}\n");
  write(path.join(root, "shared", "scripts", "x.py"), "print(1)\n");
  write(
    path.join(root, "demo-post", "SKILL.md"),
    `---\nname: demo-post\ndescription: demo. Use when demo.\nmetadata:\n  version: "0.1.2"\n---\n\n${linkShared ? "See ../shared/scripts/x.py\n" : "Self-contained.\n"}`,
  );
  write(path.join(root, "demo-post", "scripts", "run.py"), "print(2)\n");
}

function runAdd(source, dest) {
  return spawnSync(process.execPath, [installer, "add", source, "--dest", dest], { encoding: "utf8" });
}

test("external pack installs only skill dirs (no evals/LICENSE/README/shared)", () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "tm-ext-"));
  try {
    const src = path.join(tmp, "src");
    const dest = path.join(tmp, "dest");
    makeExternalPack(src);
    const r = runAdd(src, dest);
    assert.equal(r.status, 0, r.stderr || r.stdout);
    assert.ok(fs.existsSync(path.join(dest, "demo-post", "SKILL.md")));
    assert.ok(fs.existsSync(path.join(dest, "demo-post", "scripts", "run.py")));
    for (const stray of ["evals", "LICENSE", "README.md", "shared", "INSTALL.md", "install-targets"]) {
      assert.equal(fs.existsSync(path.join(dest, stray)), false, `${stray} must not land in the skills root`);
    }
    assert.equal(fs.existsSync(path.join(dest, ".topmind-skills-install.json")), false, "topmind receipt untouched");
    const receipt = JSON.parse(fs.readFileSync(path.join(dest, ".topmind-skills-install.demo-writing-skills.json"), "utf8"));
    assert.equal(receipt.version, "0.1.2");
    assert.deepEqual(receipt.skill_ids, ["demo-post"]);
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});

test("external pack brings shared/ only when a SKILL.md links ../shared/", () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "tm-ext-"));
  try {
    const src = path.join(tmp, "src");
    const dest = path.join(tmp, "dest");
    makeExternalPack(src, { linkShared: true });
    const r = runAdd(src, dest);
    assert.equal(r.status, 0, r.stderr || r.stdout);
    assert.ok(fs.existsSync(path.join(dest, "shared", "scripts", "x.py")));
    assert.equal(fs.existsSync(path.join(dest, "evals")), false);
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});

test("topmind pack install still ships shared/ and topmind-pack.json with its receipt", () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "tm-pack-"));
  try {
    const dest = path.join(tmp, "dest");
    const r = runAdd(repoRoot, dest);
    assert.equal(r.status, 0, r.stderr || r.stdout);
    assert.ok(fs.existsSync(path.join(dest, "topmind", "SKILL.md")));
    assert.ok(fs.existsSync(path.join(dest, "shared", "trigger-disambiguation.md")));
    assert.ok(fs.existsSync(path.join(dest, "topmind-pack.json")));
    assert.ok(fs.existsSync(path.join(dest, ".topmind-skills-install.json")));
    assert.equal(fs.existsSync(path.join(dest, "topmind-wechat")), false, "topmind-wechat is no longer shipped");
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});
