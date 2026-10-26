# topmind Skills

把 topmind 的个人知识工作流装进你的 AI 助手（Claude Code、Codex、Cursor、OpenCode、Hermes 等）。你只管说「记一下」「整理本周」「写成稿」，助手按同一套约定把内容存进你自己的 `topmind-workspace` 文件夹。

[简体中文](README.md) · [English](README.en.md) · [安装说明](./INSTALL.md) · [更新记录](./CHANGELOG.md) · [产品总览](https://github.com/topmindspace/topmind) · [npm](https://www.npmjs.com/package/@topmindspace/topmind-skills)

## 安装

```bash
npx @topmindspace/topmind-skills add topmindspace/topmind-skills -g
```

装好后对助手说「topmind」或直接说要做的事即可。升级用：

```bash
npx @topmindspace/topmind-skills update -g
```

- 包里版本更新时直接覆盖，打印 `Upgraded <技能> <旧> -> <新>`；版本相同打印 `Already up to date`；已装版本更新时不降级，要降级加 `--force`。
- 只装给部分助手：在 `add` 后面加 `-a claude-code -a codex`。
- 社区 CLI `npx skills add topmindspace/topmind-skills -g -y` 也能装，但不带 `shared/` 目录，部分规则会读不到，装完要补一步，见 [INSTALL.md](./INSTALL.md#社区-cli-npx-skills)。
- 固定版本或离线安装、项目级安装、各助手的目录位置，都在 [INSTALL.md](./INSTALL.md)。

## 怎么用

日常入口只暴露 `topmind` 一个。你说的话由它判断交给哪个技能，你不用记子技能的名字。

| 你说 | 交给 | 结果 |
|---|---|---|
| 「记一下这个链接」「收进来」 | `topmind-capture` | 存进动态周期本、专题或 Inbox，回执告诉你放在哪 |
| 「记一下要做 X」「别忘了 X」 | `topmind-capture` | 材料落盘，待办写进 `memory/todo.md` |
| 「有什么要做的」 | `topmind` | 列出 `memory/todo.md` 里没做完的事 |
| 「整理本周」「总结一下这个专题」 | `topmind-organize` | 理顺本周动态，或在专题里整理、对比、提炼 |
| 「写成稿」「润色一下」 | `topmind-write` | 起草或改稿，放到交付目录或专题里 |
| 「记住我…」「更新我的情况」 | `topmind-memory` | 更新 `memory/profile.md` 或周期反思 |
| 「体检一下」「doctor」 | `topmind-maintain` | 检查目录结构和配置，做可回退的清理 |
| 「跑一遍 loop」 | `topmind-loop` | 逐个专题巡检，中断后能接着跑 |
| 「同步微信读书」 | `topmind-weread` | 可选：把划线和想法同步到专题 |
| 「发推」「归档我的推文」 | `topmind-x` | 可选：X 归档、搜索与发帖 |
| 「记一笔，午饭 35」 | `topmind-ledger` | 可选：记账到 `memory/ledgers/` |

本包共 10 个技能：入口 `topmind`、6 个动作技能、2 个可选连接器、1 个可选记账。清单见 [skills.md](./skills.md)。

### 配套技能（单独安装）

下面这些不随本包发布，装了以后 `topmind` 会把对应请求转过去，没装时退回 `topmind-write` 或在回执里说明。

| 需求 | 技能 | 仓库 |
|---|---|---|
| 公众号、X 长文、短文、段子、封面、长图 | `topmind-wechat-post` 等 8 个写作技能 | [topmind-writing-skills](https://github.com/topmindspace/topmind-writing-skills) |
| AI 行业动态、读论文、核实数字 | `topmind-research` | [topmind-research](https://github.com/topmindspace/topmind-research) |
| 把材料做成可翻页 HTML 和 PPTX | `topmind-presentation` | [topmind-presentation](https://github.com/topmindspace/topmind-presentation) |
| 跨工具交接记忆 | `topmind-handoff` | [topmind-handoff](https://github.com/topmindspace/topmind-handoff) |

各技能怎么分工，见 [`shared/trigger-disambiguation.md`](./shared/trigger-disambiguation.md)。

## 内容存在哪

所有内容都是你本机 `topmind-workspace` 里的 Markdown 文件，用 Obsidian 或任何编辑器都能打开。

```text
topmind-workspace/
├── topmind.yaml          # 工作区配置
├── memory/               # 我的情况、周期反思、待办、账本
├── 00-Inbox/             # 一时分不了类的先放这里
├── 10-动态/              # 按周的动态周期本
├── …                     # 其他大类，按模板生成，可以改名、隐藏、新增
├── 88-交付/              # 写好的稿件
└── 99-归档/
```

- 一个大类下面，同一主题的笔记多了会自然聚成专题文件夹 `{大类}/{YYYY-主题}/`；没有专题时笔记直接放在大类根。
- 大类不重叠、专题自然形成、动态平铺、Inbox 约 30 天清一次、参考资料单独放、大类名称保持稳定。完整规则见 [`shared/project-model-brief.md`](./shared/project-model-brief.md)。

## 几条约定

- **先存下来再说**：分类不确定时先放 Inbox，不因为分类拦住保存。
- **每次写入都有回执**：写了哪个文件、为什么放这里、下一步可以做什么。
- **保存设置**：`writeback_mode: auto | confirm`。auto 直接写并给回执；confirm 内容编辑也直接写，仅删除/归档进入审阅。明确要求的建专题、记忆更新直接执行；推测的建议需接受，规则见 [`shared/auto-suggest.md`](./shared/auto-suggest.md)。
- **文件是唯一的数据来源**：助手自己的会话状态不得成为 topmind 内容真源。
- **不要求 Desktop，UTR 可选**：topmind Desktop 和 UTR 命令行都不是必需的，没有时用助手自带的文件工具，遵守同一套约定。
- **不代发**：任何技能都只起草，发布由你操作。

## 给维护者

- 版本和技能清单以 [`topmind-pack.json`](./topmind-pack.json) 为准（`npm run versions` 查看），各 `SKILL.md` 的 `metadata.version` 必须一致。
- `SKILL.md` frontmatter 只用 Agent Skills 规范字段（`name`、`description`、`license`、`compatibility`、`metadata`、`allowed-tools`），自定义字段放在 `metadata` 下、值为字符串。CI 用 `agentskills validate` 逐个检查。
- 本地测试：`npm test`。发布流程见 [INSTALL.md](./INSTALL.md#发布维护者)。

```text
topmind-skills/
├── topmind/              # 日常入口（路由）
├── topmind-capture/ … topmind-loop/   # 6 个动作技能
├── topmind-weread/  topmind-x/        # 可选连接器
├── topmind-ledger/       # 可选记账
├── shared/               # 各技能共用的规则文档
├── install-targets/      # 各助手的安装形状
├── integrations/         # Codex、Hermes、OpenCode 接入说明
├── evals/                # 路由评测
├── bin/install-skills.mjs
└── topmind-pack.json
```

## 许可证

MIT
