---
name: topmind
description: >-
  topmind 工作区入口：处理模糊请求、待办查询和多动作任务。Use when topmind、有什么要做的、收集并整理成稿。Do NOT intercept a clear single-action sub-skill.
license: MIT
compatibility: >-
  topmind workspace with {NN-Name}/ categories. Host file tools primary; UTR optional.
  Install with shared/ sibling for progressive disclosure links.
metadata:
  version: "4.15.9"
  action_category: "router"
  entrypoint: "true"
  triggers: "topmind, 知识库, 工作区, 待办, 有什么要做的, 要做的事, todo, todo list"
  tags: "router, entrypoint, topmind"
  author: "TopMindSpace"
  homepage: "https://github.com/topmindspace/topmind-skills"
  updated: "2026-10-28"
  degradation: "../shared/capability-degradation.md"
---

# topmind

用户日常入口是 `topmind`；单意图明确时直接使用对应子技能。不要让用户选择内部模块。

## 识别与执行

确认当前工作区根，按需读 `topmind.yaml` 与真实目录；已有本轮上下文不重复扫描。根据用户目标选择动作，缺少会影响结果的信息才询问。默认不加载整工作区。

| 目标 | 技能 / 操作 |
|---|---|
| 记链接、摘录、想法、记一下要做某事 | `topmind-capture`；动态周期本 / 专题 / Inbox，显式待办进 `memory/todo.md` |
| 待办有哪些、完成/更新某条待办 | 直接读写 `memory/todo.md`，不启动整理流程 |
| 整理本周、总结/对比已有材料、开/并专题 | `topmind-organize`；临时问答按需回复，持久整理写回 |
| 用工作区素材起草、润色、保存通用稿件 | `topmind-write` |
| 明确公众号、X 长文/短帖、封面或长图 | 直接使用已安装的独立写作技能；需保存到工作区时沿用 `topmind-write` 的落盘约定 |
| 记住我、更新我的情况、周期反思 | `topmind-memory` |
| 结构体检、修复、恢复 | `topmind-maintain` |
| 全工作区语义巡检、长任务断点恢复 | `topmind-loop` |
| 微信读书 / X / 记账 | 可选 `topmind-weread` / `topmind-x` / `topmind-ledger` |

外部检索研究、平台写作、封面/海报、幻灯片、交接的可选技能与容易混淆的请求，按需读 [路由消歧](../shared/trigger-disambiguation.md)。仅使用宿主实际可用的技能和工具；未安装专用技能时完成通用可行部分并说明限制。不让用户先选择内部技能。

用户一次要求多步，按依赖连续完成到最终交付；不因切换技能重复确认。用户未请求的延伸只给建议，见 [多意图](references/multi-intent.md) 与 [授权及建议](../shared/auto-suggest.md)。

## 产品特有约定

- 文件是内容真源。类别动态发现，跳过 hidden；名字取真实目录，低信心落 role:buffer，不访谈分类。
- 动态默认按 `stream.packing` 追加周期本，`stream.year_dir` 默认 true；专题明确才进入专题。`topic.md` 有则按需读，不为补结构强建。
- 我的情况默认 `memory/profile.md`，反思在 `memory/periodic/{YYYY}/`；开专题是在内容大类下建目录，只有明说语义专题记忆才用 `memory/topics/`。
- 复利纪律：持久整理与稿件按意图落盘；临时问答不强存。不建 `INDEX.md` 硬索引或平行 wiki，不把会话当内容真源。
- 内容与路径细节：[工作区模型](../shared/project-model-brief.md)；类别角色：[模板类别](references/template-categories.md)；连接器：[解析](references/connector-resolution.md)。

## 保存设置与交付

`writeback_mode: auto | confirm`，自动保存 auto 直接写 + 回执；confirm 内容编辑直接落盘，删除/归档走审阅入口。完整写闸、locked 首写快照和恢复语义见 [writeback-receipt](../shared/writeback-receipt.md)。用户的明确授权只覆盖请求范围，不能绕过程序围栏。

主路径是宿主文件工具，UTR 可选；不编造 shell 或不存在的工具。工具不足时参照 [能力降级](../shared/capability-degradation.md)，失败不得伪装成功。仅操作当前 active 工作区。

回复只需结果与实际路径；只有能帮助用户决策时才附建议，不固定列出信心、模式、理由等模板字段。输出语言按 [output-language](../shared/output-language.md)。宿主加载与安装问题才读 [host-loading](../shared/host-loading.md)。
