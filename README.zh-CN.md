# topmind Skills

可移植 AI 技能包：在 Claude Code / Codex / OpenCode / Hermes 等 Host 上使用同一套内容约定。

[简体中文](README.md) · [English](README.en.md) · [产品总览](https://github.com/topmindspace/topmind) · [安装与发布](./INSTALL.md) · [npm](https://www.npmjs.com/package/@topmindspace/topmind-skills)

```bash
# 1) npm（推荐 · pack-aware · 含 shared/ · canonical .agents + 多智能体）
npx @topmindspace/topmind-skills add topmindspace/topmind-skills -g
# 只装给部分智能体
npx @topmindspace/topmind-skills add topmindspace/topmind-skills -g -a claude-code -a mimocode
# 升级
npx @topmindspace/topmind-skills update -g

# 2) 社区 CLI（快速试用；不含 shared/ — 见 INSTALL.md）
npx skills add topmindspace/topmind-skills -g -y

# 3) Pack-aware 安装器（源码仓内）
npm run add -- topmindspace/topmind-skills -g
npm run update -- -g

# 4) 从 GitHub Release 装（离线/固定版本）
node bin/install-skills.mjs add release:latest -g

# 查看矩阵 / 修断链
node bin/install-skills.mjs agents
node bin/install-skills.mjs doctor --repair
```

安装模型：**canonical `.agents/skills` 一份真身** + 私有目录（Claude Code / MiMoCode…）相对软链；与 [`npx skills`](https://github.com/vercel-labs/skills) 一致。详见 [INSTALL.md](./INSTALL.md)。

**版本与清单真源：** [`topmind-pack.json`](./topmind-pack.json)（`npm run versions`）。  
各 `SKILL.md` 的 `metadata.version` **必须**等于 pack 版本。

---

## 结构

```text
topmind-skills/              # pack 根 = 仓库根
├── topmind/                 # 唯一日常入口（router）
├── topmind-capture|organize|write|memory|maintain|loop/
├── topmind-weread|x/        # 可选连接器
├── topmind-ledger/          # 可选记账（记忆平面账本）
├── shared/                  # 写回回执 · 降级 · 自动建议 · 捕获 …
├── install-targets/         # Host 安装形状（claude-code / codex / mimocode / …）
├── evals/evals.json
├── bin/install-skills.mjs   # pack-aware + agent matrix 安装器
├── scripts/build-pack.mjs
└── topmind-pack.json        # 版本真源
```

| 类型 | 模块 |
|------|------|
| **入口** | `topmind` only |
| **动作** | capture · organize · write · memory · maintain · loop |
| **连接器** | weread · x（可选） |
| **可选** | ledger（记账 · 记忆平面账本） |
| **外部可选（不随包）** | 公众号 `topmind-wechat-post` 等写作技能（topmind-writing-skills）· `topmind-research` · `topmind-presentation` · `topmind-handoff`；路由见 `shared/trigger-disambiguation.md` |

> 子 skill 触发词只服务 Host 路由，**不是**第二前台入口。

---

## 产品契约

```text
User experience:     capture-first
Data organization:   category-first + topic-emerges
Content truth:       topmind-workspace
Capability model:    action-first
Save settings:       auto | confirm
Safety model:        reversible by default
Suggestions:         L0 auto-land · L1 auto-prepare · L2 confirm-apply — shared/auto-suggest.md
```

日常入口只暴露 `topmind`。Host 会话状态不得成为 topmind 内容真源。  
本 pack **不要求 Desktop**。**UTR 可选** — 没有 UTR 时用 Host 文件工具。

工作流：`收进来 -> 继续做 -> 交付/沉淀 -> 找回/调整`  
（用户说「收一下」「记一下」「整理」「写成稿」「跑一遍 loop」— router 推断类别 / 专题 / 动作。）

**想记就记 / 随用随记**：捕获零提问落盘（L0）；分类备选 / 待办 / 记忆候选默认 L1 准备——显式行动语待办在 auto 下同轮写入 `memory/todo.md`，其余建议点头再落（[`shared/auto-suggest.md`](./shared/auto-suggest.md)）。

---

## SKILL.md frontmatter

```yaml
---
name: <kebab-case-id>           # 必填；与目录名一致
description: >-                  # 必填；做什么 + Use when + Do NOT use
  …
license: MIT
compatibility: …                # 可选；运行环境说明（≤500 字符）
metadata:                       # Agent Skills 规范：自定义字段一律放这里，值为字符串
  version: "<pack.version>"     # 必填；= topmind-pack.json version
  action_category: "capture"    # skill 分类（不是用户笔记的 category）
  entrypoint: "false"           # 只有 topmind router 是 "true"
  triggers: "记一下, 收进, capture"   # 逗号分隔
  tags: "capture, inbox"
  author: "TopMindSpace"
  homepage: "https://github.com/topmindspace/topmind-skills"
  updated: "YYYY-MM-DD"
  degradation: "../shared/capability-degradation.md"
---
```

顶层只允许 `name / description / license / compatibility / metadata / allowed-tools`，CI 用官方校验器 `agentskills validate`（skills-ref）逐个检查；字段与版本由 `tests/package-manifest.test.mjs` 强制校验。topmind Desktop 的解析器同时认顶层旧写法与 `metadata.*`。一个 pack JSON（[`topmind-pack.json`](./topmind-pack.json)），无 per-skill 第二清单。

---

## 工作区契约

```text
{workspace-root}/
├── topmind.yaml                # contract v4
├── memory/                     # profile.md · periodic/ · topics/ · todo.md · 可选 ledgers/
├── .topmind/                   # rebuildable machine state
├── 00-Inbox/                   # role: buffer (live dir name)
├── 10-动态/ …                  # categories (template-driven)
├── 88-交付/ or 88-Delivery/     # role: delivery
└── 99-归档/ or 99-Archive/     # role: system
```

专题：

```text
{category}/{YYYY-theme}/
├── topic.md                 # optional
├── *.md                     # notes at topic root
└── images/                  # optional
```

尚无专题时，散篇放在 `{category}/{note}.md`。

**不要创建（已废弃）：** 默认 `outline.md` / `setting.md` / `style.md`；`project_type` frontmatter；专题内嵌套 `notes/` 或 `outputs/`；顶层 `projects/`；`YYYY-类型-项目名` 命名。

**类别：** 运行时发现 `{NN-Name}/` + `topmind.yaml` v4（`categories.extensions` / `categories.overrides` 含 `hidden`）。共享解析器：引擎 `lib/workspace-model.mjs`。优先按角色路由，不要写死 `10-` / `20-` 编号。

不要硬编码绝对路径 — 从 Host 推断 `workspace_root`，或向用户询问。

### 6 条核心规约

1. **大类不重叠**  
2. **专题自然涌现**  
3. **动态类特殊**（默认平铺）  
4. **兜底类清理**（约 30 天）  
5. **参考资料定位**  
6. **大类命名稳定**（rename via migration）  

完整规则：[`shared/project-model-brief.md`](./shared/project-model-brief.md)。

---

## 行为规则

- 先捕获；不要因为分类不完美而挡住简单保存  
- 信号足够强时自动路由；否则走 **role:buffer**（现场 Inbox 目录，不要只写死 `00-Inbox/`）  
- 专题不清时，散篇放在大类根  
- 每次写入返回回执（路径、路由原因、下一步）  
- `source_type`: `user-original` | `external-capture` | `ai-derived`  
- UTR 可选 — Host 文件工具遵守同一契约  
- 保存设置协议：`writeback_mode: auto | confirm`  
- locked：auto 下可编辑（任务级首写快照）；永久删 locked/core 仅用户  
- 本 pack 不要求 Desktop  
- **复合纪律（不改结构）：** organize 把综合写回磁盘；write 先读可选 `topic.md`；memory 仅在明确确认后写；capture 从不改 `topic.md`；**不要**硬造 `INDEX.md` / 平行 wiki 树（见 `shared/project-model-brief.md`）  

---

## 安装目标

已打包的 skill 目录（7 个核心 + 2 个可选连接器 + 可选记账；4.15.2 起公众号改由写作包的 `topmind-wechat-post` 提供）可以符号链接或复制到 Claude Code、Codex、OpenCode、Hermes 等。  
优先使用 npm / pack-aware 安装器，保证 `shared/` 与 `topmind-pack.json` 完整 — 见 [`INSTALL.md`](./INSTALL.md)。

```bash
npx @topmindspace/topmind-skills add topmindspace/topmind-skills -g
```

Host 适配器**不得**改变内容真源、新增并列日常入口，或把内容存进 agent 运行态。见 [`shared/capability-degradation.md`](./shared/capability-degradation.md)。
