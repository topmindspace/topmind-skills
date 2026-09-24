# Install & update topmind Skills

[简体中文](./README.md) · [English](./README.en.md) · [产品](https://github.com/topmindspace/topmind)

Repository: https://github.com/topmindspace/topmind-skills  
npm: [`@topmindspace/topmind-skills`](https://www.npmjs.com/package/@topmindspace/topmind-skills)  
Daily entry after install: **`topmind`**

```text
Source → install into host skills root → update later from the same source
Source:  topmindspace/topmind-skills | . | release:latest
Dest:    $HOME/.claude/skills | ./.claude/skills | $HOME/.codex/skills | …
```

---

## Quick start

```bash
# npm（推荐 · pack-aware · 含 shared/）
npx @topmindspace/topmind-skills add topmindspace/topmind-skills -g
npx @topmindspace/topmind-skills update -g

# 社区 CLI（快速试用；不含 shared/）
npx skills add topmindspace/topmind-skills -g -y

# 从 GitHub Release（离线 / 固定版本）
node bin/install-skills.mjs add release:latest -g
```

已装 **topmind Desktop** 时也可在 **设置 → 关于与更新** 里对探测到的宿主一键安装 / 升级 / 卸载。

---

## Installers

### A. npm / Pack-aware（推荐）

装齐 skill 目录 + `shared/` + `topmind-pack.json`，保证 `../shared/*.md` 渐进披露可用。

```bash
# 无需 clone
npx @topmindspace/topmind-skills add topmindspace/topmind-skills -g
npx @topmindspace/topmind-skills update -g
npx @topmindspace/topmind-skills list topmindspace/topmind-skills

# 全局 CLI
npm i -g @topmindspace/topmind-skills
topmind-skills add topmindspace/topmind-skills -g

# 指定宿主 / 目标
npx @topmindspace/topmind-skills add topmindspace/topmind-skills --host codex
npx @topmindspace/topmind-skills add topmindspace/topmind-skills --dest ./.claude/skills

# 源码仓内
npm run add -- topmindspace/topmind-skills -g
npm run update -- --dest $HOME/.claude/skills
npm run list -- topmindspace/topmind-skills

# 本地目录 / symlink 热更新
node bin/install-skills.mjs add . --mode symlink --dest $HOME/.claude/skills

# Release zip
node bin/install-skills.mjs add release:latest -g
```

私有仓：`export GH_TOKEN=…`（或 `GITHUB_TOKEN`）后再 `add`。

### B. Community CLI — `npx skills`

适用于 Claude Code / Cursor / Codex / OpenCode 等认 Agent Skills 目录布局的 host。

```bash
npx skills add topmindspace/topmind-skills -g -y
npx skills add topmindspace/topmind-skills -g -y -s topmind -s topmind-capture
npx skills update -g -y
npx skills add topmindspace/topmind-skills -l
```

**注意：社区 CLI 不会装 `shared/`。** topmind skill 有 `../shared/*.md` 链接，缺了会打不开子文档。装完后请再跑一次 pack-aware（或手动拷 `shared/`）：

```bash
npx @topmindspace/topmind-skills add topmindspace/topmind-skills --dest $HOME/.agents/skills
# 或
cp -R /path/to/topmind-skills/shared $HOME/.agents/skills/shared
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
| `--dest <dir>` | 安装目标 = host 的 skills 根 |
| `-g` / `--global` | dest → `$HOME/.claude/skills` |
| `--host codex` 等 | 换默认 dest |
| `--mode symlink` | 仅本地源；开发时热更新 |
| `--skill topmind` | 只装列出的 skill id |
| `--locale en-US` | locale overlay（当前未提供 overlay，回退中文正文） |

### Host destinations

| Host | 典型 dest | 写法 |
|------|-----------|------|
| Claude Code | `$HOME/.claude/skills` 或项目 `.claude/skills` | `-g` 或 `--dest ./.claude/skills` |
| Codex | `$HOME/.codex/skills` | `--host codex` |
| Hermes | `$HOME/.hermes/skills` | `--host hermes` |
| OpenCode | 项目 skills 路径 / config `skills.paths` | `--host opencode` 或见 `integrations/opencode/` |

无 skill 系统的 host：把 `topmind/SKILL.md` 当 system 片段粘贴，`shared/` 按链接手动附上。

---

## Update

安装后 dest 会写入 `{dest}/.topmind-skills-install.json`（记录 `source` / `path` / `version`）：

```bash
npx @topmindspace/topmind-skills update -g
# 或
node bin/install-skills.mjs update --dest <同一 dest>
# 社区 CLI
npx skills update -g -y
```

装完结构：

```text
{dest}/
├── topmind/SKILL.md      # 日常唯一入口
├── topmind-*/
├── shared/
├── topmind-pack.json
└── .topmind-skills-install.json
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
4. **只保留最近 2 个 GitHub Release**，更旧的 Release 与 tag 会被删除

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
- 安装器只写 `--dest`，不改其他目录。
