#!/usr/bin/env node
/**
 * topmind skills install / update — same mental model as open skill registries:
 *
 *   "Point at a repo (or local path) + optional skills subdir → install into a host skills root → update later."
 *
 * Compatible with the community CLI (installs individual SKILL.md trees):
 *
 *   npx skills add topmindspace/topmind-skills -g -y
 *   npx skills update -g -y
 *
 * This script is pack-aware: it also copies shared/, topmind-pack.json, INSTALL.md, etc.
 * so progressive-disclosure links like ../shared/*.md keep working.
 *
 * Commands:
 *   add <source>     Install or reinstall from a source
 *   update           Re-install from the receipt written at dest
 *   list             Show what a source would install (no write)
 *
 * Source forms for `add`:
 *   topmindspace/topmind-skills                  GitHub owner/repo (default branch)
 *   topmindspace/topmind-skills@main             owner/repo@ref
 *   https://github.com/topmindspace/topmind-skills.git  git URL
 *   ./skills                                     local pack root or monorepo skills/
 *   release:latest | release:v4.3.0              GitHub Release zip (topmind-skills-*)
 *
 * Options:
 *   --path <subdir>     Subdir inside the repo that holds the pack (default: skills)
 *   --dest <dir>        Host skills root to install into
 *   --host <name>       Default dest: claude-code|codex|hermes|opencode|generic
 *   --mode copy|symlink copy (default) or symlink (local sources only)
 *   --skill <id>        Only install these skill ids (repeatable / comma-separated)
 *   --global / -g       Alias: --host claude-code (user-level ~/.claude/skills)
 *   --dry-run           Print plan only
 *   --force             Replace non-symlink destinations when using symlink mode
 *
 * Examples:
 *   # Like `npx skills add topmindspace/topmind-skills -g`
 *   node bin/install-skills.mjs add topmindspace/topmind-skills -g
 *
 *   # Custom monorepo path: only the skills/ tree
 *   node bin/install-skills.mjs add topmindspace/topmind-skills --dest ~/.claude/skills
 *
 *   # Install into a project-local skills dir
 *   node bin/install-skills.mjs add topmindspace/topmind-skills --dest ./.claude/skills
 *
 *   # Upgrade later (reads .topmind-skills-install.json at dest)
 *   node bin/install-skills.mjs update --dest ~/.claude/skills
 *
 *   # Local checkout, live symlink while developing
 *   node bin/install-skills.mjs add . --mode symlink --dest ~/.claude/skills
 *
 * Private GitHub: export GH_TOKEN or GITHUB_TOKEN.
 */

import { promises as fs, existsSync } from "node:fs";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import { createWriteStream } from "node:fs";
import { pipeline } from "node:stream/promises";
import { Readable } from "node:stream";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, "..");
const DEFAULT_OWNER_REPO = "topmindspace/topmind-skills";
const DEFAULT_GIT = `https://github.com/${DEFAULT_OWNER_REPO}.git`;
// Pack lives at repo root in topmind-skills (no monorepo skills/ subdir).
const DEFAULT_PATH = ".";
const RECEIPT_NAME = ".topmind-skills-install.json";

const AGENTS_SUB = path.join(".agents", "skills");

function homeDir() {
  return process.env.HOME || process.env.USERPROFILE || os.homedir();
}

function configHome() {
  return process.env.XDG_CONFIG_HOME || path.join(homeDir(), ".config");
}

/**
 * Ecosystem agent matrix (aligned with `npx skills` / skills.sh):
 *   canonical  <base>/.agents/skills   (project base=cwd, global base=~)
 *   universal  agents whose skillsDir is .agents/skills read it directly
 *   private    others get relative symlink (default) or copy into their own root
 */
function agentCatalog() {
  const home = homeDir();
  const cfg = configHome();
  return {
    universal: {
      id: "universal",
      label: "Universal (.agents/skills)",
      projectDir: AGENTS_SUB,
      globalDir: path.join(home, AGENTS_SUB),
      detect: () => true,
      universal: true,
    },
    "claude-code": {
      id: "claude-code",
      label: "Claude Code",
      projectDir: path.join(".claude", "skills"),
      globalDir: path.join(home, ".claude", "skills"),
      detect: () => fsSyncExists(path.join(home, ".claude")),
      universal: false,
    },
    mimocode: {
      id: "mimocode",
      label: "MiMoCode / MiMo Desktop",
      projectDir: path.join(".mimocode", "skills"),
      globalDir: path.join(cfg, "mimocode", "skills"),
      detect: () => fsSyncExists(path.join(cfg, "mimocode")) || fsSyncExists(path.join(home, ".mimocode")),
      universal: false,
    },
    codex: {
      id: "codex",
      label: "Codex",
      projectDir: AGENTS_SUB,
      globalDir: path.join(home, ".codex", "skills"),
      detect: () => fsSyncExists(path.join(home, ".codex")),
      universal: false,
    },
    cursor: {
      id: "cursor",
      label: "Cursor",
      projectDir: AGENTS_SUB,
      globalDir: path.join(home, ".cursor", "skills"),
      detect: () => fsSyncExists(path.join(home, ".cursor")),
      universal: false,
    },
    "gemini-cli": {
      id: "gemini-cli",
      label: "Gemini CLI",
      projectDir: AGENTS_SUB,
      globalDir: path.join(home, ".gemini", "skills"),
      detect: () => fsSyncExists(path.join(home, ".gemini")),
      universal: false,
    },
    opencode: {
      id: "opencode",
      label: "OpenCode",
      projectDir: AGENTS_SUB,
      globalDir: path.join(cfg, "opencode", "skills"),
      detect: () => fsSyncExists(path.join(cfg, "opencode")) || fsSyncExists(path.join(home, ".opencode")),
      universal: false,
    },
    hermes: {
      id: "hermes",
      label: "Hermes",
      projectDir: path.join(".hermes", "skills"),
      globalDir: path.join(home, ".hermes", "skills"),
      detect: () => fsSyncExists(path.join(home, ".hermes")),
      universal: false,
    },
    "github-copilot": {
      id: "github-copilot",
      label: "GitHub Copilot",
      projectDir: AGENTS_SUB,
      globalDir: path.join(home, ".copilot", "skills"),
      detect: () => fsSyncExists(path.join(home, ".copilot")),
      universal: false,
    },
  };
}

