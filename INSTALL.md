# Install & update topmind Skills

[简体中文](./README.md) · [English](./README.en.md) · [产品](https://github.com/topmindspace/topmind)

Repository: https://github.com/topmindspace/topmind-skills  
npm: [`@topmindspace/topmind-skills`](https://www.npmjs.com/package/@topmindspace/topmind-skills)  
Daily entry after install: **`topmind`**

```text
canonical  <base>/.agents/skills     ← pack body (one copy)
universal  tools that read .agents/skills need nothing else
private    Claude Code / MiMoCode / Hermes …  ← relative symlink (or --copy)
```

安装模型与开源生态 [`npx skills`](https://github.com/vercel-labs/skills) / [skills.sh](https://skills.sh) 对齐，与 `@topmindspace/tms-skills` 同一套机制。

---

## Quick start

```bash
# npm（推荐 · pack-aware · 含 shared/）
npx @topmindspace/topmind-skills add topmindspace/topmind-skills -g
npx @topmindspace/topmind-skills update -g

# 社区 CLI（快速试用；不含 shared/ — 见下文）
npx skills add topmindspace/topmind-skills -g -y

# 从 GitHub Release（离线 / 固定版本）
node bin/install-skills.mjs add release:latest -g
```

已装 **topmind Desktop** 时也可在 **设置 → 关于与更新** 里对探测到的宿主一键安装 / 升级 / 卸载。

---

## 安装模型（canonical + agents）

| 概念 | 路径 | 说明 |
|------|------|------|
| **Canonical** | `<base>/.agents/skills/` | 整包只存一份（project base = cwd，global base = `~`） |
| **Universal** | 就是 `.agents/skills` | Codex / Cursor / Gemini CLI / Warp / Zed… 项目级**直接读** |
| **Private** | `.claude/skills` · `.mimocode/skills` · `~/.codex/skills` … | 相对**软链**到 canonical（默认）；`--copy` 改为独立副本 |

装完结构（global 示例）：

```text
~/.agents/skills/                 ← canonical（真身 + receipt）
├── topmind/SKILL.md              ← 日常唯一入口
├── topmind-*/
├── shared/
├── topmind-pack.json
└── .topmind-skills-install.json

~/.claude/skills/topmind    → ../../.agents/skills/topmind
~/.claude/skills/shared     → ../../.agents/skills/shared
~/.config/mimocode/skills/topmind → ../../../.agents/skills/topmind
…
```

`../shared/*.md` 渐进披露：在 canonical 内解析到 `~/.agents/skills/shared`；经软链进入时同样落在 canonical 的 `shared/`（相对链接指向同一真身）。

| 命令 | 作用 |
|------|------|
| `add <source>` | 默认 **matrix**：canonical + 已检测智能体 |
| `add … -g` / `-p` | 全局 `~/.agents/skills` / 项目 `./.agents/skills` |
| `add … -a claude-code -a mimocode` | 指定智能体（可多个；`'*'` 全部） |
| `add … --copy` | 私有目录独立副本（默认软链） |
| `add … --dest <dir>` | **只**装进一个目录（单宿主 / 兼容旧用法） |
| `add … --host claude-code` | 兼容旧用法：单宿主默认 dest |
| `update -g` | 从 canonical 里的 receipt 重装 |
| `agents` · `paths` · `doctor [--repair]` | 智能体矩阵 / 路径 / 修复断链 |

---

## Installers

### A. npm / Pack-aware（推荐）

装齐 skill 目录 + `shared/` + `topmind-pack.json`，保证 `../shared/*.md` 渐进披露可用。

```bash
# 矩阵：canonical .agents + 已检测智能体（全局）
npx @topmindspace/topmind-skills add topmindspace/topmind-skills -g

# 只喂给部分智能体
npx @topmindspace/topmind-skills add topmindspace/topmind-skills -g -a claude-code -a mimocode

# 项目级
npx @topmindspace/topmind-skills add topmindspace/topmind-skills -p

# 单目录（旧 --dest 仍可用）
npx @topmindspace/topmind-skills add topmindspace/topmind-skills --dest ~/.claude/skills

# 升级（读 receipt）
npx @topmindspace/topmind-skills update -g

# 查看
npx @topmindspace/topmind-skills agents
npx @topmindspace/topmind-skills paths -g
npx @topmindspace/topmind-skills doctor --repair

# 本地开发：symlink 热更新（单目录）
node bin/install-skills.mjs add . --mode symlink --dest ~/.claude/skills

# Release zip
node bin/install-skills.mjs add release:latest -g
```

私有仓：`export GH_TOKEN=…`（或 `GITHUB_TOKEN`）后再 `add`。

### B. Community CLI — `npx skills`

适用于认 Agent Skills 目录布局的 host。

```bash
npx skills add topmindspace/topmind-skills -g -y
npx skills add topmindspace/topmind-skills -g -y -s topmind -s topmind-capture
npx skills update -g -y
npx skills add topmindspace/topmind-skills -l
```

**注意：社区 CLI 不会装 `shared/`。** topmind skill 有 `../shared/*.md` 链接，缺了会打不开子文档。装完后请再跑一次 pack-aware（或手动拷 `shared/`）：

```bash
npx @topmindspace/topmind-skills add topmindspace/topmind-skills -g
# 或
cp -R /path/to/topmind-skills/shared ~/.agents/skills/shared
```

日志末尾若出现 `Failed to install 9` 且指向 **PromptScript**，是该 host 不支持 global 安装，可忽略；topmind 本身已装上。

---

## Source / options

| Source | 含义 |
|--------|------|
| `topmindspace/topmind-skills` | GitHub `owner/repo`，默认分支，pack 在仓根 |
| `topmindspace/topmind-skills@v*` | 指定 ref / tag |
| `https://github.com/topmindspace/topmind-skills.git` | 任意 git URL |
| `./` / 绝对路径 | 本地 pack 根 |
| `release:latest` | GitHub Release 里的 `topmind-skills-*.zip` |

| Option | 含义 |
|--------|------|
| `-g` / `--global` | **全局 scope**（canonical `~/.agents/skills`）— 与 `npx skills -g` 同义 |
| `-p` / `--project` | 项目 scope（canonical `./.agents/skills`） |
| `-a` / `--agent <ids>` | 目标智能体（可多个；`'*'` 全部） |
| `--copy` | 私有目录复制而非软链 |
| `--dest <dir>` | 只装进这个 skills 根（绕过矩阵） |
| `--host <name>` | 兼容旧用法：单宿主默认 dest |
| `--mode copy\|symlink` | 单目录安装模式（默认 copy） |
| `--skill <id>` | 只装列出的 skill id |
| `--locale en-US` | locale overlay（当前未提供 overlay，回退中文正文） |
| `-n` / `--dry-run` | 只打印计划 |
| `--force` | symlink 模式下替换非软链目标 |

### Agents

| id | 项目路径 | 全局路径 | 类型 |
|----|----------|----------|------|
| `universal` | `.agents/skills` | `~/.agents/skills` | canonical |
| `claude-code` | `.claude/skills` | `~/.claude/skills` | private |
| `mimocode` | `.mimocode/skills` | `~/.config/mimocode/skills` | private |
| `codex` | `.agents/skills` | `~/.codex/skills` | 项目 universal / 全局 private |
| `cursor` | `.agents/skills` | `~/.cursor/skills` | 同上 |
| `gemini-cli` | `.agents/skills` | `~/.gemini/skills` | 同上 |
| `opencode` | `.agents/skills` | `~/.config/opencode/skills` | 同上 |
| `hermes` | `.hermes/skills` | `~/.hermes/skills` | private |
| `github-copilot` | `.agents/skills` | `~/.copilot/skills` | 项目 universal / 全局 private |

无 skill 系统的 host：把 `topmind/SKILL.md` 当 system 片段粘贴，`shared/` 按链接手动附上。

---

## Update

安装后 **canonical** 会写入 `.topmind-skills-install.json`（记录 `source` / `scope` / `agents` / `version`）：

```bash
npx @topmindspace/topmind-skills update -g
# 或
node bin/install-skills.mjs update -g
# 社区 CLI
npx skills update -g -y
```

---

## Zip 加载报 `SKILL.md not found`？

Release 包是 **多 skill 组合包**：

```text
topmind-skills-<ver>.zip
└── topmind-skills-<ver>/
    ├── SKILL.md              ← 根入口 = router
    ├── topmind/SKILL.md      ← 推荐日常入口
    ├── topmind-*/
    └── shared/
```

| Host 行为 | 正确处理 |
|-----------|----------|
| 在 zip 根找 `SKILL.md` | 用包内根 `SKILL.md`（router） |
| 扫描 `*/SKILL.md` | 装全部 `topmind*` 目录 + `shared/` |
| `npx skills add` | 从 GitHub 仓根装（不依赖 zip 根） |

`skills.md` 是包索引，不是 `SKILL.md` 的替代名。

---

## 发布（GitHub Release + npm）

版本真源：`topmind-pack.json`（须与 `package.json` `version`、各 `SKILL.md` / `evals` 一致）。

```bash
# 1) 同步 bump 版本后校验
npm test
npm run pack          # 可选：本地 dist 产物

# 2) 提交并打 tag（推荐发版方式）
git add . && git commit -m "chore: topmind-skills x.y.z"
git tag vX.Y.Z
git push origin main vX.Y.Z
```

push tag `v*` 后 CI 自动：

1. 测试 + 打包
2. 创建 GitHub Release（附 zip / tar.gz / manifest / SHA256SUMS / latest.json）
3. `npm publish` → [`@topmindspace/topmind-skills`](https://www.npmjs.com/package/@topmindspace/topmind-skills)（需仓库 Secret `NPM_TOKEN`，Automation token）
4. **只保留最近 2 个 GitHub Release**（删旧 Release 与附件）。git tag 保留。

| 渠道 | 触发 | 自动 |
|------|------|------|
| GitHub 仓库 / skills.sh | `git push` | 是（直连索引） |
| GitHub Release | tag `v*` | 是 |
| npm | tag `v*`（有 `NPM_TOKEN`） | 是 |

手动兜底（无 CI 时）：

```bash
npm publish --access public
```

### skills.sh

公开 GitHub 仓即可被 `npx skills` / [skills.sh](https://skills.sh/topmindspace/topmind-skills) 索引，无需额外注册：

```bash
npx skills add topmindspace/topmind-skills -g -y
npx skills add topmindspace/topmind-skills -l
```

---

## Security

- Skills 是 Markdown 指令；不信任的 fork 先审再装。
- API Key 不要写进 skill 文件。
- 安装器只写 canonical 与所选智能体技能根，不改其他目录。
- 断链（第三方卸载残留）用 `doctor --repair` 修复，不要手删整棵技能树。
