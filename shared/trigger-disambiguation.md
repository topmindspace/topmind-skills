# Trigger Disambiguation（路由消歧真源）

> Router（`topmind`）与各子 skill 的「When NOT」必须与本表一致。  
> 子 skill **不得**自动链式 dispatch 下一 skill；「下一步」仅用户面建议。  
> 外部可选技能不随本包发布：仅在宿主已安装时按表路由；未安装按该行写明的回退处理，回执可提示可选安装，不报错。当前清单：
> - 写作包 topmind-writing-skills：`topmind-wechat-post`（公众号）、`topmind-x-article`（X 长文）、`topmind-briefs`（干货短文）、`topmind-viral-posts`（引流短帖）、`topmind-cover`（封面 / 配图）、`topmind-poster`（长图 / 海报）
> - 独立技能：`topmind-research`（对外检索与研究报告）、`topmind-presentation`（HTML / PPTX 演示稿）、`topmind-handoff`（跨工具交接包）
> - 第三方：`last30days`、`TopStream每日精选`
>
> 任何技能都不代用户发布：写稿技能只出稿；要发出去走对应连接器（如 `topmind-x`），并且每次都须用户确认。

## 碰撞词裁决

| 用户说 | 撞到的 skills | 裁决 |
|--------|--------------|------|
| 总结要点 | organize vs memory | 默认 → `topmind-organize`。仅「更新我的情况 / 加到专题记忆 / 沉淀到记忆」→ memory |
| 沉淀 | capture vs memory | 默认 → `topmind-capture`。仅「沉淀成稳定结论 / 更新我的情况」→ memory |
| **记一下 / Note it** | capture 主入口 | **完整捕获**（笔记 / 链接 / 附件）→ `topmind-capture` |
| **记下 / Log it** | capture（追加） | **写入当前周期本**（动态追加，同文件续写）→ `topmind-capture`，默认平铺到当前周期；不弹分类访谈 |
| 记一下要做 X / 别忘了 X | capture vs todo | → `topmind-capture`（材料落盘）+ 待办写入/建议 `memory/todo.md`（见 `auto-suggest.md`） |
| 待办 / 有什么要做的 | router 直达 | 读 `memory/todo.md` 活跃项；不新建概念、不进 organize |
| X 做完了 / 这条不用了 | todo vs organize | 清单项 → 勾掉/归档 `memory/todo.md`；整周事项状态 → organize「整理本周」 |
| 体检 / 检查 | maintain vs loop | 「快速体检 / 体检 / 检查 / doctor」→ maintain。「整体体检 / 全面检查 / 巡检 / audit / review」→ loop |
| 审计 / audit | maintain vs loop | 默认 → loop。maintain 用 doctor / 诊断 / 快速体检 |
| 整理 | organize | 「整理 inbox」→ organize + `plan-inbox-routing`。其它 → organize |
| 复盘 | organize vs loop | 「复盘」→ loop。「复盘要点成笔记」→ organize |
| 归档 | capture vs maintain | 「归档材料」→ capture。「归档专题 / archive topic」→ maintain |
| 笔记 / note | capture vs write | 未限定 → capture。「写作 / 起草 / 续写」→ write |
| 记账 / 记一笔 / 花了 / 存入 | ledger vs capture | 「记账 / 记一笔 / 花了 / 存入 / 查看账单 / 账户余额」→ `topmind-ledger`（记忆平面账本）。「记一下」仍 → capture |
| 研究 / 分析 / 对比 | organize vs topmind-research（外部可选） | 对象是工作区里已存的笔记、专题内材料 → `topmind-organize`。需要对外检索一手资料（论文、技术报告、官方公告、模型或产品横向对比）、AI 前沿深挖 → `topmind-research`（analyze）；未安装 → `topmind-organize`「研究分析」 |
| AI 动态 / 大厂动态 / AI 周报 / 最近有什么新的 | topmind-research vs last30days vs TopStream每日精选（均外部可选） | 官方公告、技术报告、论文的周度汇总 → `topmind-research`（collect）。社区讨论与口碑（X、Reddit、HN 等）→ `last30days`。每日精选例行 → `TopStream每日精选`。对应技能未安装 → `topmind-organize`（只用工作区已存材料，回执注明）。「整理本周 / 理顺本周动态」指工作区动态类别，仍 → organize「整理本周」 |
| 读论文 / 论文解读 | topmind-research vs topmind-briefs（均外部可选） | 想弄懂内容、要带来源的研究报告 → `topmind-research`（analyze）；未安装 → `topmind-organize`「研究分析」。要直接出一篇短稿发布 → `topmind-briefs`（可附 research 产出的已核验事实表）；未安装 → `topmind-write` |
| 公众号 / 微信排版 / 定稿发公众号 | topmind-wechat-post（外部可选）vs write | 「公众号 / 微信排版 / 公众号定稿 / 发公众号」→ `topmind-wechat-post`（交付包、质量三关、微信排版；只出稿，不代发）；未安装 → `topmind-write`。通用「写一篇」仍 → `topmind-write`。本包 4.15.2 起不再自带 `topmind-wechat` |
| 写短文 / 快讯 / 新品速递 | topmind-briefs vs topmind-viral-posts（均外部可选） | 信息密度型（数据、榜单、发布、论文要点）→ `topmind-briefs`；引流互动型（段子、钩子、涨粉）→ `topmind-viral-posts`；均未安装 → `topmind-write` |
| 发推 / 推文 | topmind-x（连接器）vs topmind-viral-posts / topmind-briefs（外部可选） | 写稿 → `topmind-viral-posts` / `topmind-briefs`（未安装 → `topmind-write`）；发出去 → `topmind-x`，且须用户确认；归档 / 搜索推文 → `topmind-x` |
| X 长文 / 推特长文 | topmind-x-article（外部可选）vs write vs x | 写 X Articles 长文与一键复制 → `topmind-x-article`；未安装 → `topmind-write`。短帖不走 x-article |
| 研究报告 / 调研报告 | organize vs topmind-research vs topmind-presentation | 要找证据、核事实 → `topmind-research`；对工作区已有材料做分析 → `topmind-organize`；要做成可翻页 HTML / PPTX → `topmind-presentation`。「做一份 X 的研究报告」先 research，回执建议 presentation，不自动链式；对应技能未安装 → organize / write |
| 复盘 / 汇报材料 | loop vs organize vs topmind-presentation | 工作区巡检 → loop；本周动态 → organize「整理本周」；要出汇报幻灯片 → `topmind-presentation`（未安装 → `topmind-write`） |
| 交接 / 导出记忆 / 记忆同步 | topmind-handoff（外部可选）vs memory vs write | 跨工具打包或接收交接包 → `topmind-handoff`；更新本工作区「我的情况」→ `topmind-memory`；导出稿件 → `topmind-write`。handoff 未安装 → 回执说明，不自动打包 |
| 配图 / 封面 / 长图 / 海报 | topmind-cover vs topmind-poster vs topmind-presentation（均外部可选） | 文章头图、封面、单张配图 → `topmind-cover`；长图、信息海报、多段竖版 → `topmind-poster`；可翻页演示 → `topmind-presentation`；均未安装 → 回执说明，不硬生成 |

