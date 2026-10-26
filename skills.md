# topmind Skills 包索引

日常入口只有 `topmind`。包内另有 6 个动作技能、2 个可选连接器、1 个可选记账，连入口共 10 个目录。公众号技能 `topmind-wechat-post` 在外部写作包 [topmind-writing-skills](https://github.com/topmindspace/topmind-writing-skills)，不计入本包。

版本以 [`topmind-pack.json`](./topmind-pack.json) 为准（`npm run versions`）。使用说明见 [README](./README.md)（[English](./README.en.md)），安装见 [INSTALL.md](./INSTALL.md)。

## 技能清单

| # | 技能 | 类型 | 常见说法 | 做什么 |
|---|---|---|---|---|
| 1 | `topmind` | 入口 | topmind、待办、意图不明确或一次说了几件事 | 判断你要做什么，交给对应技能；多件事拆成几步 |
| 2 | `topmind-capture` | 动作 | 记一下、收进、保存链接 | 速记、链接、文件落盘，行动语提取待办 |
| 3 | `topmind-organize` | 动作 | 整理本周、整理、总结、对比 | 理顺动态，在专题内整理、研究、分析，分流 Inbox |
| 4 | `topmind-write` | 动作 | 写、起草、润色、出稿 | 依据专题与资料起草、改稿、交付 |
| 5 | `topmind-memory` | 动作 | 记住这个、更新我的情况 | 维护 `memory/profile.md` 与周期反思 |
| 6 | `topmind-maintain` | 动作 | 体检、doctor、清理 | 目录与配置的确定性检查和可回退清理 |
| 7 | `topmind-loop` | 动作 | 跑一遍 loop、巡检 | 全工作区语义巡检，可中断续跑 |
| 8 | `topmind-weread` | 连接器（可选） | 微信读书、同步划线 | 同步划线、想法与阅读统计到专题 |
| 9 | `topmind-x` | 连接器（可选） | 发推、推特、x.com | X 归档、搜索与发帖 |
| 10 | `topmind-ledger` | 记账（可选） | 记账、记一笔、花了、存入 | 默认个人账本，可自建账本与分类，写入 `memory/ledgers/` |

旧技能 `topmind-wechat` 已在 4.15.2 移出本包，由写作包的 `topmind-wechat-post` 接替。已装旧目录的请删除，否则两者会抢同一批说法。

## 核心约定

1. 只向用户推荐 `topmind` 一个入口，子技能的触发词只服务助手路由。
2. 按需加载：先读技能名和描述，触发后读 `SKILL.md`，需要细节时再读 `shared/` 和 `references/`。
3. 文件就是数据来源，不依赖数据库或助手会话状态。
4. 遵守 6 条工作区规约，见 [`shared/project-model-brief.md`](./shared/project-model-brief.md)。
5. 自动建议分级见 [`shared/auto-suggest.md`](./shared/auto-suggest.md)：材料直接落盘；明确说了要做的事，auto 模式下同轮写入待办；其余建议等你点头；明确请求沿用授权，额外记忆/专题建议需接受，删档按写闸确认。待办放在 `memory/todo.md`。
