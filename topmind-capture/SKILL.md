---
name: topmind-capture
description: >-
  把链接、摘录、随手记保存到 topmind 动态、专题或 Inbox；显式行动同时记入待办。Use when 记一下、收进、capture、save URL/idea。Do NOT use for only editing existing notes or updating profile.
license: MIT
compatibility: topmind workspace. Host file tools or optional UTR capture-note.
metadata:
  version: "4.15.10"
  action_category: "capture"
  entrypoint: "false"
  triggers: "收集, 收进, 保存, 剪藏, 记一下, 临时存放, 随手记, 想法, 灵感, 暂存沉淀, 记录, 备忘, 存一下, 暂存, 笔记, 抄下来, 摘录, 记一下要做, 别忘了, 要做, capture, note, save, Note it"
  tags: "capture, inbox, note, material"
  author: "TopMindSpace"
  homepage: "https://github.com/topmindspace/topmind-skills"
  updated: "2026-10-26"
  degradation: "../shared/capability-degradation.md"
---

# topmind Capture

把用户给的材料存下来，保留原文、来源和可找回的位置。用户说“记一下”时不访谈分类。多意图请求仍按 [授权及建议](../shared/auto-suggest.md) 完成已要求的后续工作。

## 路由与写入

从当前工作区上下文与 `topmind.yaml` 确定真实类别；已有本轮证据不重复扫描。跳过 hidden，不写死编号。

- 日常动态 → 当前周期本 append；`stream.packing` 默认 weekly，支持 daily/monthly/atom；`stream.year_dir` 默认 true。
- 明确专题 → 专题根新笔记；类别清楚而无专题 → 大类根。
- 不清楚 → role:buffer（常为 Inbox），先保证落盘；有用时附最多 3 个分类备选。
- 待办 `memory/todo.md` 的显式写入与隐含提案，统一见 [auto-suggest](../shared/auto-suggest.md)。

新材料记录适用的 `title`、`source_type`、来源 URL / captured_at；`source_type` 为 user-original / external-capture / ai-derived。保留引用与用户想法的区别，正文截断须说明。不为周期本每次追加重写全文件。

禁止因 capture 顺手改 `topic.md` 或静默写 `memory/profile.md`、`memory/topics/`。只有用户明确要求更新记忆时才进入 memory。

## 特殊输入按需处理

- 长 URL / 网页 → [long-url-capture](../shared/long-url-capture.md)，其中 L1/L2/L3 是抓取档，不是建议阶梯；有 fetch 则取正文，失败保留 URL/摘录并标明限制。GitHub Markdown 优先 raw/README。
- 本地 Office / PDF / 邮件 / 文件夹 → [document-ingest](../shared/document-ingest.md)。有转换能力则转 MD；否则记录原文件位置，不冒充已读正文。
- 用 UTR 时 `capture-note`；Desktop 对应 ingestInbox 的 stream 目标。没有这些工具时用宿主可用文件工具，不要求安装运行时。

## 保存与回执

按 [writeback-receipt](../shared/writeback-receipt.md) 写入：auto 内容直接保存；confirm 内容编辑仍直接保存，仅删除/归档待审阅。回复保存结果和实际路径；失败保留材料并说明失败，不报告虚假成功。

写回之外的细节：[工作区模型](../shared/project-model-brief.md)、[能力降级](../shared/capability-degradation.md)。
