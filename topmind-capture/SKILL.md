---
name: topmind-capture
description: >-
  把链接、摘录、随手记收进动态周期本、Inbox 或专题；行动语自动提取/建议待办。Use when 记一下、
  收进、剪藏、保存链接、记一下要做/别忘了、capture、save URL/idea、Note it。
  记下/Log it 是动态主区「写入当前周期本」——路由仍进本 skill，但不作 frontmatter 触发词（见 shared/trigger-disambiguation.md）。
  Do NOT use for 整理本周、出稿、写我的情况、doctor/loop、微信读书、X.
license: MIT
compatibility: topmind workspace. Host file tools or optional UTR capture-note.
metadata:
  version: "4.15.2"
  action_category: "capture"
  entrypoint: "false"
  triggers: "收集, 收进, 保存, 剪藏, 记一下, 临时存放, 随手记, 想法, 灵感, 暂存沉淀, 记录, 备忘, 存一下, 暂存, 笔记, 抄下来, 摘录, 记一下要做, 别忘了, 要做, capture, note, save, Note it"
  tags: "capture, inbox, note, material"
  author: "TopMindSpace"
  homepage: "https://github.com/topmindspace/topmind-skills"
  updated: "2026-10-08"
  degradation: "../shared/capability-degradation.md"
---

# topmind Capture

先存材料（用户动词：**记一下**）。不负责重塑、交付、诊断或外部连接。  
**想记就记 / 随用随记**：默认零提问落盘；分类、待办、记忆一律走 [`../shared/auto-suggest.md`](../shared/auto-suggest.md) 的 L1 建议，不弹多选。

## Activation checklist

1. 工作区根 + `list-categories` / 扫盘（跳过 hidden）  
2. 读 `topmind.yaml` 的 `stream.packing`（默认 **weekly**）  
3. 按内容性质选 **真实目录名**（role；禁止写死编号）  
4. **日常/动态** → 追加到当前周期本；专题明确 → 专题根；不清 → Inbox  
5. 写 frontmatter；白话回执（如「已记到每周一本」）；**不**自动 organize/write  
6. **同轮 L1**：扫描行动语 / 稳定个人信息 / 低信心分类 → 回执附最多 3 条建议（见下）  

## When NOT to use

- 整理已有内容 → `topmind-organize`  
- 基于素材写稿 → `topmind-write`  
- 写入「我的情况」/ 周期反思 → `topmind-memory`  
- 系统体检 / 巡检 → `topmind-maintain` / `topmind-loop`  
- 微信读书 / 发推 → connectors  

消歧总表：[`../shared/trigger-disambiguation.md`](../shared/trigger-disambiguation.md)。

## Inputs

- URL / 文件名 / 来源标签  
- 摘录、想法、自由文本  
- 当前类别/专题（若有）  
- 可选 title、route confidence  

## Routing（低摩擦）

```text
先 list-categories / 扫盘 + 读 topmind.yaml（schema v4）
跳过 hidden；按 role + 内容性质选 directory（真实目录名）
读 stream.packing（atom|daily|weekly|monthly，默认 weekly）

high cat + high topic     → {大类}/{专题}/*.md（新文件）
high cat + med topic      → 专题 + route_reason
loose-stream + 无专题     → 当前周期本 append（packing≠atom）
  packing weekly          → {动态类}/[YYYY/]YYYY-Www.md 今日段落下追加（year_dir 默认 true）
  packing daily           → {动态类}/[YYYY/]YYYY-MM-DD.md 追加
  packing monthly         → {动态类}/[YYYY/]YYYY-MM.md 追加
  packing atom / forceAtom→ {大类}/YYYY-MM-DD-标题.md 新文件
low cat                   → role:buffer（Inbox）
```

默认不访谈分类。存完可移动。禁止写死类名编号。用户只要「记一下」——不要解释 packing 术语（回执可用「本周动态」）。

**低信心时不要只丢 Inbox 就完事**：仍落 buffer，回执附分类备选（最多 3 个，真实目录名），如「更像 ① 20-研究 ② 10-动态，说一声即可移」。详见 [`../shared/auto-suggest.md`](../shared/auto-suggest.md)。

### 待办与记忆（L1，不打断捕获）

捕获正文只写材料；下列副作用走建议阶梯，**不**为分类/待办向用户提问：

