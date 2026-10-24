# 安装与更新 topmind Skills

[简体中文](./README.md) · [English](./README.en.md) · [产品总览](https://github.com/topmindspace/topmind)

仓库：https://github.com/topmindspace/topmind-skills  
npm：[`@topmindspace/topmind-skills`](https://www.npmjs.com/package/@topmindspace/topmind-skills)（需要 Node.js 20.11+）  
装好后的日常入口：`topmind`

旧包 `@topmindspace/tms-skills` 已停止维护，请改用 `@topmindspace/topmind-skills`。

## 快速开始

```bash
# 推荐：装到全局，自动给检测到的助手建链接
npx @topmindspace/topmind-skills add topmindspace/topmind-skills -g

# 升级
npx @topmindspace/topmind-skills update -g

# 从 GitHub Release 安装（固定版本）
npx @topmindspace/topmind-skills add release:latest -g
```

已装 topmind Desktop 时，也可以在「设置 → 关于与更新」里对检测到的助手一键安装、升级或卸载。

## 装到了哪里

安装方式和社区工具 [`npx skills`](https://github.com/vercel-labs/skills) 一致：整包只存一份，其他助手通过软链接读同一份。

| 位置 | 路径 | 说明 |
|---|---|---|
| 主目录 | `<base>/.agents/skills/` | 整包只存这一份。全局安装时 `<base>` 是用户主目录，项目安装时是当前目录 |
| 直接读主目录的助手 | 同上 | Codex、Cursor、Gemini CLI 等在项目级直接读 `.agents/skills` |
| 有自己目录的助手 | `.claude/skills`、`.mimocode/skills`、`~/.codex/skills` 等 | 默认建相对软链接指向主目录；加 `--copy` 改为独立副本 |

全局安装后的样子：

```text
~/.agents/skills/
├── topmind/SKILL.md              ← 日常入口
├── topmind-*/
├── shared/
├── topmind-pack.json
└── .topmind-skills-install.json  ← 安装记录，update 时读取

~/.claude/skills/topmind    → ../../.agents/skills/topmind
~/.claude/skills/shared     → ../../.agents/skills/shared
```

技能文档里的 `../shared/*.md` 链接，无论从主目录还是从软链接进入，都指向同一份 `shared/`。

## 常用命令

```bash
# 只装给部分助手
npx @topmindspace/topmind-skills add topmindspace/topmind-skills -g -a claude-code -a codex

# 装到当前项目
npx @topmindspace/topmind-skills add topmindspace/topmind-skills -p

# 只装进一个目录（不建链接）
npx @topmindspace/topmind-skills add topmindspace/topmind-skills --dest ~/.claude/skills

# 先看会装什么，不实际写入
npx @topmindspace/topmind-skills add topmindspace/topmind-skills -g --dry-run

# 查看助手列表、安装路径；检查并修补断掉的软链接
npx @topmindspace/topmind-skills agents
npx @topmindspace/topmind-skills paths -g
npx @topmindspace/topmind-skills doctor --repair
```

升级规则：包里版本更新时直接覆盖，不留备份，打印 `Upgraded <技能> <旧> -> <新>`；版本相同跳过，打印 `Already up to date`（加 `--force` 重装）；已装版本比包里新时不降级，加 `--force` 才降级。

私有仓库：先 `export GH_TOKEN=…`（或 `GITHUB_TOKEN`）再执行 `add`。

## 社区 CLI npx skills

适合认 Agent Skills 目录结构的助手：

```bash
npx skills add topmindspace/topmind-skills -g -y
npx skills add topmindspace/topmind-skills -g -y -s topmind -s topmind-capture   # 只装部分技能
npx skills update -g -y
npx skills add topmindspace/topmind-skills -l                                     # 只列出技能
```

社区 CLI 不会装 `shared/`。缺了它：

- 路由分工表、写回回执、能力降级、自动建议等文档打不开，助手只能按 `SKILL.md` 正文判断，相近的说法更容易路由错；
- 用 `-s` 只装单个技能时同样如此，而且没有入口 `topmind`，多步请求拆不开；
- 助手不会报错，看起来装上了，需要自己补齐。

补齐方法：再用本包安装器装一次，然后检查：

```bash
npx @topmindspace/topmind-skills add topmindspace/topmind-skills -g
npx @topmindspace/topmind-skills doctor
```

社区 CLI 日志末尾如果出现 `Failed to install 9` 并指向 PromptScript，是那个助手不支持全局安装，可以忽略。

## 安装来源与参数

| 来源 | 含义 |
|---|---|
| `topmindspace/topmind-skills` | GitHub 仓库默认分支 |
| `topmindspace/topmind-skills@v4.15.5` | 指定 tag 或分支 |
| `https://github.com/topmindspace/topmind-skills.git` | 任意 git 地址 |
| `.` 或绝对路径 | 本地检出 |
| `release:latest` | GitHub Release 里的 `topmind-skills-*.zip` |

| 参数 | 含义 |
|---|---|
| `-g` / `--global` | 全局安装，主目录 `~/.agents/skills`，与 `npx skills -g` 相同 |
| `-p` / `--project` | 项目安装，主目录 `./.agents/skills` |
| `-a` / `--agent <id>` | 目标助手，可重复或用逗号分隔；`'*'` 表示全部 |
| `--copy` | 给有自己目录的助手复制独立副本，不建软链接 |
| `--dest <dir>` | 只装进这一个目录 |
| `--host <name>` | 旧用法，按助手名选默认目录，等同单目录安装 |
| `--mode copy\|symlink` | 单目录安装的方式，默认 copy |
| `--skill <id>` | 只装指定技能 |
| `--locale <code>` | 安装语言版本；目前只有中文，其他值回退中文 |
| `-n` / `--dry-run` | 只打印计划 |
| `--force` | 允许降级、同版本重装，或在 symlink 模式下替换无关的同名目录 |

### 支持的助手

| id | 项目路径 | 全局路径 | 方式 |
|---|---|---|---|
| `universal` | `.agents/skills` | `~/.agents/skills` | 主目录 |
| `claude-code` | `.claude/skills` | `~/.claude/skills` | 软链接 |
| `mimocode` | `.mimocode/skills` | `~/.config/mimocode/skills` | 软链接 |
| `codex` | `.agents/skills` | `~/.codex/skills` | 项目直接读主目录，全局软链接 |
| `cursor` | `.agents/skills` | `~/.cursor/skills` | 同上 |
| `gemini-cli` | `.agents/skills` | `~/.gemini/skills` | 同上 |
| `opencode` | `.agents/skills` | `~/.config/opencode/skills` | 同上 |
| `hermes` | `.hermes/skills` | `~/.hermes/skills` | 软链接 |
| `github-copilot` | `.agents/skills` | `~/.copilot/skills` | 项目直接读主目录，全局软链接 |

没有技能系统的助手：把 `topmind/SKILL.md` 当系统提示粘贴，`shared/` 里的文档按需附上。各助手的接入说明见 [`integrations/`](./integrations/)。

## Release 压缩包

Release 里的 `topmind-skills-<版本>.zip` 是多技能组合包：

```text
topmind-skills-<版本>/
├── SKILL.md              ← 包根入口，内容同 topmind
├── topmind/SKILL.md      ← 推荐的日常入口
├── topmind-*/
└── shared/
```

助手报 `SKILL.md not found` 时：在压缩包根找 `SKILL.md` 的，用包根入口；扫描 `*/SKILL.md` 的，把全部 `topmind*` 目录和 `shared/` 一起装。`skills.md` 是包索引，不能代替 `SKILL.md`。

## 发布（维护者）

版本以 `topmind-pack.json` 为准，`package.json`、各 `SKILL.md` 的 `metadata.version`、`evals/evals.json` 要与它一致。

```bash
npm test
npm run pack          # 可选：本地生成 dist/ 产物
git tag vX.Y.Z
git push origin main vX.Y.Z
```

推送 `v*` tag 后 CI 会：

1. 跑测试并打包；
2. 创建 GitHub Release（附 zip、tar.gz、manifest、SHA256SUMS、latest.json）；
3. 发布 npm 包（需要仓库 Secret `NPM_TOKEN`，缺少时这一步直接失败）；
4. 只保留最近 2 个 GitHub Release，git tag 保留。

公开仓库会被 [skills.sh](https://skills.sh) 自动收录，不需要另外登记。

## 安全

- 技能是 Markdown 指令，来路不明的 fork 先读再装。
- 不要把 API Key 写进技能文件。
- 安装器只写主目录和所选助手的技能目录，不动其他位置。
- 软链接断了（例如别的工具卸载后留下的）用 `doctor --repair` 修补，不要手动删整个技能目录。
