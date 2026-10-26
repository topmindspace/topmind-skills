# Changelog

topmind-skills 的版本记录。GitHub 只保留最近 2 个 Release，本文件是完整历史的入口；更早的版本见 git tag（`v4.13.x` 起）与 `git log`。

版本真源：`topmind-pack.json`。`package.json`、每个 `SKILL.md` 的 `metadata.version`、`evals/evals.json` 与之一致。

## 4.15.8 — 2026-10-26

- 明确写作包独立发布、Desktop/Obsidian 默认内置，其他 Agent 按需安装；发现宿主能力后路由，不凭核心目录误判。
- 区分 topmind-revise 与 topmind-format，平台排版优先宿主 render_article；持久写入与外部发布继续遵守原有边界。
- 同步统一版本与路由资源。

## 4.15.7 — 2026-10-26

- 精简入口、捕获与写作流程，按需加载共享参考；不再要求固定回执模板、无意义的分类访谈和重复扫描。
- 多意图任务按依赖连续完成；用户明确要求的记忆更新直接执行，主动建议仍待接受，不因内部技能切换重复确认。
- 对齐 Desktop / Obsidian 的分级写闸与技能资源来源，保留路径围栏、锁定内容快照及永久删除授权。
- 合并重复的授权/路由矩阵，补充自然语言任务与否定意图评估案例；不自动安装外部技能或发布内容。
- 修复手动草稿发布误用分支标签和 latest.json 标签错误；统一版本校验并增加可执行回归测试，草稿不触发旧正式版本清理。

## 4.15.6 — 2026-10-24

### 优化

- README（中文、英文）、`INSTALL.md`、`skills.md` 按用户视角重写：先讲安装和怎么用，去掉契约块和弃用名单，标题统一用中文。
- `README.zh-CN.md` 改为跳转页，中文说明只维护 `README.md` 一份。
- `topmind-loop/DESIGN.md` 的 UTR 命令数按 topmind 仓库 `TOOLS.md` 更新为 8 域 / 38 条。
- `topmind-memory` 周期反思的说明改写得更直白，语义不变。
- CHANGELOG 里只涉及发布流程与 CI 的条目压成一行。

## 4.15.5 — 2026-10-16

### 安装器

- 默认升级：包里版本更新（或已装版本缺失）就直接覆盖，不备份，打印 `Upgraded <skill> <旧> -> <新>`；同版本跳过，打印 `Already up to date`（`--force` 重装）；已装版本比包里新时拒绝降级，需 `--force`。
- symlink 模式：之前装过的同名 skill 普通目录（SKILL.md name 一致）直接换成软链；无关目录才需要 `--force`，并给一行提示。
- 新增 `tests/installer-upgrade.test.mjs`；README 中英文、INSTALL.md、帮助文本同步。

## 4.15.4 — 2026-10-16

### 优化

- 捕获说明不再写「待办一律 L1」。建议阶梯只留 `shared/auto-suggest.md`：材料 L0 落盘，显式行动语待办在 auto 下同轮写入，其余建议点头再落。
- `topmind-capture` 不再复制一套抓取 L1/L2/L3 表。`shared/long-url-capture.md` 标明那些是抓取档，不是建议阶梯。
- `skills.md` 的包内计数改回 10。公众号 `topmind-wechat-post` 仍在外部写作包，退役的 `topmind-wechat` 不进包。
- Router 的错误处理改指向 `shared/writeback-receipt.md`，不再留第二份清单。

## 4.15.3 — 2026-10-10

### 优化

- 安装文档 `INSTALL.md` 的技能目录站点链接指向通用页面。
- 其余为发布流程与 CI 调整，技能内容不变。

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
- 发布流程与 CI 调整（新增官方校验器检查每个技能）。
- 新增本 CHANGELOG，并加入 npm 包。

### 包体积

- `npm pack --dry-run`：4.15.1 为 tarball 159,771 B / 解包 460,031 B / 72 个文件；4.15.2 约为 tarball 92 kB / 解包 278 kB / 51 个文件（移除 `topmind-wechat`，新增 CHANGELOG）。
