# Auto-Suggest Ladder（自动建议阶梯 · Skills 共享）

> 产品北极星：**记下来尽可能简单；系统默默准备建议；你点头后再沉淀；文件永远是你的。**  
> 与 Desktop「自动准备建议（默认开）· 高影响确认后执行」同一语义。Host 无 Desktop 时由 Agent 自己扮演建议生成器。  
> 真源对齐：`docs/ARCHITECTURE-RESET.md` §D · `PRODUCT-BOUNDARIES.md`。

用户**不需要**知道内部模块名，也**不需要**在落盘前做分类/记忆/待办的多选题。Agent 默认走阶梯，只在 L2 停下来问一句。

## 三级阶梯

```text
L0 自动（无询问，直接做）
   路由落盘 + 路径回执 · frontmatter/provenance · 周期本 append
   —— 「想记就记 / 随用随记」的主路径

L1 自动准备建议（默认生成并展示；一键接受；不静默写）
   分类备选 · 待办提取 · 记忆候选 · 专题升级 · 整理本周下一步
   —— 「自动分类或分类建议 / 提取 todo / 记忆机制」的主路径

L2 确认后执行（高影响；一句话确认即可）
   写 memory/profile.md 或 memory/topics/ · 创建/合并专题
   删除/归档（confirm 模式）· 批量改待办状态 · 永久删
```

**纪律**：

1. L1 **只是建议卡片/回执附言**，不改内容真源；用户说「好 / 记上 / 移过去」即接受。
2. L2 **不问细节**，只问「要不要写」；接受后一次做完并给路径回执。
3. **禁止**为了「更智能」把 L2 静默升成 L0。**禁止**把 L1 做成一长串选择题。
4. 子 skill **不**自动 dispatch 下一 skill；L1 的「下一步」是用户面建议，不是链式调用。
5. 建议输出语言：用户本轮要求 → 宿主 UI → 工作区 locale（见 [`output-language.md`](./output-language.md)）。

## L1 建议类型（按触发）

| 建议 | 何时准备 | 接受后写到 | 拒绝 |
|------|----------|------------|------|
| **分类备选** | capture 低信心类别 | 用户点名的大类 / 真实目录名 | 留在 Inbox |
| **待办提取** | 正文含行动语（要做/记得/别忘/截止/待办/todo/need to） | `memory/todo.md`（语义平面卫星） | 只留周期本原文 |
| **记忆候选** | 稳定个人信息（偏好/目标/关系/进行中/周期洞察） | `memory/profile.md` 或 `memory/periodic/` | 不写 memory |
| **专题升级** | 同主题反复出现（≥2 次）且尚无专题 | 内容大类 `{YYYY-主题}/` | 流水永远只是流水 |
| **整理下一步** | capture 完成 / 周期本变脏 | 用户说「整理」再走 organize | 无 |

### 待办提取细则（todo satellite）

`memory/todo.md` 是**语义平面卫星**（与 `todo-engine` 同契约），**不是**第 6 个用户概念。用户话术仍是「记一下 / 待办」。

```text
显式行动语（「记一下要做 X」「别忘了 X」「待办：X」）
  → L0：材料照常落盘
  → L0/L1：同轮把 X 写入 memory/todo.md（writeback auto 可直接写 + 回执；
           confirm 则建议后写）。语义重复按文本去重。

隐含行动语（「周三截止」「下周要交」）
  → L1：建议提取 1–N 条，用户点头再写

「有什么要做的 / 待办 / todo list」
  → 读 memory/todo.md 活跃项；不新建概念

「X 做完了 / 这条不用了」
  → 勾掉/归档对应 todo（可恢复）；同时可在周期本留一行状态（organize 语义）
```

Host 能力映射：

| 能力 | Desktop | UTR | 纯 Host Agent |
|------|---------|-----|---------------|
| 提取 | `add_todo` · `todo_maintain` | `memory.add-todo` | 读活动窗口 → 识别行动语 → 写 checklist |
| 维护 | `toggle_todo` · `update_todo` · `set_todo_due` · `delete_todo` · `maintainTodos` | `memory.toggle-todo` | 对照周期本与 todo.md 做 diff 建议 |
| 列表 | `list_todos` · Todo 面板 | `memory.list-todos` | 读 `memory/todo.md` 活跃段 |
| 动态查询 | `list_recent_stream` | `workspace-read.list-recent-captures` | 读最近周期本日段 |
| 记忆查询 | `list_recent_memories` | `memory.list-profile` 等 | 读 `memory/` 活跃段（勿整库倾倒） |
| 分类/专题建议 | `topic_classify`（确认后 `create_topic`） | 文件工具 + role 路由 | 按 role + 内容性质给最多 3 候选 |
| 记忆建议 | `memory_organize`（append/update/retire 建议） | `memory.append-profile` 等（确认后） | 识别稳定事实 → L1 候选 |

写入格式：markdown checklist（`- [ ]` / `- [x]`），可带截止日期；保持简单可编辑。详见引擎 `lib/todo-engine.mjs`。

### 分类备选细则

高信心 → 直接落盘（L0）。低信心 → 仍落 **role:buffer**（L0 不丢数据），回执附 L1：

```text
已收进 Inbox。更像是：① 20-研究  ② 10-动态  —— 说「移到研究」即可。
```

**不要**弹出多选表单；最多 3 个候选，按角色 + 内容性质排序。

### 记忆候选细则

- **写**仍属 L2（须用户确认或明说「记住 / 更新我的情况」）。
- **准备**属 L1：capture / organize / 整理本周 之后，识别稳定事实就附一句候选。
- 禁止因剪藏/导入自动改 `memory/profile.md` 或 `memory/topics/`（见 [`trigger-disambiguation.md`](./trigger-disambiguation.md)）。

## 回执中的建议（统一形状）

```text
已记到：10-动态 → 本周动态
位置：10-动态/2026/2026-W39.md
——
顺手建议（说一声即可）：
 · 待办：周三前交报告 → 记入清单？
 · 更像 20-研究？可移过去
 · 「换工作了」可进「我的情况」
```

一条回执最多 3 条建议；超过的丢弃或留给 loop。建议可整体忽略，不影响 L0 结果。

## 与保存设置

| writeback | L0 | L1 | L2 |
|-----------|----|----|-----|
| `auto` | 直接写 | **显式行动语的待办可直接写** + 回执；其余仍建议 | 仍须确认（memory / 删档 / 建专题） |
| `confirm` | 内容直接写（分级） | 全部建议后写 | 确认后写 |

高影响（locked 覆盖、删/归档、永久删）永远走写闸，与本阶梯无关（见 [`writeback-receipt.md`](./writeback-receipt.md)）。

## 反模式

- 让用户先选「你要 capture 还是 organize 还是 memory？」
- 记一条笔记弹出分类树 / 标签多选 / 记忆层级选择
- 静默把整段聊天写进 profile
- 为提取待办再造一个顶层 `todo/` 目录或第六概念
- L1 建议不给路径、不给一键接受话术
