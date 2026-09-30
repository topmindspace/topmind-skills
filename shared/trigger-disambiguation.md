# Trigger Disambiguation（路由消歧真源）

> Router（`topmind`）与各子 skill 的「When NOT」必须与本表一致。  
> 子 skill **不得**自动链式 dispatch 下一 skill；「下一步」仅用户面建议。

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
| 公众号 / 微信排版 | wechat vs write | 「公众号 / 微信排版 / 公众号定稿 / 发公众号」→ `topmind-wechat`。通用「写一篇」仍 → `topmind-write` |

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

## 多意图顺序

| 意图组合 | 裁决 |
|---------|------|
| capture + organize | 先 capture，回执建议 organize（不自动链式） |
| capture + memory | 先 capture，回执建议 memory（须用户再确认才写 profile / periodic） |
| organize + write | 先 organize（落盘综合），再 write |
| organize + memory | 先 organize 候选与综合笔记，**用户接受建议后再** memory |
| write + memory | 先 write，回执建议 memory |
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