| 信号 | L0 | L1 |
|------|----|----|
| 显式行动语（要做 / 记得 / 别忘 / 待办 / 截止 / todo） | 材料照常落盘 | 同轮提取到 `memory/todo.md`（auto 可直接写+回执；confirm 则建议） |
| 隐含行动语（「周三截止」「下周要交」） | 材料照常落盘 | 建议提取 1–N 条待办，点头再写 |
| 稳定个人信息（偏好 / 目标 / 进行中） | 材料照常落盘 | 建议进「我的情况」（写入仍须确认） |
| 低信心类别 | Inbox | 分类备选 |

清单是语义平面卫星（`memory/todo.md`），**不是**新概念、**不**新建顶层 `todo/`。去重按文本；拒绝过的条目不要反复再提。

UTR：`capture-note`（自动识别周期本）。Desktop：`ingestInbox` dest.mode=`stream`（默认）。

## Provenance

`source_type`: `user-original` | `external-capture` | `ai-derived`。

```yaml
title: …
source_type: external-capture
captured_at: 2026-07-13T15:30:00+08:00
topic: {专题名}
category: {大类目录名}
route_confidence: medium
route_reason: …
status: todo
```

长 URL / 网页：[`../shared/long-url-capture.md`](../shared/long-url-capture.md)。

| 层 | 谁 | 能力 |
|----|----|------|
| L1 | Desktop `fetchUrl` / host fetch | Mozilla Readability + 启发式 |
| L1-GH | 同上 · GitHub md/README | raw 直取 + 相对图改写（`lib/github-md.mjs`） |
| L2 | Desktop 增强渲染 | SPA 空壳（ephemeral Chromium） |
| L3 | 手动粘贴 | 永远可用 |
| L3+ | 浏览器扩展 Clip Bridge | 活 DOM Readability → Desktop 清洗落盘 |

Agent host 能 fetch 则提取正文，否则保留 URL + 摘录；推荐日常剪藏走 L3+。GitHub 仓库 / Markdown 文件优先走 raw/README，不 HTML scrape。

### 本地文档 / Office / 邮件 / 统一捕获

协议：[`../shared/document-ingest.md`](../shared/document-ingest.md)。

| 入口 | 能力 |
|------|------|
| **Desktop 统一捕获** | ⌘N 层 / ⌘⇧N 全局便签；智能粘贴文件；笔记+文档复合提交 |
| **Desktop 知识加工 Hub** | 队列、批文件夹、转换器检测/安装；默认 anydoc（docx·doc·pdf·xlsx·pptx·odt·rtf·epub·csv）+ 内置 eml/html；可选 markitdown/pandoc |
| **Agent** | 有转换能力则转 MD 后按 capture 写回；否则路径说明进 Inbox |

默认 **md-only**；失败 original-fallback。不新增并列 skill 入口——仍走 `topmind` → `capture`。

## Workflow

1. 按内容性质推断类别（动态发现），再推断专题  
2. 类别不清 → Inbox（+ 分类备选建议）  
3. 保留 provenance；长文标注截断  
4. 按保存设置写入（见 [`../shared/writeback-receipt.md`](../shared/writeback-receipt.md)）  
5. 回执：路径、目标、信心、下一步（不自动触发其他 skill）  
6. L1 建议：待办提取 / 记忆候选 / 分类备选（见 [`../shared/auto-suggest.md`](../shared/auto-suggest.md)）

**边界**：只写材料笔记。**禁止**改 `topic.md`、禁止自动 organize、禁止静默写 memory/profile 或 memory/topics。存完可在回执**建议**「需要时整理 / 记入待办 / 更新我的情况」——仅用户面，不自动链式。

「刚才收哪」：按 mtime 扫近期 `.md`（或 UTR `list-recent-captures` advanced）。

## Capability Degradation

见 [`../shared/capability-degradation.md`](../shared/capability-degradation.md)。主命令：`capture-note` · `list-categories` · `list-topics`。

## 保存设置

- **自动保存 (auto)**：直接写入并返回路径回执（path receipt）
- **需要审阅 (confirm)**：分级——内容新建/更新/编辑直接落盘；仅删除/归档待确认
- `writeback_mode: auto | confirm`。详见 [`../shared/writeback-receipt.md`](../shared/writeback-receipt.md)。

