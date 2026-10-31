/**
 * Agent-facing contracts stay one copy: daily entry, suggest ladder,
 * writeback, optional connectors, and retired WeChat. The installer
 * under test is bin/install-skills.mjs.
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

function read(rel) {
  return fs.readFileSync(path.join(repoRoot, rel), "utf8");
}

test("skill bodies do not restate a second suggest ladder or a bundled wechat skill", () => {
  const pack = JSON.parse(read("topmind-pack.json"));
  const pkg = JSON.parse(read("package.json"));
  assert.equal(pkg.version, pack.version);
  assert.equal(pack.daily_entry, "topmind");
  assert.equal(pack.skills.length, 10);
  assert.deepEqual(
    pack.skills.map((skill) => skill.id),
    [
      "topmind",
      "topmind-capture",
      "topmind-organize",
      "topmind-write",
      "topmind-memory",
      "topmind-maintain",
      "topmind-loop",
      "topmind-weread",
      "topmind-x",
      "topmind-ledger",
    ],
  );
  assert.equal(pack.external_optional_skills.retired["topmind-wechat"] != null, true);

  const capture = read("topmind-capture/SKILL.md");
  const router = read("topmind/SKILL.md");
  const index = read("skills.md");
  const ladder = read("shared/auto-suggest.md");
  const fetchTiers = read("shared/long-url-capture.md");
  const writeback = read("shared/writeback-receipt.md");

  assert.doesNotMatch(capture, /一律走/u);
  assert.doesNotMatch(capture, /\| 显式行动语/u);
  assert.doesNotMatch(capture, /\| L1 \| Desktop/u);
  assert.match(capture, /\.\.\/shared\/auto-suggest\.md/u);
  assert.match(capture, /\.\.\/shared\/long-url-capture\.md/u);
  assert.match(capture, /抓取档/u);
  assert.doesNotMatch(router, /行动语 \/ 稳定个人信息 → L1/u);
  assert.match(router, /\.\.\/shared\/auto-suggest\.md/u);
  assert.match(router, /\.\.\/shared\/writeback-receipt\.md/u);
  assert.doesNotMatch(index, /共 11/u);
  assert.match(index, /共 10 个目录/u);
  assert.match(index, /topmind-wechat-post/u);
  assert.doesNotMatch(index, /公众号 write 子技能/u);
  assert.match(ladder, /显式行动语/);
  assert.match(ladder, /writeback auto 可直接写/u);
  assert.match(ladder, /方向大于约束/);
  assert.match(ladder, /引导、目标、已有经验与知识经验优先于固定操作剧本/);
  assert.match(ladder, /推测出的分类、记忆、专题仍只提案/);
  assert.match(ladder, /明确请求不重复询问/);
  assert.match(router, /方向大于约束/);
  for (const rel of [
    "topmind-capture/SKILL.md",
    "topmind-organize/SKILL.md",
    "topmind-write/SKILL.md",
    "topmind-memory/SKILL.md",
    "topmind-maintain/SKILL.md",
    "topmind-loop/SKILL.md",
  ]) {
    assert.doesNotMatch(read(rel), /\| 显式行动语/u, rel);
  }
  assert.match(fetchTiers, /抓取档/);
  assert.match(fetchTiers, /不是 \[`auto-suggest\.md`\]/);
  assert.match(writeback, /writeback:\s*\n\s*mode: auto \| confirm/u);

  for (const rel of ["README.md", "README.en.md", "README.zh-CN.md", "INSTALL.md", "skills.md"]) {
    const text = read(rel);
    assert.match(text, /topmind/);
    assert.doesNotMatch(text, /├── topmind-wechat\//u);
  }
  const readme = read("README.md");
  const readmeEn = read("README.en.md");
  assert.match(readme, /topmind-pack\.json/);
  assert.match(readmeEn, /topmind-pack\.json/);
  assert.match(readme, /topmind-wechat-post/);
  assert.match(readmeEn, /topmind-wechat-post/);
});

test("installer add into a fresh directory leaves shared/ reachable from the daily entry", () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "tm-contract-"));
  try {
    const dest = path.join(tmp, "skills");
    const result = spawnSync(process.execPath, [installer, "add", repoRoot, "--dest", dest], {
      encoding: "utf8",
    });
    assert.equal(result.status, 0, result.stderr || result.stdout);
    const entry = path.join(dest, "topmind", "SKILL.md");
    const sharedLadder = path.resolve(path.dirname(entry), "../shared/auto-suggest.md");
    const sharedWriteback = path.resolve(path.dirname(entry), "../shared/writeback-receipt.md");
    assert.equal(fs.existsSync(entry), true);
    assert.equal(fs.existsSync(sharedLadder), true);
    assert.equal(fs.existsSync(sharedWriteback), true);
    assert.equal(fs.existsSync(path.join(dest, "topmind-wechat")), false);
    const installedCapture = fs.readFileSync(path.join(dest, "topmind-capture", "SKILL.md"), "utf8");
    assert.doesNotMatch(installedCapture, /一律走/u);
    assert.match(installedCapture, /\.\.\/shared\/auto-suggest\.md/u);
    for (const id of ["topmind-weread", "topmind-x", "topmind-ledger"]) {
      assert.equal(fs.existsSync(path.join(dest, id, "SKILL.md")), true, id);
    }
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});