/** Legacy --host names → agent ids + single-dir default dest. */
const HOST_DEFAULTS = {
  "claude-code": () => path.join(homeDir(), ".claude", "skills"),
  codex: () => path.join(homeDir(), ".codex", "skills"),
  hermes: () => path.join(homeDir(), ".hermes", "skills"),
  opencode: () => path.join(process.cwd(), ".opencode", "skills"),
  generic: () => path.join(process.cwd(), "topmind-skills"),
  mimocode: () => path.join(configHome(), "mimocode", "skills"),
};

function fsSyncExists(p) {
  return existsSync(p);
}

function canonicalBase(global) {
  return path.join(global ? homeDir() : process.cwd(), AGENTS_SUB);
}

function agentSkillsRoot(agent, global) {
  return global ? agent.globalDir : path.join(process.cwd(), agent.projectDir);
}

function samePath(a, b) {
  return path.resolve(a) === path.resolve(b);
}

function detectedAgentIds() {
  return Object.values(agentCatalog())
    .filter((a) => a.detect())
    .map((a) => a.id);
}

function resolveAgentSelection(requested, global) {
  const cat = agentCatalog();
  const all = Object.keys(cat);
  let ids;
  if (!requested || !requested.length) ids = detectedAgentIds();
  else if (requested.includes("*")) ids = all;
  else ids = [...new Set(requested)];
  for (const id of ids) {
    if (!cat[id]) fail(`unknown agent: ${id}\nknown: ${all.join(", ")}`);
  }
  ids.sort((a, b) => (a === "universal" ? -1 : b === "universal" ? 1 : a.localeCompare(b)));
  if (!ids.includes("universal")) ids.unshift("universal");
  return ids.map((id) => {
    const agent = cat[id];
    const root = agentSkillsRoot(agent, global);
    return { agent, root, sharesCanonical: samePath(root, canonicalBase(global)) };
  });
}

function log(msg) {
  process.stdout.write(`[install-skills] ${msg}\n`);
}

function fail(msg, code = 1) {
  process.stderr.write(`[install-skills] ERROR: ${msg}\n`);
  process.exit(code);
}

function printHelp() {
  process.stdout.write(`Usage:
  node bin/install-skills.mjs add <source> [options]
  node bin/install-skills.mjs update [--dest <dir>]
  node bin/install-skills.mjs list <source> [options]
  node bin/install-skills.mjs agents | paths | doctor [--repair]

Source: owner/repo | owner/repo@ref | git-url | local-path | release:<tag>

Layout (aligned with npx skills / skills.sh):
  canonical  <base>/.agents/skills     pack body lives here (one copy)
  universal  agents that read .agents/skills need nothing else
  private    Claude Code / MiMoCode / Hermes … get symlink (or --copy)

Options:
  -g, --global         Global scope (canonical ~/.agents/skills + agent global roots)
  -p, --project        Project scope (canonical ./.agents/skills + agent project roots)
  -a, --agent <ids>    Target agents (repeatable / comma-separated; '*' = all)
  --copy               Copy into each private agent dir (default: symlink)
  --dest <dir>         Install ONLY into this skills root (single-dir / legacy)
  --host <name>        Legacy single-host dest: claude-code|codex|hermes|opencode|mimocode|generic
  --mode copy|symlink  Mode for --dest/--host single-dir installs (default: copy)
  --skill <id>         Only install these skill ids (repeatable / comma-separated)
  --locale <code>      Install locale overlay (e.g. en-US); falls back to topmind_LOCALE env
  -n, --dry-run        Print plan only
  --force              Replace non-symlink destinations when using symlink mode

Examples:
  node bin/install-skills.mjs add topmindspace/topmind-skills -g
  node bin/install-skills.mjs add topmindspace/topmind-skills -a claude-code -a mimocode
  node bin/install-skills.mjs add . --dest ~/.claude/skills
  node bin/install-skills.mjs update -g
  node bin/install-skills.mjs doctor --repair

See INSTALL.md for full docs.
`);
}

