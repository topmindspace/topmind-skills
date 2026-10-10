---
name: topmind-organize
description: >-
  整理本周动态、专题内整理/研究/分析/路由 Inbox。Use when 整理本周、整理、分析、研究、对比、总结要点、organize、summarize。
  Do NOT use for 首次捕获、最终出稿、仅写我的情况、快速 doctor、全库 loop、对外检索一手资料与 AI 前沿深挖（已装外部 topmind-research 时）.
license: MIT
compatibility: topmind workspace with stream period notes, topics, or Inbox.
metadata:
  version: "4.15.3"
  action_category: "organize"
  entrypoint: "false"
  triggers: "整理本周, 理顺本周, 周复盘, 整理, 组织, 研究, 分析, 对比, 提取, 梳理, 归纳, 证据, 实体, 质量审查, 总结, 概括, 汇总, 提纲, 分类整理, 找关联, 总结成笔记要点, organize, summarize, analyze, weekly review"
  tags: "organize, research, analyze, stream, weekly-review"
  author: "TopMindSpace"
  homepage: "https://github.com/topmindspace/topmind-skills"
  updated: "2026-10-08"
  degradation: "../shared/capability-degradation.md"
---

# topmind Organize

已存材料 → 可用结构。用户高频入口：**整理本周**（理顺动态）。

## Activation checklist

1. 若用户说「整理本周 / 理顺流水」→ **整理本周**流程  
2. 否则确认已有笔记 / Inbox（无材料则先 capture）  
3. `list-categories` / 读周期本或专题 `.md`  
4. 按 writeback 写回（默认 auto；整篇替换先备份）  
5. 回执；L1 建议待办/记忆/专题候选，不自动写 memory（见 [`../shared/auto-suggest.md`](../shared/auto-suggest.md)）  

## When NOT to use

- 存新材料 → `topmind-capture`  
- 交付最终报告/文章 → `topmind-write`  
- 只写「我的情况」/ 周期反思 → `topmind-memory`  
- doctor / 全库巡检 → `topmind-maintain` / `topmind-loop`  
- 对外检索一手资料（论文、技术报告、官方公告、模型或产品横向对比）、AI 前沿深挖、周度官方动态 → 外部可选 `topmind-research`（已安装时）；未安装仍由本 skill「研究分析」接手，回执注明来源范围（见 [`../shared/trigger-disambiguation.md`](../shared/trigger-disambiguation.md)）  

## 动作入口判断

| 用户表达 | 入口 |
|---------|------|
| **整理本周 / 理顺本周 / 周复盘** | **整理本周**（主路径） |
| 对比 / 证据 / 来源 / 研究 | 研究分析 |
| 质量 / 矛盾 / 一致性 | 质量审查 |
| 提取实体 / 人物 / 概念（显式） | 实体提取 |
| 整理 inbox / 归类 inbox | Inbox 路由（`plan-inbox-routing`） |
| 默认 / 整理 / 梳理 / 总结 | 整理结构 |

### 整理本周（Stream reconcile · 活动窗口）

用户只感到「点一下整理」；系统以 **近期活动窗口** 为范围（不只最新周期文件名）：

```text
活动窗口 =
  最近周期本
  ∪ 近期 mtime 变更的笔记
  ∪ 增补锚定的原文（旧文评论后整包进入）

1. 读活动窗口材料（优先当前周期本；含对旧文的增补与其 parent）
2. 就地理顺周期本：
   - 合并同一事项状态（「要做 X」+「X 完成」→ 进行中列表更新）
   - 去重、整理 ## 进行中
   - 保留可读叙事；不要为分类而拆文件
3. L1 候选（列表请用户接受后再写；见 ../shared/auto-suggest.md）：
   - **待办维护**：对照 memory/todo.md，新增/完成/更新（todo_maintain 语义）
   - 更新「我的情况」/ 周期反思 → memory skill（profile + periodic，不是专题）
   - 反复主题 → 建议在内容大类下开/并入专题（勿写 memory/topics；勿自动升专题）
```

**待办同步是整理本周的默认建议之一**（不是第六概念）：周期本里「要做 / 完成了」与 `memory/todo.md` 对不上时，给出 diff 建议，点头后写。纯 Host 自行 diff；Desktop `todo_maintain`/`maintainTodos`；UTR `memory.list-todos`/`add-todo`/`toggle-todo`。

**流水可以永远只是流水**——不升专题也完全健康。  
条目上的「增补」= 同文件续写（评论感），不是平行评论库。

写回：默认 `writebackMode: auto`；仅锁定/核心笔记覆盖或删除才备份到现场 **role:system** 目录的 `backups/`（常为 `99-归档/` / `99-Archive/`，不写死中文）。  
回执白话：「本周动态已理顺」+ 路径 + 可选候选列表。

### 整理结构

读专题材料 → 聚类提炼 → 结构化笔记或建议；克制整理，保留原始细节；识别可升 memory 的候选（不自动写 memory）。

**整理留痕（复利，不改目录）**：用户要整理/总结/分析时，除对话回答外，**默认按 writeback 写回**专题根一篇 md（或更新已有综合笔记）。不要只回话不落盘。不建 `INDEX.md`、不建 entities/、不强制 topic.md。可升 memory 的条目、可提取的待办只在回执里**建议**（L1），用户说「记住 / 记上」再落。

### 研究分析

证据链：来源 → 事实 → 推断 → 待验证。对比用表；保留 URL/日期；区分确认与假设。有价值的对比/结论同样**默认落盘**（专题根 md），避免只留在聊天里。

对象是工作区已存材料。需要对外检索一手资料时，已装外部可选 `topmind-research` 则交给它；未安装时本节接手，回执写明只用了工作区材料和宿主可用的检索。

### 实体提取（非默认）

仅显式要求时。实体附证据；不建默认子目录。

### 质量审查

目标对齐、事实一致、溯源、不确定性、输出就绪、写回安全。

### Inbox 路由

内容组织动作（不是 maintain/loop）。`plan-inbox-routing` → 建议类别/专题 → 按保存设置移动或预览。

## 通用流程：读 → 做 → 报

1. **读** `topic.md`（若有）+ 当前对象；不预加载整专题  
2. **做** 标记 `source_type`；原始与 AI 分析用分隔线 + `[AI整理]`  
3. **报** 结果 + 路径回执 + 下一步；**综合默认落专题根**（auto 直接写 / confirm 先审阅）；不自动 write/memory  
   - 入口先确认类别表（`list-categories` / 扫盘）；跳过 hidden；不硬编码编号

克制：不加戏、表格优于空泛罗列、专业术语内联解释。

## 目录偏好

专题根扁平；分类靠 frontmatter 与文件名，不硬建子目录树。**禁止**维护 `INDEX.md` 硬索引、禁止为「像 wiki」新建平行目录；`state.json` 非内容真源。位置靠类别+专题树 + 搜索即可。

## Capability Degradation

[`../shared/capability-degradation.md`](../shared/capability-degradation.md)。`workspace-read.*` · `capture-note` · `plan-inbox-routing`。

## 保存设置

- **自动保存 (auto)**：直接写入并返回路径回执（path receipt）
- **需要审阅 (confirm)**：分级——内容新建/更新/编辑直接落盘；仅删除/归档待确认
- `writeback_mode: auto | confirm`。详见 [`../shared/writeback-receipt.md`](../shared/writeback-receipt.md)。

