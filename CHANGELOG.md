# Changelog

topmind-skills 的版本记录。GitHub 只保留最近 2 个 Release，本文件是完整历史的入口；更早的版本见 git tag（`v4.13.x` 起）与 `git log`。

版本真源：`topmind-pack.json`。`package.json`、每个 `SKILL.md` 的 `metadata.version`、`evals/evals.json` 与之一致。

## 4.15.2 — 2026-10-08

### 不兼容变更（请先看）

- **移除 `topmind-wechat`。** 公众号能力统一由写作包 [topmind-writing-skills](https://github.com/topmindspace/topmind-writing-skills) 的 `topmind-wechat-post` 提供，两边不再各维护一份。
  - 已安装旧版的用户：请删除技能目录里的 `topmind-wechat/`（例如 `~/.agents/skills/topmind-wechat`、`~/.claude/skills/topmind-wechat`，或你的宿主技能目录下同名文件夹），再安装写作包的 `topmind-wechat-post`。两者触发词相同，同时存在会互相抢路由。
  - 本包安装器重装或 `update` 不会自动删除旧目录，需要手动删。
  - topmind Desktop 的「公众号创作」会优先找 `topmind-wechat-post`，找不到时仍认旧目录。
- **SKILL.md frontmatter 改为 Agent Skills 规范格式。** 顶层只保留 `name / description / license / compatibility / metadata`；`version / action_category / entrypoint / triggers / tags / author / homepage / updated / degradation` 移到 `metadata` 下，值一律为字符串，`triggers` 与 `tags` 改为逗号分隔。
  - 自己解析 SKILL.md 顶层字段的工具需要改为同时读 `metadata.*`。topmind Desktop 的解析器已同步优化（引擎仓库同批提交）；未升级的旧版 Desktop 会把这些技能都显示为默认分类，router 的入口标记也读不到，内容与路由不受影响。

### 优化

- 路由消歧真源 `shared/trigger-disambiguation.md`：公众号改指外部可选 `topmind-wechat-post`；新增写短文、发推、X 长文、研究报告、复盘与汇报材料、交接、配图与长图七类裁决行，覆盖 `topmind-x-article`、`topmind-briefs`、`topmind-viral-posts`、`topmind-cover`、`topmind-poster`、`topmind-presentation`、`topmind-handoff`；表头列出外部可选技能清单，并写明任何技能都不代用户发布。
- `topmind` router 与 `topmind-write` 的路由表同步：公众号、X 长文、短文、幻灯片、交接都标为外部可选，未安装时回退到 write 或在回执里说明。
- `topmind-pack.json`：去掉「markdown-only / pure-markdown」的说法，改为 `runtime: markdown-instructions` 并说明 npm 包附带 Node 安装器；`content_schema` 按规范拆成顶层字段与 `metadata` 字段；新增 `external_optional_skills`，记录外部技能与已移除的 `topmind-wechat`。
- 所有 `SKILL.md` 的 `metadata.homepage` 统一指向 topmind-skills 仓库。
- 安装器：安装外部技能仓库（没有 `topmind-pack.json` 的普通 Agent Skills 布局，例如写作包）时只装技能目录，不再把仓库根的 `evals/`、`LICENSE`、`README.md`、`INSTALL.md`、`install-targets/` 铺进宿主技能目录；只有 SKILL.md 链接了 `../shared/` 才带上 `shared/`；回执写到单独的 `.topmind-skills-install.<包名>.json`，不再覆盖 topmind 本包的回执。
- `INSTALL.md`：去掉旧包 `@topmindspace/tms-skills` 的提法；写明 `npx skills` 不装 `shared/` 的后果（子文档打不开、路由消歧表缺席、宿主不报错）与补救步骤。
- `evals/evals.json`：新增 8 条外部技能路由用例（公众号 2 条，含「不代发」；干货短文、引流短帖、X 长文、研究报告转幻灯片、交接、封面与长图各 1 条），字段 `external_skills` 由测试校验必须出现在消歧表里且不属于本包。
- CI：引擎交叉校验的 checkout 不再 `continue-on-error`，3 项交叉校验每次都跑；新增官方校验器 `agentskills validate`（skills-ref 0.1.1）逐个检查技能。
- Release：缺少 `NPM_TOKEN` 时「Publish to npm」步骤直接失败并给出提示，与其他 topmind 仓库一致，避免 Release 成功而 npm 未发布。
- 新增本 CHANGELOG，并加入 npm 包。

### 包体积

- `npm pack --dry-run`：4.15.1 为 tarball 159,771 B / 解包 460,031 B / 72 个文件；4.15.2 约为 tarball 92 kB / 解包 278 kB / 51 个文件（移除 `topmind-wechat`，新增 CHANGELOG）。