**原则**：动作动词定 action；修饰词定 confidence。无法判定 → capture（先存后整）。

## 写回边界（与复利纪律对齐）

| 动作 | 默认写什么 | 禁止 |
|------|------------|------|
| capture | 材料笔记；显式行动语可写/建议 `memory/todo.md` | 改 `topic.md`；自动 organize；静默写 memory/profile 或 memory/topics |
| organize | 专题根综合/结构笔记（留痕）；L1 待办/记忆/专题建议 | 自动写稳定记忆；建 `INDEX.md` / entities 树 |
| memory | 仅 confirmed stable → `memory/profile.md` 或 `memory/periodic/`（用户明说才写 `memory/topics/`） | 因 capture/整理顺手刷写；把 `topic.md` 当记忆默认落点 |
| todo（卫星） | `memory/todo.md` checklist | 新建顶层 `todo/`；当第六用户概念 |
| write | 稿件 / delivery | 为「补结构」空建 `topic.md` |
| loop | 状态 / 可逆修复 | 代写记忆；建硬索引 |
| ledger | `{memory.dir}/ledgers/` 追加一行 | 改 `topic.md`；发明 ClassFund/Giggs/Mom；当第六用户概念 |
| topmind-research（外部可选） | 研究报告、周报、已核验事实表，按 `writeback-receipt.md` 落专题或 Inbox（frontmatter `source_type: ai-derived`） | 自动写记忆；自动改它自带的 `config/sources.yaml`；未经用户点名自动深挖；自动链式 briefs / write |

## 多意图顺序

| 意图组合 | 裁决 |
|---------|------|
| capture + organize | 先 capture，回执建议 organize（不自动链式） |
| capture + memory | 先 capture，回执建议 memory（须用户再确认才写 profile / periodic） |
| organize + write | 先 organize（落盘综合），再 write |
| organize + memory | 先 organize 候选与综合笔记，**用户接受建议后再** memory |
| write + memory | 先 write，回执建议 memory |
| research + write | 先 research 出报告与事实表，回执建议 briefs / write（不自动链式） |
| research + memory | 先 research 落盘，回执建议 memory（须用户再确认才写） |
| 整理 inbox | organize + plan-inbox-routing（不是 maintain/loop） |
| 清理工作区 | maintain |

三个以上意图：拆成顺序步骤，每步回执。

## Action unsure

- 记账 / 记一笔 / 花了 / 存入 / 查看账单 / 账户余额 → ledger  
- 内容动词（写/存/记一下）且无修复/巡检 → capture  
- 修复 / 清理 / 重建 → maintain  
- 巡检 / 整体 / 断点 → loop  
- 整理 / 分析 / 总结 → organize  
- 写 / 发布 / 出稿 → write  
- 记忆 / 更新我的情况 / 周期反思 → memory  
- 仅类别名 → capture 到该类别根  
- 全不像 → capture 到 Inbox（buffer）  