// ─── args ───────────────────────────────────────────────────────────────────

function parseArgs(argv) {
  const out = {
    command: null,
    source: null,
    dest: null,
    repoPath: DEFAULT_PATH,
    mode: "copy",
    host: null,
    agents: [],
    scope: null, // 'global' | 'project' | null
    linkMode: "symlink", // for agent matrix: symlink | copy
    skillsFilter: null,
    dryRun: false,
    force: false,
    locale: null,
    repair: false,
  };

  if (argv.length === 0) {
    printHelp();
    process.exit(0);
  }

  const first = argv[0];
  if (first === "add" || first === "install" || first === "a") {
    out.command = "add";
    argv = argv.slice(1);
  } else if (first === "update" || first === "upgrade" || first === "u") {
    out.command = "update";
    argv = argv.slice(1);
  } else if (first === "list" || first === "ls") {
    out.command = "list";
    argv = argv.slice(1);
  } else if (first === "agents") {
    out.command = "agents";
    argv = argv.slice(1);
  } else if (first === "paths") {
    out.command = "paths";
    argv = argv.slice(1);
  } else if (first === "doctor") {
    out.command = "doctor";
    argv = argv.slice(1);
  } else if (first === "--help" || first === "-h") {
    printHelp();
    process.exit(0);
  } else if (first.startsWith("-")) {
    out.command = "add";
  } else {
    out.command = "add";
  }

  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const next = () => {
      const v = argv[++i];
      if (v == null || (v.startsWith("-") && v !== "-")) fail(`missing value for ${a}`);
      return v;
    };

    if (a === "--dest" || a === "-d") out.dest = next();
    else if (a === "--path" || a === "--subdir") out.repoPath = next().replace(/^\/+|\/+$/g, "") || ".";
    else if (a === "--source" || a === "-s") out.source = next();
    else if (a === "--from-git") {
      const peek = argv[i + 1];
      if (peek && !peek.startsWith("-")) out.source = next();
      else out.source = DEFAULT_OWNER_REPO;
    } else if (a === "--from-release") {
      const peek = argv[i + 1];
      out.source = peek && !peek.startsWith("-") ? `release:${next()}` : "release:latest";
    } else if (a === "--mode" || a === "-m") out.mode = next();
    else if (a === "--host") out.host = next();
    else if (a === "--global" || a === "-g") out.scope = "global";
    else if (a === "--project" || a === "-p") out.scope = "project";
    else if (a === "--agent" || a === "-a") {
      const raw = next();
      for (const part of raw.split(",")) {
        const id = part.trim();
        if (id) out.agents.push(id);
      }
    } else if (a === "--copy") {
      out.linkMode = "copy";
      out.mode = "copy";
    } else if (a === "--link") out.linkMode = "symlink";
    else if (a === "--skill") {
      const raw = next();
      out.skillsFilter = out.skillsFilter || new Set();
      for (const part of raw.split(",")) {
        const id = part.trim();
        if (id) out.skillsFilter.add(id);
      }
    } else if (a === "--dry-run" || a === "-n") out.dryRun = true;
    else if (a === "--locale") out.locale = next();
    else if (a === "--force" || a === "-f") out.force = true;
    else if (a === "--repair") out.repair = true;
    else if (a === "--update" || a === "-u") out.command = "update";
    else if (a === "--help" || a === "-h") {
      printHelp();
      process.exit(0);
    } else if (a.startsWith("-")) fail(`unknown option: ${a}`);
    else if (!out.source) out.source = a;
    else fail(`unexpected argument: ${a}`);
  }

  if (!["copy", "symlink"].includes(out.mode)) fail(`--mode must be copy|symlink`);
  if (!["copy", "symlink"].includes(out.linkMode)) fail(`--copy/--link must be copy|symlink`);

  // Scope default: project (matches npx skills); -g flips to global.
  if (!out.scope) out.scope = "project";
  out.global = out.scope === "global";

  // Single-dir path: --dest or legacy --host (not the multi-agent matrix).
  if (out.dest) {
    out.dest = path.resolve(out.dest.replace(/^~(?=\/|$)/, os.homedir()));
  } else if (out.host) {
    if (!HOST_DEFAULTS[out.host]) {
      fail(`unknown --host ${out.host}; pass --dest or use: ${Object.keys(HOST_DEFAULTS).join("|")}`);
    }
    out.dest = HOST_DEFAULTS[out.host]();
    out.dest = path.resolve(out.dest.replace(/^~(?=\/|$)/, os.homedir()));
  }

  if (!out.locale) out.locale = process.env.topmind_LOCALE || null;
  return out;
}

// ─── fs helpers ─────────────────────────────────────────────────────────────

async function pathExists(p) {
  try {
    await fs.access(p);
    return true;
  } catch {
    return false;
  }
}

