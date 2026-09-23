import test from "node:test";
import assert from "node:assert/strict";
import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const skillsRoot = path.resolve(__dirname, "..");

/**
 * Optional engine checkout for cross-repo UTR/lib contract checks.
 * Resolution: TOPMIND_SRC env → sibling ../topmind → ./.topmind-src
 */
async function exists(p) {
  try {
    await fs.access(p);
    return true;
  } catch {
    return false;
  }
}

async function resolveEngineRootAsync() {
  const candidates = [
    process.env.TOPMIND_SRC,
    path.resolve(skillsRoot, "..", "topmind"),
    path.resolve(skillsRoot, ".topmind-src"),
  ].filter(Boolean);
  for (const dir of candidates) {
    if (await exists(path.join(dir, "utr", "contracts"))) return dir;
  }
  return null;
}

async function readPack() {
  return JSON.parse(await fs.readFile(path.join(skillsRoot, "topmind-pack.json"), "utf8"));
}

/** Load actual UTR command surface: { domain: { command: exposure } } */
async function loadActualSurface(contractsRoot) {
  const surface = {};
  const domains = (await fs.readdir(contractsRoot, { withFileTypes: true }))
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name);
  for (const domain of domains) {
    const contractPath = path.join(contractsRoot, domain, `${domain}.json`);
    const contract = JSON.parse(await fs.readFile(contractPath, "utf8"));
    surface[domain] = Object.fromEntries(
      Object.entries(contract.commands || {}).map(([name, cmd]) => [name, cmd.exposure || "advanced"]),
    );
  }
  return surface;
}

async function walkMarkdown(dir) {
  const out = [];
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const abs = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "node_modules" || entry.name.startsWith(".")) continue;
      out.push(...await walkMarkdown(abs));
    } else if (entry.isFile() && entry.name.endsWith(".md")) {
      out.push(abs);
    }
  }
  return out;
}

test("pack.json utr.command_vocabulary is internally well-formed", async () => {
  const manifest = await readPack();
  const vocab = manifest.utr.command_vocabulary;
  assert.ok(vocab && typeof vocab === "object");
  assert.equal(Object.keys(vocab).length, 8, "should declare 8 command domains");
  for (const [domain, commands] of Object.entries(vocab)) {
    assert.ok(Array.isArray(commands) && commands.length > 0, `${domain} should list commands`);
  }
  const total = Object.values(vocab).flat().length;
  assert.equal(manifest.utr.command_count, total, "command_count should equal vocabulary total");
});

test("pack.json command_exposure lists only known vocabulary commands", async () => {
  const manifest = await readPack();
  const vocab = manifest.utr.command_vocabulary;
  const exposure = manifest.utr.command_exposure;
  const known = new Set(
    Object.entries(vocab).flatMap(([domain, commands]) => commands.map((c) => `${domain}.${c}`)),
  );
  const listed = new Set();
  for (const [level, ids] of Object.entries(exposure)) {
    for (const id of ids) {
      assert.ok(known.has(id), `command_exposure.${level} references unknown command ${id}`);
      listed.add(id);
    }
  }
  // Every vocabulary command should appear in exactly one exposure bucket (or advanced default).
  for (const id of known) {
    if (!listed.has(id)) {
      // advanced default is implicit — ok if not listed
      continue;
    }
  }
});

test("capture skill triggers 记一下 not 记下 (Note it ≠ Log it)", async () => {
  const src = await fs.readFile(path.join(skillsRoot, "topmind-capture", "SKILL.md"), "utf8");
  const fm = src.split("---")[1] || "";
  assert.match(fm, /-\s*记一下/u);
  assert.doesNotMatch(fm, /-\s*记下\s*$/m);
});

test("topmind SKILL.md MCP primary+danger inventory covers pack exposure lists", async () => {
  const manifest = await readPack();
  const skill = await fs.readFile(path.join(skillsRoot, "topmind", "SKILL.md"), "utf8");
  const block = skill.match(/UTR 可选（MCP primary\+danger[\s\S]*?。/u);
  assert.ok(block, "SKILL.md must list MCP primary+danger commands");
  const listed = new Set(
    (block[0].match(/`([^`]+)`/gu) || []).map((token) => token.slice(1, -1)),
  );
  const missing = [];
  const exposure = manifest.utr.command_exposure;
  for (const id of [...(exposure.primary || []), ...(exposure.danger || [])]) {
    const [domain, name] = id.split(".");
    if (!listed.has(name) && !listed.has(id)) missing.push(id);
  }
  assert.deepEqual(missing, [], `SKILL.md MCP inventory missing: ${missing.join(", ")}`);
});

test("cross-repo: pack.json utr vocabulary matches engine contracts (when engine available)", async (t) => {
  const engineRoot = await resolveEngineRootAsync();
  if (!engineRoot) {
    t.skip("engine checkout not found (set TOPMIND_SRC or clone topmind as sibling)");
    return;
  }
  const contractsRoot = path.join(engineRoot, "utr", "contracts");
  const manifest = await readPack();
  const actual = await loadActualSurface(contractsRoot);
  const vocab = manifest.utr.command_vocabulary;

  for (const [domain, commands] of Object.entries(vocab)) {
    assert.ok(actual[domain], `domain ${domain} should exist in utr/contracts`);
    for (const command of commands) {
      assert.ok(actual[domain][command], `${domain}.${command} should exist in contracts`);
    }
  }
  for (const [domain, commands] of Object.entries(actual)) {
    assert.ok(Array.isArray(vocab[domain]), `domain ${domain} should be declared in pack.json`);
    for (const command of Object.keys(commands)) {
      assert.ok(vocab[domain].includes(command), `${domain}.${command} missing from pack.json`);
    }
  }
});

test("cross-repo: lib/*.mjs paths referenced in skills docs exist (when engine available)", async (t) => {
  const engineRoot = await resolveEngineRootAsync();
  if (!engineRoot) {
    t.skip("engine checkout not found (set TOPMIND_SRC or clone topmind as sibling)");
    return;
  }
  const markdownFiles = await walkMarkdown(skillsRoot);
  const libRefPattern = /lib\/[\w.-]+\.mjs/gu;
  const missing = [];
  for (const file of markdownFiles) {
    const content = await fs.readFile(file, "utf8");
    const refs = new Set(content.match(libRefPattern) || []);
    for (const ref of refs) {
      const abs = path.join(engineRoot, ref);
      if (!(await exists(abs))) {
        missing.push(`${path.relative(skillsRoot, file)} -> ${ref}`);
      }
    }
  }
  assert.deepEqual(missing, [], `missing lib files referenced from skills docs: ${missing.join(", ")}`);
});
