import test from "node:test";
import assert from "node:assert/strict";
import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// Pack lives at repo root after the topmind-skills split.
const repoRoot = path.resolve(__dirname, "..");

async function readText(relativePath) {
  return fs.readFile(path.join(repoRoot, relativePath), "utf8");
}

async function readJson(relativePath) {
  return JSON.parse(await readText(relativePath));
}

function assertSurfaceContract(source, label, contentTruth, { desktopOptional = true, utrOptional = true } = {}) {
  const escaped = contentTruth.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  assert.match(source, new RegExp(escaped, "u"), `${label} should name the portable content truth`);
  assert.doesNotMatch(source, /categories-and-topics/u, `${label} must not name a nested categories-and-topics directory`);
  assert.match(
    source,
    /only [`"]?topmind[`"]?|only daily|Expose only `topmind`|same daily entry \(`topmind`\)|日常入口只暴露 `?topmind`?/iu,
    `${label} should expose a single daily entry`,
  );
  assert.match(
    source,
    /not .*content truth|must not .*content truth|must not become topmind content truth|not .*topic state|不得成为 topmind 内容真源|不得成为内容真源/iu,
    `${label} should reject host state as truth`,
  );

  if (desktopOptional) {
    assert.match(
      source,
      /Desktop is not required|requires_desktop["\s:]*false|optional.*Desktop|Desktop, and MCP integrations must expose|Desktop 可选|不要求 Desktop|Desktop 非必需/iu,
      `${label} should keep Desktop optional`,
    );
  }
  if (utrOptional) {
    assert.match(
      source,
      /UTR is optional|requires_utr["\s:]*false|UTR.*optional|Use UTR.*when available|CLI\/MCP when available|UTR 可选|UTR 非必需/iu,
      `${label} should keep UTR optional`,
    );
  }

  assert.doesNotMatch(source, /\/Users\/|\/home\/|~\//u, `${label} should avoid host-specific absolute paths`);
  assert.doesNotMatch(source, /should fork OpenCode|writesContent:\s*true/iu, `${label} should not describe a forked or duplicated truth model`);
  assert.doesNotMatch(source, /topmind-workspace\/projects\//u, `${label} should not mention the v2.x projects/ root`);
  assert.doesNotMatch(source, /\bYYYY-类型-项目名\b/u, `${label} should not mention the v2.x project naming convention`);
  assert.doesNotMatch(source, /\bcreate-project\b|\binspect-project\b|\blist-projects\b|\bappend-project-memory\b|\bupdate-project\b|\bcheck-project\b|\bnormalize-project\b|\barchive-project\b|\brepair-project-index\b/u, `${label} should not reference v2.x UTR command names`);
}

test("portable surface docs mirror the skill-pack content contract", async () => {
  const pack = await readJson("topmind-pack.json");
  const contentTruth = pack.portable_contract.content_truth;

  assert.equal(contentTruth.includes("/"), false);
  assert.doesNotMatch(contentTruth, /categories-and-topics/u);
  assert.equal(pack.product_contract.content_truth, contentTruth);
  assert.equal(pack.daily_entry, "topmind");
  assert.equal(pack.portable_contract.requires_desktop, false);
  assert.equal(pack.portable_contract.requires_utr, false);

  const surfaceDocs = {
    "pack README": await readText("README.md"),
    "Codex integration": await readText("integrations/codex/README.md"),
    "Hermes integration": await readText("integrations/hermes/README.md"),
    "OpenCode integration": await readText("integrations/opencode/README.md"),
  };

  for (const [label, source] of Object.entries(surfaceDocs)) {
    assertSurfaceContract(source, label, contentTruth);
  }
});

test("install target manifests share the portable host prohibitions", async () => {
  const pack = await readJson("topmind-pack.json");

  for (const target of pack.install_targets) {
    const config = await readJson(target.path);

    assert.equal(config.daily_entry, pack.daily_entry);
    assert.equal(config.content_truth, pack.portable_contract.content_truth);
    assert.deepEqual(config.host_must_not, pack.portable_contract.host_must_not);
    assert.doesNotMatch(JSON.stringify(config), /\/Users\/|\/home\/|~\//u);
    assert.ok(config.skills.includes("topmind-loop"), `${target.id} should include topmind-loop`);
    assert.ok(config.skills.includes("topmind-ledger"), `${target.id} should include topmind-ledger`);
    assert.ok(config.skills.includes("topmind-wechat"), `${target.id} should include topmind-wechat`);
  }
});

test("pack docs describe save settings instead of the old preview-confirm lifecycle", async () => {
  const docs = {
    "README": await readText("README.md"),
    "INSTALL": await readText("INSTALL.md"),
    "shared writeback-receipt": await readText("shared/writeback-receipt.md"),
  };

  const combined = Object.values(docs).join("\n");
  assert.match(combined, /writeback_mode:\s*auto\s*\|\s*confirm|writeback\.mode|auto\s*\|\s*confirm/iu);

  for (const [label, source] of Object.entries(docs)) {
    assert.doesNotMatch(source, /Preview\/Confirm\/Evidence|confirm-preview-evidence/u, `${label} should not use the old lifecycle name`);
  }
});

test("write skill presents flexible entry points instead of workflow stages", async () => {
  const source = await readText("topmind-write/SKILL.md");

  assert.match(source, /## Writing Entry Points/u);
  assert.doesNotMatch(source, /## Writing Stages|whichever stage|Stages are not rigid|skip stages|loop back|workflow stages/iu);
});

test("pack is free of legacy project naming and project_type field", async () => {
  const docs = {
    "README": await readText("README.md"),
    "pack": await readText("topmind-pack.json"),
    "router": await readText("topmind/SKILL.md"),
  };

  const combined = Object.values(docs).join("\n");
  const deprecated = [
    { pattern: /topmind-workspace\/projects\//u, name: "old projects/ root" },
    { pattern: /\bYYYY-类型-项目名\b/u, name: "old project naming" },
    { pattern: /\bproject_type:\s/u, name: "old project_type field" },
    { pattern: /\bcreate-project\b|\binspect-project\b|\blist-projects\b|\bappend-project-memory\b|\bupdate-project\b|\bcheck-project\b|\bnormalize-project\b|\barchive-project\b|\brepair-project-index\b/u, name: "v2.x UTR command names" },
  ];

  for (const { pattern, name } of deprecated) {
    assert.doesNotMatch(combined, pattern, `pack docs should not contain ${name}`);
  }
});

test("pack does not reference TUI surface (removed)", async () => {
  const pack = await readJson("topmind-pack.json");
  assert.ok(!pack.surfaces.includes("tui"), "pack surfaces should not include tui");
  assert.ok(!pack.portable_contract.host_may_provide.includes("tui"), "host_may_provide should not include tui");
});

test("content_truth is the workspace directory the engine canon marks as 内容真源", async (t) => {
  const pack = await readJson("topmind-pack.json");
  const candidates = [
    process.env.TOPMIND_SRC && path.join(process.env.TOPMIND_SRC, "PRODUCT-BOUNDARIES.md"),
    path.resolve(repoRoot, "..", "topmind", "PRODUCT-BOUNDARIES.md"),
    path.resolve(repoRoot, ".topmind-src", "PRODUCT-BOUNDARIES.md"),
  ].filter(Boolean);
  let boundaries = null;
  for (const candidate of candidates) {
    try {
      boundaries = await fs.readFile(candidate, "utf8");
      break;
    } catch {
      /* try the next engine checkout */
    }
  }
  if (!boundaries) {
    t.skip("engine PRODUCT-BOUNDARIES.md not available");
    return;
  }
  const marked = boundaries.match(/^├──\s+([A-Za-z0-9._-]+)\/\s+#\s*内容真源/m);
  assert.ok(marked, "PRODUCT-BOUNDARIES home layout must mark one directory as 内容真源");
  assert.equal(pack.portable_contract.content_truth, marked[1]);
  assert.equal(pack.product_contract.content_truth, marked[1]);
});

test("INSTALL prune step keeps git tags and does not document tag deletion", async () => {
  const install = await readText("INSTALL.md");
  assert.match(install, /只保留最近 2 个 GitHub Release/);
  assert.match(install, /git tag 保留/);
  assert.doesNotMatch(install, /tag 会被删除/);
  const workflow = await readText(".github/workflows/release.yml");
  const code = workflow
    .split("\n")
    .filter((line) => {
      const trimmed = line.trim();
      return trimmed && !trimmed.startsWith("#");
    })
    .join("\n");
  assert.doesNotMatch(code, /git\/refs\/tags/u);
});

test("integration README relative links resolve inside this pack", async () => {
  for (const host of ["codex", "hermes", "opencode"]) {
    const rel = path.join("integrations", host, "README.md");
    const source = await readText(rel);
    assert.doesNotMatch(source, /skills\/topmind-pack\.json/u, `${rel} must cite the pack file that exists at repo root`);
    assert.doesNotMatch(source, /10 modules/u, `${rel} must not freeze a stale module count`);
    const links = [...source.matchAll(/\]\(([^)]+)\)/g)].map((match) => match[1]);
    for (const link of links) {
      if (/^(https?:|mailto:|#)/u.test(link)) continue;
      const abs = path.resolve(repoRoot, "integrations", host, link.split("#")[0]);
      await fs.stat(abs);
    }
  }
});