async function isSkillsRoot(dir) {
  if (!(await pathExists(dir))) return false;
  const hasPack = await pathExists(path.join(dir, "topmind-pack.json"));
  const hasRouter = await pathExists(path.join(dir, "topmind", "SKILL.md"));
  if (hasPack && hasRouter) return true;
  // Accept a bare Agent-Skills layout (dirs with SKILL.md) without pack json
  try {
    const entries = await fs.readdir(dir, { withFileTypes: true });
    let n = 0;
    for (const e of entries) {
      if (e.isDirectory() && (await pathExists(path.join(dir, e.name, "SKILL.md")))) n++;
    }
    return n > 0;
  } catch {
    return false;
  }
}

async function resolveSkillsRoot(dir) {
  if (await isSkillsRoot(dir)) return dir;
  if (await isSkillsRoot(path.join(dir, "skills"))) return path.join(dir, "skills");
  return dir;
}

function run(cmd, args, opts = {}) {
  const r = spawnSync(cmd, args, {
    encoding: "utf8",
    stdio: opts.silent ? "pipe" : "inherit",
    env: { ...process.env, ...opts.env },
  });
  if (r.status !== 0) {
    const err = (r.stderr || r.stdout || "").toString().slice(0, 500);
    fail(`${cmd} ${args.join(" ")} failed (${r.status}): ${err}`);
  }
  return r;
}

function githubHeaders() {
  const token = process.env.GH_TOKEN || process.env.GITHUB_TOKEN || "";
  const h = {
    Accept: "application/vnd.github+json",
    "User-Agent": "topmind-install-skills",
  };
  if (token) h.Authorization = `Bearer ${token}`;
  return h;
}

async function fetchJson(url) {
  const res = await fetch(url, { headers: githubHeaders() });
  if (!res.ok) fail(`GET ${url} → ${res.status} ${res.statusText} (private repo needs GH_TOKEN)`);
  return res.json();
}

async function downloadTo(url, destFile) {
  const res = await fetch(url, { headers: githubHeaders(), redirect: "follow" });
  if (!res.ok) fail(`download ${url} → ${res.status}`);
  await fs.mkdir(path.dirname(destFile), { recursive: true });
  await pipeline(Readable.fromWeb(res.body), createWriteStream(destFile));
}

// ─── source resolution ──────────────────────────────────────────────────────

/**
 * Normalize user source string into a descriptor.
 * @returns {{ kind: 'local'|'git'|'release', value: string, ref?: string, label: string }}
 */
function parseSource(raw, repoPath) {
  if (!raw || raw === ".") {
    // topmind-skills: pack lives at repo root; monorepo fallback: skills/
    const root = path.join(REPO_ROOT, "skills");
    const value = REPO_ROOT; // resolveSkillsRoot will pick the right child
    void root;
    return { kind: "local", value, label: `local:${value}` };
  }

  // release:tag
  if (raw.startsWith("release:")) {
    return { kind: "release", value: raw.slice("release:".length) || "latest", label: raw };
  }

  // absolute / relative filesystem path
  if (
    raw.startsWith("/") ||
    raw.startsWith("./") ||
    raw.startsWith("../") ||
    raw.startsWith("~") ||
    raw === "skills"
  ) {
    const p = path.resolve(raw.replace(/^~(?=\/|$)/, os.homedir()));
    return { kind: "local", value: p, label: `local:${p}` };
  }

  // git URL
  if (/^(https?:\/\/|git@)/i.test(raw) || raw.endsWith(".git")) {
    return { kind: "git", value: raw, ref: "HEAD", path: repoPath, label: `git:${raw}` };
  }

  // owner/repo or owner/repo@ref  (skills-add style)
  const m = raw.match(/^([A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+)(?:@([A-Za-z0-9_./-]+))?$/);
  if (m) {
    const repo = m[1];
    const ref = m[2] || "HEAD";
    const url = `https://github.com/${repo}.git`;
    return { kind: "git", value: url, ref, path: repoPath, label: `github:${repo}${m[2] ? "@" + m[2] : ""}` };
  }

  fail(
    `unrecognized source "${raw}". Use owner/repo, git URL, local path, or release:<tag>.\n` +
      `  examples: topmindspace/topmind-skills  .  release:latest`,
  );
}

async function materializeFromGit(gitUrl, ref, subPath, workDir) {
  log(`clone ${gitUrl} (sparse: ${subPath || "."}${ref && ref !== "HEAD" ? ` @ ${ref}` : ""})`);
  await fs.mkdir(workDir, { recursive: true });
  const repoDir = path.join(workDir, "repo");
  if (await pathExists(repoDir)) await fs.rm(repoDir, { recursive: true, force: true });

  // depth-1 sparse clone; checkout ref if not default
  const cloneArgs = ["clone", "--filter=blob:none", "--sparse"];
  if (!ref || ref === "HEAD") cloneArgs.push("--depth", "1");
  cloneArgs.push(gitUrl, repoDir);
  run("git", cloneArgs);

  if (ref && ref !== "HEAD") {
    run("git", ["-C", repoDir, "fetch", "--depth", "1", "origin", ref]);
    run("git", ["-C", repoDir, "checkout", "FETCH_HEAD"]);
  }

  if (subPath && subPath !== ".") {
    run("git", ["-C", repoDir, "sparse-checkout", "set", subPath]);
    const candidate = path.join(repoDir, subPath);
    const root = await resolveSkillsRoot(candidate);
    if (!(await isSkillsRoot(root))) {
      fail(`no skills pack found under ${candidate} (looked for topmind-pack.json or */SKILL.md)`);
    }
    return root;
  }

  // Default: pack at repo root (topmind-skills) or monorepo skills/
  run("git", ["-C", repoDir, "sparse-checkout", "set", "skills"]);
  if (!(await pathExists(path.join(repoDir, "skills")))) {
    run("git", ["-C", repoDir, "sparse-checkout", "disable"]);
  }
  const root = await resolveSkillsRoot(repoDir);
  if (!(await isSkillsRoot(root))) {
    fail(`no skills pack found under ${repoDir} (looked for topmind-pack.json or */SKILL.md)`);
  }
  return root;
}

async function materializeFromRelease(tag, workDir) {
  log(`fetch release assets (tag=${tag}) from ${DEFAULT_OWNER_REPO}`);
  let release;
  if (tag === "latest") {
    try {
      release = await fetchJson(`https://api.github.com/repos/${DEFAULT_OWNER_REPO}/releases/latest`);
    } catch {
      const list = await fetchJson(`https://api.github.com/repos/${DEFAULT_OWNER_REPO}/releases?per_page=10`);
      release = Array.isArray(list) ? list.find((r) => !r.draft) || list[0] : null;
    }
  } else {
    release = await fetchJson(`https://api.github.com/repos/${DEFAULT_OWNER_REPO}/releases/tags/${tag}`);
  }
  if (!release) fail("no GitHub release found — use owner/repo source or publish a v* release tag");
  const assets = release.assets || [];
  const zip =
    assets.find((a) => /^topmind-skills-.*\.zip$/i.test(a.name)) ||
    assets.find((a) => /skills.*\.zip$/i.test(a.name));
  if (!zip) {
    fail(`release ${release.tag_name || tag} has no topmind-skills-*.zip — use owner/repo instead`);
  }
  const zipPath = path.join(workDir, zip.name);
  log(`download ${zip.name}`);
  await downloadTo(zip.browser_download_url, zipPath);
  const unpack = path.join(workDir, "unpack");
  await fs.mkdir(unpack, { recursive: true });
  const tar = spawnSync("tar", ["-xf", zipPath, "-C", unpack], { encoding: "utf8" });
  if (tar.status !== 0) run("unzip", ["-q", zipPath, "-d", unpack]);

  async function walk(dir, depth = 0) {
    if (depth > 4) return null;
    if (await isSkillsRoot(dir)) return resolveSkillsRoot(dir);
    let entries;
    try {
      entries = await fs.readdir(dir, { withFileTypes: true });
    } catch {
      return null;
    }
    for (const e of entries) {
      if (!e.isDirectory()) continue;
      const hit = await walk(path.join(dir, e.name), depth + 1);
      if (hit) return hit;
    }
    return null;
  }
  const root = await walk(unpack);
  if (!root) fail(`could not find skills pack root inside ${zip.name}`);
  return root;
}

async function materialize(sourceDesc, opts, workDir) {
  if (sourceDesc.kind === "local") {
    const root = await resolveSkillsRoot(sourceDesc.value);
    if (!(await isSkillsRoot(root))) fail(`not a skills pack: ${root}`);
    return root;
  }
  if (sourceDesc.kind === "git") {
    return materializeFromGit(sourceDesc.value, sourceDesc.ref || "HEAD", sourceDesc.path || opts.repoPath, workDir);
  }
  if (sourceDesc.kind === "release") {
    return materializeFromRelease(sourceDesc.value, workDir);
  }
  fail(`unknown source kind ${sourceDesc.kind}`);
}

// ─── install plan ───────────────────────────────────────────────────────────

async function listInstallEntries(skillsRoot, skillsFilter) {
  const packPath = path.join(skillsRoot, "topmind-pack.json");
  let version = "unknown";
  let name = "skills";
  let ids = [];

  if (await pathExists(packPath)) {
    const pack = JSON.parse(await fs.readFile(packPath, "utf8"));
    version = pack.version || version;
    name = pack.name || name;
    ids = (pack.skills || []).map((s) => s.id || s.path).filter(Boolean);
  } else {
    // bare Agent Skills layout
    const entries = await fs.readdir(skillsRoot, { withFileTypes: true });
    for (const e of entries) {
      if (e.isDirectory() && (await pathExists(path.join(skillsRoot, e.name, "SKILL.md")))) {
        ids.push(e.name);
      }
    }
  }

  if (skillsFilter && skillsFilter.size) {
    ids = ids.filter((id) => skillsFilter.has(id));
    if (!ids.length) fail(`--skill filter matched nothing. available: ${(await listInstallEntries(skillsRoot, null)).entries.filter((e) => !e.includes(".")).join(", ")}`);
  }

  const entries = new Set(ids);
  // Pack support files (needed for progressive disclosure)
  if (!skillsFilter) {
    for (const e of ["shared", "install-targets", "evals"]) {
      if (await pathExists(path.join(skillsRoot, e))) entries.add(e);
    }
    for (const f of ["topmind-pack.json", "skills.md", "LICENSE", "README.md", "INSTALL.md"]) {
      if (await pathExists(path.join(skillsRoot, f))) entries.add(f);
    }
  } else {
    // still bring shared/ when filtering — SKILL.md links to it
    if (await pathExists(path.join(skillsRoot, "shared"))) entries.add("shared");
    if (await pathExists(path.join(skillsRoot, "topmind-pack.json"))) entries.add("topmind-pack.json");
  }

  return { version, name, entries: [...entries], skillIds: ids };
}

async function applyLocaleOverlay(overlayDir, targetDir) {
  const entries = await fs.readdir(overlayDir, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(overlayDir, entry.name);
    const dstPath = path.join(targetDir, entry.name);
    if (entry.isDirectory()) {
      await fs.mkdir(dstPath, { recursive: true });
      await applyLocaleOverlay(srcPath, dstPath);
    } else {
      await fs.copyFile(srcPath, dstPath);
      log(`    ~ locale overlay: ${entry.name}`);
    }
  }
}

async function installCopy(skillsRoot, dest, entries, locale) {
  await fs.mkdir(dest, { recursive: true });
  for (const name of entries) {
    const src = path.join(skillsRoot, name);
    const dst = path.join(dest, name);
    if (!(await pathExists(src))) continue;
    const st = await fs.lstat(src);
    if (await pathExists(dst)) await fs.rm(dst, { recursive: true, force: true });
    if (st.isDirectory()) {
      await fs.cp(src, dst, { recursive: true });
      // Apply locale overlay if exists
      if (locale) {
        const overlayDir = path.join(src, "locales", locale);
        if (await pathExists(overlayDir)) {
          await applyLocaleOverlay(overlayDir, dst);
          log(`    locale: ${locale}`);
        }
        // Clean up locales/ directory from installed copy (not needed at runtime)
        const localesInstalledDir = path.join(dst, "locales");
        if (await pathExists(localesInstalledDir)) {
          await fs.rm(localesInstalledDir, { recursive: true, force: true });
        }
      }
    } else {
      await fs.copyFile(src, dst);
    }
    log(`  + ${name}`);
  }
}

async function installSymlink(skillsRoot, dest, entries, { force }) {
  await fs.mkdir(dest, { recursive: true });
  for (const name of entries) {
    const src = path.join(skillsRoot, name);
    const dst = path.join(dest, name);
    if (!(await pathExists(src))) continue;
    if (await pathExists(dst)) {
      const st = await fs.lstat(dst);
      if (st.isSymbolicLink() || force) await fs.rm(dst, { recursive: true, force: true });
      else fail(`${dst} exists and is not a symlink (pass --force)`);
    }
    await fs.symlink(src, dst, "junction");
    log(`  ~ ${name} → ${src}`);
  }
}

async function writeInstallReceipt(dest, meta) {
  const receipt = {
    schema: 2,
    package: meta.name || "topmind",
    version: meta.version,
    installed_at: new Date().toISOString(),
    source: meta.sourceLabel,
    source_raw: meta.sourceRaw,
    repo_path: meta.repoPath,
    mode: meta.mode,
    host: meta.host || null,
    scope: meta.scope || null,
    agents: meta.agents || null,
    skill_ids: meta.skillIds,
    locale: meta.locale || null,
    repository: `https://github.com/${DEFAULT_OWNER_REPO}`,
    update: {
      command: "add",
      source: meta.sourceRaw,
      path: meta.repoPath,
      mode: meta.mode,
      host: meta.host || null,
      scope: meta.scope || null,
      agents: meta.agents || null,
    },
  };
  await fs.writeFile(path.join(dest, RECEIPT_NAME), JSON.stringify(receipt, null, 2) + "\n", "utf8");
}

/** Relative-symlink each pack entry from an agent root back to the canonical body. */
async function linkPackEntries(canonicalRoot, agentRoot, entryNames, { force }) {
  await fs.mkdir(agentRoot, { recursive: true });
  for (const name of entryNames) {
    const src = path.join(canonicalRoot, name);
    const dst = path.join(agentRoot, name);
    if (!(await pathExists(src))) continue;
    if (samePath(agentRoot, canonicalRoot)) continue;
    if ((await pathExists(dst)) || (await isBrokenSymlink(dst))) {
      const st = await fs.lstat(dst).catch(() => null);
      if (st && st.isSymbolicLink()) await fs.rm(dst, { recursive: true, force: true });
      else if (force) await fs.rm(dst, { recursive: true, force: true });
      else {
        log(`  ! ${dst} exists (not symlink) — skip (pass --force to replace)`);
        continue;
      }
    }
    const rel = path.relative(agentRoot, src);
    await fs.symlink(rel, dst, "junction");
    log(`  ~ ${path.join(agentRoot, name)} → ${rel}`);
  }
}

async function isBrokenSymlink(p) {
  let st;
  try {
    st = await fs.lstat(p);
  } catch {
    return false;
  }
  if (!st.isSymbolicLink()) return false;
  try {
    await fs.stat(p);
    return false;
  } catch {
    return true;
  }
}

/**
 * Install pack into canonical `.agents/skills`, then link/copy into agent-private roots.
 * Returns the canonical dest (receipt lives there).
 */
async function installViaMatrix(skillsRoot, plan, opts) {
  const global = !!opts.global;
  const canonical = canonicalBase(global);
  const targets = resolveAgentSelection(opts.agents, global);
  const linkMode = opts.linkMode || "symlink";

  log(`matrix ${global ? "global" : "project"} · ${linkMode} · canonical ${canonical}`);

  if (opts.dryRun) {
    log(`  · ${canonical}  [canonical pack]`);
    for (const t of targets) {
      if (t.sharesCanonical) continue;
      log(`  · ${t.root}  [${t.agent.label} → ${linkMode}]`);
    }
    log("(dry-run)");
    return { canonical, targets, plan };
  }

  // 1) Full pack body → canonical
  await installCopy(skillsRoot, canonical, plan.entries, opts.locale);

  // 2) Private agent dirs: symlink entries (default) or copy
  for (const t of targets) {
    if (t.sharesCanonical) {
      log(`  · shared via .agents/skills: ${t.agent.id}`);
      continue;
    }
    if (linkMode === "copy") {
      await installCopy(skillsRoot, t.root, plan.entries, opts.locale);
    } else {
      await linkPackEntries(canonical, t.root, plan.entries, opts);
    }
  }

  await writeInstallReceipt(canonical, {
    name: plan.name,
    version: plan.version,
    sourceLabel: "matrix",
    sourceRaw: opts.source,
    repoPath: opts.repoPath,
    mode: linkMode,
    host: null,
    scope: opts.scope,
    agents: targets.map((t) => t.agent.id),
    skillIds: plan.skillIds,
    locale: opts.locale,
  });

  log(`done → ${canonical}`);
  log(`daily entry: ${path.join(canonical, "topmind", "SKILL.md")}`);
  log(`update later: node bin/install-skills.mjs update -g`);
  return { canonical, targets, plan };
}

function cmdAgents() {
  const cat = agentCatalog();
  const det = new Set(detectedAgentIds());
  log("Agents (id · kind · project · global · status):");
  for (const a of Object.values(cat)) {
    const kind = a.projectDir === AGENTS_SUB ? "universal-project" : "private-project";
    const st = det.has(a.id) ? "detected" : "-";
    log(`  ${a.id.padEnd(16)} ${kind}`);
    log(`  ${"".padEnd(16)} project ${a.projectDir}`);
    log(`  ${"".padEnd(16)} global  ${a.globalDir}`);
    log(`  ${"".padEnd(16)} ${st}`);
  }
}

function cmdPaths(opts) {
  const global = !!opts.global;
  log(`Canonical (${global ? "global" : "project"}):`);
  log(`  ${canonicalBase(global)}`);
  log("Agents:");
  for (const a of Object.values(agentCatalog())) {
    const root = agentSkillsRoot(a, global);
    const share = samePath(root, canonicalBase(global)) ? " (shares .agents/skills)" : "";
    const det = a.detect() ? "detected" : "not detected";
    log(`  ${a.id.padEnd(16)} ${root}${share}  [${det}]`);
  }
}

async function cmdDoctor(opts) {
  const cat = agentCatalog();
  let problems = 0;
  log("Skill root health:");
  for (const a of Object.values(cat)) {
    for (const [scopeName, root] of [
      ["project", path.join(process.cwd(), a.projectDir)],
      ["global", a.globalDir],
    ]) {
      if (!(await pathExists(root)) && !(await pathExists(path.dirname(root)))) continue;
      let st = null;
      try {
        st = await fs.lstat(root);
      } catch {
        st = null;
      }
      if (st && st.isSymbolicLink()) {
        let ok = true;
        try {
          await fs.stat(root);
        } catch {
          ok = false;
        }
        if (!ok) {
          problems++;
          log(`  ✗ ${root}  [${a.label} · ${scopeName}] broken symlink`);
          if (opts.repair) {
            await fs.rm(root, { force: true });
            await fs.mkdir(root, { recursive: true });
            log("    repaired → real directory");
          }
          continue;
        }
      }
      if (st && !st.isDirectory() && !(st.isSymbolicLink())) {
        problems++;
        log(`  ✗ ${root}  [${a.label} · ${scopeName}] not a directory`);
        continue;
      }
      if (st) log(`  ✓ ${root}  [${a.label} · ${scopeName}]`);
    }
  }
  if (!problems) log("  all clear");
  else if (!opts.repair) log("Run `topmind-skills doctor --repair` to replace broken symlinks.");
  if (problems && !opts.repair) process.exitCode = 1;
}

async function readReceipt(dest) {
  const p = path.join(dest, RECEIPT_NAME);
  if (!(await pathExists(p))) return null;
  try {
    return JSON.parse(await fs.readFile(p, "utf8"));
  } catch {
    return null;
  }
}

// ─── commands ───────────────────────────────────────────────────────────────

async function cmdAdd(opts, sourceOverride) {
  const sourceRaw = sourceOverride || opts.source || DEFAULT_OWNER_REPO;
  const sourceDesc = parseSource(sourceRaw, opts.repoPath);
  const useMatrix = !opts.dest;
  const dest = opts.dest || canonicalBase(opts.global);

  log(`add  source=${sourceDesc.label}`);
  log(
    useMatrix
      ? `     path=${opts.repoPath}  scope=${opts.scope}  link=${opts.linkMode}  agents=${opts.agents.length ? opts.agents.join(",") : "detected"}`
      : `     path=${opts.repoPath}  mode=${opts.mode}  dest=${dest}`,
  );

  const tmpRoot = await fs.mkdtemp(path.join(os.tmpdir(), "topmind-skills-"));
  try {
    const skillsRoot = await materialize(sourceDesc, opts, tmpRoot);
    const plan = await listInstallEntries(skillsRoot, opts.skillsFilter);
    log(`pack ${plan.name}@${plan.version} · ${plan.skillIds.length} skill(s) · ${plan.entries.length} entries`);

    if (opts.command === "list") {
      for (const e of plan.entries) log(`  - ${e}`);
      log("(list only)");
      return;
    }

    if (useMatrix) {
      await installViaMatrix(skillsRoot, plan, opts);
      return;
    }

    // Legacy / explicit single-dir install
    if (opts.dryRun) {
      for (const e of plan.entries) log(`  - ${e}`);
      log(`(dry-run) would install → ${dest}`);
      return;
    }

    if (opts.mode === "symlink") {
      if (sourceDesc.kind !== "local") {
        fail("symlink mode needs a durable local --source (git/release clones are temporary)");
      }
      await installSymlink(skillsRoot, dest, plan.entries, opts);
    } else {
      await installCopy(skillsRoot, dest, plan.entries, opts.locale);
    }

    await writeInstallReceipt(dest, {
      name: plan.name,
      version: plan.version,
      sourceLabel: sourceDesc.label,
      sourceRaw,
      repoPath: opts.repoPath,
      mode: opts.mode,
      host: opts.host,
      scope: opts.scope,
      agents: opts.agents,
      skillIds: plan.skillIds,
      locale: opts.locale,
    });

    log(`done → ${dest}`);
    log(`daily entry: ${path.join(dest, "topmind", "SKILL.md")}`);
    log(`update later: node bin/install-skills.mjs update --dest ${dest}`);
  } finally {
    await fs.rm(tmpRoot, { recursive: true, force: true }).catch(() => {});
  }
}

async function cmdUpdate(opts) {
  // Prefer receipt at matrix canonical; fall back to explicit --dest receipt.
  const destCandidates = opts.dest
    ? [opts.dest]
    : [canonicalBase(opts.global), canonicalBase(!opts.global), HOST_DEFAULTS["claude-code"]()];
  let dest = null;
  let receipt = null;
  for (const d of destCandidates) {
    receipt = await readReceipt(d);
    if (receipt) {
      dest = d;
      break;
    }
  }
  if (!receipt) {
    fail(
      `no ${RECEIPT_NAME} in ${destCandidates.join(", ")}.\n` +
        `  First install: node bin/install-skills.mjs add ${DEFAULT_OWNER_REPO} -g\n` +
        `  Or community:  npx skills update -g -y`,
    );
  }
  log(`update from receipt: ${receipt.source} @ ${receipt.version} → ${dest}`);
  const next = {
    ...opts,
    command: "add",
    source: receipt.source_raw || receipt.update?.source || DEFAULT_OWNER_REPO,
    repoPath: receipt.repo_path || receipt.update?.path || DEFAULT_PATH,
    mode: receipt.mode === "symlink" ? "symlink" : "copy",
    linkMode: receipt.agents ? "symlink" : opts.linkMode,
    host: receipt.host || opts.host,
    scope: receipt.scope || opts.scope,
    agents: receipt.agents || opts.agents,
    locale: receipt.locale || opts.locale,
  };
  // Keep matrix mode when the receipt was a matrix install (no single dest host).
  if (receipt.agents) next.dest = null;
  else if (!next.dest) next.dest = dest;

  if (next.mode === "symlink" && next.dest) {
    const local = parseSource(next.source, next.repoPath);
    if (local.kind !== "local" || !(await pathExists(local.value))) {
      log("original symlink source gone — falling back to copy from default git source");
      next.mode = "copy";
      next.source = DEFAULT_OWNER_REPO;
    }
  }
  await cmdAdd(next, next.source);
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));

  if (opts.command === "agents") {
    cmdAgents();
    return;
  }
  if (opts.command === "paths") {
    cmdPaths(opts);
    return;
  }
  if (opts.command === "doctor") {
    await cmdDoctor(opts);
    return;
  }
  if (opts.command === "list") {
    opts.dryRun = true;
    if (!opts.source) opts.source = DEFAULT_OWNER_REPO;
    await cmdAdd({ ...opts, command: "list" });
    return;
  }
  if (opts.command === "update") {
    await cmdUpdate(opts);
    return;
  }
  if (!opts.source) opts.source = DEFAULT_OWNER_REPO;
  await cmdAdd(opts);
}

main().catch((e) => {
  process.stderr.write(`[install-skills] ${e.stack || e}\n`);
  process.exit(1);
});
